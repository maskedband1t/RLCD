"""E62: run the E42 cause question over every unique DMV description, keep the
distribution, and ask whether the splits cluster. Question mirrors e42_disengage.Q."""
import collections, csv, glob, json, math, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://api.typesafe.ai/v1/systemone"
Q = {"cause": {"type": "choice",
  "instructions": ("This is a report of why an autonomous vehicle stopped driving itself and a human "
                   "took over. Different companies write these very differently. What is the underlying cause?"),
  "criteria": {
    "perception": "Failed to see, classify or track something -- sensors, detection, misclassification.",
    "planning": "Chose a poor manoeuvre, hesitated, mis-timed, or a planning module failed.",
    "localization_mapping": "Lost track of where it was, or the map was wrong.",
    "control_execution": "Knew what to do but executed it badly -- steering, braking, lane keeping.",
    "other_road_user": "Another driver, cyclist or pedestrian behaved unexpectedly.",
    "hardware_comms": "A hardware fault, sensor failure, or loss of communication.",
    "environment": "Weather, road works, debris, poor markings or lighting.",
    "operational": "Testing procedure, handover protocol, or a precautionary takeover with no fault.",
    "unclear": "The description does not say enough to tell."}}}

def corpus():
    man = {}
    for p in sorted(glob.glob("data/dmv/*.csv")):
        rows = list(csv.DictReader(open(p, encoding="latin-1")))
        if not rows: continue
        cols = {k.lower(): k for k in rows[0]}
        dk = next(cols[k] for k in cols if "description" in k)
        mk = next(cols[k] for k in cols if "manufacturer" in k)
        for r in rows:
            t = " ".join((r.get(dk) or "").split())
            if t: man.setdefault(t, (r.get(mk) or "").strip())
    return man

def ask(text, key, retries=3):
    body = json.dumps({"state": {"report": text}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}",
                                                                   "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["answers"]["cause"]["probabilities"]
        except Exception:                                      # noqa: BLE001
            if a == retries - 1: return None
            time.sleep(1.5 * (a + 1))

def main():
    key = os.environ["TYPESAFE_API_KEY"]; man = corpus(); texts = list(man)
    print(f"{len(texts)} unique descriptions")
    with ThreadPoolExecutor(8) as ex: probs = list(ex.map(lambda t: ask(t, key), texts))
    out = []
    for t, p in zip(texts, probs):
        if not p: continue
        s = sorted(p.items(), key=lambda x: -x[1]); pmax = s[0][1]
        H = -sum(v * math.log(v) for v in p.values() if v > 0)
        out.append(dict(text=t, man=man[t], probs=p, top=s[0][0], p2=s[1][0], pmax=pmax, H=H,
                        split=pmax < .5, unclear_top=s[0][0] == "unclear"))
    json.dump(out, open("notes/e62.json", "w"))
    n = len(out); split = [o for o in out if o["split"]]; unc = [o for o in out if o["unclear_top"]]
    print(f"\nsplit (no option > .50): {len(split)}/{n} = {100*len(split)/n:.1f}%     "
          f"unclear-top: {len(unc)}/{n} = {100*len(unc)/n:.1f}%")
    print("pmax distribution:", " ".join(f"[{lo/10:.1f}-{(lo+1)/10:.1f}) {sum(lo/10 <= o['pmax'] < (lo+1)/10 for o in out):4d}"
                                         for lo in range(1, 10)) + f"  [1.0] {sum(o['pmax']>=1 for o in out)}")
    pairs = collections.Counter(tuple(sorted((o["top"], o["p2"]))) for o in split)
    print(f"\ntop-2 pairs among the {len(split)} splits (prediction: >=50% in <=3 pairs):")
    cum = 0
    for (a, b), k in pairs.most_common(10):
        cum += k; print(f"  {a:22s} ↔ {b:22s} {k:4d}  {100*k/len(split):5.1f}%   cum {100*cum/len(split):5.1f}%")
    print(f"\nsplit rate by manufacturer (n >= 15):")
    bym = collections.defaultdict(list)
    for o in out: bym[o["man"]].append(o["split"])
    for m, v in sorted(bym.items(), key=lambda x: -len(x[1])):
        if len(v) >= 15: print(f"  {m[:28]:28s} n={len(v):4d}  split {100*sum(v)/len(v):5.1f}%")
    print("\n25 most-split descriptions (highest entropy):")
    for o in sorted(split, key=lambda o: -o["H"])[:25]:
        p = o["probs"]; print(f"  {o['top'][:11]:11s}{p[o['top']]:.2f} / {o['p2'][:11]:11s}{p[o['p2']]:.2f}  [{o['man'][:10]:10s}] {o['text'][:95]}")

if __name__ == "__main__":
    main()

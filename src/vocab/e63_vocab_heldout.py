"""E63: candidate categories from half the splits; test on the other half + controls."""
import collections, json, os, random, time, urllib.request, copy
from concurrent.futures import ThreadPoolExecutor
from e62_vocab import API, Q as Q9

Q12 = copy.deepcopy(Q9)
Q12["cause"]["criteria"].update({
  "anticipatory_takeover": "The driver intervened BEFORE any fault, judging the vehicle's plan or trajectory was becoming risky (too close to a boundary, heavy traffic for a manoeuvre, preventive stop).",
  "expectation_mismatch": "The vehicle's behaviour was permissible but not what the driver expected -- faster, a different path, an unfamiliar manoeuvre; a comfort or expectation takeover.",
  "odd_exit": "The situation fell outside the vehicle's operational design domain -- an obstruction in lane, unmapped works, an unsupported manoeuvre -- and the driver took over for that reason."})

def ask(text, key, Q, retries=3):
    body = json.dumps({"state": {"report": text}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())["answers"]["cause"]["probabilities"]
        except Exception:                                      # noqa: BLE001
            if a == retries - 1: return None
            time.sleep(1.5 * (a + 1))

def main():
    key = os.environ["TYPESAFE_API_KEY"]; rows = json.load(open("notes/e62.json"))
    splits = sorted([o for o in rows if o["split"]], key=lambda o: -o["H"])
    derive, test = splits[0::2], splits[1::2]
    rng = random.Random(0); controls = rng.sample([o for o in rows if not o["split"]], 200)
    with ThreadPoolExecutor(8) as ex:
        t9  = list(ex.map(lambda o: ask(o["text"], key, Q9),  test))
        t12 = list(ex.map(lambda o: ask(o["text"], key, Q12), test))
        c12 = list(ex.map(lambda o: ask(o["text"], key, Q12), controls))
    res = lambda ps: sum(1 for p in ps if p and max(p.values()) > .6)
    print(f"test half (n={len(test)}): 9-way re-ask resolved {res(t9)}/{len(test)} = {100*res(t9)/len(test):.0f}%  (noise floor)")
    print(f"                        12-way      resolved {res(t12)}/{len(test)} = {100*res(t12)/len(test):.0f}%  (prediction ≥ 50%; falsifier < 30%)")
    absorb = collections.Counter(max(p, key=p.get) for p in t12 if p)
    print("12-way top choice on the test half:", dict(absorb.most_common()))
    changed = [(o, p) for o, p in zip(controls, c12) if p and max(p, key=p.get) != o["top"]]
    print(f"\ncontrols (n={len(controls)}): top choice unchanged {len(controls)-len(changed)}/{len(controls)} = {100*(len(controls)-len(changed))/len(controls):.0f}%  (prediction ≥ 90%)")
    moves = collections.Counter((o["top"], max(p, key=p.get)) for o, p in changed)
    print("control moves:", dict(moves.most_common()))
    print("\ntest-half examples, 9-way → 12-way:")
    for o, p9, p12 in list(zip(test, t9, t12))[:16]:
        if not (p9 and p12): continue
        a, b = max(p9, key=p9.get), max(p12, key=p12.get)
        print(f"  {a[:11]:11s}{p9[a]:.2f} → {b[:20]:20s}{p12[b]:.2f}  {o['text'][:80]}")
    json.dump({"test": [(o["text"], p9, p12) for o, p9, p12 in zip(test, t9, t12)],
               "controls": [(o["text"], o["top"], p) for o, p in zip(controls, c12)]}, open("notes/e63.json", "w"))

if __name__ == "__main__":
    main()

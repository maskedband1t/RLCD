"""E65: Jev as a calibrated critic over a planner's candidate next steps.
gen -> notes/e65-questions.json ; jev -> notes/e65-jev.json ; report."""
import collections, json, math, os, random, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://api.typesafe.ai/v1/systemone"
RX = re.compile(r"^(put|place)\s+(?:the\s+|a\s+|an\s+)?(?P<x>[a-z][a-z0-9\- ]{1,30}?)\s+(?P<p>in|into|inside|on|onto)\s+(?:the\s+|a\s+)?(?P<y>[a-z][a-z0-9\- ]{1,30}?)\.?$", re.I)
TYPES = ["skip_ahead", "repeat", "wrong_object", "irrelevant", "post_failure"]

def plan(x, y, p):
    p = "in" if p in ("in", "into", "inside") else "on"
    return [f"locate the {x}", f"move the gripper above the {x}", f"grasp the {x}", f"lift the {x}",
            f"move the {x} over the {y}", f"lower the {x} and release it {p} the {y}", "retract the gripper", "done"]

def tasks():
    import os
    here = os.path.dirname(os.path.abspath(__file__)); alt = os.path.join(here, "..", "..", "data", "droid_tasks.json")
    if os.path.exists("data/tensors/episodes.json"): strings = [(e.get("task") or "").strip() for e in json.load(open("data/tensors/episodes.json"))]
    else: strings = json.load(open(alt if os.path.exists(alt) else "data/droid_tasks.json"))
    out = {}
    for t in strings:
        m = RX.match(t)
        if not m: continue
        x, y = m.group("x").strip().lower(), m.group("y").strip().lower()
        if " and " in x or " and " in y or len(x.split()) > 4 or len(y.split()) > 4 or x == y: continue
        out[t] = (x, y, m.group("p").lower())
    return out

def gen(n_per_type=80, seed=0):
    rng = random.Random(seed); T = tasks(); items = list(T.items()); rng.shuffle(items)
    qs = []; used = set()
    def other(x):
        while True:
            t, (x2, y2, p2) = rng.choice(items)
            if x2 != x: return t, x2, y2, p2
    for typ in TYPES:
        made = 0; i = 0
        while made < n_per_type and i < len(items):
            t, (x, y, p) = items[i]; i += 1
            if t in used: continue
            P = plan(x, y, p); k = None; prefix = None; correct = None; ds = None
            if typ == "skip_ahead":
                k = rng.choice([1, 2, 3]); correct = P[k]; ds = rng.sample(P[k + 1:], 3)
            elif typ == "repeat":
                k = rng.choice([3, 4, 5, 6]); correct = P[k]; ds = rng.sample(P[:k], 3)
            elif typ == "wrong_object":
                k = rng.choice([1, 2, 3, 4, 5]); correct = P[k]; ds = []
                while len(ds) < 3:
                    _, x2, _, _ = other(x); d = P[k].replace(f"the {x}", f"the {x2}")
                    if d != correct and d not in ds: ds.append(d)
            elif typ == "irrelevant":
                k = rng.choice([1, 2, 3, 4, 5]); correct = P[k]; ds = []
                while len(ds) < 3:
                    _, x2, y2, p2 = other(x); d = rng.choice(plan(x2, y2, p2)[1:6])
                    if d not in ds and d != correct: ds.append(d)
            elif typ == "post_failure":
                k = 3; correct = P[2]                                   # retry the grasp
                ds = [P[3], P[4], P[5]]                                 # naive continuations
            prefix = P[:k]
            if typ == "post_failure":
                prefix = P[:2] + [f"{P[2]} — FAILED: the gripper closed on nothing; the {x} is still in place directly below the gripper"]
            opts = [correct] + ds; rng.shuffle(opts); letters = "ABCD"
            qs.append(dict(id=len(qs), type=typ, task=t, x=x, y=y, k=k, steps_completed=prefix,
                           candidates=dict(zip(letters, opts)), truth=letters[opts.index(correct)]))
            used.add(t); made += 1
    json.dump(qs, open("notes/e65-questions.json", "w"), indent=0)
    print(f"{len(qs)} questions over {len(used)} tasks; per type {collections.Counter(q['type'] for q in qs)}; truth positions {collections.Counter(q['truth'] for q in qs)}")
    return qs

def jev_q(q):
    C = q["candidates"]
    Q = {"next_step": {"type": "choice",
          "instructions": ("A robot arm is executing a manipulation task one step at a time. Given the task and the steps "
                           "already completed, including any reported failure, which candidate is the correct next step?"),
          "criteria": {L: f"Candidate {L}: {C[L]}" for L in "ABCD"}}}
    for L in "ABCD":
        Q[f"ok_{L}"] = {"type": "noul", "instructions": f"Is candidate {L} — \"{C[L]}\" — the correct next step for the robot right now?",
                        "criteria": {"true": "Yes, it is exactly what should happen next.", "false": "No — it skips something required, repeats what is done, uses the wrong object, or is not part of this task."}}
    return Q

def jev(q, key, retries=3):
    state = {"task": q["task"], "steps_completed": q["steps_completed"], "candidate_next_steps": q["candidates"]}
    body = json.dumps({"state": state, "model": "jev-latest", "questions": jev_q(q)}).encode()
    for a in range(retries):
        t0 = time.time()
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())["answers"]
            ns = d["next_step"]; pr = ns["probabilities"]
            return dict(id=q["id"], choice=ns.get("choice") or max(pr, key=pr.get), probs=pr,
                        conf=ns.get("confidence"), ok={L: d[f"ok_{L}"]["noul"] for L in "ABCD"}, secs=time.time() - t0)
        except Exception as e:                                   # noqa: BLE001
            if a == retries - 1: return dict(id=q["id"], error=str(e))
            time.sleep(1.5 * (a + 1))

def lexical(q, rng):
    tw = set(re.findall(r"[a-z0-9]+", q["task"].lower()))
    sc = {L: len(tw & set(re.findall(r"[a-z0-9]+", c.lower()))) / max(1, len(tw | set(re.findall(r"[a-z0-9]+", c.lower())))) for L, c in q["candidates"].items()}
    best = max(sc.values()); return rng.choice([L for L, v in sc.items() if v == best])

def ece(conf, correct, bins=10):
    n = len(conf); tot = 0.0
    for b in range(bins):
        idx = [i for i in range(n) if b / bins <= conf[i] < (b + 1) / bins + (1e-9 if b == bins - 1 else 0)]
        if idx: tot += len(idx) / n * abs(sum(correct[i] for i in idx) / len(idx) - sum(conf[i] for i in idx) / len(idx))
    return tot

def auroc(score, label):
    pos = [s for s, l in zip(score, label) if l]; neg = [s for s, l in zip(score, label) if not l]
    if not pos or not neg: return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

def report(qs, res, name, pick, conf=None):
    by = collections.defaultdict(list); allc = []; allconf = []
    for q in qs:
        r = res.get(q["id"]); 
        if r is None or "error" in r: continue
        c = pick(r) == q["truth"]; by[q["type"]].append(c); allc.append(c)
        if conf: allconf.append(conf(r))
    line = f"{name:14s}" + "".join(f"{100*sum(by[t])/max(1,len(by[t])):6.0f}%" for t in TYPES) + f"   all {100*sum(allc)/max(1,len(allc)):5.1f}%"
    if conf: line += f"   ECE {ece(allconf, allc):.3f}  AUROC {auroc(allconf, allc):.3f}"
    print(line); return by

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    qs = gen() if cmd in ("gen", "all") or not os.path.exists("notes/e65-questions.json") else json.load(open("notes/e65-questions.json"))
    if cmd in ("jev", "all"):
        key = os.environ["TYPESAFE_API_KEY"]
        with ThreadPoolExecutor(6) as ex: out = list(ex.map(lambda q: jev(q, key), qs))
        json.dump(out, open("notes/e65-jev.json", "w")); print(f"jev: {sum('error' in o for o in out)} errors, mean {sum(o.get('secs',0) for o in out)/len(out):.2f}s, max {max(o.get('secs',0) for o in out):.2f}s")
    res = {o["id"]: o for o in json.load(open("notes/e65-jev.json"))}
    rng = random.Random(1)
    print(f"{'':14s}" + "".join(f"{t[:10]:>7s}" for t in TYPES))
    report(qs, {q["id"]: dict(id=q["id"], c=rng.choice("ABCD")) for q in qs}, "random", lambda r: r["c"])
    report(qs, {q["id"]: dict(id=q["id"], c=lexical(q, rng)) for q in qs}, "lexical", lambda r: r["c"])
    report(qs, res, "jev choice", lambda r: r["choice"], conf=lambda r: max(r["probs"].values()))
    report(qs, res, "jev noul-max", lambda r: max(r["ok"], key=r["ok"].get), conf=lambda r: max(r["ok"].values()))
    # per-candidate noul as a gate: P(true) vs is-correct over all 4N candidates
    s, l = [], []
    for q in qs:
        r = res.get(q["id"])
        if r and "ok" in r:
            for L in "ABCD": s.append(r["ok"][L]); l.append(L == q["truth"])
    print(f"\nper-candidate noul over {len(s)} candidates: AUROC {auroc(s, l):.3f}  ECE {ece(s, l):.3f}  mean P(true) correct {sum(x for x,y in zip(s,l) if y)/max(1,sum(l)):.2f} vs wrong {sum(x for x,y in zip(s,l) if not y)/max(1,len(l)-sum(l)):.2f}")

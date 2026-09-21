"""E70: state format (numeric vs categorical) × model. Builds the paired suite; runs Jev + program now; 7B via --llm."""
import json, os, sys, random, time, urllib.request, collections, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dispatch"))
from e65_critic import API, plan, tasks
from baselines import program_pick

def build(seed=3, n=80):
    rng = random.Random(seed); T = list(tasks().items()); rng.shuffle(T); T = T[300:]        # tasks unused elsewhere
    items = []
    for i in range(n):
        t, (x, y, p) = T[i]; P = plan(x, y, p)
        for fmt, line in (("numeric", f"{P[2]} — done; gripper force sensor reads 0.0 N"), ("categorical", f"{P[2]} — done; gripper reports: nothing held")):
            opts = [f"open the gripper and grasp the {x} again", P[3], P[4], P[5]]; rng2 = random.Random(f"{i}{fmt}"); rng2.shuffle(opts)
            items.append(dict(id=f"fail-{i}-{fmt}", setting="critic", kind="failure", fmt=fmt, task=t, x=x, y=y, steps_completed=P[:2] + [line],
                              candidates=dict(zip("ABCD", opts)), truth="ABCD"[opts.index(f"open the gripper and grasp the {x} again")]))
    for i in range(n, 2 * n):
        t, (x, y, p) = T[i]; P = plan(x, y, p)
        for fmt, line in (("numeric", f"{P[2]} — done; gripper force sensor reads 4.2 N"), ("categorical", f"{P[2]} — done; gripper reports: object secured")):
            opts = [P[3], f"open the gripper and grasp the {x} again", f"locate the {x}", P[1]]; rng2 = random.Random(f"{i}{fmt}"); rng2.shuffle(opts)
            items.append(dict(id=f"benign-{i}-{fmt}", setting="critic", kind="benign", fmt=fmt, task=t, x=x, y=y, steps_completed=P[:2] + [line],
                              candidates=dict(zip("ABCD", opts)), truth="ABCD"[opts.index(P[3])]))
    return items

def ask_jev(q, key):
    C = q["candidates"]; Q = {"next_step": {"type": "choice", "instructions": ("A robot arm is executing a manipulation task one step at a time. Given the task and the steps "
          "already completed, including any status report, which candidate is the correct next step?"), "criteria": {L: f"Candidate {L}: {C[L]}" for L in C}}}
    body = json.dumps({"state": {"task": q["task"], "steps_completed": q["steps_completed"], "candidate_next_steps": C}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: d = json.loads(r.read())["answers"]["next_step"]
            pr = d["probabilities"]; return dict(id=q["id"], choice=d.get("choice") or max(pr, key=pr.get), probs=pr)
        except Exception as e:                                   # noqa: BLE001
            if a == 2: return dict(id=q["id"], error=str(e))
            time.sleep(1.5 * (a + 1))

def dispatch_items():
    """Numeric vs code-evaluated categorical state for threshold/unit items; truth = ok sets; decision via decide_by_cost."""
    from dispatch import ask as dask, decide_by_cost, prepare_state
    from dispatch.paraphrase import P as PP
    from dispatch.scenarios import S as SS
    pick = [s for s in PP if s["cat"] in ("just-under 10.0", "inclusive 10.0")] + [s for s in SS if s["name"] in ("unit mismatch: 22 lbs vs 'over 10 kg'", "load in grams: 10000 g vs 'exceeding 10 kg'", "load exactly 10.0 kg vs 'over 10 kg'", "load 10.5 kg vs 'over 10 kg'", "'exceeding 10 kg' at exactly 10.0")]
    return pick, dask, decide_by_cost, prepare_state

def boot_gain(rows_num, rows_cat, n=10000):
    """rows_*: dict base_id -> correct(bool). Paired by base item."""
    ids = sorted(set(rows_num) & set(rows_cat)); d = [int(rows_cat[i]) - int(rows_num[i]) for i in ids]; rng = random.Random(0)
    bs = [sum(rng.choice(d) for _ in d) / len(d) for _ in range(n)]; bs.sort(); return sum(d) / len(d), bs[int(.025 * n)], bs[int(.975 * n)], len(ids)

def main():
    key = os.environ["TYPESAFE_API_KEY"]; items = build(); json.dump(items, open("data/suites/e70-factorial-critic.json", "w"), indent=0)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(6) as ex: jev = {r["id"]: r for r in ex.map(lambda q: ask_jev(q, key), items)}
    json.dump(list(jev.values()), open("results/e70-jev-critic.json", "w"))
    print("=== critic setting (160 base items × 2 formats) ===")
    for model, pick in (("jev", lambda q: jev[q["id"]].get("choice")), ("program", program_pick)):
        acc = collections.defaultdict(list); paired = {"numeric": {}, "categorical": {}}
        for q in items:
            ok = pick(q) == q["truth"]; acc[(q["kind"], q["fmt"])].append(ok); paired[q["fmt"]][q["id"].rsplit("-", 1)[0]] = ok
        g, lo, hi, n = boot_gain(paired["numeric"], paired["categorical"])
        print(f"  {model:8s} " + "  ".join(f"{k[0]}/{k[1][:3]} {100*sum(v)/len(v):5.1f}%" for k, v in sorted(acc.items())) + f"   gain categorical−numeric {100*g:+.1f} pts [{100*lo:+.1f},{100*hi:+.1f}] n={n}")
    print("\n=== dispatch setting (threshold/unit items; numeric raw state vs code-evaluated categorical state) ===")
    pick, dask, dbc, prep = dispatch_items(); res = {"numeric": {}, "categorical": {}}
    for s in pick:
        for fmt, st in (("numeric", s["st"]), ("categorical", prep(s["st"]))):
            for rep in range(2):
                a = dask(st); d, _ = dbc(a); res[fmt].setdefault(s["name"], []).append(d in s["ok"])
    num = {k: sum(v) / len(v) >= 0.5 for k, v in res["numeric"].items()}; cat = {k: sum(v) / len(v) >= 0.5 for k, v in res["categorical"].items()}
    g, lo, hi, n = boot_gain(num, cat)
    print(f"  jev      numeric {100*sum(num.values())/len(num):5.1f}%   categorical {100*sum(cat.values())/len(cat):5.1f}%   gain {100*g:+.1f} pts [{100*lo:+.1f},{100*hi:+.1f}] n={n} items (2 repeats each, majority)")
    json.dump({"numeric": res["numeric"], "categorical": res["categorical"]}, open("results/e70-jev-dispatch.json", "w"))
if __name__ == "__main__": main()

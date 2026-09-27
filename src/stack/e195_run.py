"""E195. Train bank fits the two fitted arms; a held-out bank the fitting never touches scores everything."""
import json, sys, time, subprocess
import numpy as np
from stack.ground import Grounder, counter_positions, approach_pose, viewpoint, APPEARANCE, BIN_BOUND
from stack.ground_arms import (episode, AlwaysCommit, AlwaysVerify, MarginRule, FittedLogistic,
                               COST_IRREVERSIBLE, COST_MISPLACED)

TRAIN = range(0, 500)
TEST = range(10_000, 10_300)
SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "nogit"


def labelled(seeds):
    """(evidence, was-it-right) pairs, for fitting. The label is exact, which is the whole point of a simulator."""
    pos = counter_positions(); names = [k for k in pos if k != "medicine"]
    out = []
    for s in seeds:
        so, lat, ye = viewpoint(s)
        xy, yaw = approach_pose(so, lat, ye)
        g = Grounder(s * 17, names, pos, xy, yaw)
        intended = names[s % len(names)]
        ev, ok, got = g.attempt(intended)
        if got is None: continue
        ev = dict(ev); ev["intended"] = intended
        out.append((ev, ok))
    return out


def auroc(p, y):
    p, y = np.asarray(p, float), np.asarray(y, int)
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg): return float("nan")
    a = np.concatenate([pos, neg]); o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(1, len(a) + 1)
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def ece(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, int)
    if not len(p): return float("nan")
    e = 0.0
    for i in range(bins):
        m = (p >= i / bins) & (p < (i + 1) / bins if i < bins - 1 else p <= 1.0)
        if m.sum(): e += m.sum() / len(p) * abs(p[m].mean() - y[m].mean())
    return float(e)


tr = labelled(TRAIN)
print(f"E195  sha={SHA}  train={len(tr)} labelled attempts  test={len(TEST)} held-out episodes")
print(f"  training-bank grounding accuracy {np.mean([r[1] for r in tr]):.1%}")

best_tau, best_cost = None, 1e18
for tau in np.arange(0.0, 6.01, 0.25):
    c = sum(episode(s, MarginRule(float(tau)))["cost"] for s in list(TRAIN)[:200])
    if c < best_cost: best_cost, best_tau = c, float(tau)
print(f"  margin threshold fitted on the training bank: tau={best_tau}")

lg = FittedLogistic().fit(tr)
print(f"  logistic fitted on {len(tr)} labelled attempts\n")

ARMS = [("always_commit", lambda: AlwaysCommit()), ("always_verify", lambda: AlwaysVerify()),
        ("margin_rule", lambda: MarginRule(best_tau)), ("fitted_logistic", lambda: lg)]
if "--jev" in sys.argv:
    from stack.ground_jev import GroundJev
    ARMS.append(("jev_ground", lambda: GroundJev()))

H = (f"{'arm':<17}{'right':>9}{'IRREVERSIBLE':>14}{'misplaced':>11}{'verifies':>10}"
     f"{'walk s':>9}{'cost/ep':>9}{'calls':>7}")
print(H); print("-" * len(H))
rows = []
for label, mk in ARMS:
    arm = mk(); recs = [episode(s, arm) for s in TEST]
    for r in recs: r["arm"] = label; r["sha"] = SHA
    rows += recs
    n = len(recs); binb = [r for r in recs if r["bin_bound"]]
    print(f"{label:<17}{sum(r['correct'] for r in recs):>6}/{n:<3}"
          f"{sum(r['irreversible'] for r in recs):>8} /{len(binb):<3}"
          f"{sum(r['misplaced'] for r in recs):>11}{sum(r['verifies'] for r in recs):>10}"
          f"{sum(r['t_verify'] for r in recs):>9.0f}{sum(r['cost'] for r in recs) / n:>9.2f}"
          f"{getattr(arm, 'calls', 0):>7}", flush=True)
    if getattr(arm, "first_error", None): print(f"    first error: {arm.first_error}", flush=True)

print("\n--- is the NUMBER any good? (E195.3, E195.4) ---")
te = labelled(TEST)
y = [int(o) for _, o in te]
pl = [lg.prob(e) for e, _ in te]
print(f"  {'source':<17}{'AUROC':>8}{'ECE all':>10}{'ECE bin-bound':>15}")
bb = [i for i, (e, _) in enumerate(te) if APPEARANCE[e['intended']]['belongs'] == 'bin']
print(f"  {'fitted logistic':<17}{auroc(pl, y):>8.3f}{ece(pl, y):>10.3f}"
      f"{ece([pl[i] for i in bb], [y[i] for i in bb]):>15.3f}")
if "--jev" in sys.argv:
    from stack.ground_jev import GroundJev
    j = GroundJev(); pj = []
    for e, _ in te:
        try: pj.append(j.prob(e))
        except Exception: pj.append(float("nan"))
    ok = [i for i, v in enumerate(pj) if np.isfinite(v)]
    print(f"  {'jev zero-shot':<17}{auroc([pj[i] for i in ok], [y[i] for i in ok]):>8.3f}"
          f"{ece([pj[i] for i in ok], [y[i] for i in ok]):>10.3f}"
          f"{ece([pj[i] for i in bb if np.isfinite(pj[i])], [y[i] for i in bb if np.isfinite(pj[i])]):>15.3f}"
          f"   ({j.calls} calls, {j.errors} errors)")
with open("results/table/e195.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
print(f"\nwrote results/table/e195.jsonl ({len(rows)} rows)")

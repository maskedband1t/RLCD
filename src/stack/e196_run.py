"""E196: three models in the same seat. Same bench, same question, same state, same 25-label recalibration."""
import json, subprocess, sys, time
import numpy as np
from stack.ground import Grounder, counter_positions, approach_pose, viewpoint, APPEARANCE
from stack.ground_arms import episode, FittedLogistic, expected_cost_says_verify
from stack.ground_seats import seats

TRAIN = range(0, 400)
TEST = range(10_000, 10_150)
RECAL_N = 25
SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "nogit"


def labelled(seeds):
    pos = counter_positions(); names = [k for k in pos if k != "medicine"]; out = []
    for s in seeds:
        so, lat, ye = viewpoint(s); xy, yaw = approach_pose(so, lat, ye)
        g = Grounder(s * 17, names, pos, xy, yaw)
        intended = names[s % len(names)]
        ev, ok, got = g.attempt(intended)
        if got is None: continue
        ev = dict(ev); ev["intended"] = intended
        out.append((ev, ok))
    return out


def auroc(p, y):
    p, y = np.asarray(p, float), np.asarray(y, int)
    m = np.isfinite(p); p, y = p[m], y[m]
    pos, neg = p[y == 1], p[y == 0]
    if not len(pos) or not len(neg): return float("nan")
    a = np.concatenate([pos, neg]); o = np.argsort(a); r = np.empty(len(a)); r[o] = np.arange(1, len(a) + 1)
    return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def ece(p, y, bins=10):
    p, y = np.asarray(p, float), np.asarray(y, int)
    m = np.isfinite(p); p, y = p[m], y[m]
    if not len(p): return float("nan")
    e = 0.0
    for i in range(bins):
        sel = (p >= i / bins) & (p < (i + 1) / bins if i < bins - 1 else p <= 1.0)
        if sel.sum(): e += sel.sum() / len(p) * abs(p[sel].mean() - y[sel].mean())
    return float(e)


def platt(p, y, iters=3000, lr=0.15):
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); y = np.asarray(y, float)
    z = np.log(p / (1 - p)); a, b = 1.0, 0.0
    for _ in range(iters):
        q = 1 / (1 + np.exp(-(a * z + b))); g = y - q
        a += lr * (g * z).mean(); b += lr * g.mean()
    return float(a), float(b)


def apply_ab(p, ab):
    a, b = ab; p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return 1 / (1 + np.exp(-(a * np.log(p / (1 - p)) + b)))


class Recal:
    """Any seat, wrapped in a two-parameter recalibration fitted on RECAL_N labels."""
    def __init__(self, inner, ab): self.inner = inner; self.ab = ab; self.last_p = None
    @property
    def calls(self): return self.inner.calls
    def verify(self, ev):
        try: raw = self.inner.prob(ev)
        except Exception: return False
        self.last_p = float(apply_ab(np.array([raw]), self.ab)[0])
        if ev["verifications_left"] <= 0: return False
        return expected_cost_says_verify(self.last_p, ev)


tr, te = labelled(TRAIN), labelled(TEST)
ytr = [int(o) for _, o in tr]; yte = [int(o) for _, o in te]
print(f"E196  sha={SHA}  train={len(tr)}  test={len(te)}  recal labels={RECAL_N}")
print(f"  grounding accuracy on the held-out bank: {np.mean(yte):.1%}\n")

lg = FittedLogistic().fit(tr)
pl = [lg.prob(e) for e, _ in te]
print(f"  control, logistic on {len(tr)} labels:  AUROC {auroc(pl, yte):.3f}  ECE {ece(pl, yte):.3f}\n")

H = (f"{'seat':<14}{'AUROC':>8}{'ECE raw':>10}{'ECE +25':>10}{'ms/call':>9}"
     f"{'cost raw':>10}{'cost +25':>10}{'irrev':>7}{'verifies':>10}")
print(H); print("-" * len(H), flush=True)
rows = []
for name, mk in seats():
    s = mk()
    pte, ptr = [], []
    for e, _ in te:
        try: pte.append(s.prob(e))
        except Exception: pte.append(float("nan"))
    for e, _ in tr[:RECAL_N]:
        try: ptr.append(s.prob(e))
        except Exception: ptr.append(float("nan"))
    m = [i for i, v in enumerate(ptr) if np.isfinite(v)]
    ab = platt([ptr[i] for i in m], [ytr[i] for i in m]) if m else (1.0, 0.0)
    pc = apply_ab([v if np.isfinite(v) else 0.5 for v in pte], ab)
    raw_recs = [episode(sd, s) for sd in TEST]
    cal_recs = [episode(sd, Recal(s, ab)) for sd in TEST]
    lat = np.mean(s.latency) * 1000 if getattr(s, "latency", None) else float("nan")
    print(f"{name:<14}{auroc(pte, yte):>8.3f}{ece(pte, yte):>10.3f}{ece(pc, yte):>10.3f}{lat:>9.0f}"
          f"{np.mean([r['cost'] for r in raw_recs]):>10.2f}{np.mean([r['cost'] for r in cal_recs]):>10.2f}"
          f"{sum(r['irreversible'] for r in cal_recs):>7}{sum(r['verifies'] for r in cal_recs):>10}", flush=True)
    if getattr(s, "errors", 0): print(f"    {s.errors} errors; first: {s.first_error}", flush=True)
    rows.append(dict(seat=name, auroc=auroc(pte, yte), ece_raw=ece(pte, yte), ece_cal=ece(pc, yte),
                     ms=lat, cost_raw=float(np.mean([r['cost'] for r in raw_recs])),
                     cost_cal=float(np.mean([r['cost'] for r in cal_recs])),
                     irrev_cal=sum(r['irreversible'] for r in cal_recs),
                     verifies_cal=sum(r['verifies'] for r in cal_recs), ab=ab, sha=SHA))
with open("results/table/e196.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
c = [r["cost_cal"] for r in rows]
print(f"\n  E196.4: after recalibration, costs span {min(c):.2f} to {max(c):.2f} "
      f"= {(max(c) - min(c)) / min(c):.0%} spread")

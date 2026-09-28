"""E197: a success detector that reads what the robot observed, against the ways it is done today."""
import json, os, subprocess, sys, time
import numpy as np
from typesafe_sdk import TypeSafeClient, Choice
from stack.detector import collect, derived, ARMS
from stack.ground_arms import FittedLogistic
from stack.e196_run import auroc, ece, platt, apply_ab

TRAIN_SEEDS = range(0, 50)
TEST_SEEDS = range(10_000, 10_025)
RECAL_N = 25
SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "nogit"

ROLE = ("You read the end-of-task report a warehouse robot files about itself. The report is written from what the robot "
        "believes, and its beliefs come from sensors that are sometimes wrong. You judge only whether the task was "
        "actually completed.")


class DetectorJev:
    def __init__(self, model=None):
        self.client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
        self.model = model or "jev-latest"
        self.calls = self.errors = 0; self.first_error = None; self.latency = []

    def prob(self, obs):
        state = {k: v for k, v in obs.items() if not k.startswith("_")}
        q = {"done": Choice(
            instructions={"role": ROLE, "ask": "Was the task actually completed?"},
            criteria={"completed": "Every object is where the task requires, and the report is consistent with that.",
                      "report_is_optimistic": "The robot reports finishing, but something in the sensor data is not "
                                              "consistent with the task actually being done.",
                      "not_completed": "The report itself shows the task is unfinished."})}
        t0 = time.time(); self.calls += 1
        a = self.client.system_one(state=state, model=self.model, questions=q).answers["done"]
        self.latency.append(time.time() - t0)
        pr = getattr(a, "probabilities", None) or {}
        return float(pr.get("completed", 1.0 if a.choice == "completed" else 0.0))


class TrustTheReport:
    """What is done today: take the robot's own word for it. Dong & Finn's 'hand-built per task' in its simplest form."""
    name = "trust_the_report"
    def prob(self, obs): return 1.0 if obs.get("robot_reports_finished") else 0.0


class LogisticDetector(FittedLogistic):
    FEATS = tuple(sorted(derived({}).keys()))
    @staticmethod
    def derive(obs): return derived(obs)


tr = collect(TRAIN_SEEDS); te = collect(TEST_SEEDS)
ytr = [y for _, y in tr]; yte = [y for _, y in te]
print(f"E197  sha={SHA}  train={len(tr)} episodes  test={len(te)}  recal labels={RECAL_N}")
print(f"  held-out success rate {np.mean(yte):.1%}; "
      f"the robot's own report is wrong on "
      f"{np.mean([float(o['robot_reports_finished']) != y for o, y in te]):.0%} of them\n")

H = f"{'detector':<22}{'labels':>8}{'accuracy':>10}{'AUROC':>8}{'ECE':>8}"
print(H); print("-" * len(H), flush=True)

tt = TrustTheReport()
pt = [tt.prob(o) for o, _ in te]
print(f"{'trust the report':<22}{0:>8}{np.mean([(p > .5) == y for p, y in zip(pt, yte)]):>10.1%}"
      f"{auroc(pt, yte):>8.3f}{ece(pt, yte):>8.3f}", flush=True)

lg = LogisticDetector().fit(tr)
pl = [lg.prob(o) for o, _ in te]
print(f"{'logistic (control)':<22}{len(tr):>8}{np.mean([(p > .5) == y for p, y in zip(pl, yte)]):>10.1%}"
      f"{auroc(pl, yte):>8.3f}{ece(pl, yte):>8.3f}", flush=True)

j = DetectorJev()
pj, pjt = [], []
for o, _ in te:
    try: pj.append(j.prob(o))
    except Exception as e:
        j.errors += 1; j.first_error = j.first_error or f"{type(e).__name__}: {e}"; pj.append(float("nan"))
for o, _ in tr[:RECAL_N]:
    try: pjt.append(j.prob(o))
    except Exception: pjt.append(float("nan"))
print(f"{'calibrated, zero-shot':<22}{0:>8}{np.mean([(p > .5) == y for p, y in zip(pj, yte) if np.isfinite(p)]):>10.1%}"
      f"{auroc(pj, yte):>8.3f}{ece(pj, yte):>8.3f}", flush=True)

m = [i for i, v in enumerate(pjt) if np.isfinite(v)]
ab = platt([pjt[i] for i in m], [ytr[i] for i in m]) if m else (1.0, 0.0)
pc = apply_ab([v if np.isfinite(v) else 0.5 for v in pj], ab)
print(f"{'calibrated + 25 labels':<22}{RECAL_N:>8}{np.mean([(p > .5) == y for p, y in zip(pc, yte)]):>10.1%}"
      f"{auroc(pc, yte):>8.3f}{ece(pc, yte):>8.3f}", flush=True)
print(f"\n  {j.calls} model calls, {j.errors} errors, {np.mean(j.latency)*1000:.0f} ms mean"
      + (f"; first: {j.first_error}" if j.first_error else ""))
with open("results/table/e197.jsonl", "w") as f:
    for (o, y), a, b, c, d in zip(te, pt, pl, pj, pc):
        f.write(json.dumps({"mode": o["_mode"], "arm": o["_arm"], "seed": o["_seed"], "truth": y,
                            "trust": a, "logistic": b, "jev_raw": c, "jev_cal": float(d), "sha": SHA}) + "\n")
print(f"wrote results/table/e197.jsonl ({len(te)} rows)")

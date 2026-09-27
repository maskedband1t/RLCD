"""E187: the decomposition is the variable. Plan, bench, seeds, body and model held fixed; only the question changes."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stack.table_run import episode
from stack.table_framings import TableJev
from stack.table_arms import TableRules, TableNullFast
from stack.table_plans import MINE_PLAN, MINE_CONT

HDR = f"{'framing':<14}{'success':>9}{'cleared':>9}{'broken':>7}{'viol':>6}{'falls':>7}{'calls':>7}{'err':>5}{'teleop x':>10}"
print(HDR); print("-" * len(HDR), flush=True)
rows = []


def run(label, arm):
    ok = clr = brk = viol = fell = 0; t = 0.0
    for seed in range(12):
        rec, _ = episode(seed, arm, MINE_PLAN, MINE_CONT)
        rec["framing"] = label; rows.append(rec)
        ok += rec["success"]; clr += rec["cleared"]; brk += rec["broken"]
        viol += rec["workspace_violations"]; fell += rec["fell"]; t += rec["t_end"]
    calls = getattr(arm, "calls", 0); err = getattr(arm, "errors", 0)
    print(f"{label:<14}{ok:>6}/12{clr:>7}/36{brk:>7}{viol:>6}{fell:>7}{calls:>7}{err:>5}{t/12/62.5:>10.2f}", flush=True)
    fe = getattr(arm, "first_error", None)
    if fe: print(f"    first error: {fe[:160]}", flush=True)


for fr in ("pick", "keys", "split", "step"):
    run(fr, TableJev(framing=fr))
run("rules (bar)", TableRules())
run("null_fast (floor)", TableNullFast())
os.makedirs("results/table", exist_ok=True)
with open("results/table/e187.jsonl", "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
print(f"\n  {len(rows)} episodes -> results/table/e187.jsonl")

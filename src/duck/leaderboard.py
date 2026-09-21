"""The duck bench leaderboard: every run in results/duck/*.jsonl, by representation version and arm."""
import json, glob, os, collections
import numpy as np
import sys; sys.path.insert(0, "src")
from cell.analyze import wilson
VERSION = {"e93": "R0", "e93b": "R0 (fixed instrument, τ=.5)", "e94": "R1", "e95": "R2 (judge void: API credits)", "e96": "R3 owned head (R2 options)", "e98": "R4 owned head + correction round (test seeds 70-99 = unseen bank, fresh seeds)", "e99": "R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99", "e100": "R5, head r4 with the operator notes hidden (note ablation, seeds 70-99)", "e101": "R6: head r6 = correction round with masked targets (the head's own probabilities inside the acceptable set), R5 instrument", "e102": "R5 instrument, the API teacher (jev) beside its copies, seeds 0-39 and 70-99", "e103a": "R7 (acceptable set with a progress clause): head r6 and baselines re-measured; the correction source", "e103": "R7: head r7 = correction round 2 (both banks, masked targets) on the progress-aware acceptable set", "e104": "R5 instrument, the open 27B (Featherless Simple Jev) beside the RLCD judge, seeds 0-39 and 70-99"}
lines = ["# Duck bench leaderboard", "", "Seeds 0–39 unless noted. goal = reached within 90 s; viol = near-contacts + falls + child-metre entries while moving + door collisions, per episode; op s = operator seconds per episode.", "",
         "| version | run | arm | n | goal | t to goal | viol/ep | near | op s | asks/ep | events handled |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for p in sorted(glob.glob("results/duck/e9*.jsonl")):
    run = os.path.basename(p)[:-6]
    if "record" in run: continue   # *_record.jsonl and *_records.jsonl are decision records / correction labels, not episodes
    by = collections.defaultdict(list)
    for l in open(p):
        r = json.loads(l); by[r["arm"]].append(r)
    known = ["rules", "rules_ask", "oracle", "jev", "jev_gate0.7", "jev_confirm0.7", "jev_gate0.5", "jev_confirm0.5", "sj", "laya", "laya_confirm0.5"]
    for arm in known + sorted(a for a in by if a not in known):   # tagged heads (laya-r3, laya-r4, ...) follow the known order
        rs = by.get(arm)
        if not rs: continue
        n = len(rs); g = sum(r["goal_reached"] for r in rs); _, lo, hi = wilson(g, n); tg = np.mean([r["t_goal"] for r in rs if r["goal_reached"]]) if g else float("nan")
        lines.append(f"| {VERSION.get(run, run)} | {run} | {arm} | {n} | {100*g/n:.0f} % [{100*lo:.0f}, {100*hi:.0f}] | {tg:.1f} s | {np.mean([r['violations'] for r in rs]):.2f} | {sum(r['near_contacts'] for r in rs)} | {np.mean([r['operator_seconds'] for r in rs]):.1f} | {np.mean([r['n_asks'] for r in rs]):.2f} | {sum(r['event_correct'] for r in rs)}/{n} |")
open("results/duck/LEADERBOARD.md", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))

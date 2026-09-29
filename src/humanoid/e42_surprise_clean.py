"""S1-E42 -- S1-E41's result, run clean: same seeds for every arm, and the per-episode costs normalised.

S1-E41 found that escalating on prediction error took the worst arm to the best. Two things make that claim
weaker than it reads, and neither is a criticism of the finding -- they are the reason to re-run it:

  1. **The surprise arm ran on 4 seeds; every other arm on 10.** With n = 4 a success rate is quantised to
     0/25/50/75/100 %, and 4-of-4 carries a Wilson interval reaching down to about 51 %. The comparison
     against a 10-seed 60 % cannot be read off the point estimates.
  2. **`violations`, `operator_seconds` and `calls` are raw SUMS over episodes** (`kitchen_run.run`), while
     `success`, `cleared` and `steps` are normalised. So "2 violations, fewer than the always-right
     ceiling's 3" compares 2-over-4-episodes with 3-over-10 -- **0.50 per episode against 0.30.** Normalised,
     the surprise arm has MORE violations than the ceiling, not fewer, and the direction of that claim
     inverts.

This file changes nothing about the mechanism. It runs every arm on the same seeds and divides by n.

The planner is switched off rather than allowed to fail: S1-E41's arm was labelled `xplanner+rules` and got
its clean single-variable comparison **because** X-Planner failed all 45 plans, and a discarded plan narrows
no options. `plan_enabled=False` makes that configuration explicit, which also removes the llama calls that
limited it to 4 seeds in the first place. `_predict`/`observe` are reused, not copied.
"""
import os
import sys
import time

import numpy as np

from cell.analyze import wilson
from humanoid.kitchen_run import ARMS, NAMES, episode

SEEDS = [int(x) for x in os.environ.get("SEEDS", "0,1,2,3,4,5,6,7,8,9").split(",")]
ARM_LIST = os.environ.get("ARMS", "rules,rules_note,oracle,rules+surprise,rules_note+surprise").split(",")


def run_arm(name, seeds):
    make = ARMS[name]
    rows = []
    t0 = time.time()
    for s in seeds:
        rows.append(episode(s, make()))
    n = len(rows)
    succ = sum(1 for r in rows if r["success"])
    p, lo, hi = wilson(succ, n)
    return {
        "arm": name, "n": n,
        "success": succ, "success_p": p, "lo": lo, "hi": hi,
        "cleared": sum(r["cleared"] for r in rows) / (n * len(NAMES)),
        "falls": sum(1 for r in rows if r["fell"]) / n,
        # normalised, which is the whole point of this file
        "viol_per_ep": sum(r["violations"] for r in rows) / n,
        "ops_per_ep": sum(r["operator_seconds"] for r in rows) / n,
        "calls_per_ep": sum(r["calls"] for r in rows) / n,
        "steps": float(np.mean([r["decisions"] for r in rows])),
        "secs": round(time.time() - t0, 1),
        "rows": rows,
    }


def main():
    print(f"S1-E42 -- every arm on the SAME {len(SEEDS)} seeds, costs per episode\n")
    print(f"{'arm':<22}{'success':>9}{'95% CI':>16}{'cleared':>10}{'viol/ep':>9}{'op s/ep':>9}"
          f"{'calls/ep':>10}{'steps':>8}")
    print("-" * 93)
    out = []
    for a in ARM_LIST:
        r = run_arm(a, SEEDS)
        out.append(r)
        print(f"{a:<22}{r['success']}/{r['n']:<7}{f'[{r['lo']:.2f}, {r['hi']:.2f}]':>16}"
              f"{r['cleared']:>9.0%}{r['viol_per_ep']:>9.2f}{r['ops_per_ep']:>9.1f}"
              f"{r['calls_per_ep']:>10.1f}{r['steps']:>8.0f}   [{r['secs']}s]", flush=True)

    # The comparison the result rests on, stated as an interval rather than two point estimates.
    base = next((r for r in out if r["arm"] == "rules"), None)
    surp = next((r for r in out if r["arm"] == "rules+surprise"), None)
    if base and surp:
        print(f"\n  rules            {base['success']}/{base['n']}  CI [{base['lo']:.2f}, {base['hi']:.2f}]")
        print(f"  rules+surprise   {surp['success']}/{surp['n']}  CI [{surp['lo']:.2f}, {surp['hi']:.2f}]")
        overlap = not (surp["lo"] > base["hi"] or base["lo"] > surp["hi"])
        print(f"  => intervals {'OVERLAP -- the difference is not established at this n' if overlap else 'are disjoint -- the difference survives'}")
    return out


if __name__ == "__main__":
    main()

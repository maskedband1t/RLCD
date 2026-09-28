"""Capture everything needed to train and improve, in one pass.

Written 2026-09-28, after S1-E15 showed the failure that matters is a LIVELOCK -- repetition without
progress -- and that confidence does not see it (0.52-0.66 throughout a 37-second livelock, and 0.94 on
the worst decision of the episode). So a capture that stores only (state, action, confidence) cannot
support the thing we now know we need to detect. Every record here carries trajectory context.

Four training targets this feeds, all from the same pass:

  1. A REPLACEMENT HEAD      expert demonstrations from the oracle, recorded on the CORRECTED bench.
                             The current head was distilled on ghost geometry and is worthless here
                             (S1-E14: 10% correct, 80% falls).
  2. A STALENESS DETECTOR    per-decision progress features: how long since the world changed, how long
                             since this action changed anything, run-length of the current action.
  3. A VALUE / RISK MODEL    outcome fields: did this episode fall, how many violations followed, how far
                             from the end, plus the skill table's fast+close risk context.
  4. A CALIBRATOR            confidence against ground-truth acceptability, so the 0.94-on-a-wrong-answer
                             case is measurable rather than anecdotal.

  PYTHONPATH=src USE_TF=0 DUCK_BODY=g1 DUCK_CONTACT=1 DUCK_CONTACT_PROPS=all DUCK_TABLE_STANDOFF=1.05 \
  python src/duck/capture.py --arms oracle,jev,laya,rules --seeds 40-59 --out results/duck/train.jsonl
"""
import os, sys, json, time, argparse
from collections import deque

sys.path.insert(0, "src")


def run(arms, seeds, out):
    from duck import e93_run as R
    import numpy as np
    n_rows = 0
    t0 = time.time()
    with open(out, "a") as fh:
        for arm_name in arms:
            for seed in seeds:
                rec = []
                o = R.episode(seed, arm_name, record=rec)
                log = o["log"]
                # ---- trajectory features, computed after the fact over the whole episode ----
                persd = [p for (_t, _k, p, _c, _ok) in log]
                keys = [k for (_t, k, _p, _c, _ok) in log]
                n = len(log)
                since_world_change = 0
                run_len = 0
                for i, (t, k, pd, conf, ok) in enumerate(log):
                    # how long has the person's distance been effectively frozen?
                    if i > 0 and abs(persd[i] - persd[i - 1]) < 0.10:
                        since_world_change += 1
                    else:
                        since_world_change = 0
                    # how many times in a row has this same action been chosen?
                    run_len = run_len + 1 if (i > 0 and keys[i] == keys[i - 1]) else 0
                    # how much of the REMAINING episode is the same action? (livelock, seen from the end)
                    tail = keys[i:]
                    tail_same = sum(1 for x in tail if x == k) / max(len(tail), 1)
                    fh.write(json.dumps({
                        "arm": arm_name, "seed": seed, "event": o["event"],
                        "i": i, "t": t, "n_decisions": n,
                        "action": k, "acceptable": bool(ok), "confidence": conf,
                        "person_dist": pd,
                        # --- staleness / livelock features (target 2) ---
                        "frozen_steps": since_world_change,
                        "action_run_length": run_len,
                        "same_action_fraction_of_tail": round(tail_same, 3),
                        "steps_remaining": n - i - 1,
                        # --- outcome fields (target 3) ---
                        "episode_fell": bool(o["fell"]),
                        "episode_violations": o["violations"],
                        "episode_correct": bool(o["event_correct"]),
                        "episode_delivered": o["delivered_to"] is not None,
                        "episode_operator_s": o["operator_seconds"],
                        # --- expert flag (target 1) ---
                        "is_expert": arm_name == "oracle",
                    }) + "\n")
                    n_rows += 1
                fh.flush()
            el = time.time() - t0
            print(f"  {arm_name:<8} done · {n_rows} decisions captured · {el:.0f}s", flush=True)
    print(f"\ncaptured {n_rows} decision records -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default="oracle,jev,laya,rules")
    ap.add_argument("--seeds", default="40-59")
    ap.add_argument("--out", default="results/duck/train.jsonl")
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-")
    seeds = list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    run(a.arms.split(","), seeds, a.out)

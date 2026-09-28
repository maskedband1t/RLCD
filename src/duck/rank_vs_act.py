"""Does a model RANK better, or merely ACT better? They are different products.

CLM-8B scores 65% task-correct against the calibrated arm's 35% when it drives (S1-E14). That is an
ACTING result: each arm visits its own states, so the comparison confounds judgement with trajectory.
This scores models on IDENTICAL states with no acting at all.

States come from oracle rollouts, so every model is judged on the same expert trajectory rather than on
the mess its own choices produced. Metrics:

  top1        does the argmax fall inside the ground-truth acceptable set
  auroc       does P(top choice) separate acceptable decisions from unacceptable ones
  ece         is the reported confidence calibrated

  stage 1:  PYTHONPATH=src python src/duck/rank_vs_act.py states --seeds 40-59 --out results/duck/states.jsonl
  stage 2:  PYTHONPATH=src python src/duck/rank_vs_act.py score --arm laya --out results/duck/rank_laya.jsonl
"""
import os, sys, json, argparse, time
sys.path.insert(0, "src")


def collect(seeds, out):
    from duck import e93_run as R
    n = 0
    with open(out, "a") as fh:
        for s in seeds:
            rec = []
            o = R.episode(s, "oracle", record=rec)
            # episode() only records when the arm reports probabilities, so replay for states instead
            from humanoid.fetch_sim import Room
            room = Room(s); room.physics(int(1.0 / room.cdt))
            arm = R.make_arm("oracle")
            for _ in range(240):
                f = room.facts(); opts = room.options(); acc = sorted(room.acceptable())
                if not opts: break
                key, _ = arm.decide(f, opts, room)
                fh.write(json.dumps({"seed": s, "event": room.event, "state": f,
                                     "options": opts, "acceptable": acc,
                                     "oracle_choice": key}) + "\n")
                n += 1
                if key == "done": break
                room.run_skill(key)
                if room.fallen(): break
            fh.flush()
            print(f"  seed {s}: {n} states so far", flush=True)
    print(f"collected {n} states -> {out}")


def score(arm_name, states_path, out):
    from duck.e93_run import make_arm
    arm = make_arm(arm_name)
    rows = [json.loads(l) for l in open(states_path)]
    n = 0
    t0 = time.time()
    with open(out, "a") as fh:
        for r in rows:
            try:
                key, j = arm.decide(r["state"], r["options"], None)
            except Exception as e:
                fh.write(json.dumps({"seed": r["seed"], "error": str(e)[:100]}) + "\n"); continue
            probs = j.get("probabilities") or {}
            acc = set(r["acceptable"])
            fh.write(json.dumps({
                "arm": arm_name, "seed": r["seed"], "event": r["event"],
                "choice": key, "correct": key in acc,
                "confidence": j.get("confidence"),
                "p_acceptable": round(sum(v for k, v in probs.items() if k in acc), 4) if probs else None,
                "n_options": len(r["options"]), "n_acceptable": len(acc),
                "oracle_choice": r["oracle_choice"],
            }) + "\n")
            n += 1
            if n % 100 == 0:
                print(f"  {n}/{len(rows)} scored · {time.time()-t0:.0f}s", flush=True)
            fh.flush()
    print(f"scored {n} states with {arm_name} -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["states", "score"])
    ap.add_argument("--seeds", default="40-59")
    ap.add_argument("--arm", default="laya")
    ap.add_argument("--states", default="results/duck/states.jsonl")
    ap.add_argument("--out", default="results/duck/states.jsonl")
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-")
    seeds = list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    os.makedirs("results/duck", exist_ok=True)
    if a.cmd == "states":
        collect(seeds, a.out)
    else:
        score(a.arm, a.states, a.out)

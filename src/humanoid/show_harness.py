"""Show the harness working, one decision at a time, with every layer visible.

This prints what each layer of the stack actually does on a real episode of the kitchen bench --
what the robot believes, which options the code offers it, what the chooser picks, what the plan
predicted should happen, and whether the world agreed. Nothing here is a mock: it is the same
`episode()` loop the experiments run, with the internals printed instead of aggregated.

  PYTHONPATH=src python src/humanoid/show_harness.py --arm rules+surprise --seed 2
"""
import argparse
import sys

from humanoid.kitchen_run import ARMS
from humanoid.kitchen_task import ASK_S, MAX_T, KitchenTask

W = 100


def rule(ch="-"):
    print(ch * W)


def short(v, n=58):
    s = str(v)
    return s if len(s) <= n else s[: n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="rules+surprise")
    ap.add_argument("--seed", type=int, default=2)
    ap.add_argument("--max-steps", type=int, default=22)
    a = ap.parse_args()

    room = KitchenTask(seed=a.seed)
    arm = ARMS[a.arm]()

    rule("=")
    print(f"  THE HARNESS, one decision at a time   ·   arm = {a.arm}   seed = {a.seed}")
    rule("=")
    print("""
  Five layers, and the point of the design is that each one can be measured separately:

    PLANNER    holds the goal and the order                      (System 2)
    ENUMERATOR code decides which options legally exist here     <- the safety boundary
    CHOOSER    picks one option, reports confidence              (System 1 / the calibrated seat)
    EXECUTOR   runs the skill on the body                        (motion + control)
    PREDICTOR  says what the world SHOULD look like after        <- the world model
    RECORDER   compares prediction to reality; a mismatch is the cue to spend a human
""")

    ops = 0.0
    pending = None
    n = 0
    asks = 0
    surprises = 0

    while room.t < MAX_T and not room.fell and n < a.max_steps:
        f, opts = room.facts(), room.options()
        acc = room.acceptable()

        rule()
        print(f"  DECISION {n}        t = {room.t:6.1f}s")
        rule()

        # ---- what the robot believes
        held = f.get("holding", "nothing")
        print(f"  BELIEF      holding: {held}")
        for k in ("counter", "bin", "task"):
            if k in f:
                print(f"              {k}: {short(f[k])}")

        # ---- what code allows
        print(f"\n  ENUMERATOR  {len(opts)} legal option(s) -- code decides this, not the model:")
        for o in sorted(opts):
            mark = "  <- acceptable" if o in acc else ""
            print(f"                {o}{mark}")

        if pending is not None:
            key, pending = pending, None
            print(f"\n  CHOOSER     (operator's answer from the last escalation) -> {key}")
        else:
            key, _ = arm.decide(f, opts, room)
            if key == "ask_operator":
                ops += ASK_S
                asks += 1
                room.run_skill("ask_operator")
                pending = sorted(acc)[0]
                print(f"\n  CHOOSER     -> ask_operator   (spends {ASK_S}s of a human's attention)")
                print(f"  OPERATOR    answers: {pending}")
                n += 1
                continue
            if key not in opts:
                key = "stop"
            print(f"\n  CHOOSER     -> {key}")

        # ---- what the world model expects
        expected = getattr(arm, "_expected", None)
        if key == "done":
            room.declared_done = True
            print("\n  EXECUTOR    declares the job finished.")
            n += 1
            break

        room.run_skill(key)
        print(f"  EXECUTOR    ran {key} on the body")

        after = room.facts()
        if expected and expected[1]:
            pred = expected[1]
            agreed = all(str(after.get(k)) == str(v) for k, v in pred.items())
            pretty = ", ".join(f"{k} == {v}" for k, v in pred.items())
            print(f"\n  PREDICTOR   expected: {pretty}")
            print(f"  REALITY     {'matches.' if agreed else 'DOES NOT MATCH -> SURPRISE'}")
            if not agreed:
                got = ", ".join(f"{k} == {after.get(k)}" for k in pred)
                print(f"              got: {got}")

        if hasattr(arm, "observe") and arm.observe(room.facts()):
            surprises += 1
            ops += ASK_S
            asks += 1
            room.run_skill("ask_operator")
            pending = sorted(room.acceptable())[0]
            print(f"  RECORDER    prediction error -> escalate. Spends {ASK_S}s of a human.")
            print(f"  OPERATOR    answers: {pending}")

        n += 1
        if room.succeeded():
            print("\n  >> task complete")
            break

    rule("=")
    rec = room.record() if hasattr(room, "record") else {}
    print(f"  {n} decisions · {asks} asks · {ops:.0f} operator-seconds · {surprises} surprises · "
          f"cleared {len(room.cleared)} · t = {room.t:.0f}s")
    print("  Every one of those columns is a thing the experiments score separately.")
    rule("=")


if __name__ == "__main__":
    main()

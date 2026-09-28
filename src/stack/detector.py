"""E197: does a success detector cost 25 labels per task?

WHY THIS EXPERIMENT AND WHY NOW. Dong & Finn, 23 September: *"In LLM RL, reinforcement learning from verifiable rewards
gave the field a default answer: check the answer, check the tests. Robotics has no equivalent."* And immediately:
*"Today, success detectors are either hand-built per task or replaced by a human watching each trajectory and calling it,
neither of which scales."* That is the gap, named by Chelsea Finn's group, four days before this was written.

THE FLAW IN THE OBVIOUS VERSION, stated before it cost anything. With the simulator supplying typed facts, whether an
episode succeeded is COMPUTABLE -- three objects in the tray, nothing broken, nobody crowded. A detector reading those
fields has nothing to judge, and this would be the fourth bench in three days where a zero-model arm wins.

So the detector reads what the ROBOT OBSERVED, not what happened. Under the ghost modes the robot's own belief says the
box is in the tray while it sits on the table, so a detector reading the robot's report sees a finished task and the
truth is a failure. That is exactly the case a human watching the trajectory would catch and a hand-built field check
would not, which is the case Dong & Finn are describing. The label is the simulator's exact outcome, so it costs nothing
to collect -- which is the point: if 25 labels suffice, the detector is per-task-cheap rather than per-task-built."""
import numpy as np

from humanoid.table_sim import TableRoom
from stack.percept import Perceived, options_with_look, MODES, CHANNEL
from stack.table_run import episode
from stack.percept_arms import NullTrust, Code3, CodeAll, AlwaysVerify
from stack.table_plans import MINE_PLAN, MINE_CONT

ARMS = [("null_trust", NullTrust), ("code_3", Code3), ("code_all", CodeAll), ("always_verify", AlwaysVerify)]


def observed_summary(room, rec):
    """What the robot would report at the end, from its own beliefs. The truth is deliberately absent."""
    believed_cleared = sorted(room.cleared)                 # the proxy's view: includes the ghost
    still_listed = sorted(room.remaining())
    ev = room.evidence()
    return {
        "task": "Clear every object from the table into the tray.",
        "robot_reports_finished": bool(not still_listed),
        "objects_the_robot_believes_it_cleared": believed_cleared,
        "objects_the_robot_still_expects_to_clear": still_listed,
        "robot_is_upright": not bool(rec["fell"]),
        "seconds_taken": round(rec["t_end"], 1),
        "times_it_re_examined_a_reading": int(room.looks),
        "sensor_report_at_the_end": ev,
    }


def collect(seeds, arms=None, verbose=False):
    """(observed summary, did it ACTUALLY succeed). The label is exact and free: no annotator, no human watching."""
    out = []
    for name, mk in (arms or ARMS):
        arm = mk()
        for s in seeds:
            room = Perceived(TableRoom(s), s)
            rec, _ = episode(s, arm, MINE_PLAN, MINE_CONT, room=room,
                             opts_fn=options_with_look, recover=True)
            obs = observed_summary(room, rec)
            obs["_arm"] = name; obs["_mode"] = room.mode; obs["_seed"] = s
            out.append((obs, int(rec["success"])))
            if verbose:
                print(f"  {name:<14} seed {s:>3} mode {room.mode:<18} "
                      f"robot says finished={obs['robot_reports_finished']}  truth={rec['success']}", flush=True)
    return out


def derived(obs):
    """Features a code detector could compute from the same observed report. The control gets everything the model gets."""
    ev = obs.get("sensor_report_at_the_end") or {}
    rows = ev.get("objects") or []
    return {
        "reports_finished": float(obs.get("robot_reports_finished", False)),
        "n_believed_cleared": float(len(obs.get("objects_the_robot_believes_it_cleared") or [])),
        "n_still_expected": float(len(obs.get("objects_the_robot_still_expects_to_clear") or [])),
        "upright": float(obs.get("robot_is_upright", True)),
        "seconds": float(obs.get("seconds_taken", 0.0)),
        "looks": float(obs.get("times_it_re_examined_a_reading", 0)),
        "min_detections": float(min([r.get("times_detected", 1) for r in rows], default=1)),
        "max_position_age": float(max([r.get("position_age_s", 0.0) for r in rows], default=0.0)),
        "min_confidence": float(min([r.get("detector_confidence", 1.0) for r in rows], default=1.0)),
        "objects_in_report": float(len(rows)),
        "people_reported": float(ev.get("people_reported", 0)),
        "motion_flag": float(str(ev.get("motion_sensor", "")).startswith("movement")),
    }


def dose(seeds=range(10)):
    """A detector needs both outcomes present, AND cases where the robot's own report disagrees with the truth.
    If the robot's report always matches reality there is nothing for any detector to add."""
    rows = collect(seeds)
    y = [o for _, o in rows]
    disagree = [(s, o) for s, o in rows if float(s["robot_reports_finished"]) != float(o)]
    print(f"  {len(rows)} episodes: {sum(y)} succeeded, {len(y) - sum(y)} failed")
    print(f"  episodes where the ROBOT'S OWN REPORT disagrees with the truth: {len(disagree)} "
          f"({len(disagree) / max(1, len(rows)):.0%})")
    from collections import Counter
    c = Counter(s["_mode"] for s, _ in disagree)
    print(f"  which modes produce the disagreement: {dict(c)}")
    ok = 0 < sum(y) < len(y) and len(disagree) >= 0.10 * len(rows)
    print(f"  dose gate: {'PASS' if ok else 'FAIL'}")
    return ok, rows


if __name__ == "__main__":
    dose()

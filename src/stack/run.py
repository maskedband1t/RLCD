"""Run one episode through the four-layer stack, with every layer named in the record so any of them can be ablated."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.fetch_sim import Room
from duck.e93_run import make_arm
from stack.layers import (ScriptPlanner, StalePlanner, ReplanPlanner, CodeEnumerator, DroppedEnumerator,
                          NoisyEnumerator, VLMEnumerator, Library2Enumerator, PlannedLibrary2Enumerator, ConstrainedEnumerator, ValidatedEnumerator, FreeOperator, QueuedOperator)

PLANNERS = {"script": ScriptPlanner, "stale": StalePlanner, "replan": ReplanPlanner}
try:
    from stack.planner import GoalPlanner; PLANNERS["goal"] = GoalPlanner
except Exception: pass
MAX_T = 120.0

import datetime as _dt, subprocess as _sp
RUN_ID = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
try: GIT_SHA = _sp.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5).stdout.strip() or "?"
except Exception: GIT_SHA = "?"

def _oracle2():
    from stack.skills2 import Oracle2; return Oracle2()

def build_enum(spec, seed=0):
    if spec == "lib2": return Library2Enumerator()
    if spec == "lib2planned": return PlannedLibrary2Enumerator()
    if spec == "code": return CodeEnumerator()
    if spec.startswith("code/"): return CodeEnumerator(docs=spec.split("/", 1)[1])
    if spec.startswith("vlm"): return VLMEnumerator(prompt=spec.split("/", 1)[1] if "/" in spec else "facts")
    if spec.startswith("drop1x"): return DroppedEnumerator(float(spec[6:]), seed=seed, mode="one")
    if spec.startswith("drop"): return DroppedEnumerator(float(spec[4:]), seed=seed, mode="all")
    if spec.startswith("noise"): return NoisyEnumerator(float(spec[5:]), seed=seed)
    if spec.startswith("constrained:"):
        rest = spec.split(":", 1)[1]; inner, _, m = rest.partition("@")
        return ConstrainedEnumerator(build_enum(inner, seed), min_m=float(m or 0.5))
    if spec.startswith("validated:"):
        rest = spec.split(":", 1)[1]
        inner, _, fb = rest.partition("|")
        return ValidatedEnumerator(build_enum(inner, seed), fallback=fb or "stop")
    raise SystemExit(f"unknown enumerator {spec}")

def build_op(spec):
    if spec == "free": return FreeOperator()
    if spec.startswith("queue"):
        fleet, rate = spec[5:].split("@"); return QueuedOperator(int(fleet), float(rate))
    raise SystemExit(f"unknown operator {spec}")

def episode(seed, arm_name, planner_name="script", enum_spec="code", op_spec="free", record=None, max_dec=0, lib="v1"):
    """Mirrors duck.e93_run.episode exactly, with the four seams inserted. Verified to reproduce it seed for seed."""
    room = Room(seed); arm = make_arm(arm_name) if not (lib == "v2" and arm_name == "oracle") else _oracle2()
    # v2 differs from v1 in exactly three places: where the acceptable set comes from, what executes an action, and what
    # the fallback action is called. Everything else -- the settle, the cadence, the operator hold -- is shared, because
    # duplicating this function is how two experiments end up under one label.
    if lib == "v2":
        from stack.skills2 import acceptable2, key_to_bound, run2
        _acc = lambda: acceptable2(room); _run = lambda k: run2(room, key_to_bound(k, room)); _idle = "stand(seconds=0.5)"
        _walking = lambda k: k.startswith("move_to(") and "speed=normal" in k
        _slow = lambda k: k.startswith("move_to(") and "speed=slow" in k
    else:
        _acc = lambda: room.acceptable(); _run = lambda k: room.run_skill(k); _idle = "stop"
        _walking = lambda k: k in ("walk_fast", "walk"); _slow = lambda k: k == "walk_slow"
    planner = PLANNERS[planner_name](); enum = build_enum(enum_spec, seed=10_000 + seed); op = build_op(op_spec)
    plan = planner.plan(room); sub = plan[0] if plan else None
    room.physics(int(1.0 / room.cdt))          # one second to settle on the standing policy, as the original does
    goal = False; n = acc_ok = 0; pending = None; replans = 0; DEC = 0.5; picks = {}
    capped = False
    while room.t < MAX_T and not room.fell:
        if max_dec and n >= max_dec: capped = True; break   # censoring, recorded; a paralysed episode must not burn an
                                                            # hour of model calls, and 3x the oracle's normal length is
                                                            # unambiguously a failing episode already
        if hasattr(planner, "current"): sub = planner.current(room)
        f = room.facts(); opts = enum.options(room, f, sub); acc = _acc()
        if not opts: break
        _probs = None
        if pending is not None:
            key = pending; pending = None
            for _ in range(int(round(getattr(room, "OPERATOR_HOLD_S", DEC) / DEC)) - 1): _run(key)
        else:
            key, _m = arm.decide(f, opts, room)
            _probs = (_m if isinstance(_m, dict) and all(isinstance(v, (int, float)) for v in _m.values())
                      else None)                       # a rule program states no probability; record None, never a fake 1.0
            if key not in opts: key = _idle
        n += 1; acc_ok += int(key in acc); picks[key] = picks.get(key, 0) + 1
        room.recent.append(f"t={room.t:.0f}s: {key}")
        room.cmd = (0.12 if _walking(key) else 0.06 if _slow(key) else 0.0, 0.0)
        rec = None
        if record is not None:
            from stack.record import open_record, close_record
            rec = open_record(seed, room, f, opts, key, _probs, acc, arm_name, enum.name, planner_name, op.name, sub)
            rec["unresolved_proposals"] = getattr(enum, "unresolved", None)
            record.append(rec)
        if key == "ask_operator":
            wait, served = op.ask(room.t)
            for _ in range(int(round(wait / DEC))): _run(_idle if lib == "v2" else "wait")
            _run("ask_operator")
            if rec is not None: close_record(rec, room)
            if served: pending = (_oracle2() if lib == "v2" else make_arm("oracle")).decide(
                room.facts(), enum.options(room, room.facts(), sub), room)[0]
            else:
                nxt = planner.replan(room, sub, "unachievable")
                if nxt: plan = nxt; sub = plan[0]; replans += 1
            continue
        if key == "done":
            room.declared_done = True; goal = room.goal_dist() < 0.25
            if rec is not None: close_record(rec, room)
            break
        _run(key)
        if rec is not None: close_record(rec, room)
        if room.goal_dist() < 0.25 and not goal: goal = True
    return {"run": RUN_ID, "sha": GIT_SHA,            # method error 60: two runs were once filed under one label,
                                                     # indistinguishable. Every row now carries when and from what code.
            "seed": seed, "arm": arm_name, "planner": planner_name, "enumerator": enum.name, "operator": op.name,
            "event": room.event, "handled": bool(room.event_correct(goal)),
            "t_end": round(room.t, 2), "decisions": n, "acceptable_decisions": acc_ok,
            "operator_asks": op.asks, "operator_wait_s": round(op.waited, 1), "operator_dropped": op.dropped,
            "replans": replans, "wrong_handovers": room.wrong_handovers, "fell": int(room.fell), "picks": picks,
            "enum_calls": getattr(enum, "calls", None), "enum_fallbacks": getattr(enum, "fallbacks", None),
            "enum_kept": getattr(enum, "kept", None), "enum_rejected": getattr(enum, "rejected", None),
            "enum_fired": getattr(enum, "fired", None), "enum_blocked": getattr(enum, "blocked", None),
            "near_contacts": room.near_contact_events, "child_zone": room.child_zone_events,
            "door_collisions": room.door_collisions,
            "enum_unresolved": getattr(getattr(enum, "inner", enum), "unresolved", None),
            "enum_proposed": getattr(getattr(enum, "inner", enum), "proposed", None), "capped": int(capped), "library": lib, "plan_advances": getattr(planner, "advances", None)}

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-dec", type=int, default=0)
    ap.add_argument("--library", default="v1", choices=["v1", "v2"])
    ap.add_argument("--seeds", default="0-9"); ap.add_argument("--arms", nargs="+", default=["oracle"])
    ap.add_argument("--planner", default="script"); ap.add_argument("--enum", default="code")
    ap.add_argument("--operator", default="free"); ap.add_argument("--out", default=None)
    # per-DECISION records, in the shape duck/correction.py and the five learned heads already consume. The keys are
    # Bound.key from the declared contract, so a correction record can finally be joined to a skill.
    ap.add_argument("--record", default=None)
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split("-"))
    fo = open(a.out, "a") if a.out else None
    fr = open(a.record, "a") if a.record else None
    for arm in a.arms:
        for s in range(lo, hi + 1):
            recs = [] if fr else None
            r = episode(s, arm, a.planner, a.enum, a.operator, record=recs, max_dec=a.max_dec, lib=a.library)
            if fr:
                for x in recs: fr.write(json.dumps(x) + "\n")
                fr.flush()
            line = (f"  {arm:<12} {r['enumerator']:<18} {r['operator']:<14} seed {s:<4} {r['event']:<16} "
                    f"{'OK ' if r['handled'] else 'miss'} t {r['t_end']:6.1f} dec {r['decisions']:>4} "
                    f"acc {r['acceptable_decisions']:>4} asks {r['operator_asks']:>2} wait {r['operator_wait_s']:>5.1f}s "
                    f"dropped {r['operator_dropped']}")
            print(line, flush=True)
            if fo: fo.write(json.dumps(r) + "\n"); fo.flush()
    print("STACK_DONE", flush=True)

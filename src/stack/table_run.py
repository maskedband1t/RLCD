"""One long-horizon episode, end to end: System Two's plan, code's assumption monitor, System One's choice, the body.

The division of labour, and it is the whole point:
  System Two   names the ORDER of the work and the assumptions each step rests on. Called once, then only when an
               assumption actually breaks. Slow and expensive, so it must be woken rarely.
  the monitor  re-evaluates every assumption of the live step at 2 Hz, in code, with no model call. This is the piece
               HomeBody does not have: their five skills each carry a prose `reason` that IS a precondition, written by
               the VLM and checked by nobody, and E171 measured what prose is worth to a downstream model.
  System One   picks HOW, from a handful of options code enumerated for the live goal: full speed or slow, stand and
               wait, back away from someone, or ask. Half a second, a hundredth of a cent.
  the body     the G1 and its shipped walking policy, unchanged from bench 3.

When an assumption breaks, the monitor tries a contingency the planner supplied for a currently-active trigger; failing
that it raises a replan request, which is the only thing that wakes System Two mid-task.
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.table_sim import TableRoom, TELEOP_REF_S, MAX_T_TABLE

DEC = 0.5


def options_for(room, goal, speed=None):
    """The option set for the live goal. Small by construction: the plan has already chosen WHERE, so what is left to
    choose is how fast, whether to yield, and whether to escalate."""
    out = {}
    if goal.startswith("pick:"):
        obj = goal.split(":", 1)[1]
        if room.table_reach() or (obj in room.placed_at and room.dist(room.obj_xy(obj)) < 1.0):
            out[f"pick(object={obj})"] = f"Pick up the {obj}."
        else:
            out["move_to(place=table,speed=normal)"] = "Walk to the table at normal speed."
            out["move_to(place=table,speed=slow)"] = "Walk to the table slowly."
    elif goal == "place":
        if room.tray_reach():
            out["place()"] = "Put down what you are holding, here at the tray."
        else:
            out["move_to(place=tray,speed=normal)"] = "Carry it to the tray at normal speed."
            out["move_to(place=tray,speed=slow)"] = "Carry it to the tray slowly."
    elif goal == "done":
        out["done()"] = "Declare the task finished."
    # METHOD ERROR 71: the planner's prompt says a step "may carry speed: slow or normal to constrain how the robot
    # walks during that step", and the runner ignored the field -- so Opus's plan was scored with its own safety
    # constraints stripped out (it pinned every glass carry to slow) and took 4 falls against the hand-written plan's 1.
    # A plan-level speed constraint narrows what the chooser may pick; that is the plan doing its job, not overreach.
    if speed in ("slow", "normal"):
        keep = {k: v for k, v in out.items() if "speed=" not in k or f"speed={speed}" in k or "away:" in k}
        if any("speed=" in k for k in keep): out = keep
    out["stand(seconds=2.0)"] = "Stand still for two seconds."
    for p in room.people:                                   # yielding is always the chooser's own call
        if room.dist(p.xy) < 2.5:
            out[f"move_to(place=away:{p.name},speed=slow)"] = f"Back away from {p.name}."
    out["ask_operator()"] = "Ask the remote operator what to do."
    return out


def step_done(room, goal):
    # A step is done when the robot BELIEVES it is done. For pick, that means holding the object -- or already having
    # put it in the tray, which is how a plan step gets skipped rather than repeated. Reading belief here rather than
    # ground truth is not a concession to E192: a robot that thinks the box is in the tray does not try to pick it, and
    # the previous version could only ever run the plan to completion no matter what it had been told.
    if goal.startswith("pick:"):
        o = goal.split(":", 1)[1]
        return room.holding == o or room.placed_at.get(o) == "tray"
    if goal == "place": return room.holding is None
    if goal == "done": return bool(room.declared_done)
    return True


def step_impossible(room, goal):
    """Distinct from an assumption breaking: the goal itself can no longer be achieved at all."""
    if goal.startswith("pick:"):
        o = goal.split(":", 1)[1]
        return o in room.broken or o in room.removed or (room.holding is not None and room.holding != o)
    return False


RECOVER_CAP = 2         # second chances per episode, counted and reported


def recover_missing(room, steps, i):
    """Give a plan back a step it skipped on a belief that has since been corrected.

    E192b's first run found something sharper than a bug: `code_3` detected the corruption on 34 occasions and scored
    exactly what `null_trust` scored while trusting everything. Detection earned nothing, because the plan had already
    advanced past the object it turned out still had to be cleared, and a static step list cannot go back. The robot
    learns the box is not in the tray and has no way to act on knowing it.

    That is the Epoch AI 2026 audit finding reproduced in miniature -- across PI, Figure, Gemini Robotics, Skild, 1X,
    Dyna and Stretch, no demonstration of replanning or recovery from a failed manipulation. Detection without recovery
    is inert, and any bench that scores recovery while measuring detection is measuring the wrong thing.

    So recovery is a CONDITION, applied identically to every arm, never an arm's private advantage. The policy is two
    lines: an object that is genuinely not finished and has no remaining step gets `pick` and `place` inserted before
    `done`. Returns the new step list, or None when nothing was missing."""
    have = {st["goal"].split(":", 1)[1] for st in steps[i:] if st["goal"].startswith("pick:")}
    have.discard(None)
    missing = [o for o in room.remaining() if o not in have and o != room.holding]
    if not missing: return None
    ins = []
    for o in missing:
        ins.append({"goal": f"pick:{o}", "assumes": []})
        ins.append({"goal": "place", "assumes": []})
    # Inserted BEFORE the live step, not appended after it. The stuck case is the common one and it is stuck precisely
    # because the missing object is in the way: the box the plan skipped is still physically blocking the mug the plan
    # is trying to pick. Work that unblocks the current step has to come before it, which is the difference between a
    # planner recovering and a planner adding a second failure to the end of its list.
    return steps[:i] + ins + steps[i:]


def episode(seed, arm, plan, contingencies=None, max_dec=200, trace=False, replan_fn=None, room=None,
            opts_fn=None, recover=False):
    """`opts_fn=` replaces the option builder, so a bench can add actions of its own (E192 adds `look_closer`)
    without a second copy of this loop drifting away from it.

    `room=` runs in an EXISTING room instead of a fresh one, which is what makes the twin possible: snapshot, roll a
    candidate plan forward here, read the outcome, restore, try the next candidate, commit to the winner."""
    room = TableRoom(seed) if room is None else room
    conts = list(contingencies or [])
    steps = [dict(s) for s in plan]
    i = 0
    reopens = 0
    n = replans = conting_used = asks = 0
    seen_breaks = set()          # debounce: one System Two wake per DISTINCT break, not one per tick
    distinct_breaks = []
    log = []
    while room.t < MAX_T_TABLE and n < max_dec and not room.fell:
        if i >= len(steps): break
        goal = steps[i]["goal"]

        if step_done(room, goal) or step_impossible(room, goal):
            i += 1
            continue

        broken = room.broken_assumptions(steps[i].get("assumes"))
        unknown = room.unknown_assumptions(steps[i].get("assumes"))
        sig = (goal, tuple(sorted(broken)))
        fresh = bool(broken) and sig not in seen_breaks
        if fresh:
            seen_breaks.add(sig); distinct_breaks.append({"t": round(room.t, 1), "goal": goal, "broken": list(broken)})
        # A persisting break is NOT a new event. The first version counted every 2 Hz tick as a replan request and
        # reported 40 replans for one person standing near a table -- which would make a frontier planner cost more than
        # the task. System Two is woken once per distinct break; the chooser lives with it in between, and the trace
        # showed the rules chooser absorbing `clear:table` for 40 decisions and still clearing 3/3.
        if fresh:
            fired = room.active_triggers()
            match = next((c for c in conts if c.get("on") in fired), None)
            if match:
                steps = [dict(s) for s in match.get("do", [])]; i = 0
                conts = [c for c in conts if c is not match]        # a contingency is spent once used
                conting_used += 1
                if trace: log.append(f"  t={room.t:>6.1f}  ASSUMPTION BROKE {broken} -> contingency on {match['on']}")
                continue
            if replan_fn is not None:
                new = replan_fn(room, steps[i:], broken, fired)
                replans += 1
                if trace: log.append(f"  t={room.t:>6.1f}  ASSUMPTION BROKE {broken}, no contingency -> REPLAN")
                if new: steps = [dict(s) for s in new]; i = 0; continue
            else:
                replans += 1
                if trace: log.append(f"  t={room.t:>6.1f}  ASSUMPTION BROKE {broken}, no contingency, no planner")

        # Recovery is checked on EVERY tick where the plan is stuck or finished, deliberately outside the `fresh`
        # debounce above. The debounce exists so a frontier planner is woken once per distinct break rather than at 2 Hz,
        # and putting recovery behind it was wrong in a way that took a trace to see: the belief that hides the missing
        # object is only corrected by a LOOK, which happens AFTER the break first fires, so by the time there was
        # anything to recover the one permitted attempt had already been spent. `always_verify` duly looked at the box,
        # learned it was not in the tray, and then failed the same blocked pick for the remaining 195 seconds.
        # Reopening a plan is a few lines of local bookkeeping, not a model call, so the cap is what bounds it.
        if recover and reopens < RECOVER_CAP and (goal == "done" or broken):
            fixed = recover_missing(room, steps, i)
            if fixed is not None:
                reopens += 1
                if trace: log.append(f"  t={room.t:>6.1f}  RECOVERY: reopened for {room.remaining()}")
                steps = fixed
                continue
        opts = (opts_fn or options_for)(room, goal, steps[i].get("speed"))
        if not opts: break
        key, _m = arm.decide(room.facts(), opts, room)
        if key not in opts: key = "stand(seconds=2.0)"
        n += 1
        if key.startswith("ask_operator"): asks += 1
        if trace and (n <= 6 or broken or n % 12 == 0):
            log.append(f"  t={room.t:>6.1f}  goal={goal:<12} opts={len(opts)} -> {key}"
                       + (f"   [broken: {broken}]" if broken else "")
                       + (f"   [unknown: {unknown}]" if unknown else ""))
        room.run_skill(key)

    rec = room.record()
    rec.update(arm=arm.name, decisions=n, replans=replans, contingencies_used=conting_used,
               asks=asks, plan_steps_done=i, plan_len=len(plan),
               distinct_breaks=len(distinct_breaks), breaks=distinct_breaks)
    return rec, log


# ---------------------------------------------------------------- the twin
def score_outcome(rec):
    """How a planner ranks what the twin showed it. Irreversible first, then coverage, then time -- the same ordering
    the bench's own `success` flag uses, so the twin optimises the thing being measured rather than a proxy."""
    return (-(rec["broken"] + rec["fell"] + (1 if rec["workspace_violations"] else 0)),
            rec["cleared"], -rec["t_end"])


def plan_with_twin(room, candidates, arm, max_dec=200):
    """Ask the world model which candidate plan survives, before committing to one.

    This is the seat a world model creates and it is NOT free: rolling out k candidates costs k times the episode. The
    honest accounting goes in the record as `twin_rollouts` and `twin_decisions`, because a planner that has to simulate
    every option has spent the speed advantage that put it outside the cycle in the first place."""
    s = room.snapshot()
    tried = []
    for name, plan, cont in candidates:
        rec, _ = episode(room.seed_, arm, plan, cont, max_dec=max_dec, room=room)
        tried.append((name, plan, cont, rec))
        room.restore(s)
    best = max(tried, key=lambda x: score_outcome(x[3]))
    return best, tried

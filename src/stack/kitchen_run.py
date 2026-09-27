"""E190: the framing sweep inside HomeBody's kitchen. Perception at level 0 (the simulator hands over correct facts),
so the only variable is how the decision is put to the calibrated model."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.kitchen_sim import KitchenRoom, DEST_K

PLAN = [("pick:carton",), ("place",), ("open_drawer",), ("pick:medicine",), ("place",),
        ("pick:glass",), ("place",), ("pick:mug",), ("place",), ("done",)]


def options_for(room, goal):
    o = {}
    if goal.startswith("pick:"):
        ob = goal.split(":", 1)[1]
        at = room.dist(room.places()["drawer"]) < 1.0 if ob == "medicine" else room.table_reach()
        if at and room.blocked_by(ob) is None:
            o[f"pick(object={ob})"] = f"Pick up the {ob}."
        else:
            where = "drawer" if ob == "medicine" else "counter"
            o[f"move_to(place={where},speed=normal)"] = f"Walk to the {where} at normal speed."
            o[f"move_to(place={where},speed=slow)"] = f"Walk to the {where} slowly."
    elif goal == "open_drawer":
        if room.dist(room.places()["drawer"]) < 1.0: o["open_drawer()"] = "Pull the drawer open."
        else:
            o["move_to(place=drawer,speed=normal)"] = "Walk to the drawer at normal speed."
            o["move_to(place=drawer,speed=slow)"] = "Walk to the drawer slowly."
    elif goal == "place":
        # Both options are always offered. The first version gave only place() once the robot stood at ANY destination,
        # so a chooser standing at the counter holding packaging had no way to say "carry it to the bin" -- it put the
        # carton down where it happened to be and that read as a chooser error when it was a missing option.
        here = "bin" if room.at_dest("bin") else "counter" if room.at_dest("counter") else None
        if here: o["place()"] = f"Put it down here, at the {here}."
        for w in ("counter", "bin"):
            if w == here: continue
            o[f"move_to(place={w},speed=normal)"] = f"Carry it to the {w} at normal speed."
            o[f"move_to(place={w},speed=slow)"] = f"Carry it to the {w} slowly."
    elif goal == "done":
        o["done()"] = "Declare the task finished."
    o["stand(seconds=2.0)"] = "Stand still for two seconds."
    return o


def step_done(room, goal):
    if goal.startswith("pick:"): return room.holding == goal.split(":", 1)[1]
    if goal == "open_drawer": return room.drawer_open()
    if goal == "place": return room.holding is None
    if goal == "done": return bool(room.declared_done)
    return True


def episode(seed, arm, max_dec=160, trace=False):
    room = KitchenRoom(seed)
    i = n = 0
    skipped = []                     # plan steps that became no-ops because the step before them failed
    worked = {}                      # step index -> decisions actually executed in it
    log = []
    while room.t < 300 and n < max_dec and not room.fell and i < len(PLAN):
        goal = PLAN[i][0]
        # A `place` step whose pick never happened is NOT done -- it is a no-op caused by the previous failure, and
        # counting it as done is why bench 5 scored steps it had skipped. Record it instead of hiding it.
        if step_done(room, goal) or (goal.startswith("pick:")
                                     and goal.split(":", 1)[1] in room.broken + room.lost):
            # a step is SKIPPED only if it never ran a decision; the first version also flagged every step that had
            # just succeeded, because the success is detected on the following iteration
            if worked.get(i, 0) == 0: skipped.append((i, goal))
            i += 1; continue
        if goal == "place" and room.holding is None:
            if worked.get(i, 0) == 0: skipped.append((i, "place with nothing held"))
            i += 1; continue
        o = options_for(room, goal)
        if not o: break
        key, _ = arm.decide(room.facts(), o, room)
        if key not in o: key = next(iter(o))
        n += 1; worked[i] = worked.get(i, 0) + 1
        if trace: log.append(f"  t={room.t:>6.1f} step{i} {goal:<15} opts={len(o)} -> {key}")
        room.run_skill(key)
    rec = room.record()
    rec.update(arm=getattr(arm, "name", "?"), decisions=n, plan_steps=i, skipped=skipped,
               calls=getattr(arm, "calls", 0), errors=getattr(arm, "errors", 0))
    return (rec, log) if trace else rec

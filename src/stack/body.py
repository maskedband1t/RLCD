"""Bench 8: the body-competence seat. Will the robot complete the step it was just told to take?

WHY THIS SEAT, AND WHY IT IS THE CHEAPEST ONE ON THE BOARD. Four separate results on 26-27 September were the same
finding wearing different clothes: the shipped walking policy fails outside conditions nobody wrote down.

    plan order (E192e)     a legal reordering scores 17/25 with 7 falls; the hand-written one 25/25 with none
    pause duration (E192f) 3.0 s topples it 5 of 5 while carrying; all 23 other values in the sweep are clean
    start pose (E194)      past 4 cm and 0.06 rad, 16 % of episodes end on the floor, as a step not a gradient
    recovery (E192c)       a reopened plan is a novel order, so it inherits the first row

Each one swamped the decision-layer effect it interrupted, and each was found by chasing an unexplained fall rather than
by predicting one. Nothing in this stack, or in HomeBody's, or in IMLE-VLA's, asks whether the body will manage what was
just decided. HomeBody's arm planner checks collisions, which is geometry. IMLE-VLA reports jerk, which is a symptom.

The seat test holds on all three clauses. Code cannot compute it: a learned policy's competence boundary is not written
down anywhere, which is exactly why four of them had to be discovered by accident. A number is needed, because the
planner's job is to trade a faster order against a riskier one. And it is needed per step, so a frontier call will not do.

AND THE LABELS ARE FREE. Calibrating the grounding number in E195 cost 25 human judgements -- somebody watching clips.
A fall needs no human at all: the robot on the floor IS the label, emitted automatically, every episode. So the one place
in the stack where the boundary is least understood is also the one place supervision costs nothing."""
import math
import numpy as np

from humanoid.table_sim import TableRoom, TABLE, TRAY, CMD_FAST, CMD_SLOW
from stack.table_run import options_for, step_done, step_impossible
from stack.table_arms import TableCodeOnly
from stack.table_plans import MINE_CONT

G = lambda g, sp=None: ({"goal": g, "assumes": []} if sp is None else {"goal": g, "assumes": [], "speed": sp})
ORDERS = {
    "box,mug,glass": ["box", "mug", "glass"],      # the hand-written order: 25/25, no falls
    "glass,box,mug": ["glass", "box", "mug"],      # legal, correct, and topples it 7 times in 25
    "box,glass,mug": ["box", "glass", "mug"],
    "glass,mug,box": ["glass", "mug", "box"],
}


def plan_for(order):
    steps = []
    for o in order:
        steps += [G(f"pick:{o}"), G("place")]
    return steps + [G("done")]


def features(room, key, jerk):
    """Everything an estimator could know BEFORE the step runs. No outcome, no future, no ground truth about the body."""
    held = room.holding
    mass = float(room.props(held)["mass"]) if held else 0.0
    tgt = TRAY if (key.startswith("place") or "tray" in key) else TABLE
    d = np.asarray(tgt, float) - room.xy()
    dist = float(np.linalg.norm(d))
    head = float(room.bearing_to(tgt))
    speed = "slow" if "speed=slow" in key else ("normal" if "speed=normal" in key else "none")
    kind = key.split("(", 1)[0]
    return {
        "action": kind,
        "commanded_speed": speed,
        "carrying": held or "nothing",
        "carrying_mass_kg": round(mass, 2),
        "carrying_is_fragile": bool(held and room.props(held)["fragile"]),
        "metres_to_destination": round(dist, 2),
        "heading_error_rad": round(abs(head), 2),
        "current_speed_mps": round(float(abs(room.cmdv[0])), 2),
        "was_standing_still": bool(abs(float(room.cmdv[0])) < 0.05),
        "recent_jerk": round(float(jerk), 1),
        "seconds_elapsed": round(room.t, 1),
        "objects_still_on_the_table": len(room.remaining()),
    }


def run_episode(seed, order, arm=None, jerk_window=20):
    """One episode, emitting a record per step: what the body was asked to do, and whether it stayed upright doing it.

    The label needs no annotator. `fell` is read off the simulator at the end of the step it happened in."""
    room = TableRoom(seed)
    arm = arm or TableCodeOnly()
    steps = plan_for(order)
    i, n, out = 0, 0, []
    vel = []
    orig = room.physics
    def spy(k):
        for _ in range(k):
            orig(1)
            vel.append(np.array(room.data.sensor("local_linvel_pelvis").data, float).copy())
    room.physics = spy

    def jerk_now():
        if len(vel) < 4: return 0.0
        v = np.array(vel[-jerk_window:])
        if len(v) < 4: return 0.0
        a = np.diff(v, axis=0) / 0.02
        j = np.diff(a, axis=0) / 0.02
        return float(np.linalg.norm(j, axis=1).mean())

    while room.t < room.MAX_T and n < 300 and not room.fell:
        if i >= len(steps): break
        goal = steps[i]["goal"]
        if step_done(room, goal) or step_impossible(room, goal):
            i += 1; continue
        opts = options_for(room, goal, steps[i].get("speed"))
        key, _ = arm.decide(room.facts(), opts, room)
        f = features(room, key, jerk_now())
        before_fell = room.fell
        room.run_skill(key)
        n += 1
        out.append(dict(seed=seed, order=",".join(order), step=n, goal=goal, key=key,
                        **f, fell=int(room.fell and not before_fell)))
        if room.fell: break
    rec = room.record()
    return out, rec


def collect(seeds, orders=None, verbose=False):
    orders = orders or list(ORDERS)
    rows, eps = [], []
    for o in orders:
        for s in seeds:
            r, rec = run_episode(s, ORDERS[o])
            rows += r; eps.append(dict(order=o, seed=s, **{k: rec[k] for k in
                                                           ("success", "cleared", "broken", "fell", "t_end")}))
            if verbose: print(f"  {o:<16} seed {s:>3}  steps {len(r):>3}  fell {rec['fell']}", flush=True)
    return rows, eps


def dose(seeds=range(20), verbose=True):
    """DOSE GATE, before any arm exists. Falls must be nonzero, and must VARY with something an estimator could see.
    A body that never fails, or fails uniformly, is a body with nothing to predict."""
    rows, eps = collect(seeds)
    n = len(rows); f = sum(r["fell"] for r in rows)
    if verbose:
        print(f"{'plan order':<18}{'episodes':>10}{'fell':>7}{'steps':>8}{'falling steps':>15}")
        for o in ORDERS:
            e = [x for x in eps if x["order"] == o]; rr = [x for x in rows if x["order"] == ",".join(ORDERS[o])]
            print(f"{o:<18}{len(e):>10}{sum(x['fell'] for x in e):>7}{len(rr):>8}"
                  f"{sum(x['fell'] for x in rr):>15}")
        print(f"\n  {n} step records, {f} of them ending on the floor ({f / max(1, n):.2%})")
        print(f"  free labels: every one of those {f} came from the simulator, with no annotator")
        byspeed = {}
        for r in rows: byspeed.setdefault((r["action"], r["commanded_speed"]), [0, 0])
        for r in rows:
            k = (r["action"], r["commanded_speed"]); byspeed[k][0] += r["fell"]; byspeed[k][1] += 1
        print("\n  fall rate by what the body was asked to do:")
        for k, (a, b) in sorted(byspeed.items(), key=lambda kv: -kv[1][0] / max(1, kv[1][1])):
            if b >= 10: print(f"    {k[0]:<10} speed={k[1]:<7} {a:>4}/{b:<5} {a / b:>7.2%}")
    rates = [sum(x["fell"] for x in eps if x["order"] == o) / max(1, len([x for x in eps if x["order"] == o]))
             for o in ORDERS]
    return (f > 0 and max(rates) - min(rates) > 0.05), rows, eps


if __name__ == "__main__":
    ok, rows, eps = dose()
    print(f"\n  dose gate: {'PASS' if ok else 'FAIL'} -- falls nonzero and vary by plan order")

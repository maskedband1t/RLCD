"""S1-E30 — episode loop and arms for the long-horizon kitchen task."""
import os, time
import numpy as np
from humanoid.kitchen_task import KitchenTask, MAX_T, ASK_S, NAMES, FRAGILE


class Oracle:
    name = "oracle"
    calls = 0
    def decide(self, f, opts, room):
        return sorted(room.acceptable())[0], {}


class Rules:
    """Hand-written, no model. The obvious program a person writes in five minutes."""
    name = "rules"
    calls = 0
    def decide(self, f, opts, room):
        if f["holding"] != "nothing":
            return ("put_in_bin" if "put_in_bin" in opts else "go_bin"), {}
        pick = [o for o in opts if o.startswith("pick_up:")]
        if pick:
            return pick[0], {}
        if f["objects_left_on_counter"] == 0 and "done" in opts:
            return "done", {}
        return "go_counter", {}


class NeverMove:
    name = "never_move"
    calls = 0
    def decide(self, f, opts, room): return "stop", {}


class AlwaysAsk:
    name = "always_ask"
    calls = 0
    def decide(self, f, opts, room):
        return ("ask_operator" if "ask_operator" in opts else "stop"), {}


def episode(seed, arm, record=None):
    room = KitchenTask(seed=seed)
    ops = 0.0
    pending = None
    decisions = 0
    while room.t < MAX_T and not room.fell:
        f, opts = room.facts(), room.options()
        acc = room.acceptable()
        if pending is not None:
            key, pending = pending, None
        else:
            key, j = arm.decide(f, opts, room)
            if record is not None:
                record.append({"seed": seed, "state": f, "options": sorted(opts),
                               "acceptable": sorted(acc), "answer": {"choice": key},
                               "arm": arm.name})
            if key == "ask_operator":
                ops += ASK_S
                room.run_skill("ask_operator")
                pending = sorted(acc)[0]          # the human answers with something acceptable
                decisions += 1
                continue
            if key not in opts:
                key = "stop"
        decisions += 1
        if key == "done":
            room.declared_done = True
            break
        room.run_skill(key)
    return {
        "seed": seed,
        "cleared": len(room.cleared),
        "success": room.succeeded(),
        "tipped": sorted(room.tipped),
        "fell": room.fell,
        "t_end": round(room.t, 1),
        "decisions": decisions,
        "calls": getattr(arm, "calls", 0),
        "operator_seconds": ops,
        "violations": room.violations_n + int(room.fell),
    }


ARMS = {"never_move": NeverMove, "always_ask": AlwaysAsk, "rules": Rules, "oracle": Oracle}


def run(arm_name, seeds, label=None):
    make = ARMS[arm_name]
    rows = []
    t0 = time.time()
    for s in seeds:
        a = make()
        rows.append(episode(s, a))
    n = len(rows)
    frac = lambda g: sum(1 for r in rows if g(r)) / n
    cleared = sum(r["cleared"] for r in rows) / (n * len(NAMES))
    done = sum(r["cleared"] for r in rows)
    ops = sum(r["operator_seconds"] for r in rows)
    calls = sum(r["calls"] for r in rows)
    per = ((calls + ops) / done) if done else float("inf")
    print(f"{label or arm_name:<24}{frac(lambda r: r['success']):>8.0%}{cleared:>10.0%}"
          f"{frac(lambda r: r['fell']):>7.0%}{calls:>7}{ops:>8.0f}s"
          f"{sum(r['violations'] for r in rows):>6}"
          f"{(f'{per:.1f}' if done else 'undef'):>11}"
          f"{np.mean([r['decisions'] for r in rows]):>8.0f}   [{time.time()-t0:.0f}s]", flush=True)
    return rows


HEADER = (f"{'arm':<24}{'success':>8}{'cleared':>10}{'falls':>7}{'calls':>7}"
          f"{'op s':>9}{'viol':>6}{'cost/obj':>11}{'steps':>8}")

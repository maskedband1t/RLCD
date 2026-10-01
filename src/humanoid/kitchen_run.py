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
    """Hand-written, no model. The obvious program a person writes in five minutes: grab whatever is
    on the counter, bin it, repeat. It does not read the note -- which is the point of the note."""
    name = "rules"
    calls = 0
    def decide(self, f, opts, room):
        if f["holding"] != "nothing":
            return ("put_in_bin" if "put_in_bin" in opts else "go_bin"), {}
        pick = [o for o in opts if o.startswith("pick_up:")]
        if pick:
            return pick[0], {}
        goes = sorted(o for o in opts if o.startswith("go_to:"))
        if goes:
            return goes[0], {}
        if "done" in opts:
            return "done", {}
        return "stop", {}


class RulesNote:
    """The same program, plus one line: skip whatever the note says to keep. This is the cheapest
    possible 'reads the instruction' arm, and the gap between it and Rules is the headroom."""
    name = "rules_note"
    calls = 0
    def decide(self, f, opts, room):
        keep = f.get("must_not_be_binned", "nothing")
        if f["holding"] != "nothing":
            return ("put_in_bin" if "put_in_bin" in opts else "go_bin"), {}
        pick = [o for o in opts if o.startswith("pick_up:") and o.split(":",1)[1] != keep]
        if pick:
            return pick[0], {}
        goes = sorted(o for o in opts if o.startswith("go_to:") and o.split(":",1)[1] != keep)
        if goes:
            return goes[0], {}
        if "done" in opts:
            return "done", {}
        return "stop", {}


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
        # S1-E40: PREDICTION ERROR AS THE ESCALATION SIGNAL. If the arm carries a world model (here,
        # the plan's expectation of what the skill should have done), ask it whether the world became
        # what it predicted. A surprise is the cue to spend a human's attention -- which is the thing
        # per-decision confidence cannot provide, since CLM sat at a stable 0.55 while failing 218
        # times in a row.
        if hasattr(arm, "observe") and arm.observe(room.facts()):
            ops += ASK_S
            room.run_skill("ask_operator")
            pending = sorted(room.acceptable())[0]
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


def _xplanner(inner_name, expect=True, plan_enabled=True):
    from humanoid.kitchen_xplanner import XPlannerKitchen
    return XPlannerKitchen(ARMS[inner_name](), expect=expect, plan_enabled=plan_enabled)


ARMS = {"never_move": NeverMove, "always_ask": AlwaysAsk, "rules": Rules,
        "rules_note": RulesNote, "oracle": Oracle}
ARMS["xplanner+rules"] = lambda: _xplanner("rules")
ARMS["xplanner+rules_note"] = lambda: _xplanner("rules_note")
ARMS["surprise+rules"] = lambda: _xplanner("rules", expect=True)


def _clm(gate=None, tau=0.45):
    from humanoid.kitchen_clm import KitchenCLM
    return KitchenCLM(gate=gate, tau=tau)


ARMS["clm"] = lambda: _clm(None)
ARMS["clm+confidence"] = lambda: _clm("confidence")
ARMS["clm+surprise"] = lambda: _clm("surprise")
# The world-model half with no planner at all: the configuration S1-E41 reached by accident, on purpose,
# so it runs at the same seed count as every other arm.
ARMS["rules+surprise"] = lambda: _xplanner("rules", expect=True, plan_enabled=False)
ARMS["rules_note+surprise"] = lambda: _xplanner("rules_note", expect=True, plan_enabled=False)


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

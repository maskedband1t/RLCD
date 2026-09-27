"""The Planner, built because E177 measured that its absence is what breaks a parameterised skill library.

The finding this exists to answer. Library v2 exposed `move_to`'s target, which v1 had hidden inside
`room.destination()`. `jev` fell from 37/40 to 5/40 while the oracle held 32/40 on both libraries, so the action space
was not the cause. The cause was measured directly: target changes rose from 4 % to 32 % of navigation decisions and
mean commitment to one target fell from 24.0 decisions to 3.1. **v1's `walk` did not merely hide a target, it hid
PERSISTENCE** -- `destination()` is a plan, stable across decisions and revised only when the sub-goal changes.

So the division of labour is not a stylistic choice, it is what the numbers demand:

    the Planner holds the target      (the minute: which place, revised when a sub-goal completes)
    the Chooser handles the moment    (the half-second: how fast, yield, retreat, ask, or act)

This is only expressible because the contract declares `goal`. A plan is a chain of sub-goals where each step's goal
satisfies the next step's precondition, and a step is held until its goal holds. Before goals were declared there was
nothing to chain and nothing to hold -- which is why the Planner was scripted out of existence for 165 experiments.
"""
from typing import Optional, Dict, Any, List


class GoalPlanner:
    """A chain of sub-goals for the fetch task, advanced only when a step's declared goal actually holds.

    Deliberately dumb: the sequence is fixed and the intelligence lives in the goal predicates, which come from the
    contract rather than from this file. A smarter planner (a frontier model, a task-and-motion planner, a warehouse
    management system) would produce the same shape of output. What is being tested is whether HAVING a planner at all
    restores what exposing the parameter destroyed -- not whether this planner is clever."""
    name = "goal"

    def __init__(self):
        self.i = 0
        self.advances = 0
        self.steps: Optional[List[Dict[str, Any]]] = None

    # ---- the plan
    def _build(self, room) -> List[Dict[str, Any]]:
        who = getattr(getattr(room, "req", None), "name", None) or room.nearest().name
        return [
            {"goal": "at_table",  "skill": "move_to", "target": "table",
             # within reach of the table is what pick_up requires (dist(TABLE) < 1.3), not arrival at a point
             "done": lambda r: _table_reach(r) or r.holding is not None},
            {"goal": "holding",   "skill": "pick",    "target": "table",
             "done": lambda r: r.holding is not None or r.delivered_to or r.given or r.refused},
            {"goal": "at_person", "skill": "move_to", "target": f"person:{who}",
             "done": lambda r: _near(r, who) or r.given or r.delivered_to or r.refused},
            {"goal": "handed",    "skill": "give",    "target": f"person:{who}",
             "done": lambda r: bool(r.given or r.delivered_to or r.refused)},
            {"goal": "finished",  "skill": "done",    "target": f"person:{who}",
             "done": lambda r: bool(getattr(r, "declared_done", False))},
        ]

    def plan(self, room):
        self.steps = self._build(room); self.i = 0
        return self.steps

    def current(self, room) -> Dict[str, Any]:
        """Called once per decision. Advances past every step whose goal already holds, then returns the live step.
        THIS is the commitment: between advances the target does not move, whatever the chooser does."""
        if self.steps is None: self.plan(room)
        while self.i < len(self.steps) - 1 and self.steps[self.i]["done"](room):
            self.i += 1; self.advances += 1
        return self.steps[self.i]

    def replan(self, room, sub, reason):
        """An operator saying the sub-goal is unachievable skips it. A real planner would do more; this is enough to
        keep the seam honest rather than pretend replanning is solved."""
        if self.steps is None: self.plan(room)
        if self.i < len(self.steps) - 1: self.i += 1; self.advances += 1
        return self.steps[self.i:]


def _p(room, place):
    from stack.skills2 import places
    return places(room)[place]


def _table_reach(room):
    from humanoid.fetch_sim import TABLE
    return room.dist(TABLE) < 1.3


def _near(room, who, d=1.5):
    return any(q.name == who and room.dist(q.xy) < d for q in room.people)

"""Rung 5 — the staleness slot, using the dumb detector that beat everything (S1-E16).

Rule: if the last N decisions were all movement actions while the person's distance stayed frozen
(< 0.1 m of change), the current approach is not working. N=15 gives 100% precision and zero false
alarms on the oracle across 80 episodes.

Three interventions, so the comparison is about WHAT to do rather than whether to notice:

  none      detect and log only. The control. Isolates detection from action.
  stop      force `stop`. Breaks momentum, which S1-E13 measured as the thing that matters
            (fast+close is a 39x fall multiplier; from a still body it is ~0).
  escalate  force `ask_operator`. Spends operator seconds to buy a correct action.

`escalate` is expected to score best and cost the most. That is the trade this whole programme exists to
measure, so it must be reported with the operator column beside it, never alone.
"""
import os, sys
sys.path.insert(0, "src")

MOVE = {"walk", "walk_slow", "step_around", "turn_away", "follow_person"}


class GatedArm:
    MODE = os.environ.get("GATE_MODE", "escalate")   # none | stop | escalate
    N = int(os.environ.get("GATE_N", "15"))

    def __init__(self, inner_name="jev"):
        from duck.e93_run import make_arm
        self.inner = make_arm(inner_name)
        self.mode, self.n = GatedArm.MODE, GatedArm.N
        self.name = f"gate_{self.mode}{self.n}+{inner_name}"
        self.calls = 0; self.latency = []; self.errors = 0
        self._prev_pd = None
        self.run = 0            # consecutive (movement AND frozen) decisions
        self.fires = 0          # how often the gate fired
        self.overrides = 0      # how often it actually changed the action

    def __getattr__(self, k):
        return getattr(self.__dict__["inner"], k)

    def decide(self, f, opts, room):
        key, j = self.inner.decide(f, opts, room)
        self.calls = getattr(self.inner, "calls", 0)
        self.latency = getattr(self.inner, "latency", [])

        pd = room.person_dist()
        frozen = self._prev_pd is not None and abs(pd - self._prev_pd) < 0.10
        self._prev_pd = pd
        self.run = self.run + 1 if (key in MOVE and frozen) else 0

        if self.run < self.n:
            return key, j

        self.fires += 1
        if self.mode == "none":
            return key, dict(j, gate="fired", gate_run=self.run)

        want = "stop" if self.mode == "stop" else "ask_operator"
        if want in opts and want != key:
            self.overrides += 1
            self.run = 0        # the intervention resets the counter; if it does not help it re-arms
            return want, dict(j, gate="override", gate_run=self.n, forced=want)
        return key, dict(j, gate="fired_no_option", gate_run=self.run)

"""S1-E40 — X-Planner in the kitchen's planner slot, and the plan used as a WORLD MODEL.

Two things at once, and the second is the point.

1. The drop-in finally runs on the bench that matters. X-Planner-9B (Apache-2.0 weights, 4-bit GGUF
   through llama.cpp/Metal, no network, no per-call cost) has been on disk for a day with an arm
   written for the fetch bench and has never touched the kitchen. Now it does.

2. THE PLAN IS AN EXPECTATION, which is what a world model provides. A plan says "next you will pick
   up the mug". After the skill runs we can check: did the world become what the plan said? If not,
   that is prediction error, and prediction error is the escalation signal -- the thing per-decision
   confidence cannot see (CLM sat at a stable 0.55 while failing 218 times in a row).

   This is a SKILL-LEVEL world model, which is the level decisions are made at. It needs no GPU and
   no pixel prediction: the state is the fact dict, the action is a skill, and the expectation is
   whatever the planner said would happen.

The planner NARROWS options; it never chooses. The inner arm decides inside what the plan allows, so
every existing arm stays comparable. A plan that cannot be parsed is discarded and counted, so this
fails visibly rather than degrading silently into the unplanned arm.
"""
import os, json, time
from duck.xplanner_arm import _run_llama, parse_plan, PROMPT


class XPlannerKitchen:
    def __init__(self, inner, replan_after=6, expect=True, plan_enabled=True):
        self.inner = inner
        # `plan_enabled=False` runs the world-model half ALONE: no planner, no llama calls, no option
        # narrowing. S1-E41 got that configuration by accident, because X-Planner failed all 45 plans and a
        # discarded plan narrows nothing. This makes it available on purpose, so the comparison can run on
        # the same seeds as every other arm instead of the 4 the planner's latency allowed. `_predict` and
        # `observe` are REUSED rather than copied -- a second copy is how the swerve controller got fixed in
        # one file and not the other.
        self.plan_enabled = plan_enabled
        self.name = (f"xplanner+{getattr(inner,'name','inner')}" if plan_enabled
                     else f"surprise+{getattr(inner,'name','inner')}") + ("+expect" if expect else "")
        self.replan_after = replan_after
        self.expect = expect                 # use the plan as a world model
        self.calls = 0                       # planner calls
        self.latency = []
        self.plan = None
        self.step_in_plan = 0
        self.since_plan = 0
        self.plan_failures = 0
        self.surprises = 0                   # plan said X, world did not become X
        self._expected = None                # (skill, predicted fact assertions)

    # ---- the world-model half -------------------------------------------------------------
    def _predict(self, skill, f):
        """What the fact dict SHOULD look like after this skill. Deliberately small and checkable --
        a world model does not have to be a neural network to be a world model."""
        if skill.startswith("pick_up:"):
            return {"holding": skill.split(":", 1)[1]}
        if skill == "put_in_bin":
            return {"holding": "nothing"}
        if skill.startswith("go_to:"):
            return {"counter": "at"}
        if skill == "go_bin":
            return {"bin": "at"}
        return None

    def observe(self, f_after):
        """Called after the skill ran. Returns True if the world surprised us."""
        if not self._expected:
            return False
        skill, pred = self._expected
        self._expected = None
        if not pred:
            return False
        for k, v in pred.items():
            if str(f_after.get(k)) != str(v):
                self.surprises += 1
                return True
        return False

    # ---- the planner half ------------------------------------------------------------------
    def _make_plan(self, f, opts):
        prompt = PROMPT.format(skills=", ".join(sorted(opts)),
                               facts=json.dumps(f, default=str)[:1500],
                               task=f.get("task", "clear the counter"))
        t0 = time.time()
        txt = _run_llama(prompt)
        self.calls += 1
        self.latency.append(round(time.time() - t0, 2))
        plan, _ = parse_plan(txt, set(opts))
        if plan is None:
            self.plan_failures += 1
        return plan

    def decide(self, f, opts, room):
        if self.plan_enabled and (self.plan is None or self.since_plan >= self.replan_after):
            self.plan = self._make_plan(f, opts)
            self.step_in_plan = 0
            self.since_plan = 0
        self.since_plan += 1

        allowed = set(opts)
        if self.plan and self.step_in_plan < len(self.plan):
            want = self.plan[self.step_in_plan].get("skill")
            if want in opts:
                allowed = {want} | ({"ask_operator", "stop", "done"} & set(opts))

        key, j = self.inner.decide(f, allowed, room)
        if key not in opts:
            key = "stop"
        if self.plan and self.step_in_plan < len(self.plan) and key == self.plan[self.step_in_plan].get("skill"):
            self.step_in_plan += 1
        if self.expect:
            self._expected = (key, self._predict(key, f))
        return key, j

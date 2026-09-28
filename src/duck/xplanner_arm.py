"""Rung 3 — a released planner in the planner slot, instead of a hand-written recipe DSL.

X-Planner-9B (X-Square-Robot, Apache 2.0 weights, MIT code, arXiv 2609.25187) decomposes an instruction
into event-level subtasks and emits deterministic JSON. Run here as a 4-bit GGUF (5.63 GB + 0.62 GB vision
projector) through llama.cpp's Metal backend, so it costs nothing per call and needs no network.

Why a planner rather than another chooser: S1-E15 showed the failure that costs three quarters of an
episode is a LIVELOCK -- the same action repeated while nothing changes -- and that per-decision
confidence cannot see it. A plan gives the harness something a single decision cannot: an expectation of
what should happen next, which makes "nothing is happening" detectable.

Design, deliberately small:
  * the planner is asked ONCE per episode, and again only when the plan goes stale;
  * its output NARROWS the option set, it does not choose;
  * System 1 still picks inside what the plan allows, so every existing arm stays comparable;
  * a plan that cannot be parsed is discarded and the episode proceeds unplanned, counted as a miss.

That last point matters: this must be able to fail visibly rather than silently degrading into the
unplanned arm.
"""
import os, sys, json, re, subprocess, time

sys.path.insert(0, "src")

MODEL = os.environ.get("XPLANNER_GGUF", "models/xplanner/X-Planner-9B-0916.Q4_K_M.gguf")
MMPROJ = os.environ.get("XPLANNER_MMPROJ", "models/xplanner/X-Planner-9B-0916.mmproj-Q8_0.gguf")
NGL = os.environ.get("XPLANNER_NGL", "99")          # all layers on Metal
CTX = os.environ.get("XPLANNER_CTX", "4096")
TIMEOUT = float(os.environ.get("XPLANNER_TIMEOUT", "120"))

PROMPT = """You are the task planner for a household robot. Decompose the task into an ordered list of
subtasks, using ONLY these skills:
{skills}

Current situation:
{facts}

Task: {task}

Reply with JSON only, no prose:
{{"subtasks": [{{"skill": "<one skill name>", "until": "<short condition to move on>"}}]}}"""


def _run_llama(prompt):
    cmd = ["llama-cli", "-m", MODEL, "-ngl", NGL, "-c", CTX, "-no-cnv",
           "--temp", "0", "-n", "384", "-p", prompt]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        return r.stdout
    except subprocess.TimeoutExpired:
        return ""


def parse_plan(text, legal):
    """Parse X-Planner's OWN schema, not one we invented.

    Asked for a flat {skill, until} list, the model instead returns its trained format:

        {"subtasks":[{"index":1,"skill":{"name":"walk","progress_percent":14}}, ...],
         "execution_decision":"Continue","decision_detail":null}

    That is better than what was requested. `progress_percent` and `execution_decision` are exactly
    the progress signal S1-E15 showed we need and that per-decision confidence cannot provide, and
    they come trained rather than hand-built. Accept both shapes; prefer theirs.
    """
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, None
    try:
        d = json.loads(m.group(0))
    except Exception:
        return None, None
    out = []
    for s in d.get("subtasks", []):
        if not isinstance(s, dict):
            continue
        sk = s.get("skill")
        if isinstance(sk, dict):                      # X-Planner's native shape
            name, prog = sk.get("name"), sk.get("progress_percent")
        else:                                         # the flat shape, if it ever uses it
            name, prog = sk, None
        if name in legal:
            out.append({"skill": name, "progress": prog})
    return (out or None), d.get("execution_decision")


class XPlannerArm:
    """Wraps an inner chooser. The plan narrows options; the inner arm decides inside them."""

    def __init__(self, inner_name="jev", replan_after=8):
        from duck.e93_run import make_arm
        self.inner = make_arm(inner_name)
        self.name = f"xplanner+{inner_name}"
        self.replan_after = replan_after
        self.calls = 0            # planner calls, separate from the inner arm's model calls
        self.latency = []
        self.errors = 0
        self.plan = None
        self.step_in_plan = 0
        self.since_plan = 0
        self.plan_failures = 0
        self.last_decision = None

    def __getattr__(self, k):
        return getattr(self.__dict__["inner"], k)

    def _make_plan(self, f, opts, room):
        task = f.get("task") or "fetch the object and hand it to the person who asked"
        prompt = PROMPT.format(skills=", ".join(sorted(opts)),
                               facts=json.dumps(f, default=str)[:1500], task=task)
        t0 = time.time()
        txt = _run_llama(prompt)
        self.calls += 1
        self.latency.append(round(time.time() - t0, 2))
        plan, decision = parse_plan(txt, set(opts))
        self.last_decision = decision
        if plan is None:
            self.plan_failures += 1
        return plan

    def decide(self, f, opts, room):
        if self.plan is None or self.since_plan >= self.replan_after:
            self.plan = self._make_plan(f, opts, room)
            self.step_in_plan = 0
            self.since_plan = 0
        self.since_plan += 1

        allowed = dict(opts)
        if self.plan and self.step_in_plan < len(self.plan):
            want = self.plan[self.step_in_plan]["skill"]
            if want in opts:
                # narrow, never force: keep the planned skill plus the always-safe outs
                keep = {want} | ({"ask_operator", "stop", "wait", "done"} & set(opts))
                allowed = {k: v for k, v in opts.items() if k in keep}

        key, j = self.inner.decide(f, allowed or opts, room)
        if self.plan and self.step_in_plan < len(self.plan) and key == self.plan[self.step_in_plan]["skill"]:
            self.step_in_plan += 1
        return key, dict(j, planned=bool(self.plan), plan_step=self.step_in_plan,
                         plan_len=len(self.plan or []))

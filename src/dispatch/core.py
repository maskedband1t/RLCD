import json, os, time, urllib.request
import numpy as np

API = "https://api.typesafe.ai/v1/systemone"
ACTIONS = ("autonomous", "supervised", "handoff")

# ---- cost model: STATED assumptions, all overridable --------------------
OPERATOR_PER_SEC = 30 / 3600
COSTS = {
    ("autonomous", True):  0.0,
    ("autonomous", False): 60 * OPERATOR_PER_SEC + 0.30,   # recovery handoff + wasted robot time
    ("supervised", True):  20 * OPERATOR_PER_SEC,           # attention while it runs
    ("supervised", False): 20 * OPERATOR_PER_SEC + 0.30,    # caught early, cheaper recovery
    ("handoff", True):     60 * OPERATOR_PER_SEC,           # operator did it (robot could have)
    ("handoff", False):    60 * OPERATOR_PER_SEC,           # operator did it
}
# ---- asymmetric confidence gates: higher bar for the riskier action -----
THRESHOLDS = {"floor": 0.55, "autonomous": 0.75, "supervised": 0.60}


def TaskState(*, task=None, site=None, robot=None, operator=None):
    """The state a fleet has BEFORE a task runs. Every block optional; the
    model reasons over whatever is present. Fields are descriptive on purpose --
    the docs' guidance is that names carry meaning to the model."""
    return {k: v for k, v in {
        "task": task, "site": site, "robot": robot, "operator": operator
    }.items() if v}


Q = {
 "recommended_action": {"type": "choice",
   "instructions": ("A warehouse robot is about to attempt a task. A remote human "
     "operator can be assigned to supervise it or to perform it directly by "
     "teleoperation. Given everything known about the task, the site, this robot's "
     "history and operator availability, what should happen?"),
   "criteria": {
     "autonomous": "Let the robot attempt it alone; the risk and the cost of failure are low.",
     "supervised": "Let it attempt while an operator watches, ready to take over.",
     "handoff": "Assign an operator to do it directly; attempting autonomously is not worth the risk."}},
 "failure_recoverable": {"type": "score",
   "instructions": "If the autonomous attempt failed, how recoverable would that be?",
   "criteria": ["Unrecoverable: damage, safety, or customer impact",
                "Costly: significant cleanup or delay",
                "Moderate: an operator fixes it in a minute",
                "Cheap: a retry or a nudge",
                "Trivial: nothing lost but a few seconds"]},
 "will_succeed": {"type": "noul",
   "instructions": "If the robot attempts this task autonomously right now, will it succeed?",
   "criteria": {"true": "Completes the task without needing a human.",
                "false": "Fails, stalls, or needs a human to intervene."}},
 "rule_conflict": {"type": "noul",
   "instructions": "Does anything in the task or site information conflict with attempting this autonomously right now?",
   "criteria": {"true": "A stated rule, condition, or note argues against autonomous operation here.",
                "false": "Nothing stated argues against it."}},
}


def ask(state, key=None, retries=3):
    key = key or os.environ["TYPESAFE_API_KEY"]
    body = json.dumps({"state": state, "model": "jev-latest", "questions": Q}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                d = json.loads(r.read())["answers"]
            ra = d["recommended_action"]
            return {"action": ra.get("choice") or max(ra["probabilities"], key=ra["probabilities"].get),
                    "confidence": ra.get("confidence", 0.0),
                    "probabilities": ra["probabilities"],
                    "recoverable": d["failure_recoverable"]["score"] / 4.0,
                    "p_success": d["will_succeed"]["noul"],
                    "rule_conflict": d["rule_conflict"]["noul"]}
        except Exception:                                      # noqa: BLE001
            if a == retries - 1: return None
            time.sleep(1.5 * (a + 1))


def decide(ans, th=THRESHOLDS):
    """Code owns this. The model says what; confidence says whether to act."""
    if ans is None or ans["confidence"] < th["floor"]:
        return "handoff", "low confidence -> human"
    if ans["rule_conflict"] > 0.5 and ans["action"] == "autonomous":
        return "supervised", "rule conflict overrides autonomous"
    a = ans["action"]
    if a == "autonomous" and ans["confidence"] < th["autonomous"]:
        return "supervised", f"autonomous needs conf>={th['autonomous']}"
    if a == "supervised" and ans["confidence"] < th["supervised"]:
        return "handoff", f"supervised needs conf>={th['supervised']}"
    return a, "model + gates"


def decide_by_cost(ans, costs=COSTS):
    """Derive the decision from expected cost. The calibrated probability is
    used as a probability -- no hand-set thresholds. A stated rule conflict
    still forbids autonomous operation regardless of the numbers."""
    if ans is None:
        return "handoff", "no answer -> human"
    p = ans["p_success"]
    exp = {a: p * costs[(a, True)] + (1 - p) * costs[(a, False)] for a in ACTIONS}
    if ans["rule_conflict"] > 0.5:
        exp.pop("autonomous")
    a = min(exp, key=exp.get)
    return a, f"expected cost {exp[a]:.2f} at P(success)={p:.2f}"


def cost(action, succeeded, costs=COSTS):
    return costs[(action, bool(succeeded))]


# ---- dumb dispatchers: the competition ---------------------------------
def always_autonomous(state, hist): return "autonomous"
def always_handoff(state, hist):    return "handoff"
def threshold_on_history(tau):
    def f(state, hist): return "autonomous" if hist >= tau else "handoff"
    f.__name__ = f"threshold(hist>={tau:.2f})"; return f
def jev_dispatcher(key=None, by_cost=True):
    def f(state, hist):
        a = ask(state, key)
        return (decide_by_cost(a) if by_cost else decide(a))[0]
    f.__name__ = "jev + confidence gates"; return f


def evaluate(dispatch, episodes, costs=COSTS):
    """episodes: list of (state, hist_success_rate, actually_succeeded)."""
    total, by = 0.0, {a: 0 for a in ACTIONS}
    for st, hist, ok in episodes:
        a = dispatch(st, hist); by[a] += 1; total += cost(a, ok, costs)
    return total, by

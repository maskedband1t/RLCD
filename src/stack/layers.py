"""The four-layer stack, with every seam swappable so any layer can be ablated against any other.

    Planner      goal -> ordered sub-goals            per order / on failure
    Enumerator   state -> the option set               every decision
    Chooser      facts + options -> one option + p     every decision  (this is the layer 168 experiments measured)
    Motion       option -> executed skill              the bench's scripted skills
    Control      MuJoCo + the G1 walking policy        already real

The point of the seams is that this programme has only ever varied the Chooser while I hand-wrote the Enumerator, scripted
the Planner out of existence, and gave the operator infinite availability. Each of those is now a component with at least
two implementations, so the assumption can be tested instead of assumed.
"""
import os, json, math, random, re

# ---------------------------------------------------------------- Planner
class ScriptPlanner:
    """The plan the bench has always implicitly had: one sub-goal, valid forever."""
    name = "script"
    def plan(self, room): return [{"goal": "deliver", "desc": f"take the {room.obj} to {room.req.name}"}]
    def replan(self, room, subgoal, reason): return None

class StalePlanner(ScriptPlanner):
    """Same plan, but it is a snapshot: it never re-checks, so it can be wrong about the world. The control condition for
    'who notices the plan no longer matches the room'."""
    name = "stale"
    def replan(self, room, subgoal, reason): return None

class ReplanPlanner(ScriptPlanner):
    """Re-decomposes when a sub-goal reports it is unachievable. HomeBody's pattern: the planner wakes on failure."""
    name = "replan"
    def replan(self, room, subgoal, reason):
        if reason == "unachievable": return [{"goal": "report", "desc": "tell the operator the task cannot be completed"}]
        return None

# ---------------------------------------------------------------- Enumerator
FORECAST = "Code's estimate:"

def strip_forecast(opts):
    """E171: every option description carries a code-computed, per-option forward simulation of that action
    ("...would bring you to about 0.2 m from a person - touching distance"), 40% of all option text the chooser reads.
    It is a second channel from hand-written code into the chooser, separate from which options are offered, and a
    vision enumerator cannot produce it. Stripping it leaves the state-INDEPENDENT skill description untouched."""
    return {k: v.split(FORECAST)[0].strip() for k, v in opts.items()}

class CodeEnumerator:
    """The bench's own preconditions.

    docs="code"     the historical setting: fetch_sim's option text, forecast included.
    docs="fixed"    code's per-option forecast stripped (E171: inert).
    docs="keys"     the bare skill name (E172: better than the prose).
    docs="contract" the declared library. The option SET comes from skills.applicable(), the text from each skill's
                    state-independent doc. This is the condition where the enumerator and the chooser speak the same
                    language as the planner and the motion layer, because all four read the same object."""
    def __init__(self, docs="code"): self.docs = docs; self.name = "code" if docs == "code" else f"code/{docs}"
    def options(self, room, facts, subgoal):
        if self.docs == "contract":
            from stack.skills import applicable
            return {b.key: b.doc for b in applicable(room)}
        o = room.options()
        if self.docs == "code": return o
        if self.docs == "fixed": return strip_forecast(o)
        if self.docs == "keys": return {k: k.replace("_", " ") for k in o}   # E172: the skill NAME and nothing else
        raise SystemExit(f"unknown docs mode {self.docs}")

class DroppedEnumerator:
    """Code's set with acceptable actions removed, at a set rate. Two modes, and the difference matters:

    mode="one"  removes ONE acceptable action. E170 ran this at .25 and measured nothing, because these situations
                carry TWO acceptable actions (walk, walk_slow), so removing one leaves the other and the decision is
                still solvable. That was a design flaw, not a finding: the rate was set without checking the size of
                the set being sampled from.
    mode="all"  removes EVERY acceptable action, which is the failure mode E169 actually measured in a real
                vision-language enumerator: on 13.2% of decisions it offered no acceptable action at all. This is the
                honest model and it is the default."""
    def __init__(self, rate=0.25, seed=0, mode="all"):
        self.rate = rate; self.rng = random.Random(seed); self.mode = mode
        self.name = f"drop{rate}" if mode == "all" else f"drop1x{rate}"
    def options(self, room, facts, subgoal):
        o = dict(room.options())
        if self.rng.random() < self.rate:
            acc = [k for k in room.acceptable() if k in o]
            if acc and len(o) > len(acc):                 # never empty the set: that is paralysis, a different failure
                for k in (acc if self.mode == "all" else [self.rng.choice(acc)]): o.pop(k, None)
        return o

class NoisyEnumerator:
    """Code's set plus a plausible action that is NOT currently applicable. Models an enumerator that over-offers."""
    def __init__(self, rate=0.25, seed=0): self.rate = rate; self.rng = random.Random(seed); self.name = f"noise{rate}"
    ALL = ["walk", "walk_slow", "stop", "wait", "turn_away", "step_around", "follow_person", "pick_up", "put_down", "ask_operator"]
    def options(self, room, facts, subgoal):
        o = dict(room.options())
        if self.rng.random() < self.rate:
            extra = [k for k in self.ALL if k not in o]
            if extra: o[self.rng.choice(extra)] = "An action the enumerator believes is available."
        return o

class ValidatedEnumerator:
    """A generative enumerator's proposals, filtered by the declared preconditions. The architecture the hallucination
    result argues for: let the big model propose, let the contract check, let the typed chooser pick.

    The fallback is the whole experiment, so it is COUNTED, not hidden. The first version ended `return keep or valid`,
    which silently handed back code's entire option set whenever the model proposed nothing applicable -- so the
    condition quietly became the code enumerator exactly when the model failed, and the failure rate was invisible.
    Caught on the first row: the oracle took 233 decisions instead of 21 with 25 of them acceptable.

    fallback="code"   hand back the full declared set, and count it (an upper bound: assumes a safety net exists)
    fallback="none"   offer nothing, which ends the episode as paralysis (the lower bound, and the honest default)
    fallback="stop"   offer only `stop`, which is what a real stack with a watchdog would do"""
    def __init__(self, inner, fallback="stop"):
        self.inner = inner; self.fallback = fallback; self.name = f"validated({inner.name})/{fallback}"
        self.fallbacks = 0; self.calls = 0; self.kept = 0; self.rejected = 0
    def options(self, room, facts, subgoal):
        from stack.skills import applicable
        proposed = self.inner.options(room, facts, subgoal)
        valid = {b.key: b.doc for b in applicable(room)}
        keep = {k: v for k, v in proposed.items() if k in valid}
        self.calls += 1; self.kept += len(keep); self.rejected += len(proposed) - len(keep)
        if keep: return keep
        self.fallbacks += 1
        if self.fallback == "code": return valid
        if self.fallback == "stop": return {"stop": valid.get("stop", "stop")}
        return {}

# ---------------------------------------------------------------- Operator
class FreeOperator:
    """The operator this programme has always had: always available, answers instantly, costs a fixed four seconds."""
    name = "free"
    def __init__(self, ask_s=4.0): self.ask_s = ask_s; self.waited = 0.0; self.asks = 0; self.dropped = 0
    def ask(self, t): self.asks += 1; return 0.0, True

class QueuedOperator:
    """One operator, several robots. An ask joins a queue whose depth comes from the *measured* ask rate of the other
    robots, so an arm that asks a lot makes the queue worse for itself. Waits beyond `patience` are given up on.

    This is the layer the whole value proposition rests on and the one the bench has never had."""
    def __init__(self, fleet=4, other_ask_rate_hz=0.05, ask_s=4.0, patience=12.0, seed=0):
        self.fleet, self.rate, self.ask_s, self.patience = fleet, other_ask_rate_hz, ask_s, patience
        self.rng = random.Random(seed); self.waited = 0.0; self.asks = 0; self.dropped = 0
        self.name = f"queue{fleet}@{other_ask_rate_hz}"
    def ask(self, t):
        self.asks += 1
        others = self.fleet - 1
        ahead = sum(1 for _ in range(others) if self.rng.random() < self.rate * self.ask_s * others)
        wait = ahead * self.ask_s
        if wait > self.patience: self.dropped += 1; return wait, False
        self.waited += wait
        return wait, True

class VLMEnumerator:
    """The option set proposed by a local vision-language model looking through the robot's own head camera.

    There is no matcher here, which is the whole point. The model's lines go through skills.resolve(), the single
    text-to-skill function the scorer and every other layer also use, so the dialect mismatch that cost 549 lines in
    method error 59 cannot recur. A proposal that resolves to nothing in the library is counted, not silently dropped:
    E173 found those are mostly requests for skills the library does not have (a parameterised turn, a retreat, a gaze),
    which is information about the library rather than noise.

    Measured standing alone (E169/E173, 212 decisions, base-name basis, against a floor of 80.2% for a constant that
    always proposes {walk}): free-form image+facts offers an acceptable action on 91.5% of decisions but puts an
    inapplicable one in 80.7% of its sets. So raw is the honest-but-dangerous condition and
    ValidatedEnumerator(VLMEnumerator(...)) is the architecture this argues for."""
    _MODEL = None                                            # one load per process, not per episode

    def __init__(self, prompt="facts", tmp=None):
        self.prompt = prompt; self.name = f"vlm/{prompt}"
        self.tmp = tmp or os.path.join(os.environ.get("E169_TMP", "/tmp"), "vlm_frame.png")
        self.eye = None; self.proposed = 0; self.unresolved = 0

    @classmethod
    def _load(cls):
        if cls._MODEL is None:
            from mlx_vlm import load
            model, proc = load("mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
            cls._MODEL = (model, proc, model.config)
        return cls._MODEL

    def options(self, room, facts, subgoal):
        from PIL import Image
        from mlx_vlm import generate, apply_chat_template
        from humanoid.eye import Eye
        from humanoid.e169_enumerator import PROMPT_IMG, PROMPT_BOTH, facts_text
        from stack.skills import resolve, SKILLS
        model, proc, cfg = self._load()
        if self.eye is None: self.eye = Eye(room.model)
        self.eye.aim(room.xy(), room.yaw()); rgb, _ = self.eye.look(room.data)
        Image.fromarray(rgb).save(self.tmp)
        prompt = PROMPT_IMG if self.prompt == "image" else PROMPT_BOTH.format(facts=facts_text(facts))
        try:
            fp = apply_chat_template(proc, cfg, prompt, num_images=1)
            g = generate(model, proc, fp, image=[self.tmp], max_tokens=110, verbose=False)
            txt = g.text if hasattr(g, "text") else str(g)
        except Exception as e:
            txt = f"<error {type(e).__name__}>"
        out = {}
        for ln in txt.splitlines():
            ln = ln.strip()
            if not ln or len(ln) > 120: continue
            self.proposed += 1
            b = resolve(ln, room)
            if b is None: self.unresolved += 1
            else: out[b.key] = b.doc
        return out


class Library2Enumerator:
    """Skill library v2's applicable set: eight skills with explicit arguments instead of twelve with hidden ones.
    Option-set size rises from 8.5 to 23.9 after preconditions, which is the redesign's cost and the open question."""
    name = "lib2"
    def options(self, room, facts, subgoal):
        from stack.skills2 import applicable2
        return {b.key: b.doc for b in applicable2(room)}


class ConstrainedEnumerator:
    """The missing layer: a constraint that FILTERS rather than informs.

    E173 found a category of thing a real model asks for that no skill library can express -- "keep a safe distance from
    Zoe", "keep watch for the child". Those are not actions, they are conditions to hold WHILE doing something else.

    And the bench already computes one. `predicted_dist(key)` forward-simulates each candidate action two seconds and
    returns its closest approach to any person; the result was appended to every option's text as
    "Code's estimate: ... about 0.2 m from a person - touching distance". E171 measured that channel and found it
    INERT: stripping it moved the chooser by one episode out of forty and its acceptable-decision rate by 0.1 points.

    So the constraint is being computed, communicated in plain English, and ignored. This layer stops asking. An action
    predicted to violate the constraint is not offered.

    If EVERY action violates it, `fallback="safest"` offers only the least-violating one, which is what a real safety
    filter does -- it never leaves the chooser with an empty set, and it never silently hands back the unfiltered set
    (the mistake ValidatedEnumerator made, caught the same afternoon)."""
    def __init__(self, inner, min_m=0.5, fallback="safest"):
        self.inner = inner; self.min_m = min_m; self.fallback = fallback
        self.name = f"constrained({inner.name})@{min_m}"
        self.calls = 0; self.fired = 0; self.blocked = 0; self.fallbacks = 0

    def options(self, room, facts, subgoal):
        o = self.inner.options(room, facts, subgoal)
        self.calls += 1
        d = {}
        for k in o:
            try: d[k] = room.predicted_dist(k)
            except Exception: d[k] = 9.9                 # an action the forecaster does not model is not constrained
        keep = {k: v for k, v in o.items() if d[k] >= self.min_m}
        if len(keep) < len(o): self.fired += 1; self.blocked += len(o) - len(keep)
        if keep: return keep
        self.fallbacks += 1
        if self.fallback == "safest":
            best = max(d, key=lambda k: d[k]); return {best: o[best]}
        return o if self.fallback == "off" else {}


class PlannedLibrary2Enumerator:
    """Library v2's applicable set, with navigation restricted to the PLANNER's current target.

    This is the whole point of E180. v2's navigation options are `move_to(place, speed)` over every named place, and
    E177 measured the chooser re-picking a place every 1.5 seconds. Here the planner owns the place and the chooser owns
    everything else -- the speed, whether to stand, whether to retreat from someone, whether to ask. Retreat targets
    (`away:X`) stay on offer regardless of the plan, because backing away from a child is a decision about the moment
    and must not require the planner's permission.

    So the option set keeps v2's parameterisation and v2's new capability, and gives back v1's persistence."""
    name = "lib2planned"
    def options(self, room, facts, subgoal):
        from stack.skills2 import applicable2
        want = (subgoal or {}).get("target")
        out = {}
        for b in applicable2(room):
            n = b.skill.name; a = b.kwargs
            if n in ("move_to", "turn_to"):
                pl = a["place"]
                if pl.startswith("away:"): pass                  # the chooser's own call, always offered
                elif want is None or pl != want: continue        # otherwise only the planner's target
            out[b.key] = b.doc
        return out

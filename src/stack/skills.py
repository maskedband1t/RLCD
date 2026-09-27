"""The skill library, as one declaration that every layer imports.

Why this file exists. Before it, a "skill" was four unlinked fragments in three files: a name string in
`fetch_sim.OPTIONS`, a description string beside it, an execution branch in an eleven-way `elif` chain inside
`run_skill`, and a precondition expressed as an imperative `opts.pop(...)` line inside `options()`. `walk_slow` was
re-declared independently in four files. There were no typed parameters -- `hand_to_Maya` was a string key built by
f-string concatenation -- and no skill declared what it achieved, which is exactly why the Planner had to be scripted
out of existence: you cannot chain steps if nothing says what a step accomplishes.

Every layer-to-layer bug this programme has hit was a translator between two dialects of the same word. Method error 59
is the clean example: a vision model emitted `step_around` and the scorer was looking for `"step around"`, so 549
correct lines were discarded. `resolve()` below is now the ONLY place text becomes a skill, so there is no second
matcher to disagree with the first.

What each field is for, and which layer reads it:
  name, params    identity. Typed, so hand_to(person="Maya") rather than the string "hand_to_Maya".
  precondition    the Enumerator. Returns the offered set.
  effect          the Planner. A step chains onto a step whose effect satisfies the next one's precondition.
  doc             the Chooser. State-INDEPENDENT: no forecast, no availability hint (method error 50).
  cost_s          the Planner and any operator-time accounting.
  run             the Motion layer.

The preconditions here are transcribed from `fetch_sim.options()` and must reproduce it exactly; `verify()` checks that
state by state and is the only reason to trust the refactor.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Dict, Any, List
import os, re

# ---------------------------------------------------------------- the contract

@dataclass(frozen=True)
class Skill:
    name: str
    doc: str                                           # one sentence, true in every state
    params: Tuple[str, ...] = ()
    precondition: Optional[Callable] = None            # (room, args) -> bool
    # METHOD ERROR 62: these were one field called `effect`, and conflating them made every `walk` read as a motion
    # failure -- the oracle, which always picks an acceptable skill, came back 137/161 "motion failure". Two different
    # things:
    #   postcondition  true after ONE execution, or the motion layer failed to deliver. Only four skills have one.
    #   goal           what repeated execution approaches. Used by the Planner to chain, never to attribute a failure.
    #   progress       a scalar repeated execution should REDUCE. This is how a walking skill is held to account.
    postcondition: Optional[Callable] = None           # (room, args) -> bool
    goal: Optional[Callable] = None                    # (room, args) -> bool, the state chaining aims at
    progress: Optional[Callable] = None                # (room, args) -> float, lower is nearer
    cost_s: float = 0.5
    def bind(self, **args) -> "Bound":
        missing = set(self.params) - set(args)
        if missing: raise ValueError(f"{self.name} needs {sorted(missing)}")
        return Bound(self, tuple(sorted(args.items())))

@dataclass(frozen=True)
class Bound:
    """A skill with its arguments filled in. `key` is the wire format the existing bench speaks, so the contract can be
    introduced without rewriting run_skill: the old string keys are now DERIVED from typed parameters, not authored."""
    skill: Skill
    args: Tuple = ()
    @property
    def kwargs(self) -> Dict[str, Any]: return dict(self.args)
    @property
    def key(self) -> str:
        return self.skill.name if not self.args else self.skill.name + "_" + "_".join(str(v) for _, v in self.args)
    @property
    def doc(self) -> str: return self.skill.doc
    def holds(self, room) -> bool:
        p = self.skill.precondition
        return True if p is None else bool(p(room, self.kwargs))
    def achieved(self, room) -> Optional[bool]:
        """Did ONE execution deliver what the skill guarantees? None when the skill guarantees nothing."""
        e = self.skill.postcondition
        return None if e is None else bool(e(room, self.kwargs))
    def at_goal(self, room) -> Optional[bool]:
        g = self.skill.goal
        return None if g is None else bool(g(room, self.kwargs))
    def distance(self, room) -> Optional[float]:
        pr = self.skill.progress
        return None if pr is None else float(pr(room, self.kwargs))
    def run(self, room): return room.run_skill(self.key)
    def __str__(self): return self.key

# ---------------------------------------------------------------- the library
# Preconditions transcribed from fetch_sim.options(); the comment on each names the line it comes from.

def _always(room, a): return True
def _recent_pick_fail(room):
    t = getattr(room, "pickup_failed_at", None)
    return t is not None and room.t - t < 0.9          # R5c (E150)

SKILLS: Dict[str, Skill] = {}
def _reg(s: Skill) -> Skill: SKILLS[s.name] = s; return s

_reg(Skill("walk", "Walk toward the current destination at normal speed (about 0.7 m/s), steering around nothing.",
           precondition=_always, goal=lambda r, a: r.goal_dist() < 0.25,
           progress=lambda r, a: r.goal_dist(), cost_s=0.5))
_reg(Skill("walk_slow", "Walk toward the current destination slowly (about 0.35 m/s).",
           precondition=_always, goal=lambda r, a: r.goal_dist() < 0.25,
           progress=lambda r, a: r.goal_dist(), cost_s=0.5))
_reg(Skill("stop", "Stop and stand still where you are.", precondition=_always))
_reg(Skill("wait", "Stand still and wait two seconds for the people to move on.", precondition=_always, cost_s=2.0))
_reg(Skill("turn_away", "Turn to face away from the nearest person and stand still.", precondition=_always, cost_s=1.5))
_reg(Skill("follow_person", "Walk toward the nearest person and stop about two steps from them.", precondition=_always))
_reg(Skill("step_around",
           "Step around the nearest person: veer to the side for a moment, then continue toward the destination "
           "(near a child: back off first, then go around).",
           # options(): popped when person_dist() > 2.5, and when circling()
           precondition=lambda r, a: r.person_dist() <= 2.5 and not r.circling(), cost_s=4.0))
_reg(Skill("pick_up", "Pick the object up from the table (only works within reach of the table).",
           # options(): popped when holding is not None, or delivered/given/refused, or a recent failed pick, or gone
           precondition=lambda r, a: r.holding is None and not (r.delivered_to or r.given or r.refused)
                                     and not (_recent_pick_fail(r)) and not getattr(r, "object_gone", False),
           postcondition=lambda r, a: r.holding is not None, goal=lambda r, a: r.holding is not None, cost_s=1.5))
_reg(Skill("put_down", "Put the object down where you stand.",
           precondition=lambda r, a: r.holding is not None and not r.delivered_to,
           postcondition=lambda r, a: r.holding is None, goal=lambda r, a: r.holding is None, cost_s=1.0))
_reg(Skill("hand_to", "Hand the object you are holding to a named person who is within reach.", params=("person",),
           # options(): offered per person, only while holding and within 1.6 m
           precondition=lambda r, a: r.holding is not None
                                     and any(p.name == a["person"] and r.dist(p.xy) < 1.6 for p in r.people),
           postcondition=lambda r, a: r.given_to == a["person"], goal=lambda r, a: r.given_to == a["person"], cost_s=2.0))
_reg(Skill("ask_operator", "Ask the remote operator what to do (four seconds of their time).",
           precondition=_always, cost_s=4.0))
_reg(Skill("done", "The object has been delivered (or the hand-over refused): finish.",
           precondition=lambda r, a: bool(((r.delivered_to or r.given or r.refused) and r.withdrawn)
                                          or getattr(r, "job_closed", False)),
           postcondition=lambda r, a: bool(getattr(r, "declared_done", False)), goal=lambda r, a: bool(getattr(r, "declared_done", False))))

# Six of the twelve declare no goal -- stop, wait, turn_away, step_around, follow_person, ask_operator. That is not an
# omission: they are recovery actions that change the world without advancing the task, so a Planner cannot chain them.
# And only four guarantee a postcondition after one execution (pick_up, put_down, hand_to, done) while two carry a
# progress measure instead (walk, walk_slow); the remaining six can never be held to account for anything, which is a
# real structural fact about this library rather than a gap in the bookkeeping.
PLANNABLE = [n for n, s in SKILLS.items() if s.goal is not None]          # what a Planner can chain
ATTRIBUTABLE = [n for n, s in SKILLS.items() if s.postcondition is not None or s.progress is not None]

# ---------------------------------------------------------------- the enumerator's half of the contract

def all_bound(room) -> List[Bound]:
    """Every skill instance that EXISTS in this world, parameters enumerated, regardless of whether it applies."""
    out = []
    for s in SKILLS.values():
        if not s.params: out.append(s.bind())
        elif s.params == ("person",): out += [s.bind(person=p.name) for p in room.people]
        else: raise SystemExit(f"{s.name} has unhandled params {s.params}")
    return out

def applicable(room) -> List[Bound]:
    """The offered set, derived from the declared preconditions rather than from a sequence of pops."""
    return [b for b in all_bound(room) if b.holds(room)]

# ---------------------------------------------------------------- the ONE text->skill resolver
# Imported by the vision enumerator, by any scorer, and by anything that reads a model's words. Method error 59 was
# caused by there being two of these that disagreed; there is now one.

_SYN = {"walk_slow": ("walk slow", "slowly", "slow down", "creep", "cautiously", "carefully forward"),
        "step_around": ("step around", "go around", "side step", "sidestep", "avoid", "move aside", "steer around"),
        "turn_away": ("turn away", "turn around", "face away", "turn back"),
        "follow_person": ("follow",),
        "pick_up": ("pick up", "pickup", "grab", "grasp", "take the", "lift", "collect", "retrieve"),
        "put_down": ("put down", "set down", "place", "drop", "release", "put it"),
        "hand_to": ("hand to", "hand ", "give ", "deliver", "pass ", "hand over", "offer"),
        "ask_operator": ("ask", "request help", "call ", "operator", "check with", "query"),
        "done": ("done", "finish", "complete", "stop the task", "end task"),
        "wait": ("wait", "pause", "stand still", "hold", "remain"),
        "stop": ("stop", "halt", "brake", "stand"),
        "walk": ("walk", "move forward", "go forward", "drive", "advance", "approach", "navigate", "move toward",
                 "move towards", "move to ", "move closer", "move back", "return to", "return the", "head to",
                 "head towards", "go to ", "carry the", "proceed", "continue to", "continue towards",
                 "move through", "go through", "retreat back to")}
# The walk synonyms above were widened ONCE, after reading the 39 distinct phrasings a real model produced (E169's raw
# text). Every addition is a destination-phrasing of walk and none of them is ambiguous between two skills. Reported
# both ways in the notebook, because widening a translator after seeing its misses flatters whichever condition it
# rescues, and free-form is the condition it rescues.
_ORDER = ["walk_slow", "step_around", "turn_away", "follow_person", "pick_up", "put_down", "hand_to",
          "ask_operator", "done", "wait", "stop", "walk"]        # longest / most specific first

def resolve(text: str, room=None) -> Optional[Bound]:
    """One line of anybody's text -> a Bound skill, or None. Exact declared names win before any synonym, so a model
    told to emit `walk_slow` is never silently downgraded to `walk` (method error 59)."""
    s = text.lower().strip(" -*0123456789.)\t`\"'")
    people = [p.name for p in room.people] if room is not None else []
    for name in sorted(SKILLS, key=len, reverse=True):                       # exact declared names, longest first
        if s == name or s == name.replace("_", " "): return _fill(SKILLS[name], s, people, room)
        if s.startswith(name + "_") or s.startswith(name + " "):
            rest = s[len(name) + 1:].strip()
            if SKILLS[name].params and rest: return _fill(SKILLS[name], s, people, room, hint=rest)
            if s == name or not SKILLS[name].params and s.replace("_", " ") == name.replace("_", " "):
                return _fill(SKILLS[name], s, people, room)
    flat = s.replace("_", " ")
    for name in _ORDER:
        if any(k in flat for k in _SYN[name]): return _fill(SKILLS[name], s, people, room)
    return None

def _fill(skill: Skill, raw: str, people, room, hint: str = "") -> Optional[Bound]:
    if not skill.params: return skill.bind()
    if skill.params == ("person",):
        for p in people:                                                     # a name the world actually contains
            if p.lower() in raw or (hint and p.lower() in hint): return skill.bind(person=p)
        if room is not None:                                                 # otherwise the nearest, which is what
            try: return skill.bind(person=room.nearest().name)               # "hand it over" means in context
            except Exception: return None
    return None

# ---------------------------------------------------------------- verification

def verify(seeds=range(0, 40), steps=14, verbose=True):
    """The contract is worthless unless its preconditions reproduce the bench's own option set state by state."""
    from humanoid.fetch_sim import Room
    bad = tot = 0
    for sd in seeds:
        room = Room(sd)
        for i in range(steps):
            want = set(room.options()); got = {b.key for b in applicable(room)}
            tot += 1
            if want != got:
                bad += 1
                if verbose and bad <= 6:
                    print(f"  seed {sd} step {i} event={room.event}: contract-only {sorted(got - want)} | "
                          f"bench-only {sorted(want - got)}")
            room.run_skill("walk" if i % 3 else "wait")
    print(f"verify: {tot - bad}/{tot} states reproduce fetch_sim.options() exactly" + ("" if bad else "  EXACT"))
    return bad == 0

if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"{len(SKILLS)} skills declared")
    print(f"  plannable (declare a goal)        {len(PLANNABLE):>2}: {sorted(PLANNABLE)}")
    print(f"  postcondition after one run       {len([n for n,x in SKILLS.items() if x.postcondition]):>2}: "
          f"{sorted(n for n,x in SKILLS.items() if x.postcondition)}")
    print(f"  progress measure instead          {len([n for n,x in SKILLS.items() if x.progress]):>2}: "
          f"{sorted(n for n,x in SKILLS.items() if x.progress)}")
    print(f"  accountable for nothing           {len(set(SKILLS)-set(ATTRIBUTABLE)):>2}: "
          f"{sorted(set(SKILLS)-set(ATTRIBUTABLE))}\n")
    verify()

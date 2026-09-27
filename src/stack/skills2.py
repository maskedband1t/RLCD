"""Skill library v2: eight skills with explicit arguments, in place of twelve with hidden ones.

Why. E176 re-resolved the 1161 lines a real vision model produced against a parameterised vocabulary and unresolved fell
from 16.9% to 1.1% on the free-form condition (70.4% to 14.5% on image alone). The bound forms it asks for are
move_to 450, give 281, turn_to 174, pick 149, ask_operator 57, stand 37. The library below is that list, not taste.

What was wrong with v1. `walk`'s destination came from `room.destination()`, so it meant "go wherever the bench thinks
the goal is" -- an atomic-looking skill with a concealed argument, and the reason `move_to(table)` was inexpressible.
`walk`/`walk_slow` differed by a speed. `turn_away`/`step_around`/`follow_person` all navigated relative to a person who
was always implicitly the nearest. `stop`/`wait` differed by a duration.

**This is a DIFFERENT BENCH and its numbers are not comparable to the 165 experiments before it.** The action space is
larger, so choosing may well get harder -- that is the open question, not a foregone conclusion. Method error 60's
lesson at a larger scale: it gets its own name and its own file.

The honest cost is `reduces_to()`. The bench's `acceptable()` is authored in v1's vocabulary, so scoring v2 needs each
v2 action mapped to the v1 action it is equivalent to. Where that map is exact, v2 can be scored on the existing banks.
Where it is None, the action is something v1 could not express -- which is the point of v2, and also precisely what
cannot be scored until the acceptable sets are re-authored. Both counts are reported rather than papered over.
"""
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Dict, Any, List
import os
import numpy as np

# ---------------------------------------------------------------- places, the argument v1 hid

def places(room) -> Dict[str, Any]:
    """The named targets a navigation skill can be given.

    METHOD ERROR 65: the first version returned the OBJECTS -- `table` was TABLE and `person:Maya` was Maya's body
    centre. You cannot stand where a person is standing, so those goals could never complete, and `move_to(person:Maya)`
    was jev's most-chosen action in E177 (1280 times). A target that cannot be reached makes re-picking rational rather
    than thrashing, which confounded E177's commitment finding.

    `fetch_sim.destination()` had it right all along and these now match it exactly: TABLE + [-0.7, 0] to reach the
    table, and the requester's live position + [-1.4, 0] to reach a person."""
    from humanoid.fetch_sim import TABLE, DOOR_X
    p = {"destination": room.destination(),
         "table": np.asarray(TABLE) + np.array([-0.7, 0.0]),          # the approach point, as destination() uses
         "door": np.array([DOOR_X, room.xy()[1]])}
    req = getattr(room, "req", None)
    if req is not None: p["requester"] = np.asarray(req.xy) + np.array([-1.4, 0.0])
    # E180's four-episode gain over v1 is confounded between HAVING a planner and my approach geometry threading the
    # doorway better than the bench's own. FETCH_V2_APPROACH=fixed is the control: it uses destination()'s fixed -x
    # offset instead of the bearing-adaptive one. If the door collisions come back, the gain was geometry, not planning.
    adaptive = os.environ.get("FETCH_V2_APPROACH", "adaptive") != "fixed"
    for q in room.people:
        d = room.xy() - np.asarray(q.xy); n = float(np.linalg.norm(d))
        u = d / n if n > 1e-6 else np.array([1.0, 0.0])
        # adaptive: a step and a half short of the person on the robot's own side -- reachable from any bearing
        p[f"person:{q.name}"] = np.asarray(q.xy) + (u * 1.4 if adaptive else np.array([-1.4, 0.0]))
        p[f"away:{q.name}"] = room.xy() + u * 1.5
    return p

SPEEDS = {"normal": "at normal speed, about 0.7 m/s", "slow": "slowly, about 0.35 m/s"}
# stand(4.0) removed: it reduces to the same v1 action as stand(2.0), so it was pure redundancy in the action space,
# and it made the do-nothing floor incomparable across libraries (method error 63) -- v1's longest stillness is 2 s.
STILLS = {0.5: "briefly", 2.0: "for two seconds"}

# ---------------------------------------------------------------- the contract (same shape as v1)

@dataclass(frozen=True)
class Skill2:
    name: str
    doc: str
    params: Tuple[str, ...] = ()
    precondition: Optional[Callable] = None
    postcondition: Optional[Callable] = None
    progress: Optional[Callable] = None
    goal: Optional[Callable] = None
    cost_s: float = 0.5
    def bind(self, **a): return Bound2(self, tuple(sorted(a.items())))

@dataclass(frozen=True)
class Bound2:
    skill: Skill2
    args: Tuple = ()
    @property
    def kwargs(self): return dict(self.args)
    @property
    def key(self): return self.skill.name + ("" if not self.args else "(" + ",".join(f"{k}={v}" for k, v in self.args) + ")")
    @property
    def doc(self):
        a = self.kwargs
        if self.skill.name == "move_to": return f"Walk to the {a['place']} {SPEEDS[a['speed']]}."
        if self.skill.name == "turn_to": return f"Turn in place to face the {a['place']}."
        if self.skill.name == "stand":   return f"Stand still {STILLS[a['seconds']]}."
        if self.skill.name == "give":    return f"Hand what you are holding to {a['person']}."
        return self.skill.doc
    def holds(self, room): return True if self.skill.precondition is None else bool(self.skill.precondition(room, self.kwargs))
    def __str__(self): return self.key

SKILLS2: Dict[str, Skill2] = {}
def _r(s): SKILLS2[s.name] = s; return s

def _place_ok(room, a):
    """A navigation target must exist, be somewhere other than here, and be reachable in this room."""
    P = places(room); p = a["place"]
    if p not in P: return False
    if p.startswith("away:"):                                            # only meaningful with someone close
        who = p.split(":", 1)[1]
        return any(q.name == who and room.dist(q.xy) < 2.5 for q in room.people)
    if p == "table" and (room.holding is not None or room.delivered_to): return False   # nothing to fetch
    return room.dist(P[p]) > 0.4

_r(Skill2("move_to", "Walk to a named place.", ("place", "speed"),
          precondition=_place_ok,
          goal=lambda r, a: r.dist(places(r)[a["place"]]) < 0.4,
          progress=lambda r, a: r.dist(places(r)[a["place"]]), cost_s=0.5))
_r(Skill2("turn_to", "Turn in place to face a named place.", ("place",),
          precondition=lambda r, a: a["place"] in places(r) and abs(r.bearing_to(places(r)[a["place"]])) > 0.25,
          goal=lambda r, a: abs(r.bearing_to(places(r)[a["place"]])) < 0.25,
          progress=lambda r, a: abs(r.bearing_to(places(r)[a["place"]])), cost_s=1.5))
_r(Skill2("stand", "Stand still for a given time.", ("seconds",),
          precondition=lambda r, a: a["seconds"] in STILLS, cost_s=0.5))
_r(Skill2("pick", "Pick up the object on the table, if you are within reach of it.",
          precondition=lambda r, a: r.holding is None and not (r.delivered_to or r.given or r.refused)
                                    and not getattr(r, "object_gone", False),
          postcondition=lambda r, a: r.holding is not None,
          goal=lambda r, a: r.holding is not None, cost_s=1.5))
_r(Skill2("put_down", "Put what you are holding down where you stand.",
          precondition=lambda r, a: r.holding is not None and not r.delivered_to,
          postcondition=lambda r, a: r.holding is None,
          goal=lambda r, a: r.holding is None, cost_s=1.0))
_r(Skill2("give", "Hand what you are holding to a named person within reach.", ("person",),
          precondition=lambda r, a: r.holding is not None
                                    and any(q.name == a["person"] and r.dist(q.xy) < 1.6 for q in r.people),
          postcondition=lambda r, a: r.given_to == a["person"],
          goal=lambda r, a: r.given_to == a["person"], cost_s=2.0))
_r(Skill2("ask_operator", "Ask the remote operator what to do (four seconds of their time).",
          precondition=lambda r, a: True, cost_s=4.0))
_r(Skill2("done", "Finish: the object has been delivered, or the hand-over refused.",
          precondition=lambda r, a: bool(((r.delivered_to or r.given or r.refused) and r.withdrawn)
                                         or getattr(r, "job_closed", False)),
          postcondition=lambda r, a: bool(getattr(r, "declared_done", False)),
          goal=lambda r, a: bool(getattr(r, "declared_done", False))))

def all_bound2(room) -> List[Bound2]:
    out = []
    P = list(places(room))
    for s in SKILLS2.values():
        if not s.params: out.append(s.bind())
        elif s.params == ("place", "speed"): out += [s.bind(place=p, speed=v) for p in P for v in SPEEDS]
        elif s.params == ("place",): out += [s.bind(place=p) for p in P]
        elif s.params == ("seconds",): out += [s.bind(seconds=x) for x in STILLS]
        elif s.params == ("person",): out += [s.bind(person=q.name) for q in room.people]
        else: raise SystemExit(f"{s.name}: unhandled params {s.params}")
    return out

def applicable2(room) -> List[Bound2]: return [b for b in all_bound2(room) if b.holds(room)]

# ---------------------------------------------------------------- the bridge, and the honest cost

def reduces_to(b: Bound2, room) -> Optional[str]:
    """The v1 key this v2 action is EQUIVALENT to, or None when v1 could not express it. None is not a failure -- it is
    the capability v2 adds -- but it is also exactly what cannot be scored against banks authored in v1's vocabulary."""
    n = b.skill.name; a = b.kwargs
    if n == "pick": return "pick_up"
    if n == "put_down": return "put_down"
    if n == "give": return f"hand_to_{a['person']}"
    if n == "ask_operator": return "ask_operator"
    if n == "done": return "done"
    if n == "stand": return "wait" if a["seconds"] >= 2.0 else "stop"
    if n == "move_to":
        # METHOD ERROR 65 part 2: this compared the place NAME, so move_to(table) reduced to nothing even when the table
        # IS where destination() points -- so acceptable2 could not score the planner's own target and Oracle2 stood
        # still forever. The reduction is SEMANTIC: walking to X is v1's `walk` whenever X is where v1 was walking.
        P = places(room); here = P.get(a["place"])
        if here is not None and float(np.linalg.norm(np.asarray(here) - np.asarray(room.destination()))) < 0.35:
            return "walk" if a["speed"] == "normal" else "walk_slow"
        if a["place"].startswith("person:"): return "follow_person"
        return None                                   # a target v1 was NOT heading for: genuinely new
    if n == "turn_to":
        if a["place"].startswith("away:"): return "turn_away"
        return None                                   # turning to face a named place: genuinely new
    return None

# ---------------------------------------------------------------- the motion layer, over the sim's own primitives
# Nothing new in physics. v1's `walk` was `steer(CMD_FAST, room.destination())`; v2's move_to is the same call with the
# destination passed in rather than looked up. That is the entire difference, and it is why v2 needed no new simulator.

def run2(room, b: Bound2):
    """Execute one v2 action. Mirrors fetch_sim.run_skill's cadence exactly: walking skills use the decision cadence,
    fixed-duration skills use their own count, so gait behaviour is unchanged from v1."""
    from humanoid.fetch_sim import CMD_FAST, CMD_SLOW, DECISION_S
    n = int(round(0.5 / room.cdt)); nc = int(round(DECISION_S / room.cdt))
    name, a = b.skill.name, b.kwargs
    if name == "move_to":
        room.moving = True; room.fast = a["speed"] == "normal"
        room.steer(CMD_FAST if room.fast else CMD_SLOW, places(room)[a["place"]]); room.physics(nc)
    elif name == "turn_to":
        room.moving = False; room.fast = False
        err = room.bearing_to(places(room)[a["place"]])
        room.set_cmd(0.0, max(-0.8, min(0.8, 2.0 * err))); room.physics(3 * n); room.set_cmd(0, 0)
    elif name == "stand":
        room.moving = False; room.fast = False
        room.set_cmd(0, 0); room.physics(int(round(a["seconds"] / room.cdt)))
    else:
        room.run_skill(reduces_to(b, room))      # pick / put_down / give / ask_operator / done are v1 skills renamed,
                                                 # so they reuse the bench's own implementation unchanged
    return b


# ---------------------------------------------------------------- v2's arms and enumerator

class Oracle2:
    """FetchOracle's preference order, expressed over v2 actions. It reads the bench's true acceptable set (v1 keys) and
    takes the first preferred one, then picks any v2 action that reduces to it. Actions v1 cannot express are invisible
    to this oracle by construction -- it is a v1-optimal ceiling on a v2 action space, which is the right control: if a
    chooser beats it, the win came from the new actions."""
    name = "oracle2"
    ORDER = ["done", "hand_to", "put_down", "pick_up", "walk", "walk_slow", "step_around", "wait",
             "follow_person", "stop", "turn_away", "ask_operator"]
    def decide(self, f, opts, room):
        acc = room.acceptable()
        red = {}
        for k in opts:
            b = key_to_bound(k, room)
            if b is not None: red.setdefault(reduces_to(b, room), []).append(k)
        hands = sorted(x for x in acc if x.startswith("hand_to_"))
        for want in ["done"] + hands + [x for x in self.ORDER if x != "hand_to"]:
            if want in acc and want in red: return sorted(red[want])[0], {}
        return ("stand(seconds=0.5)" if "stand(seconds=0.5)" in opts else (sorted(opts)[0] if opts else "stand(seconds=0.5)")), {}

_BOUND_CACHE = {}
def key_to_bound(key, room):
    """v2 keys are self-describing -- move_to(place=table,speed=normal) -- so parsing one back is exact, no guessing."""
    if "(" not in key: return SKILLS2[key].bind() if key in SKILLS2 else None
    name, _, rest = key.partition("(")
    if name not in SKILLS2: return None
    args = {}
    for part in rest.rstrip(")").split(","):
        k, _, v = part.partition("=")
        args[k] = float(v) if k == "seconds" else v
    try: return SKILLS2[name].bind(**args)
    except Exception: return None

def acceptable2(room):
    """The v2 keys whose reduction is in the bench's acceptable set. Actions v1 could not express are NOT counted
    acceptable -- not because they are wrong, but because nothing has said whether they are, and guessing would be
    scoring my own redesign favourably."""
    acc = room.acceptable(); out = set()
    for b in applicable2(room):
        r = reduces_to(b, room)
        if r is not None and r in acc: out.add(b.key)
    return out

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from humanoid.fetch_sim import Room
    from stack.skills import applicable as applicable1
    print(f"{len(SKILLS2)} skills declared (v1 had 12)\n")
    tot = collections = 0
    import collections as C
    sizes1, sizes2, newc, mapc = [], [], C.Counter(), C.Counter()
    for sd in range(20):
        room = Room(sd)
        for i in range(12):
            b2 = applicable2(room); b1 = applicable1(room)
            sizes1.append(len(b1)); sizes2.append(len(b2))
            for b in b2:
                r = reduces_to(b, room)
                (newc if r is None else mapc)[b.key.split("(")[0]] += 1
            room.run_skill("walk" if i % 3 else "wait")
    print(f"option-set size after preconditions: v1 {sum(sizes1)/len(sizes1):.1f}   v2 {sum(sizes2)/len(sizes2):.1f}"
          f"   (v2 max {max(sizes2)})")
    n_new, n_map = sum(newc.values()), sum(mapc.values())
    print(f"of {n_new+n_map} offered v2 actions: {n_map} ({n_map/(n_new+n_map)*100:.0f}%) reduce to a v1 action, "
          f"{n_new} ({n_new/(n_new+n_map)*100:.0f}%) are NEW and unscoreable on v1-authored banks")
    print(f"  new, by skill: {dict(newc)}")
    print(f"  mapped, by skill: {dict(mapc)}")
    print("\nMOTION CHECK: v2's move_to(destination) must move the body exactly as v1's walk did")
    for speed, v1key in (("normal", "walk"), ("slow", "walk_slow")):
        ra, rb = Room(3), Room(3)
        for _ in range(8):
            ra.run_skill(v1key)
            run2(rb, SKILLS2["move_to"].bind(place="destination", speed=speed))
        da = float(np.linalg.norm(ra.xy() - rb.xy()))
        print(f"  {v1key:<10} vs move_to(destination,{speed:<6}) -> positions differ by {da:.4f} m"
              + ("   EXACT" if da < 1e-6 else "   *** DIVERGES ***"))

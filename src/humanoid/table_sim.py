"""Bench 5: clear the table. The first long-horizon task in this programme.

**Why a new bench and not a bigger one.** Every bench so far is a *fixed* sequence -- table, pick, requester, hand over,
done -- so there has never been a choice about ORDER, and therefore never any compounding. Here three objects must each be
carried to a tray, the order matters for real reasons, and one mistake is permanent. That breaks seven assumptions the
programme's measurement model rests on, which is why this is a mental-model change rather than a longer episode:

  acceptability  was a per-decision ground truth; here two orders can both be defensible and which was right depends on
                 what happens thirty decisions later. `acceptable()` and the chance bar do not survive the move.
  the oracle     was "first preferred action in the acceptable set"; a ceiling arm here needs SEARCH over futures.
  mistakes       were forgiving -- E170 showed a 25% enumerator fault cost the oracle 16 points of acceptable decisions
                 and ZERO handled, because you can waste decisions and still arrive. A broken glass is not 0.5 seconds.
  the probability stops answering "am I right about this action" and starts answering "does this foreclose the rest".
  credit         layer attribution says WHICH LAYER failed; nothing says which of forty decisions did.
  a correction   was "this action, not that one"; here it can be "this ORDER, not that order".
  success        was a boolean; here it is subtasks cleared, damage done, and time.

**The body is identical on purpose.** This subclasses `fetch_sim.Room`, so the G1, the MuJoCo Playground walking policy,
the physics loop, the people and `steer`/`set_cmd` are the same code. The motion layer's own measured failure rate (5.6% of
correctly-chosen skills, E175) therefore carries over rather than being re-earned, and any difference in outcome is the
task, not the robot.

**It is inherently parameterised, which is the point.** `pick(glass)` against `pick(box)` IS the choice, so this bench
speaks skill library v2's shape natively and the Planner is not optional -- the plan *is* the ordering.

The ordering structure, and each clause exists to create one specific decision:
  glass   fragile. Carried at full walking speed it breaks, and a break is terminal. So the chooser must trade time for
          care, which is the first genuine cost/risk decision in the programme.
  box     heavy, and it physically blocks the mug. `pick(mug)` is unavailable until the box has moved, so a chooser that
          reaches for the mug first has wasted a decision and learned nothing.
  mug     blocked by the box. The only hard ordering constraint, so there is a right answer to find.
  a person stands near the table at the start and leaves. Clearing the near object first means working beside them;
          waiting costs time. The same trade as the glass, on a different axis.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, mujoco
from humanoid.fetch_sim import (Room, Person, assets, G1_DIR, TABLE, DOOR_X, CMD_FAST, CMD_SLOW, DECISION_S,
                                NEAR, CLOSE, TOUCH)

TRAY = np.array([4.6, -1.2])        # where cleared objects go, on the robot's side of the doorway
MAX_T_TABLE = 240.0                 # four minutes: three carries is genuinely longer than one fetch
FRAGILE_SPEED = 0.5                 # m/s of commanded forward speed above which the glass breaks while held
# THE REFERENCE TIME, and what it is not. This was `TELEOP_REF_S = 62.5` with the comment "measured, not assumed: a human
# picks the order and the speed". the author asked how we knew that. We did not. No human ever drove this robot: I wrote the
# order and the speeds by hand, the simulator ran the script, the median of twelve runs was 62.5 s, and then the script
# was not kept -- so the number could not be re-derived by anyone, including me. A reference with no runnable arm behind
# it is a guess with a decimal point.
#
# `stack/scripted_ref.py` is that arm, written out explicitly. It measures 45.0 s median, 12/12 success, range 26.5-54.0.
# The 62.5 cannot be reconciled with it because the original script no longer exists, so the reproducible number wins.
#
# It is a SCRIPTED OPTIMAL policy: perfect information, zero reaction time, no camera latency, never hesitates or
# misjudges depth. A person driving a real robot through a video link has all four. So this is a LOWER BOUND on human
# remote operation, not an estimate of it, and every ratio against it flatters the autonomous arms by an unknown margin.
# Argon's convention (task time against a reference) and Epoch AI's 2026 survey ("robots are typically 3-10x slower than
# humans") both denominate in HUMAN time, which this is not, so neither citation licenses comparing our multiple to
# theirs.
SCRIPTED_REF_S = 45.0
TELEOP_REF_S = SCRIPTED_REF_S       # kept so old call sites keep working; the name is wrong and is being retired

# name, half-size, mass, colour, fragile, blocks
OBJECTS = [
    ("glass", 0.045, 0.25, "0.75 0.85 0.95 1", True,  None),
    ("box",   0.070, 1.20, "0.65 0.50 0.35 1", False, "mug"),
    ("mug",   0.050, 0.35, "0.85 0.85 0.30 1", False, None),
]
OBJ_XY = {"glass": (-0.22, 0.10), "box": (0.18, -0.02), "mug": (0.30, -0.02)}   # offsets from TABLE; mug behind box
OBJ_JITTER = 0.045      # m, uniform per axis per object, seeded
START_JITTER_M = 0.12   # m, the robot's own starting position
START_JITTER_RAD = 0.22 # rad, its starting heading

# METHOD ERROR 77. The seed used to vary exactly two things: which disruption fires (`seed % 5`) and where the person
# starts. On the three disruptions where the person never approaches the work area, the second could not matter, so all
# five replicates of those were THE SAME EPISODE -- identical outcome, identical elapsed time, identical jerk to the
# decimal. 25 seeds produced 12 distinct outcomes, and five of E193's seven "falls" were one fall counted five times.
#
# Jittering the objects varies something that matters on EVERY episode: the approach heading, the reach margin at the
# table, and the order the arm can comfortably take them in. The blocking relation is declared in OBJECTS rather than
# computed from geometry, so `box blocks mug` survives the jitter and the bench's one structural constraint is intact.


def jittered_obj_xy(seed):
    import random as _r
    g = _r.Random(70_000 + seed)
    return {n: (x + g.uniform(-OBJ_JITTER, OBJ_JITTER), y + g.uniform(-OBJ_JITTER, OBJ_JITTER))
            for n, (x, y) in OBJ_XY.items()}


class TableRoom(Room):
    """Clear the table. Subclasses the fetch room so the body, policy and physics are literally the same code."""

    def __init__(self, seed):
        self.cleared = []            # set before super().__init__ because build() reads them
        self.broken = []
        self.carry_fast_while_fragile = 0
        self.wasted_picks = 0
        self.placed_at = {}
        self.seed_ = seed
        super().__init__(seed, event="clear_table")
        self.MAX_T = MAX_T_TABLE

    # ---------------------------------------------------------------- the world
    def build(self):
        xml = open(os.path.join(G1_DIR, "xmls", "scene_mjx_feetonly_flat_terrain.xml")).read()
        people = "".join(
            f'<body name="{p.name}" mocap="true" pos="{p.xy[0]} {p.xy[1]} 0.85">'
            f'<geom type="capsule" size="0.22 0.55" rgba="{"0.9 0.5 0.2 1" if p.kind == "child" else "0.3 0.5 0.8 1"}"'
            f' contype="0" conaffinity="0"/></body>' for p in self.people)
        objs = "".join(
            f'<body name="{n}" pos="{TABLE[0] + self._oxy[n][0]} {TABLE[1] + self._oxy[n][1]} 0.8"><freejoint/>'
            f'<geom type="box" size="{s} {s} {s * 1.2}" mass="{m}" rgba="{c}" contype="0" conaffinity="0"/></body>'
            for n, s, m, c, _f, _b in OBJECTS)
        scene = (f'<body name="table" pos="{TABLE[0]} {TABLE[1]} 0.36">'
                 f'<geom type="box" size="0.45 0.3 0.36" rgba="0.5 0.35 0.2 1" contype="0" conaffinity="0"/></body>'
                 f'<body name="tray" pos="{TRAY[0]} {TRAY[1]} 0.08">'
                 f'<geom type="box" size="0.35 0.28 0.08" rgba="0.35 0.38 0.42 1" contype="0" conaffinity="0"/></body>'
                 + objs + people)
        eq = "<equality>" + "".join(
            f'<weld name="hold_{n}" body1="right_wrist_yaw_link" body2="{n}" active="false" relpose="0.05 0 0 1 0 0 0"/>'
            f'<weld name="rest_{n}" body1="world" body2="{n}" active="true"/>' for n, *_ in OBJECTS) + "</equality>"
        xml = xml.replace("</worldbody>", scene + "</worldbody>", 1).replace("</mujoco>", eq + "</mujoco>", 1)
        self.model = mujoco.MjModel.from_xml_string(xml, assets=assets())
        self.data = mujoco.MjData(self.model); self.model.opt.timestep = 0.002
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.keyframe("knees_bent").id)
        # Jittering the OBJECTS alone changed nothing measurable, and that is worth recording: the robot navigates to the
        # TABLE as a place, not to each object, and picks by name behind a 1.3 m reach test, so a few centimetres of
        # object offset never reaches the dynamics. The robot's own starting pose does: it sets the approach heading, the
        # distance to walk, and how much turning the gait has to absorb before it gets there. A real robot does not start
        # from the same square twice either.
        import random as _r
        _g = _r.Random(60_000 + getattr(self, "seed_", 0))
        self.data.qpos[0] += _g.uniform(-START_JITTER_M, START_JITTER_M)
        self.data.qpos[1] += _g.uniform(-START_JITTER_M, START_JITTER_M)
        _yaw = _g.uniform(-START_JITTER_RAD, START_JITTER_RAD)
        self.data.qpos[3:7] = [math.cos(_yaw / 2), 0.0, 0.0, math.sin(_yaw / 2)]
        for n, *_ in OBJECTS:
            bid = self.model.body(n).id; jadr = self.model.jnt_qposadr[self.model.body_jntadr[bid]]
            self.data.qpos[jadr:jadr + 7] = [TABLE[0] + self._oxy[n][0], TABLE[1] + self._oxy[n][1], 0.8, 1, 0, 0, 0]
        self.data.qvel[:] = 0
        for p in self.people: p.mid = self.model.body(p.name).mocapid[0]
        self.eq = {}
        for n, *_ in OBJECTS:
            self.eq[f"hold_{n}"] = self.model.equality(f"hold_{n}").id
            self.eq[f"rest_{n}"] = self.model.equality(f"rest_{n}").id
        mujoco.mj_forward(self.model, self.data)
        self.holder = None; self.start_xy = self.xy().copy(); self.started = False
        self.pickup_failed_at = None; self.cart_mid = None

    # ---------------------------------------------------------------- object queries
    def obj_xy(self, n):
        return self.data.body(n).xpos[:2].copy()

    def obj_z(self, n):
        return float(self.data.body(n).xpos[2])

    def props(self, n):
        for nm, s, m, c, frag, blocks in OBJECTS:
            if nm == n: return dict(half=s, mass=m, fragile=frag, blocks=blocks)
        raise KeyError(n)

    def at_table(self, n):
        """Is this object PHYSICALLY still on the table? Position, not bookkeeping.

        The first version asked whether the object was in `cleared`, which made blocking a bookkeeping relation rather
        than a physical one: the box dropped on the floor was not `cleared`, so the mug behind it stayed blocked even
        though nothing was in front of it any more. Blocking is geometry."""
        if n in self.broken or self.holding == n: return False
        return self.dist_xy(self.obj_xy(n), TABLE) < 0.65 and self.obj_z(n) > 0.5

    @staticmethod
    def dist_xy(a, b):
        return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))

    def blocked_by(self, n):
        """The object physically in front of n, if it is still on the table."""
        for nm, *_rest in OBJECTS:
            if self.props(nm)["blocks"] == n and self.at_table(nm): return nm
        return None

    def on_table(self):
        return [n for n, *_ in OBJECTS if self.at_table(n)]

    def pickable(self):
        """Anything not broken, not held, and not already in the tray -- including objects on the floor, which are a
        recoverable mistake precisely because they can be picked up again."""
        return [n for n, *_ in OBJECTS
                if n not in self.broken and self.holding != n and self.placed_at.get(n) != "tray"]

    def remaining(self):
        return [n for n, *_ in OBJECTS if n not in self.cleared and n not in self.broken]

    def table_reach(self, m=1.3):
        return self.dist(TABLE) < m

    def tray_reach(self, m=1.35):
        """1.35 m, not 1.0: the tray's approach point is 0.8 m out and the navigation tolerance is about 0.45, so a
        robot that has correctly arrived can stand 1.25 m from the tray body. At 1.0 it placed the box on the floor
        while standing beside the tray."""
        return self.dist(TRAY) < m

    # ---------------------------------------------------------------- places (v2's shape, natively)
    def places(self):
        p = {"table": np.asarray(TABLE) + np.array([-0.7, 0.0]), "tray": np.asarray(TRAY) + np.array([-0.8, 0.0])}
        for q in self.people:
            d = self.xy() - np.asarray(q.xy); n = float(np.linalg.norm(d))
            u = d / n if n > 1e-6 else np.array([1.0, 0.0])
            p[f"away:{q.name}"] = self.xy() + u * 1.5
        return p

    # ---------------------------------------------------------------- the skills
    # Three severities of mistake, deliberately graded, because a bench with only one kind of failure cannot teach a
    # chooser what a probability is for:
    #   wasted      pick a blocked object -- costs half a second, nothing changes, recoverable
    #   recoverable place away from the tray -- the object is on the floor, pickable again, costs a round trip
    #   terminal    carry the glass at walking speed -- it breaks, and nothing recovers it
    def run_skill(self, key):
        n = int(round(0.5 / self.cdt)); nc = int(round(DECISION_S / self.cdt))
        name, _, rest = key.partition("(")
        args = {}
        for part in rest.rstrip(")").split(","):
            k, _, v = part.partition("=")
            if k: args[k] = v

        if name == "move_to":
            place = args.get("place", "table"); speed = args.get("speed", "normal")
            vx = CMD_FAST if speed == "normal" else CMD_SLOW
            self.moving = True; self.fast = speed == "normal"
            # `clear:table` had no consequence until this existed: a person arrived, the assumption flipped, and the
            # teleop reference still scored a perfect 3/3 in the same 62.5 s. An assumption nothing punishes cannot be
            # measured, so E184's precision on it would have been vacuous. fetch_sim's near-contact threshold is 0.5 m,
            # tuned for passing someone in a corridor; working at a shared table is a metre.
            if min((self.dist(q.xy) for q in self.people), default=9.9) < WORKSPACE_R and speed == "normal":
                self.workspace_violations += 1
            self._fragile_risk(vx)                      # checked BEFORE the step: the decision is what breaks it
            self._steer_tight(vx, self.places().get(place, self.places()["table"])); self.physics(nc)

        elif name == "turn_to":
            place = args.get("place", "table")
            self.moving = False; self.fast = False
            err = self.bearing_to(self.places().get(place, self.places()["table"]))
            self.set_cmd(0.0, max(-0.8, min(0.8, 2.0 * err))); self.physics(3 * n); self.set_cmd(0, 0)

        elif name == "stand":
            self.moving = False; self.fast = False
            self.set_cmd(0, 0); self.physics(int(round(float(args.get("seconds", 0.5)) / self.cdt)))

        elif name == "pick":
            obj = args.get("object", "")
            self.moving = False; self.fast = False; self.set_cmd(0, 0)
            near = self.table_reach() if self.at_table(obj) else self.dist(self.obj_xy(obj)) < 1.0
            ok = (obj in self.pickable() and self.holding is None and near
                  and self.blocked_by(obj) is None and obj not in getattr(self, "removed", []))
            self.last_pick_failed = None
            if ok and getattr(self, "disruption", "") == "pick_fails" and not self.pick_fail_used and self.cleared:
                ok = False; self.pick_fail_used = True; self.last_pick_failed = obj   # a grasp that slips, once
                if self.fired_at is None: self.fired_at = self.t
            elif not ok and obj in self.remaining(): self.last_pick_failed = obj
            if not ok and obj in self.remaining(): self.wasted_picks += 1
            self.physics(2 * n)
            if ok:
                bid = self.model.body(obj).id; jadr = self.model.jnt_qposadr[self.model.body_jntadr[bid]]
                palm = self.data.site_xpos[self.model.site("right_palm").id]
                self.data.eq_active[self.eq[f"rest_{obj}"]] = 0
                self.data.qpos[jadr:jadr + 3] = palm + np.array([0.05, 0, 0])
                self.data.qpos[jadr + 3:jadr + 7] = [1, 0, 0, 0]
                mujoco.mj_forward(self.model, self.data)
                self.data.eq_active[self.eq[f"hold_{obj}"]] = 1
                self.holding = obj; self.pick_t = self.t
            self.physics(n)

        elif name == "place":
            self.moving = False; self.fast = False; self.set_cmd(0, 0)
            held = self.holding
            self.physics(2 * n)
            if held is not None:
                at_tray = self.tray_reach()
                pos = (np.array([TRAY[0], TRAY[1], 0.18]) if at_tray
                       else np.append(self.obj_xy(held), 0.06))            # otherwise it goes on the floor
                self.model.eq_data[self.eq[f"rest_{held}"], 3:6] = pos
                self.model.eq_data[self.eq[f"rest_{held}"], 6:10] = [1, 0, 0, 0]
                self.data.eq_active[self.eq[f"hold_{held}"]] = 0
                self.data.eq_active[self.eq[f"rest_{held}"]] = 1
                self.holding = None
                self.placed_at[held] = "tray" if at_tray else "floor"
                if at_tray and held not in self.cleared: self.cleared.append(held)
                elif not at_tray and held in self.cleared: self.cleared.remove(held)
                mujoco.mj_forward(self.model, self.data)
            self.physics(n)

        elif name == "ask_operator":
            self.cmd_target = np.array((0.0, 0.0, 0.0), np.float32); self.physics(8 * n)
            self.operator_asks += 1

        elif name == "done":
            self.declared_done = True; self.set_cmd(0, 0); self.physics(n)

        else:
            self.set_cmd(0, 0); self.physics(n)

    def _steer_tight(self, vx, target):
        """This bench's own navigation law, and fetch_sim.steer is left untouched so no earlier result moves.

        fetch_sim walks forward whenever the bearing error is under 1.2 rad while turning at most 0.8 rad/s. Its targets
        sit three metres apart, so the resulting arc never mattered. Here the table and the tray are 1.9 m apart --
        comparable to that turning radius -- and the robot arced past the tray and circled, placing two of three objects
        on the floor. Turning in place first above 0.35 rad costs a little time and converges."""
        err = self.bearing_to(target)
        wz = max(-0.8, min(0.8, 2.0 * err))
        self.set_cmd(0.0 if abs(err) > 0.35 else vx, wz)

    def _fragile_risk(self, vx):
        """A fragile object carried above FRAGILE_SPEED breaks. Keyed to the COMMANDED speed, not the measured one,
        because the command is what the chooser decided and that keeps the causal link teachable -- a correction can
        say 'that speed, with that object'. The simplification is recorded: a real glass breaks on impact, not on
        velocity, and modelling impact needs contact geometry these objects do not have (contype=0)."""
        if self.holding is not None and self.props(self.holding)["fragile"] and vx > FRAGILE_SPEED:
            self.carry_fast_while_fragile += 1
            broken = self.holding
            self.data.eq_active[self.eq[f"hold_{broken}"]] = 0
            self.broken.append(broken); self.holding = None
            if broken in self.cleared: self.cleared.remove(broken)

# ---------------------------------------------------------------- the world shifting mid-task
# Every disruption is STATE-triggered, never clock-triggered. Method errors 48 and 49 were both clock-timed events that
# fired before the robot had reached the situation they were about, so the bench was testing the clock and not the robot.
# Each one fires off something the robot itself did.
DISRUPTIONS = ["none", "person_at_table", "person_at_tray", "object_removed", "pick_fails"]
STAND_S = 22.0          # how long a person lingers once they arrive
PERSON_SPEED = 0.9      # m/s
WORKSPACE_R = 1.0       # m: moving at full speed inside this radius of a person is a violation

ASSUME_TERMS = ("on_table:", "exists:", "unblocked:", "holding:", "clear:table", "clear:tray")
TRIGGERS = ("person_near_table", "person_near_tray", "object_gone:", "pick_failed:")


class TableRoom(TableRoom):          # noqa: F811  -- extends the class defined above, same file
    def __init__(self, seed):
        self.disruption = DISRUPTIONS[seed % len(DISRUPTIONS)]
        self._oxy = jittered_obj_xy(seed)
        self.removed = []
        self.fired_at = None
        self.pick_fail_used = False
        self.last_pick_failed = None
        self._arrive_target = None
        self._stand_until = None
        self.workspace_violations = 0
        super().__init__(seed)

    # ---- the assumption vocabulary, evaluated by code at every decision, no model call
    def assume_holds(self, a):
        if a == "clear:table": return self.person_dist_to(TABLE) > 1.5
        if a == "clear:tray": return self.person_dist_to(TRAY) > 1.5
        if a == "holding:none": return self.holding is None
        if a.startswith("holding:"): return self.holding == a.split(":", 1)[1]
        if a.startswith("on_table:"): return self.at_table(a.split(":", 1)[1])
        if a.startswith("exists:"):
            o = a.split(":", 1)[1]; return o not in self.broken and o not in self.removed
        if a.startswith("unblocked:"): return self.blocked_by(a.split(":", 1)[1]) is None
        return None                                   # outside the declared vocabulary: recorded, never guessed at

    def broken_assumptions(self, assumes):
        return [a for a in (assumes or []) if self.assume_holds(a) is False]

    def unknown_assumptions(self, assumes):
        return [a for a in (assumes or []) if self.assume_holds(a) is None]

    def active_triggers(self):
        t = []
        if self.person_dist_to(TABLE) <= 1.5: t.append("person_near_table")
        if self.person_dist_to(TRAY) <= 1.5: t.append("person_near_tray")
        t += [f"object_gone:{o}" for o in self.removed]
        if self.last_pick_failed: t.append(f"pick_failed:{self.last_pick_failed}")
        return t

    def person_dist_to(self, xy):
        return min((self.dist_xy(p.xy, xy) for p in self.people), default=9.9)

    # ---- the disruptions themselves
    def step_people(self, dt):
        """Overrides the fetch room's event-specific people logic, which branches on events this bench does not have."""
        d = self.disruption
        if d == "person_at_table" and self.fired_at is None and self.dist(TABLE) < 2.0:
            self.fired_at = self.t; self._arrive_target = np.asarray(TABLE) + np.array([0.0, 0.55])
        elif d == "person_at_tray" and self.fired_at is None and self.holding is not None:
            self.fired_at = self.t; self._arrive_target = np.asarray(TRAY) + np.array([0.0, 0.55])
        elif d == "object_removed" and self.fired_at is None and self.cleared:
            self.fired_at = self.t
            gone = next((o for o in self.remaining() if o != self.holding), None)
            if gone:
                # METHOD ERROR 70: the first version wrote the object's qpos directly and called mj_forward mid-episode.
                # That perturbs the whole physics state and TOPPLED THE ROBOT -- both arms fell at exactly t=24.5 on
                # every object_removed seed, identical to the tick, which is the signature of the bench and not the
                # chooser. Forcing the disruption off made the same seeds clear 3/3 upright. Moving the weld TARGET lets
                # the constraint carry the object away over the following steps, touching nothing else; the object has
                # contype=0 so it collides with nothing on the way out.
                self.removed.append(gone)
                self.model.eq_data[self.eq[f"rest_{gone}"], 3:6] = [40.0, 40.0, 0.2]

        if self._arrive_target is not None:
            p = self.people[0]
            gap = self._arrive_target - p.xy; nrm = float(np.linalg.norm(gap))
            if nrm > 0.15 and self._stand_until is None:
                p.v = gap / nrm * PERSON_SPEED; p.mode = "walking"; p.attention = "walking"
            else:
                if self._stand_until is None: self._stand_until = self.t + STAND_S
                if self.t < self._stand_until:
                    p.v[:] = 0; p.mode = "standing"; p.attention = "looking_at_the_robot"
                else:
                    p.v = np.array([0.9, 0.35]); p.mode = "leaving"     # wanders off again
            p.xy = p.xy + p.v * dt
            self.data.mocap_pos[p.mid] = [p.xy[0], p.xy[1], 0.85]

    def record(self):
        """The episode outcome. No `acceptable()` and no per-decision ground truth: in a path-dependent task two orders
        can both be defensible, so the episode is scored and the decisions are recorded rather than judged one by one.
        `success` takes breakage as terminal, which is the default flagged to the author and not overridden."""
        floor = [o for o, w in self.placed_at.items() if w == "floor" and o not in self.cleared]
        return {"seed": self.seed_, "disruption": self.disruption, "fired_at": self.fired_at,
                "cleared": len(self.cleared), "cleared_objects": list(self.cleared),
                "broken": len(self.broken), "broken_objects": list(self.broken),
                "removed": list(self.removed), "on_floor": len(floor),
                "wasted_picks": self.wasted_picks, "fast_while_fragile": self.carry_fast_while_fragile,
                "workspace_violations": self.workspace_violations,
                "interventions": self.operator_asks,
                "teleop_multiple": round(self.t / TELEOP_REF_S, 2),
                "t_end": round(self.t, 2), "fell": int(self.fell),
                "success": int(len(self.broken) == 0 and self.workspace_violations == 0 and not self.fell
                               and len(self.cleared) == len([n for n, *_ in OBJECTS if n not in self.removed]))}

    # ---------------------------------------------------------------- facts, for a chooser
    def facts(self):
        """Bench 5's own typed facts. The inherited ones describe the fetch task (one object, a requester, a doorway)
        and would tell a chooser about a world that is not there.

        Categorical, not numeric: E70 measured +46.9 points for bands over raw distances, and every bench since has
        reported them this way."""
        near = self.nearest() if self.people else None
        left = []
        for n, *_ in OBJECTS:
            if n in self.broken or n in self.removed or self.placed_at.get(n) == "tray": continue
            blk = self.blocked_by(n)
            left.append({"name": n, "fragile": self.props(n)["fragile"],
                         "where": ("in_your_hand" if self.holding == n
                                   else "on_the_table" if self.at_table(n) else "on_the_floor"),
                         "blocked_by": blk})
        return {
            "task": "Clear every object from the table into the tray. One hand: carry one at a time. "
                    "A fragile object carried at walking speed breaks, and a break cannot be undone.",
            "robot": {"status": "walking" if self.moving else "standing",
                      "speed": ("normal" if self.fast else "slow") if self.moving else "stopped",
                      "holding": self.holding or "nothing",
                      "holding_is_fragile": bool(self.holding and self.props(self.holding)["fragile"]),
                      "table": self.band(self.dist(TABLE)), "tray": self.band(self.dist(TRAY))},
            "objects_left": left,
            "cleared_so_far": list(self.cleared),
            "gone_from_the_scene": list(self.broken) + list(self.removed),
            "person": ({"name": near.name, "kind": near.kind, "distance": self.band(self.dist(near.xy)),
                        "motion": near.mode, "attention": near.attention,
                        "distance_to_the_table": self.band(self.dist_xy(near.xy, TABLE)),
                        "distance_to_the_tray": self.band(self.dist_xy(near.xy, TRAY))} if near else None),
            "notes_from_operators": [],
            "recent_actions": list(self.recent)[-4:],
        }

    # ---------------------------------------------------------------- the twin
    # Real2Sim2Real's promise is that the correction loop runs in a twin before the floor. In simulation the twin is the
    # sim itself, so a planner can ASK what a candidate plan does before committing to it. That needs exact
    # save/restore, and hand-picking fields does not give it: a first attempt saved qpos, qvel, ctrl, act and the Python
    # bookkeeping, and three rollouts from the "same" state landed the robot 5-10 cm apart, because MuJoCo carries
    # integration state (warm-start accelerations, applied forces, solver history) that is not in those arrays.
    # mjSTATE_INTEGRATION is MuJoCo's own full integration state and covers all of it, including eq_active.
    # model.eq_data still needs saving by hand, because placing an object and removing one both mutate the MODEL.
    _STATE_SPEC = None

    def snapshot(self):
        import mujoco as _mj
        # forward BOTH sides before serialising: restore ends with mj_forward, so snapshotting a live state that has not
        # been forwarded made the first rollout differ from every later one while later ones matched each other exactly.
        _mj.mj_forward(self.model, self.data)
        if TableRoom._STATE_SPEC is None:
            TableRoom._STATE_SPEC = int(_mj.mjtState.mjSTATE_INTEGRATION)
        n = _mj.mj_stateSize(self.model, TableRoom._STATE_SPEC)
        buf = np.zeros(n, np.float64)
        _mj.mj_getState(self.model, self.data, buf, TableRoom._STATE_SPEC)
        return {
            "mj": buf, "eq_data": self.model.eq_data.copy(),
            "py": dict(
                t=self.t, holding=self.holding, cleared=list(self.cleared), broken=list(self.broken),
                removed=list(self.removed), placed_at=dict(self.placed_at), declared_done=self.declared_done,
                cmdv=self.cmdv.copy(), phase=self.phase.copy(), last=self.last.copy(),
                cmd_target=(self.cmd_target.copy() if hasattr(self, "cmd_target") else None),
                moving=self.moving, fast=self.fast, fell=self.fell, hold_alpha=self.hold_alpha,
                arm_hold=(dict(self.arm_hold) if self.arm_hold else None),
                wasted_picks=self.wasted_picks, workspace_violations=self.workspace_violations,
                carry_fast_while_fragile=self.carry_fast_while_fragile, recent=list(self.recent),
                near_contact=self.near_contact_events, child_zone=self.child_zone_events,
                door_collisions=self.door_collisions, min_person_dist=self.min_person_dist,
                in_contact=self._in_contact, in_zone=self._in_zone, in_door=self._in_door,
                operator_asks=self.operator_asks, pick_t=getattr(self, "pick_t", None),
                pickup_failed_at=self.pickup_failed_at, last_pick_failed=self.last_pick_failed,
                pick_fail_used=self.pick_fail_used, fired_at=self.fired_at,
                stand_until=self._stand_until, arrive=(None if self._arrive_target is None
                                                      else self._arrive_target.copy()),
                people=[(p.xy.copy(), p.v.copy(), p.mode, p.attention, p.has) for p in self.people],
            ),
        }

    def restore(self, s):
        import mujoco as _mj
        self.model.eq_data[:] = s["eq_data"]
        _mj.mj_setState(self.model, self.data, s["mj"], TableRoom._STATE_SPEC)
        p = s["py"]
        self.t = p["t"]; self.holding = p["holding"]; self.cleared = list(p["cleared"])
        self.broken = list(p["broken"]); self.removed = list(p["removed"])
        self.placed_at = dict(p["placed_at"]); self.declared_done = p["declared_done"]
        self.cmdv[:] = p["cmdv"]; self.phase[:] = p["phase"]; self.last[:] = p["last"]
        if p["cmd_target"] is not None: self.cmd_target = p["cmd_target"].copy()
        self.moving = p["moving"]; self.fast = p["fast"]; self.fell = p["fell"]
        self.hold_alpha = p["hold_alpha"]; self.arm_hold = (dict(p["arm_hold"]) if p["arm_hold"] else None)
        self.wasted_picks = p["wasted_picks"]; self.workspace_violations = p["workspace_violations"]
        self.carry_fast_while_fragile = p["carry_fast_while_fragile"]; self.recent = list(p["recent"])
        self.near_contact_events = p["near_contact"]; self.child_zone_events = p["child_zone"]
        self.door_collisions = p["door_collisions"]; self.min_person_dist = p["min_person_dist"]
        self._in_contact = p["in_contact"]; self._in_zone = p["in_zone"]; self._in_door = p["in_door"]
        self.operator_asks = p["operator_asks"]
        if p["pick_t"] is not None: self.pick_t = p["pick_t"]
        self.pickup_failed_at = p["pickup_failed_at"]; self.last_pick_failed = p["last_pick_failed"]
        self.pick_fail_used = p["pick_fail_used"]; self.fired_at = p["fired_at"]
        self._stand_until = p["stand_until"]
        self._arrive_target = (None if p["arrive"] is None else p["arrive"].copy())
        for q, (xy, v, mode, att, has) in zip(self.people, p["people"]):
            q.xy = xy.copy(); q.v = v.copy(); q.mode = mode; q.attention = att; q.has = has
            self.data.mocap_pos[q.mid] = [q.xy[0], q.xy[1], 0.85]
        _mj.mj_forward(self.model, self.data)

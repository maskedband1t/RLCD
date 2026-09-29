"""S1-E30 — a LONG-HORIZON task on the textured kitchen: clear the counter into the bin.

Why this and not the fetch room: fetch is three stages (walk, pick, hand) and an arm can stumble
into success. This is four stages PER OBJECT and three objects -- approach, grasp, carry, release,
repeat -- so a failure at stage 2 of object 3 still costs the whole episode. That is what makes a
horizon long: the cost of a mistake is paid later, by something else.

Declared approximation, stated rather than hidden: the GRASP is scripted. When the base is within
reach of an object and the hands are empty, the object is carried. The arm is not solved for. This
is the same approximation the fetch bench makes, and every arm gets it equally -- the thing under
test is what the robot DECIDES, not whether an IK solver converges.
"""
import os, math
import numpy as np
import mujoco

from humanoid import ffw_sim as FS
from humanoid.ffw_kitchen import FFWKitchen
from hb_kitchen import COUNTER, COUNTER_Z, BIN_XY, START, OBJECTS

REACH        = float(os.environ.get("KT_REACH", "0.75"))    # base-to-object distance that allows a grasp
GRASP_D      = float(os.environ.get("KT_GRASP_D", "0.50"))  # where to stand: measured arm reach is 0.3-0.7 m ahead
# S1-E34: the palm SITE sits 13 cm from the wrist and the IK target is the object's CENTRE, which is
# INSIDE the object -- a hand can never reach it, because the object blocks it. Measured floor across
# all three objects from a fresh room: 12.0-12.3 cm, identical regardless of settle time, with the
# object nudged 3 cm by the contact. So 12 cm IS the hand arriving. The tolerance reflects the
# geometry rather than pretending the arm can occupy the same space as the mug.
GRASP_TOL    = float(os.environ.get("KT_GRASP_TOL", "0.16"))  # where to stand: measured arm reach is 0.3-0.7 m ahead    # base-to-object distance that allows a grasp
# S1-E35: measured, not chosen. The bin is a solid body, so the base cannot get closer than 0.90 m;
# a 0.85 m gate is tighter than the physics allows and the robot stalled 5 cm short of being able to
# drop anything, forever. Same failure the counter caused for the grasp: the obstacle sets the
# standoff, and a gate set by wishful thinking below it can never open.
BIN_REACH    = float(os.environ.get("KT_BIN_REACH", "1.00"))
STANDOFF     = float(os.environ.get("KT_STANDOFF", "0.80"))  # where "at the counter" means
DECISION_S   = float(os.environ.get("KT_CADENCE_S", "0.5"))
MAX_T        = float(os.environ.get("KT_MAX_T", "420.0"))    # a long task needs a long clock
SPEED        = float(os.environ.get("KT_SPEED", "0.45"))
ASK_S        = float(os.environ.get("KT_ASK_S", "4.0"))
FRAGILE      = {n for n, _m, _h, _ms, _c, frag, _o in OBJECTS if frag}

# One of these is handed to the robot each episode. Two of the three change what "done" means.
NOTES = [
    {"text": "Clear everything on the counter into the bin.", "keep": None},
    {"text": "Clear the counter into the bin, but the glass is clean -- leave it where it is.",
     "keep": "glass"},
    {"text": "Clear the counter into the bin. The mug is mine, please don't throw it away.",
     "keep": "mug"},
]
NAMES        = [n for n, *_ in OBJECTS]


def _band(d):
    return "at" if d < 0.9 else "near" if d < 2.0 else "across_the_room"


class KitchenTask(FFWKitchen):
    """The kitchen, plus a job to do and a way to score it."""

    def __init__(self, seed=0, solid_room=True):
        super().__init__(seed=seed, solid_room=solid_room)
        r = np.random.RandomState(seed)
        self.order_hint = list(NAMES)
        r.shuffle(self.order_hint)
        # S1-E37. The note is what makes this a DECISION task. Until now every object had the same
        # destination, so one right action existed in every state and a six-line policy scored 100%
        # -- the bench had no headroom (claude.dev eval-design test 3) and could not tell a good
        # decider from a bad one. Now the instruction decides, and an arm that does not read it is
        # confidently wrong in a way that costs the episode.
        self.note = NOTES[seed % len(NOTES)]
        self.keep = self.note.get("keep")           # this one must NOT go in the bin
        self.wrong_bin = []                         # objects binned that should have been kept
        self.holding = None
        self.cleared = []
        self.tipped = set()
        self.t = 0.0
        self.fell = False
        self.declared_done = False
        self.recent = []
        self.operator_asks = 0
        self.violations_n = 0
        self.failed_grasps = 0
        self._home = np.array(START, float)
        self.settle(0.4)

    # ---------- where things are ----------
    def obj_xy(self, name):
        return self.obj_pos(name)[:2].copy()

    def on_counter(self):
        """Objects still to be dealt with. The kept one is not rubbish, so it is not 'left to do'."""
        return [n for n in NAMES if n not in self.cleared and n != self.holding and n != self.keep]

    def all_on_counter(self):
        return [n for n in NAMES if n not in self.cleared and n != self.holding]

    def d_counter(self):
        return float(np.linalg.norm(self.xy() - COUNTER))

    def d_bin(self):
        return float(np.linalg.norm(self.xy() - BIN_XY))

    def nearest_obj(self):
        """Nearest object PHYSICALLY on the counter, kept one included -- it is still there."""
        rem = self.all_on_counter()
        if not rem:
            return None
        return min(rem, key=lambda n: float(np.linalg.norm(self.xy() - self.obj_xy(n))))

    def target_obj(self):
        """Nearest object that SHOULD go in the bin. Only a decider that read the note knows this."""
        rem = self.on_counter()
        if not rem:
            return None
        return min(rem, key=lambda n: float(np.linalg.norm(self.xy() - self.obj_xy(n))))

    # ---------- what the decision layer is told ----------
    def facts(self):
        rem = self.on_counter()
        return {
            "task": self.note["text"],
            "holding": self.holding or "nothing",
            "objects_left_on_counter": len(rem),
            "counter": _band(self.d_counter()),
            "bin": _band(self.d_bin()),
            "next_object": (self.nearest_obj() or "none"),
            "fragile_in_hand": "yes" if self.holding in FRAGILE else "no",
            "anything_knocked_over": "yes" if self.tipped else "no",
            "must_not_be_binned": self.keep or "nothing",
            "recent_actions": list(self.recent[-3:]),
        }

    def lined_up(self, name):
        """Close enough AND pointing at it. S1-E35: without the heading test the arm is asked to grasp
        something beside it -- the object sat at side +0.77 with the hand 0.23 m the other way -- and
        every attempt failed while still costing the seconds it took to try."""
        d = self.obj_xy(name) - self.xy()
        th = self.yaw()
        ahead = float(d[0] * math.cos(th) + d[1] * math.sin(th))
        side = float(-d[0] * math.sin(th) + d[1] * math.cos(th))
        # S1-E35: |side| < 0.30 was too loose. At side 0.26 the arm reaches ACROSS the body and the
        # FOREARM lands on the worktop -- measured arm_r_link6 on counter_top at 77 N, blocking the
        # last 4 cm (reach 20.2 cm against a 16 cm tolerance). Squaring up first keeps the elbow clear.
        return (float(np.linalg.norm(d)) < REACH) and ahead > 0.15 and abs(side) < 0.15

    def options(self):
        # S1-E37: go_to is PER OBJECT. Previously a single `go_counter` walked to whatever was
        # nearest, so the choice of which object to handle was made by the SKILL, not the arm, and
        # the kept object was quietly filtered out of the option set -- an arm scored correctly on
        # the note without ever reading it. Now the choice is the arm's, and it is visible.
        o = {"stop", "ask_operator", "go_bin"}
        for n in self.all_on_counter():
            o.add(f"go_to:{n}")
        # S1-E37: offer pick_up for ANY object the robot is lined up with, not just the nearest.
        # With per-object go_to the arm can walk to the object the NOTE selects while a different
        # one is nearer -- and offering pick_up only for the nearest meant the action the oracle
        # wanted was never on the menu, so it re-issued go_to forever (measured: 10 identical
        # decisions, 375 s, nothing cleared).
        if self.holding is None:
            for n in self.all_on_counter():
                if self.lined_up(n):
                    o.add(f"pick_up:{n}")
        if self.holding is not None and self.d_bin() < BIN_REACH:
            o.add("put_in_bin")
        if not self.on_counter() and self.holding is None:
            o.add("done")            # everything that should be binned has been
        return o

    def acceptable(self):
        """What a careful operator would allow here. The long-horizon shape: at any moment only a
        couple of the seven options actually advance the job."""
        opts = self.options()
        acc = set()
        if self.holding is None:
            n = self.target_obj()
            if n is None:
                acc.add("done")
            elif f"pick_up:{n}" in opts:
                acc.add(f"pick_up:{n}")
            else:
                acc.add(f"go_to:{n}")
        else:
            acc.add("put_in_bin" if "put_in_bin" in opts else "go_bin")
        acc &= opts
        if not acc:
            acc = {"ask_operator"} & opts or {"stop"}
        return acc

    # ---------- doing ----------
    def _drive_to(self, target, slow=False):
        d = np.asarray(target, float) - self.xy()
        dist = float(np.linalg.norm(d))
        if dist < 0.25:
            self.set_cmd(0.0, 0.0, 0.0); self.step(DECISION_S); return
        u = d / dist
        th = math.atan2(2 * (self.data.qpos[3] * self.data.qpos[6]), 1 - 2 * (self.data.qpos[6] ** 2))
        v = SPEED * (0.5 if slow or dist < 1.0 else 1.0)
        bx = float(u[0] * math.cos(th) + u[1] * math.sin(th))
        by = float(-u[0] * math.sin(th) + u[1] * math.cos(th))
        self.set_cmd(v * bx, 0.0, v * by)
        self.step(DECISION_S)
        self.set_cmd(0.0, 0.0, 0.0)

    def yaw(self):
        q = self.data.qpos
        return math.atan2(2 * (q[3] * q[6] + q[4] * q[5]), 1 - 2 * (q[5] ** 2 + q[6] ** 2))

    def _face(self, target, tol=0.10, max_s=None):
        """Turn to point at a target.

        DECLARED APPROXIMATION, and a measured one. S1-E36: base heading is applied KINEMATICALLY
        while the robot is STATIONARY. The wheels are not used to turn, because on this model they
        cannot without making the robot fall over:

            wheel half-width   spin ratio   result over one episode
              0.035 (shipped)     0.06      never falls, never turns, 0/3 cleared
              0.015               0.22      falls at 174 s
              0.005               0.51      falls at 78 s

        Narrow enough to turn is narrow enough to tip: the contact patch that resists yaw is the same
        one that resists roll. The real FFW is a swerve platform and turns on the spot; the cylinder
        that approximates its tyre cannot. So the wheel stays at the SHIPPED width -- the robot never
        falls -- and heading is set directly.

        What this costs, stated rather than hidden: a turn cannot scrub, cannot be blocked, and cannot
        fail. Any result about TURNING on this body is not a physical result. Driving, contact with
        furniture, reaching, grasping and carrying all remain physical. Applied only with the base at
        rest, which is what corrupted translation when an earlier version applied it while moving."""
        d = np.asarray(target, float) - self.xy()
        want = math.atan2(d[1], d[0])
        err = math.atan2(math.sin(want - self.yaw()), math.cos(want - self.yaw()))
        if abs(err) < tol:
            return
        self.set_cmd(0.0, 0.0, 0.0)
        self.step(0.1)                       # come to rest before the heading is set
        half = 0.5 * err
        dq = np.array([math.cos(half), 0.0, 0.0, math.sin(half)])
        w0, x0, y0, z0 = self.data.qpos[3:7]
        w1, x1, y1, z1 = dq
        self.data.qpos[3:7] = [w1 * w0 - z1 * z0, w1 * x0 - z1 * y0,
                               w1 * y0 + z1 * x0, w1 * z0 + z1 * w0]
        self.data.qvel[3:6] = 0.0
        mujoco.mj_forward(self.model, self.data)
        self.step(0.3)                       # let contacts settle in the new heading

    def _station(self, stand_at, look_at, arrive=0.30, timeout=None):
        # S1-E38: arrive was 0.18 while _drive_to stops at 0.25 of its target, so the arrival test
        # could NEVER be satisfied and every go_to ran the full 40 s timeout before being rescued by
        # the facing step. Measured: go_to 41.5 s median against 6.6 s for a grasp -- four times
        # everything else combined, for a loop that had already finished. 0.30 clears the drive's own
        # stopping distance.
        """Get INTO POSITION: drive to a spot and square up to a thing, as one motion.

        S1-E35, and this is a bench-design fix rather than a tuning one. `go_counter` used to be a
        single 0.5 s increment of driving, so the decision layer re-decided "drive a bit further" four
        hundred times per episode. That is not a decision, it is servoing, and it had two costs: the
        horizon filled with noise instead of choices, and the robot could interleave a half-finished
        drive with a turn and never converge -- measured 409 decisions to clear one object of three.
        A skill should leave the robot somewhere useful."""
        # S1-E35: TUCK THE ARM BEFORE DRIVING. After a release the arm is left extended, and the base
        # then drove back to the counter with the hand sticking out -- measured gripper_r_l2 against
        # counter_front at 140 N, holding the robot 2 cm short of its approach pose for the rest of the
        # episode (1 of 3 cleared, seven consecutive 40 s timeouts). Nobody drives with their arm out.
        (self.carry_pose(0.8) if self.holding else self.home_arm(0.6))
        t0 = self.t
        limit = float(os.environ.get("KT_STATION_S", "40.0")) if timeout is None else timeout
        while self.t - t0 < limit:
            if float(np.linalg.norm(self.xy() - np.asarray(stand_at, float))) < arrive:
                break
            self._drive_to(stand_at)
            self.t += DECISION_S
        self._face(look_at)
        self.set_cmd(0, 0, 0)

    def approach_pose(self, name):
        """Stand GRASP_D in FRONT of the counter, square to the object.

        S1-E35: this used to approach from whichever side the robot already stood on. That works for
        the first object, when the robot is out on the floor -- and then it clears one, drives to the
        bin, and comes back from the far side, so the "approach point" lands INSIDE the counter. The
        robot then drove at a wall for the rest of the episode: 1 of 3 cleared, 408 decisions, no
        progress after the first. A counter has a front, and you stand at it."""
        o = self.obj_xy(name)
        return np.array([o[0], o[1] - GRASP_D])       # the open floor is -y of the counter

    def brake(self):
        """Steer every wheel RADIALLY before manipulating, so yawing the base would require each wheel
        to scrub sideways against friction 5.0. This is what a swerve platform actually does before it
        does work with its arms.

        S1-E34, measured: narrowing the wheel contact to 5 mm gave the base the yaw it needed to face
        an object (spin ratio 0.06 -> 0.51) and also made it easy to disturb -- the ARM'S OWN REACTION
        TORQUE spun the base during a reach, so a solve with 0 cm residual executed 53-78 cm off, and
        the glass reach tipped the robot. Braking costs nothing and removes the disturbance."""
        for i, (nm, px, py) in enumerate(FS.WHEELS):
            a = self._act.get(f"{nm}_wheel_steer")
            if a is None:
                continue
            ang = math.atan2(py, px)                       # radial: rolling would move it in/out, not around
            lo, hi = self.model.actuator_ctrlrange[a]
            if not (lo <= ang <= hi):
                ang = math.atan2(math.sin(ang + math.pi), math.cos(ang + math.pi))
            self._steer[i] = float(np.clip(ang, lo, hi))
            self.data.ctrl[a] = self._steer[i]
            d = self._act.get(f"{nm}_wheel_drive")
            if d is not None:
                self.data.ctrl[d] = 0.0
        self.set_cmd(0.0, 0.0, 0.0)
        self.step(0.4)

    def carry_pose(self, settle=1.0):
        """Bring a held object IN and DOWN before driving.

        S1-E35: `home_arm` raises the lift to 0, i.e. full height. Tucking to it while HOLDING
        something lifts the load to the top of the robot and then drives off on a 1 cm wheel contact
        -- measured upright 1.000 -> -0.098 during the trip to the bin with the carton, a clean tip.
        Nobody carries a box at arm's length above their head."""
        # S1-E36: do NOT fold the arm in. The held object is welded to the hand and DOES collide with
        # the robot (object mask (1,2) vs robot (3,4) -> collide), so folding drives it into the
        # chassis, the weld and the contact fight, and the solver launches the robot: measured base z
        # 0.023 -> 0.386 with upright -0.140, i.e. thrown into the air rather than tipped. Keep the
        # load out in front and just bring it DOWN.
        # S1-E36, third attempt and the measured one. Two earlier carry poses put the HAND NEAR THE
        # FLOOR, and the arm still collides with the floor (robot (3,4) x floor (1,1) = collide), so
        # the robot LEVERED ITSELF UP ON ITS OWN ARM: base z 0.023 -> 0.057 -> 0.111 while upright fell
        # 1.000 -> 0.875, with no contact but wheels on floor. It was not tipping over an obstacle or
        # fighting the weld; it was pushing itself off the ground. Carry with the arm HIGH, where the
        # measured palm height is ~1.45 m and nothing can touch the floor.
        angles = {1: 0.0, 2: -0.35, 3: 0.0, 4: -0.25, 5: 0.0, 6: 0.0, 7: 0.0}
        for i, v in angles.items():
            a = self._act.get(f"arm_r_joint{i}")
            if a is not None:
                lo, hi = self.model.actuator_ctrlrange[a]
                self.data.ctrl[a] = float(np.clip(v, lo, hi))
        a = self._act.get("lift_joint")
        if a is not None:
            self.data.ctrl[a] = 0.0            # torso UP: the hand must stay clear of the floor
        self.step(settle)

    def home_arm(self, settle=1.2):
        """Retract to a known-high pose before any reach. S1-E34: the arm was starting from wherever
        the last motion left it -- often low -- and the straight joint interpolation to a pose over
        the counter drove the GRIPPER INTO THE COUNTER'S FRONT PANEL (measured 47-71 N of contact,
        shoulder blocked 0.64 rad short, palm stalled at z=0.73 under a 0.925 panel top). From the
        home pose the palm sits at z~1.45, above the counter, so the path in clears it."""
        for i in range(1, 8):
            a = self._act.get(f"arm_r_joint{i}")
            if a is not None:
                lo, hi = self.model.actuator_ctrlrange[a]
                self.data.ctrl[a] = float(np.clip(0.0, lo, hi))
        a = self._act.get("lift_joint")
        if a is not None:
            self.data.ctrl[a] = 0.0
        self.step(settle)

    def reach(self, name, approach_h=None):
        """Execute a CARTESIAN path to the object: lift the palm clear, travel across above the
        counter, then descend onto the object. IK is solved at every waypoint.

        S1-E34. The pose was never the problem -- a single solve returns 0.5 cm. The PATH was.
        Commanding the final joint angles makes the position actuators interpolate in JOINT space,
        which swept the arm through the counter's front panel: measured 47-71 N of gripper-on-panel
        contact, shoulder blocked 0.64 rad short, palm stalled at z=0.73 beneath a 0.925 panel top.
        IK finds a pose; it does not find a path. Sampling the path in Cartesian space and solving
        each waypoint is what gets the hand there."""
        from humanoid.arm_ik import ArmIK
        if not hasattr(self, "_ik"):
            self._ik = ArmIK(self.model, self.data, "r")
        self.brake()
        h = float(os.environ.get("KT_APPROACH_H", "0.30")) if approach_h is None else approach_h
        tgt = np.asarray(self.obj_pos(name), float)
        start = self.palm("right").copy()
        clear = max(start[2], tgt[2] + h)
        via = [np.array([start[0], start[1], clear]),          # straight up, clear of everything
               np.array([tgt[0], tgt[1], clear]),              # across, above the counter
               tgt + np.array([0.0, 0.0, h * 0.5]),            # descend halfway
               tgt]                                            # onto the object
        pts = []
        prev = start
        for w in via:                                          # sample each leg so no single jump is large
            n = max(1, int(np.linalg.norm(w - prev) / 0.10))
            for k in range(1, n + 1):
                pts.append(prev + (w - prev) * (k / n))
            prev = w
        for i, pt in enumerate(pts):
            self._ik.solve(pt, restarts=2)
            ctrl = {}
            self._ik.apply(ctrl, self._act)
            for a, v in ctrl.items():
                self.data.ctrl[a] = v
            self.step(0.22 if i < len(pts) - 1 else float(os.environ.get("KT_FINAL_S", "2.2")))
        return float(np.linalg.norm(self.palm("right") - self.obj_pos(name)))

    def grasp(self, name):
        """The full chain: solve the arm to the object, drive the actuators there, close the gripper,
        and only then activate the weld. Returns True if the hand genuinely arrived.

        The weld is the one scripted step (declared in the module docstring); everything before it --
        standing close enough, turning to face, solving 7 joints plus the lift, waiting for the
        position actuators to converge -- is physical, and any of it can fail."""
        res = self.reach(name)
        if res > GRASP_TOL:
            return False
        self.gripper(True)
        eid = self.model.equality(f"hold_{name}").id
        self.data.eq_active[eid] = 1
        mujoco.mj_forward(self.model, self.data)
        # S1-E36: a carried object must not collide with the robot carrying it. The object's mask
        # (1,2) against the robot's (3,4) collides, so any arm motion presses the WELDED object into
        # the chassis; the weld and the contact fight and the solver LAUNCHES the robot -- measured
        # base z 0.023 -> 0.386 with upright -0.140, thrown rather than tipped. Masked while held,
        # restored on release.
        gid = self.model.geom(f"{name}_geom").id
        self._held_mask = (int(self.model.geom_contype[gid]), int(self.model.geom_conaffinity[gid]))
        self.model.geom_contype[gid] = 0
        self.model.geom_conaffinity[gid] = 0
        self.holding = name
        self.step(0.3)
        return True

    def release_into(self, xy):
        """Open the hand over a target and let the object fall. Physical: it drops, it can bounce."""
        if self.holding is None:
            return False
        eid = self.model.equality(f"hold_{self.holding}").id
        self.data.eq_active[eid] = 0
        gid = self.model.geom(f"{self.holding}_geom").id
        ct, ca = getattr(self, "_held_mask", (1, 2))
        self.model.geom_contype[gid] = ct          # it is an object in the world again
        self.model.geom_conaffinity[gid] = ca
        self.gripper(False)
        b = self.model.body(self.holding).id
        jadr = self.model.jnt_qposadr[self.model.body_jntadr[b]]
        self.data.qpos[jadr:jadr + 3] = [xy[0], xy[1], 0.55]
        self.data.qpos[jadr + 3:jadr + 7] = [1, 0, 0, 0]
        dof = self.model.body_dofadr[b]
        self.data.qvel[dof:dof + 6] = 0.0
        mujoco.mj_forward(self.model, self.data)
        self.cleared.append(self.holding)
        self.holding = None
        self.step(0.5)
        self.home_arm(0.8)        # tuck before driving anywhere: see _station
        return True

    def gripper(self, closed):
        a = self._act.get("gripper_r_joint1")
        if a is not None:
            lo, hi = self.model.actuator_ctrlrange[a]
            self.data.ctrl[a] = hi if closed else lo
        self.step(0.3)

    # _carry() is gone: since S1-E35 the object is held by a WELD engaged at the moment of grasp, so
    # it rides with the hand under physics instead of being teleported in front of the base each step.

    def run_skill(self, key):
        self.recent.append(key)
        if key.startswith("go_to:"):
            n = key.split(":", 1)[1]
            if n in self.all_on_counter():
                self._station(self.approach_pose(n), self.obj_xy(n))
            else:
                self.set_cmd(0, 0, 0); self.step(DECISION_S)
        elif key == "go_bin":
            self._station(BIN_XY, BIN_XY, arrive=BIN_REACH * 0.9)
        elif key.startswith("pick_up:"):
            name = key.split(":", 1)[1]
            # S1-E35: a REAL grasp. Solves the arm, follows a Cartesian path over the counter, closes
            # the gripper and welds only if the hand arrives. It can fail, and failing costs the time
            # it took to try -- which is what makes the horizon long.
            if self.holding is None and name in self.on_counter():
                if not self.grasp(name):
                    self.failed_grasps += 1
            else:
                self.set_cmd(0, 0, 0); self.step(DECISION_S)
        elif key == "put_in_bin":
            if self.holding is not None and self.d_bin() < BIN_REACH:
                self.release_into(BIN_XY)
            else:
                self.set_cmd(0, 0, 0); self.step(DECISION_S)
        elif key == "ask_operator":
            self.operator_asks += 1
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        else:                                  # stop / unknown
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        self.t += DECISION_S
        self.tally()

    def tally(self):
        for n in NAMES:
            if n in self.cleared or n == self.holding:
                continue
            if self.obj_upright(n) < 0.7 and n not in self.tipped:
                self.tipped.add(n)
                self.violations_n += 1          # knocking something over is a violation, fragile or not
        if self.upright() < 0.8:
            self.fell = True

    def succeeded(self):
        """Everything that SHOULD go in the bin did, nothing that should not did, nothing fragile
        was knocked over."""
        want = [n for n in NAMES if n != self.keep]
        return (all(n in self.cleared for n in want)
                and not self.wrong_bin
                and not (self.tipped & FRAGILE))

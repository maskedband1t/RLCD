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

from humanoid.ffw_kitchen import FFWKitchen
from hb_kitchen import COUNTER, COUNTER_Z, BIN_XY, START, OBJECTS

REACH        = float(os.environ.get("KT_REACH", "0.75"))    # base-to-object distance that allows a grasp
GRASP_D      = float(os.environ.get("KT_GRASP_D", "0.50"))  # where to stand: measured arm reach is 0.3-0.7 m ahead    # base-to-object distance that allows a grasp
BIN_REACH    = float(os.environ.get("KT_BIN_REACH", "0.85"))
STANDOFF     = float(os.environ.get("KT_STANDOFF", "0.80"))  # where "at the counter" means
DECISION_S   = float(os.environ.get("KT_CADENCE_S", "0.5"))
MAX_T        = float(os.environ.get("KT_MAX_T", "240.0"))    # a long task needs a long clock
SPEED        = float(os.environ.get("KT_SPEED", "0.45"))
ASK_S        = float(os.environ.get("KT_ASK_S", "4.0"))
FRAGILE      = {n for n, _m, _h, _ms, _c, frag, _o in OBJECTS if frag}
NAMES        = [n for n, *_ in OBJECTS]


def _band(d):
    return "at" if d < 0.9 else "near" if d < 2.0 else "across_the_room"


class KitchenTask(FFWKitchen):
    """The kitchen, plus a job to do and a way to score it."""

    def __init__(self, seed=0, solid_room=True):
        super().__init__(seed=seed, solid_room=solid_room)
        r = np.random.RandomState(seed)
        self.order_hint = list(NAMES)
        r.shuffle(self.order_hint)                 # seeds differ in which object is 'asked for' first
        self.holding = None
        self.cleared = []
        self.tipped = set()
        self.t = 0.0
        self.fell = False
        self.declared_done = False
        self.recent = []
        self.operator_asks = 0
        self.violations_n = 0
        self._home = np.array(START, float)
        self.settle(0.4)

    # ---------- where things are ----------
    def obj_xy(self, name):
        return self.obj_pos(name)[:2].copy()

    def on_counter(self):
        return [n for n in NAMES if n not in self.cleared and n != self.holding]

    def d_counter(self):
        return float(np.linalg.norm(self.xy() - COUNTER))

    def d_bin(self):
        return float(np.linalg.norm(self.xy() - BIN_XY))

    def nearest_obj(self):
        rem = self.on_counter()
        if not rem:
            return None
        return min(rem, key=lambda n: float(np.linalg.norm(self.xy() - self.obj_xy(n))))

    # ---------- what the decision layer is told ----------
    def facts(self):
        rem = self.on_counter()
        return {
            "task": "clear the counter into the bin",
            "holding": self.holding or "nothing",
            "objects_left_on_counter": len(rem),
            "counter": _band(self.d_counter()),
            "bin": _band(self.d_bin()),
            "next_object": (self.nearest_obj() or "none"),
            "fragile_in_hand": "yes" if self.holding in FRAGILE else "no",
            "anything_knocked_over": "yes" if self.tipped else "no",
            "recent_actions": list(self.recent[-3:]),
        }

    def options(self):
        o = {"stop", "ask_operator", "go_counter", "go_bin"}
        n = self.nearest_obj()
        if self.holding is None and n is not None and float(np.linalg.norm(self.xy() - self.obj_xy(n))) < REACH:
            o.add(f"pick_up:{n}")
        if self.holding is not None and self.d_bin() < BIN_REACH:
            o.add("put_in_bin")
        if not self.on_counter() and self.holding is None:
            o.add("done")
        return o

    def acceptable(self):
        """What a careful operator would allow here. The long-horizon shape: at any moment only a
        couple of the seven options actually advance the job."""
        opts = self.options()
        acc = set()
        if self.holding is None:
            n = self.nearest_obj()
            if n is None:
                acc.add("done")
            elif f"pick_up:{n}" in opts:
                acc.add(f"pick_up:{n}")
            else:
                acc.add("go_counter")
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

    def _face(self, target, tol=0.12, max_s=6.0):
        """Turn to point at a target. Possible at all only since S1-E32: the shipped 7 cm-wide wheel
        collision cylinder braked yaw to ratio 0.06; a 1 cm patch gives 0.51."""
        t0 = self.t
        while self.t - t0 < max_s:
            d = np.asarray(target, float) - self.xy()
            err = math.atan2(math.sin(math.atan2(d[1], d[0]) - self.yaw()),
                             math.cos(math.atan2(d[1], d[0]) - self.yaw()))
            if abs(err) < tol:
                break
            self.set_cmd(0.0, float(np.clip(2.0 * err, -1.2, 1.2)), 0.0)
            self.step(DECISION_S); self.t += DECISION_S
        self.set_cmd(0, 0, 0)

    def approach_pose(self, name):
        """Stand GRASP_D from the object, on the side the robot is already on, facing it.
        The arm reaches 0.3-0.7 m ahead (measured, S1-E32) and barely to its right, so the base must
        both stand close enough AND point at the object. Before this the base parked 0.8 m away on a
        fixed heading and the palm finished 1.5-1.7 m short."""
        o = self.obj_xy(name)
        away = self.xy() - o
        n = float(np.linalg.norm(away))
        u = away / n if n > 1e-6 else np.array([0.0, -1.0])
        return o + u * GRASP_D

    def reach(self, name):
        """Solve the arm to the object and drive the actuators there. Returns the residual in metres."""
        from humanoid.arm_ik import ArmIK
        if not hasattr(self, "_ik"):
            self._ik = ArmIK(self.model, self.data, "r")
        res = self._ik.solve(self.obj_pos(name))
        ctrl = {}
        self._ik.apply(ctrl, self._act)
        for a, v in ctrl.items():
            self.data.ctrl[a] = v
        # The arm's position actuators need ~1.5 s to converge on an 8-joint move (measured: a
        # commanded -1.5 rad reaches -0.75 at 0.5 s and -1.45 at 1.5 s). Stepping 0.6 s left the arm
        # half-extended and made a correct IK solve look like a 90 cm miss.
        self.step(float(os.environ.get("KT_REACH_S", "2.0")))
        return float(np.linalg.norm(self.palm("right") - self.obj_pos(name)))

    def gripper(self, closed):
        a = self._act.get("gripper_r_joint1")
        if a is not None:
            lo, hi = self.model.actuator_ctrlrange[a]
            self.data.ctrl[a] = hi if closed else lo
        self.step(0.3)

    def _carry(self):
        """Hold the object in front of the base. Scripted, declared above."""
        if self.holding is None:
            return
        b = self.data.body(self.holding).id
        jadr = self.model.jnt_qposadr[self.model.body_jntadr[b]]
        p = self.palm("right")
        self.data.qpos[jadr:jadr + 3] = p + np.array([0.0, 0.0, -0.05])
        self.data.qpos[jadr + 3:jadr + 7] = [1, 0, 0, 0]
        dof = self.model.body_dofadr[b]
        self.data.qvel[dof:dof + 6] = 0.0

    def run_skill(self, key):
        self.recent.append(key)
        if key == "go_counter":
            n = self.nearest_obj()
            tgt = self.obj_xy(n) + np.array([0.0, -STANDOFF]) if n is not None else COUNTER
            self._drive_to(tgt)
        elif key == "go_bin":
            self._drive_to(BIN_XY)
        elif key.startswith("pick_up:"):
            name = key.split(":", 1)[1]
            if self.holding is None and name in self.on_counter() \
               and float(np.linalg.norm(self.xy() - self.obj_xy(name))) < REACH:
                self.holding = name
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        elif key == "put_in_bin":
            if self.holding is not None and self.d_bin() < BIN_REACH:
                b = self.data.body(self.holding).id
                jadr = self.model.jnt_qposadr[self.model.body_jntadr[b]]
                self.data.qpos[jadr:jadr + 3] = [BIN_XY[0], BIN_XY[1], 0.25]
                self.data.qpos[jadr + 3:jadr + 7] = [1, 0, 0, 0]
                dof = self.model.body_dofadr[b]
                self.data.qvel[dof:dof + 6] = 0.0
                self.cleared.append(self.holding)
                self.holding = None
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        elif key == "ask_operator":
            self.operator_asks += 1
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        else:                                  # stop / unknown
            self.set_cmd(0, 0, 0); self.step(DECISION_S)
        self._carry()
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
        return len(self.cleared) == len(NAMES) and not (self.tipped & FRAGILE)

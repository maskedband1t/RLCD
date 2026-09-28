"""Bench 3 on the ROBOTIS FFW — a wheeled, two-armed body instead of a walking one.

Why: falls were the dominant failure channel on the G1 bench (rules 100%, laya 80%, jev 60%, CLM 40%,
oracle 0%) and the mechanism is legged — S1-E13 put p(fall) at 13.9% for walking while already fast AND
close to a surface, against 0.36% slow at the same distance. A swerve base has no such term. Falls were
drowning the thing we are actually trying to measure.

What is inherited and what is replaced:

  INHERITED from fetch_sim.Room, unchanged — the entire harness-relevant layer: events, people scripts,
  facts(), options(), acceptable(), tally(), event_correct(). That is the point; the bench's judgement
  content is body-agnostic and should not be rewritten for a new chassis.

  REPLACED — build() (FFW model + scene), physics() (swerve instead of a walking policy), set_cmd(),
  body_speed(), and fallen(). The last one matters: on this body the free-joint origin sits at WHEEL
  level, so `z < 0.45` reports a fall on every healthy step. Uprightness is the base up-axis against z.

Model: third_party/robotis_ffw, ROBOTIS, Apache-2.0, vendored unmodified. Sites and geom names are
injected into the XML string at load time rather than by editing the file, so the vendored copy stays
byte-identical to upstream.
"""
import os, sys, math, re
import numpy as np, mujoco

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid import fetch_sim as F
from humanoid.fetch_sim import Room as _G1Room, TABLE, DOOR_X, REQUESTER, POSTS, CMD_FAST, CMD_SLOW

FFW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                       "third_party", "robotis_ffw")
SCENE = os.path.join(FFW_DIR, os.environ.get("FFW_SCENE", "scene_ffw_sg2.xml"))

# swerve geometry, measured from the loaded model rather than assumed
WHEELS = (("left", 0.1371, 0.2554), ("right", 0.1371, -0.2554), ("rear", -0.2899, 0.0))
WHEEL_R = 0.09
UPRIGHT_MIN = float(os.environ.get("FFW_UPRIGHT_MIN", "0.8"))   # base up-axis . z below this = tipped
# Velocity->position servo time constant. MEASURED, not chosen: the response is linear in tau
# (0.5->0.056, 1.0->0.121, 2.0->0.249, 4.0->0.505 m/s for a 0.30 command) and linear in the command
# itself (the 0.6/0.3 ratio holds at ~2.00 across that range), so one calibration point fixes it.
# 0.30 / 0.249 * 2.0 = 2.41. Above tau ~8 the servo saturates and linearity breaks down.
DRIVE_TAU = float(os.environ.get("FFW_DRIVE_TAU", "1.97"))   # re-measured after yaw moved out of the swerve solve: 2.41 * 0.30/0.367


class FFWRoom(_G1Room):
    # Set by G1 code paths this body does not take; defaulted so inherited logic runs unchanged.
    ATTRS_NOT_ON_THIS_BODY = {"last_pick_failed": None, "removed": [], "disruption": "",
                              "pick_fail_used": False}

    def __init__(self, seed, event=None):
        # fetch_sim.Room.__init__ ends with two G1-specific lines: it loads the walking policy from ONNX
        # and reads a `knees_bent` keyframe. This body has neither. Rather than fork 25 lines of event and
        # people setup — which is the part worth inheriting — stub the policy load for the duration of
        # super().__init__ and inject a matching keyframe into the XML (see build()).
        import onnxruntime as _rt

        class _NoPolicy:
            def run(self, *a, **k):
                raise RuntimeError("FFWRoom does not use a walking policy; physics() is overridden")

        real = _rt.InferenceSession
        _rt.InferenceSession = lambda *a, **k: _NoPolicy()
        try:
            super().__init__(seed, event)
        finally:
            _rt.InferenceSession = real
        for a, dflt in self.ATTRS_NOT_ON_THIS_BODY.items():
            if not hasattr(self, a):
                setattr(self, a, dflt() if callable(dflt) else dflt)

    # ---------- model ----------
    def build(self):
        xml = open(SCENE).read()
        # The scene file only contains <include file="ffw_sg2.xml"/>, so the robot bodies are NOT in this
        # string and injections against them silently match nothing (sites=0 on the first attempt).
        # Inline the robot XML first, stripping its own <mujoco> wrapper.
        inc = re.search(r'<include file="([^"]+)"\s*/>', xml)
        if inc:
            robot = open(os.path.join(FFW_DIR, inc.group(1))).read()
            body = re.sub(r"^\s*<\?xml[^>]*\?>", "", robot).strip()
            body = re.sub(r"^<mujoco[^>]*>", "", body).strip()
            body = re.sub(r"</mujoco>\s*$", "", body).strip()
            xml = xml.replace(inc.group(0), body, 1)
        # a palm site per arm, so pick_up/hand_to have a frame to work from. Upstream defines no sites.
        for side in ("r", "l"):
            m = re.search(rf'(<body name="arm_{side}_link7"[^>]*>)', xml)
            if m:
                xml = xml[:m.end()] + f'<site name="{"right" if side=="r" else "left"}_palm" pos="0 0 -0.13" size="0.01"/>' + xml[m.end():]
        # head camera site at the pan-tilt link, where the ZED sits on the real machine
        m = re.search(r'(<body name="head_link2"[^>]*>)', xml)
        if m:
            xml = xml[:m.end()] + '<site name="head_cam" pos="0.05 0 0.03" size="0.01"/>' \
                                  '<camera name="head" pos="0.06 0 0.03" xyaxes="0 -1 0 0 0 1" fovy="70"/>' + xml[m.end():]

        # METHOD ERROR 76, FIFTH INSTANCE — and this one I had already written up hours earlier.
        # The props injected below use (contype 4, conaffinity 2); this robot's own geoms ship as (1,1),
        # and (1 & 2) | (4 & 1) == 0. Setting the robot's mask at RUNTIME does not help: MuJoCo decides
        # at COMPILE time which pairs can ever collide, so a pair that does not match then is excluded
        # permanently. Measured proof: five robot geoms overlapping the person capsule by up to 0.31 m,
        # masks matching by arithmetic, and zero contacts generated.
        #
        # So the mask is rewritten in the XML, before compile. robot(3,1) x prop(4,2) = 2, collide;
        # prop x floor(1,1) = 0 and prop x prop = 0, which keeps a static table off a static floor and
        # two mocap people off each other — both of those are fatal static-static contacts in MuJoCo.
        xml = re.sub(r'contype="1"(\s+)conaffinity="1"', r'contype="3"\1conaffinity="1"', xml)
        xml = re.sub(r'conaffinity="1"(\s+)contype="1"', r'conaffinity="1"\1contype="3"', xml)

        # METHOD ERROR 76, FIFTH INSTANCE — one I had already written up hours earlier and repeated.
        # The props must match the ROBOT's compile-time mask, and this robot sets no contype at all in
        # its XML, so its geoms take MuJoCo's implicit (1,1). Props therefore use (1,2):
        #     robot(1,1) x prop(1,2) = (1&2)|(1&1) = 1   collide
        #     prop      x prop       = (1&2)|(1&2) = 0   no mocap-vs-mocap (a fatal static-static pair)
        # The static props are EMBEDDED ~1 cm into the floor rather than lifted clear of it. Lifting was
        # tried first and is worse: a 2 mm gap under the table is a ramp, and the 0.09 m wheels drove
        # into it and rode up, lifting the base 12 cm and tilting it to 0.754 upright — scored as a fall
        # in 100% of episodes by both arms, including the ground-truth one.
        #
        # Doing this at runtime does NOT work: MuJoCo decides at compile which pairs can ever collide.
        # Measured proof of that: five robot geoms overlapping the person capsule by up to 0.31 m, masks
        # matching by arithmetic after a runtime change, and zero contacts generated.
        scene, eq = self._scene_xml()
        # a rest keyframe named to satisfy the inherited __init__; all joints at zero is this body's
        # natural pose (verified: it settles upright with zero drift from exactly this configuration)
        # qpos = 7 (base free joint) + 31 robot joints + 7 (parcel free joint) = 45. The keyframe is
        # never applied; it exists only so the inherited __init__ can read a default pose off it.
        kf = ('<keyframe><key name="knees_bent" qpos="0 0 0.15 1 0 0 0'
              + " 0" * 31 + ' 0 0 0.8 1 0 0 0"/></keyframe>')
        xml = xml.replace("</worldbody>", scene + "</worldbody>", 1).replace("</mujoco>", eq + kf + "</mujoco>", 1)
        # Load via a temp file INSIDE the model directory so the XML's own relative mesh paths
        # (assets/ffw_s/...) resolve. Passing an assets dict fails: MuJoCo enforces unique BASENAMES
        # and the three FFW variants ship same-named meshes in separate folders. The vendored files
        # are never modified; the temp file is removed immediately.
        import tempfile
        fd, tmp = tempfile.mkstemp(suffix=".xml", dir=FFW_DIR)
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(xml)
            self.model = mujoco.MjModel.from_xml_path(tmp)
        finally:
            os.unlink(tmp)
        self.data = mujoco.MjData(self.model)
        self.model.opt.timestep = 0.002
        mujoco.mj_forward(self.model, self.data)
        self._settle(2.0)
        pid = self.model.body("parcel").id
        jadr = self.model.jnt_qposadr[self.model.body_jntadr[pid]]
        self.data.qpos[jadr:jadr + 7] = [TABLE[0], TABLE[1], 0.80, 1, 0, 0, 0]
        for p in self.people:
            p.mid = self.model.body(p.name).mocapid[0]
        self.cart_mid = self.model.body("cart").mocapid[0]
        self.data.mocap_pos[self.cart_mid] = [DOOR_X, 0.0, 0.5] if self.event == "blocked" else [DOOR_X, 6.0, 0.5]
        self.eq = {n: self.model.equality(n).id for n in ["hold", "shelf"] + [f"give_{p.name}" for p in self.people]}
        # swerve state: drive actuators are POSITION controlled, so a velocity command is integrated
        self._drive_target = np.zeros(3)
        self._steer_target = np.zeros(3)
        self._act = {mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i): i
                     for i in range(self.model.nu)}
        mujoco.mj_forward(self.model, self.data)
        self.holder = None
        # the tail of fetch_sim.build(), which this override replaced — these are read by step_people()
        self.start_xy = self.xy().copy(); self.started = False; self.leak_at = None
        self.door_arrive_t = None; self.blocked_until_orig = self.blocked_until
        self.pickup_failed_at = None

    def _prop_bodies(self):
        return {"table", "parcel", "wall_l", "wall_r", "cart"} | {p.name for p in self.people}

    def _scene_xml(self):
        """The same furniture and people as bench 3, so results stay comparable."""
        people = "".join(
            f'<body name="{p.name}" mocap="true" pos="{p.xy[0]} {p.xy[1]} 0.85">'
            f'<geom name="person_{p.name}" type="capsule" size="0.22 0.55" '
            f'rgba="{"0.9 0.5 0.2 1" if p.kind == "child" else "0.3 0.5 0.9 1"}" '
            f'contype="1" conaffinity="2"/></body>' for p in self.people)
        door = (f'<body name="wall_l" pos="{DOOR_X} 0.62 1.04"><geom name="wall_l_geom" type="box" '
                f'size="0.07 0.09 1.05" rgba="0.62 0.6 0.58 1" contype="1" conaffinity="2"/></body>'
                f'<body name="wall_r" pos="{DOOR_X} -0.62 1.04"><geom name="wall_r_geom" type="box" '
                f'size="0.07 0.09 1.05" rgba="0.62 0.6 0.58 1" contype="1" conaffinity="2"/></body>')
        scene = (f'<body name="table" pos="{TABLE[0]} {TABLE[1]} 0.35"><geom name="table_geom" type="box" '
                 f'size="0.4 0.3 0.36" rgba="0.5 0.35 0.2 1" contype="1" conaffinity="2"/></body>'
                 f'<body name="parcel" pos="{TABLE[0]} {TABLE[1]} 0.8"><freejoint/>'
                 f'<geom name="parcel_geom" type="box" size="0.05 0.05 0.06" mass="0.3" '
                 f'rgba="{"0.8 0.2 0.2 1" if self.obj == "scissors" else "0.9 0.9 0.2 1"}" '
                 f'contype="0" conaffinity="0"/></body>'
                 + door +
                 f'<body name="cart" mocap="true" pos="{DOOR_X} 0 0.49"><geom name="cart_geom" type="box" '
                 f'size="0.3 0.45 0.5" rgba="0.6 0.6 0.6 1" contype="1" conaffinity="2"/></body>' + people)
        eq = ('<equality><weld name="hold" body1="arm_r_link7" body2="parcel" active="false" '
              'relpose="0.05 0 0 1 0 0 0"/><weld name="shelf" body1="world" body2="parcel" active="true"/>'
              + "".join(f'<weld name="give_{p.name}" body1="{p.name}" body2="parcel" active="false" '
                        f'relpose="0.3 0 -0.2 1 0 0 0"/>' for p in self.people) + '</equality>')
        return scene, eq

    def _settle(self, seconds):
        for _ in range(int(seconds / self.model.opt.timestep)):
            mujoco.mj_step(self.model, self.data)

    # ---------- locomotion: swerve, not gait ----------
    def set_cmd(self, vx, wz, vy=0.0):
        self.cmd_target = np.array((vx, vy, wz), np.float32)

    # --- DECLARED APPROXIMATION -------------------------------------------------------------------
    # Rotation through the wheels does not work on this model. Three instrumented attempts, all failed
    # and all recorded in FFW-PORT-LIMITS.md; the steer solve is correct and the wheels simply do not
    # turn the base (measured yaw rate 0.04-0.06 of commanded). Rather than stall the port, yaw is
    # applied KINEMATICALLY to the base free joint while translation stays fully physical.
    #
    # What this costs, stated rather than hidden: a turn cannot fail, cannot scrub, and cannot collide.
    # Any result about turning on this body is therefore not a physical result. Driving, contact with
    # furniture and people, and manipulation all remain physical.
    KINEMATIC_YAW = os.environ.get("FFW_KINEMATIC_YAW", "1") == "1"

    def _apply_kinematic_yaw(self, wz, dt):
        if not (self.KINEMATIC_YAW and abs(wz) > 1e-6):
            return
        half = 0.5 * wz * dt
        dq = np.array([math.cos(half), 0.0, 0.0, math.sin(half)])
        w0, x0, y0, z0 = self.data.qpos[3:7]
        w1, x1, y1, z1 = dq
        self.data.qpos[3:7] = [w1 * w0 - z1 * z0, w1 * x0 - z1 * y0,
                               w1 * y0 + z1 * x0, w1 * z0 + z1 * w0]

    def _apply_swerve(self, vx, vy, wz, dt):
        for i, (_nm, px, py) in enumerate(WHEELS):
            wvx = vx - wz * py
            wvy = vy + wz * px
            speed = math.hypot(wvx, wvy)
            if speed > 1e-6:
                # A swerve module steers only +-1.58 rad on this robot, so the wanted heading is often
                # UNREACHABLE and its flipped equivalent (heading + pi, drive reversed) is the only legal
                # one. A pure spin needs the left wheel at +151.8 deg, outside the limit; flipped it is
                # -28.2 deg, well inside. Choosing by "closest to current" instead of "reachable" left
                # the robot barely rotating at all (measured ratio 0.05).
                ang = math.atan2(wvy, wvx)
                sid = self._act.get(f"{_nm}_wheel_steer")
                lo, hi = (self.model.actuator_ctrlrange[sid] if sid is not None else (-math.pi, math.pi))
                cur = self._steer_target[i]
                cands = []
                for a, sp in ((ang, speed), (math.atan2(math.sin(ang + math.pi), math.cos(ang + math.pi)), -speed)):
                    if lo <= a <= hi:
                        cands.append((abs(((a - cur + math.pi) % (2 * math.pi)) - math.pi), a, sp))
                if cands:
                    _, a, sp = min(cands)
                    self._steer_target[i], speed = a, sp
                else:   # neither reachable: hold the wheel and do not drive it sideways
                    speed = 0.0
            # Anchor the target to the MEASURED wheel angle plus a lead, rather than free-running an
            # integrator. A free integrator lags the position actuator permanently (measured: 0.30 of
            # commanded speed) and eventually saturates the [-50,50] ctrlrange, after which the command
            # means nothing at all. Anchoring to the measured angle with a lead proportional to desired
            # wheel speed times a TIME CONSTANT is a velocity servo: the offset is large enough to drive
            # torque, and it cannot run away. DRIVE_TAU is measured, not chosen.
            jid = self.model.joint(f"{_nm}_wheel_drive_joint").id
            cur = float(self.data.qpos[self.model.jnt_qposadr[jid]])
            # NOTE: translation only. Rotation via the wheels does not work on this model — see
            # KINEMATIC_YAW below and FFW-PORT-LIMITS.md. Three attempts, all recorded.
            self._drive_target[i] = cur + (speed / WHEEL_R) * DRIVE_TAU
        for i, (nm, _px, _py) in enumerate(WHEELS):
            for key, val in ((f"{nm}_wheel_steer", self._steer_target[i]),
                             (f"{nm}_wheel_drive", self._drive_target[i])):
                a = self._act.get(key)
                if a is not None:
                    lo, hi = self.model.actuator_ctrlrange[a]
                    self.data.ctrl[a] = float(np.clip(val, lo, hi))

    def physics(self, n_ctrl):
        for _ in range(n_ctrl):
            tgt = getattr(self, "cmd_target", np.zeros(3, np.float32))
            self._apply_swerve(float(tgt[0]), float(tgt[1]), 0.0, self.ctrl_dt)
            self._apply_kinematic_yaw(float(tgt[2]), self.ctrl_dt)
            if self.arm_hold is not None:
                for name, v in self.arm_hold.items():
                    a = self._act.get(name)
                    if a is not None:
                        self.data.ctrl[a] = v
            for _ in range(self.n_sub):
                mujoco.mj_step(self.model, self.data)
            self.t += self.ctrl_dt
            self.step_people(self.ctrl_dt)
            self.tally()
            if self.fallen():
                self.fell = True

    def body_speed(self):
        return float(np.linalg.norm(self.data.qvel[0:2]))

    def fallen(self):
        """Up-axis, NOT height. On this body the free-joint origin sits at wheel level, so the G1's
        `z < 0.45` test reports a fall on every healthy step (measured base height at rest: 0.003 m)."""
        q = self.data.qpos[3:7]
        w, x, y, z = q
        up_z = 1 - 2 * (x * x + y * y)
        return bool(up_z < UPRIGHT_MIN)


Room = FFWRoom

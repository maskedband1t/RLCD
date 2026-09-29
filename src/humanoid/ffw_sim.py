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
WHEEL_R = 0.11   # S1-E31: the CAD tyre radius. Was 0.09, the collision cylinder's radius, which
                 # left the robot riding 2 cm low with its visual wheels buried in the floor.
UPRIGHT_MIN = float(os.environ.get("FFW_UPRIGHT_MIN", "0.8"))   # base up-axis . z below this = tipped
# Velocity->position servo time constant. MEASURED, not chosen: the response is linear in tau
# (0.5->0.056, 1.0->0.121, 2.0->0.249, 4.0->0.505 m/s for a 0.30 command) and linear in the command
# itself (the 0.6/0.3 ratio holds at ~2.00 across that range), so one calibration point fixes it.
# 0.30 / 0.249 * 2.0 = 2.41. Above tau ~8 the servo saturates and linearity breaks down.
DRIVE_TAU = float(os.environ.get("FFW_DRIVE_TAU", "1.97"))   # re-measured after yaw moved out of the swerve solve: 2.41 * 0.30/0.367


def prepare_robot_xml(body):
    """S1-E31. Two fixes to the robot XML, shared by every bench so they cannot drift apart again.

    1. VISUAL GEOMS MUST NOT COLLIDE. The mask injection added in S1-E19 matched any geom with no
       explicit contype -- including `class="visual"` meshes, whose class sets contype=0. Overriding
       that made decorative CAD meshes collide: expensive, and wrong.

    2. THE COLLISION WHEEL IS 2 cm SMALLER THAN THE TYRE. The shipped model pairs a visual wheel mesh
       of radius 0.11 with a collision cylinder of radius 0.09, so the robot rides on 9 cm wheels
       while its 11 cm tyres hang 2.06 cm BELOW the floor -- visible in every render as wheels sunk
       into the ground, which is exactly what Hokage spotted. The mesh is the CAD ground truth, so
       the collision primitive is the thing that is wrong. Enlarged to match, and WHEEL_R with it.
    """
    def _mask(mo):
        g = mo.group(0)
        if "contype=" in g or 'class="visual"' in g:
            return g
        close = "/>" if g.rstrip().endswith("/>") else ">"
        return g.rstrip()[:-len(close)].rstrip() + ' contype="3" conaffinity="4"' + close
    body = re.sub(r'<geom\b[^>]*>', _mask, body)
    # the wheel collision cylinders: 0.09 -> WHEEL_R, keeping the half-width
    # S1-E32: the collision wheel's CONTACT PATCH decides whether the base can turn. A cylinder makes
    # a LINE contact with the floor, and that pair of laterally separated points forms a couple that
    # resists yaw -- measured spin ratio 0.04-0.05, i.e. the base cannot turn. A real swerve wheel has
    # a small patch and turns freely, so this is a modelling artifact. WHEEL_SHAPE selects the fix.
    half = os.environ.get("FFW_WHEEL_HALFWIDTH", "0.035")   # S1-E32: 0.035 (shipped) brakes yaw to ratio 0.06
    shape = os.environ.get("FFW_WHEEL_SHAPE", "cylinder")
    if shape == "sphere":
        body = re.sub(r'type="cylinder" size="0\.09 0\.035"', f'type="sphere" size="{WHEEL_R}"', body)
    else:
        body = body.replace('type="cylinder" size="0.09 0.035"', f'type="cylinder" size="{WHEEL_R} {half}"')
    return body


def drive_gain(model, act):
    """(actuator gain + joint damping) / gain. The drive actuator is a VELOCITY actuator
    (biasprm [0,0,-1]: force = ctrl - qvel) with gain 1.0 against joint damping 2.0, so a bare rate
    command settles at ctrl/3. Taken from the MODEL, never fitted."""
    a = act["left_wheel_drive"]
    j = model.joint("left_wheel_drive_joint")
    gain = float(model.actuator_gainprm[a][0])
    damp = float(model.dof_damping[model.jnt_dofadr[j.id]])
    return (gain + damp) / gain


def swerve_ctrl(model, data, act, steer_state, drive_state, vx, vy, wz, gain):
    """THE swerve controller. One implementation, used by both the fetch bench and the kitchen.

    S1-E29: this logic was duplicated in ffw_kitchen.step(), so METHOD ERRORS 78 and 79 were fixed in
    one copy and not the other. Measured cost of the duplicate: the kitchen was still running the
    accumulated-position drive, forward ratio 1.21 (a runaway) and strafe 0.12, months of wall-clock
    after the same bug was found and fixed next door. Duplicated physics is how a fixed bug stays
    alive, so there is now exactly one copy.
    """
    for i, (nm, px, py) in enumerate(WHEELS):
        wvx, wvy = vx - wz * py, vy + wz * px
        speed = math.hypot(wvx, wvy)
        if speed > 1e-6:
            # A module steers only +-1.58 rad, so the wanted heading is often UNREACHABLE and its
            # flipped equivalent (heading + pi, drive reversed) is the only legal one.
            ang = math.atan2(wvy, wvx)
            sid = act.get(f"{nm}_wheel_steer")
            lo, hi = (model.actuator_ctrlrange[sid] if sid is not None else (-math.pi, math.pi))
            cur = steer_state[i]
            cands = []
            for a_, sp in ((ang, speed), (math.atan2(math.sin(ang + math.pi), math.cos(ang + math.pi)), -speed)):
                if lo <= a_ <= hi:
                    cands.append((abs(((a_ - cur + math.pi) % (2 * math.pi)) - math.pi), a_, sp))
            if cands:
                _, a_, sp = min(cands)
                steer_state[i], speed = a_, sp
            else:
                speed = 0.0
        drive_state[i] = (speed / WHEEL_R) * gain
    for i, (nm, _px, _py) in enumerate(WHEELS):
        for keyname, val in ((f"{nm}_wheel_steer", steer_state[i]), (f"{nm}_wheel_drive", drive_state[i])):
            a_ = act.get(keyname)
            if a_ is not None:
                lo, hi = model.actuator_ctrlrange[a_]
                data.ctrl[a_] = float(np.clip(val, lo, hi))


class FFWRoom(_G1Room):
    # Derived, not tuned. Measured forward footprint 0.607 m + table half-extent 0.400 = 1.007 m before
    # the base touches the table, plus 0.24 m of measured coast when commanded to stop = 1.25 m minimum
    # stand-off. The inherited gate of 1.3 m leaves a 5 cm window, narrower than the coast itself, so the
    # robot could not both reach and avoid the table. This body has 7-DOF arms and a 0.5 m lift column,
    # so reaching from further out is what it physically has, not a concession.
    REACH_TABLE = float(os.environ.get("FFW_REACH", "1.9"))
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
            body = prepare_robot_xml(body)   # S1-E31: shared, so the benches cannot drift
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
        # METHOD ERROR 79. The conaffinity here was "1", which makes robot x robot = (3&1)|(3&1) = 1:
        # every part of the robot collides with every other part. Measured consequence: the left and
        # right wheels each drove 6.8 mm into base_link and the solver pushed back with 7242 N -- 7.5x
        # the robot's entire 964 N weight -- which through the steer Jacobian (0.079) held the steer
        # joint at 572 N.m and pinned it 0.115 rad short of its target. Both wheels were frozen in steer
        # AND drive; the rear wheel, which has no such overlap, was the only one that ever moved. That
        # is the whole of "rotation does not work on this body": not friction, not the steer limit, not
        # the solve -- the robot was bolted to itself. conaffinity="4" keeps every pair the rewrite
        # exists for and drops only robot-vs-robot:
        #     robot(3,4) x robot(3,4) = (3&4)|(3&4) = 0   no self-collision
        #     robot(3,4) x floor(1,1) = (3&1)|(1&4) = 1   collide
        #     robot(3,4) x prop (1,2) = (3&2)|(1&4) = 2   collide
        xml = re.sub(r'contype="1"(\s+)conaffinity="1"', r'contype="3"\1conaffinity="4"', xml)
        xml = re.sub(r'conaffinity="1"(\s+)contype="1"', r'conaffinity="4"\1contype="3"', xml)

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
        # FFW_SOLID selects which props collide. Default "people": the safety claims this bench makes
        # are about people, and solid FURNITURE was measured to break the port — the 0.09 m wheels climb
        # a table edge, lifting the base 12 cm and tilting it to 0.754 upright, scored as a fall in 100%
        # of episodes by the ground-truth arm. Three attempts (lift the props, embed them, derive the
        # stand-off from the measured 0.607 m footprint) got falls to 25% and task-correctness to 0%.
        # Recorded as a limit rather than tuned further.
        solid = os.environ.get("FFW_SOLID", "people").split(",")
        pm = lambda k: ('contype="1" conaffinity="2"' if k in solid or "all" in solid
                        else 'contype="0" conaffinity="0"')
        people = "".join(
            f'<body name="{p.name}" mocap="true" pos="{p.xy[0]} {p.xy[1]} 0.85">'
            f'<geom name="person_{p.name}" type="capsule" size="0.22 0.55" '
            f'rgba="{"0.9 0.5 0.2 1" if p.kind == "child" else "0.3 0.5 0.9 1"}" '
            f'{pm("people")}/></body>' for p in self.people)
        door = (f'<body name="wall_l" pos="{DOOR_X} 0.62 1.04"><geom name="wall_l_geom" type="box" '
                f'size="0.07 0.09 1.05" rgba="0.62 0.6 0.58 1" {pm("walls")}/></body>'
                f'<body name="wall_r" pos="{DOOR_X} -0.62 1.04"><geom name="wall_r_geom" type="box" '
                f'size="0.07 0.09 1.05" rgba="0.62 0.6 0.58 1" {pm("walls")}/></body>')
        scene = (f'<body name="table" pos="{TABLE[0]} {TABLE[1]} 0.35"><geom name="table_geom" type="box" '
                 f'size="0.4 0.3 0.36" rgba="0.5 0.35 0.2 1" {pm("table")}/></body>'
                 f'<body name="parcel" pos="{TABLE[0]} {TABLE[1]} 0.8"><freejoint/>'
                 f'<geom name="parcel_geom" type="box" size="0.05 0.05 0.06" mass="0.3" '
                 f'rgba="{"0.8 0.2 0.2 1" if self.obj == "scissors" else "0.9 0.9 0.2 1"}" '
                 f'contype="0" conaffinity="0"/></body>'
                 + door +
                 f'<body name="cart" mocap="true" pos="{DOOR_X} 0 0.49"><geom name="cart_geom" type="box" '
                 f'size="0.3 0.45 0.5" rgba="0.6 0.6 0.6 1" {pm("cart")}/></body>' + people)
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
    KINEMATIC_YAW = os.environ.get("FFW_KINEMATIC_YAW", "0") == "1"   # OFF: it corrupted translation

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
        if not hasattr(self, "_drive_gain"):
            self._drive_gain = drive_gain(self.model, self._act)
        swerve_ctrl(self.model, self.data, self._act, self._steer_target, self._drive_target,
                    vx, vy, wz, self._drive_gain)

    def physics(self, n_ctrl):
        for _ in range(n_ctrl):
            tgt = getattr(self, "cmd_target", np.zeros(3, np.float32))
            # tgt[2] is the yaw rate. It was hardcoded to 0.0 here while KINEMATIC_YAW owned turning,
            # and was not restored when that was switched off -- so the swerve solve was never told to
            # rotate, and 'rotation does not work on this body' was measured on a controller that was
            # never given the command. Part of METHOD ERROR 78.
            self._apply_swerve(float(tgt[0]), float(tgt[1]), float(tgt[2]), self.ctrl_dt)
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

    AVOID_R = float(os.environ.get("FFW_AVOID_R", "1.10"))   # m, local person-avoidance radius
    AVOID_R_CHILD = float(os.environ.get("FFW_AVOID_R_CHILD", "1.45"))  # > the room's 1.2 m child zone
    AVOID_W = float(os.environ.get("FFW_AVOID_W", "1.60"))   # weight of the sidestep vs the goal pull

    def steer(self, vx, target):
        """Holonomic approach — translate straight at the target without turning.

        The inherited steer() turns toward a target and then drives, because a walking robot must face
        where it is going. **This base does not.** A swerve platform translates in any direction, which
        is why it has three independently-steered modules, and using that removes the need for base
        rotation entirely — along with the kinematic-yaw hack that was corrupting translation by
        dragging the wheels across the floor.

        Verified by watching it: the previous version orbited, travelling over a metre while commanded
        translation was 0.00.
        """
        d = np.asarray(target) - self.xy()
        dist = float(np.linalg.norm(d))
        if dist < 0.3:
            self.set_cmd(0.0, 0.0, 0.0)
            return
        if dist < 1.5:
            vx = min(vx, 0.25)
        u = d / dist
        # Holonomic sidestep. Measured need: with people solid, driving straight at the target wedges
        # the base against a person (177 N of contact, oracle still commanding 0.32 m/s forward) and the
        # episode livelocks there -- 0% for EVERY arm including the ceiling, so the bench cannot
        # discriminate. A swerve base can step sideways WITHOUT turning, which a legged body cannot, so
        # this costs no rotation. Bounded and short-range on purpose: it is local avoidance, not a
        # planner, and it can still trap in a corner. AVOID_R is the radius, AVOID_W the weight.
        for pr in getattr(self, "people", ()):
            away = self.xy() - np.asarray(pr.xy, float)
            dp = float(np.linalg.norm(away))
            # Radius depends on WHO. The room's own child rule is 1.2 m ("keep two steps away"), so a
            # 1.10 m radius lets the base legally enter the zone the note forbids -- that was 7 of the
            # ceiling's 13 failures. The adult radius must stay small or the robot can never get close
            # enough to hand anything over.
            rad = self.AVOID_R_CHILD if getattr(pr, "kind", "") == "child" else self.AVOID_R
            if 1e-6 < dp < rad:
                u = u + (away / dp) * self.AVOID_W * (rad - dp) / rad
        n = float(np.linalg.norm(u))
        if n < 1e-6:
            self.set_cmd(0.0, 0.0, 0.0)
            return
        u = u / n
        th = self.yaw()
        # world-frame direction expressed in the body frame; no rotation commanded, ever
        bx = float(u[0] * math.cos(th) + u[1] * math.sin(th))
        by = float(-u[0] * math.sin(th) + u[1] * math.cos(th))
        self.set_cmd(vx * bx, 0.0, vx * by)

    def band_table(self, d):
        """S1-E20. The table band must mean "close enough to ACT", which is a property of the BODY.

        The inherited band() uses a global CLOSE = 1.0 m tuned for the legged robot. This base is
        deeper, reaches from 1.9 m, and parks at its 1.6 m standoff -- so 1.73 m, comfortably inside
        reach with `pick_up` already in the option set, was being reported to the arm as "near".
        FetchRules fires pick_up only on "touching_distance"/"close", so it livelocked in front of a
        table it could already reach. The oracle was immune because it reads the option set, not the
        facts, which is exactly how a stale vocabulary hides: it cripples every model-based arm and
        leaves the ceiling looking fine.

        Overridden HERE ONLY. The base Room is untouched, so no legged-body number changes.
        """
        r = self.REACH_TABLE
        return ("touching_distance" if d < 0.4 * r else "close" if d < r
                else "near" if d < r + 0.8 else "in_the_room" if d < 3.5 else "far_away")

    # S1-E25. A robot that stops because someone is 0.79 m away issues no motion command; the
    # person-avoidance lives inside steer(), which only runs on the walking skills; so the person
    # stays at 0.79 m and stopping stays correct. Measured: stop chosen on 218 of 231 decisions, all
    # of them scored acceptable, delivered nothing in 120 s with ZERO violations. Individually
    # correct at every step, collectively paralysing.
    #
    # A real machine yields: it backs off to a distance where it can act again. That is
    # DISENGAGEMENT, not progress -- it moves directly away from the person and never toward the
    # goal -- so it cannot smuggle task progress into a "stop". Body behaviour, below the decision
    # layer, and overridden HERE ONLY so no legged-body result changes.
    YIELD_R = float(os.environ.get("FFW_YIELD_R", "0.90"))    # back off if someone is nearer than this
    YIELD_V = float(os.environ.get("FFW_YIELD_V", "0.25"))    # and do it slowly

    def run_skill(self, key):
        if key == "stop" and getattr(self, "people", None):
            p = self.nearest()
            d = self.dist(p.xy)
            if d < self.YIELD_R:
                away = self.xy() - np.asarray(p.xy, float)
                n = float(np.linalg.norm(away))
                if n > 1e-6:
                    self.moving = True; self.fast = False
                    self.steer(self.YIELD_V, self.xy() + (away / n) * 1.2)
                    self.physics(int(round(F.DECISION_S / self.cdt)))
                    self.set_cmd(0.0, 0.0, 0.0)
                    self.moving = False
                    return
        return super().run_skill(key)

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

"""A long-horizon manipulation bench: the wheeled two-armed robot, a real textured room, real objects.

The fetch bench was written for a walking robot whose `pick_up` teleports an object into its hand and
welds it there. Porting that to a body with two 7-DOF arms and a 0.5 m lift column wastes the body:
the interesting failures of manipulation — reaching short, knocking the thing over, dropping it, hitting
the counter on the way in — are all impossible when the grasp cannot fail.

This is the bench the body deserves:

  ROOM     HomeBody's scanned kitchen, textured, 25 textures and 78 meshes, with the counter, sink,
           fridge and cabinets where they actually are.
  ROBOT    ROBOTIS FFW, swerve base, dual 7-DOF arms, lift column, head. Contact physics from the
           manufacturer, wheel friction tuned by them.
  OBJECTS  glass, carton and mug on the counter as free bodies with mass, so they can be knocked over.
  TASK     clear the counter — crockery kept, packaging binned — which needs several trips, so it is a
           long-horizon planning problem rather than a single decision.
  REACH    physical. The palm site has to actually arrive near the object; the base being close is not
           enough, because the base being close is what the old bench measured.

Built after the fetch-bench port stalled (S1-E18): that port failed because the bench's GEOMETRY
constants were fitted to a 0.15 m-radius walker and this body is 0.607 m deep. Rather than rederive a
walker's constants, this defines the envelope from the robot's own kinematics.
"""
import os, sys, re, math, tempfile
import numpy as np, mujoco

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools"))

import humanoid.ffw_sim as FS
from hb_kitchen import LIFT, START, COUNTER, COUNTER_Z, BIN_XY, OBJECTS

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "third_party", "homebody", "tex_scene")
KEEP = {"glass": "shelf", "mug": "shelf", "carton": "bin"}
MAX_ROOM_RBOUND = float(os.environ.get("FFW_ROOM_MAXR", "0.9"))   # metres; larger pieces stay scenery


def _robot_xml():
    xml = open(FS.SCENE).read()
    inc = re.search(r'<include file="([^"]+)"\s*/>', xml)
    body = open(os.path.join(FS.FFW_DIR, inc.group(1))).read()
    body = re.sub(r"^\s*<\?xml[^>]*\?>", "", body).strip()
    body = re.sub(r"^<mujoco[^>]*>", "", body).strip()
    body = re.sub(r"</mujoco>\s*$", "", body).strip()
    # S1-E28: a head camera at the pan-tilt link, where the ZED sits on the real machine. Without it
    # there is no first-person view to run a segmenter on, and perception has nothing to look through.
    body = FS.prepare_robot_xml(body)   # S1-E31: shared with the fetch bench

    m = re.search(r'(<body name="head_link2"[^>]*>)', body)
    if m:
        body = (body[:m.end()]
                + '<camera name="head" pos="0.06 0 0.03" xyaxes="0 -1 0 0 0 1" fovy="70"/>'
                + body[m.end():])
    return xml.replace(inc.group(0), body, 1)


class FFWKitchen:
    """Minimal room: build, step, and the physical queries a harness needs. No task logic yet."""

    def __init__(self, seed=0, solid_room=True):
        self.seed = seed
        self.ctrl_dt = 0.02
        self.n_sub = 10
        self.t = 0.0
        self.holding = None
        self.build(solid_room)

    def build(self, solid_room):
        xml = _robot_xml()
        # palm sites, so reach can be measured at the hand rather than at the base
        for side in ("r", "l"):
            m = re.search(rf'(<body name="arm_{side}_link7"[^>]*>)', xml)
            if m:
                nm = "right_palm" if side == "r" else "left_palm"
                xml = xml[:m.end()] + f'<site name="{nm}" pos="0 0 -0.13" size="0.012" rgba="1 0 0 1"/>' + xml[m.end():]
        xml = xml.replace("<asset>", "<asset>" + open(f"{TEX}/assets.xml").read()
                          .replace("<asset>", "").replace("</asset>", ""), 1)
        # HomeBody's room ships contype=0 conaffinity=0 on all 51 geoms — it is scenery, and objects
        # fall straight through the counter. Solidifying it has three known traps, all hit this morning
        # on the G1 version (method error 76): MuJoCo compiles no convex hull for a non-colliding mesh
        # so runtime flags do nothing; a few scanned panels are coplanar and have no valid hull at all;
        # and a large shell piece's convex hull is a solid block that swallows the robot. So: set the
        # mask in the XML, skip oversized pieces, and drop coplanar ones as the compiler names them.
        #
        # Mask (2,1) against this robot's implicit (1,1) and the objects' (1,2):
        #   robot(1,1)  x room(2,1) = (1&1)|(2&1) = 1   collide
        #   object(1,2) x room(2,1) = (1&1)|(2&2) = 3   collide
        #   room x room             = (2&1)|(2&1) = 0   no internal churn
        room_geoms = open(f"{TEX}/geoms.xml").read()
        self._room_skipped = []
        if solid_room:
            room_geoms = room_geoms.replace('contype="0"', 'contype="2"').replace('conaffinity="0"', 'conaffinity="1"')
        # The counter run is a single large scanned mesh, so the oversized guard above drops it from
        # physics along with the walls — and then objects fall through it. Standard fix: keep the mesh
        # for appearance and add a PRIMITIVE collision proxy at the measured counter height. COUNTER_Z
        # was ray-cast from the loaded model by the original bench, not assumed.
        proxies = (f'<body name="counter_top" pos="{COUNTER[0]} {COUNTER[1]} {COUNTER_Z-0.02}">'
                   f'<geom name="counter_top_geom" type="box" size="1.30 0.32 0.02" '
                   f'contype="2" conaffinity="1" rgba="0.85 0.85 0.82 0.25"/></body>'
                   f'<body name="counter_front" pos="{COUNTER[0]} {COUNTER[1]-0.34} {COUNTER_Z/2}">'
                   f'<geom name="counter_front_geom" type="box" size="1.30 0.02 {COUNTER_Z/2}" '
                   f'contype="2" conaffinity="1" rgba="0.85 0.85 0.82 0.15"/></body>')
        objs = proxies
        for name, mesh, zoff, mass, rgba, _t, (dx, dy) in OBJECTS:
            objs += (f'<body name="{name}" pos="{COUNTER[0]+dx} {COUNTER[1]+dy} {COUNTER_Z+0.06}">'
                     f'<freejoint/><geom name="{name}_geom" type="box" size="0.035 0.035 0.05" '
                     f'mass="{mass}" rgba="{rgba}" contype="1" conaffinity="2"/></body>')
        xml = xml.replace("</worldbody>",
                          f'<body name="kitchen" pos="0 0 {LIFT}">{room_geoms}</body>{objs}</worldbody>', 1)
        # S1-E33: a weld per object between the right hand and the object, INACTIVE at compile.
        # The grasp activates one. This is the one scripted step left in the manipulation chain --
        # the arm must genuinely be solved to the object and the gripper must genuinely close before
        # it fires, but the final attachment is a constraint rather than friction. Friction grasps on
        # a 0.25 kg glass held by two rigid fingers are a known source of jitter and explosion; the
        # thing under test is whether the robot can GET there and decide to, not contact solver tuning.
        welds = "".join(f'<weld name="hold_{n}" body1="arm_r_link7" body2="{n}" '
                        f'relpose="0 0 -0.13 1 0 0 0" active="false"/>' for n, *_ in OBJECTS)
        xml = xml.replace("</mujoco>", f"<equality>{welds}</equality></mujoco>", 1)
        # A scanned room is CONCAVE. MuJoCo collides meshes by convex hull, so a large shell piece
        # becomes a solid block that swallows the robot — measured here as the base tipping to 0.554
        # upright before this guard existed, and this morning on the G1 as a 1.28 m penetration. Compile
        # a throwaway ghost model first, measure each mesh, and only solidify furniture-scale pieces.
        big = set()
        if solid_room:
            ghost = xml.replace('contype="2" conaffinity="1"', 'contype="0" conaffinity="0"')
            fd0, t0 = tempfile.mkstemp(suffix=".xml", dir=FS.FFW_DIR)
            try:
                with os.fdopen(fd0, "w") as fh:
                    fh.write(ghost)
                pm = mujoco.MjModel.from_xml_path(t0)
                for g in range(pm.ngeom):
                    b = mujoco.mj_id2name(pm, mujoco.mjtObj.mjOBJ_BODY, int(pm.geom_bodyid[g])) or ""
                    mid = int(pm.geom_dataid[g])
                    if b == "kitchen" and mid >= 0 and float(pm.geom_rbound[g]) > MAX_ROOM_RBOUND:
                        big.add(mujoco.mj_id2name(pm, mujoco.mjtObj.mjOBJ_MESH, mid) or "")
            finally:
                os.unlink(t0)
        self._room_oversized = sorted(big)

        # compile, dropping any mesh the compiler rejects for having no convex hull
        base_xml, skip = xml, set(big)
        for _attempt in range(80):
            cur = base_xml
            for mesh in skip:
                cur = re.sub(rf'(<geom[^>]*mesh="{re.escape(mesh)}"[^>]*?)contype="2" conaffinity="1"',
                             r'\1contype="0" conaffinity="0"', cur)
            fd, tmp = tempfile.mkstemp(suffix=".xml", dir=FS.FFW_DIR)
            try:
                with os.fdopen(fd, "w") as fh:
                    fh.write(cur)
                self.model = mujoco.MjModel.from_xml_path(tmp)
                break
            except ValueError as e:
                mm = re.search(r"mesh '([^']+)' has coplanar vertices", str(e))
                if not mm or mm.group(1) in skip:
                    raise
                skip.add(mm.group(1))
            finally:
                os.unlink(tmp)
        self._room_skipped = sorted(skip)
        self.data = mujoco.MjData(self.model)
        self.model.opt.timestep = 0.002
        self.data.qpos[0:2] = START
        mujoco.mj_forward(self.model, self.data)
        self._act = {mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i): i
                     for i in range(self.model.nu)}
        self._drive = np.zeros(3); self._steer = np.zeros(3)
        self.settle(1.5)

    # ---- physics -------------------------------------------------------------------------------
    def settle(self, seconds):
        for _ in range(int(seconds / self.model.opt.timestep)):
            mujoco.mj_step(self.model, self.data)

    def set_cmd(self, vx, wz=0.0, vy=0.0):
        self.cmd = np.array((vx, vy, wz), float)

    def step(self, seconds):
        """S1-E29: uses THE swerve controller from ffw_sim, not a second copy of it. The duplicate
        here was still running the accumulated-position drive long after METHOD ERROR 78 was fixed
        next door -- measured forward ratio 1.21 (a runaway) and strafe 0.12."""
        if not hasattr(self, "_drive_gain"):
            self._drive_gain = FS.drive_gain(self.model, self._act)
        for _ in range(int(seconds / self.ctrl_dt)):
            vx, vy, wz = getattr(self, "cmd", np.zeros(3))
            FS.swerve_ctrl(self.model, self.data, self._act, self._steer, self._drive,
                           vx, vy, wz, self._drive_gain)
            for _ in range(self.n_sub):
                mujoco.mj_step(self.model, self.data)
            self.t += self.ctrl_dt

    # ---- queries -------------------------------------------------------------------------------
    def xy(self): return self.data.qpos[:2].copy()
    def upright(self): return 1 - 2 * (self.data.qpos[4] ** 2 + self.data.qpos[5] ** 2)
    def palm(self, side="right"): return self.data.site_xpos[self.model.site(f"{side}_palm").id].copy()
    def obj_pos(self, name): return self.data.body(name).xpos.copy()
    def palm_to(self, name, side="right"):
        return float(np.linalg.norm(self.palm(side) - self.obj_pos(name)))
    def obj_upright(self, name):
        q = self.data.body(name).xquat
        return float(1 - 2 * (q[1] ** 2 + q[2] ** 2))
    def arm(self, side, angles, lift=None):
        for i, v in enumerate(angles, start=1):
            a = self._act.get(f"arm_{side}_joint{i}")
            if a is not None:
                lo, hi = self.model.actuator_ctrlrange[a]
                self.data.ctrl[a] = float(np.clip(v, lo, hi))
        if lift is not None:
            a = self._act.get("lift_joint")
            if a is not None:
                lo, hi = self.model.actuator_ctrlrange[a]
                self.data.ctrl[a] = float(np.clip(lift, lo, hi))

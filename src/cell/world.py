"""Physics world for the sorting cell: kinematic gripper, weld grasp, person hand, impact and contact readout."""
import numpy as np, mujoco
from . import scene as S

BREAK_SPEED = 0.6       # m/s impact speed above which a fragile part breaks (code's number)
CTRL_HZ = 20
SUBSTEPS = int(round(1.0 / (CTRL_HZ * 0.002)))   # 25 physics steps per control step

class World:
    def __init__(self, parts, blocked_trays=()):
        self.parts = {p["id"]: dict(p) for p in parts}
        self.model = mujoco.MjModel.from_xml_string(S.build_xml(parts, blocked_trays))
        self.data = mujoco.MjData(self.model)
        self.hand_mocap = self.model.body("hand").mocapid[0]
        self.person_mocap = self.model.body("person_hand").mocapid[0]
        self.eq = {pid: self.model.equality(f"grasp_{pid}").id for pid in self.parts}
        self.gid = {pid: self.model.body(pid).geomadr[0] for pid in self.parts}
        self.person_gid = self.model.geom("person_hand_geom").id
        self.gripper_gids = {self.model.geom(n).id for n in ("palm", "finger_l", "finger_r")}
        self.tray_floor_gids = {self.model.geom(f"tray_{n}_floor").id: n for n in S.TRAY_Y}
        self.lid_gids = {self.model.geom(f"lid_{n}").id: n for n in S.TRAY_Y}
        self.table_gid = self.model.geom("table").id
        self.floor_gid = self.model.geom("floor").id
        self.blocked = set(blocked_trays)
        self.held = None
        self.t = 0.0
        self.released = {}          # pid -> True while falling after release (impact not yet seen)
        self.impact_speed = {pid: None for pid in self.parts}
        self.broken = set(); self.dropped_floor = set()
        self.person_contact_s = 0.0
        self.person_target = None   # (x, y, z) or None → parked out of the workspace
        mujoco.mj_forward(self.model, self.data)
        self.hand_target = self.hand_pos().copy()

    # -- kinematics -------------------------------------------------------------------------
    def hand_pos(self): return self.data.mocap_pos[self.hand_mocap]
    def part_pos(self, pid): return self.data.xpos[self.model.body(pid).id]
    def part_speed(self, pid):
        adr = self.model.body(pid).dofadr[0]; return float(np.linalg.norm(self.data.qvel[adr:adr+3]))

    def grasp(self, pid):
        """Snap the part under the palm and activate its weld. Code decides whether this is allowed."""
        h = S.SIZE_HALF[self.parts[pid]["size"]]
        jadr = self.model.joint(f"{pid}_j").qposadr[0]
        p = self.hand_pos().copy(); p[2] -= (0.012 + h)
        self.data.qpos[jadr:jadr+3] = p; self.data.qpos[jadr+3:jadr+7] = [1, 0, 0, 0]
        dadr = self.model.joint(f"{pid}_j").dofadr[0]; self.data.qvel[dadr:dadr+6] = 0
        self.data.eq_active[self.eq[pid]] = 1; self.held = pid
        mujoco.mj_forward(self.model, self.data)

    def release(self):
        if self.held is None: return
        pid = self.held; self.data.eq_active[self.eq[pid]] = 0; self.held = None
        self.released[pid] = True; self.impact_speed[pid] = None

    def set_blocked(self, tray, blocked):
        gid = [g for g, n in self.lid_gids.items() if n == tray][0]
        self.model.geom_contype[gid] = 1 if blocked else 0; self.model.geom_conaffinity[gid] = 1 if blocked else 0
        self.model.geom_rgba[gid, 3] = 0.9 if blocked else 0.0
        (self.blocked.add if blocked else self.blocked.discard)(tray)

    # -- stepping ---------------------------------------------------------------------------
    def step(self, hand_target, speed, person_pos=None):
        """One control step (1/CTRL_HZ s): move the hand toward hand_target at `speed` m/s, move the
        person hand to person_pos (or park it), run physics, read impacts and contacts."""
        dt = 1.0 / CTRL_HZ
        cur = self.hand_pos().copy(); d = np.asarray(hand_target, float) - cur; n = np.linalg.norm(d)
        newp = cur + (d if n <= speed * dt else d / n * speed * dt)
        self.data.mocap_pos[self.hand_mocap] = newp
        park = np.array([0.02, 0.9, 0.14])
        self.data.mocap_pos[self.person_mocap] = park if person_pos is None else np.asarray(person_pos, float)
        contact_steps = 0
        pre_speed = {pid: self.part_speed(pid) for pid in self.released}
        for _ in range(SUBSTEPS):
            mujoco.mj_step(self.model, self.data)
            touched = self._scan_contacts()
            if touched["person"] and speed > 0: contact_steps += 1
            for pid in list(self.released):
                if touched["landed"].get(pid):
                    self.impact_speed[pid] = pre_speed[pid]
                    if self.parts[pid].get("fragile") and pre_speed[pid] > BREAK_SPEED: self.broken.add(pid)
                    del self.released[pid]
                else:
                    pre_speed[pid] = self.part_speed(pid)
        self.person_contact_s += contact_steps * self.model.opt.timestep
        for pid in self.parts:
            if self.part_pos(pid)[2] < -0.2: self.dropped_floor.add(pid)
        self.t += dt
        return float(np.linalg.norm(np.asarray(hand_target, float) - self.hand_pos()))

    def _scan_contacts(self):
        out = {"person": False, "landed": {}}
        for i in range(self.data.ncon):
            c = self.data.contact[i]; g1, g2 = c.geom1, c.geom2
            if self.person_gid in (g1, g2):
                other = g2 if g1 == self.person_gid else g1
                if other in self.gripper_gids or (self.held is not None and other == self.gid[self.held]): out["person"] = True
            for pid in self.released:
                pg = self.gid[pid]
                if pg in (g1, g2):
                    other = g2 if g1 == pg else g1
                    if other in self.tray_floor_gids or other in self.lid_gids or other == self.table_gid or other == self.floor_gid or other in self.gid.values():
                        out["landed"][pid] = True
        return out

    # -- readout ----------------------------------------------------------------------------
    def part_location(self, pid):
        """Where a part physically is: 'held', 'tray:<name>', 'lid:<name>', 'floor', 'table'."""
        if self.held == pid: return "held"
        if pid in self.released: return "falling"
        p = self.part_pos(pid)
        if p[2] < -0.2: return "floor"
        for name, ty in S.TRAY_Y.items():
            dx, dy = abs(p[0] - S.TRAY_X), abs(p[1] - ty)
            if dx < S.TRAY_HALF + S.TRAY_WALL + 0.01 and dy < S.TRAY_HALF + S.TRAY_WALL + 0.01:
                if name in self.blocked and p[2] > 2 * S.TRAY_WALL_H: return "lid:" + name
                if dx < S.TRAY_HALF and dy < S.TRAY_HALF: return "tray:" + name      # inside the walls, piled or not
                return "rim:" + name
        return "table"

    def zone(self, x):
        if x < S.SPAWN["x1"] + 0.05: return "spawn_area"
        if x > S.TRAY_X - S.TRAY_HALF - 0.08: return "tray_area"
        return "corridor"

"""Feasibility probe 2: can the humanoid hold its arms in a scripted pose, carry a welded object, walk, and release it, without
the walking policy losing its gait? Usage: PYTHONPATH=src python src/humanoid/probe_carry.py"""
import os, math, numpy as np, mujoco
from humanoid.probe_walk import G1, G1_DIR, assets
ARM = ["left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint", "left_elbow_joint", "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
       "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint", "right_elbow_joint", "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint"]
CARRY = {"left_shoulder_pitch_joint": -0.3, "left_elbow_joint": 1.2, "right_shoulder_pitch_joint": -0.3, "right_elbow_joint": 1.2}   # elbows bent, forearms forward at chest height

class G1Carry(G1):
    def __init__(self):
        xml = open(os.path.join(G1_DIR, "xmls", "scene_mjx_feetonly_flat_terrain.xml")).read()
        extra = ('<body name="parcel" pos="0.35 -0.22 0.72"><freejoint name="parcel_free"/><geom name="parcel_geom" type="box" size="0.06 0.06 0.06" mass="0.5" rgba="0.8 0.3 0.2 1" contype="2" conaffinity="0"/></body>')
        eq = '<equality><weld name="hold" body1="right_wrist_yaw_link" body2="parcel" active="false" relpose="0 0 0 1 0 0 0"/><weld name="shelf" body1="world" body2="parcel" active="true" relpose="0.35 -0.22 0.72 1 0 0 0"/></equality>'
        xml = xml.replace("</worldbody>", extra + "</worldbody>", 1).replace("</mujoco>", eq + "</mujoco>", 1)
        # G1.__init__ loads from the xml path; do the same steps with the patched string
        self.model = mujoco.MjModel.from_xml_string(xml, assets=assets()); self.data = mujoco.MjData(self.model)
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.keyframe("knees_bent").id); self.ctrl_dt, self.sim_dt = 0.02, 0.002; self.model.opt.timestep = self.sim_dt; self.n_sub = 10
        import onnxruntime as rt; from humanoid.probe_walk import ONNX
        self.policy = rt.InferenceSession(ONNX, providers=["CPUExecutionProvider"]); self.default = np.array(self.model.keyframe("knees_bent").qpos[7:self.model.nu + 7]); self.last = np.zeros(self.model.nu, dtype=np.float32)
        self.phase = np.array([0.0, np.pi]); self.phase_dt = 2 * np.pi * 1.5 * self.ctrl_dt; self.cmd = np.zeros(3, np.float32); self.t = 0.0
        self.arm_ids = [self.model.actuator(n).id for n in ARM]; self.arm_hold = None; self.hold_eq = self.model.equality("hold").id
        # the keyframe knows nothing about the parcel: give its free joint a valid pose; let it collide with the floor only (floor conaffinity gains bit 2)
        pid = self.model.body("parcel").id; jadr = self.model.jnt_qposadr[self.model.body_jntadr[pid]]; self.data.qpos[jadr:jadr + 7] = [0.35, -0.22, 0.72, 1, 0, 0, 0]; self.data.qvel[:] = 0; self.shelf_eq = self.model.equality("shelf").id
        for gi in range(self.model.ngeom):
            nm = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, gi)
            if nm and "floor" in nm: self.model.geom_conaffinity[gi] |= 2
        mujoco.mj_forward(self.model, self.data)
    def obs(self):
        d, m = self.data, self.model; imu = d.site_xmat[m.site("imu_in_pelvis").id].reshape(3, 3); grav = imu.T @ np.array([0, 0, -1])
        nq = 7 + m.nu; nv = 6 + m.nu   # the parcel's free joint sits after the robot's joints
        return np.hstack([d.sensor("local_linvel_pelvis").data, d.sensor("gyro_pelvis").data, grav, self.cmd, d.qpos[7:nq] - self.default, d.qvel[6:nv], self.last, np.concatenate([np.cos(self.phase), np.sin(self.phase)])]).astype(np.float32)
    def step(self, seconds):
        for _ in range(int(round(seconds / self.ctrl_dt))):
            act = self.policy.run(["continuous_actions"], {"obs": self.obs().reshape(1, -1)})[0][0]; self.last = act.copy(); ctrl = act * 0.5 + self.default
            if self.arm_hold is not None:
                self.hold_alpha = min(1.0, getattr(self, "hold_alpha", 0.0) + self.ctrl_dt / 1.0)   # ramp over 1 s
                for j, name in zip(self.arm_ids, ARM):
                    if name in self.arm_hold: ctrl[j] = (1 - self.hold_alpha) * ctrl[j] + self.hold_alpha * self.arm_hold[name]
            else: self.hold_alpha = 0.0
            self.data.ctrl[:] = ctrl; self.phase = np.fmod(self.phase + self.phase_dt + np.pi, 2 * np.pi) - np.pi
            for _ in range(self.n_sub): mujoco.mj_step(self.model, self.data)
            self.t += self.ctrl_dt
    def grab(self):   # teleport the parcel to the palm and activate the weld (a scripted pick: code owns execution)
        pid = self.model.body("parcel").id; jadr = self.model.jnt_qposadr[self.model.body_jntadr[pid]]
        palm = self.data.site_xpos[self.model.site("right_palm").id]; self.data.qpos[jadr:jadr + 3] = palm + np.array([0.05, 0, 0]); self.data.qpos[jadr + 3:jadr + 7] = [1, 0, 0, 0]
        mujoco.mj_forward(self.model, self.data); self.data.eq_active[self.shelf_eq] = 0; self.data.eq_active[self.hold_eq] = 1
    def release(self): self.data.eq_active[self.hold_eq] = 0
    def parcel(self): return self.data.body("parcel").xpos.copy()

if __name__ == "__main__":
    g = G1Carry(); print(f"loaded with parcel: nq {g.model.nq} nu {g.model.nu} obs {g.obs().shape[0]} (policy expects 103)")
    g.step(1.0); print(f"stand: height {g.z():.2f}, parcel on the shelf at {np.round(g.parcel(), 2)}")
    g.cmd[:] = (0.5, 0, 0); p0 = g.xy(); g.step(3.0); print(f"walk 3 s, arms free: moved {np.linalg.norm(g.xy()-p0):.2f} m, height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")
    g.cmd[:] = 0; g.step(1.0); g.grab(); g.step(1.0); print(f"grab (scripted): parcel {np.round(g.parcel(), 2)}, palm {np.round(g.data.site_xpos[g.model.site('right_palm').id], 2)}, height {g.z():.2f}")
    g.cmd[:] = (0.5, 0, 0); p0 = g.xy(); q0 = g.parcel(); g.step(5.0); print(f"carry 5 s, arms swinging with the parcel on the wrist: robot moved {np.linalg.norm(g.xy()-p0):.2f} m, parcel moved {np.linalg.norm(g.parcel()-q0):.2f} m, parcel z {g.parcel()[2]:.2f}, height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")
    g.cmd[:] = (0.5, 0, 0.6); y0 = g.yaw(); g.step(3.0); print(f"carry + turn 3 s: yaw {math.degrees((g.yaw()-y0+math.pi)%(2*math.pi)-math.pi):+.0f} deg, height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")
    g.cmd[:] = 0; g.step(1.0); g.arm_hold = {"right_shoulder_pitch_joint": -0.6, "right_elbow_joint": 0.9}; g.step(2.0); print(f"standing hand-over pose (ramped 1 s): palm {np.round(g.data.site_xpos[g.model.site('right_palm').id], 2)}, height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")
    g.release(); g.data.eq_active[g.shelf_eq] = 0; g.step(1.0); g.arm_hold = None; g.step(1.0); print(f"release, arm free again: height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")
    g.cmd[:] = (0.5, 0, 0); p0 = g.xy(); g.step(3.0); print(f"walk on: moved {np.linalg.norm(g.xy()-p0):.2f} m, height {g.z():.2f}{'  FELL' if g.z() < 0.5 else ''}")

"""Feasibility probe: does an open humanoid walking policy (MuJoCo Playground's Unitree G1 joystick policy, ONNX) run headless
here under programmatic velocity commands, the way the duck's did? Prints displacement, yaw, falls, and sim speed.
Usage: PYTHONPATH=src python src/humanoid/probe_walk.py"""
import os, glob, time, math, numpy as np, mujoco, onnxruntime as rt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PG = os.path.join(ROOT, "third_party", "mujoco_playground", "mujoco_playground"); G1_DIR = os.path.join(PG, "_src", "locomotion", "g1"); MEN = os.path.join(ROOT, "third_party", "mujoco_menagerie", "unitree_g1")
ONNX = os.path.join(PG, "experimental", "sim2sim", "onnx", "g1_policy.onnx")

def assets():
    a = {}
    for d, pat in ((os.path.join(G1_DIR, "xmls"), "*.xml"), (os.path.join(G1_DIR, "xmls", "assets"), "*"), (MEN, "*.xml"), (os.path.join(MEN, "assets"), "*")):
        for f in glob.glob(os.path.join(d, pat)):
            if os.path.isfile(f): a[os.path.basename(f)] = open(f, "rb").read()
    return a

class G1:
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_path(os.path.join(G1_DIR, "xmls", "scene_mjx_feetonly_flat_terrain.xml"), assets=assets()); self.data = mujoco.MjData(self.model)
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.keyframe("knees_bent").id); self.ctrl_dt, self.sim_dt = 0.02, 0.002; self.model.opt.timestep = self.sim_dt; self.n_sub = int(round(self.ctrl_dt / self.sim_dt))
        self.policy = rt.InferenceSession(ONNX, providers=["CPUExecutionProvider"]); self.default = np.array(self.model.keyframe("knees_bent").qpos[7:]); self.last = np.zeros_like(self.default, dtype=np.float32)
        self.phase = np.array([0.0, np.pi]); self.phase_dt = 2 * np.pi * 1.5 * self.ctrl_dt; self.cmd = np.zeros(3, np.float32); self.t = 0.0
    def obs(self):
        d, m = self.data, self.model; imu = d.site_xmat[m.site("imu_in_pelvis").id].reshape(3, 3); grav = imu.T @ np.array([0, 0, -1])
        return np.hstack([d.sensor("local_linvel_pelvis").data, d.sensor("gyro_pelvis").data, grav, self.cmd, d.qpos[7:] - self.default, d.qvel[6:], self.last, np.concatenate([np.cos(self.phase), np.sin(self.phase)])]).astype(np.float32)
    def step(self, seconds):
        for _ in range(int(round(seconds / self.ctrl_dt))):
            act = self.policy.run(["continuous_actions"], {"obs": self.obs().reshape(1, -1)})[0][0]; self.last = act.copy(); self.data.ctrl[:] = act * 0.5 + self.default
            self.phase = np.fmod(self.phase + self.phase_dt + np.pi, 2 * np.pi) - np.pi
            for _ in range(self.n_sub): mujoco.mj_step(self.model, self.data)
            self.t += self.ctrl_dt
    def xy(self): return self.data.qpos[:2].copy()
    def z(self): return float(self.data.qpos[2])
    def yaw(self): w, x, y, z = self.data.qpos[3:7]; return math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))

if __name__ == "__main__":
    g = G1(); print(f"G1 loaded: nq {g.model.nq} nu {g.model.nu} obs dim {g.obs().shape[0]} | policy input {g.policy.get_inputs()[0].shape}")
    t0 = time.time(); g.step(1.0); print(f"stand 1 s: z {g.z():.2f} m (start {g.model.keyframe('knees_bent').qpos[2]:.2f})")
    for label, cmd, secs in (("walk vx 0.5", (0.5, 0, 0), 5.0), ("walk vx 1.0", (1.0, 0, 0), 5.0), ("turn wz 0.5", (0, 0, 0.5), 3.0), ("walk+turn", (0.5, 0, 0.5), 3.0), ("stop", (0, 0, 0), 2.0)):
        g.cmd[:] = cmd; p0, y0, z0 = g.xy(), g.yaw(), g.z(); g.step(secs); d = g.xy() - p0
        print(f"{label:12s} {secs:.0f} s: moved {np.linalg.norm(d):.2f} m ({np.linalg.norm(d)/secs:.2f} m/s), yaw {math.degrees((g.yaw()-y0+math.pi)%(2*math.pi)-math.pi):+6.1f} deg, height {g.z():.2f} m{'  FELL' if g.z() < 0.5 else ''}")
    wall = time.time() - t0; print(f"sim {g.t:.0f} s in {wall:.1f} s wall = {g.t/wall:.0f}x real time")

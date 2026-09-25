"""E140: a locomotion environment for post-training the G1 walking policy on the fault the fetch bench paid for in falls,
stop-start command changes at the decision layer's cadence. Same body, scene, observation (103-d), control rate (50 Hz,
10 substeps) and action mapping (ctrl = act * 0.5 + knees_bent default) as the fetch room; no people, no task: only a
velocity command that changes every 0.5-1.5 s among stand (a true zero), slow (0.35) and normal (0.7) forward speeds with
a yaw rate, exactly the command stream the decision layer produces. Reward: Playground-style tracking of the commanded
planar velocity and yaw rate, an action-rate cost, a fall penalty; episodes end at 20 s or a fall (pelvis below 0.45 m)."""
import os, sys, math, numpy as np, mujoco
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.fetch_sim import G1_DIR, assets

CTRL_DT, N_SUB, EP_S = 0.02, 10, 20.0
SPEEDS = (0.0, 0.35, 0.7)

class G1LocoEnv:
    def __init__(self, seed=0, speeds=SPEEDS, hold_range=(0.5, 1.5), yaw_max=0.8, instant=True, stop_vx=0.0, handover_prob=0.3, perturb_delta=0.0, perturb_params=("mass", "friction", "gain")):
        self.rng = np.random.RandomState(seed); self.speeds, self.hold_range, self.yaw_max, self.instant, self.stop_vx, self.handover_prob = speeds, hold_range, yaw_max, instant, stop_vx, handover_prob
        self.arm_ids = None; self.arm_pose = {"right_shoulder_pitch_joint": -0.6, "right_elbow_joint": 0.9}   # the fetch room's hand-over hold, blended in over a second while standing
        xml = open(os.path.join(G1_DIR, "xmls", "scene_mjx_feetonly_flat_terrain.xml")).read()
        self.model = mujoco.MjModel.from_xml_string(xml, assets=assets()); self.data = mujoco.MjData(self.model); self.model.opt.timestep = 0.002
        self.perturb = None
        if perturb_delta > 0:   # E142: how wrong is the simulator allowed to be. Per episode: every body's mass and inertia, all contact friction (one draw), every actuator's position gain, each x U(1-d, 1+d)
            d = perturb_delta; f_mass = self.rng.uniform(1 - d, 1 + d, size=self.model.nbody); f_fric = float(self.rng.uniform(1 - d, 1 + d)); f_gain = self.rng.uniform(1 - d, 1 + d, size=self.model.nu)
            if "mass" in perturb_params: self.model.body_mass[:] *= f_mass; self.model.body_inertia[:] *= f_mass[:, None]
            if "friction" in perturb_params: self.model.geom_friction[:, 0] *= f_fric
            if "gain" in perturb_params: self.model.actuator_gainprm[:, 0] *= f_gain; self.model.actuator_biasprm[:, 1] *= f_gain
            mujoco.mj_setConst(self.model, self.data)   # E142b: one family at a time; the draws are made in the same order either way, so a family's draw matches E142's for the same seed
            self.perturb = {"delta": d, "friction": round(f_fric, 3), "mass_range": (round(float(f_mass.min()), 3), round(float(f_mass.max()), 3)), "gain_range": (round(float(f_gain.min()), 3), round(float(f_gain.max()), 3))}
        self.default = np.array(self.model.keyframe("knees_bent").qpos[7:7 + self.model.nu]); self.nu = self.model.nu
        self.phase_dt = 2 * math.pi * 1.5 * CTRL_DT; self.imu = self.model.site("imu_in_pelvis").id
        self.reset()
    def reset(self):
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.keyframe("knees_bent").id); self.data.qvel[:] = 0; mujoco.mj_forward(self.model, self.data)
        self.last = np.zeros(self.nu, np.float32); self.phase = np.array([0.0, math.pi]); self.cmdv = np.zeros(3, np.float32); self.t = 0.0; self.next_cmd_t = 0.0; self.fell = False
        self.log_v = []; self.handover = False; self.hold_alpha = 0.0; self._new_cmd(); return self.obs()
    def _new_cmd(self):
        vx = float(self.rng.choice(self.speeds)); wz = float(self.rng.uniform(-self.yaw_max, self.yaw_max)) if vx > 0 or self.rng.uniform() < 0.3 else 0.0
        self.target = np.array((self.stop_vx if vx == 0.0 else vx, 0.0, wz), np.float32); self.cmd_true = np.array((vx, 0.0, wz), np.float32)
        self.handover = (vx == 0.0 and self.rng.uniform() < self.handover_prob); self.hold_alpha = 0.0
        self.next_cmd_t = self.t + float(self.rng.uniform(*self.hold_range))
    def obs(self):
        d, m = self.data, self.model; R = d.site_xmat[self.imu].reshape(3, 3); grav = R.T @ np.array([0, 0, -1.0]); nq = 7 + m.nu; nv = 6 + m.nu
        return np.hstack([d.sensor("local_linvel_pelvis").data, d.sensor("gyro_pelvis").data, grav, self.cmdv, d.qpos[7:nq] - self.default, d.qvel[6:nv], self.last, np.concatenate([np.cos(self.phase), np.sin(self.phase)])]).astype(np.float32)
    def step(self, act):
        """act: 29-d in [-1, 1]. -> obs, reward, done, info"""
        if self.t >= self.next_cmd_t: self._new_cmd()
        self.cmdv[:] = self.target   # instant command changes (E108's setting): the fault under test
        act = np.clip(np.asarray(act, np.float32), -1, 1); rate = float(np.sum((act - self.last) ** 2)); self.last = act.copy()
        ctrl = act * 0.5 + self.default
        if self.handover:   # the hand-over: arm raised and held while standing, as the fetch room does it
            if self.arm_ids is None: self.arm_ids = {self.model.actuator(n).id: v for n, v in self.arm_pose.items()}
            self.hold_alpha = min(1.0, self.hold_alpha + CTRL_DT)
            for j, v in self.arm_ids.items(): ctrl[j] = (1 - self.hold_alpha) * ctrl[j] + self.hold_alpha * v
        self.data.ctrl[:] = ctrl; self.phase = np.fmod(self.phase + self.phase_dt + math.pi, 2 * math.pi) - math.pi
        for _ in range(N_SUB): mujoco.mj_step(self.model, self.data)
        self.t += CTRL_DT
        v = self.data.sensor("local_linvel_pelvis").data; wz = self.data.sensor("gyro_pelvis").data[2]
        lin_err = float((v[0] - self.cmd_true[0]) ** 2 + (v[1] - self.cmd_true[1]) ** 2); ang_err = float((wz - self.cmd_true[2]) ** 2)
        R = self.data.site_xmat[self.imu].reshape(3, 3); grav = R.T @ np.array([0, 0, -1.0]); tilt = float(grav[0] ** 2 + grav[1] ** 2)
        fell = float(self.data.qpos[2]) < 0.45
        r = 1.0 * math.exp(-lin_err / 0.25) + 0.5 * math.exp(-ang_err / 0.25) - 0.05 * rate - 1.0 * tilt - (5.0 if fell else 0.0)
        self.log_v.append((self.cmd_true[0], float(v[0]), float(math.hypot(v[0], v[1]))))
        done = fell or self.t >= EP_S - 1e-9; self.fell = self.fell or fell
        return self.obs(), r, done, {"fell": fell, "lin_err": lin_err, "t": self.t}

def evaluate(policy_act, n_episodes=100, seed=1000, **kw):
    """Fall rate, tracking error and standing creep of a policy (a callable obs -> act) on the stop-start schedule."""
    falls = 0; errs = []; creep = []; fall_t = []
    for i in range(n_episodes):
        env = G1LocoEnv(seed=seed + i, **kw); o = env.reset(); done = False
        while not done:
            o, r, done, info = env.step(policy_act(o)); errs.append(info["lin_err"])
        falls += env.fell
        if env.fell: fall_t.append(env.t)
        creep += [sp for c, vx, sp in env.log_v if c == 0.0]
    return {"episodes": n_episodes, "fall_rate": falls / n_episodes, "mean_fall_time_s": float(np.mean(fall_t)) if fall_t else None, "rmse_vx": float(math.sqrt(np.mean(errs))), "stand_speed_mean": float(np.mean(creep)) if creep else None, "stand_speed_p90": float(np.percentile(creep, 90)) if creep else None}

if __name__ == "__main__":
    import time, json
    from humanoid.g1_policy_torch import load_from_onnx
    pol = load_from_onnx(); n = int(sys.argv[1]) if len(sys.argv) > 1 else 20; t0 = time.time()
    res = evaluate(pol.act, n_episodes=n); res["wall_s"] = round(time.time() - t0, 1); print("shipped policy, stop-start schedule, true zeros:", json.dumps(res))
    t0 = time.time(); res2 = evaluate(pol.act, n_episodes=n, stop_vx=-0.2); res2["wall_s"] = round(time.time() - t0, 1); print("shipped policy, the bench's -0.2 stand workaround:", json.dumps(res2))
    res3 = evaluate(pol.act, n_episodes=n, speeds=(0.35, 0.7), hold_range=(3.0, 6.0)); print("shipped policy, plain walking (no stops, 3-6 s holds):", json.dumps(res3))

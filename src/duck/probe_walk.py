"""E93 feasibility probe: does the shipped MicroDuck walking policy run headless in CPU MuJoCo on this machine, driven
programmatically? Uses Pollen's playback code (Apache-2.0, third_party/microduck_rl/scripts/infer_policy.py) as a library:
same BAM actuator model, same 61-D observation contract, same 50 Hz control loop, no viewer."""
import os, sys, time, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RL = os.path.join(ROOT, "third_party", "microduck_rl"); POL = os.path.join(ROOT, "third_party", "microduck_policies")
sys.path.insert(0, os.path.join(RL, "scripts")); os.chdir(RL)
import mujoco, infer_policy as ip

def run(seconds=12.0, vx=0.15, quiet=True):
    bam_model = ip.load_bam_model(ip.BAM_KP_FW, 7.4, None)
    model, data, bam_ctrl, _ = ip.load_mujoco_with_bam(ip.MICRODUCK_XML, bam_model, 0.005, 0.1, ip.BAM_VIN_MIN)
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf if quiet else sys.stdout):
        pol = ip.PolicyInference(model, data, bam_ctrl=bam_ctrl, walking_onnx_path=f"{POL}/BEST_alpha_walking.onnx", standing_onnx_path=f"{POL}/BEST_alpha_stand.onnx",
                                 new_cmd_obs=True, use_projected_gravity=True)  # sit-stand and roulade loaded separately when a behaviour needs them (loading them here stalled the walk)
    dec = 4; dt = dec * model.opt.timestep; q = pol._trunk_qpos_adr; p0 = data.qpos[q:q+3].copy(); t_wall = time.time(); steps = int(seconds / dt); zmin = 1e9; log = []
    for i in range(steps):
        t = i * dt
        if abs(t - 1.0) < 1e-9: pol.set_vel_cmd(vx, 0.0, 0.0)
        if abs(t - (seconds - 2.0)) < 1e-9: pol.set_vel_cmd(0.0, 0.0, 0.0)
        with contextlib.redirect_stdout(buf):
            a = pol.infer(); pol.apply_action(a)
        for _ in range(dec):
            bam_ctrl.update(); mujoco.mj_step(model, data)
        z = float(data.qpos[q+2]); zmin = min(zmin, z)
        if i % int(1.0 / dt) == 0: log.append((round(t, 1), round(float(data.qpos[q]-p0[0]), 3), round(float(data.qpos[q+1]-p0[1]), 3), round(z, 3), pol.current_policy))
    wall = time.time() - t_wall; p1 = data.qpos[q:q+3]
    print(f"model: {model.nbody} bodies, {model.nu} actuators, dt {model.opt.timestep}, control {1/dt:.0f} Hz | obs dim {pol.get_observations().size}")
    print(f"walked {float(p1[0]-p0[0]):+.3f} m forward, {float(p1[1]-p0[1]):+.3f} m lateral in {seconds:.0f} s (cmd {vx} m/s for {seconds-3:.0f} s → expected ≈ {vx*(seconds-3):.2f} m) | trunk z min {zmin:.3f} m (start {p0[2]:.3f}) | {'UPRIGHT' if zmin > 0.6*p0[2] else 'FELL'}")
    print(f"wall time {wall:.1f} s for {seconds:.0f} s of sim = {seconds/wall:.1f}x real time | per control step {1000*wall/steps:.2f} ms")
    print("t, dx, dy, z, policy:", log)

if __name__ == "__main__": run()

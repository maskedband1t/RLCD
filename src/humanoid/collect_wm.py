"""S1-E39 — collect world-model training data with PHYSICAL rotation.

Why a separate collector, and why a different wheel: the task bench runs the SHIPPED wheel
(half-width 0.035), where the base cannot turn at all (spin ratio 0.06) and heading is therefore set
KINEMATICALLY. That is a fine declared approximation for scoring deciders -- you report it -- but it
is poison for a world model, which would learn that turning is instantaneous and free and then plan
against physics that does not exist.

So collection runs the NARROW wheel (half-width 0.005): spin ratio 0.51, fully physical, and the
robot tips when it extends its arm while moving. Tipping cost four fixes on the task bench. Here it
is exactly what we want -- random-action rollouts do not care about task success, they care about
correct dynamics, and a robot that falls over is real dynamics the model should learn.

Still approximated, and stated rather than hidden: the GRASP is a weld, so this data contains no
friction-grasp dynamics. A model trained here will not know what slipping looks like.
"""
import os, sys, time, argparse
import numpy as np
import mujoco

os.environ.setdefault("FFW_WHEEL_HALFWIDTH", "0.005")   # BEFORE the model is built
sys.path[:0] = ["src", "tools"]

from humanoid.kitchen_task import KitchenTask          # noqa: E402
from hb_kitchen import OBJECTS                          # noqa: E402

NAMES = [n for n, *_ in OBJECTS]


def rollout(seed, steps, res, out_dir, every=2):
    """One episode of correlated random actions. Correlated, not iid: a world model learns nothing
    useful from white noise that never travels anywhere. An Ornstein-Uhlenbeck-ish walk produces
    trajectories that actually cross the room, approach the counter, and knock things over."""
    r = KitchenTask(seed=seed)
    m = r.model
    m.vis.global_.offwidth, m.vis.global_.offheight = res, res
    ren = mujoco.Renderer(m, res, res)
    cam = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_CAMERA, "head")
    rng = np.random.RandomState(seed)

    obs, acts, meta = [], [], []
    a = np.zeros(3)
    for i in range(steps):
        # Correlated random walk. S1-E39: the first version used 0.85*a + 0.15*noise, whose
        # steady-state spread is ~0.08 -- the walk never left the origin, the robot pottered, and 150
        # frames contained ZERO falls and ZERO tipped objects. A world model trained on that learns a
        # world where nothing happens. k is now set so the steady-state spread actually fills the
        # action range: std = k*scale/sqrt(3)/sqrt(1-rho^2).
        a = 0.80 * a + 0.45 * rng.uniform(-1, 1, 3) * np.array([0.6, 0.45, 1.0])
        a = np.clip(a, [-0.45, -0.35, -0.9], [0.5, 0.35, 0.9])
        # Extend the arm WHILE MOVING, often. On the task bench this toppled the robot and cost four
        # fixes; here it is the point -- a robot that falls over is dynamics the model must learn.
        if rng.rand() < 0.12:
            r.home_arm(0.3) if rng.rand() < 0.5 else r.carry_pose(0.3)
        r.set_cmd(float(a[0]), float(a[2]), float(a[1]))
        r.step(0.1)
        if i % every == 0:
            ren.update_scene(r.data, cam)
            obs.append(ren.render())
            acts.append(a.copy())
            meta.append((float(r.upright()), float(r.data.qpos[2]),
                         *[float(r.obj_upright(n)) for n in NAMES]))
    out = os.path.join(out_dir, f"ep_{seed:05d}.npz")
    np.savez_compressed(out,
                        obs=np.asarray(obs, np.uint8),
                        act=np.asarray(acts, np.float32),
                        meta=np.asarray(meta, np.float32))
    return len(obs), out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=4)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--res", type=int, default=224)
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("--out", default="data/wm_kitchen")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time(); total = 0
    for k in range(a.episodes):
        n, path = rollout(a.seed0 + k, a.steps, a.res, a.out)
        total += n
        print(f"  ep {k}: {n} frames -> {os.path.basename(path)}  [{time.time()-t0:.0f}s]", flush=True)
    dt = time.time() - t0
    print(f"\n{total} transitions in {dt:.0f}s = {total/dt:.1f}/s")
    print(f"  one core:  500k in {500_000/(total/dt)/3600:.1f} h")
    print(f"  12 cores:  500k in {500_000/(total/dt)/3600/12:.1f} h")

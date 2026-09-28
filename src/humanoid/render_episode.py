"""Render an episode to GIF + MP4. Run this for anything worth looking at.

  PYTHONPATH=src USE_TF=0 DUCK_BODY=g1 python src/humanoid/render_episode.py \
      --body ffw --arm oracle --seed 41 --out figures/ffw-fetch

  --body g1  uses the legged bench (needs DUCK_CONTACT=1 etc for contact)
  --body ffw uses the wheeled ROBOTIS body
"""
import os, sys, argparse
sys.path.insert(0, "src")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", default="ffw", choices=["ffw", "g1"])
    ap.add_argument("--arm", default="oracle")
    ap.add_argument("--seed", type=int, default=41)
    ap.add_argument("--steps", type=int, default=24)
    ap.add_argument("--out", default="figures/episode")
    ap.add_argument("--width", type=int, default=960)
    a = ap.parse_args()

    import numpy as np, mujoco, imageio
    from duck import e93_run as R
    from humanoid.fetch_sim import TABLE

    if a.body == "ffw":
        import humanoid.ffw_sim as FS
        R.Room = FS.FFWRoom
    room = R.Room(a.seed)
    room.physics(int(1.0 / room.cdt))
    arm = R.make_arm(a.arm)

    m = room.model
    h = int(a.width * 9 / 16)
    m.vis.global_.offwidth, m.vis.global_.offheight = a.width, h
    ren = mujoco.Renderer(m, h, a.width)
    cam = mujoco.MjvCamera()
    frames, actions = [], []
    for _ in range(a.steps):
        f = room.facts(); opts = room.options()
        key, _j = arm.decide(f, opts, room)
        if key == "done":
            break
        for _sub in range(3):                      # a few frames per decision, so motion reads
            room.physics(int(0.17 / room.ctrl_dt))
            bx, by = float(room.data.qpos[0]), float(room.data.qpos[1])
            cam.lookat[:] = [(bx + TABLE[0]) / 2, (by + TABLE[1]) / 2, 0.7]
            cam.distance = 4.2; cam.elevation = -18
            cam.azimuth = float(np.degrees(np.arctan2(TABLE[1] - by, TABLE[0] - bx))) + 205
            ren.update_scene(room.data, cam)
            frames.append(ren.render())
        actions.append(key)
        if room.fallen():
            break
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    imageio.mimsave(a.out + ".gif", frames[::2], duration=0.09, loop=0)
    imageio.mimsave(a.out + ".mp4", frames, fps=18)
    print(f"  {len(frames)} frames · actions {actions}")
    print(f"  {a.out}.gif  {os.path.getsize(a.out + '.gif')/1e6:.1f} MB")
    print(f"  {a.out}.mp4  {os.path.getsize(a.out + '.mp4')/1e6:.2f} MB")


if __name__ == "__main__":
    main()

"""Offscreen renders of the cell for figures: a contact sheet of one episode."""
import sys, os, numpy as np, mujoco
from PIL import Image
from .harness import episode

def contact_sheet(seed, arm, out, every_s=3.0, cols=4, width=480, height=320, azimuth=150, elevation=-32, distance=1.9, replay=None):
    frames = []; last = {"t": -1e9}
    renderer = {"r": None, "cam": None}
    def on_step(world, st, skill, ctrl):
        if renderer["r"] is None:
            renderer["r"] = mujoco.Renderer(world.model, height=height, width=width)
            cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam.lookat[:] = [0.0, 0.0, 0.05]; cam.distance = distance; cam.azimuth = azimuth; cam.elevation = elevation
            renderer["cam"] = cam
        if world.t - last["t"] >= every_s:
            last["t"] = world.t
            renderer["r"].update_scene(world.data, camera=renderer["cam"])
            img = renderer["r"].render().copy()
            label = f"t={world.t:4.1f}s  {skill.name if skill else ''}  hand={'YES' if ctrl['hand_seen'] else 'no'}  held={world.held}"
            frames.append((img, label))
    pkw = {"replay": replay, "record": []} if arm.startswith("jev") else {}
    from .policies import make_policy
    pol = make_policy(arm, **pkw) if arm.startswith("jev") else None
    r = episode(seed, arm, policy=pol, on_step=on_step)
    if renderer["r"] is not None: renderer["r"].close()
    from PIL import ImageDraw
    n = len(frames); rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * height), (20, 20, 20))
    for i, (img, label) in enumerate(frames):
        im = Image.fromarray(img); d = ImageDraw.Draw(im); d.rectangle([0, 0, width, 16], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 255, 255))
        sheet.paste(im, ((i % cols) * width, (i // cols) * height))
    sheet.save(out); return r, out

if __name__ == "__main__":
    seed = int(sys.argv[1]); arm = sys.argv[2]; out = sys.argv[3]
    r, p = contact_sheet(seed, arm, out)
    print("saved", p, "| correct", r["parts_correct"], "viol", r["violations"], "| log:", [(e[0], e[1]) for e in r["log"]])

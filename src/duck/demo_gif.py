"""Demo clip for the MicroDuck room: one seed, several arms side by side, frames every 0.2 s of sim time, a label bar with the
decision, the judge's confidence and the person's distance. Usage: PYTHONPATH=src python src/duck/demo_gif.py --seed 2 --arms rules jev --out figures/demo-duck-seed2.gif"""
import os, sys, argparse, subprocess, shutil, tempfile, contextlib
import numpy as np, mujoco
from PIL import Image, ImageDraw
sys.path.insert(0, "src")
import duck.e93_run as R
from duck.e93_sim import Room, GOAL

class FilmedRoom(Room):
    def __init__(self, seed, outdir, fps=5, width=560, height=340, **kw):
        super().__init__(seed, **kw); self.outdir = outdir; self.fps = fps; self.w = width; self.h = height; self.next_t = 0.0; self.i = 0; self.label = ("", None); self.renderer = None
        os.makedirs(outdir, exist_ok=True)
    def physics(self, n_ctrl):
        for _ in range(n_ctrl):
            super().physics(1)
            if self.t >= self.next_t:
                self.next_t += 1.0 / self.fps
                if self.renderer is None:
                    self.renderer = mujoco.Renderer(self.model, height=self.h, width=self.w); cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                    cam.lookat[:] = [0.75, 0.0, 0.1]; cam.distance = 4.2; cam.azimuth = 120; cam.elevation = -32; self.cam = cam  # wide enough to keep the person in frame
                self.renderer.update_scene(self.data, camera=self.cam); img = Image.fromarray(self.renderer.render().copy()); d = ImageDraw.Draw(img)
                d.rectangle([0, 0, self.w, 34], fill=(12, 14, 18)); key, conf = self.label
                d.text((6, 3), self.title, fill=(235, 235, 235)); d.text((6, 19), f"t={self.t:5.1f}s  {key:<14}{'' if conf is None else f'conf {conf:.2f}  '}person {self.person_dist():.2f} m  goal {self.goal_dist():.2f} m", fill=(200, 205, 215))
                img.save(os.path.join(self.outdir, f"f{self.i:05d}.png")); self.i += 1

def film(seed, arm_name, outdir, fps):
    title = None
    if "@" in arm_name:   # laya@results/duck/head_r6#the corrected copy : an owned head from a named checkpoint, with a panel title
        arm_name, rest = arm_name.split("@", 1); ckpt, _, title = rest.partition("#"); os.environ["DUCK_HEAD"] = ckpt
    room = FilmedRoom(seed, outdir, fps=fps); room.title = title or {"rules": "frozen rules", "jev": "RLCD judge (Jev) + governor"}.get(arm_name.split("_")[0], arm_name)
    if title is None and arm_name != "rules" and not arm_name.startswith("oracle"): room.title = f"RLCD judge ({arm_name}) + governor"
    arm = R.make_arm(arm_name); room.physics(int(1.0 / room.cdt)); pending = None
    while room.t < float(os.environ.get("DUCK_FILM_S", "45")) and not room.fell:
        f = room.facts(); opts = room.options(); acc = room.acceptable()
        if pending: key, j = pending, {}; pending = None
        else:
            key, j = arm.decide(f, opts, room)
            if key.startswith("confirm:"):
                prop = key[8:]; room.label = ("confirm " + prop, j.get("confidence")); room.run_skill("confirm_wait"); key = prop if prop in acc else R.Oracle().decide(f, opts, room)[0]
            elif key not in opts: key = "stop"
        room.label = (key, j.get("confidence")); room.recent.append(f"t={room.t:.0f}s: {key}"); room.cmd = (0.12 if key == "walk_fast" else 0.06 if key == "walk_slow" else 0.0, 0.0)
        if key == "ask_operator": room.run_skill("ask_operator"); pending = R.Oracle().decide(room.facts(), room.options(), room)[0]; continue
        if key == "done": break
        room.run_skill(key)
    if room.renderer: room.renderer.close()
    return room.i

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=2); ap.add_argument("--arms", nargs="+", default=["rules", "jev"]); ap.add_argument("--out", default="figures/demo-duck.gif"); ap.add_argument("--fps", type=int, default=5); a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="duckdemo_"); dirs = []
    for arm in a.arms:
        d = os.path.join(tmp, arm.replace(".", "_")); n = film(a.seed, arm, d, a.fps); dirs.append((arm, d, n)); print(f"{arm}: {n} frames")
    nmax = max(n for _, _, n in dirs)
    for _, d, n in dirs:
        for i in range(n, nmax): shutil.copy(os.path.join(d, f"f{n-1:05d}.png"), os.path.join(d, f"f{i:05d}.png"))
    inputs = sum([["-framerate", str(a.fps), "-i", os.path.join(d, "f%05d.png")] for _, d, _ in dirs], []); k = len(dirs)
    stack = "".join(f"[{i}:v]" for i in range(k)) + f"hstack=inputs={k}[v];" if k > 1 else "[0:v]null[v];"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", stack + "[v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer", a.out], check=True)
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", stack[:-1] if k > 1 else "[0:v]null", "-map", "[v]", "-pix_fmt", "yuv420p", os.path.splitext(a.out)[0] + ".mp4"], check=True)
    print("saved", a.out, f"({os.path.getsize(a.out)//1024} KB)"); shutil.rmtree(tmp); sys.stdout.flush(); os._exit(0)  # skip interpreter teardown: MuJoCo renderer + onnxruntime threads abort on exit

if __name__ == "__main__": main()

"""Demo clip for the humanoid fetch room: one seed, several arms side by side, frames every 0.2 s of sim time, a label bar with
the decision, the judge's confidence, the requester's distance and attention, and what the robot holds. The harness's own
episode loop runs unchanged (the filmed room is injected into duck.e93_run), so the clip is the run, not a re-enactment.
Usage: USE_TF=0 PYTHONPATH=src DUCK_BODY=g1 python src/humanoid/demo_gif.py --seed 42 --arms rules rules_hindsight jev --out figures/demo-g1-seed42-phone.gif"""
import os, sys, argparse, subprocess, shutil, tempfile
import numpy as np, mujoco
from PIL import Image, ImageDraw
sys.path.insert(0, "src"); os.environ["DUCK_BODY"] = "g1"
import duck.e93_run as R
from humanoid import fetch_sim as F

LABEL = {"key": "", "conf": None}
TITLES = {"rules": "frozen rules", "rules_hindsight": "rules rewritten with hindsight", "rules_mined": "rules + the judge's drafted clauses", "jev": "RLCD judge (Jev) + governor", "jev_confirm0.5": "RLCD judge + one-second veto window", "oracle": "oracle (code that knows the truth)"}

class FilmedRoom(F.Room):
    def __init__(self, seed, outdir, fps=5, width=560, height=340, title=""):
        super().__init__(seed); self.outdir = outdir; self.fps = fps; self.w = width; self.h = height; self.next_t = 0.0; self.i = 0; self.title = title; self.renderer = None
        self.film_s = float(os.environ.get("DUCK_FILM_S", "75")); os.makedirs(outdir, exist_ok=True)
    def physics(self, n_ctrl):
        for _ in range(n_ctrl):
            super().physics(1)
            if self.t >= self.next_t and self.t <= self.film_s:
                self.next_t += 1.0 / self.fps
                if self.renderer is None:
                    self.renderer = mujoco.Renderer(self.model, height=self.h, width=self.w); cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
                    cam.lookat[:] = [4.6, -0.2, 0.7]; cam.distance = 6.8; cam.azimuth = 150; cam.elevation = -20; self.cam = cam   # the whole room: table, doorway, requester
                self.renderer.update_scene(self.data, camera=self.cam); img = Image.fromarray(self.renderer.render().copy()); d = ImageDraw.Draw(img)
                d.rectangle([0, 0, self.w, 34], fill=(12, 14, 18)); key, conf = LABEL["key"], LABEL["conf"]
                d.text((6, 3), self.title, fill=(235, 235, 235))
                d.text((6, 19), f"t={self.t:5.1f}s  {key:<14}{'' if conf is None else f'conf {conf:.2f}  '}{self.req.name} {self.goal_dist():.1f} m, {str(self.req.attention).replace('_', ' ')}  holds {self.holding or 'nothing'}", fill=(200, 220, 255))
                img.save(os.path.join(self.outdir, f"f{self.i:05d}.png")); self.i += 1

def film(seed, arm_name, outdir, fps):
    title = TITLES.get(arm_name, arm_name)
    if "@" in arm_name:   # laya@results/duck/head_g1_r0#the owned copy : a head from a named checkpoint, with a panel title
        arm_name, rest = arm_name.split("@", 1); ckpt, _, t2 = rest.partition("#"); os.environ["DUCK_HEAD"] = ckpt; title = t2 or title
    R.Room = lambda s: FilmedRoom(s, outdir, fps=fps, title=title)
    base = R.make_arm
    def wrapped(name):
        arm = base(name)
        if name == arm_name:
            dec = arm.decide
            def decide(f, opts, room):
                key, j = dec(f, opts, room); LABEL["key"] = key; LABEL["conf"] = j.get("confidence"); return key, j
            arm.decide = decide
        return arm
    R.make_arm = wrapped; LABEL["key"] = ""; LABEL["conf"] = None
    out = R.episode(seed, arm_name, verbose=True); R.make_arm = base
    n = len([f for f in os.listdir(outdir) if f.endswith(".png")]); return n, out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=42); ap.add_argument("--arms", nargs="+", default=["rules", "jev"]); ap.add_argument("--out", default="figures/demo-g1.gif"); ap.add_argument("--fps", type=int, default=5); a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="g1demo_"); dirs = []
    for arm in a.arms:
        d = os.path.join(tmp, arm.replace(".", "_").replace("/", "_")); n, out = film(a.seed, arm, d, a.fps); dirs.append((arm, d, n)); print(f"{arm}: {n} frames, event {out['event']}, handled {out['event_correct']}, delivered to {out['delivered_to']}, wrong hand-overs {out['wrong_handovers']}, fell {out['fell']}"); sys.stdout.flush()
    nmax = max(n for _, _, n in dirs)
    for _, d, n in dirs:
        for i in range(n, nmax): shutil.copy(os.path.join(d, f"f{n-1:05d}.png"), os.path.join(d, f"f{i:05d}.png"))
    inputs = sum([["-framerate", str(a.fps), "-i", os.path.join(d, "f%05d.png")] for _, d, _ in dirs], []); k = len(dirs)
    stack = "".join(f"[{i}:v]" for i in range(k)) + f"hstack=inputs={k}[v];" if k > 1 else "[0:v]null[v];"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", stack + "[v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer", a.out], check=True)
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", stack[:-1] if k > 1 else "[0:v]null", "-map", "[v]", "-pix_fmt", "yuv420p", os.path.splitext(a.out)[0] + ".mp4"], check=True)
    print("saved", a.out, f"({os.path.getsize(a.out)//1024} KB)"); shutil.rmtree(tmp); sys.stdout.flush(); os._exit(0)

if __name__ == "__main__": main()

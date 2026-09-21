"""Demo clip: one seed, several arms side by side, 5 fps, with a label bar (time, action, hand, held part, confidence).
Usage: PYTHONPATH=src python src/cell/demo_gif.py --seed 40 --arms rules laya_v2 --out figures/demo-seed40.gif
Append "+gov" to an arm to turn the governor's set-down rule on for that panel only; CELL_LAYA_CKPT picks the owned head."""
import os, sys, argparse, subprocess, shutil, tempfile
import numpy as np, mujoco
from PIL import Image, ImageDraw
sys.path.insert(0, "src")
import cell.harness as H
from cell.harness import episode
from cell.policies import make_policy

def record(seed, arm_spec, outdir, fps=5, width=480, height=320, bank="notes"):
    gov = arm_spec.endswith("+gov"); arm = arm_spec[:-4] if gov else arm_spec; H.GOV_SETDOWN = gov  # per-panel governor rule: "laya_v2+gov"
    os.makedirs(outdir, exist_ok=True); renderer = {"r": None, "cam": None}; last = {"t": -1e9, "i": 0, "conf": None, "key": ""}
    def on_step(world, st, skill, ctrl):
        if renderer["r"] is None:
            renderer["r"] = mujoco.Renderer(world.model, height=height, width=width); cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
            cam.lookat[:] = [0.0, 0.0, 0.05]; cam.distance = 1.9; cam.azimuth = 150; cam.elevation = -32; renderer["cam"] = cam
        if st["log"]: e = st["log"][-1]; last["key"] = e[1]; last["conf"] = e[4] if len(e) > 4 else None
        if world.t - last["t"] >= 1.0 / fps:
            last["t"] = world.t; renderer["r"].update_scene(world.data, camera=renderer["cam"]); img = Image.fromarray(renderer["r"].render().copy()); d = ImageDraw.Draw(img)
            d.rectangle([0, 0, width, 34], fill=(12, 14, 18)); conf = f"  conf {last['conf']:.2f}" if isinstance(last["conf"], float) else ""
            d.text((6, 3), f"{'owned head (Laya 421M, on-device)' if arm.startswith('laya') else arm}{'  + governor set-down rule' if gov else ''}", fill=(235, 235, 235))
            d.text((6, 19), f"t={world.t:5.1f}s  {last['key'][:34]}{conf}  hand={'YES' if ctrl['hand_seen'] else 'no'}  held={world.held or '-'}", fill=(200, 205, 215))
            img.save(os.path.join(outdir, f"f{last['i']:05d}.png")); last["i"] += 1
    pol = make_policy(arm, record=[]) if (arm.startswith("jev") or arm.startswith("laya") or arm.startswith("sj")) else None
    r = episode(seed, arm, policy=pol, on_step=on_step, bank=bank)
    if renderer["r"] is not None: renderer["r"].close()
    return r, last["i"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=40); ap.add_argument("--arms", nargs="+", default=["rules", "laya_v2"]); ap.add_argument("--out", default="figures/demo.gif"); ap.add_argument("--fps", type=int, default=5); ap.add_argument("--bank", default="notes"); a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="demo_"); dirs = []
    for arm in a.arms:
        d = os.path.join(tmp, arm.replace(".", "_").replace("+", "_")); r, n = record(a.seed, arm, d, fps=a.fps, bank=a.bank); dirs.append((arm, d, n))
        print(f"{arm}: {n} frames | parts correct {r['parts_correct']}/{r['n_parts']} | violations {r['violations']} | broken {r['broken']} | log {[(e[0], e[1]) for e in r['log']][:12]}")
    nmax = max(n for _, _, n in dirs)
    for _, d, n in dirs:  # pad shorter clips with their last frame so the panels stay aligned
        lastf = os.path.join(d, f"f{n-1:05d}.png")
        for i in range(n, nmax): shutil.copy(lastf, os.path.join(d, f"f{i:05d}.png"))
    inputs = sum([["-framerate", str(a.fps), "-i", os.path.join(d, "f%05d.png")] for _, d, _ in dirs], [])
    filt = "".join(f"[{i}:v]" for i in range(len(dirs))) + f"hstack=inputs={len(dirs)}[v];[v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer" if len(dirs) > 1 else "[0:v]split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", filt, a.out], check=True)
    mp4 = os.path.splitext(a.out)[0] + ".mp4"
    subprocess.run(["/opt/homebrew/bin/ffmpeg", "-y", "-loglevel", "error"] + inputs + ["-filter_complex", "".join(f"[{i}:v]" for i in range(len(dirs))) + f"hstack=inputs={len(dirs)}" if len(dirs) > 1 else "null", "-pix_fmt", "yuv420p", mp4], check=True)
    print("saved", a.out, "and", mp4, f"({os.path.getsize(a.out)//1024} KB gif)"); shutil.rmtree(tmp)

if __name__ == "__main__": main()

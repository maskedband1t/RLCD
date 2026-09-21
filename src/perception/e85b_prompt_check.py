"""E85b (post hoc, exploratory; declared after E85's result): does ANY phrasing make the SAM 3 LiteText-S0
instrument find the gripper that "robot gripper"/"gripper finger" missed in 96/96 frames? Positive controls
("bowl", "cup", "hand") test the vision side; the gripper phrasings test the distilled text encoder's vocabulary.
12 release frames (every fourth tile), same threshold as E85 (0.3). Not a pre-registered test; it decides only
whether E85's failure is the instrument's vocabulary or the view."""
import json, os, sys, time, glob, argparse
import numpy as np, torch
from PIL import Image

PROMPTS = ["robot gripper", "black claw", "robot arm", "robot hand", "mechanical claw", "tongs", "black plastic",
           "bowl", "cup", "hand"] + (["gripper", "robotic gripper", "end effector", "black robotic claw", "robot"] if os.environ.get("E85D") else [])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="vil-uob/sam3-litetext-s0"); ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu")
    a = ap.parse_args()
    from transformers import AutoModel, AutoProcessor
    t0 = time.time()
    if a.model.startswith("facebook/sam3"):
        from transformers import Sam3Model, Sam3Processor   # the repo's Auto classes resolve to the video model (no text prompt)
        model = Sam3Model.from_pretrained(a.model, dtype=torch.float32).to(a.device).eval(); proc = Sam3Processor.from_pretrained(a.model)
    else:
        model = AutoModel.from_pretrained(a.model, dtype=torch.float32).to(a.device).eval(); proc = AutoProcessor.from_pretrained(a.model)
    print(f"loaded {a.model} in {time.time()-t0:.0f}s on {a.device}", flush=True)
    files = sorted(glob.glob(os.path.join(a.frames, "t*_rel.jpg")))[::4]
    out = {}
    for k, f in enumerate(files):
        img = Image.open(f).convert("RGB"); W, H = img.size; rec = {"W": W, "H": H, "prompts": {}}; t1 = time.time()
        for p in PROMPTS:
            inputs = proc(images=img, text=p, return_tensors="pt").to(a.device)
            with torch.no_grad(): o = model(**inputs)
            res = proc.post_process_instance_segmentation(o, threshold=0.3, mask_threshold=0.5, target_sizes=inputs.get("original_sizes").tolist())[0]
            inst = []
            for m, b, sc in zip(res["masks"], res["boxes"], res["scores"]):
                m = m.cpu().numpy().astype(bool); ys, xs = np.nonzero(m)
                if len(xs) == 0: continue
                inst.append({"score": float(sc), "box": [float(x) for x in b.tolist()], "area": int(m.sum()), "cy_frac": float(ys.mean() / H)})
            rec["prompts"][p] = sorted(inst, key=lambda d: -d["score"])
        rec["secs"] = round(time.time() - t1, 2); out[os.path.basename(f)] = rec
        print(f"{k+1}/{len(files)} {os.path.basename(f)} {rec['secs']}s " + " ".join(f"{p}:{len(rec['prompts'][p])}" for p in PROMPTS), flush=True)
        json.dump(out, open(a.out, "w"))
    print("\nprompt            frames>=1  n_det  n_score>=.5  frac_in_bottom_45%(gripper region)")
    for p in PROMPTS:
        dets = [d for r in out.values() for d in r["prompts"][p]]
        nf = sum(1 for r in out.values() if r["prompts"][p])
        bottom = np.mean([d["cy_frac"] >= 0.55 for d in dets]) if dets else float("nan")
        print(f"{p:16s} {nf:2d}/{len(out)}     {len(dets):3d}    {sum(1 for d in dets if d['score']>=.5):3d}        {bottom:.2f}")
    print("E85B_DONE", flush=True)

if __name__ == "__main__": main()

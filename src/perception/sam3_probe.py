"""E85 (C1''): text-promptable segmentation (SAM 3) + code-computed facts on the E64 wrist frames.
Prompts and features are fixed in the notebook pre-registration. Evaluation is threshold-free (AUROC) with
leave-one-tile-out accuracy. No task text or episode metadata reaches the model."""
import json, os, sys, time, glob, argparse
import numpy as np, torch
from PIL import Image

PROMPTS = ["robot gripper", "gripper finger", "small object", "table", "floor"]

def auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]; neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg: return float("nan")
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))

def loo_accuracy(scores, labels):
    """Best-threshold accuracy with leave-one-out threshold selection."""
    s = np.asarray(scores, float); y = np.asarray(labels, bool); n = len(s); correct = 0
    for i in range(n):
        tr = np.delete(np.arange(n), i); cands = np.unique(s[tr]); best = (-1, 0.0, True)
        for c in cands:
            for direction in (True, False):
                pred = (s[tr] >= c) if direction else (s[tr] < c); acc = (pred == y[tr]).mean()
                if acc > best[0]: best = (acc, c, direction)
        pred_i = (s[i] >= best[1]) if best[2] else (s[i] < best[1]); correct += (pred_i == y[i])
    return correct / n

def run(model_id, frames_dir, out_json, device, gripper_phrase="robot gripper"):
    from transformers import AutoModel, AutoProcessor
    t0 = time.time()
    if model_id.startswith("facebook/sam3"):
        # the official repo's Auto* classes resolve to the VIDEO model/processor, whose __call__ takes no text prompt;
        # image-level promptable concept segmentation needs the image classes explicitly (transformers sam3 docs)
        from transformers import Sam3Model, Sam3Processor
        model = Sam3Model.from_pretrained(model_id, dtype=torch.float32).to(device).eval(); proc = Sam3Processor.from_pretrained(model_id)
    else:
        model = AutoModel.from_pretrained(model_id, dtype=torch.float32).to(device).eval(); proc = AutoProcessor.from_pretrained(model_id)
    print(f"loaded {model_id} in {time.time()-t0:.0f}s on {device}", flush=True)
    files = sorted(glob.glob(os.path.join(frames_dir, "t*_rel.jpg"))) + sorted(glob.glob(os.path.join(frames_dir, "t*_p1s.jpg")))
    out = {}
    for k, f in enumerate(files):
        img = Image.open(f).convert("RGB"); W, H = img.size; rec = {"W": W, "H": H, "prompts": {}}
        t1 = time.time()
        for p in PROMPTS:
            inputs = proc(images=img, text=(gripper_phrase if p == "robot gripper" else p), return_tensors="pt").to(device)  # role key stays "robot gripper" (E85c)
            with torch.no_grad(): o = model(**inputs)
            res = proc.post_process_instance_segmentation(o, threshold=0.3, mask_threshold=0.5, target_sizes=inputs.get("original_sizes").tolist())[0]
            inst = []
            for m, b, sc in zip(res["masks"], res["boxes"], res["scores"]):
                m = m.cpu().numpy().astype(bool); ys, xs = np.nonzero(m)
                if len(xs) == 0: continue
                inst.append({"score": float(sc), "box": [float(x) for x in b.tolist()], "area": int(m.sum()), "cx": float(xs.mean()), "cy": float(ys.mean()),
                             "ymax": int(ys.max()), "touches_bottom": bool(ys.max() >= H - 2)})
            rec["prompts"][p] = sorted(inst, key=lambda d: -d["score"])
        rec["secs"] = round(time.time() - t1, 2); out[os.path.basename(f)] = rec
        print(f"{k+1}/{len(files)} {os.path.basename(f)} {rec['secs']}s " + " ".join(f"{p}:{len(rec['prompts'][p])}" for p in PROMPTS), flush=True)
        json.dump(out, open(out_json, "w"))
    return out

def features(rec):
    P = rec["prompts"]; W, H = rec["W"], rec["H"]; f = {}
    gmin = float(os.environ.get("E85_GRIP_MIN", "0.5"))  # E85/E85c pre-registered .5; E85c post hoc re-evaluation at .3 sets the env var
    grip = [d for d in P["robot gripper"] if d["score"] >= gmin]; fingers = [d for d in P["gripper finger"] if d["score"] >= gmin]
    objs = [d for d in P["small object"] if d["score"] >= 0.5]
    f["gripper_detected"] = bool(grip or fingers); f["n_fingers"] = len(fingers)
    gbox = grip[0]["box"] if grip else (None)
    if gbox is None and len(fingers) >= 1:
        xs = [d["box"] for d in fingers]; gbox = [min(b[0] for b in xs), min(b[1] for b in xs), max(b[2] for b in xs), max(b[3] for b in xs)]
    gw = (gbox[2] - gbox[0]) if gbox else W
    if len(fingers) >= 2: f["jaw_gap"] = abs(fingers[0]["cx"] - fingers[1]["cx"]) / max(gw, 1)
    else: f["jaw_gap"] = float("nan")
    f["object_present"] = bool(objs)
    if objs and gbox:
        o = objs[0]; inside = (gbox[0] <= o["cx"] <= gbox[2]) and (gbox[1] <= o["cy"] <= gbox[3])
        f["object_in_gripper_box"] = float(inside); f["object_below_gripper"] = (o["cy"] - gbox[3]) / H; f["object_touches_bottom"] = float(o["touches_bottom"]); f["object_area_frac"] = o["area"] / (W * H)
    else:
        f["object_in_gripper_box"] = 0.0; f["object_below_gripper"] = float("nan"); f["object_touches_bottom"] = float(bool(objs) and objs[0]["touches_bottom"]); f["object_area_frac"] = objs[0]["area"] / (W * H) if objs else 0.0
    tables = [d for d in P["table"] if d["score"] >= 0.5]; f["table_detected"] = bool(tables)
    return f

def evaluate(out_json, mapping_json):
    out = json.load(open(out_json)); mapping = {m["tile"]: m["label"] for m in json.load(open(mapping_json))}
    F = {k: features(v) for k, v in out.items()}
    rel = [k for k in F if k.endswith("_rel.jpg")]; p1s = [k for k in F if k.endswith("_p1s.jpg")]
    print(f"\nframes {len(F)}; gripper detected {100*np.mean([F[k]['gripper_detected'] for k in F]):.0f}%; object detected in rel frames {100*np.mean([F[k]['object_present'] for k in rel]):.0f}%, in +1s frames {100*np.mean([F[k]['object_present'] for k in p1s]):.0f}%; mean secs/frame {np.mean([v['secs'] for v in out.values()]):.1f}")
    # P85.2 open (p1s) vs closed (rel) by jaw gap
    keys = [k for k in F if not np.isnan(F[k]["jaw_gap"])]; lab = [k.endswith("_p1s.jpg") for k in keys]; sc = [F[k]["jaw_gap"] for k in keys]
    if keys: print(f"open vs closed (n={len(keys)} frames with 2 fingers): AUROC(jaw gap) {auroc(sc, lab):.3f}; LOO accuracy {100*loo_accuracy(sc, lab):.0f}%")
    # P85.3 place vs drop on +1s frames
    tiles = sorted({int(k[1:3]) for k in p1s}); y = [mapping[t] == "drop" for t in tiles]
    for feat in ("object_present", "object_in_gripper_box", "object_below_gripper", "object_touches_bottom", "object_area_frac", "table_detected"):
        s = [float(F[f"t{t:02d}_p1s.jpg"][feat]) if not (isinstance(F[f"t{t:02d}_p1s.jpg"][feat], float) and np.isnan(F[f"t{t:02d}_p1s.jpg"][feat])) else 0.0 for t in tiles]
        print(f"place vs drop (+1 s), feature {feat:<24}: AUROC(→drop) {auroc(s, y):.3f}  LOO acc {100*loo_accuracy(s, y):.0f}%")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="facebook/sam3"); ap.add_argument("--frames", required=True); ap.add_argument("--mapping", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--gripper-phrase", default="robot gripper"); ap.add_argument("--device", default="mps" if torch.backends.mps.is_available() else "cpu"); ap.add_argument("--eval-only", action="store_true")
    a = ap.parse_args()
    if not a.eval_only: run(a.model, a.frames, a.out, a.device, a.gripper_phrase)
    evaluate(a.out, a.mapping)

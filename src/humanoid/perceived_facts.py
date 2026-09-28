"""S1-E28 — facts derived from the robot's own camera instead of handed to it.

The handed-over facts take 55 distinct values across 14,064 decisions (S1-E26), which is why a
49-entry dictionary beat an 8B model on this bench. This produces the SAME KIND of categorical
fact vector -- counts and coarse bands, nothing continuous -- but from SAM 3 run on the head
camera, so the comparison isolates one variable: where the facts come from.
"""
import numpy as np

PROMPTS = ("refrigerator", "sink", "stool", "microwave", "cabinet", "trash bin")


def _count_band(n):
    return "0" if n == 0 else "1" if n == 1 else "2" if n == 2 else "3+"


def _size_band(frac):
    # fraction of the frame the largest instance covers -- the camera's proxy for "how close"
    if frac <= 0:      return "absent"
    if frac < 0.005:   return "far"
    if frac < 0.02:    return "mid"
    if frac < 0.08:    return "near"
    return "filling_view"


def _side(cx, w):
    r = cx / max(w, 1)
    return "left" if r < 0.36 else "right" if r > 0.64 else "ahead"


def perceive(img, proc, model, device="mps", prompts=PROMPTS, threshold=0.45):
    """PIL image -> categorical fact dict, the shape the decision layer already consumes."""
    import torch
    H, W = img.size[1], img.size[0]
    out = {}
    for p in prompts:
        inp = proc(images=img, text=p, return_tensors="pt").to(device)
        with torch.no_grad():
            res = model(**inp)
        r = proc.post_process_instance_segmentation(
            res, threshold=threshold, mask_threshold=0.5, target_sizes=[(H, W)])[0]
        masks = r["masks"]
        n = len(masks)
        out[f"{p}.count"] = _count_band(n)
        if n == 0:
            out[f"{p}.size"] = _size_band(0); out[f"{p}.side"] = "absent"; continue
        areas = []
        for mk in masks:
            mm = mk.cpu().numpy()
            if mm.ndim == 3: mm = mm[0]
            areas.append((mm > 0.5))
        big = max(areas, key=lambda a: a.sum())
        frac = float(big.sum()) / float(H * W)
        ys, xs = np.nonzero(big)
        out[f"{p}.size"] = _size_band(frac)
        out[f"{p}.side"] = _side(float(xs.mean()) if xs.size else W / 2, W)
    return out


def state_key(facts):
    return tuple(sorted(f"{k}={v}" for k, v in facts.items()))

"""E87 · RelateAnything on the real E64 wrist frames, with regions from SAM 3 LiteText (E85c's "robot arm"
box for the gripper role, "small object" boxes for candidate objects). Pre-registered in the notebook before
the run; depends on E85c having produced a gripper box in most frames.

Per frame: regions = best gripper-role box (score >= .3) + up to 8 "small object" boxes (score >= .5, best
first). One RelateAnything pass (<= 9 boxes, 72 ordered pairs, inside the 128-pair budget). Frame features:
  hold_max   = max over objects of max(holding, gripping, carrying)(gripper -> object)
  heldby_max = max over objects of "held by"(object -> gripper)
  below_max  = max over objects of "below"(object -> gripper)      (object under the open jaws at +1 s)
  touch_max  = max over objects of "touching"(gripper -> object)
Questions: (1) release frame vs +1 s frame of the same tile (object in the jaws vs jaws open by construction):
AUROC of hold_max, paired by tile; (2) place vs drop on the +1 s frames (HIDDEN_mapping), for each feature."""
import sys, os, json, argparse, glob
import numpy as np
from PIL import Image
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, REPO)
from src.perception.e86_relations import Head, auroc
from src.perception.sam3_probe import loo_accuracy

VOCAB = ["holding", "gripping", "carrying", "held by", "below", "touching", "near", "above", "inside", "on"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sam", required=True, help="E85c results json"); ap.add_argument("--frames", required=True)
    ap.add_argument("--mapping", required=True); ap.add_argument("--out", required=True); ap.add_argument("--eval-only", action="store_true")
    a = ap.parse_args()
    if not a.eval_only:
        head = Head(vocab=VOCAB); sam = json.load(open(a.sam)); out = {}
        for name, rec in sam.items():
            grip = [d for d in rec["prompts"].get("robot gripper", []) if d["score"] >= 0.3]
            objs = [d for d in rec["prompts"].get("small object", []) if d["score"] >= 0.5][:8]
            fr = {"gripper": bool(grip), "n_obj": len(objs), "feat": None}
            if grip and objs:
                img = np.array(Image.open(os.path.join(a.frames, name)).convert("RGB"))
                names = ["gripper"] + [f"o{i}" for i in range(len(objs))]
                boxes = np.array([grip[0]["box"]] + [d["box"] for d in objs], np.float32)
                res = head(img, boxes)
                sig = lambda pl, pr: 1.0 / (1.0 + np.exp(-(head.a * (np.asarray(pl) + pr) + head.b)))
                V = {v: i for i, v in enumerate(head.vocab)}
                hold, heldby, below, touch = [], [], [], []
                for j in range(1, len(names)):
                    if (0, j) in res:
                        p = sig(*res[(0, j)]); hold.append(max(p[V["holding"]], p[V["gripping"]], p[V["carrying"]])); touch.append(p[V["touching"]])
                    if (j, 0) in res:
                        p = sig(*res[(j, 0)]); heldby.append(p[V["held by"]]); below.append(p[V["below"]])
                fr["feat"] = {"hold_max": max(hold) if hold else 0.0, "heldby_max": max(heldby) if heldby else 0.0,
                              "below_max": max(below) if below else 0.0, "touch_max": max(touch) if touch else 0.0, "pairs_scored": len(res)}
            out[name] = fr
        json.dump(out, open(a.out, "w"), indent=1)
    out = json.load(open(a.out)); mapping = json.load(open(a.mapping))
    n = len(out); ng = sum(1 for f in out.values() if f["gripper"]); nf = sum(1 for f in out.values() if f["feat"])
    print(f"frames {n} | gripper box {ng} | gripper+object {nf}")
    tiles = sorted({k.split("_")[0] for k in out})
    # Q1: release vs +1 s, paired by tile, hold_max
    s, y = [], []
    for t in tiles:
        r, p = out.get(f"{t}_rel.jpg"), out.get(f"{t}_p1s.jpg")
        if r and p and r["feat"] and p["feat"]:
            s += [r["feat"]["hold_max"], p["feat"]["hold_max"]]; y += [1, 0]
    print(f"Q1 release(held) vs +1s(open): tiles with both frames scored {len(s)//2} | hold_max AUROC {auroc(s, y):.3f} | LOO acc {loo_accuracy(np.array(s), np.array(y)):.0%}")
    # Q2: place vs drop on +1 s frames
    lab = {f"t{m['tile']:02d}": (1 if m["label"] == "drop" else 0) for m in mapping}
    for feat in ["hold_max", "heldby_max", "below_max", "touch_max"]:
        s, y = [], []
        for t in tiles:
            p = out.get(f"{t}_p1s.jpg")
            if p and p["feat"] and t in lab: s.append(p["feat"][feat]); y.append(lab[t])
        if len(set(y)) == 2: print(f"Q2 place vs drop (+1 s), {feat:10s}: n {len(y)} | AUROC(→drop) {auroc(s, y):.3f} | LOO acc {loo_accuracy(np.array(s), np.array(y)):.0%}")
    print("E87_DONE", flush=True)

if __name__ == "__main__": main()

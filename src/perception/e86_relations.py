"""E86 (C1''') · RelateAnything relation scores on the sorting cell, ground-truth regions.

Question: does an open-vocabulary relation model (RelateAnything, relsgg-vits16plus, 53 M params, boxes in,
calibrated relation scores out, no class labels) recover the relational facts our eye writes for the judgment
head (part inside tray / part on lid / gripper holding part) from rendered frames, given exact regions from
MuJoCo's segmentation renderer? Regions are ground truth on purpose: this isolates the relation model from
detection, the way the paper's A1 axis does, and it is the first rung of a learned perception seam
(regions -> relations -> facts -> decision).

Instrument: the published ONNX graph + predicate bank (Hugging Face maelic/relsgg-vits16plus, ungated, DINOv3
licence), run with onnxruntime on CPU; the feed follows the authors' deploy/runtime.py contract (plain square
resize to 448, RGB/255, normalised cxcywh boxes zero-padded to 32, W/alpha rows from the bank, score =
sigmoid(a*(pred_logit + pair_logit) + b) with the shipped Platt (a, b)). No third-party code is executed.

Protocol fixed in the notebook before the run (E86 pre-registration, 2026-09-19).
"""
import sys, os, json, time, argparse, glob
import numpy as np, mujoco, cv2
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from src.cell import scene as S

RAM_DIR = os.environ.get("CELL_RAM_DIR", "third_party/relate_anything/weights")  # RelateAnything ONNX export + bank_names.json; set CELL_RAM_DIR to point elsewhere
VOCAB = ["inside", "contained in", "on", "on top of", "resting on", "holding", "gripping", "carrying", "held by",
         "above", "below", "near", "touching", "covering", "reaching for"]
QUESTIONS = {  # question -> (subject kind, object kind, primary predicates, GT rule)
    "part_in_tray": dict(sub="part", obj="tray", preds=["inside", "contained in"]),
    "part_on_lid": dict(sub="part", obj="lid", preds=["on top of", "on", "resting on"]),
    "gripper_holding_part": dict(sub="gripper", obj="part", preds=["holding", "gripping", "carrying"]),
}

class Head:
    def __init__(self, d=RAM_DIR, vocab=VOCAB):
        import onnxruntime as ort
        meta = json.load(open(os.path.join(d, "relateanything.json")))
        self.img_size, self.max_boxes = meta["img_size"], meta["max_boxes"]
        self.a, self.b = float(meta["calibration"]["a"]), float(meta["calibration"]["b"])
        names = json.load(open(os.path.join(d, "bank_names.json")))["names"]
        z = np.load(os.path.join(d, "predicate_bank.npz"), allow_pickle=False)
        idx = [names.index(v) for v in vocab]
        self.vocab = list(vocab); self.W = np.ascontiguousarray(z["W"][idx].astype(np.float32)); self.alpha = np.ascontiguousarray(z["alpha"][idx].astype(np.float32))
        self.sess = ort.InferenceSession(os.path.join(d, "relateanything.onnx"), providers=["CPUExecutionProvider"])

    def __call__(self, rgb, boxes_xyxy):
        """rgb: HxWx3 uint8 (already RGB). boxes: [N,4] pixels. Returns per ordered pair (i,j): logits [V], pair logit."""
        H, W = rgb.shape[:2]; N = len(boxes_xyxy)
        img = cv2.resize(rgb, (self.img_size, self.img_size), interpolation=cv2.INTER_LINEAR)
        x = np.ascontiguousarray(img.transpose(2, 0, 1)[None].astype(np.float32) / 255.0)
        b = np.asarray(boxes_xyxy, np.float32).copy(); b[:, [0, 2]] /= W; b[:, [1, 3]] /= H
        cxcywh = np.stack([(b[:, 0] + b[:, 2]) / 2, (b[:, 1] + b[:, 3]) / 2, b[:, 2] - b[:, 0], b[:, 3] - b[:, 1]], -1).astype(np.float32)
        padded = np.zeros((1, self.max_boxes, 4), np.float32); n = min(N, self.max_boxes); padded[0, :n] = cxcywh[:n]
        feed = {"image": x, "boxes": padded, "box_counts": np.array([n], np.int64), "W": self.W, "alpha": self.alpha}
        pred, pair, sub, obj, valid = self.sess.run(None, feed)
        pred, pair, sub, obj, valid = pred[0], pair[0], sub[0], obj[0], valid[0]
        out = {}
        for k in range(len(valid)):
            if not valid[k] or sub[k] >= n or obj[k] >= n: continue
            out[(int(sub[k]), int(obj[k]))] = (pred[k].astype(float).tolist(), float(pair[k]))
        return out

    def score(self, pred_logit, pair_logit, w=1.0):
        return float(1.0 / (1.0 + np.exp(-(self.a * (pred_logit + w * pair_logit) + self.b))))

def make_camera(cam_cfg):
    cam = mujoco.MjvCamera(); cam.type = mujoco.mjtCamera.mjCAMERA_FREE
    cam.lookat[:] = cam_cfg["lookat"]; cam.distance = cam_cfg["distance"]; cam.azimuth = cam_cfg["azimuth"]; cam.elevation = cam_cfg["elevation"]
    return cam

def regions(world, spec, seg):
    """Ground-truth boxes from the segmentation render: parts, trays (walls+floor, lid excluded), visible lids, gripper."""
    m = world.model; gid = seg[..., 0]; typ = seg[..., 1]; G = int(mujoco.mjtObj.mjOBJ_GEOM)
    def box_of(gids):
        mask = np.isin(gid, list(gids)) & (typ == G); ys, xs = np.nonzero(mask)
        return None if len(xs) == 0 else [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1, int(mask.sum())]
    out = {}
    for p in spec["parts"]: out[p["id"]] = box_of([world.gid[p["id"]]])
    for name in S.TRAY_Y:
        bid = m.body(f"tray_{name}").id; gids = set(range(m.body_geomadr[bid], m.body_geomadr[bid] + m.body_geomnum[bid])) - {m.geom(f"lid_{name}").id}
        out[f"tray_{name}"] = box_of(gids); out[f"lid_{name}"] = box_of([m.geom(f"lid_{name}").id])
    out["gripper"] = box_of(world.gripper_gids)
    return {k: v for k, v in out.items() if v is not None}

def containment(a, b):
    """fraction of box a inside box b."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    area = max(1e-6, (a[2] - a[0]) * (a[3] - a[1])); return ix * iy / area

def collect(jobs, cam_cfg, width, height, every_s, out_json, preview_dir=None, one_pass=False):
    """jobs: list of (seed, arm)."""
    from src.cell.harness import episode
    head = Head(); frames = []; t_head = []
    for seed, arm in jobs:
        renderer = {}; last = {"t": -1e9}
        def on_step(world, st, skill, ctrl, seed=seed):
            if not renderer:
                renderer["r"] = mujoco.Renderer(world.model, height=height, width=width); renderer["cam"] = make_camera(cam_cfg); renderer["spec"] = st.get("spec")
            if world.t - last["t"] < every_s: return
            last["t"] = world.t; r = renderer["r"]
            r.disable_segmentation_rendering(); r.update_scene(world.data, camera=renderer["cam"]); rgb = r.render().copy()
            r.enable_segmentation_rendering(); r.update_scene(world.data, camera=renderer["cam"]); seg = r.render().copy()
            spec = world._spec
            reg = regions(world, spec, seg)
            loc = {p["id"]: world.part_location(p["id"]) for p in spec["parts"]}
            rec = {"seed": seed, "arm": arm, "t": round(world.t, 2), "W": width, "H": height, "boxes": reg, "loc": loc, "held": world.held,
                   "blocked": sorted(world.blocked), "pairs": {}}
            names = list(reg.keys()); boxes = np.array([reg[n][:4] for n in names], np.float32)
            t0 = time.time()
            if one_pass:
                res = head(rgb, boxes); groups = [(names, res)]
            else:
                # per-question passes so every relevant pair is inside the head's 128-pair budget
                groups = []
                parts = [n for n in names if n.startswith("P")]
                for tray in [n for n in names if n.startswith("tray_")]:
                    lid = "lid_" + tray[5:]; sel = parts + [tray] + ([lid] if lid in reg else []) + ["gripper"]
                    sel = [n for n in sel if n in reg]; res = head(rgb, np.array([reg[n][:4] for n in sel], np.float32)); groups.append((sel, res))
                sel = parts + ["gripper"]; res = head(rgb, np.array([reg[n][:4] for n in sel], np.float32)); groups.append((sel, res))
            t_head.append(time.time() - t0)
            for sel, res in groups:
                for (i, j), (pl, pr) in res.items():
                    key = f"{sel[i]}|{sel[j]}"
                    if key not in rec["pairs"]: rec["pairs"][key] = {"pred": pl, "pair": pr}
            frames.append(rec)
            if preview_dir and len(frames) <= 8:
                from PIL import Image, ImageDraw
                im = Image.fromarray(rgb); dr = ImageDraw.Draw(im)
                for k, b in reg.items(): dr.rectangle(b[:4], outline=(255, 0, 0) if k.startswith("P") else (0, 255, 0), width=1); dr.text((b[0], max(0, b[1] - 10)), k, fill=(255, 255, 0))
                dr.text((4, 4), f"seed {seed} t={world.t:.1f} held={world.held} loc={loc}", fill=(255, 255, 255)); im.save(os.path.join(preview_dir, f"e86_s{seed}_t{world.t:05.1f}.png"))
        # the harness does not expose spec to on_step; wrap World to remember it
        import src.cell.harness as Hm
        orig_World = Hm.World
        class WorldSpec(orig_World):
            def __init__(self, parts, blocked_trays=()):
                super().__init__(parts, blocked_trays); self._spec = None
        Hm.World = WorldSpec
        orig_make = Hm.make_episode
        def make_and_remember(*a, **k):
            spec = orig_make(*a, **k); make_and_remember.last = spec; return spec
        Hm.make_episode = make_and_remember
        def on_step_wrapped(world, st, skill, ctrl):
            if getattr(world, "_spec", None) is None: world._spec = make_and_remember.last
            on_step(world, st, skill, ctrl)
        try:
            r = episode(seed, arm, on_step=on_step_wrapped)
        finally:
            Hm.World = orig_World; Hm.make_episode = orig_make
            if renderer: renderer["r"].close()
        print(f"seed {seed} arm {arm}: {sum(1 for f in frames if f['seed']==seed and f['arm']==arm)} frames | parts_correct {r['parts_correct']} on_lid {r.get('on_lid')} floor {r.get('floor')} | head {np.mean(t_head):.2f}s/frame", flush=True)
        json.dump({"vocab": head.vocab, "calib": [head.a, head.b], "camera": cam_cfg, "frames": frames}, open(out_json, "w"))
    return frames

def auroc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, bool)
    if y.all() or (~y).all(): return float("nan")
    order = np.argsort(s); ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    # average ranks for ties
    for v in np.unique(s):
        m = s == v
        if m.sum() > 1: ranks[m] = ranks[m].mean()
    return float((ranks[y].sum() - y.sum() * (y.sum() + 1) / 2) / (y.sum() * (~y).sum()))

def evaluate(out_json):
    d = json.load(open(out_json)); vocab = d["vocab"]; a, b = d["calib"]; frames = d["frames"]
    sig = lambda pl, pr: 1.0 / (1.0 + np.exp(-(a * (np.asarray(pl) + pr) + b)))
    print(f"frames {len(frames)} | episodes {len(set((f['seed'], f.get('arm')) for f in frames))} | arms {sorted(set(str(f.get('arm')) for f in frames))}")
    rows = {}
    for q, spec in QUESTIONS.items():
        S_, L_, G_, meta = [], [], [], []
        for f in frames:
            names = list(f["boxes"].keys()); parts = [n for n in names if n.startswith("P")]
            trays = [n for n in names if n.startswith("tray_")]; lids = [n for n in names if n.startswith("lid_")]
            if q == "part_in_tray": pairs = [(p, t, f["loc"][p] == "tray:" + t[5:]) for p in parts for t in trays]
            elif q == "part_on_lid": pairs = [(p, l, f["loc"][p] == "lid:" + l[4:]) for p in parts for l in lids]
            else: pairs = [("gripper", p, f["held"] == p) for p in parts if "gripper" in names]
            for s_, o_, gt in pairs:
                key = f"{s_}|{o_}"; rec = f["pairs"].get(key)
                bs, bo = f["boxes"][s_], f["boxes"][o_]
                if q == "gripper_holding_part": geo = containment(bo[:4], bs[:4])     # part box inside gripper box
                else: geo = containment(bs[:4], bo[:4])                              # part box inside container box
                if rec is None: sc = 0.0; scored = False
                else:
                    pv = sig(rec["pred"], rec["pair"]); sc = float(max(pv[vocab.index(p)] for p in spec["preds"])); scored = True
                S_.append(sc); L_.append(bool(gt)); G_.append(geo); meta.append((f["seed"], f["t"], s_, o_, scored, f["loc"].get(o_ if q == "gripper_holding_part" else s_), f))
        S_, L_, G_ = np.array(S_), np.array(L_), np.array(G_)
        n_pos = int(L_.sum()); pruned = sum(1 for m in meta if not m[4])
        au_m, au_g = auroc(S_, L_), auroc(G_, L_)
        print(f"\n[{q}] pairs {len(L_)} (pos {n_pos}) | pruned-by-sampler {pruned} | model AUROC {au_m:.3f} | box-containment AUROC {au_g:.3f}")
        # the ambiguous subset: geometry says 'inside the container box' (>= .9) -- can the image separate in-tray from held-above / on-lid / rim?
        amb = G_ >= 0.9
        if amb.sum() > 0 and L_[amb].any() and (~L_[amb]).any():
            print(f"   geometry-ambiguous subset (containment >= .9): n {int(amb.sum())} pos {int(L_[amb].sum())} | model AUROC {auroc(S_[amb], L_[amb]):.3f} | containment AUROC {auroc(G_[amb], L_[amb]):.3f}")
            negs = [m[5] for m, l, g in zip(meta, L_, amb) if g and not l]
            from collections import Counter; print("   negatives in that subset by true location:", dict(Counter(negs).most_common(6)))
        # per-predicate AUROC
        per = {}
        for p in spec["preds"]:
            sp = [float(sig(m[6]["pairs"][f"{m[2]}|{m[3]}"]["pred"], m[6]["pairs"][f"{m[2]}|{m[3]}"]["pair"])[vocab.index(p)]) if m[4] else 0.0 for m in meta]
            per[p] = auroc(sp, L_)
        # negatives inside the ambiguous subset, and where the model still fails: top-scored negatives by location
        if amb.sum() > 0:
            from collections import Counter
            hi_neg = [m[5] for m, l, g, sc_ in zip(meta, L_, amb, S_) if g and not l and sc_ >= 0.5]
            print("   ambiguous negatives the model still scores >= .5, by true location:", dict(Counter(hi_neg).most_common(6)), "of", int((amb & ~L_).sum()))
            lo_pos = int(((S_ < 0.5) & L_ & amb).sum()); print(f"   ambiguous positives scored < .5: {lo_pos} of {int((amb & L_).sum())}")
        # frames per arm and location mix, once
        if q == "part_in_tray":
            from collections import Counter
            print("   location mix over all part-frames:", dict(Counter(v for f in frames for v in f["loc"].values()).most_common(8)))
        print("   per predicate:", {k: round(v, 3) for k, v in per.items()})
        rows[q] = dict(n=len(L_), pos=n_pos, pruned=pruned, model=au_m, geometry=au_g, per_predicate=per)
    json.dump(rows, open(out_json.replace(".json", "_eval.json"), "w"), indent=1)
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", default="0-19"); ap.add_argument("--arm", default="rules"); ap.add_argument("--greedy-seeds", default=""); ap.add_argument("--out", default="results/perception/e86_ram_cell.json")
    ap.add_argument("--every", type=float, default=2.0); ap.add_argument("--width", type=int, default=800); ap.add_argument("--height", type=int, default=500)
    ap.add_argument("--camera", default="B"); ap.add_argument("--preview", default=None); ap.add_argument("--eval-only", action="store_true"); ap.add_argument("--one-pass", action="store_true")
    a = ap.parse_args()
    CAMS = {"A": dict(lookat=[0.0, 0.0, 0.05], distance=1.9, azimuth=150, elevation=-32),
            "B": dict(lookat=[0.15, 0.0, 0.05], distance=1.45, azimuth=150, elevation=-42),
            "C": dict(lookat=[0.2, 0.0, 0.05], distance=1.3, azimuth=180, elevation=-55)}
    lo, hi = a.seeds.split("-"); jobs = [(s_, a.arm) for s_ in range(int(lo), int(hi) + 1)]
    if a.greedy_seeds:
        glo, ghi = a.greedy_seeds.split("-"); jobs += [(s_, "greedy") for s_ in range(int(glo), int(ghi) + 1)]
    if not a.eval_only:
        if a.preview: os.makedirs(a.preview, exist_ok=True)
        collect(jobs, CAMS[a.camera], a.width, a.height, a.every, a.out, preview_dir=a.preview, one_pass=a.one_pass)
    evaluate(a.out); print("E86_DONE", flush=True)

"""E139: post-train CLM's projection heads on this fleet's own decision records (the same files the Laya copy trains on).

Rows: the harness's records (state, options, answer{choice, probabilities}); teacher rows give a soft target (the judge's
distribution over the options present), correction rows a one-hot on the operator's replacement. Each row becomes one
ChoiceExample in the engine's own text (schema.build_pairs with the harness's question), embedded once with the local
Qwen3-8B encoder (cached on disk), and the two heads are trained from the reference checkpoint with the group-masked
soft/hard cross-entropy of the reference trainer (train/finetune.py run_choice). Output: a checkpoint in the reference
format, loadable by clm_local via CLM_CKPT.
usage: python src/duck/clm_train.py --out results/duck/clm_head_pick_r5.pt --records <teacher.jsonl> --arm jev --seeds 0-2399 --extra <corr.jsonl ...> [--epochs 3 --lr 5e-4]"""
import os, sys, json, math, time, random, argparse, pickle, collections
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "third_party", "CLM", "src")); sys.path.insert(0, os.path.join(ROOT, "src"))
from clm.schema import build_pairs
from clm.heads import make_head, default_checkpoint, HF_FILE, PROJ_DIM, HIDDEN
from duck.clm_local import LocalEmbedder, ROOT as _R

ASK = "Which single action should the robot take right now? Follow the task and the operators' notes; keep people comfortable and safe before making progress."

def load_rows(paths, arm=None, seeds=None):
    lo, hi = (map(int, seeds.split("-")) if seeds else (None, None))
    rows = []
    for p in paths:
        for l in open(p):
            r = json.loads(l)
            if arm and r.get("arm") != arm: continue
            if seeds and not (lo <= r["seed"] <= hi): continue
            rows.append(r)
    return rows

def examples(rows, role, smooth=0.0):
    out, dropped = [], 0
    for r in rows:
        opts = r["options"]
        if len(opts) < 2: dropped += 1; continue
        q = {"type": "choice", "instructions": {"role": role, "ask": ASK}, "criteria": opts}
        stext, keys, cands = build_pairs(r["state"], {"action": q})["action"]
        probs = r["answer"].get("probabilities") or {}; tgt = np.array([float(probs.get(k, 0.0)) for k in keys], dtype=np.float32)
        if tgt.sum() <= 0: tgt = np.array([float(k == r["answer"]["choice"]) for k in keys], dtype=np.float32)
        tgt = tgt / tgt.sum()
        if smooth > 0:   # E155: soften the correction target over the actions that were acceptable, so a round teaches the action without teaching certainty
            acc = [k for k in (r.get("acceptable") or []) if k in keys] or list(keys)
            u = np.array([1.0 / len(acc) if k in acc else 0.0 for k in keys], dtype=np.float32)
            tgt = (1.0 - smooth) * tgt + smooth * u; tgt = tgt / tgt.sum()
        out.append((stext, keys, cands, tgt))
    return out, dropped

class DiskCache:
    def __init__(self, path):
        self.path = path; self.d = pickle.load(open(path, "rb")) if os.path.exists(path) else {}
    def save(self): pickle.dump(self.d, open(self.path, "wb"))

def embed_all(texts, cache_path, log):
    cache = DiskCache(cache_path); todo = [t for t in dict.fromkeys(texts) if t not in cache.d]
    log(f"embeddings: {len(set(texts))} unique texts, {len(todo)} to compute")
    if todo:
        emb = LocalEmbedder(); t0 = time.time()
        for i, t in enumerate(todo):
            cache.d[t] = emb._one(t)
            if (i + 1) % 50 == 0: log(f"  {i + 1}/{len(todo)} embedded, {time.time() - t0:.0f}s"); cache.save()
        cache.save(); del emb
    return cache.d

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--records", nargs="+", required=True); ap.add_argument("--arm", default="jev"); ap.add_argument("--seeds", default=None)
    ap.add_argument("--extra", nargs="*", default=[]); ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--lr", type=float, default=5e-4); ap.add_argument("--batch", type=int, default=64); ap.add_argument("--wd", type=float, default=0.01)
    ap.add_argument("--init", default=None, help="reference head checkpoint to start from (default: the CLM_v0.1-8B head)"); ap.add_argument("--cache", default=os.path.join(ROOT, "results", "duck", "clm_emb_cache.pkl")); ap.add_argument("--smooth", type=float, default=0.0, help="E155: mix this much uniform-over-acceptable into every target"); ap.add_argument("--entropy", type=float, default=0.0, help="E155: add lambda * sum(p log p), i.e. reward keeping entropy"); ap.add_argument("--val-frac", type=float, default=0.1); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(); log = lambda m: print(m, flush=True)
    os.environ.setdefault("DUCK_BODY", "pick"); from duck.e93_run import ROLE
    teacher = load_rows(a.records, a.arm, a.seeds); extra = load_rows(a.extra)
    ex_t, d1 = examples(teacher, ROLE); ex_e, d2 = examples(extra, ROLE, smooth=a.smooth); ex = ex_t + ex_e
    log(f"clm post-training: {len(teacher)} teacher rows ({a.arm}, {a.seeds}) + {len(extra)} correction rows -> {len(ex)} examples (dropped {d1 + d2} single-option)")
    texts = [e[0] for e in ex] + [c for e in ex for c in e[2]]; vec = embed_all(texts, a.cache, log)
    import torch, torch.nn.functional as F
    torch.manual_seed(a.seed); rng = random.Random(a.seed)
    groups = collections.defaultdict(list)
    for e in ex: groups[e[0]].append(e)
    keys_ = list(groups); rng.shuffle(keys_); nv = int(len(keys_) * a.val_frac); val = [e for k in keys_[:nv] for e in groups[k]]; tr = [e for k in keys_[nv:] for e in groups[k]]
    log(f"split on {len(keys_)} unique state texts: train {len(tr)} val {len(val)}")
    init = a.init or default_checkpoint() or os.path.join(ROOT, "third_party", "CLM", "checkpoints", HF_FILE)
    ck = torch.load(init, map_location="cpu"); cfg = dict(ck["cfg"])
    kw = dict(width=cfg["width"], depth=cfg["depth"], proj=ck.get("projection_dim", cfg.get("projection_dim", PROJ_DIM)), activation=cfg.get("activation", "gelu"), layernorm=cfg.get("layernorm", False), residual=cfg.get("residual", False), hidden=cfg.get("hidden_size", HIDDEN))
    sh, ah = make_head(**kw), make_head(**kw); sh.load_state_dict(ck["state_head"]); ah.load_state_dict(ck["action_head"])
    logit_scale = torch.nn.Parameter(torch.as_tensor(ck["logit_scale"]).float().clone())
    params = list(sh.parameters()) + list(ah.parameters()) + [logit_scale]; opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=a.wd)
    def tensors(batch):
        S = torch.from_numpy(np.stack([vec[e[0]] for e in batch])); K = max(len(e[2]) for e in batch)
        C = torch.zeros(len(batch), K, HIDDEN); M = torch.zeros(len(batch), K, dtype=torch.bool); T = torch.zeros(len(batch), K)
        for i, e in enumerate(batch):
            C[i, :len(e[2])] = torch.from_numpy(np.stack([vec[c] for c in e[2]])); M[i, :len(e[2])] = True; T[i, :len(e[3])] = torch.from_numpy(e[3])
        return S, C, M, T
    def logits(S, C, M):
        zq = F.normalize(sh(S), dim=-1); zc = F.normalize(ah(C), dim=-1)
        lg = logit_scale.exp().clamp(max=100.0) * torch.einsum("bh,bkh->bk", zq, zc); return lg.masked_fill(~M, -1e9)
    def evaluate(data):
        sh.eval(); ah.eval(); agree = ce = 0.0; n = 0
        with torch.no_grad():
            for i in range(0, len(data), 256):
                b = data[i:i + 256]; S, C, M, T = tensors(b); lg = logits(S, C, M); lp = F.log_softmax(lg, -1)
                ce += float(-(T * lp).sum(-1).sum()); agree += float((lg.argmax(-1) == T.argmax(-1)).sum()); n += len(b)
        sh.train(); ah.train(); return ce / max(n, 1), agree / max(n, 1)
    ce0, ag0 = evaluate(val) if val else (float("nan"), float("nan")); log(f"before: val CE {ce0:.3f} agreement {100 * ag0:.1f}% | logit_scale {logit_scale.exp().item():.2f}")
    steps = a.epochs * math.ceil(len(tr) / a.batch); sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=max(steps, 1), pct_start=0.1, anneal_strategy="cos"); t0 = time.time()
    for ep in range(1, a.epochs + 1):
        rng.shuffle(tr); tot = 0.0
        for i in range(0, len(tr), a.batch):
            b = tr[i:i + a.batch]; S, C, M, T = tensors(b); lp = F.log_softmax(logits(S, C, M), -1); loss = -(T * lp).sum(-1).mean()
            if a.entropy > 0: loss = loss + a.entropy * (lp.exp() * lp).masked_fill(~M, 0.0).sum(-1).mean()   # E155: minimising sum(p log p) maximises entropy
            opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tot += float(loss) * len(b)
        ce, ag = evaluate(val) if val else (float("nan"), float("nan")); log(f"=== epoch {ep}: train CE {tot / len(tr):.3f} | val CE {ce:.3f} agreement {100 * ag:.1f}% | logit_scale {logit_scale.exp().item():.2f} | {time.time() - t0:.0f}s")
    out = {"state_head": sh.state_dict(), "action_head": ah.state_dict(), "logit_scale": logit_scale.detach().cpu(), "cfg": cfg, "projection_dim": kw["proj"],
           "meta": {"records": a.records, "arm": a.arm, "seeds": a.seeds, "extra": a.extra, "epochs": a.epochs, "lr": a.lr, "init": init, "examples": len(ex), "smooth": a.smooth, "entropy": a.entropy}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True); torch.save(out, a.out); log(f"saved {a.out} | val CE {ce:.3f} agreement {100 * ag:.1f}%")

if __name__ == "__main__": main()

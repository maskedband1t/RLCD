"""E77 · the owned head (north-star path E2): distil Jev's recorded typed decisions into a ~0.5M-parameter
option-attention scorer (the jevlike / CUA-S1 shape: byte-level encoders over the context and over each option,
each option attends over the context, one logit per option, softmax over the live option set), then run it as a
closed-loop decision source with no API. Stdlib + torch. Code owns the option enumeration exactly as for Jev."""
import json, math, random, sys, os, time, collections
import torch, torch.nn as nn, torch.nn.functional as F

PAD = 256; CTX_MAX = 1024; OPT_MAX = 256

def render_context(state):
    """Compact text of the facts (the task text is constant and omitted; the model learns it implicitly)."""
    r = state["robot"]; lines = []
    if state.get("notes_from_operators"): lines.append("NOTES: " + " | ".join(state["notes_from_operators"]))
    lines.append(f"ROBOT holding={r['holding']} grasp={r['grasp']} at={r['location']} hand={'YES' if r['person_hand_in_workspace'] else 'no'}")
    for p in state["parts"]:
        lines.append(f"{p['id']} {p['size']} {p['colour']} {p['shape']} dmg={'Y' if p['looks_damaged'] else 'n'} frag={p['fragile']} wt={p['weight']} lot={p['lot']} {p['status']}{' BROKEN' if p['broken'] else ''}")
    lines.append("TRAYS " + " ".join(f"{k}={v}" for k, v in state["trays"].items()))
    if state.get("recent_actions"): lines.append("RECENT " + " ; ".join(state["recent_actions"][-3:]))
    return "\n".join(lines)

def encode(text, n):
    b = text.encode("utf-8")[:n]; ids = list(b) + [PAD] * (n - len(b)); return ids

class ByteEncoder(nn.Module):
    def __init__(self, d=96, layers=2, heads=4, max_len=CTX_MAX):
        super().__init__(); self.emb = nn.Embedding(257, d, padding_idx=PAD); self.pos = nn.Embedding(max_len, d)
        layer = nn.TransformerEncoderLayer(d, heads, dim_feedforward=2 * d, dropout=0.1, batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(layer, layers)
    def forward(self, ids):
        mask = ids == PAD; pos = torch.arange(ids.shape[1], device=ids.device)
        h = self.emb(ids) + self.pos(pos)[None]; h = self.enc(h, src_key_padding_mask=mask); return h, mask

class OwnedHead(nn.Module):
    def __init__(self, d=96):
        super().__init__(); self.ctx = ByteEncoder(d, layers=2, max_len=CTX_MAX); self.opt = ByteEncoder(d, layers=2, max_len=OPT_MAX)
        self.q = nn.Linear(d, d); self.k = nn.Linear(d, d); self.v = nn.Linear(d, d)
        self.out = nn.Sequential(nn.Linear(3 * d, d), nn.GELU(), nn.Linear(d, 1)); self.d = d
    def forward(self, ctx_ids, opt_ids, opt_mask):
        """ctx_ids [B, Lc]; opt_ids [B, O, Lo]; opt_mask [B, O] (True = live option). Returns logits [B, O]."""
        B, O, Lo = opt_ids.shape
        hc, mc = self.ctx(ctx_ids)                                        # [B, Lc, d]
        ho, mo = self.opt(opt_ids.view(B * O, Lo)); ho = ho.view(B, O, Lo, -1); mo = mo.view(B, O, Lo)
        w = (~mo).float().unsqueeze(-1); qo = (ho * w).sum(2) / w.sum(2).clamp(min=1)   # mean-pooled option [B, O, d]
        q = self.q(qo); k = self.k(hc); v = self.v(hc)
        att = torch.einsum("bod,bld->bol", q, k) / math.sqrt(self.d); att = att.masked_fill(mc[:, None, :], -1e9)
        c = torch.einsum("bol,bld->bod", att.softmax(-1), v)             # attended context per option
        logits = self.out(torch.cat([qo, c, qo * c], -1)).squeeze(-1)
        return logits.masked_fill(~opt_mask, -1e9)

def load_records(paths, exclude_kinds=(), seed_index=None):
    rows = []
    for p in paths:
        for line in open(p):
            r = json.loads(line); a = r["answer"]
            if "probabilities" not in a: continue
            if exclude_kinds and seed_index is not None:
                # match by parts signature, not by the (sometimes missing) seed tag — the first ablation leaked untagged E71 records
                norm = lambda sh: "unfamiliar_shape" if sh in ("capsule", "unfamiliar_shape") else sh
                sig = tuple((q["id"], q["colour"], norm(q["shape"]), q["size"], q["lot"]) for q in r["state"]["parts"])
                kind = seed_index.get(sig)
                if kind in exclude_kinds: continue
            keys = sorted(r["options"]); probs = [a["probabilities"].get(k, 0.0) for k in keys]
            s = sum(probs) or 1.0; probs = [x / s for x in probs]
            rows.append(dict(ctx=render_context(r["state"]), opts=[r["options"][k] for k in keys], keys=keys, probs=probs))
    return rows

def batchify(rows, device):
    B = len(rows); O = max(len(r["opts"]) for r in rows)
    ctx = torch.tensor([encode(r["ctx"], CTX_MAX) for r in rows], device=device)
    opt = torch.full((B, O, OPT_MAX), PAD, dtype=torch.long, device=device); mask = torch.zeros(B, O, dtype=torch.bool, device=device)
    tgt = torch.zeros(B, O, device=device)
    for i, r in enumerate(rows):
        for j, o in enumerate(r["opts"]): opt[i, j] = torch.tensor(encode(o, OPT_MAX), device=device); mask[i, j] = True; tgt[i, j] = r["probs"][j]
    return ctx, opt, mask, tgt

def train(rows, out_path, epochs=25, bs=24, lr=2e-3, device=None, val_frac=0.1, seed=0, log=print):
    rng = random.Random(seed); rows = rows[:]; rng.shuffle(rows); nv = max(1, int(len(rows) * val_frac)); val, tr = rows[:nv], rows[nv:]
    device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
    torch.manual_seed(seed); model = OwnedHead().to(device); nparams = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01); steps = epochs * math.ceil(len(tr) / bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=steps, pct_start=0.1)
    log(f"train {len(tr)} val {len(val)} decisions; params {nparams:,}; device {device}")
    best = (1e9, None); t0 = time.time()
    for ep in range(epochs):
        model.train(); rng.shuffle(tr); tot = 0.0
        for i in range(0, len(tr), bs):
            ctx, o, m, tgt = batchify(tr[i:i + bs], device); logits = model(ctx, o, m)
            logp = F.log_softmax(logits, -1); loss = -(tgt * logp).sum(-1).mean()        # cross-entropy to the teacher's distribution
            opt.zero_grad(); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); tot += loss.item() * len(tr[i:i + bs])
        model.eval(); agree = 0; vloss = 0.0
        with torch.no_grad():
            for i in range(0, len(val), bs):
                ctx, o, m, tgt = batchify(val[i:i + bs], device); logits = model(ctx, o, m)
                vloss += -(tgt * F.log_softmax(logits, -1)).sum(-1).sum().item(); agree += (logits.argmax(-1) == tgt.argmax(-1)).sum().item()
        vloss /= len(val); log(f"epoch {ep+1:2d} train CE {tot/len(tr):.3f} val CE {vloss:.3f} val argmax-agreement {100*agree/len(val):.1f}%  ({time.time()-t0:.0f}s)")
        if vloss < best[0]: best = (vloss, {k: v.detach().cpu() for k, v in model.state_dict().items()})
    torch.save({"state_dict": best[1], "val_ce": best[0], "n_train": len(tr), "params": nparams}, out_path); log(f"saved {out_path} (best val CE {best[0]:.3f})")
    return out_path

class StudentScorer:
    """Loads a checkpoint and scores an option dict for a facts state. Used by the `distilled` policy."""
    def __init__(self, path, device=None):
        self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        ck = torch.load(path, map_location="cpu"); self.model = OwnedHead(); self.model.load_state_dict(ck["state_dict"]); self.model.to(self.device).eval()
    def score(self, state, opts):
        keys = sorted(opts); row = dict(ctx=render_context(state), opts=[opts[k] for k in keys], keys=keys, probs=[0] * len(keys))
        with torch.no_grad():
            ctx, o, m, _ = batchify([row], self.device); p = self.model(ctx, o, m).softmax(-1)[0, :len(keys)].cpu().tolist()
        return dict(zip(keys, p))

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--records", nargs="+", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=25); ap.add_argument("--exclude-kind", nargs="*", default=[])
    args = ap.parse_args()
    idx = None
    if args.exclude_kind:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cell.episodes import make_episode
        idx = {}
        for s in range(280):
            e = make_episode(s); norm = lambda sh: "unfamiliar_shape" if sh in ("capsule", "unfamiliar_shape") else sh
            idx[tuple((q["id"], q["colour"], norm(q["shape"]), q["size"], q["lot"]) for q in e["parts"])] = e["events"]["unanticipated"]["kind"]
    rows = load_records(args.records, exclude_kinds=tuple(args.exclude_kind), seed_index=idx)
    train(rows, args.out, epochs=args.epochs)

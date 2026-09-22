"""E90 · Owned head v2: fine-tune Laya (ModernBERT-large, 421 M) on Jev's recorded sorting-cell decisions with
Laya's own RLCD recipe (policy-gradient on a proper scoring rule + soft cross-entropy to the teacher), on Apple
silicon. Mirrors the E77/E80 protocol: same teacher records (seeds 0-39), same held-out seeds (40-79), same
closed-loop arm structure (code picks the part; 7 options).

Rendering (fixed before training, declared in the notebook): state = `render_state` compact lines (D6);
options = short texts ("P1 -> jade tray", "pause in place", ...) so that 27 options fit Laya's 256-token
option head without truncation (D6's long option texts were cut to ~8 tokens each by build_sequence).

Usage:
  build + train:   USE_TF=0 PYTHONPATH=src python -m cell.e90_laya_head train --out results/cell/laya_v2
  eval decisions:  ... eval --ckpt results/cell/laya_v2 --records results/cell/e77_jev3_heldout_record.jsonl
  zero-shot D6b:   ... eval --ckpt convaiinnovations/laya --records results/cell/e71_jev_record.jsonl --d1cell
"""
import os, sys, json, time, math, random, argparse, shutil, collections
import numpy as np, torch
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.d6_laya_arm import render_state
from cell.decision_eval import seed_index, signature, acceptable, auroc

INSTRUCTIONS = "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."
TRAIN_RECORDS = ["results/cell/e71_jev_record.jsonl", "results/cell/e72_jev2_record.jsonl", "results/cell/e73_cons_record.jsonl",
                 "results/cell/e75_jev3_record.jsonl", "results/cell/e76_freeze_record.jsonl"]   # the E77 teacher set, seeds 0-39

def compact_option(key):
    if key.startswith("place_"):
        _, pid, tray = key.split("_", 2); return f"{pid} -> {tray} tray"
    return {"pause": "pause in place", "wait": "wait for the tray", "ask_operator": "ask the operator", "set_down": "set the part down on the table",
            "regrasp": "regrasp the slipping part", "done": "finished, nothing left to do"}.get(key, key.replace("_", " "))

def question(options):
    return {"t": "choice", "ins": INSTRUCTIONS, "crit": {k: compact_option(k) for k in options}}

def load_teacher_records(paths):
    rows = []
    for p in paths:
        for line in open(p):
            r = json.loads(line); a = r["answer"]
            if "probabilities" not in a or not r.get("options"): continue
            rows.append(r)
    return rows

def build_items(rows, tok, cfg):
    from laya.common import build_sequence, render_options, QTYPES
    items = []; dropped = 0
    for r in rows:
        q = question(r["options"]); keys = list(q["crit"].keys())
        if len(keys) < 2: dropped += 1; continue   # a single-option decision carries nothing to learn (the station's "done" states)
        target = np.array([r["answer"]["probabilities"].get(k, 0.0) for k in keys], float); s = target.sum(); target = target / s if s > 0 else np.full(len(keys), 1 / len(keys))
        seq, markers = build_sequence(tok, render_state(r["state"], cfg["max_len"]), q, cfg["max_len"], cfg["head_max_len"])
        if len(markers) != len(keys): dropped += 1; continue
        items.append({"ids": seq, "markers": markers, "qtype": QTYPES["choice"], "target": target.tolist(), "label": int(target.argmax()), "n": len(keys)})
    return items, dropped

def collate(items, pad_id):
    n, L = len(items), max(len(it["ids"]) for it in items); kmax = max(len(it["markers"]) for it in items)
    ids = torch.full((n, L), pad_id, dtype=torch.long); att = torch.zeros((n, L), dtype=torch.long)
    mpos = torch.zeros((n, kmax), dtype=torch.long); mmask = torch.zeros((n, kmax), dtype=torch.bool); target = torch.zeros((n, kmax), dtype=torch.float32)
    for i, it in enumerate(items):
        ids[i, :len(it["ids"])] = torch.tensor(it["ids"]); att[i, :len(it["ids"])] = 1; k = len(it["markers"])
        mpos[i, :k] = torch.tensor(it["markers"]); mmask[i, :k] = True; target[i, :len(it["target"])] = torch.tensor(it["target"], dtype=torch.float32)
    return {"input_ids": ids, "attention_mask": att, "marker_pos": mpos, "marker_mask": mmask, "target": target,
            "qtype": torch.tensor([it["qtype"] for it in items]), "label": torch.tensor([it["label"] for it in items])}

def fit_temp(Zs, Ts):
    if len(Zs) < 10: return 1.0
    kmax = max(len(z) for z in Zs); Z = torch.full((len(Zs), kmax), -1e4); T = torch.zeros((len(Zs), kmax))
    for i, (z, t) in enumerate(zip(Zs, Ts)): Z[i, :len(z)] = torch.tensor(z); T[i, :len(t)] = torch.tensor(t, dtype=torch.float32)
    log_t = torch.zeros(1, requires_grad=True); opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=100)
    def closure():
        opt.zero_grad(); loss = -(T * torch.log_softmax(Z / log_t.exp(), -1)).sum(-1).mean(); loss.backward(); return loss
    opt.step(closure); return float(torch.clamp(log_t.exp(), 0.1, 10.0).item())

def base_dir(model_id="convaiinnovations/laya"):
    from huggingface_hub import snapshot_download
    return snapshot_download(model_id)

def train(out_dir, records=TRAIN_RECORDS, epochs=3, micro=4, accum=8, group=4, lr_enc=2.5e-5, lr_head=1e-4, sigma0=0.4, sigma1=0.1, val_frac=0.1, seed=0, max_steps=None, log=print, recipe="rlcd"):
    from transformers import AutoTokenizer
    from safetensors.torch import load_file, save_file
    from laya.agent import _fix_tokenizer_config
    from laya.common import build_model, proper_reward
    torch.manual_seed(seed); random.seed(seed)
    mdir = base_dir(); _fix_tokenizer_config(mdir); tok = AutoTokenizer.from_pretrained(os.path.join(mdir, "tokenizer"))
    cfg = json.load(open(os.path.join(mdir, "rl_agent_config.json"))); cfg["max_len"] = 1024; cfg["head_max_len"] = 256
    rows = load_teacher_records(records); items, dropped = build_items(rows, tok, cfg)
    if recipe == "ce_hard":  # E91: the log-only-the-action baseline — one-hot on the teacher's argmax
        for it in items: t = [0.0] * len(it["target"]); t[it["label"]] = 1.0; it["target"] = t
    log(f"recipe {recipe}")
    random.Random(seed).shuffle(items); n_val = int(len(items) * val_frac); val, tr = items[:n_val], items[n_val:]
    log(f"records {len(rows)} | items {len(items)} (dropped {dropped}) | train {len(tr)} val {len(val)} | mean options {np.mean([it['n'] for it in items]):.1f} | mean tokens {np.mean([len(it['ids']) for it in items]):.0f}")
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = build_model(cfg, encoder_dir=os.path.join(mdir, "encoder")); model.load_state_dict(load_file(os.path.join(mdir, "model.safetensors")), strict=True)
    try: model.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False}); log("gradient checkpointing on")
    except Exception as e: log(f"no gradient checkpointing: {str(e)[:80]}")
    model.to(device).train()
    enc = [p for n_, p in model.named_parameters() if "encoder." in n_]; head = [p for n_, p in model.named_parameters() if "encoder." not in n_]
    opt = torch.optim.AdamW([{"params": enc, "lr": lr_enc}, {"params": head, "lr": lr_head}], weight_decay=0.01)
    total = max(1, (len(tr) // (micro * accum)) * epochs); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=total, eta_min=1e-6)
    t0 = time.time(); step = 0; history = []
    def evaluate_val():
        model.eval(); ce = []; agree = []; Z = []; T = []
        with torch.no_grad():
            for i in range(0, len(val), 8):
                b = collate(val[i:i + 8], tok.pad_token_id)
                logits, _ = model(b["input_ids"].to(device), b["attention_mask"].to(device), b["marker_pos"].to(device), b["marker_mask"].to(device), b["qtype"].to(device))
                logits = logits.float().cpu(); mask = b["marker_mask"]; lp = torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)
                ce += (-(b["target"] * lp).sum(-1)).tolist(); agree += (lp.argmax(-1) == b["label"]).tolist()
                for r_ in range(len(b["label"])):
                    k = int(mask[r_].sum()); Z.append(logits[r_, :k].tolist()); T.append(b["target"][r_, :k].tolist())
        model.train(); return float(np.mean(ce)), float(np.mean(agree)), Z, T
    for ep in range(epochs):
        random.Random(seed + ep).shuffle(tr); sigma = sigma0 + (sigma1 - sigma0) * (ep / max(1, epochs - 1)); opt.zero_grad(set_to_none=True); acc = 0; ep_loss = []; ep_rew = []
        for bi in range(0, len(tr), micro):
            chunk = tr[bi:bi + micro]; b = collate(chunk, tok.pad_token_id)
            logits, act = model(b["input_ids"].to(device), b["attention_mask"].to(device), b["marker_pos"].to(device), b["marker_mask"].to(device), b["qtype"].to(device))
            logits = logits.float(); mask = b["marker_mask"].to(device); k = mask.sum(-1, keepdim=True).float(); target = b["target"].to(device)
            eps = torch.randn((group,) + logits.shape, device=device) * sigma * mask; eps = (eps - eps.sum(-1, keepdim=True) / k) * mask
            z = logits.detach().unsqueeze(0) + eps; q = torch.softmax(z.masked_fill(~mask, -1e4), -1)
            with torch.no_grad():
                r = proper_reward(q, target.unsqueeze(0), b["qtype"].to(device), mask, w_sph=0.75, w_rps=1.0); adv = r - r.mean(0, keepdim=True); adv = adv / (adv.std() + 1e-6)
            logp = -(((z - logits.unsqueeze(0)) ** 2) * mask).sum(-1) / (2 * sigma ** 2)
            loss_rl = -(adv * logp).mean() if recipe == "rlcd" else torch.zeros((), device=device); loss_ce = -(target * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1).mean()
            loss = (loss_rl + 1.0 * loss_ce) / accum + 0.0 * act.sum(); loss.backward(); acc += 1; ep_loss.append(float(loss) * accum); ep_rew.append(float(r.mean()))
            if acc % accum == 0 or bi + micro >= len(tr):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad(set_to_none=True); step += 1
                if step % 10 == 0: log(f"  ep {ep+1}/{epochs} step {step}/{total} loss {np.mean(ep_loss[-10*accum:]):.3f} reward {np.mean(ep_rew[-10*accum:]):.3f} lr {sched.get_last_lr()[0]:.2e} {time.time()-t0:.0f}s")
                if max_steps and step >= max_steps: break
        ce, ag, Z, T = evaluate_val(); history.append({"epoch": ep + 1, "val_ce": ce, "val_agreement": ag, "seconds": round(time.time() - t0)}); log(f"=== epoch {ep+1}: val CE {ce:.3f} agreement {ag:.1%} | {time.time()-t0:.0f}s")
        if max_steps and step >= max_steps: break
    # temperatures by option-count bucket, fitted on validation
    model.eval(); ce, ag, Z, T = evaluate_val(); temps = {}
    for name, sel in [("choice:6-10", lambda k: 6 <= k <= 10), ("choice:11+", lambda k: k >= 11), ("choice:3-5", lambda k: 3 <= k <= 5), ("choice:2", lambda k: k == 2)]:
        zz = [(z, t) for z, t in zip(Z, T) if sel(len(z))]
        if len(zz) >= 10: temps[name] = fit_temp([z for z, _ in zz], [t for _, t in zz])
    os.makedirs(out_dir, exist_ok=True); save_file({k: v.detach().cpu().contiguous() for k, v in model.state_dict().items()}, os.path.join(out_dir, "model.safetensors"))
    for sub in ("encoder", "tokenizer"):
        if os.path.exists(os.path.join(out_dir, sub)): shutil.rmtree(os.path.join(out_dir, sub))
        shutil.copytree(os.path.join(mdir, sub), os.path.join(out_dir, sub))
    cfg2 = dict(cfg); cfg2["temperature_by_options"] = {**cfg.get("temperature_by_options", {}), **temps}; cfg2["temperature"] = [temps.get("choice:6-10", cfg["temperature"][0])] + list(cfg["temperature"][1:])
    cfg2["training"] = {"source": "E90 owned head v2", "recipe": recipe, "records": records, "items": len(items), "epochs": epochs, "steps": step, "history": history, "temps_fitted": temps, "val_ce": ce, "val_agreement": ag}
    json.dump(cfg2, open(os.path.join(out_dir, "rl_agent_config.json"), "w"), indent=1); log(f"saved {out_dir} | temps {temps} | val CE {ce:.3f} agreement {ag:.1%}")
    return history

def eval_decisions(ckpt, records, d1cell=False, limit=400, out=None):
    """Decision-level: argmax agreement with the teacher, acceptable rate, AUROC(conf -> acceptable)."""
    os.environ.setdefault("USE_TF", "0"); import laya
    agent = laya.Agent(ckpt, device="mps" if torch.backends.mps.is_available() else "cpu")
    rows = [json.loads(l) for l in open(records) if l.strip()]; rows = [r for r in rows if r.get("options") and "choice" in r["answer"]]
    if d1cell: random.Random(20260918).shuffle(rows); rows = rows[:limit]
    idx = seed_index(); res = []; lat = []
    for r in rows:
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec); q = question(r["options"])
        t0 = time.time(); ans = agent.predict(render_state(r["state"], 1024), {"action": {"type": "choice", "instructions": q["ins"], "criteria": q["crit"]}})["answers"]["action"]; lat.append(time.time() - t0)
        res.append({"seed": seed, "choice": ans["choice"], "conf": float(ans["confidence"]), "teacher": r["answer"]["choice"], "ok": ans["choice"] in acc, "teacher_ok": r["answer"]["choice"] in acc, "probs": ans.get("probabilities"), "acc": sorted(acc)})
    ok = np.array([x["ok"] for x in res]); tok_ = np.array([x["teacher_ok"] for x in res]); conf = np.array([x["conf"] for x in res]); agree = np.mean([x["choice"] == x["teacher"] for x in res])
    print(f"{ckpt} on {records}: decisions {len(res)} | acceptable {ok.mean():.1%} (teacher {tok_.mean():.1%}) | agreement with teacher {agree:.1%} | AUROC(conf->acceptable) {auroc(conf, ok):.3f} | latency median {np.median(lat):.3f}s")
    for lo, hi in [(0, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        m = (conf >= lo) & (conf < hi)
        if m.sum(): print(f"   conf [{lo:.1f},{hi:.1f}): n={m.sum():>3} acceptable {ok[m].mean():.1%}")
    if out: json.dump(res, open(out, "w"))
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["train", "eval", "smoke"]); ap.add_argument("--out", default="results/cell/laya_v2"); ap.add_argument("--ckpt", default="results/cell/laya_v2")
    ap.add_argument("--records", default="results/cell/e77_jev3_heldout_record.jsonl"); ap.add_argument("--d1cell", action="store_true"); ap.add_argument("--epochs", type=int, default=3); ap.add_argument("--micro", type=int, default=4); ap.add_argument("--accum", type=int, default=8)
    ap.add_argument("--extra-records", nargs="*", default=[]); ap.add_argument("--max-steps", type=int, default=None); ap.add_argument("--recipe", default="rlcd", choices=["rlcd", "ce_soft", "ce_hard"]); ap.add_argument("--eval-out", default=None)
    a = ap.parse_args()
    if a.cmd == "smoke": train(a.out + "_smoke", epochs=1, micro=a.micro, accum=2, max_steps=3)
    elif a.cmd == "train": train(a.out, records=TRAIN_RECORDS + a.extra_records, epochs=a.epochs, micro=a.micro, accum=a.accum, recipe=a.recipe)
    else: eval_decisions(a.ckpt, a.records, d1cell=a.d1cell, out=a.eval_out)

"""E91b · refit one scalar temperature on VALIDATION acceptability (the singleton event: exactly one acceptable action) for a
trained owned head, then write a refit checkpoint (weights symlinked, per-bucket temperatures scaled) and re-score the E77
held-out decisions. Pre-registered 2026-09-20 02:55 PDT. The validation split is rebuilt from the training shuffle (seed 0,
10 %, no dropped items), so no held-out seed is ever used for the fit."""
import os, sys, json, random, argparse, time
import numpy as np
sys.path.insert(0, "src")
from cell.e90_laya_head import TRAIN_RECORDS, load_teacher_records, question, eval_decisions
from cell.d6_laya_arm import render_state
from cell.decision_eval import seed_index, signature, acceptable, auroc
from cell.d7_calibration import ece

def val_rows(records, seed=0, val_frac=0.1):
    rows = load_teacher_records(records); idx = list(range(len(rows))); random.Random(seed).shuffle(idx)
    n_val = int(len(rows) * val_frac); return [rows[i] for i in idx[:n_val]]

def top1_at(z, T):
    q = np.exp((z - z.max()) / T); q /= q.sum(); return float(q.max())

def fit(ckpt, records, seed=0, all_rows=False):
    os.environ.setdefault("USE_TF", "0"); import laya, torch
    agent = laya.Agent(ckpt, device="mps" if torch.backends.mps.is_available() else "cpu"); idx = seed_index(); Z = []; ok = []; single = []
    for r in (load_teacher_records(records) if all_rows else val_rows(records, seed)):
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        acc = acceptable(r["state"], idx[sig][1]); q = question(r["options"])
        ans = agent.predict(render_state(r["state"], 1024), {"action": {"type": "choice", "instructions": q["ins"], "criteria": q["crit"]}})["answers"]["action"]
        p = np.array([max(1e-9, float(v)) for v in ans["probabilities"].values()]); Z.append(np.log(p)); ok.append(ans["choice"] in acc); single.append(len(acc) == 1)
    ok = np.array(ok, bool); single = np.array(single, bool)
    def nll(T, sel):
        t1 = np.array([top1_at(z, T) for z in Z])[sel]; t1 = np.clip(t1, 1e-6, 1 - 1e-6); o = ok[sel]; return -float(np.mean(o * np.log(t1) + (~o) * np.log(1 - t1)))
    grid = np.logspace(-1, 1, 161); Ts = grid[np.argmin([nll(T, single) for T in grid])]
    fine = np.linspace(Ts / 1.3, Ts * 1.3, 121); Ts = float(fine[np.argmin([nll(T, single) for T in fine])])
    before = np.array([top1_at(z, 1.0) for z in Z]); after = np.array([top1_at(z, Ts) for z in Z])
    rep = {}
    for name, sel in [("val all", np.ones_like(ok)), ("val singleton", single)]:
        rep[name] = dict(n=int(sel.sum()), acc=float(ok[sel].mean()), over_before=float(before[sel].mean() - ok[sel].mean()), ece_before=ece(before[sel], ok[sel])[0], over_after=float(after[sel].mean() - ok[sel].mean()), ece_after=ece(after[sel], ok[sel])[0], auroc=float(auroc(before[sel], ok[sel])))
    return Ts, rep

def write_refit(ckpt, out, T, rep):
    os.makedirs(out, exist_ok=True)
    for sub in ("model.safetensors", "encoder", "tokenizer"):
        dst = os.path.join(out, sub)
        if not os.path.exists(dst): os.symlink(os.path.abspath(os.path.join(ckpt, sub)), dst)
    cfg = json.load(open(os.path.join(ckpt, "rl_agent_config.json")))
    cfg["temperature_by_options"] = {k: v * T for k, v in cfg.get("temperature_by_options", {}).items()}; cfg["temperature"] = [t * T for t in cfg["temperature"]]
    cfg["refit"] = {"source": "E91b", "scalar_T_on_validation_singleton_acceptability": T, "validation_report": rep, "from": ckpt}
    json.dump(cfg, open(os.path.join(out, "rl_agent_config.json"), "w"), indent=1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--ckpt", required=True); ap.add_argument("--out", required=True); ap.add_argument("--records", nargs="*", default=TRAIN_RECORDS); ap.add_argument("--eval-out", default=None); ap.add_argument("--all-rows", action="store_true", help="fit on every record given (external records), not the 10 %% validation split"); a = ap.parse_args()
    t0 = time.time(); T, rep = fit(a.ckpt, a.records, all_rows=a.all_rows); write_refit(a.ckpt, a.out, T, rep)
    print(f"{a.ckpt}: fitted T = {T:.3f} ({time.time()-t0:.0f}s)")
    for k, v in rep.items(): print(f"   {k:<14} n={v['n']:>4} acc {v['acc']:.3f} | over {v['over_before']:+.3f} -> {v['over_after']:+.3f} | ECE {v['ece_before']:.3f} -> {v['ece_after']:.3f} | AUROC {v['auroc']:.3f}")
    if a.eval_out: eval_decisions(a.out, "results/cell/e77_jev3_heldout_record.jsonl", d1cell=True, out=a.eval_out)

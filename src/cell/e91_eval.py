"""E91 · recipe ablation scoring: closed loops paired by seed against laya_v2 (rlcd 1x), decision-level calibration on
the E77 held-out set (strict and singleton), and the pre-registered predictions P91.1–P91.5 scored in place."""
import json, sys, os, glob
import numpy as np
sys.path.insert(0, "src")
from cell.analyze import wilson, boot_diff
from cell.decision_eval import auroc
from cell.d7_calibration import ece, scores

def load(p): return {r["seed"]: r for r in (json.loads(l) for l in open(p) if l.strip())}
LOOPS = [("teacher jev3 (E77)", "results/cell/e77_jev3_heldout.jsonl"), ("rlcd 1x (E90 laya_v2)", "results/cell/e90_laya_v2_heldout.jsonl"),
         ("rlcd 2x (E90b)", "results/cell/e90b_laya_v2_2x_heldout.jsonl"), ("ce_soft (E91)", "results/cell/e91_ce_soft_heldout.jsonl"), ("ce_hard (E91)", "results/cell/e91_ce_hard_heldout.jsonl"),
         ("ce_soft refit (E91b)", "results/cell/e91c_laya_v2_ce_soft_refit_heldout.jsonl"), ("ce_soft refit2 (E91b2)", "results/cell/e91c_laya_v2_ce_soft_refit2_heldout.jsonl"),
         ("ce_soft 2x (E91c)", "results/cell/e91c_laya_v2_ce_soft_2x_heldout.jsonl"), ("ce_soft 2x refit (E91c)", "results/cell/e91c_laya_v2_ce_soft_2x_refit_heldout.jsonl"),
         ("teacher + set-down rule (E92)", "results/cell/e92_jev3_setdown_heldout.jsonl"), ("ce_soft + rule (E92)", "results/cell/e92_laya_v2_ce_soft_setdown_heldout.jsonl"), ("ce_soft 2x + rule (E92)", "results/cell/e92_laya_v2_ce_soft_2x_setdown_heldout.jsonl")]
DEC = [("teacher (recorded)", None), ("laya zero-shot", "results/cell/e91_laya_heldout_decisions.json"), ("rlcd 1x", "results/cell/e91_laya_v2_heldout_decisions.json"),
       ("rlcd 2x", "results/cell/e91_laya_v2_2x_heldout_decisions.json"), ("ce_soft", "results/cell/e91_laya_v2_ce_soft_heldout_decisions.json"), ("ce_hard", "results/cell/e91_laya_v2_ce_hard_heldout_decisions.json"),
       ("ce_soft refit", "results/cell/e91b_laya_v2_ce_soft_refit_heldout_decisions.json"), ("ce_soft 2x", "results/cell/e91c_laya_v2_ce_soft_2x_heldout_decisions.json"), ("ce_soft 2x refit", "results/cell/e91c_laya_v2_ce_soft_2x_refit_heldout_decisions.json")]

def loop_table():
    ref = load(LOOPS[1][1]) if os.path.exists(LOOPS[1][1]) else None
    print(f"{'arm, seeds 40–79':<28}{'parts correct':>22}{'viol/ep':>9}{'pauses':>8}{'asks':>7}{'dec/ep':>8}{'op s':>7}{'bank':>7}{'paired vs rlcd 1x':>26}")
    for name, p in LOOPS:
        if not os.path.exists(p): print(f"{name:<28} (pending)"); continue
        d = load(p); rows = list(d.values()); n = len(rows)
        k = sum(r["parts_correct"] for r in rows); N = sum(r["n_parts"] for r in rows); _, lo, hi = wilson(k, N)
        viol = np.mean([r["violations"] for r in rows])
        bank = np.mean([bool(r["unanticipated_correct"]) for r in rows]); pc = {s: 100 * r["parts_correct"] / r["n_parts"] for s, r in d.items()}
        pair = ""
        if ref is not None and p != LOOPS[1][1]:
            m, lo2, hi2 = boot_diff(pc, {s: 100 * r["parts_correct"] / r["n_parts"] for s, r in ref.items()}); pair = f"{m:+.1f} [{lo2:+.1f}, {hi2:+.1f}]"
        print(f"{name:<28}{100*k/N:6.1f} % [{100*lo:4.1f}, {100*hi:4.1f}]{viol:>9.2f}{np.mean([r['n_pauses'] for r in rows]):>8.2f}{np.mean([r['n_asks'] for r in rows]):>7.2f}{np.mean([r['decisions'] for r in rows]):>8.1f}{np.mean([r['operator_seconds'] for r in rows]):>7.1f}{100*bank:>6.0f} %{pair:>26}")
        ev = {}
        for r in rows: ev.setdefault(r["unanticipated"], []).append(bool(r["unanticipated_correct"]))
        gov = np.mean([r.get("n_gov_setdown", 0) for r in rows]); print("      by event: " + ", ".join(f"{k} {sum(v)}/{len(v)}" for k, v in sorted(ev.items())) + (f" | governor set-downs/ep {gov:.2f}" if gov else ""))

def dec_table():
    print(f"\n{'head, E77 held-out decisions':<20}{'n':>5}{'acceptable':>12}{'agree':>8}{'AUROC':>7}{'ECE':>6}{'over':>7} | singleton: {'n':>4}{'acc':>7}{'ECE':>6}{'over':>7}{'AUROC':>7}{'lat':>7}")
    out = {}
    for name, p in DEC:
        if p is None or not os.path.exists(p): print(f"{name:<20} (missing)" if p else f"{name:<20} see D7 panel B"); continue
        rows = json.load(open(p)); ok = np.array([r["ok"] for r in rows], bool); conf = np.array([r["conf"] for r in rows]); agree = np.mean([r["choice"] == r["teacher"] for r in rows])
        e, _ = ece(conf, ok); sing = [r for r in rows if len(r.get("acc", [])) == 1]
        so = np.array([r["ok"] for r in sing], bool); sc = np.array([r["conf"] for r in sing]); se, _ = ece(sc, so) if len(sing) else (float("nan"), [])
        out[name] = dict(n=len(rows), acc=float(ok.mean()), agree=float(agree), auroc=float(auroc(conf, ok)), ece=float(e), over=float(conf.mean() - ok.mean()), s_n=len(sing), s_acc=float(so.mean()) if len(sing) else None, s_ece=float(se), s_over=float(sc.mean() - so.mean()) if len(sing) else None, s_auroc=float(auroc(sc, so)) if len(sing) else None)
        o = out[name]; print(f"{name:<20}{o['n']:>5}{100*o['acc']:>11.1f}%{100*o['agree']:>7.1f}%{o['auroc']:>7.3f}{o['ece']:>6.3f}{o['over']:>+7.3f} | {o['s_n']:>13}{100*o['s_acc']:>6.1f}%{o['s_ece']:>6.3f}{o['s_over']:>+7.3f}{o['s_auroc']:>7.3f}")
    return out

def score(out):
    print("\n--- P91 scoring (thresholds as pre-registered 2026-09-19 23:31 PDT)")
    r, s, h = out.get("rlcd 1x"), out.get("ce_soft"), out.get("ce_hard")
    if r and s and h:
        ag = [o["agree"] for o in (r, s, h)]; print(f"P91.1 agreement within ±2 points: rlcd {100*r['agree']:.1f} / soft {100*s['agree']:.1f} / hard {100*h['agree']:.1f} -> spread {100*(max(ag)-min(ag)):.1f} pts -> {'HELD' if max(ag)-min(ag) <= .02 else 'FAILED'}")
        print(f"P91.2 ce_hard over-confident: ECE {h['ece']:.3f} vs rlcd {r['ece']:.3f} (+{h['ece']-r['ece']:.3f}; need ≥ +.05) and AUROC {h['auroc']:.3f} (need ≤ .62); ce_soft AUROC {s['auroc']:.3f} vs rlcd {r['auroc']:.3f} (|Δ| {abs(s['auroc']-r['auroc']):.3f}, need ≤ .03) -> {'HELD' if (h['ece']-r['ece'] >= .05 and h['auroc'] <= .62 and abs(s['auroc']-r['auroc']) <= .03) else 'FAILED (see parts)'}")
        print(f"      singleton view: ECE rlcd {r['s_ece']:.3f} soft {s['s_ece']:.3f} hard {h['s_ece']:.3f}; over rlcd {r['s_over']:+.3f} soft {s['s_over']:+.3f} hard {h['s_over']:+.3f}")
        print(f"P91.3 rlcd ECE ≤ ce_soft ECE: {r['ece']:.3f} vs {s['ece']:.3f} -> {'HELD' if r['ece'] <= s['ece'] else 'FAILED'} (loop half scored in the loop table)")
    print("P91.4 / P91.5: read from the loop table (asks ce_hard ≤ half of rlcd; violations ≥ +.15) and the eval latency line.")

if __name__ == "__main__":
    loop_table(); out = dec_table(); score(out)

"""D7 · reliability of confidence on identical decisions (pre-registered 2026-09-19 23:31 PDT).
Panel A: D4's 400 E71 decisions — Jev (full distribution recovered by key) vs the open models through the Simple
Jev readout. Panel B: the E77 held-out decisions — the teacher vs the owned heads. Panel C: live in-loop decisions.
Measures: ECE (10 equal-width bins), over-confidence, Brier, AUROC of confidence / top-2 margin / negative entropy,
median confidence when wrong. Dumb baseline shown: 'always confidence 1' (ECE = 1 - accuracy)."""
import json, sys, random, glob, os, hashlib
import numpy as np
sys.path.insert(0, "src")
from cell.decision_eval import seed_index, signature, acceptable, auroc
from cell.episodes import make_episode

def ece(conf, ok, bins=10):
    conf = np.asarray(conf, float); ok = np.asarray(ok, float); edges = np.linspace(0, 1, bins + 1); e = 0.0; rows = []
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (conf >= lo) & ((conf < hi) if i < bins - 1 else (conf <= hi))
        if m.sum(): e += m.mean() * abs(ok[m].mean() - conf[m].mean()); rows.append([float(lo), float(hi), int(m.sum()), float(ok[m].mean()), float(conf[m].mean())])
    return float(e), rows

def scores(probs):
    if not probs: return None
    p = np.clip(np.array(sorted(probs.values(), reverse=True), float), 0, None); s = p.sum()
    if s <= 0: return None
    p = p / s; ent = -(p[p > 0] * np.log(p[p > 0])).sum()
    return float(p[0]), float(p[0] - (p[1] if len(p) > 1 else 0.0)), float(-ent)

DEFER = {"ask_operator", "pause", "wait"}
def summarize(name, rows, out, variants=("strict", "singleton", "lenient")):
    """rows: list of (probs-or-None, conf, ok, acc_size, choice). Variants: strict = choice in the acceptable set;
    singleton = strict, on decisions with exactly one acceptable action (confidence then means 'this is the right one');
    lenient = strict or a deferral (ask/pause/wait when not required: costly, not wrong)."""
    for v in variants:
        if v == "singleton": sel = [r for r in rows if r[3] == 1]
        else: sel = rows
        if v == "lenient": sel = [(p, c, (o or ch in DEFER), a, ch) for p, c, o, a, ch in sel]
        if len(sel) >= 20: _summ(f"{name} [{v}]", sel, out)

def _summ(name, rows, out):
    # method error 27: models report different "confidence" quantities (Laya: 1 - H/log k). Calibration is measured on the
    # top-1 PROBABILITY for every row that carries a distribution; the reported field is used only when no distribution exists.
    conf = np.array([(scores(p)[0] if scores(p) is not None else c) for p, c, _, _, _ in rows], float); ok = np.array([o for _, _, o, _, _ in rows], bool)
    sc = [scores(p) for p, _, _, _, _ in rows]; have = all(s is not None for s in sc)
    marg = np.array([s[1] for s in sc]) if have else None; ne = np.array([s[2] for s in sc]) if have else None
    e, bins = ece(conf, ok); acc = ok.mean(); brier = float(np.mean((conf - ok) ** 2)); wrong = conf[~ok]
    d = dict(name=name, n=int(len(ok)), acc=float(acc), mean_conf=float(conf.mean()), over=float(conf.mean() - acc), ece=e, brier=brier,
             auroc_conf=float(auroc(conf, ok)), auroc_margin=float(auroc(marg, ok)) if have else None, auroc_negent=float(auroc(ne, ok)) if have else None,
             wrong_median_conf=float(np.median(wrong)) if len(wrong) else None, frac_wrong_above_0_8=float((wrong >= .8).mean()) if len(wrong) else None, bins=bins)
    f = lambda x: "  –  " if x is None else f"{x:.3f}"
    print(f"{name:<58} n={d['n']:>4} acc {acc:.3f} conf {conf.mean():.3f} over {conf.mean()-acc:+.3f} ECE {e:.3f} (conf=1: {1-acc:.3f}) Brier {brier:.3f} | AUROC conf {d['auroc_conf']:.3f} margin {f(d['auroc_margin'])} -ent {f(d['auroc_negent'])} | wrong: median conf {f(d['wrong_median_conf'])}, ≥.8 {f(d['frac_wrong_above_0_8'])}")
    out.append(d); return d

def load(path): return [json.loads(l) for l in open(path) if l.strip()]

def main():
    out = []
    # ---------------- Panel A
    print("=== Panel A · D4's 400 E71 decisions (identical inputs)")
    e71 = [r for r in load("results/cell/e71_jev_record.jsonl") if len(r["options"]) >= 2 and "choice" in r["answer"]]
    random.Random(20260918).shuffle(e71); e71 = e71[:400]; bykey = {r["key"]: r for r in e71}
    jev_rows = {}
    for f in sorted(glob.glob("results/cell/d4_*-classifier.jsonl")):
        rows = load(f); name = os.path.basename(f)[3:-6]; open_rows = []; seen_keys = set()
        for r in rows:
            src = bykey[r["key"]]; assert src["answer"]["choice"] == r["jev"]["choice"], r["key"]
            jev_rows[r["key"]] = (src["answer"].get("probabilities"), float(src["answer"]["confidence"]), bool(r["jev_ok"]), len(r["acceptable_set"]), src["answer"]["choice"])
            o = r["open"]
            if "choice" in o and "probabilities" in o and r["key"] not in seen_keys: open_rows.append((o["probabilities"], float(o["confidence"]), bool(r["open_ok"]), len(r["acceptable_set"]), o["choice"])); seen_keys.add(r["key"])
        summarize(f"A · {name} (Simple Jev readout)", open_rows, out)
    summarize("A · Jev (System One API)", list(jev_rows.values()), out)
    if os.path.exists("results/cell/d8_preview_decisions.jsonl"):  # D8: the second RLCD model on the same decisions
        pr = [(r["preview"].get("probabilities"), float(r["preview"]["confidence"]), bool(r["preview_ok"]), len(r["acceptable_set"]), r["preview"]["choice"]) for r in load("results/cell/d8_preview_decisions.jsonl") if "choice" in r["preview"]]
        summarize("A · jev-preview (second RLCD model, D8)", pr, out)
    # ---------------- Panel B
    print("\n=== Panel B · E77 held-out decisions, seeds 40–79 (the teacher vs the owned heads)")
    idx = seed_index(); jb = []; e77_acc = []
    for r in load("results/cell/e77_jev3_heldout_record.jsonl"):
        if not r.get("options") or "choice" not in r["answer"]: continue
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        acc = acceptable(r["state"], idx[sig][1]); jb.append((r["answer"].get("probabilities"), float(r["answer"]["confidence"]), r["answer"]["choice"] in acc, len(acc), r["answer"]["choice"])); e77_acc.append(sorted(acc))
    summarize("B · Jev teacher (recorded)", jb, out)
    heads = [("B · laya_v2 (E90, rlcd 1x)", "results/cell/e90_heldout_decisions.json")] + [(f"B · {os.path.basename(f).split('_',1)[1][:-23]}", f) for f in sorted(glob.glob("results/cell/e91*_heldout_decisions.json"))]
    for name, f in heads:
        if os.path.exists(f):
            rows = json.load(open(f))
            if "acc" not in rows[0]:  # E90's file: acceptable sets by file-order alignment with the E77 rows (verified 372/372 on seed+teacher)
                assert len(rows) == len(e77_acc); rows = [dict(r, acc=a) for r, a in zip(rows, e77_acc)]
            summarize(name, [(r.get("probs"), float(r["conf"]), bool(r["ok"]), len(r["acc"]), r["choice"]) for r in rows], out)
    # ---------------- Panel C
    print("\n=== Panel C · live in-loop decisions (states the model steered into; de-duplicated)")
    def dedupe(rows):
        seen = set(); keep = []
        for r in rows:
            h = hashlib.sha1((json.dumps(r["state"], sort_keys=True) + json.dumps(sorted(r["options"]))).encode()).hexdigest()
            if h in seen or "choice" not in r["answer"]: continue
            seen.add(h); keep.append(r)
        return keep
    def score(rows, idx_, patch_foreign=False):
        res = []; miss = 0
        for r in rows:
            sig = signature(r["state"]["parts"])
            if sig not in idx_: miss += 1; continue
            facts = r["state"]
            if patch_foreign: facts = json.loads(json.dumps(facts)); facts["trays"] = {k: ("blocked_by_lid" if v == "contains_a_foreign_object" else v) for k, v in facts["trays"].items()}
            acc = acceptable(facts, idx_[sig][1]); res.append((r["answer"].get("probabilities"), float(r["answer"]["confidence"]), r["answer"]["choice"] in acc, len(acc), r["answer"]["choice"]))
        return res, miss
    idx_u = {}
    for s in range(40): e = make_episode(s, bank="unflagged"); idx_u[signature(e["parts"])] = (s, e)
    jev_u = dedupe(load("results/cell/e83_unflagged_record.jsonl") + load("results/cell/e88_unflagged_record.jsonl")); jev_u = [r for r in jev_u if not str(r.get("arm", "")).startswith("jev5")]
    sj_u = dedupe(load("results/cell/d4d_sj_record.jsonl"))
    pv_u = dedupe(load("results/cell/d8_preview_unflagged_record.jsonl")) if os.path.exists("results/cell/d8_preview_unflagged_record.jsonl") else []
    for name, rows in [("C · Jev, unflagged bank (E83+E88 arms)", jev_u), ("C · Qwen3.8-27B, unflagged bank (D4d arms)", sj_u)] + ([("C · jev-preview, unflagged bank (D8 arms)", pv_u)] if pv_u else []):
        res, miss = score(rows, idx_u, patch_foreign=True); print(f"   [{name}: {len(rows)} unique states, {miss} unmatched; foreign-object tray scored as blocked]"); summarize(name, res, out)
    jev_n = dedupe(load("results/cell/e88_notes_record.jsonl")); laya_n = dedupe(load("results/cell/e90_laya_v2_heldout_record.jsonl"))
    # D7b (2026-09-20): the final owned head driving the loop itself. The E92 set-down arm is excluded on purpose -
    # the governor rule changes which states the head visits, so it is not the same population as the rows above.
    soft2x = "results/cell/e91c_laya_v2_ce_soft_2x_heldout_record.jsonl"
    laya_s = dedupe(load(soft2x)) if os.path.exists(soft2x) else []
    for name, rows in [("C · Jev, notes bank (E88 arms)", jev_n), ("C · laya_v2, notes bank seeds 40–79 (E90)", laya_n)] + ([("C · laya_v2 ce_soft 2×, notes bank (E91c)", laya_s)] if laya_s else []):
        res, miss = score(rows, idx); print(f"   [{name}: {len(rows)} unique states, {miss} unmatched]"); summarize(name, res, out)
    json.dump(out, open("results/cell/d7_calibration.json", "w"), indent=1); print("\nsaved results/cell/d7_calibration.json")
    print("\n--- reliability tables (bin lo-hi: n, accuracy, mean confidence)")
    for d in out:
        print(f"{d['name']}:"); print("   " + " | ".join(f"{lo:.1f}-{hi:.1f}: {n}, {a:.2f}, {c:.2f}" for lo, hi, n, a, c in d["bins"]))

if __name__ == "__main__": main()

"""Pre-specified analysis for E69 (written before the gated numbers existed).
Operating curve per arm: completion (stations/6), operator-seconds, contact-seconds, by gate τ; P-H1..3 as pre-registered.
python -m sim.analyze_gate results/sim/gate_sweep_det.jsonl results/sim/jev_gated_live.jsonl --ungated results/sim/nojev_40x1_v2.jsonl results/sim/jev_live_40.jsonl --fig figures/fig1-handoff.png"""
import json, argparse, collections, numpy as np
def load(paths):
    rows = []
    for p in paths:
        try:
            for l in open(p): rows.append(json.loads(l))
        except FileNotFoundError: pass
    return rows
def boot(vals, n=10000, seed=0):
    v = np.array(vals, float); rng = np.random.default_rng(seed); bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(n)]
    return v.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
def main():
    p = argparse.ArgumentParser(); p.add_argument("gated", nargs="+"); p.add_argument("--ungated", nargs="*", default=[]); p.add_argument("--fig", default=None); a = p.parse_args()
    G = load(a.gated); U = load(a.ungated)
    cells = collections.defaultdict(list)
    for r in U: cells[(r["arm"], None)].append(r)
    for r in G: cells[(r["arm"], (r.get("gate") or {}).get("risk"))].append(r)
    print(f"{'arm':12s} {'τ':>5s} {'n':>3s} {'completion %':>13s} {'clean cross %':>14s} {'operator s':>16s} {'contact s':>16s} {'handoffs':>9s} {'crashed':>8s}")
    curve = collections.defaultdict(list)
    for (arm, tau), R in sorted(cells.items(), key=lambda kv: (kv[0][0], -1 if kv[0][1] is None else kv[0][1])):
        comp = [r["stations_cleared"] / 6 * 100 for r in R]; op = [r.get("operator_seconds", 0.0) for r in R]; con = [r["contact_seconds"] for r in R]
        cm, cl, ch = boot(comp); om, ol, oh = boot(op); km, kl, kh = boot(con)
        print(f"{arm:12s} {('—' if tau is None else f'{tau:.1f}'):>5s} {len(R):3d} {cm:6.0f} [{cl:3.0f},{ch:3.0f}] {100*np.mean([r.get('crossed_clean', False) for r in R]):13.0f}% {om:6.1f} [{ol:4.1f},{oh:4.1f}] {km:6.2f} [{kl:4.2f},{kh:4.2f}] {np.mean([r.get('n_handoffs', 0) for r in R]):9.1f} {sum(1 for r in R if r['crashed_at_s'] is not None):5d}/{len(R)}")
        curve[arm].append((tau, om, km, cm))
    # P-H1: Jev τ=1.6 vs ungated Jev, paired by seed
    ug = {r["seed"]: r for r in cells.get(("jev", None), [])}; g16 = {r["seed"]: r for r in cells.get(("jev", 1.6), [])}
    common = sorted(set(ug) & set(g16))
    if common:
        dc = [g16[s]["contact_seconds"] - ug[s]["contact_seconds"] for s in common]; ds = [g16[s]["stations_cleared"] - ug[s]["stations_cleared"] for s in common]
        m, lo, hi = boot(dc); ms, ls, hs = boot(ds); pct = np.mean([g16[s]["operator_pct"] for s in common])
        base = np.mean([ug[s]["contact_seconds"] for s in common])
        print(f"\nP-H1 (Jev τ=1.6 vs ungated, n={len(common)} paired seeds): contact {m:+.2f} s [{lo:+.2f},{hi:+.2f}] on a base of {base:.2f} s ({100*m/max(base,1e-9):+.0f} %); stations {ms:+.2f} [{ls:+.2f},{hs:+.2f}]; operator time {pct:.1f} % of episode  (predicted: −50 % contact, 5–15 % operator time, completion ≥)")
    # P-H2: at matched operator-seconds (~5 s), Jev-gated vs heuristic-gated contact (interpolate on each arm's curve)
    def contact_at(arm, target_op):
        pts = sorted([(o, k) for t, o, k, c in curve[arm] if t is not None]); 
        if len(pts) < 2: return None
        xs = [o for o, _ in pts]; ys = [k for _, k in pts]; return float(np.interp(target_op, xs, ys)), (min(xs), max(xs))
    for arm in ("jev", "heuristic", "climb_rule"):
        r = contact_at(arm, 5.0)
        if r: print(f"P-H2 contact at 5 operator-s, {arm:12s}: {r[0]:.2f} s  (curve spans operator-s {r[1][0]:.1f}–{r[1][1]:.1f})")
    # P-H3: handoffs near obstacles
    H = [h for r in G for h in r.get("handoffs", [])]
    if H: print(f"P-H3 handoffs with nearest obstacle < 4 m: {100*np.mean([h['nearest_m'] < 4.0 for h in H]):.0f} % of {len(H)}  (predicted ≥ 70 %); triggered by lost-target: {100*np.mean([(h.get('lost') or 0) >= 0.7 for h in H]):.0f} %")
    if a.fig:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        cols = {"published_baseline": "#bbbbbb", "heuristic": "#8a8aa0", "climb_rule": "#c8a03c", "jev": "#6ad08a", "jev_noclimb": "#2f7a48"}
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3), dpi=150)
        for arm, pts in curve.items():
            pts = sorted(pts, key=lambda x: x[1]); ax1.plot([o for _, o, _, _ in pts], [k for _, _, k, _ in pts], marker="o", color=cols.get(arm, "#444"), label=arm)
            ax2.plot([o for _, o, _, _ in pts], [c for _, _, _, c in pts], marker="o", color=cols.get(arm, "#444"), label=arm)
            for t, o, k, c in pts:
                if t is not None: ax1.annotate(f"τ{t}", (o, k), fontsize=7, xytext=(3, 3), textcoords="offset points"); ax2.annotate(f"τ{t}", (o, c), fontsize=7, xytext=(3, 3), textcoords="offset points")
        ax1.set_xlabel("operator-seconds per episode"); ax1.set_ylabel("contact-seconds per episode"); ax1.set_title("Safety bought with operator time", fontsize=10)
        ax2.set_xlabel("operator-seconds per episode"); ax2.set_ylabel("course completed (%)"); ax2.set_title("Progress vs operator time", fontsize=10)
        for ax in (ax1, ax2): ax.legend(fontsize=8, frameon=False); ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout(); plt.savefig(a.fig, bbox_inches="tight"); print("figure:", a.fig)
if __name__ == "__main__": main()

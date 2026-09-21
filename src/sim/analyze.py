"""Pre-specified analysis for H3 (written before results existed). Unit = seed. Repeats are stability, not samples.
python -m sim.analyze results/sim/nojev_40x3.jsonl [more.jsonl ...] --fig figures/fig1-course.png"""
import json, sys, collections, random, argparse, os
import numpy as np

def load(paths):
    rows = []
    for p in paths:
        for line in open(p): rows.append(json.loads(line))
    return rows

def per_seed(rows, arm, key):
    """Per-seed value = mean over repeats (repeats are not independent samples)."""
    by = collections.defaultdict(list)
    for r in rows:
        if r["arm"] == arm: by[r["seed"]].append(float(r[key]))
    return {s: np.mean(v) for s, v in by.items()}

def boot_diff(a, b, n=10000, seed=0):
    """Paired-by-seed bootstrap of mean(a - b) over seeds present in both arms."""
    seeds = sorted(set(a) & set(b)); d = np.array([a[s] - b[s] for s in seeds]); rng = np.random.default_rng(seed)
    bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(n)]
    return d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(seeds)

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h

def variance_decomposition(rows, arm, key):
    by = collections.defaultdict(list)
    for r in rows:
        if r["arm"] == arm: by[r["seed"]].append(float(r[key]))
    seeds = [v for v in by.values() if len(v) >= 2]
    if not seeds: return None
    within = np.mean([np.var(v, ddof=1) for v in seeds]); between = np.var([np.mean(v) for v in seeds], ddof=1)
    return within, between

def main():
    p = argparse.ArgumentParser(); p.add_argument("paths", nargs="+"); p.add_argument("--fig", default=None); a = p.parse_args()
    rows = load(a.paths); arms = sorted(set(r["arm"] for r in rows), key=lambda x: ["published_baseline", "heuristic", "climb_rule", "jev_noclimb", "jev"].index(x) if x in ["published_baseline", "heuristic", "climb_rule", "jev_noclimb", "jev"] else 9)
    print(f"{len(rows)} episodes · arms {arms} · seeds {len(set(r['seed'] for r in rows))} · repeats/seed/arm ≈ {len(rows)/max(1,len(arms))/max(1,len(set(r['seed'] for r in rows))):.1f}\n")
    print(f"{'arm':18s} {'seeds':>5s} {'P(cross)':>16s} {'P(clean cross)':>16s} {'stations med[IQR]':>18s} {'pre-beam s':>10s} {'contact s':>9s} {'vis %':>6s} {'crashed':>7s}")
    for arm in arms:
        R = [r for r in rows if r["arm"] == arm]; seeds = sorted(set(r["seed"] for r in R))
        cs = per_seed(rows, arm, "crossed_barrier"); k = sum(1 for s in seeds if cs[s] >= 0.5); pr, lo, hi = wilson(k, len(seeds))
        st = [np.mean([r["stations_cleared"] for r in R if r["seed"] == s]) for s in seeds]
        con = np.mean([r["contact_seconds"] for r in R]); pk = np.mean([r["peak_contact_force_N"] for r in R]); vis = np.mean([r["target_visible_pct"] for r in R])
        cr = sum(1 for r in R if r["crashed_at_s"] is not None)
        cc = per_seed(rows, arm, "crossed_clean") if all("crossed_clean" in r for r in R) else {}
        kc = sum(1 for s in seeds if cc.get(s, 0) >= 0.5); pc, lc, hc = wilson(kc, len(seeds)) if cc else (float("nan"),) * 3
        pre = np.mean([r.get("contact_before_barrier_s", float("nan")) for r in R])
        print(f"{arm:18s} {len(seeds):5d} {100*pr:5.0f}% [{100*lo:3.0f},{100*hi:3.0f}] {100*pc:5.0f}% [{100*lc:3.0f},{100*hc:3.0f}] {np.median(st):7.1f} [{np.percentile(st,25):.0f},{np.percentile(st,75):.0f}] {pre:10.2f} {con:9.2f} {vis:6.1f} {cr:4d}/{len(R)}")
    print("\npaired-by-seed differences (mean over seeds, 95% bootstrap):")
    for key, lab in (("stations_cleared", "stations"), ("crossed_barrier", "P(cross)"), ("crossed_clean", "P(clean)"), ("contact_seconds", "contact s"), ("target_visible_pct", "vis %")):
        for x, y in [("jev", "published_baseline"), ("climb_rule", "heuristic"), ("jev", "heuristic"), ("jev", "climb_rule"), ("jev", "jev_noclimb"), ("jev_noclimb", "heuristic"), ("heuristic", "published_baseline")]:
            if x in arms and y in arms:
                m, lo, hi, n = boot_diff(per_seed(rows, x, key), per_seed(rows, y, key)); print(f"  {lab:10s} {x:12s} − {y:12s} = {m:+7.2f}  [{lo:+.2f}, {hi:+.2f}]  n={n}")
    print("\nvariance decomposition (within-seed across repeats vs between-seed), stations_cleared:")
    for arm in arms:
        vd = variance_decomposition(rows, arm, "stations_cleared")
        if vd: print(f"  {arm:12s} within {vd[0]:.3f}  between {vd[1]:.3f}  → seed share {vd[1]/(vd[0]+vd[1]+1e-12):.2f}")
    if a.fig:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4.4), dpi=150); cols = {"published_baseline": "#bbbbbb", "heuristic": "#8a8aa0", "climb_rule": "#c8a03c", "jev": "#6ad08a", "jev_noclimb": "#2f7a48"}
        for arm in arms:
            R = [r for r in rows if r["arm"] == arm]; seeds = sorted(set(r["seed"] for r in R))
            xs = [np.mean([r["contact_seconds"] for r in R if r["seed"] == s]) for s in seeds]; ys = [np.mean([r["stations_cleared"] for r in R if r["seed"] == s]) / 6 * 100 for s in seeds]
            ax.scatter(xs, ys, s=18, alpha=.55, color=cols.get(arm, "#444"), label=f"{arm} (n={len(seeds)} seeds)")
            ax.scatter([np.mean(xs)], [np.mean(ys)], s=160, marker="X", color=cols.get(arm, "#444"), edgecolor="black", zorder=5)
        ax.set_xlabel("contact-seconds per episode (safety; lower is better)"); ax.set_ylabel("course completed (% of 6 stations)")
        ax.set_title("Closed loop: progress vs contact, per seed (X = arm mean)", fontsize=10); ax.legend(fontsize=8, frameon=False); ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout(); plt.savefig(a.fig, bbox_inches="tight"); print("figure:", a.fig)
if __name__ == "__main__": main()

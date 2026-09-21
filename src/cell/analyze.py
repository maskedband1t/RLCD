"""Pre-specified analysis for E71. Unit = seed. Paired-by-seed differences with a cluster bootstrap over seeds;
Wilson intervals for proportions; per-event breakdown for the unanticipated bank; the (violations, operator-seconds) plane."""
import json, sys, math, random, collections
import numpy as np

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0, 0)
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (p, c - h, c + h)

def boot_diff(a, b, n=5000, seed=0):
    """Paired difference of per-seed means, cluster bootstrap over seeds."""
    rng = random.Random(seed); keys = sorted(set(a) & set(b)); diffs = [a[k] - b[k] for k in keys]
    if not diffs: return (float('nan'),) * 3
    bs = []
    for _ in range(n):
        s = [diffs[rng.randrange(len(diffs))] for _ in diffs]; bs.append(sum(s) / len(s))
    bs.sort(); return (sum(diffs) / len(diffs), bs[int(0.025 * n)], bs[int(0.975 * n)])

def load(paths):
    rows = []
    for p in paths:
        for line in open(p):
            line = line.strip()
            if line: rows.append(json.loads(line))
    return rows

def main(paths):
    rows = load(paths); arms = sorted({r["arm"] for r in rows}, key=lambda a: ["greedy", "rules", "lexical", "rules_ask", "jev"].index(a) if a in ["greedy", "rules", "lexical", "rules_ask", "jev"] else 9)
    by = {a: {r["seed"]: r for r in rows if r["arm"] == a} for a in arms}
    print(f"{'arm':<12} {'seeds':>5} {'parts correct':>22} {'viol/ep':>8} {'unant ok':>14} {'hand s':>7} {'op s':>6} {'asks':>5} {'broken':>6} {'t s':>6} {'calls':>5}")
    for a in arms:
        R = list(by[a].values()); n = len(R)
        k = sum(r["parts_correct"] for r in R); N = sum(r["n_parts"] for r in R); p, lo, hi = wilson(k, N)
        un = [r["unanticipated_correct"] for r in R if r["unanticipated_correct"] is not None]
        uk = sum(un); up, ulo, uhi = wilson(uk, len(un))
        print(f"{a:<12} {n:>5} {k:>4}/{N:<4} {100*p:5.1f}% [{100*lo:4.1f},{100*hi:4.1f}] {np.mean([r['violations'] for r in R]):8.2f} {uk:>3}/{len(un):<3} {100*up:4.0f}% [{100*ulo:3.0f},{100*uhi:3.0f}] {np.mean([r['person_contact_s'] for r in R]):7.2f} {np.mean([r['operator_seconds'] for r in R]):6.1f} {np.mean([r['n_asks'] for r in R]):5.1f} {np.mean([r['broken'] for r in R]):6.2f} {np.mean([r['duration_s'] for r in R]):6.1f} {np.mean([r.get('jev_calls',0) for r in R]):5.1f}")
    print("\nUnanticipated bank, correct by event type (seeds with that event):")
    kinds = sorted({r["unanticipated"] for r in rows})
    print(f"{'arm':<12}" + "".join(f"{k:>18}" for k in kinds))
    for a in arms:
        cells = []
        for k in kinds:
            R = [r for r in by[a].values() if r["unanticipated"] == k and r["unanticipated_correct"] is not None]
            cells.append(f"{sum(r['unanticipated_correct'] for r in R):>3}/{len(R):<3}" if R else "   -   ")
        print(f"{a:<12}" + "".join(f"{c:>18}" for c in cells))
    print("\nPaired-by-seed differences in parts-correct fraction (cluster bootstrap over seeds, 95% CI):")
    frac = {a: {s: r["parts_correct"] / r["n_parts"] for s, r in by[a].items()} for a in arms}
    for a, b in [("jev", "lexical"), ("jev", "rules"), ("lexical", "rules"), ("rules", "greedy"), ("oracle", "jev")]:
        if a in frac and b in frac:
            m, lo, hi = boot_diff(frac[a], frac[b]); print(f"  {a:>8} - {b:<8}: {100*m:+6.1f} points  [{100*lo:+5.1f}, {100*hi:+5.1f}]")
    print("\nOperating plane (mean violations per episode vs mean operator seconds), one point per arm:")
    for a in arms:
        R = list(by[a].values()); print(f"  {a:<12} viol {np.mean([r['violations'] for r in R]):5.2f}  op-s {np.mean([r['operator_seconds'] for r in R]):6.1f}  share of episode {100*np.mean([r['operator_seconds']/max(r['duration_s'],1) for r in R]):4.1f}%")


def by_wording(paths, arm="jev"):
    rows = [r for r in load(paths) if r["arm"] == arm and r["unanticipated_correct"] is not None and r["unanticipated"] not in ("precedence",)]
    tab = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        t = tab[(r["unanticipated"], r["wording"])]; t[0] += int(r["unanticipated_correct"]); t[1] += 1
    print(f"\n{arm}: unanticipated correct by (event, wording index) — wording 0 is the one the lexical regexes were written from")
    for k in sorted(tab): print(f"  {k[0]:<18} w{k[1]}: {tab[k][0]}/{tab[k][1]}")

if __name__ == "__main__":
    main(sys.argv[1:])
    for arm in ("jev", "lexical"): by_wording(sys.argv[1:], arm)

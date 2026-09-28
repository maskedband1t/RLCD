"""S1-E9 paired analysis. Written before the sweep finished, so the estimator is not chosen to suit
the numbers. Scored per the pre-registration: paired on seed (method error 53), against bootstrap
intervals rather than point estimates (method error 56).

  PYTHONPATH=src python src/duck/s1e9_analysis.py --in results/duck/s1e9.jsonl
"""
import json, argparse, random
from collections import defaultdict

B = 10000
random.seed(7)


def boot(pairs, stat=lambda v: sum(v) / len(v)):
    """Bootstrap over SEEDS (the unit of pairing), not over decisions."""
    if not pairs:
        return (0.0, 0.0, 0.0)
    n = len(pairs)
    out = []
    for _ in range(B):
        s = [pairs[random.randrange(n)] for _ in range(n)]
        out.append(stat(s))
    out.sort()
    return (stat(pairs), out[int(0.025 * B)], out[int(0.975 * B)])


def fmt(t, unit=""):
    p, lo, hi = t
    star = "" if (lo <= 0 <= hi) else "  *"
    return f"{p:+.3f} [{lo:+.3f}, {hi:+.3f}]{unit}{star}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="results/duck/s1e9.jsonl")
    a = ap.parse_args()

    # cell[(mode, budget)][seed] = episode record
    cell = defaultdict(dict)
    for line in open(a.inp):
        r = json.loads(line)
        cell[(r["mode"], r["budget"])][r["seed"]] = r

    modes = sorted({m for m, _ in cell})
    budgets = sorted({b for _, b in cell})
    print(f"cells: {len(cell)}  modes={modes}  budgets={budgets}")

    def per_seed(mode, bud, metric):
        d = cell.get((mode, bud), {})
        out = {}
        for s, r in d.items():
            if metric == "acc_rate":
                out[s] = r["acceptable_decisions"] / max(r["decisions"], 1)
            elif metric == "fell":
                out[s] = float(r["fell"])
            elif metric == "viol":
                out[s] = float(r["violations"])
            elif metric == "event_ok":
                out[s] = float(r["event_correct"])
            elif metric == "decisions":
                out[s] = float(r["decisions"])
        return out

    def paired(mode_a, bud_a, mode_b, bud_b, metric):
        A, Bd = per_seed(mode_a, bud_a, metric), per_seed(mode_b, bud_b, metric)
        seeds = sorted(set(A) & set(Bd))
        return [A[s] - Bd[s] for s in seeds], len(seeds)

    # ---------- descriptive, with the length confound made visible ----------
    print("\n=== per-cell summary (mean of PER-SEED rates, not a ratio of sums) ===")
    print(f"{'mode':<10}{'N':>4}{'acc_rate':>12}{'fell':>8}{'viol':>8}{'event_ok':>10}{'decisions':>11}")
    for m in modes:
        for b in budgets:
            if (m, b) not in cell:
                continue
            ar = list(per_seed(m, b, "acc_rate").values())
            fe = list(per_seed(m, b, "fell").values())
            vi = list(per_seed(m, b, "viol").values())
            eo = list(per_seed(m, b, "event_ok").values())
            de = list(per_seed(m, b, "decisions").values())
            if not ar:
                continue
            f = lambda v: sum(v) / len(v)
            print(f"{m:<10}{b:>4}{f(ar):>12.3f}{f(fe):>8.2f}{f(vi):>8.2f}{f(eo):>10.2f}{f(de):>11.1f}")

    # ---------- P1: is the control flat in N? ----------
    print("\n=== P1 · random must be FLAT in N (a non-flat control voids the run) ===")
    for b in budgets[1:]:
        for metric in ("acc_rate", "fell"):
            d, n = paired("random", b, "random", budgets[0], metric)
            if d:
                print(f"  random N={b:<3} minus N={budgets[0]}   {metric:<9} n={n:<3} {fmt(boot(d))}")

    # ---------- P2/P4: selection rules against the control, at matched budget ----------
    print("\n=== P2/P4 · each rule minus random, at the SAME budget (paired on seed) ===")
    for m in [x for x in modes if x != "random"]:
        for b in budgets:
            if (m, b) not in cell:
                continue
            for metric in ("acc_rate", "fell"):
                d, n = paired(m, b, "random", b, metric)
                if d:
                    print(f"  {m:<10} N={b:<3} {metric:<9} n={n:<3} {fmt(boot(d))}")
        print()

    # ---------- P3: does selfscore saturate? ----------
    print("=== P3 · selfscore saturation (N=15 minus N=6) ===")
    for metric in ("acc_rate", "fell"):
        d, n = paired("selfscore", budgets[-1], "selfscore", 6, metric)
        if d:
            print(f"  {metric:<9} n={n:<3} {fmt(boot(d))}")

    # ---------- P5: how much headroom is left above the best real judge? ----------
    print("\n=== P5 · oracle minus selfscore (headroom left to a better scorer) ===")
    for b in budgets:
        for metric in ("acc_rate", "fell"):
            d, n = paired("oracle", b, "selfscore", b, metric)
            if d:
                print(f"  N={b:<3} {metric:<9} n={n:<3} {fmt(boot(d))}")

    print("\n  * = 95% bootstrap interval excludes zero. Anything without a star is NOT a result.")


if __name__ == "__main__":
    main()

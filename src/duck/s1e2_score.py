"""Score S1-E2 against its pre-registration. Noise floor first, pairing regime second,
arms third. Written while the run was still executing, so it cannot be tuned to the result."""
import json, sys, argparse
import numpy as np
from collections import defaultdict


def load(p):
    return [json.loads(l) for l in open(p)]


def boot(v, n=4000, seed=0):
    v = np.asarray([x for x in v if x is not None and np.isfinite(x)], float)
    if v.size < 2: return (float('nan'), float('nan'))
    r = np.random.default_rng(seed)
    m = v[r.integers(0, v.size, size=(n, v.size))].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("path"); a = ap.parse_args()
    rows = load(a.path)
    by = defaultdict(dict)
    for r in rows: by[r["mode"]][r["seed"]] = r
    modes = [m for m in ("none", "exact", "tolerance", "calibrated", "random") if m in by]
    base = by["none"]

    print("=== NOISE FLOOR (arm U, seed-to-seed) ===")
    for k in ("violations", "near_contacts", "operator_seconds", "t_end", "decisions"):
        v = [base[s][k] for s in base]
        print(f"  {k:<18} mean {np.mean(v):7.2f}  sd {np.std(v):6.2f}  95% CI of mean {boot(v)}")

    print("\n=== PAIRING REGIME (arm U: handled vs missed episode time) ===")
    hit = [base[s]["t_end"] for s in base if base[s]["event_correct"]]
    mis = [base[s]["t_end"] for s in base if not base[s]["event_correct"]]
    print(f"  event_correct  n={len(hit):<3} mean t_end {np.mean(hit) if hit else float('nan'):6.2f}")
    print(f"  missed         n={len(mis):<3} mean t_end {np.mean(mis) if mis else float('nan'):6.2f}")
    if hit and mis:
        gap = abs(np.mean(mis) - np.mean(hit))
        print(f"  gap {gap:.2f}s -> {'EMBODIED regime: pairing is load-bearing' if gap > 5 else 'DECISION-LEVEL regime: pairing matters little'}")

    print("\n=== ARMS ===")
    hdr = f"{'mode':<12}{'calls':>7}{'saved%':>8}{'dec':>6}{'ok%':>7}{'viol':>6}{'near':>6}{'fell':>6}{'op_s':>7}{'goal%':>7}{'evOK%':>7}"
    print(hdr); print("-" * len(hdr))
    ref_calls = np.mean([base[s]["calls"] for s in base])
    for m in modes:
        d = by[m]; seeds = sorted(set(d) & set(base))
        calls = np.mean([d[s]["calls"] for s in seeds])
        print(f"{m:<12}{calls:>7.1f}{100*(1-calls/ref_calls):>8.1f}"
              f"{np.mean([d[s]['decisions'] for s in seeds]):>6.1f}"
              f"{100*np.mean([d[s]['acceptable_decisions']/max(d[s]['decisions'],1) for s in seeds]):>7.1f}"
              f"{np.mean([d[s]['violations'] for s in seeds]):>6.2f}"
              f"{np.mean([d[s]['near_contacts'] for s in seeds]):>6.2f}"
              f"{np.mean([int(d[s]['fell']) for s in seeds]):>6.2f}"
              f"{np.mean([d[s]['operator_seconds'] for s in seeds]):>7.2f}"
              f"{100*np.mean([int(d[s]['goal_reached']) for s in seeds]):>7.1f}"
              f"{100*np.mean([int(d[s]['event_correct']) for s in seeds]):>7.1f}")

    print("\n=== PAIRED vs U (per seed; CI excluding 0 = outside the floor) ===")
    for m in modes[1:]:
        d = by[m]; seeds = sorted(set(d) & set(base))
        print(f"  -- {m} (n={len(seeds)})")
        for k in ("violations", "near_contacts", "operator_seconds", "acceptable_decisions"):
            diff = [d[s][k] - base[s][k] for s in seeds]
            lo, hi = boot(diff)
            flag = "" if (lo <= 0 <= hi) else "  <-- outside floor"
            print(f"     {k:<20} {np.mean(diff):+7.3f}  [{lo:+.3f},{hi:+.3f}]{flag}")
        both = [s for s in seeds if d[s]["goal_reached"] and base[s]["goal_reached"]]
        if both:
            dt = [d[s]["t_end"] - base[s]["t_end"] for s in both]
            print(f"     t_end (paired, both reached goal, n={len(both)}) {np.mean(dt):+7.2f}s  {boot(dt)}")
            allt = np.mean([d[s]["t_end"] for s in seeds]) - np.mean([base[s]["t_end"] for s in seeds])
            print(f"     t_end (UNPAIRED, fleet cost)                  {allt:+7.2f}s")


if __name__ == "__main__":
    main()

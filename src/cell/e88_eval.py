"""E88 (A4 fast-confirm) evaluation: per-arm means, paired-by-seed cluster bootstrap for confirm vs gate, the
operating plane, the precedence seeds on the notes bank, and the veto-miss sensitivity arm."""
import json, sys, collections, numpy as np

def load(path):
    return [json.loads(l) for l in open(path) if l.strip()]

def by_arm(rows):
    d = collections.defaultdict(dict)
    for r in rows: d[r["arm"]][r["seed"]] = r
    return d

def boot(a, b, key, n=5000, seed=0):
    """paired-by-seed difference of means (a - b) with cluster bootstrap over seeds."""
    seeds = sorted(set(a) & set(b)); rng = np.random.default_rng(seed)
    da = np.array([a[s][key] for s in seeds], float); db = np.array([b[s][key] for s in seeds], float); diff = da - db
    bs = [diff[rng.integers(0, len(seeds), len(seeds))].mean() for _ in range(n)]
    return diff.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5), len(seeds)

def table(d, arms):
    print(f"{'arm':<16}{'n':>4}{'correct':>9}{'viol/ep':>9}{'hazard':>8}{'broken':>8}{'unant ok':>10}{'op s':>7}{'asks':>6}{'conf':>6}{'veto':>6}{'missed':>7}{'calls':>7}")
    for a in arms:
        if a not in d: continue
        R = list(d[a].values()); n = len(R)
        un = [r["unanticipated_correct"] for r in R if r["unanticipated_correct"] is not None]
        print(f"{a:<16}{n:>4}{np.mean([r['parts_correct']/r['n_parts'] for r in R])*100:>8.1f}%{np.mean([r['violations'] for r in R]):>9.2f}{np.mean([r['hazard_misplaced'] for r in R]):>8.2f}{np.mean([r['broken'] for r in R]):>8.2f}"
              f"{(np.mean(un)*100 if un else float('nan')):>9.0f}%{np.mean([r['operator_seconds'] for r in R]):>7.1f}{np.mean([r['n_asks'] for r in R]):>6.2f}{np.mean([r.get('n_confirms',0) for r in R]):>6.2f}{np.mean([r.get('n_vetoes',0) for r in R]):>6.2f}{np.mean([r.get('n_veto_missed',0) for r in R]):>7.2f}{np.mean([r.get('jev_calls',0) for r in R]):>7.1f}")

def main():
    U = by_arm(load("results/cell/e88_unflagged.jsonl")); N = by_arm(load("results/cell/e88_notes.jsonl")); M = by_arm(load("results/cell/e88_unflagged_miss25.jsonl"))
    print("=== unflagged bank, seeds 0-39"); table(U, ["jev_gate0.6", "jev_gate0.7", "jev_gate0.8", "jev_confirm0.6", "jev_confirm0.7", "jev_confirm0.8"])
    print("\n=== notes bank, seeds 0-39"); table(N, ["jev_gate0.7", "jev_confirm0.7"])
    print("\n=== unflagged, veto-miss 25 %"); table(M, ["jev_confirm0.7"])
    print("\n=== paired-by-seed differences (confirm - gate), cluster bootstrap 95 %")
    for tau in ["0.6", "0.7", "0.8"]:
        a, b = U.get(f"jev_confirm{tau}"), U.get(f"jev_gate{tau}")
        if not a or not b: continue
        for key, lab in [("violations", "violations/ep"), ("operator_seconds", "operator s"), ("parts_correct", "parts correct"), ("broken", "broken")]:
            m, lo, hi, n = boot(a, b, key); print(f"  tau {tau} {lab:<14} {m:+7.2f}  [{lo:+6.2f}, {hi:+6.2f}]  n={n}")
        ratio = np.mean([r["operator_seconds"] for r in a.values()]) / max(1e-9, np.mean([r["operator_seconds"] for r in b.values()])); print(f"  tau {tau} operator-time ratio confirm/gate = {ratio:.2f}")
    print("\n=== P88.1 primary: confirm0.7 vs gate0.7 (unflagged)")
    a, b = U["jev_confirm0.7"], U["jev_gate0.7"]
    dv = np.mean([r["violations"] for r in a.values()]) - np.mean([r["violations"] for r in b.values()]); ratio = np.mean([r["operator_seconds"] for r in a.values()]) / np.mean([r["operator_seconds"] for r in b.values()])
    print(f"  violations diff {dv:+.2f} (held if <= +0.10; falsified if >= +0.25) | operator-time ratio {ratio:.2f} (held if <= .40; falsified if > .60)")
    un = np.mean([r["unanticipated_correct"] for r in a.values() if r["unanticipated_correct"] is not None]); print(f"  P88.2 unanticipated-correct confirm0.7 = {un:.2f} (held if >= .65)")
    print("\n=== P88.3 notes bank, precedence seeds (heavy fragile part; broken count)")
    for arm in ["jev_gate0.7", "jev_confirm0.7"]:
        R = [r for r in N[arm].values() if r["unanticipated"] == "precedence"]
        print(f"  {arm:<16} precedence seeds {len(R)} | broken total {sum(r['broken'] for r in R)} | saved {sum(1 for r in R if r['broken']==0)}/{len(R)} | unanticipated ok {sum(1 for r in R if r['unanticipated_correct'])}/{len(R)} | op s {np.mean([r['operator_seconds'] for r in R]):.1f}")
    print("\n=== P88.4 sensitivity: confirm0.7 miss25 vs confirm0.7 (unflagged)")
    m, lo, hi, n = boot(M["jev_confirm0.7"], U["jev_confirm0.7"], "violations"); print(f"  violations diff {m:+.2f} [{lo:+.2f}, {hi:+.2f}] (held if <= +0.15) | missed vetoes/ep {np.mean([r['n_veto_missed'] for r in M['jev_confirm0.7'].values()]):.2f}")
    print("\n=== P88.5 operating plane (unflagged): violations vs operator s")
    for arm in ["jev_gate0.6", "jev_gate0.7", "jev_gate0.8", "jev_confirm0.6", "jev_confirm0.7", "jev_confirm0.8"]:
        R = list(U[arm].values()); print(f"  {arm:<16} viol {np.mean([r['violations'] for r in R]):.2f}  op-s {np.mean([r['operator_seconds'] for r in R]):.1f}")
    # where does the confirm arm's operator time go?
    print("\n=== operator-time decomposition, confirm0.7 (unflagged): asks x4 + confirms x1 + vetoes x4")
    R = list(U["jev_confirm0.7"].values()); print(f"  asks {np.mean([r['n_asks'] for r in R]):.2f}/ep -> {4*np.mean([r['n_asks'] for r in R]):.1f} s | confirms {np.mean([r['n_confirms'] for r in R]):.2f}/ep -> {np.mean([r['n_confirms'] for r in R]):.1f} s | vetoes {np.mean([r['n_vetoes'] for r in R]):.2f}/ep -> {4*np.mean([r['n_vetoes'] for r in R]):.1f} s")
    G = list(U["jev_gate0.7"].values()); print(f"  gate0.7 for comparison: asks {np.mean([r['n_asks'] for r in G]):.2f}/ep -> {4*np.mean([r['n_asks'] for r in G]):.1f} s")
    # which sources did confirms come from: model-chosen asks vs gated
    srcs = collections.Counter()
    for r in R:
        for e in r["log"]:
            if str(e[1]).startswith("confirm:"): srcs["confirm"] += 1
            elif e[1] == "ask_operator": srcs["ask (model-chosen or replay-miss)"] += 1
    print("  decision log counts, confirm0.7:", dict(srcs))
    print("E88_EVAL_DONE")

if __name__ == "__main__": main()

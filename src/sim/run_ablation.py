"""python -m sim.run_ablation --arms heuristic climb_rule --seeds 0-39 --repeats 3 --out results/sim/x.jsonl"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sim  # noqa: sets up third_party path
from sim.harness import episode
def parse_seeds(s): 
    out = []
    for part in s.split(","):
        if "-" in part: a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out
if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--arms", nargs="+", default=["heuristic"]); p.add_argument("--seeds", default="0")
    p.add_argument("--repeats", type=int, default=1); p.add_argument("--seconds", type=float, default=65.0); p.add_argument("--fast", action="store_true")
    p.add_argument("--no-randomize", action="store_true"); p.add_argument("--latency", type=float, default=0.11); p.add_argument("--cache", default=None)
    p.add_argument("--record", default=None); p.add_argument("--out", required=True)
    p.add_argument("--corrupt", default=None, choices=[None, "range", "dropout", "phantom", "stale"]); p.add_argument("--corrupt-rate", type=float, default=0.0)
    p.add_argument("--corrupt-site", default="model", choices=["model", "all"]); p.add_argument("--report-uncertainty", action="store_true")
    p.add_argument("--gate-risk", type=float, default=None); p.add_argument("--gate-lost", type=float, default=0.7); p.add_argument("--gate-conf", type=float, default=None)
    p.add_argument("--handoff-window", type=float, default=3.0); p.add_argument("--handoff-cooldown", type=float, default=2.0)
    a = p.parse_args()
    with open(a.out, "a") as f:
        for seed in parse_seeds(a.seeds):
            for rep in range(a.repeats):
                for arm in a.arms:
                    r = episode(seed, arm, a.seconds, realtime=(False if a.fast else None), randomize=not a.no_randomize,
                                latency=a.latency, cache=a.cache, record=a.record, corrupt=a.corrupt, corrupt_rate=a.corrupt_rate,
                                corrupt_site=a.corrupt_site, report_uncertainty=a.report_uncertainty, gate_risk=a.gate_risk, gate_lost=a.gate_lost,
                                gate_conf=a.gate_conf, handoff_window=a.handoff_window, handoff_cooldown=a.handoff_cooldown); r["repeat"] = rep
                    f.write(json.dumps(r) + "\n"); f.flush()
                    print(f"seed {seed} rep {rep} {arm:12s} stations {r['stations_cleared']} x={r['max_x_m']:5.1f} contact {r['contact_seconds']:5.2f}s vis {r['target_visible_pct']:5.1f}% op {r.get('operator_seconds',0):5.1f}s/{r.get('n_handoffs',0)} wall {r['wall_s']}s", flush=True)

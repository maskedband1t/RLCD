"""Pre-specified H5 analysis. Outcome vs corruption per channel/rate/arm; for Jev: does mean risk rise with corruption only when uncertainty is reported?
python -m sim.analyze_h5 results/sim/h5_det.jsonl results/sim/h5_jev.jsonl --baseline results/sim/nojev_40x1_v2.jsonl results/sim/jev_live_40.jsonl"""
import json, argparse, collections, numpy as np
def load(paths):
    rows = []
    for p in paths:
        try:
            for l in open(p): rows.append(json.loads(l))
        except FileNotFoundError: pass
    return rows
def main():
    p = argparse.ArgumentParser(); p.add_argument("paths", nargs="+"); p.add_argument("--baseline", nargs="*", default=[]); a = p.parse_args()
    R = load(a.paths); B = load(a.baseline)
    base = collections.defaultdict(list)
    for r in B: base[r["arm"]].append(r)
    print(f"{'arm':10s} {'channel':8s} {'rate':>5s} {'unc':>4s} {'n':>3s} {'completion %':>13s} {'clean %':>8s} {'contact s':>10s} {'frames corrupted %':>18s}")
    for arm in sorted(base):
        b = base[arm][:20]
        if b: print(f"{arm:10s} {'none':8s} {'0':>5s} {'-':>4s} {len(b):3d} {np.mean([r['stations_cleared']/6*100 for r in b]):13.0f} {100*np.mean([r.get('crossed_clean',False) for r in b]):8.0f} {np.mean([r['contact_seconds'] for r in b]):10.2f} {0:18.0f}")
    cells = collections.defaultdict(list)
    for r in R:
        c = r.get("corrupt") or {}; cells[(r["arm"], c.get("channel"), c.get("rate"), c.get("report_uncertainty"))].append(r)
    for (arm, ch, rate, unc), rows in sorted(cells.items(), key=lambda kv: (kv[0][0], str(kv[0][1]), kv[0][2] or 0, bool(kv[0][3]))):
        print(f"{arm:10s} {str(ch):8s} {rate:5.1f} {('yes' if unc else 'no'):>4s} {len(rows):3d} {np.mean([r['stations_cleared']/6*100 for r in rows]):13.0f} {100*np.mean([r.get('crossed_clean',False) for r in rows]):8.0f} {np.mean([r['contact_seconds'] for r in rows]):10.2f} {np.mean([(r.get('corrupt') or {}).get('frames_corrupted_pct', 0) for r in rows]):18.0f}")
    print("\nP5.1/P5.2 note: Jev's per-frame risk is not logged per episode in this harness; the test of 'risk tracks corruption' uses the handoff log when gated,"
          " otherwise compare completion/contact with vs without uncertainty fields (P5.2 predicts the degradation at least halves).")
if __name__ == "__main__": main()

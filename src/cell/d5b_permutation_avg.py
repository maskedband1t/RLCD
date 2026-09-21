"""D5b · Permutation averaging below the gate threshold (pre-registered in the notebook).

On the D5 decisions with recorded confidence < .7, ask Jev with k = 4 seeded random option orders, average the
probabilities across orders, and compare the averaged argmax against the single-order (D5 repeat) argmax on the
ground truth's acceptable set. Bands: recorded confidence < .5 and [.5, .7)."""
import json, os, sys, time, random, argparse
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.policies import Jev, CAPABILITIES
from cell.decision_eval import seed_index, signature, acceptable, auroc
from cell.d5_option_order import ask

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--d5", default="results/cell/d5_option_order.jsonl"); ap.add_argument("--records", default="results/cell/e71_jev_record.jsonl")
    ap.add_argument("--k", type=int, default=4); ap.add_argument("--out", default="results/cell/d5b_permutation_avg.jsonl"); ap.add_argument("--eval-only", action="store_true"); a = ap.parse_args()
    d5 = {json.loads(l)["key"]: json.loads(l) for l in open(a.d5) if l.strip()}
    recs = {r["key"]: r for r in (json.loads(l) for l in open(a.records) if l.strip()) if r["key"] in d5}
    sel = [k for k, v in d5.items() if v["recorded"]["confidence"] < 0.7 and "choice" in v["repeat"]]
    print(f"D5 decisions {len(d5)} | below .7: {len(sel)}", flush=True)
    if not a.eval_only:
        pol = Jev(record=[], replay=None); out = open(a.out, "w")
        for i, key in enumerate(sel):
            r = recs[key]; state = r["state"] if "capabilities" in r["state"] else {"capabilities": CAPABILITIES, **r["state"]}
            items = list(r["options"].items()); rng = random.Random(key); perms = []
            for j in range(a.k):
                order = items[:]; rng.shuffle(order); ans = ask(pol, state, dict(order)); perms.append({"order": [o[0] for o in order], "answer": ans})
            out.write(json.dumps({"key": key, "perms": perms}) + "\n"); out.flush()
            if (i + 1) % 20 == 0: print(f"{i+1}/{len(sel)}", flush=True)
        out.close()
    rows = {json.loads(l)["key"]: json.loads(l) for l in open(a.out) if l.strip()}
    idx = seed_index(280)
    bands = {"<.5": [], "[.5,.7)": []}
    for key, row in rows.items():
        r = recs[key]; sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec)
        good = [p["answer"] for p in row["perms"] if "choice" in p["answer"]]
        if len(good) < 2: continue
        keys = list(r["options"].keys()); P = np.zeros(len(keys))
        for ans in good:
            for k_, v in ans["probabilities"].items():
                if k_ in keys: P[keys.index(k_)] += v / len(good)
        avg_choice = keys[int(P.argmax())]; avg_conf = float(P.max())
        single = d5[key]["repeat"]; band = "<.5" if d5[key]["recorded"]["confidence"] < 0.5 else "[.5,.7)"
        bands[band].append(dict(single_ok=single["choice"] in acc, single_conf=single["confidence"], avg_ok=avg_choice in acc, avg_conf=avg_conf,
                                perm_ok=np.mean([ans["choice"] in acc for ans in good]), recorded_ok=d5[key]["recorded"]["choice"] in acc, must_ask="ask_operator" in acc))
    for band, L in bands.items():
        if not L: continue
        s_ok = np.mean([x["single_ok"] for x in L]); a_ok = np.mean([x["avg_ok"] for x in L]); p_ok = np.mean([x["perm_ok"] for x in L]); r_ok = np.mean([x["recorded_ok"] for x in L])
        au_s = auroc([x["single_conf"] for x in L], [x["single_ok"] for x in L]); au_a = auroc([x["avg_conf"] for x in L], [x["avg_ok"] for x in L])
        rng = np.random.default_rng(0); d = np.array([x["avg_ok"] - x["single_ok"] for x in L], float); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)]
        print(f"band {band:8s} n {len(L):3d} | acceptable: recorded {r_ok:.1%} | single-order repeat {s_ok:.1%} | mean single permutation {p_ok:.1%} | permutation-averaged {a_ok:.1%} | avg - single {100*d.mean():+.1f} pts [{100*np.percentile(bs,2.5):+.1f}, {100*np.percentile(bs,97.5):+.1f}] | AUROC conf->acceptable single {au_s:.3f} averaged {au_a:.3f}")
    print("D5B_DONE", flush=True)

if __name__ == "__main__": main()

"""Fair 7B arms on a suite: constrained string scoring (+ temperature on a task split), yes/no heads, program arm.
python src/critic/run_baselines.py data/suites/e65-questions.json results/e65-baselines.json"""
import json, sys, os, math, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baselines import program_pick, constrained_scores, yesno_probs, softmax, fit_temperature, task_split
from e65_critic import auroc, ece
from mlx_lm import load
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"

def main(suite, out):
    qs = json.load(open(suite)); model, tok = load(M); t0 = time.time(); rows = {}
    for i, q in enumerate(qs):
        rows[q["id"]] = {"constrained": constrained_scores(model, tok, q), "yesno": yesno_probs(model, tok, q), "program": program_pick(q)}
        if i % 50 == 0: print(f"{i}/{len(qs)} {time.time()-t0:.0f}s", flush=True)
    json.dump(rows, open(out, "w"))
    # ---- analysis (calibration fit on a TASK split, evaluated on the other half)
    non_amb = [q for q in qs if q["type"] != "ambiguous_pair"]; fit, ev = task_split(non_amb, 0.5, 0)
    T = fit_temperature([rows[q["id"]]["constrained"] for q in fit], [q["truth"] for q in fit])
    def report(Q, name, T_):
        by = collections.defaultdict(list); conf = []; corr = []
        for q in Q:
            p = softmax(rows[q["id"]]["constrained"], T_); ch = max(p, key=p.get); ok = ch == q["truth"]
            by[q["type"]].append(ok); conf.append(p[ch]); corr.append(ok)
        wrong = [c for c, k in zip(conf, corr) if not k]; right = [c for c, k in zip(conf, corr) if k]
        print(f"  {name:28s} acc {100*sum(corr)/len(corr):5.1f}%  ECE(10 bins) {ece(conf, corr):.3f}  AUROC {auroc(conf, corr):.3f}  "
              f"conf wrong/right {sum(wrong)/max(1,len(wrong)):.2f}/{sum(right)/max(1,len(right)):.2f}  per-type " + " ".join(f"{k[:8]}={100*sum(v)/len(v):.0f}" for k, v in by.items()))
    print(f"\n=== {os.path.basename(suite)}: fitted T = {T:.2f} on {len(fit)} fit-split questions; evaluated on {len(ev)} ===")
    report(ev, "7B constrained, raw (T=1)", 1.0); report(ev, f"7B constrained, T={T:.2f}", T)
    prog = [rows[q["id"]]["program"] == q["truth"] for q in ev]; print(f"  {'program arm':28s} acc {100*sum(prog)/len(prog):5.1f}%")
    # yes/no gate: per-candidate P(yes) vs is-correct
    s = [rows[q["id"]]["yesno"][L] for q in ev for L in q["candidates"]]; l = [L == q["truth"] for q in ev for L in q["candidates"]]
    print(f"  {'7B yes/no gate (per-cand)':28s} AUROC {auroc(s, l):.3f}  ECE {ece(s, l):.3f}  mean P(yes) correct {sum(x for x,y in zip(s,l) if y)/max(1,sum(l)):.2f} vs wrong {sum(x for x,y in zip(s,l) if not y)/max(1,len(l)-sum(l)):.2f}")
    amb = [q for q in qs if q["type"] == "ambiguous_pair"]
    if amb:
        for T_, nm in ((1.0, "raw"), (T, f"T={T:.2f}")):
            mx = [max(softmax(rows[q["id"]]["constrained"], T_).values()) for q in amb]
            mass = [sum(softmax(rows[q["id"]]["constrained"], T_)[L] for L in q["acceptable"]) for q in amb]
            un = [max(softmax(rows[q["id"]]["constrained"], T_).values()) for q in ev]
            print(f"  ambiguous pairs, 7B {nm:8s}: mass on acceptable {sum(mass)/len(mass):.2f}  max-prob {sum(mx)/len(mx):.2f}  vs unambiguous {sum(un)/len(un):.2f}  ratio {sum(mx)/len(mx)/(sum(un)/len(un)):.2f}")
    print("DONE", flush=True)
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])

"""Format-artifact check for constrained string scoring: (a) candidates listed as bullets, score bare text;
(b) candidates listed 'A. text', score the letter-prefixed continuation 'A. text'. Compare to the letter-logit readout."""
import json, sys, os, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baselines import seq_logprob, softmax
from e65_critic import auroc, ece
from mlx_lm import load
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
def prompt(q, tok, bullets):
    steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])) or "  (none yet)"
    cands = "\n".join((f"  - {q['candidates'][L]}" if bullets else f"  {L}. {q['candidates'][L]}") for L in q["candidates"])
    user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\nSteps already completed (including any reported failure):\n{steps}\n"
            f"Candidate next steps:\n{cands}\nWhich candidate is the correct next step? " + ("Answer with the step text." if bullets else "Answer with the letter and the step text."))
    return tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)
def run(suite, out):
    qs = [q for q in json.load(open(suite)) if q["type"] != "ambiguous_pair"]; model, tok = load(M); rows = {}
    for i, q in enumerate(qs):
        pa = prompt(q, tok, True); pb = prompt(q, tok, False); ra = {}; rb = {}
        for L, c in q["candidates"].items():
            lp, n = seq_logprob(model, tok, pa, " " + c); ra[L] = lp / max(1, n)
            lp2, n2 = seq_logprob(model, tok, pb, f" {L}. {c}"); rb[L] = lp2 / max(1, n2)
        rows[q["id"]] = {"bullets": ra, "letter_prefixed": rb}
        if i % 100 == 0: print(f"{i}/{len(qs)}", flush=True)
    json.dump(rows, open(out, "w"))
    for name in ("bullets", "letter_prefixed"):
        corr = []; conf = []; by = collections.defaultdict(list)
        for q in qs:
            p = softmax(rows[q["id"]][name]); ch = max(p, key=p.get); ok = ch == q["truth"]; corr.append(ok); conf.append(p[ch]); by[q["type"]].append(ok)
        print(f"{os.path.basename(suite)} {name:16s} acc {100*sum(corr)/len(corr):5.1f}%  ECE {ece(conf, corr):.3f}  AUROC {auroc(conf, corr):.3f}  per-type " + " ".join(f"{k[:8]}={100*sum(v)/len(v):.0f}" for k, v in by.items()), flush=True)
if __name__ == "__main__":
    run("data/suites/e65-questions.json", "results/e65-readout-recheck.json"); run("data/suites/e65b-questions.json", "results/e65b-readout-recheck.json"); print("DONE")

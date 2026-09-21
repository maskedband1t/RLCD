"""E70 7B arms (letter readout + yes/no head) on the factorial critic suite. GPU."""
import json, sys, os, math, collections, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlx.core as mx
from mlx_lm import load
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
def main():
    items = json.load(open("data/suites/e70-factorial-critic.json")); model, tok = load(M); out = {}
    for q in items:
        steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])); cands = "\n".join(f"  {L}. {q['candidates'][L]}" for L in "ABCD")
        user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\nSteps already completed (including any status report):\n{steps}\n"
                f"Candidate next steps:\n{cands}\nWhich candidate is the correct next step? Answer with a single letter.")
        pr = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False) + "The correct next step is"
        lg = model(mx.array([tok.encode(pr)]))[0, -1, :].astype(mx.float32); lp = lg - mx.logsumexp(lg)
        probs = {L: sum(math.exp(float(lp[t])) for t in {tok.encode(" " + L, add_special_tokens=False)[-1], tok.encode(L, add_special_tokens=False)[-1]}) for L in "ABCD"}
        s = sum(probs.values()); probs = {k: v / s for k, v in probs.items()}; out[q["id"]] = {"choice": max(probs, key=probs.get), "probs": probs}
    json.dump(out, open("results/e70-7b-critic.json", "w"))
    acc = collections.defaultdict(list); paired = {"numeric": {}, "categorical": {}}
    for q in items:
        ok = out[q["id"]]["choice"] == q["truth"]; acc[(q["kind"], q["fmt"])].append(ok); paired[q["fmt"]][q["id"].rsplit("-", 1)[0]] = ok
    ids = sorted(set(paired["numeric"]) & set(paired["categorical"])); d = [int(paired["categorical"][i]) - int(paired["numeric"][i]) for i in ids]; rng = random.Random(0)
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(10000))
    print("  7B       " + "  ".join(f"{k[0]}/{k[1][:3]} {100*sum(v)/len(v):5.1f}%" for k, v in sorted(acc.items())) + f"   gain categorical−numeric {100*sum(d)/len(d):+.1f} pts [{100*bs[250]:+.1f},{100*bs[9750]:+.1f}] n={len(ids)}"); print("DONE")
if __name__ == "__main__": main()

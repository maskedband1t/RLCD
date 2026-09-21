"""D1 in the cell: a plain open LLM behind the same typed interface, scored on the recorded Jev decisions.
Letter readout: the state (compact render) and the lettered options in one prompt; next-token probabilities over the
letters give a distribution over options. Decision-level metrics as for Jev (acceptable / deferred / wrong, AUROC)."""
import json, sys, os, math, string, time, collections
import numpy as np
import mlx.core as mx
from mlx_lm import load
from .decision_eval import seed_index, signature, acceptable, auroc
from .owned_head import render_context
from .episodes import TASK

LETTERS = list(string.ascii_uppercase) + ["A" + c for c in string.ascii_uppercase]

def main(records, model_id="mlx-community/Qwen2.5-7B-Instruct-4bit", out=None, limit=None):
    model, tok = load(model_id); idx = seed_index()
    rows = [json.loads(l) for l in open(records)]
    if limit:
        import random; random.Random(20260918).shuffle(rows); rows = rows[:limit]   # seeded random subsample (declared deviation, see notebook D1-cell)
    letter_ids = {L: {tok.encode(" " + L, add_special_tokens=False)[-1], tok.encode(L, add_special_tokens=False)[-1]} for L in LETTERS}
    results = []; t0 = time.time()
    for n, r in enumerate(rows):
        keys = sorted(r["options"]); ctx = render_context(r["state"]); acc = acceptable(r["state"], idx[signature(r["state"]["parts"])][1])
        opts = "\n".join(f"  {LETTERS[i]}. {r['options'][k]}" for i, k in enumerate(keys))
        user = (f"You are the judgment layer of a sorting robot; code executes whatever you choose.\nTask: {TASK}\n\nCurrent facts:\n{ctx}\n\n"
                f"Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting.\nOptions:\n{opts}\nAnswer with the letter only.")
        pr = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False) + "The best action is"
        lg = model(mx.array([tok.encode(pr)]))[0, -1, :].astype(mx.float32); lp = lg - mx.logsumexp(lg)
        probs = {}
        for i, k in enumerate(keys):
            probs[k] = sum(math.exp(float(lp[t])) for t in letter_ids[LETTERS[i]])
        s = sum(probs.values()) or 1.0; probs = {k: v / s for k, v in probs.items()}
        choice = max(probs, key=probs.get); conf = probs[choice]
        ok = choice in acc; deferred = (not ok) and choice == "ask_operator"
        results.append(dict(choice=choice, confidence=conf, ok=ok, deferred=deferred, wrong=(not ok and not deferred), jev_choice=r["answer"]["choice"], jev_ok=r["answer"]["choice"] in acc))
        if n % 100 == 0: print(f"  {n}/{len(rows)}  {time.time()-t0:.0f}s", flush=True)
    if out: json.dump(results, open(out, "w"))
    ok = [x["ok"] for x in results]; wrong = [x["wrong"] for x in results]; conf = [x["confidence"] for x in results]
    print(f"{model_id}: decisions {len(results)}, acceptable {100*np.mean(ok):.1f}%, deferred {100*np.mean([x['deferred'] for x in results]):.1f}%, wrong {100*np.mean(wrong):.1f}%, AUROC(conf→not wrong) {auroc(conf, [not w for w in wrong]):.3f}")
    print(f"Jev on the same decisions: acceptable {100*np.mean([x['jev_ok'] for x in results]):.1f}%; agreement with Jev's choice {100*np.mean([x['choice']==x['jev_choice'] for x in results]):.1f}%")

if __name__ == "__main__":
    import argparse; ap = argparse.ArgumentParser(); ap.add_argument("records"); ap.add_argument("--model", default="mlx-community/Qwen2.5-7B-Instruct-4bit"); ap.add_argument("--out"); ap.add_argument("--limit", type=int)
    a = ap.parse_args(); main(a.records, a.model, a.out, a.limit)

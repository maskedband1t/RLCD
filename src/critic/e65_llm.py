"""E65 baseline: the planner's own logits. Qwen2.5-7B-Instruct 4-bit, same content, answer letter from logits."""
import json, sys, time, mlx.core as mx
from mlx_lm import load
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
def main():
    qs = json.load(open(sys.argv[1])); model, tok = load(M)
    letters = ["A", "B", "C", "D"]; lid = [tok.encode(" " + L, add_special_tokens=False)[-1] for L in letters]
    lid2 = [tok.encode(L, add_special_tokens=False)[-1] for L in letters]
    out = []
    for i, q in enumerate(qs):
        steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])) or "  (none yet)"
        cands = "\n".join(f"  {L}. {q['candidates'][L]}" for L in letters)
        user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\n"
                f"Steps already completed (including any reported failure):\n{steps}\n"
                f"Candidate next steps:\n{cands}\nWhich candidate is the correct next step? Answer with a single letter.")
        msgs = [{"role": "user", "content": user}]
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False) + "The correct next step is"
        ids = mx.array([tok.encode(prompt)]); t0 = time.time()
        logits = model(ids)[0, -1, :].astype(mx.float32)
        lp = mx.softmax(logits); p1 = [float(lp[t]) for t in lid]; p2 = [float(lp[t]) for t in lid2]
        pr = [a + b for a, b in zip(p1, p2)]; s = sum(pr); pr = [x / s for x in pr] if s > 0 else [0.25] * 4
        mx.eval(logits); secs = time.time() - t0
        probs = dict(zip(letters, pr)); ch = max(probs, key=probs.get)
        out.append(dict(id=q["id"], choice=ch, probs=probs, mass=s, secs=secs))
        if i % 50 == 0: print(f"{i}/{len(qs)} {ch} truth {q['truth']} P={probs[ch]:.2f} mass={s:.2f} {secs:.2f}s", flush=True)
    json.dump(out, open(sys.argv[2], "w")); print("DONE", flush=True)
if __name__ == "__main__": main()

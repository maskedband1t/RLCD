"""E65 baseline cross-check: let the 7B answer freely (greedy), parse the letter. Fair readout when letter-logit mass is thin."""
import json, re, sys, time
from mlx_lm import load, generate
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
def main():
    qs = json.load(open(sys.argv[1])); model, tok = load(M); out = []
    for i, q in enumerate(qs):
        steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])) or "  (none yet)"
        cands = "\n".join(f"  {L}. {q['candidates'][L]}" for L in "ABCD")
        user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\n"
                f"Steps already completed (including any reported failure):\n{steps}\n"
                f"Candidate next steps:\n{cands}\nWhich candidate is the correct next step? Answer with the letter only.")
        prompt = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)
        t0 = time.time(); txt = generate(model, tok, prompt=prompt, max_tokens=8, verbose=False); secs = time.time() - t0
        m = re.search(r"\b([ABCD])\b", txt); ch = m.group(1) if m else None
        out.append(dict(id=q["id"], choice=ch, text=txt.strip()[:40], secs=secs))
        if i % 100 == 0: print(f"{i}/{len(qs)} '{txt.strip()[:20]}' -> {ch} truth {q['truth']} {secs:.2f}s", flush=True)
    json.dump(out, open(sys.argv[2], "w")); print("DONE", flush=True)
if __name__ == "__main__": main()

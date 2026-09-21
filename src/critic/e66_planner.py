"""E66 planner: Qwen2.5-7B proposes next steps (6 sampled + 1 greedy) for real DROID tasks and prefixes."""
import json, random, re, sys, time
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler
sys.path.insert(0, "src"); from e65_critic import tasks, plan
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
def clean(t):
    t = t.strip().split("\n")[0]; t = re.sub(r"^\W*(next step|step \d+|\d+[.)]|[-*•])\s*[:.)-]?\s*", "", t, flags=re.I)
    t = re.sub(r"[\"'“”]", "", t).strip().rstrip(".").strip(); return " ".join(t.split()[:14])
def main(n_normal=100, n_fail=50, seed=0, out_path="notes/e66-planner.json", skip=0):
    rng = random.Random(seed); T = list(tasks().items()); random.Random(0).shuffle(T); T = T[skip:]; rng.shuffle(T); model, tok = load(M)
    samp = make_sampler(temp=1.0, top_p=0.95); greedy = make_sampler(temp=0.0)
    out = []; i = 0
    for kind, n in (("normal", n_normal), ("failure", n_fail)):
        for _ in range(n):
            t, (x, y, p) = T[i]; i += 1; P = plan(x, y, p)
            if kind == "normal":
                k = rng.choice([1, 2, 3, 4, 5, 6]); prefix = P[:k]
            else:
                k = rng.choice([3, 4])
                prefix = P[:2] + [f"{P[2]} — done; gripper reports: nothing held"] if k == 3 else P[:3] + [f"{P[3]} — done; gripper reports: nothing held; the {x} is no longer in the gripper"]
            steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(prefix))
            user = (f"You are the task planner for a robot arm with a two-finger gripper.\nTask: {t}\n"
                    f"Steps completed so far (with any status reports):\n{steps}\n"
                    "Propose the single next step for the robot as one short imperative phrase (under 12 words). Reply with the phrase only.")
            prompt = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)
            t0 = time.time(); g = clean(generate(model, tok, prompt=prompt, max_tokens=24, sampler=greedy, verbose=False))
            cands = []
            for _ in range(6):
                c = clean(generate(model, tok, prompt=prompt, max_tokens=24, sampler=samp, verbose=False))
                if c and c.lower() not in [d.lower() for d in cands]: cands.append(c)
            out.append(dict(id=len(out), kind=kind, task=t, x=x, y=y, k=k, prefix=prefix, greedy=g, candidates=cands[:5], secs=round(time.time() - t0, 1)))
            if len(out) % 25 == 1: print(f"{len(out)} {kind} k={k} greedy='{g}' cands={cands[:5]} {time.time()-t0:.1f}s", flush=True)
            json.dump(out, open(out_path, "w"), indent=0)
    print("DONE", flush=True)
if __name__ == "__main__":
    a = sys.argv[1:]; main(int(a[0]), int(a[1]), int(a[2]), a[3], int(a[4])) if a else main()

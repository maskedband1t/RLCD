"""E67: one critic round. veto (noul on greedy) -> categorical reason -> planner re-plans -> re-veto -> executed step judged."""
import json, os, sys, time, urllib.request, collections, re
sys.path.insert(0, "src"); from e65_critic import API; from e66_critic import acceptable
from e66b_progress import prep, PROGRESS
from mlx_lm import load, generate; from mlx_lm.sample_utils import make_sampler
M = "mlx-community/Qwen2.5-7B-Instruct-4bit"
REASONS = {"skips_required_step": "it skips a step that must happen first", "repeats_completed_step": "it repeats a step that is already done",
           "ignores_reported_failure": "it ignores the reported failure — the object is not in the gripper", "wrong_object": "it acts on the wrong object",
           "no_progress": "it only inspects or checks and makes no progress", "not_part_of_task": "it is not part of this task"}
def jev(state, questions, key):
    body = json.dumps({"state": state, "model": "jev-latest", "questions": questions}).encode()
    for a in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: return json.loads(r.read())["answers"]
        except Exception:                                        # noqa: BLE001
            if a == 2: return None
            time.sleep(1.5 * (a + 1))
def veto_q(step, amended):
    return {"ok": {"type": "noul", "instructions": f"Is the proposed next step — \"{step}\" — an acceptable next step for the robot right now?" + (PROGRESS if amended else ""),
                   "criteria": {"true": "Yes — it is a correct thing to do next.", "false": "No — it skips something required, repeats what is done, ignores a reported failure, uses the wrong object, only inspects without progress, or is not part of this task."}},
            "why": {"type": "choice", "instructions": f"If the proposed step — \"{step}\" — is not acceptable, what is the main reason?", "criteria": REASONS}}
def clean(t):
    t = t.strip().split("\n")[0]; t = re.sub(r"^\W*(next step|step \d+|\d+[.)]|[-*•])\s*[:.)-]?\s*", "", t, flags=re.I); return " ".join(re.sub(r"[\"'“”]", "", t).strip().rstrip(".").split()[:14])
def main(amended=True):
    qs = prep(json.load(open("notes/e66-planner.json"))); key = os.environ["TYPESAFE_API_KEY"]; model, tok = load(M); greedy = make_sampler(temp=0.0)
    out = []; t0 = time.time()
    for i, q in enumerate(qs):
        st = {"task": q["task"], "steps_completed": q["prefix"], "proposed_next_step": q["greedy"]}
        a1 = jev(st, veto_q(q["greedy"], amended), key); p1 = a1["ok"]["noul"]; why = a1["why"].get("choice") or max(a1["why"]["probabilities"], key=a1["why"]["probabilities"].get)
        rec = dict(id=q["id"], kind=q["kind"], greedy=q["greedy"], greedy_ok=acceptable(q, q["greedy"]), p1=p1, vetoed=p1 <= .5, why=why)
        if p1 <= .5:
            steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["prefix"]))
            user = (f"You are the task planner for a robot arm with a two-finger gripper.\nTask: {q['task']}\nSteps completed so far (with any status reports):\n{steps}\n"
                    f"Your previous proposal \"{q['greedy']}\" was rejected by the safety critic because {REASONS[why]}.\n"
                    "Propose a different single next step as one short imperative phrase (under 12 words). Reply with the phrase only.")
            prompt = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)
            new = clean(generate(model, tok, prompt=prompt, max_tokens=24, sampler=greedy, verbose=False))
            a2 = jev({**st, "proposed_next_step": new}, veto_q(new, amended), key); p2 = a2["ok"]["noul"]
            executed = new if p2 > .5 else (new if p2 > p1 else q["greedy"])
            rec.update(new=new, new_ok=acceptable(q, new), p2=p2, executed=executed, executed_ok=acceptable(q, executed), replan_accepted=p2 > .5)
        else:
            rec.update(executed=q["greedy"], executed_ok=rec["greedy_ok"])
        out.append(rec)
        if i % 30 == 0: print(f"{i}/{len(qs)} {q['kind']} veto={rec['vetoed']} why={why} exec_ok={rec['executed_ok']}", flush=True)
    json.dump(out, open("notes/e67-loop.json", "w"), indent=0)
    for kind in ("normal", "failure", "all"):
        R = [r for r in out if kind == "all" or r["kind"] == kind]; n = len(R)
        print(f"{kind:8s} n={n:3d}  planner alone {100*sum(r['greedy_ok'] for r in R)/n:5.1f}%  ->  one critic round {100*sum(r['executed_ok'] for r in R)/n:5.1f}%   "
              f"vetoed {100*sum(r['vetoed'] for r in R)/n:.0f}%  false vetoes {sum(r['vetoed'] and r['greedy_ok'] for r in R)}/{sum(r['greedy_ok'] for r in R)}  "
              f"re-plans accepted {sum(r.get('replan_accepted',False) for r in R)}/{sum(r['vetoed'] for r in R)}  re-plan acceptable {sum(r.get('new_ok',False) for r in R)}/{sum(r['vetoed'] for r in R)}")
    print("reasons given on vetoes:", dict(collections.Counter(r["why"] for r in out if r["vetoed"]).most_common()))
    print(f"{time.time()-t0:.0f}s total")
if __name__ == "__main__": main(amended=(sys.argv[1] != "orig") if len(sys.argv) > 1 else True)

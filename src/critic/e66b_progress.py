"""E66b: does a progress criterion fix the diagnostics preference? Same fresh candidates, two criteria."""
import json, os, sys, time, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "src"); from e65_critic import API, auroc; from e66_critic import acceptable
PROGRESS = (" Prefer the step that makes progress toward the task or recovers from a reported failure. A step that only "
            "inspects, checks or verifies — gathering nothing the status reports have not already stated — is NOT acceptable.")
def prep(qs):
    for q in qs:
        low = [c.lower() for c in q["candidates"]]
        if q["greedy"] and q["greedy"].lower() not in low: q["candidates"] = ([q["greedy"]] + q["candidates"])[:5]
        q["greedy_letter"] = "ABCDE"[[c.lower() for c in q["candidates"]].index(q["greedy"].lower())] if q["greedy"] and q["greedy"].lower() in [c.lower() for c in q["candidates"]] else None
    return qs
def ask(q, key, amended):
    L = "ABCDE"[:len(q["candidates"])]; C = dict(zip(L, q["candidates"])); extra = PROGRESS if amended else ""
    Q = {"next_step": {"type": "choice", "instructions": ("A robot arm is executing a manipulation task one step at a time. Given the task and the steps "
          "already completed, including any status report, which candidate is the best next step?" + extra), "criteria": {l: f"Candidate {l}: {C[l]}" for l in L}}}
    for l in L: Q[f"ok_{l}"] = {"type": "noul", "instructions": f"Is candidate {l} — \"{C[l]}\" — an acceptable next step for the robot right now?" + extra,
                                "criteria": {"true": "Yes — it is a correct thing to do next.", "false": "No — it skips something required, repeats what is done, ignores a reported failure, uses the wrong object, "
                                             + ("only inspects or checks without making progress, " if amended else "") + "or is not part of this task."}}
    body = json.dumps({"state": {"task": q["task"], "steps_completed": q["prefix"], "candidate_next_steps": C}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: d = json.loads(r.read())["answers"]
            pr = d["next_step"]["probabilities"]; return dict(id=q["id"], letters=L, choice=d["next_step"].get("choice") or max(pr, key=pr.get), probs=pr, ok={l: d[f"ok_{l}"]["noul"] for l in L})
        except Exception as e:                                   # noqa: BLE001
            if a == 2: return dict(id=q["id"], error=str(e))
            time.sleep(1.5 * (a + 1))
def score(qs, res, name):
    pick = [acceptable(q, q["candidates"][r["letters"].index(r["choice"])]) for q, r in zip(qs, res)]
    V = [(r["ok"][q["greedy_letter"]], acceptable(q, q["greedy"])) for q, r in zip(qs, res) if q["greedy_letter"]]
    cand = [(r["ok"][l], acceptable(q, c)) for q, r in zip(qs, res) for l, c in zip(r["letters"], q["candidates"])]
    ex = [q for q in qs if any(acceptable(q, c) for c in q["candidates"])]; cond = [acceptable(q, q["candidates"][r["letters"].index(r["choice"])]) for q, r in zip(qs, res) if q in ex]
    print(f"{name:9s} strict pick {100*sum(pick)/len(pick):5.1f}%   pick | ≥1 exists {100*sum(cond)/max(1,len(cond)):5.1f}% (n={len(cond)})   veto AUROC {auroc([p for p,_ in V],[a for _,a in V]):.3f}   per-candidate AUROC {auroc([p for p,_ in cand],[a for _,a in cand]):.3f}")
def main():
    qs = prep(json.load(open("notes/e66b-planner.json"))); key = os.environ["TYPESAFE_API_KEY"]
    print(f"{len(qs)} fresh failure prefixes; greedy acceptable {100*sum(acceptable(q,q['greedy']) for q in qs)/len(qs):.0f}%; ≥1 acceptable in set {100*sum(any(acceptable(q,c) for c in q['candidates']) for q in qs)/len(qs):.0f}%")
    with ThreadPoolExecutor(6) as ex:
        ro = list(ex.map(lambda q: ask(q, key, False), qs)); ra = list(ex.map(lambda q: ask(q, key, True), qs))
    json.dump({"orig": ro, "amended": ra}, open("notes/e66b-jev.json", "w"))
    score(qs, ro, "original"); score(qs, ra, "amended")
if __name__ == "__main__": main()

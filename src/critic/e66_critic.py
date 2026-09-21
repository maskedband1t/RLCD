"""E66 critic: Jev over the planner's candidates; rule-based acceptability; metrics; blind hand-check sheet."""
import json, os, random, re, sys, time, urllib.request, collections
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "src"); from e65_critic import API, auroc, ece
FOLD = {1: {1, 2}, 2: {2}, 3: {3, 4}, 4: {4}, 5: {5}, 6: {6, 7}}
def canon(c, x, y):
    s = c.lower(); hx = any(w in s for w in x.split()[-1:]); hy = any(w in s for w in y.split()[-1:])
    RETRY = r"\b(again|re-?grasp|retry|re-?attempt|re-?position|re-?approach|try (to )?(grasp|pick)|open the gripper and|adjust|reposition|and (then )?(grasp|grab|pick))\b"
    if re.match(r"^\W*(inspect|check|verify|examine|confirm|ensure|assess|diagnose|look at|evaluate|review|monitor|observe)\b", s) and not re.search(RETRY, s):
        return "diagnostic"                                   # method error 14: an action word inside a check is not an action
    if re.search(RETRY, s): return "recovery"
    if re.search(r"\b(done|complete|finished|task (is )?complete|no further|stop)\b", s): return 7
    if re.search(r"\b(retract|withdraw|move (the )?(arm|gripper) (away|back|up)|return (to|the)|home position)\b", s): return 6
    if re.search(r"\b(release|let go|open (the )?gripper|drop|set (it |the )?down|place|put|lower|deposit|insert)\b", s) and (hy or re.search(r"\b(in|into|on|onto|inside)\b", s)): return 5
    if re.search(r"\b(move|carry|transport|bring|transfer|position|guide|navigate|swing)\b", s) and hy and re.search(r"\b(over|above|to|toward|towards|near|onto|into|in front)\b", s) and not re.search(r"\b(above|over|to|toward|towards) the "+re.escape(x.split()[-1])+r"\b", s): return 4
    if re.search(r"\b(lift|raise|pick up|elevate|hoist)\b", s) and not re.search(r"\b(grasp|grab|close)\b", s): return 3 if not re.search(r"\bpick up\b", s) else 2
    if re.search(r"\b(grasp|grab|grip|close (the )?gripper|clamp|take hold|secure|pinch|hold)\b", s): return 2
    if re.search(r"\b(move|approach|position|align|lower|descend|navigate|go|reach|extend|bring)\b", s) and hx and not hy: return 1
    if re.search(r"\b(locate|find|identify|detect|look for|search|scan|see)\b", s): return 0
    return "other"
def acceptable(q, c):
    k = canon(c, q["x"], q["y"])
    if q["kind"] == "failure": return k in ("recovery", 1, 2) or (q["k"] == 4 and k == 0)
    return k in FOLD.get(q["k"], set())
def jev(q, key):
    L = "ABCDE"[:len(q["candidates"])]; C = dict(zip(L, q["candidates"]))
    Q = {"next_step": {"type": "choice", "instructions": ("A robot arm is executing a manipulation task one step at a time. Given the task and the steps "
          "already completed, including any status report, which candidate is the best next step?"), "criteria": {l: f"Candidate {l}: {C[l]}" for l in L}}}
    for l in L: Q[f"ok_{l}"] = {"type": "noul", "instructions": f"Is candidate {l} — \"{C[l]}\" — an acceptable next step for the robot right now?",
                                "criteria": {"true": "Yes — it is a correct thing to do next.", "false": "No — it skips something required, repeats what is done, ignores a reported failure, uses the wrong object, or is not part of this task."}}
    body = json.dumps({"state": {"task": q["task"], "steps_completed": q["prefix"], "candidate_next_steps": C}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(3):
        try:
            t0 = time.time(); req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: d = json.loads(r.read())["answers"]
            pr = d["next_step"]["probabilities"]; ch = d["next_step"].get("choice") or max(pr, key=pr.get)
            return dict(id=q["id"], letters=L, choice=ch, probs=pr, ok={l: d[f"ok_{l}"]["noul"] for l in L}, secs=time.time() - t0)
        except Exception as e:                                   # noqa: BLE001
            if a == 2: return dict(id=q["id"], error=str(e))
            time.sleep(1.5 * (a + 1))
def main():
    qs = json.load(open("notes/e66-planner.json"))
    for q in qs:                                   # the greedy proposal is always a candidate; remember which
        low = [c.lower() for c in q["candidates"]]
        if q["greedy"] and q["greedy"].lower() not in low: q["candidates"] = ([q["greedy"]] + q["candidates"])[:5]   # greedy first, never cut
        q["greedy_letter"] = "ABCDE"[[c.lower() for c in q["candidates"]].index(q["greedy"].lower())] if q["greedy"] and q["greedy"].lower() in [c.lower() for c in q["candidates"]] else None
    print("candidate-count distribution:", dict(sorted(collections.Counter(len(q["candidates"]) for q in qs).items())))
    key = os.environ["TYPESAFE_API_KEY"]
    with ThreadPoolExecutor(6) as ex: res = {r["id"]: r for r in ex.map(lambda q: jev(q, key), qs)}
    json.dump(list(res.values()), open("notes/e66-jev.json", "w"))
    rng = random.Random(0); rows = []
    for q in qs:
        r = res[q["id"]]
        if "error" in r: continue
        acc = {l: acceptable(q, c) for l, c in zip(r["letters"], q["candidates"])}
        gl = q.get("greedy_letter")
        rows.append(dict(kind=q["kind"], greedy=acceptable(q, q["greedy"]), any=any(acc.values()), jev=acc[r["choice"]], veto_p=(r["ok"][gl] if gl else None),
                         multi=len(acc) >= 2,
                         rnd=acc[rng.choice(r["letters"])], conf=max(r["probs"].values()), n=len(acc),
                         cand=[(r["ok"][l], acc[l]) for l in r["letters"]]))
    for kind in ("normal", "failure", "all"):
        R = [x for x in rows if kind == "all" or x["kind"] == kind]; n = len(R); pc = lambda f: 100 * sum(f(x) for x in R) / n
        cond = [x for x in R if x["any"]]
        print(f"{kind:8s} n={n:3d}  planner greedy {pc(lambda x: x['greedy']):5.1f}%  set has ≥1 acceptable {pc(lambda x: x['any']):5.1f}%  "
              f"random pick {pc(lambda x: x['rnd']):5.1f}%  JEV pick {pc(lambda x: x['jev']):5.1f}%  jev | ≥1 exists {100*sum(x['jev'] for x in cond)/max(1,len(cond)):5.1f}%  mean cands {sum(x['n'] for x in R)/n:.1f}")
    # VETO: noul on the planner's greedy proposal vs its rule-acceptability
    V = [(x["veto_p"], x["greedy"]) for x in rows if x["veto_p"] is not None]
    acc_th = 100 * sum((p > .5) == a for p, a in V) / len(V)
    print(f"\nVETO on the greedy proposal ({len(V)} questions; {100*sum(a for _,a in V)/len(V):.0f}% acceptable): AUROC {auroc([p for p,_ in V],[a for _,a in V]):.3f}  accept-if-P>.5 accuracy {acc_th:.1f}%  "
          f"(always-accept would score {100*sum(a for _,a in V)/len(V):.1f}%)  mean P acceptable {sum(p for p,a in V if a)/max(1,sum(a for _,a in V)):.2f} vs not {sum(p for p,a in V if not a)/max(1,sum(not a for _,a in V)):.2f}")
    for kind in ("normal", "failure"):
        Vk = [(p, a) for (p, a), x in zip(V, [x for x in rows if x["veto_p"] is not None]) if x["kind"] == kind]
        if Vk: print(f"   {kind:8s} veto AUROC {auroc([p for p,_ in Vk],[a for _,a in Vk]):.3f}  greedy acceptable {100*sum(a for _,a in Vk)/len(Vk):.0f}%")
    M = [x for x in rows if x["multi"]]; print(f"ranking subset (≥2 distinct candidates): n={len(M)}  random {100*sum(x['rnd'] for x in M)/max(1,len(M)):.1f}%  JEV {100*sum(x['jev'] for x in M)/max(1,len(M)):.1f}%  greedy {100*sum(x['greedy'] for x in M)/max(1,len(M)):.1f}%")
    s = [p for x in rows for p, _ in x["cand"]]; l = [a for x in rows for _, a in x["cand"]]
    print(f"per-candidate noul vs rule-acceptability over {len(s)} candidates: AUROC {auroc(s, l):.3f}  ECE {ece(s, l):.3f}")
    hi = [x for x in rows if x["conf"] >= .9]; print(f"selective: conf ≥ .9 on {100*len(hi)/len(rows):.0f}% of questions, JEV pick acceptable there {100*sum(x['jev'] for x in hi)/max(1,len(hi)):.1f}%")
    print(f"mean Jev secs {sum(res[q['id']].get('secs',0) for q in qs)/len(qs):.2f}")
    # blind hand-check sheet: 40 questions, candidates in letter order, no verdicts shown
    rng2 = random.Random(7); sheet = rng2.sample(qs, 40)
    with open("notes/e66-handcheck-sheet.txt", "w") as f:
        for q in sheet:
            f.write(f"\n### Q{q['id']}  [{q['kind']}]  TASK: {q['task']}\n  done: " + " | ".join(q["prefix"]) + "\n")
            for l, c in zip("ABCDE", q["candidates"]): f.write(f"    {l}. {c}\n")
    json.dump([q["id"] for q in sheet], open("notes/e66-handcheck-ids.json", "w")); print("hand-check sheet: notes/e66-handcheck-sheet.txt (40 questions)")
if __name__ == "__main__": main()

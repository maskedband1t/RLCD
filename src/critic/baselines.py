"""H1 baseline arms, as the council demanded. All arms see identical content.

  program            canonical-plan tracker: task -> canonical steps; drop completed; drop off-plan; redo FAILED
  constrained        7B/72B: log P(candidate string | prompt), length-normalised, softmax over candidates
  yesno              7B/72B: per-candidate P(Yes)/(P(Yes)+P(No)) -- the noul counterpart, same call budget as Jev
  temperature        fit T on a held-out TASK split by NLL; apply to constrained / yesno logits
  jev_single         Jev with only the `choice` question (no parallel noul heads)
"""
import json, math, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e65_critic import plan, RX

# ---------------------------------------------------------------- program arm
def canon_index(step, x, y):
    """Map free-form step text to a canonical index 0..7, 'recovery', or None (off-plan)."""
    s = step.lower()
    if re.search(r"\b(again|re-?grasp|retry|re-?attempt|open the gripper and)\b", s): return "recovery"
    for p in ("in", "on"):
        P = plan(x, y, p)
        for i, t in enumerate(P):
            if s == t.lower(): return i
    pats = [r"\blocate\b|\bfind\b", r"\b(move|position).*(above|over) the " + re.escape(x), r"\bgrasp\b|\bgrab\b|\bpick up\b",
            r"\blift\b|\braise\b", r"\bmove the " + re.escape(x) + r"\b.*\b(over|to|toward)", r"\b(lower|release|place|put)\b.*\b(in|on|into|onto)\b",
            r"\bretract\b|\bwithdraw\b", r"\bdone\b|\bcomplete\b"]
    for i, pat in enumerate(pats):
        if re.search(pat, s): return i
    return None

def program_pick(q):
    """The 12-line inverse the LLM-eval reviewer wrote: earliest not-yet-done canonical step; redo a FAILED step."""
    x, y = q["x"], q["y"]; done = q["steps_completed"]
    # a failure counts only if the LAST completed step is the unresolved one; thresholds (0.0 N) are code's job
    failed = bool(done) and bool(re.search(r"FAILED|nothing held|0\.0 N|no longer (visible|in the gripper)", done[-1])) and "secured" not in done[-1]
    idx = [canon_index(re.sub(r" — .*$", "", d), x, y) for d in done]
    idx = [i for i in idx if isinstance(i, int)]
    want = 2 if failed else (max(idx) + 1 if idx else 0)
    best, best_score = None, -1e9
    xw = x.split()[-1]
    for L, c in q["candidates"].items():
        ci = canon_index(c, x, y); cl = c.lower()
        names_obj = xw in cl
        if failed and ci in ("recovery", 0, 1, 2) and names_obj: score = 10 - {"recovery": 0, 2: 0, 1: 1, 0: 2}.get(ci, 3)
        elif ci is None or ci == "recovery": score = -5
        elif ci in (1, 2, 3, 4, 5) and not names_obj: score = -6     # acts on the wrong object
        elif ci in idx: score = -3                                  # repeat
        else: score = -abs(ci - want)                               # closest to the wanted step
        if score > best_score: best, best_score = L, score
    return best

# ---------------------------------------------------------------- 7B constrained scoring
def prompt_for(q, tok):
    steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])) or "  (none yet)"
    cands = "\n".join(f"  {L}. {q['candidates'][L]}" for L in q["candidates"])
    user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\n"
            f"Steps already completed (including any reported failure):\n{steps}\nCandidate next steps:\n{cands}\n"
            "Which candidate is the correct next step? Answer with the step text.")
    return tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False)

def seq_logprob(model, tok, prompt, continuation):
    """Sum of log-probs of `continuation` tokens given prompt, and token count."""
    import mlx.core as mx
    p_ids = tok.encode(prompt); c_ids = tok.encode(continuation, add_special_tokens=False)
    ids = mx.array([p_ids + c_ids]); logits = model(ids)[0].astype(mx.float32)
    lp = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
    tot = 0.0
    for k, tid in enumerate(c_ids):
        tot += float(lp[len(p_ids) - 1 + k, tid])
    return tot, len(c_ids)

def constrained_scores(model, tok, q):
    """Length-normalised log P(candidate text) for each candidate -> dict letter -> logit."""
    pr = prompt_for(q, tok); out = {}
    for L, c in q["candidates"].items():
        lp, n = seq_logprob(model, tok, pr, " " + c); out[L] = lp / max(1, n)
    return out

def yesno_probs(model, tok, q):
    """Per-candidate P(Yes) via constrained Yes/No -- the noul counterpart."""
    import mlx.core as mx
    steps = "\n".join(f"  {j+1}. {s}" for j, s in enumerate(q["steps_completed"])) or "  (none yet)"
    out = {}
    yes_ids = [tok.encode(" Yes", add_special_tokens=False)[-1], tok.encode("Yes", add_special_tokens=False)[-1]]
    no_ids = [tok.encode(" No", add_special_tokens=False)[-1], tok.encode("No", add_special_tokens=False)[-1]]
    for L, c in q["candidates"].items():
        user = (f"A robot arm is executing a manipulation task one step at a time.\nTask: {q['task']}\n"
                f"Steps already completed (including any reported failure):\n{steps}\n"
                f"Proposed next step: {c}\nIs this the correct next step right now? Answer Yes or No.")
        pr = tok.apply_chat_template([{"role": "user", "content": user}], add_generation_prompt=True, tokenize=False) + "Answer:"
        ids = mx.array([tok.encode(pr)]); logits = model(ids)[0, -1, :].astype(mx.float32)
        lp = logits - mx.logsumexp(logits); py = sum(math.exp(float(lp[t])) for t in yes_ids); pn = sum(math.exp(float(lp[t])) for t in no_ids)
        out[L] = py / max(1e-12, py + pn)
    return out

# ---------------------------------------------------------------- temperature scaling
def softmax(d, T=1.0):
    m = max(d.values()); e = {k: math.exp((v - m) / T) for k, v in d.items()}; s = sum(e.values()); return {k: v / s for k, v in e.items()}

def fit_temperature(logit_rows, truths):
    """logit_rows: list of dict letter->logit; truths: list of letters. Minimise NLL over T by grid."""
    best, bestT = 1e18, 1.0
    for T in [x / 20 for x in range(2, 200)]:
        nll = -sum(math.log(max(1e-12, softmax(r, T)[t])) for r, t in zip(logit_rows, truths))
        if nll < best: best, bestT = nll, T
    return bestT

def task_split(qs, frac=0.5, seed=0):
    """Split by TASK so calibration is fit on different tasks than it is evaluated on."""
    import random
    tasks = sorted(set(q["task"] for q in qs)); rng = random.Random(seed); rng.shuffle(tasks)
    fit = set(tasks[:int(len(tasks) * frac)])
    return [q for q in qs if q["task"] in fit], [q for q in qs if q["task"] not in fit]

# ---------------------------------------------------------------- Jev single-choice ablation
def jev_single_choice(q, key):
    import urllib.request, time
    from e65_critic import API
    C = q["candidates"]; L = "".join(C.keys())
    Q = {"next_step": {"type": "choice", "instructions": ("A robot arm is executing a manipulation task one step at a time. Given the task and the steps "
          "already completed, including any reported failure, which candidate is the correct next step?"), "criteria": {l: f"Candidate {l}: {C[l]}" for l in L}}}
    body = json.dumps({"state": {"task": q["task"], "steps_completed": q["steps_completed"], "candidate_next_steps": C}, "model": "jev-latest", "questions": Q}).encode()
    for a in range(3):
        try:
            req = urllib.request.Request(API, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r: d = json.loads(r.read())["answers"]["next_step"]
            pr = d["probabilities"]; return dict(id=q["id"], choice=d.get("choice") or max(pr, key=pr.get), probs=pr)
        except Exception as e:                                   # noqa: BLE001
            if a == 2: return dict(id=q["id"], error=str(e))
            time.sleep(1.5 * (a + 1))

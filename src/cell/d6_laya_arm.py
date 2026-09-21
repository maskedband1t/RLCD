"""D6 · Laya (open, RL-trained typed-decision encoder) behind our interface, scored on the same 400 recorded
sorting-cell decisions as D1-cell (plain 7B: 37.5 % acceptable; Jev: 81.5 %). Runs in the separate laya venv:

  USE_TF=0 PYTHONPATH=src <scratchpad>/laya-venv/bin/python src/cell/d6_laya_arm.py --model convaiinnovations/laya

Pre-registered in the notebook (D6). The state rendering is the instrument's one open design choice and is
fixed by hand before the run — see render_state()."""
import json, os, sys, time, random, argparse
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.decision_eval import seed_index, signature, acceptable, auroc

ACTION_INSTRUCTIONS = ("You are the judgment layer of a sorting robot; code executes whatever you choose. "
                       "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting.")

def render_state(state, budget_tokens):
    """Write the world for a bidirectional encoder with a fixed window (decision fixed 2026-09-19 13:25 PDT,
    before any Laya result was seen; one rule for both checkpoints).

    Rule: decision-critical first, constant last, one compact line per part, no JSON punctuation.
      1. task; 2. operator notes verbatim (they carry the unanticipated events the arm is scored on);
      3. robot state (holding, grasp, location, person hand); 4. trays; 5. parts, one line each with the
      attributes the rules and notes key on (colour, shape, size, lot, fragile, weight, status, damaged/broken,
      qa_sticker, printed_marking); 6. the last two recent actions.
    Dropped: `capabilities` (a constant paragraph, identical in every decision). The compact form is ~150-250
    tokens, so the 27 option texts (~470) fit the 1,024 window and mostly the 512 one. The declared dumb
    baseline is the raw JSON with everything in it, cut by the window (--raw-json)."""
    r = state.get("robot", {}) or {}
    lines = [f"TASK: {state.get('task')}"]
    notes = state.get("notes_from_operators")
    lines.append("OPERATOR NOTES: " + (json.dumps(notes, ensure_ascii=False) if notes else "none"))
    lines.append(f"ROBOT: holding={r.get('holding')} grasp={r.get('grasp')} location={r.get('location')} person_hand_in_workspace={r.get('person_hand_in_workspace')}")
    lines.append("TRAYS: " + ", ".join(f"{k}={v}" for k, v in (state.get("trays") or {}).items()))
    lines.append("PARTS:")
    for p in state.get("parts", []) or []:
        flags = [k for k in ("looks_damaged", "broken") if p.get(k)]
        extra = [f"{k}={p[k]}" for k in ("qa_sticker", "printed_marking") if p.get(k)]
        lines.append(f"  {p.get('id')}: {p.get('colour')} {p.get('shape')} {p.get('size')} lot {p.get('lot')} fragile={p.get('fragile')} weight={p.get('weight')} status={p.get('status')}"
                     + (" " + " ".join(flags) if flags else "") + (" " + " ".join(extra) if extra else ""))
    ra = state.get("recent_actions") or []
    if ra: lines.append("RECENT: " + " | ".join(ra[-2:]))
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--records", default="results/cell/e71_jev_record.jsonl"); ap.add_argument("--model", default="convaiinnovations/laya")
    ap.add_argument("--limit", type=int, default=400); ap.add_argument("--out", default=None); ap.add_argument("--budget", type=int, default=512); ap.add_argument("--raw-json", action="store_true", help="declared dumb baseline: the full state JSON, cut by the window"); a = ap.parse_args()
    out_path = a.out or f"results/cell/d6_{a.model.split('/')[-1]}{'_rawjson' if a.raw_json else ''}.jsonl"
    import laya
    t0 = time.time(); agent = laya.load(a.model); print(f"loaded {a.model} in {time.time()-t0:.0f}s", flush=True)
    rows = [json.loads(l) for l in open(a.records) if l.strip()]
    random.Random(20260918).shuffle(rows); rows = rows[:a.limit]          # the D1-cell subsample, same seed
    idx = seed_index(); res = []; lat = []
    for i, r in enumerate(rows):
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec)
        st = json.dumps(r["state"]) if a.raw_json else render_state(r["state"], a.budget)
        questions = {"action": {"type": "choice", "instructions": ACTION_INSTRUCTIONS, "criteria": r["options"]}}
        t1 = time.time()
        try:
            ans = agent.predict(st, questions)["answers"]["action"]; lat.append(time.time() - t1)
            choice = ans.get("choice"); conf = float(ans.get("confidence", 0.0)); probs = ans.get("probabilities", {})
        except Exception as e:
            choice, conf, probs = None, 0.0, {"error": str(e)[:120]}
        res.append({"key": r["key"], "seed": seed, "laya": {"choice": choice, "confidence": conf}, "jev": {"choice": r["answer"]["choice"], "confidence": r["answer"]["confidence"]},
                    "acceptable_set": sorted(acc), "laya_ok": choice in acc, "jev_ok": r["answer"]["choice"] in acc, "must_ask": "ask_operator" in acc})
        if (i + 1) % 50 == 0: print(f"{i+1}/{len(rows)}", flush=True)
    with open(out_path, "w") as f:
        for r in res: f.write(json.dumps(r) + "\n")
    ok = np.array([r["laya_ok"] for r in res]); jok = np.array([r["jev_ok"] for r in res]); conf = np.array([r["laya"]["confidence"] for r in res])
    agree = np.mean([r["laya"]["choice"] == r["jev"]["choice"] for r in res])
    print(f"\n{a.model}: decisions {len(res)} | acceptable {ok.mean():.1%} (Jev on the same {jok.mean():.1%}; plain 7B 37.5 %) | agreement with Jev {agree:.1%} | AUROC(confidence→acceptable) {auroc(conf, ok):.3f} | latency median {np.median(lat):.3f}s")
    for lo, hi in [(0, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        m = (conf >= lo) & (conf < hi)
        if m.sum(): print(f"   conf [{lo:.1f},{hi:.1f}): n={m.sum():>3} acceptable {ok[m].mean():.1%}")
    print("D6_DONE", flush=True)

if __name__ == "__main__": main()

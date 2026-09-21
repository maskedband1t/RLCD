"""D5 · Option-order sensitivity of Jev on recorded sorting-cell decisions (pre-registered in the notebook).

For a seeded subsample of E71's recorded `jev` decisions (state + 27 options + recorded answer), ask Jev again
twice with the identical state and questions: (a) options in the recorded order — the repeat control, which
absorbs API nondeterminism and any model drift since 2026-09-18; (b) options in REVERSED order. Measured on the
`action` Choice: agreement of the argmax with the recorded choice, mean absolute shift of the recorded top
option's probability, and argmax flips by recorded-confidence bin. JevBench reported a 72 % -> 21 % swing for a
plain 4B model under reversal; D1 measured letter-position bias in a plain 7B; this asks whether Jev has it."""
import json, os, sys, time, random, argparse
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.policies import Jev, CAPABILITIES

def ask(pol, state, opts):
    questions = {
        "action": pol.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                           "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."},
                             criteria=opts),
        "place_gently": pol.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                 criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
        "risk": pol.Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
    }
    for attempt in range(3):
        try:
            t0 = time.time(); r = pol.client.system_one(state=state, model=pol.model, questions=questions); a = r.answers["action"]
            return {"choice": a.choice, "confidence": float(a.confidence), "probabilities": {k: float(v) for k, v in a.probabilities.items()}, "latency": round(time.time() - t0, 3)}
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:80]}"; time.sleep(1.5 * (attempt + 1))
    return {"error": err}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--records", default="results/cell/e71_jev_record.jsonl"); ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--out", default="results/cell/d5_option_order.jsonl"); ap.add_argument("--eval-only", action="store_true"); a = ap.parse_args()
    if not a.eval_only:
        recs = [json.loads(l) for l in open(a.records) if l.strip()]; recs = [r for r in recs if len(r["options"]) >= 2 and "choice" in r["answer"]]
        rng = random.Random(0); sample = rng.sample(recs, min(a.n, len(recs)))
        pol = Jev(record=[], replay=None); out = open(a.out, "w")
        for i, r in enumerate(sample):
            state = r["state"] if "capabilities" in r["state"] else {"capabilities": CAPABILITIES, **r["state"]}
            opts = dict(r["options"]); rev = dict(reversed(list(opts.items())))
            rep = ask(pol, state, opts); rv = ask(pol, state, rev)
            out.write(json.dumps({"key": r["key"], "recorded": {"choice": r["answer"]["choice"], "confidence": r["answer"]["confidence"], "probabilities": r["answer"]["probabilities"]},
                                  "repeat": rep, "reversed": rv, "n_options": len(opts)}) + "\n"); out.flush()
            if (i + 1) % 25 == 0: print(f"{i+1}/{len(sample)}", flush=True)
        out.close()
    rows = [json.loads(l) for l in open(a.out) if l.strip()]; ok = [r for r in rows if "choice" in r["repeat"] and "choice" in r["reversed"]]
    print(f"decisions {len(rows)} | both calls ok {len(ok)} | errors {len(rows) - len(ok)}")
    rec_c = np.array([r["recorded"]["choice"] for r in ok]); rep_c = np.array([r["repeat"]["choice"] for r in ok]); rev_c = np.array([r["reversed"]["choice"] for r in ok])
    conf = np.array([r["recorded"]["confidence"] for r in ok])
    agree_rep = (rep_c == rec_c).mean(); agree_rev = (rev_c == rec_c).mean(); agree_rr = (rev_c == rep_c).mean()
    print(f"argmax agreement with recorded: repeat {agree_rep:.1%} | reversed {agree_rev:.1%} | reversed vs repeat {agree_rr:.1%}")
    dp_rep = np.array([abs(r["repeat"]["probabilities"].get(r["recorded"]["choice"], 0) - r["recorded"]["probabilities"].get(r["recorded"]["choice"], 0)) for r in ok])
    dp_rev = np.array([abs(r["reversed"]["probabilities"].get(r["recorded"]["choice"], 0) - r["recorded"]["probabilities"].get(r["recorded"]["choice"], 0)) for r in ok])
    print(f"mean |delta p(recorded top option)|: repeat {dp_rep.mean():.3f} | reversed {dp_rev.mean():.3f}")
    dc = np.array([r["reversed"]["confidence"] - r["repeat"]["confidence"] for r in ok]); print(f"confidence shift reversed - repeat: mean {dc.mean():+.3f}, |mean| {np.abs(dc).mean():.3f}")
    print("argmax flips (reversed != repeat) by recorded confidence bin:")
    for lo, hi in [(0, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        m = (conf >= lo) & (conf < hi)
        if m.sum(): print(f"   conf [{lo:.1f},{hi:.1f}): n={m.sum():>3} flips {(rev_c[m] != rep_c[m]).mean():.1%} | repeat-vs-recorded disagreement {(rep_c[m] != rec_c[m]).mean():.1%}")
    # first-position and last-position share: does the argmax favour the first-listed option under either order?
    first_rep = np.mean([r["repeat"]["choice"] == list(r["recorded"]["probabilities"].keys())[0] for r in ok]) if ok else float("nan")
    print(f"(descriptive) mean n options {np.mean([r['n_options'] for r in ok]):.1f}")
    # bootstrap CI for agreement difference (repeat - reversed)
    rng = np.random.default_rng(0); d = (rep_c == rec_c).astype(float) - (rev_c == rec_c).astype(float); bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(5000)]
    print(f"agreement difference repeat - reversed: {d.mean():+.3f} [{np.percentile(bs, 2.5):+.3f}, {np.percentile(bs, 97.5):+.3f}]")
    print("D5_DONE", flush=True)

if __name__ == "__main__": main()

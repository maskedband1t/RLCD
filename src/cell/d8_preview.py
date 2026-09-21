"""D8 (a) · the second RLCD model, `jev-preview`, on D4's 400 recorded E71 decisions with the identical request (same
instructions, criteria = the recorded options, same Noul and Score), every 4th re-asked with the options reversed;
scored with the acceptable set; paired against `jev-latest`'s recorded answer and the open 27B's (D4). Pre-registered
2026-09-20 04:02 PDT."""
import os, sys, json, time, random, argparse
import numpy as np
sys.path.insert(0, "src")
from cell.decision_eval import seed_index, signature, acceptable, auroc
from cell.analyze import wilson, boot_diff

INSTR = {"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
         "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."}

def ask(client, Choice, Noul, Score, model, state, options):
    q = {"action": Choice(instructions=INSTR, criteria=options),
         "place_gently": Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                              criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
         "risk": Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"])}
    t0 = time.time(); r = client.system_one(state=state, model=model, questions=q); a = r.answers
    return {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3), "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
            "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2), "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="jev-preview"); ap.add_argument("--records", default="results/cell/e71_jev_record.jsonl"); ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--reverse-every", type=int, default=4); ap.add_argument("--out", default="results/cell/d8_preview_decisions.jsonl"); ap.add_argument("--sleep", type=float, default=0.05); a = ap.parse_args()
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
    client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
    rows = [json.loads(l) for l in open(a.records) if l.strip()]; rows = [r for r in rows if len(r["options"]) >= 2 and "choice" in r["answer"]]
    random.Random(20260918).shuffle(rows); rows = rows[:a.limit]
    d4 = {}
    p27 = "results/cell/d4_Qwen3.8-27B-classifier.jsonl"
    if os.path.exists(p27):
        for l in open(p27): r = json.loads(l); d4[r["key"]] = r
    idx = seed_index(); f = open(a.out, "w"); res = []; errs = 0
    for i, r in enumerate(rows):
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec)
        try: ans = ask(client, Choice, Noul, Score, a.model, r["state"], r["options"])
        except Exception as e: errs += 1; ans = {"error": type(e).__name__}
        time.sleep(a.sleep); rev = None
        if i % a.reverse_every == 0 and "choice" in ans:
            try: rev = ask(client, Choice, Noul, Score, a.model, r["state"], dict(reversed(list(r["options"].items())))); time.sleep(a.sleep)
            except Exception as e: rev = {"error": type(e).__name__}
        row = {"key": r["key"], "seed": seed, "model": a.model, "preview": ans, "reversed": rev, "latest": r["answer"], "open27b": (d4.get(r["key"]) or {}).get("open"),
               "acceptable_set": sorted(acc), "preview_ok": ans.get("choice") in acc, "latest_ok": r["answer"]["choice"] in acc, "open27b_ok": (d4.get(r["key"]) or {}).get("open_ok")}
        res.append(row); f.write(json.dumps(row) + "\n"); f.flush()
        if (i + 1) % 50 == 0: print(f"  {i+1}/{len(rows)} | preview acceptable so far {100*np.mean([x['preview_ok'] for x in res]):.1f}% | errors {errs}", flush=True)
    ok = [x for x in res if "choice" in x["preview"]]
    pv = np.array([x["preview_ok"] for x in ok]); lt = np.array([x["latest_ok"] for x in ok]); conf = np.array([x["preview"]["confidence"] for x in ok])
    m, lo, hi = boot_diff({x["key"]: 100.0 * x["preview_ok"] for x in ok}, {x["key"]: 100.0 * x["latest_ok"] for x in ok})
    agree = np.mean([x["preview"]["choice"] == x["latest"]["choice"] for x in ok])
    flips = [x for x in ok if x["reversed"] and "choice" in x["reversed"]]; fl = np.mean([x["reversed"]["choice"] != x["preview"]["choice"] for x in flips]) if flips else float("nan")
    fl_hi = np.mean([x["reversed"]["choice"] != x["preview"]["choice"] for x in flips if x["preview"]["confidence"] >= .7]) if flips else float("nan")
    o27 = [x for x in ok if x["open27b_ok"] is not None]
    print(f"\n{a.model}: decisions {len(ok)} (errors {errs}) | acceptable {pv.mean():.1%} vs jev-latest {lt.mean():.1%} (paired {m:+.1f} [{lo:+.1f}, {hi:+.1f}])" + (f" vs 27B {np.mean([x['open27b_ok'] for x in o27]):.1%}" if o27 else "") +
          f" | agreement with jev-latest {agree:.1%} | AUROC(conf->acceptable) {auroc(conf, pv):.3f} | flips under reversal {fl:.1%} (n {len(flips)}), at conf>=.7 {fl_hi:.1%} | latency median {np.median([x['preview']['latency'] for x in ok]):.2f}s | tokens {sum(x['preview']['tokens'] for x in ok)}")
    for lo_, hi_ in [(0, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        msk = (conf >= lo_) & (conf < hi_)
        if msk.sum(): print(f"   conf [{lo_:.1f},{hi_:.1f}): n={msk.sum():>3} acceptable {pv[msk].mean():.1%}")

if __name__ == "__main__": main()

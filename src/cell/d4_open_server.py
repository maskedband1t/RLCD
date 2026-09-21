"""D4 · A strong open general model behind the identical typed interface, via Featherless's public Simple Jev demo
endpoint (no account, no key). Same 400 recorded decisions as D1-cell / D6; same state JSON and option texts Jev
saw; acceptable-set scoring; a 100-decision reversed-order subsample for order sensitivity. Pre-registered (D4)."""
import json, os, sys, time, random, argparse, urllib.request
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.decision_eval import seed_index, signature, acceptable, auroc

URL = "https://simple-jev-demo-api.featherless.ai/v1/classifier"
INS = {"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
       "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."}

def ask(model, state, options, timeout=60):
    body = {"model": model, "state": state, "questions": {"action": {"type": "choice", "instructions": json.dumps(INS), "criteria": options}}}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "curl/8.7.1", "Accept": "application/json"})
    for attempt in range(4):
        try:
            t0 = time.time(); r = json.loads(urllib.request.urlopen(req, timeout=timeout).read()); lat = time.time() - t0
            a = r["answers"]["action"]; return {"choice": a.get("choice"), "confidence": float(a.get("confidence", 0)), "probabilities": {k: float(v) for k, v in (a.get("probabilities") or {}).items()}, "latency": lat}
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:200]
            if e.code == 429: time.sleep(2.0 * (attempt + 1)); continue
            return {"error": f"HTTP {e.code}: {msg}"}
        except Exception as e:
            time.sleep(1.5 * (attempt + 1)); err = str(e)[:120]
    return {"error": err}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--model", default="featherless-ai/Qwen3.8-27B-classifier"); ap.add_argument("--records", default="results/cell/e71_jev_record.jsonl")
    ap.add_argument("--limit", type=int, default=400); ap.add_argument("--reverse-every", type=int, default=4); ap.add_argument("--sleep", type=float, default=0.35); ap.add_argument("--out", default=None); ap.add_argument("--smoke", type=int, default=0); a = ap.parse_args()
    out = a.out or f"results/cell/d4_{a.model.split('/')[-1]}.jsonl"
    rows = [json.loads(l) for l in open(a.records) if l.strip()]; rows = [r for r in rows if len(r["options"]) >= 2 and "choice" in r["answer"]]
    random.Random(20260918).shuffle(rows); rows = rows[:a.limit] if not a.smoke else rows[:a.smoke]
    idx = seed_index(); res = []; f = open(out, "w")
    for i, r in enumerate(rows):
        sig = signature(r["state"]["parts"]);
        if sig not in idx: continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec)
        ans = ask(a.model, r["state"], r["options"]); time.sleep(a.sleep)
        rev = None
        if i % a.reverse_every == 0 and "choice" in ans:
            rev = ask(a.model, r["state"], dict(reversed(list(r["options"].items())))); time.sleep(a.sleep)
        row = {"key": r["key"], "seed": seed, "model": a.model, "open": ans, "reversed": rev, "jev": {"choice": r["answer"]["choice"], "confidence": r["answer"]["confidence"]},
               "acceptable_set": sorted(acc), "open_ok": ans.get("choice") in acc, "jev_ok": r["answer"]["choice"] in acc}
        res.append(row); f.write(json.dumps(row) + "\n"); f.flush()
        if a.smoke: print(json.dumps(ans)[:300])
        if (i + 1) % 50 == 0: print(f"{i+1}/{len(rows)}", flush=True)
    f.close()
    ok_rows = [x for x in res if "choice" in x["open"]]; errs = len(res) - len(ok_rows)
    if not ok_rows: print("no successful calls; errors:", errs, res[:2]); return
    ok = np.array([x["open_ok"] for x in ok_rows]); jok = np.array([x["jev_ok"] for x in ok_rows]); conf = np.array([x["open"]["confidence"] for x in ok_rows])
    agree = np.mean([x["open"]["choice"] == x["jev"]["choice"] for x in ok_rows]); lat = np.median([x["open"]["latency"] for x in ok_rows])
    print(f"\n{a.model}: decisions {len(ok_rows)} (errors {errs}) | acceptable {ok.mean():.1%} (Jev on the same {jok.mean():.1%}; plain 7B 37.5 %; Laya 28-31 %) | agreement with Jev {agree:.1%} | AUROC(conf->acceptable) {auroc(conf, ok):.3f} | latency median {lat:.2f}s")
    for lo, hi in [(0, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        m = (conf >= lo) & (conf < hi)
        if m.sum(): print(f"   conf [{lo:.1f},{hi:.1f}): n={m.sum():>3} acceptable {ok[m].mean():.1%}")
    rv = [x for x in ok_rows if x["reversed"] and "choice" in x["reversed"]]
    if rv:
        flips = np.array([x["reversed"]["choice"] != x["open"]["choice"] for x in rv]); c2 = np.array([x["open"]["confidence"] for x in rv])
        print(f"order sensitivity on {len(rv)} re-asked: argmax flips {flips.mean():.1%} | by confidence: " + " | ".join(f"[{lo:.1f},{hi:.1f}) n={((c2>=lo)&(c2<hi)).sum()} flips {flips[(c2>=lo)&(c2<hi)].mean():.0%}" for lo, hi in [(0,.5),(.5,.7),(.7,.9),(.9,1.01)] if ((c2>=lo)&(c2<hi)).sum()))
    print("D4_DONE", flush=True)

if __name__ == "__main__": main()

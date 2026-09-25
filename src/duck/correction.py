"""The correction round on the duck (the E80/E90 step, no API): take the states the owned head actually visited on the
unseen bank, label each with code's acceptable set as a uniform soft target, and write them as teacher-format records.
Usage: PYTHONPATH=src python src/duck/correction.py --record results/duck/e96_record.jsonl --seeds 40-69 --out results/duck/e98_correction_records.jsonl"""
import json, argparse, collections
ap = argparse.ArgumentParser(); ap.add_argument("--record", required=True); ap.add_argument("--seeds", default="40-69"); ap.add_argument("--out", required=True); ap.add_argument("--targets", choices=["uniform", "masked", "replacement"], default="uniform", help="uniform over the acceptable set (E98) | the recorded head's probabilities masked to the acceptable set and renormalised (E101)"); a = ap.parse_args()
lo, hi = a.seeds.split("-"); seeds = set(range(int(lo), int(hi) + 1)); n = 0; fixed = 0; ev = collections.Counter()
with open(a.out, "w") as f:
    for l in open(a.record):
        r = json.loads(l)
        if r.get("seed") not in seeds or not r.get("acceptable") or not r.get("options"): continue
        acc = [k for k in r["acceptable"] if k in r["options"]]
        if not acc: continue
        if a.targets == "masked":
            src = r["answer"].get("probabilities", {}); mass = sum(float(src.get(k, 0.0)) for k in acc)
            probs = {k: (round(float(src.get(k, 0.0)) / mass, 4) if (k in acc and mass > 1e-6) else (round(1.0 / len(acc), 4) if (k in acc) else 0.0)) for k in r["options"]}
            choice = max(acc, key=lambda k: probs[k])
        elif a.targets == "replacement":   # E123: the operator's replacement, one-hot on the oracle's first acceptable action (the cheapest acceptable move by the body's preference order)
            import os as _os; from duck.e115_mine import PREFER
            body = {"g1": "g1", "pick": "pick"}.get(_os.environ.get("DUCK_BODY", "duck"), "duck")
            pick = next((k for k in PREFER[body] if k in acc), None) or next((k for k in sorted(acc) if k.startswith("hand_to_")), None) or sorted(acc)[0]
            probs = {k: (1.0 if k == pick else 0.0) for k in r["options"]}; choice = pick
        else: probs = {k: (round(1.0 / len(acc), 4) if k in acc else 0.0) for k in r["options"]}; choice = sorted(acc)[0]
        fixed += r["answer"]["choice"] not in acc; ev[r.get("event")] += 1
        f.write(json.dumps({"key": r["key"], "state": r["state"], "options": r["options"], "answer": {"choice": choice, "confidence": round(probs[choice], 3), "probabilities": probs}, "arm": "jev", "seed": r["seed"], "event": r.get("event"), "acceptable": r["acceptable"], "source": f"correction:{a.targets}:{r['arm']}"}) + "\n"); n += 1
print(f"correction records: {n} visited states on seeds {lo}-{hi} ({fixed} where the head's choice was outside the acceptable set) | by event {dict(ev)} -> {a.out}")

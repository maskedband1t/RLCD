"""E80 (DAgger round): the teacher labels the states the student actually visited. Reads a student record file
(state, options), asks Jev the same three questions Jev3 asks, writes teacher records in the training format."""
import json, sys, os, time, hashlib
from .policies import CAPABILITIES

def main(inp, out, model="jev-latest"):
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
    client = TypeSafeClient(api_key=os.environ.get("TYPESAFE_API_KEY"))
    done = set()
    if os.path.exists(out):
        for l in open(out): done.add(json.loads(l)["key"])
    rows = [json.loads(l) for l in open(inp)]; n = 0; t0 = time.time(); fo = open(out, "a")
    for r in rows:
        state = r["state"]; opts = r["options"]
        key = hashlib.sha1(json.dumps([state, sorted(opts)], sort_keys=True).encode()).hexdigest()
        if key in done: continue
        questions = {
            "action": Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                           "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."}, criteria=opts),
            "place_gently": Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                 criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
            "risk": Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
        }
        try:
            res = client.system_one(state=state, model=model, questions=questions)
        except Exception as e:
            print("error", e, file=sys.stderr); continue
        a = res.answers
        j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3),
             "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
             "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2), "tokens": res.usage.input_tokens + res.usage.output_tokens}
        fo.write(json.dumps({"key": key, "state": state, "options": opts, "answer": j, "seed": r.get("seed"), "arm": "dagger_label"}) + "\n"); fo.flush(); n += 1; done.add(key)
        if n % 100 == 0: print(f"  labelled {n}  {time.time()-t0:.0f}s", flush=True)
    print(f"labelled {n} new states → {out}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

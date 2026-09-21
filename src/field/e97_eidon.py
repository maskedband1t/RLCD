"""E97: is this hour trainable? The calibrated judge as a data-quality annotator on Eidon's real teleop-style demonstrations,
from IMU-derived facts alone, scored against the dataset's own qc_status and task_type; beside an a-priori rule, a fitted
logistic baseline (2-fold) and the base rate.
  sample:  PYTHONPATH=src python src/field/e97_eidon.py sample --features data/eidon/e97_features_shard0.parquet --out results/field/e97_sample.json
  render:  ... render --n 3            (prints facts for a few recordings; no API)
  run:     ... run --out results/field/e97_answers.jsonl        (API; resumable)
  score:   ... score"""
import os, sys, json, time, argparse, random, math, numpy as np, pandas as pd
META = "data/eidon/recordings/metadata.parquet"
TASKS = {"folding_laundry": "folding laundry", "cleaning": "cleaning surfaces or floors", "doing_the_dishes": "doing the dishes", "cooking": "cooking", "drawing": "drawing",
         "knitting": "knitting", "making_the_bed": "making the bed", "watering_plants": "watering plants", "organizing": "organizing things"}
ROLE = ("You are the data-quality judge of a robot-learning team. Contributors record household chores wearing a chest camera and a seven-sensor IMU harness "
        "(both hands, both forearms, both shoulders, chest). You see only facts computed from the IMU motion stream; there is no video. Code executes your decision.")

def band(x, cuts, names):
    if x is None or (isinstance(x, float) and math.isnan(x)): return "unknown"
    for c, n in zip(cuts, names):
        if x < c: return n
    return names[-1]

def facts(f, task=None):
    d = {"recording": {"duration": band(f["duration_s"], [30, 90, 200], ["under_30_s", "30_to_90_s", "90_to_200_s", "over_200_s"]),
                       "sensors": "all_seven_present" if f["n_slots"] == 7 else f"missing_{f['slots_missing'].replace(',', '_and_')}",
                       "signal_gaps": band(f["dropout_frac"], [0.02, 0.10], ["none", "some_gaps", "large_gaps"]),
                       "sample_rate": "normal" if f["sample_hz"] > 22 else "low"},
         "hands": {"left_hand_motion": band(f["speed_left_hand"], [0.5, 1.2, 2.5], ["nearly_still", "gentle", "active", "vigorous"]),
                   "right_hand_motion": band(f["speed_right_hand"], [0.5, 1.2, 2.5], ["nearly_still", "gentle", "active", "vigorous"]),
                   "hand_use": band(f["hand_symmetry"], [0.35, 0.65], ["right_hand_dominant", "both_hands", "left_hand_dominant"]),
                   "hands_move_relative_to_torso": band(max(f.get("rel_var_left_hand", 0) or 0, f.get("rel_var_right_hand", 0) or 0), [0.1, 0.4], ["little", "moderately", "a_lot"]),
                   "time_with_both_hands_still": band(f["still_frac"], [0.05, 0.30], ["almost_none", "some_pauses", "mostly_still"])},
         "body": {"torso_motion": band(f["speed_chest"], [0.2, 0.5], ["standing_or_sitting_still", "shifting", "walking_around"]),
                  "shoulder_motion": band((f["speed_left_shoulder"] or 0 + f["speed_right_shoulder"] or 0) / 2, [0.4, 1.0], ["low", "moderate", "high"])}}
    if task: d["intended_task_as_logged_by_the_contributor"] = TASKS.get(task, task)
    return d

def rule(f):  # a-priori thresholds, written before any label was looked at; score = conditions met (0-4)
    c = [f["n_slots"] == 7, f["duration_s"] >= 30, f["still_frac"] < 0.5, f["dropout_frac"] < 0.10]; return int(all(c)), sum(c)

NUM = ["duration_s", "n_slots", "dropout_frac", "sample_hz", "speed_left_hand", "speed_right_hand", "speed_chest", "speed_left_forearm", "speed_right_forearm", "still_frac", "hand_symmetry", "rel_var_left_hand", "rel_var_right_hand", "orient_var_chest"]
def logistic_2fold(X, y, seed=0):
    """plain numpy logistic regression, two folds, returns out-of-fold probabilities"""
    rnd = np.random.RandomState(seed); idx = rnd.permutation(len(y)); folds = [idx[: len(y) // 2], idx[len(y) // 2:]]; p = np.zeros(len(y))
    for k in range(2):
        tr, te = folds[1 - k], folds[k]; mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-6; Xt = (X[tr] - mu) / sd; Xe = (X[te] - mu) / sd
        w = np.zeros(X.shape[1]); b = 0.0
        for _ in range(3000):
            z = Xt @ w + b; pr = 1 / (1 + np.exp(-z)); g = pr - y[tr]; w -= 0.05 * (Xt.T @ g / len(tr) + 1e-3 * w); b -= 0.05 * g.mean()
        p[te] = 1 / (1 + np.exp(-(Xe @ w + b)))
    return p

def auroc(p, y):
    p, y = np.asarray(p), np.asarray(y).astype(int); pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0: return float("nan")
    return float((np.sum(pos[:, None] > neg[None, :]) + 0.5 * np.sum(pos[:, None] == neg[None, :])) / (len(pos) * len(neg)))
def ece(p, y, bins=10):
    p, y = np.asarray(p), np.asarray(y).astype(float); e = 0.0
    for lo in np.linspace(0, 1, bins + 1)[:-1]:
        m = (p >= lo) & (p < lo + 1 / bins) if lo < 0.9 else (p >= lo); 
        if m.any(): e += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(e)

def sample(features, out, seed=0, valid_match=1.0, task_per_class=60):
    F = pd.read_parquet(features); M = pd.read_parquet(META); df = F.merge(M[["recording_id", "task_type", "qc_status", "good_frame_percent", "hand_presence_ratio"]], on="recording_id")
    rnd = random.Random(seed); bad = df[df.qc_status != "valid"]; good = df[df.qc_status == "valid"]
    trainability = list(bad.recording_id) + rnd.sample(list(good.recording_id), int(len(bad) * valid_match))
    task_ids = []
    for t, g in df.groupby("task_type"): ids = list(g.recording_id); rnd.shuffle(ids); task_ids += ids[:task_per_class]
    json.dump({"trainability": sorted(trainability), "task": sorted(task_ids)}, open(out, "w"))
    print(f"sample: trainability {len(trainability)} recordings ({len(bad)} non-valid: {bad.qc_status.value_counts().to_dict()}, {len(trainability) - len(bad)} valid) | task {len(task_ids)} ({df[df.recording_id.isin(task_ids)].task_type.value_counts().to_dict()})")

def run(features, sample_path, out, model="jev-latest"):
    from typesafe_sdk import TypeSafeClient, Choice
    client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"]); F = pd.read_parquet(features).set_index("recording_id"); M = pd.read_parquet(META).set_index("recording_id"); S = json.load(open(sample_path))
    done = set()
    if os.path.exists(out):
        for l in open(out): r = json.loads(l); done.add((r["q"], r["recording_id"]))
    todo = [("trainability", i) for i in S["trainability"] if ("trainability", i) not in done] + [("task", i) for i in S["task"] if ("task", i) not in done]
    print(f"run: {len(todo)} calls to make ({len(done)} already done)", flush=True); errors = 0
    with open(out, "a") as fo:
        for n, (q, rid) in enumerate(todo):
            f = F.loc[rid].to_dict(); task = M.loc[rid, "task_type"]
            if q == "trainability":
                state = facts(f, task); questions = {"usable": Choice(instructions={"role": ROLE, "ask": "Is this recording usable as a training demonstration for a manipulation policy? Keep only recordings a policy could learn the logged task from."},
                    criteria={"usable": "Keep it: the contributor was doing the logged task with their hands for a useful stretch of time, with complete, continuous sensor data.",
                              "not_usable": "Discard it: too short, hands mostly still or barely used, sensors missing or dropping out, or the motion does not fit the logged task."})}
            else:
                state = facts(f, None); questions = {"task": Choice(instructions={"role": ROLE, "ask": "Which household task was the contributor most likely doing in this recording?"}, criteria=dict(TASKS))}
            t0 = time.time()
            try: r = client.system_one(state=state, model=model, questions=questions)
            except Exception as e:
                errors += 1; print(f"  error {type(e).__name__} on {q} {rid}", flush=True)
                if errors >= 3: raise
                time.sleep(2); continue
            a = r.answers["usable" if q == "trainability" else "task"]
            fo.write(json.dumps({"q": q, "recording_id": int(rid), "choice": a.choice, "confidence": round(float(a.confidence), 4), "probabilities": {k: round(float(v), 4) for k, v in a.probabilities.items()},
                                 "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens, "model": model}) + "\n"); fo.flush(); errors = 0
            if n % 50 == 0: print(f"  {n}/{len(todo)} {q} {rid} -> {a.choice} {a.confidence:.2f}", flush=True)
    print("run: done", flush=True)

def score(features, sample_path, answers):
    F = pd.read_parquet(features).set_index("recording_id"); M = pd.read_parquet(META).set_index("recording_id"); S = json.load(open(sample_path))
    A = [json.loads(l) for l in open(answers)]; T = {r["recording_id"]: r for r in A if r["q"] == "trainability"}; K = {r["recording_id"]: r for r in A if r["q"] == "task"}
    ids = [i for i in S["trainability"] if i in T]; y = np.array([M.loc[i, "qc_status"] == "valid" for i in ids]).astype(int); status = np.array([M.loc[i, "qc_status"] for i in ids])
    pj = np.array([T[i]["probabilities"].get("usable", 0.0) for i in ids]); cj = (pj >= 0.5).astype(int)
    rb = np.array([rule(F.loc[i].to_dict())[0] for i in ids]); rs = np.array([rule(F.loc[i].to_dict())[1] for i in ids])
    X = np.nan_to_num(F.loc[ids, NUM].to_numpy(float)); pl = logistic_2fold(X, y)
    print(f"=== E97 trainability · n {len(ids)} (valid {y.sum()}, flagged {(status == 'flagged').sum()}, invalid {(status == 'invalid').sum()}) · base rate (always usable) acc {y.mean():.3f}")
    for name, pred, prob in [("judge (Jev)", cj, pj), ("a-priori rule", rb, rs / 4.0), ("logistic on the same facts, 2-fold", (pl >= 0.5).astype(int), pl)]:
        rec_inv = (pred[status == "invalid"] == 0).mean() if (status == "invalid").any() else float("nan"); rec_fl = (pred[status == "flagged"] == 0).mean() if (status == "flagged").any() else float("nan")
        print(f"  {name:36s} acc {np.mean(pred == y):.3f} | AUROC {auroc(prob, y):.3f} | catches invalid {rec_inv:.2f}, flagged {rec_fl:.2f} | says usable {pred.mean():.2f}" + (f" | ECE {ece(prob, y):.3f} mean p {prob.mean():.3f} vs valid rate {y.mean():.3f}" if name.startswith("judge") else ""))
    tids = [i for i in S["task"] if i in K]; yt = np.array([M.loc[i, "task_type"] for i in tids]); ct = np.array([K[i]["choice"] for i in tids]); pt = np.array([K[i]["confidence"] for i in tids])
    counts = pd.Series(yt).value_counts(); maj = counts.index[0]
    print(f"\n=== E97 task · n {len(tids)} over {len(counts)} classes ({counts.to_dict()}) · majority-class acc {np.mean(yt == maj):.3f} · chance {1/len(counts):.3f}")
    print(f"  judge acc {np.mean(ct == yt):.3f} | mean confidence {pt.mean():.3f} (over {pt.mean() - np.mean(ct == yt):+.3f}) | per class: " + ", ".join(f"{t} {np.mean(ct[yt == t] == t):.2f}" for t in counts.index))
    Xt = np.nan_to_num(F.loc[tids, NUM].to_numpy(float)); classes = list(counts.index); rnd = np.random.RandomState(0); idx = rnd.permutation(len(tids)); folds = [idx[: len(tids) // 2], idx[len(tids) // 2:]]; pred = np.empty(len(tids), dtype=object)
    for k in range(2):  # nearest-centroid on standardised facts, 2-fold: the dumb fitted baseline
        tr, te = folds[1 - k], folds[k]; mu, sd = Xt[tr].mean(0), Xt[tr].std(0) + 1e-6; Z = (Xt - mu) / sd; cents = {c: Z[tr][yt[tr] == c].mean(0) for c in classes if (yt[tr] == c).any()}
        for i in te: pred[i] = min(cents, key=lambda c: np.linalg.norm(Z[i] - cents[c]))
    print(f"  nearest-centroid on the same facts, 2-fold: acc {np.mean(pred == yt):.3f}")
    conf = pd.crosstab(pd.Series(yt, name="true"), pd.Series(ct, name="judge")); print(conf.to_string())

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["sample", "render", "run", "score"]); ap.add_argument("--features", default="data/eidon/e97_features_shard0.parquet"); ap.add_argument("--sample", default="results/field/e97_sample.json")
    ap.add_argument("--out", default="results/field/e97_answers.jsonl"); ap.add_argument("--n", type=int, default=3); ap.add_argument("--model", default="jev-latest"); a = ap.parse_args(); os.makedirs("results/field", exist_ok=True)
    if a.cmd == "sample": sample(a.features, a.out if a.out.endswith(".json") else a.sample)
    elif a.cmd == "render":
        F = pd.read_parquet(a.features); M = pd.read_parquet(META).set_index("recording_id")
        for _, f in F.sample(a.n, random_state=1).iterrows(): rid = int(f.recording_id); print(f"--- recording {rid} · qc {M.loc[rid, 'qc_status']} · task {M.loc[rid, 'task_type']} · rule {rule(f.to_dict())}"); print(json.dumps(facts(f.to_dict(), M.loc[rid, 'task_type']), indent=1))
    elif a.cmd == "run": run(a.features, a.sample, a.out, a.model)
    else: score(a.features, a.sample, a.out)

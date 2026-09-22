"""E115: the judge as a rule-drafting instrument. Compile the judge's recorded decisions on the unseen bank into a small decision
tree over the same categorical facts the rule programs read, print it as if/else rules, and run it as an arm in front of the
frozen rules (`rules_mined`: the tree decides where its leaf is pure enough, otherwise the frozen program does). Two variants:
every decision the judge made, or only the decisions the operator would not have vetoed (inside code's acceptable set;
`rules_mined_clean`). Usage:
  python src/duck/e115_mine.py --records results/duck/e102_record.jsonl --arm jev --seeds 70-99 --out results/duck/mined_duck_all [--clean]"""
import os, sys, json, argparse
import numpy as np

NOTE_WORDS = ["child", "follow", "right of way", "phone", "sharp", "only the person who asked"]

def canon(key, f):
    """hand_to_<name> becomes hand_to_asker / hand_to_other so the label generalises across rooms."""
    if key.startswith("hand_to_"):
        name = key[len("hand_to_"):]; asked = any(q["name"] == name and q["asked_for_the_object"] for q in f.get("people", []))
        return "hand_to_asker" if asked else "hand_to_other"
    return key

def decanon(label, f, opts):
    if label in ("hand_to_asker", "hand_to_other"):
        want = label == "hand_to_asker"
        for k in opts:
            if k.startswith("hand_to_") and any(q["name"] == k[len("hand_to_"):] and q["asked_for_the_object"] == want for q in f.get("people", [])): return k
        return None
    return label

def features(f, opts):
    x = {}
    for k, v in f["robot"].items(): x[f"robot.{k}={v}"] = 1
    for k, v in f.get("person", {}).items(): x[f"person.{k}={v}"] = 1
    for q in f.get("people", []):
        if q.get("asked_for_the_object"):
            for k in ("distance", "attention", "kind", "motion"): x[f"asker.{k}={q.get(k)}"] = 1
        if q.get("kind") == "child": x[f"child.distance={q.get('distance')}"] = 1; x[f"child.attention={q.get('attention')}"] = 1
    notes = " ".join(f.get("notes_from_operators", [])).lower()
    for w in NOTE_WORDS: x[f"note:{w}"] = int(w in notes)
    for o in opts: x["opt:hand" if o.startswith("hand_to_") else f"opt:{o}"] = 1
    return x

def mined_choice(model, f, opts, tau=0.6):
    """The drafted clause's answer, or None where its leaf is not pure enough or its action is not on offer."""
    x = model["vec"].transform([features(f, opts)]); pr = model["tree"].predict_proba(x)[0]; i = int(np.argmax(pr))
    key = decanon(model["classes"][i], f, opts)
    return (key, float(pr[i])) if pr[i] >= tau and key in opts else None

def load(paths, arm, seeds):
    rows = []
    for p in paths:
        for l in open(p):
            if not l.strip(): continue
            r = json.loads(l)
            if r["arm"] == arm and r["seed"] in seeds: rows.append(r)
    return rows

def main():
    import joblib
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.tree import DecisionTreeClassifier, export_text
    ap = argparse.ArgumentParser(); ap.add_argument("--records", nargs="+", required=True); ap.add_argument("--arm", default="jev"); ap.add_argument("--seeds", default="70-99")
    ap.add_argument("--out", required=True); ap.add_argument("--clean", action="store_true"); ap.add_argument("--depth", type=int, default=6); ap.add_argument("--leaf", type=int, default=15); a = ap.parse_args()
    lo, hi = map(int, a.seeds.split("-")); rows = load(a.records, a.arm, set(range(lo, hi + 1))); n_all = len(rows)
    if a.clean: rows = [r for r in rows if r["answer"]["choice"] in r["acceptable"]]
    X = [features(r["state"], r["options"]) for r in rows]; y = [canon(r["answer"]["choice"], r["state"]) for r in rows]
    vec = DictVectorizer(sparse=False); Xm = vec.fit_transform(X)
    tree = DecisionTreeClassifier(max_depth=a.depth, min_samples_leaf=a.leaf, random_state=0).fit(Xm, y)
    names = [n.replace("=", " is ") for n in vec.get_feature_names_out()]
    text = export_text(tree, feature_names=names, show_weights=True, max_depth=a.depth)
    joblib.dump({"vec": vec, "tree": tree, "classes": [str(c) for c in tree.classes_]}, a.out + ".pkl"); open(a.out + ".txt", "w").write(text)
    print(f"{os.path.basename(a.out)}: {n_all} judge decisions, {len(rows)} used ({'inside the acceptable set only' if a.clean else 'all'}) | leaves {tree.get_n_leaves()} | depth {tree.get_depth()} | agreement with the judge on its own decisions {tree.score(Xm, y):.3f} | classes {sorted(set(y))}")

if __name__ == "__main__": main()

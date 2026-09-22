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

STOP = set("the a an and or of to in on at for with from by is are be it its this that they them their there here when if do not no any all into out up down about over under only even ever before after until while as so than then also very just today".split())

def flatten(prefix, v, x):
    if isinstance(v, dict):
        for k, w in v.items(): flatten(f"{prefix}.{k}" if prefix else k, w, x)
    elif isinstance(v, (list, tuple, set)):
        for w in v:
            if isinstance(w, (str, int, float, bool)): x[f"{prefix}={w}"] = 1
    elif isinstance(v, bool): x[f"{prefix}={v}"] = 1
    elif isinstance(v, (str, int, float)): x[f"{prefix}={v}"] = 1

def features(f, opts):
    """Every categorical fact as a present/absent feature, body-agnostic: the fact dicts flattened (task, notes, recent actions
    and the people list handled separately), the notes as a bag of words, the options on offer."""
    x = {}
    for k, v in f.items():
        if k in ("task", "notes_from_operators", "recent_actions", "people", "options"): continue
        flatten(k, v, x)
    for q in f.get("people", []):
        if q.get("asked_for_the_object"):
            for k in ("distance", "attention", "kind", "motion"): x[f"asker.{k}={q.get(k)}"] = 1
        if q.get("kind") == "child": x[f"child.distance={q.get('distance')}"] = 1; x[f"child.attention={q.get('attention')}"] = 1
    import re as _re
    for w in set(_re.findall(r"[a-z]+", " ".join(f.get("notes_from_operators", [])).lower())):
        if len(w) >= 4 and w not in STOP: x[f"note:{w}"] = 1
    for o in opts: x["opt:hand" if o.startswith("hand_to_") else f"opt:{o}"] = 1
    return x

def present(x): return {k for k, v in x.items() if v}

def mined_choice(model, f, opts, tau=0.6):
    """The drafted clause's answer, or None where its leaf is not pure enough or its action is not on offer. A scoped draft (E115b)
    also answers None unless the state carries a feature absent from the judge's anticipated-bank records (the old vocabulary)."""
    fx = features(f, opts)
    if model.get("old_vocab") is not None and not (present(fx) - model["old_vocab"]): return None
    x = model["vec"].transform([fx]); pr = model["tree"].predict_proba(x)[0]; i = int(np.argmax(pr))
    key = decanon(model["classes"][i], f, opts)
    return (key, float(pr[i])) if pr[i] >= tau and key in opts else None

PREFER = {"pick": ["done", "put_back", "place_in_return_bin", "place_in_customer_tote", "grasp", "regrasp", "scan_again", "wait", "ask_operator", "skip_item"],
          "g1": ["done", "pick_up", "walk", "walk_slow", "step_around", "wait", "stop", "turn_away", "ask_operator", "put_down"],
          "duck": ["done", "follow_person", "walk_fast", "walk_slow", "wait", "step_aside", "stop", "turn_away", "ask_operator"]}

def corrected_label(r, body):
    """The operator's replacement for a vetoed decision: the oracle's first acceptable action (hand-overs canonised)."""
    acc = set(r["acceptable"]); opts = r["options"]
    for k in PREFER[body]:
        if k in acc and k in opts: return canon(k, r["state"])
    for k in sorted(acc):
        if k.startswith("hand_to_") and k in opts: return canon(k, r["state"])
    return canon(sorted(acc)[0], r["state"]) if acc else canon(r["answer"]["choice"], r["state"])

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
    ap.add_argument("--out", required=True); ap.add_argument("--clean", action="store_true"); ap.add_argument("--depth", type=int, default=6); ap.add_argument("--leaf", type=int, default=15)
    ap.add_argument("--old-records", nargs="*", default=[]); ap.add_argument("--old-seeds", default="0-39"); ap.add_argument("--corrected", action="store_true", help="relabel vetoed decisions with the operator's replacement (the oracle's first acceptable action)"); ap.add_argument("--body", default=os.environ.get("DUCK_BODY", "duck")); a = ap.parse_args()
    lo, hi = map(int, a.seeds.split("-")); rows = load(a.records, a.arm, set(range(lo, hi + 1))); n_all = len(rows)
    if a.clean: rows = [r for r in rows if r["answer"]["choice"] in r["acceptable"]]
    body = {"g1": "g1", "pick": "pick"}.get(a.body, "duck")
    X = [features(r["state"], r["options"]) for r in rows]
    y = [(corrected_label(r, body) if (a.corrected and r["answer"]["choice"] not in r["acceptable"]) else canon(r["answer"]["choice"], r["state"])) for r in rows]
    n_fixed = sum(1 for r in rows if a.corrected and r["answer"]["choice"] not in r["acceptable"])
    vec = DictVectorizer(sparse=False); Xm = vec.fit_transform(X)
    tree = DecisionTreeClassifier(max_depth=a.depth, min_samples_leaf=a.leaf, random_state=0).fit(Xm, y)
    names = [n.replace("=", " is ") for n in vec.get_feature_names_out()]
    text = export_text(tree, feature_names=names, show_weights=True, max_depth=a.depth)
    old_vocab = None; scope = ""
    if a.old_records:
        olo, ohi = map(int, a.old_seeds.split("-")); old = load(a.old_records, a.arm, set(range(olo, ohi + 1)))
        old_vocab = set().union(*[present(features(r["state"], r["options"])) for r in old]); new_feats = sorted(set().union(*[present(x) for x in X]) - old_vocab)
        scope = f" | scoped: {len(old)} old decisions, {len(old_vocab)} old features; new features in the mined states: {new_feats}"
    joblib.dump({"vec": vec, "tree": tree, "classes": [str(c) for c in tree.classes_], "old_vocab": old_vocab}, a.out + ".pkl"); open(a.out + ".txt", "w").write(text + "\n" + scope + "\n")
    print(f"{os.path.basename(a.out)}: {n_all} judge decisions, {len(rows)} used ({'inside the acceptable set only' if a.clean else ('all, ' + str(n_fixed) + ' vetoed decisions relabelled with the operator replacement' if a.corrected else 'all')}) | leaves {tree.get_n_leaves()} | depth {tree.get_depth()} | agreement with the judge on its own decisions {tree.score(Xm, y):.3f} | classes {sorted(set(y))}{scope}")

if __name__ == "__main__": main()

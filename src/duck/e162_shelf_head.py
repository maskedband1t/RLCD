"""E162: a shelf-life head learned from operation rather than asked for.
Trained on the no-skip baseline's own records: given the facts now and the action chosen last time, would reusing that
action still be acceptable? Categorical features only (E115's extractor), so the gate costs microseconds and can sit in
front of a model call it then does not make."""
import sys, os, json, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from duck.e115_mine import features
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

def build(records, arm="jev"):
    by = collections.defaultdict(list)
    for r in records:
        if r["arm"] == arm: by[r["seed"]].append(r)
    rows = []
    for seed, rs in by.items():
        for prev, cur in zip(rs, rs[1:]):
            pc = (prev.get("answer") or {}).get("choice"); acc = cur.get("acceptable") or []
            if not pc or not acc: continue
            rows.append((seed, feats(cur.get("state") or {}, cur.get("options") or {}, pc), 1 if pc in acc else 0))
    return rows

def feats(state, options, last_action):
    x = features(state, options)
    x[f"last_action={last_action}"] = 1
    x["last_action_still_offered"] = 1 if last_action in (options or {}) else 0
    return x

if __name__ == "__main__":
    rec = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    out = sys.argv[2]; train_max = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    rows = build(rec)
    tr = [r for r in rows if r[0] < train_max]; te = [r for r in rows if r[0] >= train_max]
    v = DictVectorizer(sparse=True)
    Xtr = v.fit_transform([r[1] for r in tr]); ytr = np.array([r[2] for r in tr])
    m = LogisticRegression(max_iter=2000).fit(Xtr, ytr)
    rep = {"n_train": len(tr), "auroc_train": float(roc_auc_score(ytr, m.predict_proba(Xtr)[:, 1]))}
    if te:
        Xte = v.transform([r[1] for r in te]); yte = np.array([r[2] for r in te])
        rep["n_test"] = len(te); rep["auroc_heldout"] = float(roc_auc_score(yte, m.predict_proba(Xte)[:, 1]))
    pickle.dump({"vec": v, "clf": m, "trained_on_seeds_below": train_max}, open(out, "wb"))
    print(json.dumps(rep, indent=1)); print("saved", out)

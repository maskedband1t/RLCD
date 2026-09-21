"""E78: does the note-binding Noul make reading errors visible? AUROC(P(applies) → truth differs from the default rule)."""
import json, sys, collections
import numpy as np
from .decision_eval import seed_index, signature, auroc
from .episodes import COLOURS

def main(path):
    idx = seed_index(); rows = [json.loads(l) for l in open(path)]
    L = []; dest_ok = []
    for r in rows:
        a = r["answer"]
        if "note_applies" not in a: continue
        sig = signature(r["state"]["parts"]); seed, spec = idx[sig]; pid = a["part"]
        p = next(q for q in r["state"]["parts"] if q["id"] == pid); t = spec["truth"][pid]
        default = "ask" if (p["fragile"] == "unknown" or p["colour"] not in COLOURS) else ("inspection" if p["looks_damaged"] else p["colour"])
        differs = (t["dest"] != default) or t["must_ask"]
        L.append((a["note_applies"], differs, seed, spec["events"]["unanticipated"]["kind"]))
        if a["note_applies"] >= 0.5:
            nd = a["note_destination"]; dest_ok.append((nd == t["dest"]) or (nd == "ask_operator" and t["must_ask"]))
    conf = [x[0] for x in L]; lab = [x[1] for x in L]
    print(f"binding decisions {len(L)} (parts with a note present); truth-differs share {100*np.mean(lab):.1f}%; AUROC(P(applies) → differs) {auroc(conf, lab):.3f}")
    for lo, hi in [(0, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
        sel = [l for c, l in zip(conf, lab) if lo <= c < hi]
        if sel: print(f"   P(applies) [{lo:.1f},{hi:.1f}): n={len(sel):>3} truth differs {100*np.mean(sel):5.1f}%")
    print(f"when applies ≥ .5: note_destination correct {100*np.mean(dest_ok):.1f}% (n={len(dest_ok)})")
    by = collections.defaultdict(list)
    for c, l, s, k in L: by[k].append((c, l))
    for k, v in sorted(by.items()):
        print(f"   {k:<18} n={len(v):>3} AUROC {auroc([x[0] for x in v], [x[1] for x in v]):.3f}  mean P(applies) when differs {np.mean([c for c,l in v if l]) if any(l for c,l in v) else float('nan'):.2f} / when not {np.mean([c for c,l in v if not l]) if any(not l for c,l in v) else float('nan'):.2f}")

if __name__ == "__main__":
    main(sys.argv[1])

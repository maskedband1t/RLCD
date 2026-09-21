"""E79: score the once-per-episode note extraction against the event semantics, by code."""
import json, sys, collections
from .decision_eval import seed_index, signature

EXPECT = {  # kind -> (colour, size, lot, shape, destination, overrides_damage>=.5, singular>=.5); None = don't care
    "relabel": ("violet", "any", "any", "any", "amber", False, False),
    "recall": ("jade", "small", "B", "any", "inspection", False, False),
    "cosmetic": (None, "any", "any", "SHAPE", "keep_default_colour_tray", True, None),
    "reroute_on_block": ("TRAY", "any", "any", "any", "inspection", False, False),
    "ambiguous": ("any", "small", "any", "any", "violet", False, True),
}

def main(path):
    idx = seed_index(); rows = [json.loads(l) for l in open(path) if '"note_read"' in l]
    ok_all = 0; n = 0; per = collections.defaultdict(list)
    for r in rows:
        sig = signature([dict(p, shape=p["shape"], lot=p["lot"]) for p in r["state"]["parts_present"]] ) if False else None
        # match seed by parts_present signature
        parts = [dict(id=p["id"], colour=p["colour"], shape=p["shape"], size=p["size"], lot=p["lot"]) for p in r["state"]["parts_present"]]
        sig = signature(parts)
        if sig not in idx: continue
        seed, spec = idx[sig]; u = spec["events"]["unanticipated"]; kind = u["kind"]
        if kind not in EXPECT: continue
        a = r["answer"]; exp = EXPECT[kind]
        exp_shape = next(p["shape"] for p in spec["parts"] if p["id"] == u.get("part")) if exp[3] == "SHAPE" else exp[3]
        exp_colour = u.get("tray") if exp[0] == "TRAY" else exp[0]
        checks = {
            "colour": exp_colour is None or a["colour_condition"] == exp_colour,
            "size": a["size_condition"] == exp[1], "lot": a["lot_condition"] == exp[2],
            "shape": exp_shape is None or a["shape_condition"] == exp_shape,
            "destination": a["destination"] == exp[4],
            "overrides_damage": (a["overrides_damage"] >= .5) == exp[5],
            "singular": exp[6] is None or (a["singular"] >= .5) == exp[6],
        }
        full = all(checks.values()); ok_all += full; n += 1
        per[kind].append((seed, u.get("wording"), full, [k for k, v in checks.items() if not v]))
    print(f"note extractions scored: {n}; fully correct {ok_all}/{n}")
    for k, L in sorted(per.items()):
        print(f"  {k:<18} {sum(x[2] for x in L)}/{len(L)} correct; misses: " + "; ".join(f"seed {s} w{w}: {','.join(m)}" for s, w, f, m in L if not f))

if __name__ == "__main__":
    main(sys.argv[1])

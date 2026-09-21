"""D4e · which unflagged surprise types each model handles (pre-registered 2026-09-19 23:31 PDT). Existing episodes:
E83 (jev, jev_gate0.7, rules, rules_ask, oracle), E88 (jev_confirm0.7), D4d (sj, sj_gate0.7, sj_confirm0.7)."""
import json, sys, collections
sys.path.insert(0, "src")
from cell.analyze import wilson
from cell.episodes import UNFLAGGED

def load(p): return [json.loads(l) for l in open(p) if l.strip()]
rows = load("results/cell/e83_unflagged.jsonl") + load("results/cell/e88_unflagged.jsonl") + load("results/cell/d4d_sj_unflagged.jsonl")
import os
if os.path.exists("results/cell/d8_preview_unflagged.jsonl"):
    for r in load("results/cell/d8_preview_unflagged.jsonl"): r = dict(r); r["arm"] = r["arm"].replace("jev", "jevp", 1); rows.append(r)
by = collections.defaultdict(dict)
for r in rows: by[r["arm"]][r["seed"]] = (r["unanticipated"], bool(r["unanticipated_correct"]), r["n_asks"], r["parts_correct"], r["n_parts"])
arms = ["rules", "rules_ask", "jev", "jevp", "sj", "jev_gate0.7", "jevp_gate0.7", "sj_gate0.7", "jev_confirm0.7", "sj_confirm0.7", "oracle"]
print(f"{'arm':<16}" + "".join(f"{t:>28}" for t in UNFLAGGED) + f"{'all':>22}")
tab = {}
for a in arms:
    if a not in by: continue
    cells = []; tab[a] = {}
    for t in UNFLAGGED + ["all"]:
        sel = [v for v in by[a].values() if t == "all" or v[0] == t]; k = sum(v[1] for v in sel); n = len(sel); w = wilson(k, n) if n else (0, 0, 0); lo, hi = w[-2], w[-1]
        tab[a][t] = (k, n); cells.append(f"{k:>2}/{n:<2} {100*k/n:5.1f}% [{100*lo:4.1f},{100*hi:5.1f}]" if n else "–")
    print(f"{a:<16}" + "".join(f"{c:>28}" for c in cells[:-1]) + f"{cells[-1]:>22}")
# P4e.2: the 27B's handled seeds inside Jev's
for a, b in [("sj", "jev"), ("sj_gate0.7", "jev_gate0.7"), ("sj_confirm0.7", "jev_confirm0.7"), ("jevp", "jev"), ("jevp_gate0.7", "jev_gate0.7")]:
    if a in by and b in by:
        sa = {s for s, v in by[a].items() if v[1]}; sb = {s for s, v in by[b].items() if v[1]}
        print(f"\n{a} handles {len(sa)} seeds; of those {len(sa & sb)} also handled by {b} ({100*len(sa&sb)/max(1,len(sa)):.0f}%); {b} handles {len(sb)}; {a} handles {len(sa - sb)} that {b} misses: {sorted(sa - sb)}; {b} handles {len(sb - sa)} that {a} misses: {sorted(sb - sa)}")
# per-seed pattern by type
print("\nper seed (type | rules jev sj | gate: jev sj | confirm: jev sj)  ✓ handled · × missed")
for t in UNFLAGGED:
    line = []
    for s in sorted(by["jev"]):
        if by["jev"][s][0] != t: continue
        m = lambda a: ("✓" if by[a][s][1] else "×") if a in by and s in by[a] else "?"
        line.append(f"{s:>2}:{m('rules')}{m('jev')}{m('sj')} {m('jev_gate0.7')}{m('sj_gate0.7')} {m('jev_confirm0.7')}{m('sj_confirm0.7')}")
    print(f"{t:<17}" + "  ".join(line))
# P4e.3: gating deltas per type
print("\ngate .7 minus ungated, handled count per type:")
for base, g in [("jev", "jev_gate0.7"), ("sj", "sj_gate0.7"), ("jev", "jev_confirm0.7"), ("sj", "sj_confirm0.7")]:
    print(f"  {g:<16} vs {base:<4}: " + ", ".join(f"{t} {tab[g][t][0]-tab[base][t][0]:+d}" for t in UNFLAGGED))
json.dump({a: {t: list(v) for t, v in d.items()} for a, d in tab.items()}, open("results/cell/d4e_unflagged_types.json", "w"), indent=1)

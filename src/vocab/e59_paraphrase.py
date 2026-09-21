"""Run the paraphrase set through three arms, REPEATS times each; per-cell passes and flips."""
import collections, json, sys
from concurrent.futures import ThreadPoolExecutor
from dispatch import ask, decide_by_cost, prepare_state, prepare_state_jev
from dispatch.paraphrase import P

REPEATS = 2
ARMS = {"raw": lambda st: st, "regex": prepare_state, "jev": prepare_state_jev}
cats = [c for c in dict.fromkeys(s["cat"] for s in P)]

def trial(args):
    s, arm, rep = args
    a = ask(ARMS[arm](s["st"])); d, _ = decide_by_cost(a)
    return s["cat"], s["name"], arm, rep, d in s["ok"], (a or {}).get("p_success"), (a or {}).get("rule_conflict")

jobs = [(s, arm, r) for s in P for arm in ARMS for r in range(REPEATS)]
with ThreadPoolExecutor(6) as ex: rows = list(ex.map(trial, jobs))

cell = collections.defaultdict(list); per = collections.defaultdict(dict)
for cat, name, arm, rep, ok, p, c in rows:
    cell[(cat, arm)].append(ok); per[(name, arm)][rep] = ok
flips = collections.Counter((n.split(" #")[0], a) for (n, a), d in per.items() if len(set(d.values())) > 1)

print(f"{'category':18s}" + "".join(f"{a:>8s}" for a in ARMS) + "    (passes / 10; flips in brackets)")
tot = collections.Counter()
for cat in cats:
    line = f"{cat:18s}"
    for arm in ARMS:
        k = sum(cell[(cat, arm)]); tot[arm] += k
        line += f"{k:>5d}" + (f"[{flips[(cat, arm)]}]" if flips[(cat, arm)] else "   ")
    print(line)
print(f"{'ALL':18s}" + "".join(f"{tot[a]:>5d}/70" for a in ARMS))
json.dump({"rows": rows, "repeats": REPEATS}, open("notes/e59.json", "w"))

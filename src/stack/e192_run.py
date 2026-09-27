"""E192: does perception create a decision code cannot make? Per-mode breakdown is the result, not the headline."""
import json, subprocess, sys, time
from collections import defaultdict
from stack.table_run import episode
from stack.percept import Perceived, options_with_look, MODES, ANTICIPATED
from stack.percept_arms import NullTrust, AlwaysVerify, Code3, CodeAll
from stack.percept_jev import PerceptJev, PerceptJevRank
from stack.table_arms import TableRules
from stack.table_plans import MINE_PLAN, MINE_CONT
from humanoid.table_sim import TableRoom

SEEDS = int(sys.argv[1]) if len(sys.argv) > 1 else 25
RECOVER = len(sys.argv) > 2 and sys.argv[2] == "recover"
SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "nogit"
RUN = time.strftime("%Y-%m-%dT%H:%M:%S")

ARMS = [("null_trust", NullTrust), ("code_3", Code3), ("code_all", CodeAll),
        ("always_verify", AlwaysVerify), ("jev_trust", PerceptJev), ("jev_rank", PerceptJevRank),
        ("rules", TableRules)]

from stack.percept import validate_doses, CHANNEL, SIGNATURE
if not validate_doses(SEEDS):
    sys.exit("dose gate FAILED -- a mode that cannot change the outcome cannot be measured. Aborting before any arm runs.")
print()
rows, table, bymode = [], {}, defaultdict(dict)
# `censored` is success among the episodes the robot stayed upright: the chooser-attributable number, reported beside
# the raw one because E192e showed a recovered plan can topple the legs while the chooser was right (and vice versa).
H = (f"{'arm':<15}{'success':>9}{'censored':>10}{'cleared':>9}{'broken':>7}{'viol':>6}{'FELL':>6}"
     f"{'looks':>7}{'calls':>7}{'err':>5}{'teleop x':>10}")
from stack.percept import LOOK_BUDGET, LOOK_S
print(f"E192  run={RUN} sha={SHA}  seeds={SEEDS}  recovery={'ON' if RECOVER else 'OFF'}  "
      f"look_budget={LOOK_BUDGET}  look_cost={LOOK_S}s")
print(H); print("-" * len(H), flush=True)

for label, mk in ARMS:
    arm = mk(); agg = defaultdict(int); t = 0.0; per = {}
    for seed in range(SEEDS):
        room = Perceived(TableRoom(seed), seed)
        rec, _ = episode(seed, arm, MINE_PLAN, MINE_CONT, room=room, opts_fn=options_with_look,
                         recover=RECOVER)
        rec.update(arm=label, mode=room.mode, looks=room.looks, run=RUN, sha=SHA, seed=seed,
                   recovery=RECOVER)
        rows.append(rec); per[seed] = rec["success"]
        agg["ok"] += rec["success"]; agg["clr"] += rec["cleared"]; agg["brk"] += rec["broken"]
        agg["viol"] += rec["workspace_violations"]; agg["looks"] += room.looks; t += rec["t_end"]
        agg["fell"] += rec["fell"]
        if not rec["fell"]: agg["up"] += 1; agg["ok_up"] += rec["success"]
    table[label] = per
    print(f"{label:<15}{agg['ok']:>6}/{SEEDS}{agg['ok_up']:>7}/{agg['up']:<2}{agg['clr']:>7}/{SEEDS*3}"
          f"{agg['brk']:>7}{agg['viol']:>6}{agg['fell']:>6}{agg['looks']:>7}"
          f"{getattr(arm,'calls',0):>7}{getattr(arm,'errors',0):>5}{t/SEEDS/62.5:>10.2f}", flush=True)
    if getattr(arm, "first_error", None): print(f"    first error: {arm.first_error}", flush=True)
    if getattr(arm, "gated", 0): print(f"    confidence gate fired {arm.gated}/{arm.calls} decisions", flush=True)
    for m in MODES:
        ss = [s for s in range(SEEDS) if MODES[(s // len(MODES)) % len(MODES)] == m]
        bymode[label][m] = (sum(per[s] for s in ss), len(ss))

print(f"\nper mode (anticipated = {', '.join(ANTICIPATED)} | held out = {', '.join(MODES[3:])})")
hdr = f"{'arm':<15}" + "".join(f"{m:>17}" for m in MODES)
print(hdr); print("-" * len(hdr))
for label, _ in ARMS:
    print(f"{label:<15}" + "".join(f"{bymode[label][m][0]}/{bymode[label][m][1]:<15}" for m in MODES), flush=True)

print("\nheld-out modes only (E192.2, E192.3, E192.4)")
for label, _ in ARMS:
    h = sum(bymode[label][m][0] for m in MODES[3:]); n = sum(bymode[label][m][1] for m in MODES[3:])
    a = sum(bymode[label][m][0] for m in ANTICIPATED); an = sum(bymode[label][m][1] for m in ANTICIPATED)
    print(f"  {label:<15} anticipated {a}/{an}    held out {h}/{n}")

import os as _os
_b = _os.environ.get("E192_LOOK_BUDGET", "0")
_sfx = f"_budget{_b}" if _b not in ("0", "") else ""
out = f"results/table/e192{'_recover' if RECOVER else ''}{_sfx}.jsonl"
with open(out, "w") as f:
    for r in rows: f.write(json.dumps(r) + "\n")
print(f"\nwrote {out} ({len(rows)} rows)")

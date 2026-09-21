"""E60: recurrence category vs. a control set of resolved-with-history notes."""
import collections
from concurrent.futures import ThreadPoolExecutor
from dispatch import TaskState, ask, decide_by_cost, prepare_state_jev
from dispatch.scenarios import ROBOT_GOOD, OPS_FREE

PICK = {"spec": "move tote 12 to shelf C", "type": "pick_place"}
RECUR = ["left wheel seized up twice this morning, freed it by hand both times",
         "gripper has jammed three times since 08:00; each time it released after a power cycle",
         "keeps losing localisation every 20-30 minutes, recovers on its own each time",
         "right drive motor cut out twice on the ramp today, restarted fine both times",
         "camera feed dropped four times this morning, comes back after a few seconds",
         "stalls intermittently on turns - happened again 10 minutes ago, cleared itself"]
RESOLVED_HIST = ["stalled twice last week; root-caused to a loose connector, fixed Friday, no recurrence in 60 tasks",
                 "the gripper jams from Monday were traced to debris; cleaned and verified, none since",
                 "localisation drops last month were a firmware bug, patched 09/02, clean since",
                 "wheel bearing that seized in August was replaced; 200+ tasks since with no issue",
                 "had three stalls on the ramp yesterday; ramp sensor recalibrated this morning and test-driven clean"]
RESOLVED = ["drifted left at 09:00; recalibrated 09:30, verified fine since",
            "wheel 3 bearing replaced 07:45, test-driven 20 min, no noise",
            "gripper fault from yesterday fixed overnight, running fine all morning",
            "stall issue cleared by firmware update, no recurrence in 40 tasks",
            "drive motor swapped at 08:00 and verified under load"]
SETS = {"RECUR": (RECUR, {"supervised", "handoff"}), "RESOLVED_HIST": (RESOLVED_HIST, {"autonomous"}),
        "RESOLVED": (RESOLVED, {"autonomous"})}

def st(note): return TaskState(task=PICK, operator=OPS_FREE, site={"conditions": "normal", "local_time": "14:00"},
                               robot={**ROBOT_GOOD, "operator_note": note})
def trial(a):
    name, note, ok, arm, rep = a; tr = {}
    s = st(note) if arm == "raw" else prepare_state_jev(st(note), trace=tr)
    ans = ask(s); d, _ = decide_by_cost(ans)
    promoted = any("APPLIES NOW" in r for r in s.get("site", {}).get("rules", []))
    pr = tr.get("note_0", (None, {}))[1]
    return name, note, arm, d in ok, promoted, pr

jobs = [(n, w, ok, arm, r) for n, (ws, ok) in SETS.items() for w in ws for arm in ("raw", "jev") for r in range(2)]
with ThreadPoolExecutor(6) as ex: rows = list(ex.map(trial, jobs))
cell = collections.defaultdict(list); prom = collections.Counter(); seen = {}
for name, note, arm, ok, promoted, pr in rows:
    cell[(name, arm)].append(ok); prom[(name, arm)] += promoted
    if arm == "jev": seen[(name, note)] = pr
for name in SETS:
    n = len(cell[(name, "jev")])
    print(f"{name:14s} raw {sum(cell[(name,'raw')]):2d}/{n}   jev {sum(cell[(name,'jev')]):2d}/{n}   promoted {prom[(name,'jev')]}/{n}")
print("\nper-wording verdicts (jev): current / recurring / resolved")
for (name, note), pr in seen.items():
    print(f"  {name:13s} c{pr.get('current_fault',0):.2f} r{pr.get('intermittent_or_recurring',0):.2f} ok{pr.get('resolved_or_none',0):.2f}  « {note[:78]}")

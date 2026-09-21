"""Constructed dispatch scenarios with answers correct BY CONSTRUCTION.

Not a validation of outcome prediction. A behavioural test of whether the
decision logic reads the state. `ok` is the set of acceptable decisions.
"""
from dispatch import TaskState

ROBOT_GOOD = {"attempts_this_task_type_here": 20, "succeeded": 19}
OPS_FREE = {"available": 2, "of": 3, "robots_per_operator_now": 6}
OPS_NONE = {"available": 0, "of": 3, "robots_per_operator_now": 14}
DOCK_RULE = "no autonomous operation within 3 m of the loading dock after 16:00"

S = [
 # ---------------- tier 1: one clear signal ----------------------------
 dict(tier=1, name="routine, strong history", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=1, name="explicit rule applies", ok={"supervised", "handoff"}, conflict=True,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE], "location": "1 m from loading dock",
                         "local_time": "16:20"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=1, name="terrible history", ok={"supervised", "handoff"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={"attempts_this_task_type_here": 20, "succeeded": 4},
                   operator=OPS_FREE)),
 # ---------------- tier 2: combine two fields -------------------------
 dict(tier=2, name="fragile + drifting robot", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "restock glassware, FRAGILE", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={**ROBOT_GOOD, "operator_note": "drifting left since 11:00, uncorrected"},
                   operator=OPS_FREE)),
 dict(tier=2, name="good history, first time at site", ok={"supervised"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place",
                         "seen_at_this_site_before": False},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={"attempts_this_task_type_elsewhere": 40, "succeeded": 38,
                          "attempts_this_task_type_here": 0},
                   operator=OPS_FREE)),
 dict(tier=2, name="wet floor + heavy load", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "carry 18 kg case across bay 2", "type": "carry"},
                   site={"conditions": "floor wet across bay 2 after a spill", "local_time": "10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 # ---------------- tier 3: the condition does NOT apply ----------------
 dict(tier=3, name="dock rule, but it is 15:40", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE], "location": "1 m from loading dock",
                         "local_time": "15:40"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=3, name="dock rule, 16:20, but 40 m away", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE], "location": "aisle 9, 40 m from loading dock",
                         "local_time": "16:20"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=3, name="note is stale and resolved", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "14:00"},
                   robot={**ROBOT_GOOD, "operator_note": "drifted left at 09:00; recalibrated 09:30, verified fine since"},
                   operator=OPS_FREE)),
 # ---------------- tier 4: conflict, no clean answer -------------------
 dict(tier=4, name="rule forbids autonomous, no operators", ok={"supervised", "handoff"}, conflict=True,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE], "location": "1 m from loading dock",
                         "local_time": "16:20"},
                   robot=ROBOT_GOOD, operator=OPS_NONE)),
 dict(tier=4, name="great history vs. fresh alarming note", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={"attempts_this_task_type_here": 200, "succeeded": 198,
                          "operator_note": "gripper made a grinding noise on the last attempt"},
                   operator=OPS_FREE)),
]

# ---------------- tier 5: aimed at what tier 2 exposed, plus adversarial ----
WET = "floor wet across bay 2 after a spill"
S5 = [
 # A/B: the SAME hazard as a condition vs as a rule
 dict(tier=5, name="A: wet floor as CONDITION, 18 kg", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "carry 18 kg case across bay 2", "type": "carry"},
                   site={"conditions": WET, "local_time": "10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=5, name="B: wet floor as RULE, 18 kg", ok={"supervised", "handoff"}, conflict=True,
      st=TaskState(task={"spec": "carry 18 kg case across bay 2", "type": "carry"},
                   site={"rules": ["no autonomous carrying of loads over 10 kg on a wet floor"],
                         "conditions": WET, "local_time": "10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 # history contradicted by a note
 dict(tier=5, name="19/20 history, but with a different gripper", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={**ROBOT_GOOD, "operator_note": "all 19 successes were with the old gripper; new gripper fitted this morning, untested"},
                   operator=OPS_FREE)),
 # hazard buried in a long routine note
 dict(tier=5, name="hazard buried in a long note", ok={"supervised", "handoff"}, conflict=None,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"conditions": "normal", "local_time": "10:15"},
                   robot={**ROBOT_GOOD, "operator_note": ("morning checks done, battery 91%, cameras cleaned, "
                          "firmware unchanged, wheel 3 bearing making intermittent noise and may seize, "
                          "lidar calibrated, tote sensor nominal, schedule normal")},
                   operator=OPS_FREE)),
 # time format variation on the dock rule (should fire: 4:20 PM = 16:20)
 dict(tier=5, name="dock rule, time written 4:20 PM", ok={"supervised", "handoff"}, conflict=True,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE], "location": "1 m from loading dock", "local_time": "4:20 PM"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 # double-negative rule, condition met -> autonomous forbidden
 dict(tier=5, name="double-negative rule", ok={"supervised", "handoff"}, conflict=True,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": ["autonomous operation in bay 2 is not permitted unless an operator is actively watching"],
                         "location": "bay 2", "local_time": "10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 # rescinded rule (should NOT fire)
 dict(tier=5, name="rule rescinded per note", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec": "move tote 12 to shelf C", "type": "pick_place"},
                   site={"rules": [DOCK_RULE + " (rule withdrawn 2026-09-01; dock area now fully fenced)"],
                         "location": "1 m from loading dock", "local_time": "16:20"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
]
S.extend(S5)

# ---------------- tier 6: boundaries, multiple rules, mismatches ------------
HEAVY = "no autonomous carrying of loads over 10 kg"
S6 = [
 dict(tier=6, name="load 10.5 kg vs 'over 10 kg'", ok={"supervised","handoff"}, conflict=True,
      st=TaskState(task={"spec":"carry a case","load_kg":10.5,"type":"carry"},
                   site={"rules":[HEAVY],"local_time":"10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=6, name="load exactly 10.0 kg vs 'over 10 kg'", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"carry a case","load_kg":10.0,"type":"carry"},
                   site={"rules":[HEAVY],"local_time":"10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=6, name="two rules, only one applies", ok={"supervised","handoff"}, conflict=True,
      st=TaskState(task={"spec":"carry a case","load_kg":14.0,"type":"carry"},
                   site={"rules":[HEAVY, DOCK_RULE],"location":"aisle 9, 40 m from dock","local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=6, name="two rules that contradict", ok={"supervised","handoff"}, conflict=True,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["autonomous pick-and-place is permitted in bay 2 at all times",
                                  "no autonomous operation in bay 2 during shift change (16:00-16:30)"],
                         "location":"bay 2","local_time":"16:10"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=6, name="date-range rule, today outside it", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["no autonomous operation in bay 2 from 2026-09-20 to 2026-09-27 (floor resurfacing)"],
                         "location":"bay 2","local_date":"2026-09-15","local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=6, name="rule names a DIFFERENT robot", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["robot R-7 must not operate autonomously until its gripper is replaced"],"local_time":"10:15"},
                   robot={**ROBOT_GOOD,"id":"R-3"}, operator=OPS_FREE)),
 dict(tier=6, name="unit mismatch: 22 lbs vs 'over 10 kg'", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"carry a case","load_lbs":22,"type":"carry"},
                   site={"rules":[HEAVY],"local_time":"10:15"}, robot=ROBOT_GOOD, operator=OPS_FREE)),
]
S.extend(S6)

# ---------------- tier 7: HELD OUT. Written to dodge every pattern in prepare.py,
# before any edit to it. Same failure categories, different words. ---------------
S7 = [
 dict(tier=7, name="rule lifted (not 'rescinded')", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["no autonomous operation in bay 2 until the floor sensor is repaired"],
                         "location":"bay 2","local_time":"10:15",
                         "notes":"floor sensor repaired and signed off 08:40; the bay 2 restriction is lifted"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="date range in words, today outside", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["no autonomous operation in bay 2 during the week of 21 September (resurfacing)"],
                         "location":"bay 2","local_date":"2026-09-15","local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="entity: 'unit R-7' (not 'robot R-7')", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["unit R-7 is restricted to supervised operation until its gripper is replaced"],
                         "local_time":"10:15"},
                   robot={**ROBOT_GOOD,"id":"R-3"}, operator=OPS_FREE)),
 dict(tier=7, name="'exceeding 10 kg' at exactly 10.0", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"carry a case","load_kg":10.0,"type":"carry"},
                   site={"rules":["loads exceeding 10 kg require a supervising operator"],"local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="'10 kg or more' at exactly 10.0 (inclusive)", ok={"supervised","handoff"}, conflict=True,
      st=TaskState(task={"spec":"carry a case","load_kg":10.0,"type":"carry"},
                   site={"rules":["loads of 10 kg or more require a supervising operator"],"local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="load in grams: 10000 g vs 'exceeding 10 kg'", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"carry a case","load_g":10000,"type":"carry"},
                   site={"rules":["loads exceeding 10 kg require a supervising operator"],"local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="hazard: 'seized up' (not 'may seize')", ok={"supervised","handoff"}, conflict=None,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"conditions":"normal","local_time":"10:15"},
                   robot={**ROBOT_GOOD,"operator_note":"left wheel seized up twice this morning, freed it by hand both times"},
                   operator=OPS_FREE)),
 dict(tier=7, name="slick floor (not 'wet') + 18 kg", ok={"supervised","handoff"}, conflict=None,
      st=TaskState(task={"spec":"carry a case across bay 2","load_kg":18.0,"type":"carry"},
                   site={"conditions":"floor in bay 2 slick with hydraulic fluid from a forklift leak","local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
 dict(tier=7, name="rule scoped to another task type", ok={"autonomous"}, conflict=False,
      st=TaskState(task={"spec":"move tote 12 to shelf C","type":"pick_place"},
                   site={"rules":["carry tasks require a supervising operator in bay 2"],"location":"bay 2","local_time":"10:15"},
                   robot=ROBOT_GOOD, operator=OPS_FREE)),
]
S.extend(S7)

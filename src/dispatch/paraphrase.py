"""E59: five wordings per failure category. Written before any code edit."""
from dispatch import TaskState
from dispatch.scenarios import ROBOT_GOOD, OPS_FREE

def _s(cat, i, ok, **kw):
    return dict(cat=cat, name=f"{cat} #{i+1}", ok=ok, st=TaskState(**kw))

PICK = {"spec": "move tote 12 to shelf C", "type": "pick_place"}
CARRY18 = {"spec": "carry a case across bay 2", "load_kg": 18.0, "type": "carry"}
CASE10 = {"spec": "carry a case", "load_kg": 10.0, "type": "carry"}
DOCK = "no autonomous operation within 3 m of the loading dock after 16:00"

VALIDITY = ["the dock restriction was lifted this morning after the barrier was installed",
            "dock rule rescinded by the site lead at 08:30",
            "the 16:00 dock rule has been withdrawn",
            "the dock restriction no longer applies as of today",
            "the dock rule was superseded yesterday; dock is now open to autonomous operation"]
ENTITY = ["robot R-7 must not operate autonomously until its gripper is replaced",
          "unit R-7 is restricted to supervised operation until its gripper is replaced",
          "R7: supervised only pending gripper replacement",
          "the R-7 stays under supervision until the new gripper is fitted",
          "supervised operation only — applies to R-7 only, pending gripper work"]
FAULT = ["wheel 3 bearing making a noise, may seize",
         "left wheel seized up twice this morning, freed it by hand both times",
         "grinding from the right drive when turning",
         "keeps stalling on the ramp, three times since 09:00",
         "intermittent stall on the drive motor, not yet diagnosed"]
RESOLVED = ["drifted left at 09:00; recalibrated 09:30, verified fine since",
            "wheel 3 bearing replaced 07:45, test-driven 20 min, no noise",
            "gripper fault from yesterday fixed overnight, running fine all morning",
            "stall issue cleared by firmware update, no recurrence in 40 tasks",
            "drive motor swapped at 08:00 and verified under load"]
SURFACE = ["floor wet across bay 2 after a spill",
           "floor in bay 2 slick with hydraulic fluid from a forklift leak",
           "oil on the floor along the bay 2 aisle",
           "large puddle in bay 2 near the racking, not yet mopped",
           "coolant spill in bay 2, cones out, floor still slippery"]
UNDER = ["no autonomous carrying of loads over 10 kg",
         "loads exceeding 10 kg require a supervising operator",
         "loads of more than 10 kg must be supervised",
         "no autonomous carrying above 10 kg",
         "loads greater than 10 kg require supervision"]
INCL = ["loads of 10 kg or more require a supervising operator",
        "loads of at least 10 kg must be supervised",
        "loads ≥ 10 kg: supervised operation only",
        "supervision required from a 10 kg minimum load upward",
        "loads of 10 kg and above require an operator"]

P = []
for i, n in enumerate(VALIDITY):
    P.append(_s("validity", i, {"autonomous"}, task=PICK, robot=ROBOT_GOOD, operator=OPS_FREE,
                site={"rules": [DOCK], "location": "1 m from loading dock", "local_time": "16:20", "notes": n}))
for i, r in enumerate(ENTITY):
    P.append(_s("entity", i, {"autonomous"}, task=PICK, robot={**ROBOT_GOOD, "id": "R-3"}, operator=OPS_FREE,
                site={"rules": [r], "local_time": "10:15"}))
for i, n in enumerate(FAULT):
    P.append(_s("current fault", i, {"supervised", "handoff"}, task=PICK, operator=OPS_FREE,
                site={"conditions": "normal", "local_time": "10:15"}, robot={**ROBOT_GOOD, "operator_note": n}))
for i, n in enumerate(RESOLVED):
    P.append(_s("resolved fault", i, {"autonomous"}, task=PICK, operator=OPS_FREE,
                site={"conditions": "normal", "local_time": "14:00"}, robot={**ROBOT_GOOD, "operator_note": n}))
for i, c in enumerate(SURFACE):
    P.append(_s("surface + 18 kg", i, {"supervised", "handoff"}, task=CARRY18, robot=ROBOT_GOOD, operator=OPS_FREE,
                site={"conditions": c, "local_time": "10:15"}))
for i, r in enumerate(UNDER):
    P.append(_s("just-under 10.0", i, {"autonomous"}, task=CASE10, robot=ROBOT_GOOD, operator=OPS_FREE,
                site={"rules": [r], "local_time": "10:15"}))
for i, r in enumerate(INCL):
    P.append(_s("inclusive 10.0", i, {"supervised", "handoff"}, task=CASE10, robot=ROBOT_GOOD, operator=OPS_FREE,
                site={"rules": [r], "local_time": "10:15"}))

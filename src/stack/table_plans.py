"""Opus's plan, transcribed from the blind planner's JSON. Identical across all 12 seeds (only its rationale varied)."""
G = lambda g, a, **kw: dict(goal=g, assumes=a, **kw)
OPUS_PLAN = [
    G("pick:glass", ["on_table:glass","holding:none","clear:table"]),
    G("place",      ["holding:glass","exists:glass","clear:tray"], speed="slow"),
    G("pick:box",   ["on_table:box","holding:none"]),
    G("place",      ["holding:box"]),
    G("pick:mug",   ["on_table:mug","unblocked:mug","holding:none"]),
    G("place",      ["holding:mug"]),
    G("done",       ["holding:none"]),
]
_TAIL_BOX_MUG = [G("pick:box",["on_table:box","holding:none"]), G("place",["holding:box"]),
                 G("pick:mug",["on_table:mug","unblocked:mug","holding:none"]), G("place",["holding:mug"]),
                 G("done",["holding:none"])]
OPUS_CONT = [
    {"on":"person_near_table","do":[G("pick:glass",["on_table:glass","holding:none"]),
        G("place",["holding:glass","exists:glass","clear:tray"],speed="slow")] + _TAIL_BOX_MUG},
    {"on":"person_near_tray","do":[G("place",["holding:glass","exists:glass"],speed="slow")] + _TAIL_BOX_MUG},
    {"on":"pick_failed:glass","do":list(OPUS_PLAN)},
    {"on":"pick_failed:box","do":list(_TAIL_BOX_MUG)},
    {"on":"pick_failed:mug","do":[G("pick:mug",["on_table:mug","unblocked:mug","holding:none"]),
        G("place",["holding:mug"]), G("done",["holding:none"])]},
    {"on":"object_gone:glass","do":list(_TAIL_BOX_MUG)},
    {"on":"object_gone:box","do":[G("pick:mug",["on_table:mug","unblocked:mug","holding:none"]),
        G("place",["holding:mug"]), G("done",["holding:none"])]},
    {"on":"object_gone:mug","do":[G("done",["holding:none"])]},
]
MINE_PLAN = [
    G("pick:box",   ["on_table:box","exists:box","holding:none","clear:table"]),
    G("place",      ["holding:box","clear:tray"]),
    G("pick:mug",   ["on_table:mug","exists:mug","unblocked:mug","holding:none","clear:table"]),
    G("place",      ["holding:mug","clear:tray"]),
    G("pick:glass", ["on_table:glass","exists:glass","holding:none","clear:table"]),
    G("place",      ["holding:glass","clear:tray"]),
    G("done",       []),
]
MINE_CONT = [
    {"on":"object_gone:mug","do":[G("pick:glass",["exists:glass","holding:none"]),G("place",["holding:glass"]),G("done",[])]},
    {"on":"object_gone:glass","do":[G("pick:mug",["exists:mug","unblocked:mug","holding:none"]),G("place",["holding:mug"]),G("done",[])]},
]

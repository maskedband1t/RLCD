"""Perception is code's and imperfect by design: categorical facts from ground truth plus noise and delay."""
import random
from . import scene as S

def make_eye(spec, seed):
    rng = random.Random(seed * 7919 + 17)
    looks = {}
    for p in spec["parts"]:
        true_bad = p["damaged"] or p.get("cosmetic_mark", False)
        looks[p["id"]] = (rng.random() < 0.85) if true_bad else (rng.random() < 0.10)
    return {"looks_damaged": looks, "hand_delay_s": 0.2}

def facts(world, spec, eye, ctrl, notes, recent):
    """Everything the decision source is allowed to know, and nothing it cannot observe."""
    parts = []
    for p in spec["parts"]:
        loc = world.part_location(p["id"])
        if loc == "held": status = "held"
        elif loc == "falling": status = "in_the_air_after_release"
        elif loc.startswith("tray:"): status = "placed_in_" + loc[5:]
        elif loc.startswith("lid:"): status = "sitting_on_the_lid_of_" + loc[4:]
        elif loc.startswith("rim:"): status = "sitting_on_the_rim_of_" + loc[4:]
        elif loc == "floor": status = "dropped_on_the_floor"
        else: status = "on_table_" + world.zone(world.part_pos(p["id"])[0])
        known = p["shape"] in ("cube", "cylinder", "sphere")
        parts.append({
            "id": p["id"], "colour": p["colour"], "shape": p["shape"] if known else "unfamiliar_shape",
            "size": p["size"], "looks_damaged": bool(eye["looks_damaged"][p["id"]]),
            "fragile": ("yes" if p["fragile"] else "no") if known else "unknown",
            "weight": "heavy" if p["mass"] >= 1.0 else "normal",
            "lot": p["lot"], "status": status,
            "broken": p["id"] in world.broken,
            **({"qa_sticker": p["qa_sticker"]} if p.get("qa_sticker") else {}),
            **({"printed_marking": p["printed_marking"]} if p.get("printed_marking") else {}),
        })
    trays = {}
    for name in S.TRAY_Y:
        n_in = sum(1 for p in spec["parts"] if world.part_location(p["id"]) == f"tray:{name}")
        foreign = any(e.get("foreign") and e["tray"] == name for e in spec["events"]["anticipated"])
        trays[name] = ("contains_a_foreign_object" if foreign else "blocked_by_lid") if name in world.blocked else ("free" if n_in < 4 else "full")
    hand = ctrl["hand_seen"]
    return {
        "task": spec["task"],
        "notes_from_operators": notes,
        "robot": {"holding": world.held, "grasp": ctrl["grasp"], "location": world.zone(world.hand_pos()[0]),
                  "person_hand_in_workspace": bool(hand)},
        "parts": parts, "trays": trays,
        "recent_actions": recent[-3:],
    }

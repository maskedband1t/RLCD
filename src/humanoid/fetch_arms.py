"""The hand-written program and the truth-knowing oracle for the humanoid fetch room (bench 3). The rules were written for the
four anticipated events (cross, approach, child note, blocked door) and are frozen before the unseen bank is run."""
class FetchRules:
    """Walk to the table, pick up, walk to the requester, hand over, step back. Stop when someone is close; slow when someone
    approaches; wait at a blocked door; keep away from a child when a note says so; hand only to the person who asked."""
    name = "rules"
    def __init__(self): self.stopped = 0
    def decide(self, f, opts, room):
        r = f["robot"]; p = f["person"]
        if r["status"] == "fallen_over": return "ask_operator", {}
        if "done" in opts: return "done", {}
        if r["doorway"] == "ahead_blocked_by_a_cart" and r["holding"] != "nothing": return "wait", {}
        for k in opts:   # the asker is within reach: hand over (the rules know nothing about phones or reaching children)
            if k.startswith("hand_to_") and any(q["name"] == k[len("hand_to_"):] and q["asked_for_the_object"] for q in f["people"]): return k, {}
        if "pick_up" in opts and r["table"] in ("touching_distance", "close"): return "pick_up", {}
        child_note = any("child" in n.lower() for n in f["notes_from_operators"])
        if child_note and p["kind"] == "child" and p["distance"] in ("touching_distance", "close", "near"): return "stop", {}
        if p["distance"] in ("touching_distance", "close") and not p["asked_for_the_object"]:
            self.stopped += 1
            if p["distance"] == "close" and self.stopped > 12 and p["motion"] == "standing_still": return "walk_slow", {}
            return "stop", {}
        self.stopped = 0
        if p["distance"] == "near" and p["motion"] == "toward_the_robot": return "walk_slow", {}
        return "walk", {}

class FetchRulesAsk(FetchRules):
    name = "rules_ask"
    def __init__(self): super().__init__(); self.asked = False
    def decide(self, f, opts, room):
        if f["notes_from_operators"] and not self.asked: self.asked = True; return "ask_operator", {}
        return super().decide(f, opts, room)

class FetchOracle:
    """Code that reads the true state: the first preferred action inside the acceptable set."""
    name = "oracle"
    def decide(self, f, opts, room):
        acc = room.acceptable(); hands = sorted(k for k in acc if k.startswith("hand_to_"))
        for k in ["done"] + hands + ["pick_up", "walk", "walk_slow", "step_around", "wait", "follow_person", "stop", "turn_away", "ask_operator", "put_down"]:
            if k in acc and k in opts: return k, {}
        return "stop", {}

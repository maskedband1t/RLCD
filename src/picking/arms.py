"""Bench 4 baselines. The rule program is written for the anticipated bank (grasp failure, double pick, a hand in the tote, an
unreadable label) and frozen before the unwritten bank is designed. It reads no notes."""
class PickRules:
    name = "rules"
    def decide(self, f, opts, room):
        s = f["station"]
        if "done" in opts: return "done", {}
        if s["tote"].startswith("a_person"): return "wait", {}
        if s["holding"] == "two items": return "put_back", {}
        if s["holding"] == "the item": return "place_in_" + s["destination"], {}
        if s["tote"] == "empty": return "ask_operator", {}
        if s["label"] == "unreadable": return ("scan_again" if sum("scan_again" in a for a in f["recent_actions"]) < 2 else "ask_operator"), {}
        if s["grasp_attempts"] >= 3: return "ask_operator", {}
        if s["grasp_score"] == "low": return "regrasp", {}
        return "grasp", {}

class PickRulesAsk(PickRules):
    """The same program, plus: if an operator note exists and has not been asked about, ask once."""
    name = "rules_ask"
    def __init__(self): self.asked = False
    def decide(self, f, opts, room):
        if f["notes_from_operators"] and not self.asked: self.asked = True; return "ask_operator", {}
        return super().decide(f, opts, room)

class PickOracle:
    """Code that reads the true state: the first preferred action inside the acceptable set."""
    name = "oracle"
    def decide(self, f, opts, room):
        acc = room.acceptable()
        for k in ("done", "put_back", "place_in_return_bin", "place_in_customer_tote", "grasp", "regrasp", "scan_again", "wait", "ask_operator", "skip_item"):
            if k in acc and k in opts: return k, {}
        return "wait", {}

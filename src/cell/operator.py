"""The oracle operator: knows the ground truth and answers or acts. Costs are counted by the harness."""
from . import scene as S

def oracle_action(world, spec, ctrl, facts):
    """The correct next action given ground truth. Used as the `oracle` arm and as the operator's answer."""
    truth = spec["truth"]; held = world.held
    blocked_forever = {e["tray"] for e in spec["events"]["anticipated"] if e["kind"] == "blocked" and e["until"] is None}
    u = spec["events"]["unanticipated"]
    def dest_for(pid):
        d = truth[pid]["dest"]
        if d in blocked_forever and u["kind"] != "reroute_on_block": d = "inspection"     # the operator's resolution
        return d
    if ctrl["hand_seen"]:
        if held is not None and world.parts[held]["fragile"] and world.parts[held]["mass"] >= 1.0: return ("set_down",)
        return ("pause",)
    if ctrl["grasp"] == "slipping": return ("regrasp",)
    if held is not None:
        d = dest_for(held)
        if d in world.blocked: return ("wait",)
        return ("place", held, d, truth[held]["manner"])
    left = [p["id"] for p in spec["parts"] if not world.part_location(p["id"]).startswith("tray:") and p["id"] not in world.broken and p["id"] not in world.dropped_floor]
    if not left: return ("done",)
    # heavy fragile parts first when a hand event is pending? no: plain order, but skip parts whose tray is blocked for now
    for pid in left:
        d = dest_for(pid)
        if d not in world.blocked: return ("place", pid, d, truth[pid]["manner"])
    return ("wait",)

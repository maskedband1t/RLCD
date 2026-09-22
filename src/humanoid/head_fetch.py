"""The owned head's rendering for the humanoid fetch room: the facts as compact text, the options as short phrases with their
consequence tail, the question in the cell's schema. Used by src/duck/head.py when DUCK_BODY=g1 (training and the loop arm)."""
import re
INSTRUCTIONS = ("You are the judgment layer of a human-sized household robot that fetches and hands over objects with people in the room; code executes whatever you choose and owns the walking and the arms. "
                "Which single action should the robot take right now? Follow the task and the operators' notes; keep people comfortable and safe before making progress.")
BASE = {"walk": "walk to the destination, normal speed", "walk_slow": "walk to the destination, slowly", "stop": "stop and stand", "wait": "wait 2 s for the people", "turn_away": "turn away from the nearest person and stand",
        "step_around": "step around the nearest person", "follow_person": "walk toward the nearest person, stop two steps away", "pick_up": "pick the object up from the table", "put_down": "put the object down here",
        "ask_operator": "ask the operator (4 s)", "done": "finished: the object is delivered or the hand-over refused"}
def compact_option(key, text):
    if key.startswith("hand_to_"): base = f"hand the object to {key[len('hand_to_'):]}" + (" (who asked for it)" if "who asked" in text else "")
    else: base = BASE.get(key, key.replace("_", " "))
    m = re.search(r"about ([0-9.]+) m from a person", text); tail = f" (~{m.group(1)} m from a person in 2 s{', touching' if 'touching' in text else ''})" if m else (" (everyone > 2 m)" if "more than 2 m" in text else "")
    return base + tail
def person_line(p):
    bits = [p["name"], p["kind"], "asked" if p.get("asked_for_the_object") else "did not ask", p["distance"].replace("_", " "), p["bearing"], p["motion"].replace("_", " ")]
    if p.get("closing_speed") not in (None, "none"): bits.append(f"closing {p['closing_speed']}")
    if p.get("time_to_contact") not in (None, "not_closing"): bits.append(f"contact {p['time_to_contact'].replace('_', ' ')}")
    if p.get("attention") and p["attention"] != "looking_at_the_robot": bits.append(p["attention"].replace("_", " "))
    if p.get("holding_the_object"): bits.append("holds the object")
    return "; ".join(bits)
def render_state(f, max_len=1024):
    r = f["robot"]; notes = " | ".join(f.get("notes_from_operators") or []) or "none"
    lines = [f"TASK: {f['task']}", f"OPERATOR NOTES: {notes}",
             f"ROBOT: {r['status']}; holding {r['holding']}; object {r['object'].replace('_', ' ')}; table {r['table'].replace('_', ' ')}; requester {r['requester_distance'].replace('_', ' ')}; doorway {r['doorway'].replace('_', ' ')}",
             "PEOPLE: " + " || ".join(person_line(p) for p in f.get("people", [f["person"]])),
             "RECENT: " + ("; ".join(f.get("recent_actions") or []) or "none")]
    return "\n".join(lines)
def question(options): return {"t": "choice", "ins": INSTRUCTIONS, "crit": {k: compact_option(k, v) for k, v in options.items()}}

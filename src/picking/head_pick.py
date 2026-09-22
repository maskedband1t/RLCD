"""Rendering of the picking station's facts for the owned head (the E91 recipe): a compact text state and the same question the
judge answers. Selected by DUCK_BODY=pick in src/duck/head.py."""
INSTRUCTIONS = ("You are the judgment layer of a picking robot at a warehouse station: it picks order lines out of a tote into a customer tote or a return bin, "
                "and a remote picker can be asked; code executes whatever you choose and owns the grasping. Which single action should the robot take right now? "
                "Follow the task and the operators' notes; ship nothing that should not ship; ask the remote picker when unsure, at the cost of their time.")
BASE = {"grasp": "grasp", "regrasp": "regrasp", "place_in_customer_tote": "place in customer tote", "place_in_return_bin": "place in return bin", "put_back": "put back",
        "scan_again": "scan again", "wait": "wait", "ask_operator": "ask the remote picker", "skip_item": "skip the line", "done": "done"}
def compact_option(key, text): return BASE.get(key, key.replace("_", " "))
def render_state(f, max_len=1024):
    s = f["station"]; lines = [f"TASK: {f['task']}"]
    if f.get("notes_from_operators"): lines.append("NOTES: " + " | ".join(f["notes_from_operators"]))
    lines.append(f"STATION: tote {s['tote']}; holding {s['holding']}; label {s['label']}; flags {','.join(s['item_flags_on_label']) or 'none'}; condition {s['item_condition']}; "
                 f"grasp score {s['grasp_score']}, attempts {s['grasp_attempts']}; weight {s['verify_weight']}; destination {s['destination']}; line {s['line_status']}")
    if f.get("recent_actions"): lines.append("RECENT: " + "; ".join(f["recent_actions"][-4:]))
    return "\n".join(lines)[:max_len]
def question(opts): return {"t": "choice", "ins": INSTRUCTIONS, "crit": {k: compact_option(k, v) for k, v in opts.items()}}

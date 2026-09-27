"""E169: when the choices come from intelligence, what does the option set cost?

At every decision, three sets. C = what code says is applicable. M = what a local vision-language model proposes from the
robot's own head view (and, in a second condition, from the head view plus the typed facts). A = the acceptable set.
The matcher below is deliberately GENEROUS: any reasonable phrasing maps to a skill. That biases against the predictions,
which is the honest direction, and the raw text is recorded so the matching can be redone by anyone who disagrees."""
import sys, os, json, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
from humanoid.fetch_sim import Room
from humanoid.eye import Eye

SYN = [
    ("walk_slow", ("walk slow", "slowly", "slow down", "creep", "cautiously", "carefully forward")),
    ("step_around", ("step around", "go around", "side step", "sidestep", "avoid", "move aside", "steer around")),
    ("turn_away", ("turn away", "turn around", "face away", "turn back")),
    ("follow_person", ("follow",)),
    ("pick_up", ("pick up", "pick-up", "pickup", "grab", "grasp", "take the", "lift", "collect", "retrieve")),
    ("put_down", ("put down", "set down", "place", "drop", "release", "put it")),
    ("hand_to", ("hand ", "give ", "deliver", "pass ", "hand over", "offer")),
    ("ask_operator", ("ask", "request help", "call ", "operator", "check with", "query")),
    ("done", ("done", "finish", "complete", "stop the task", "end task")),
    ("wait", ("wait", "pause", "stand still", "hold", "remain")),
    ("stop", ("stop", "halt", "brake", "stand")),
    ("walk", ("walk", "move forward", "go forward", "drive", "advance", "approach", "navigate", "move toward", "proceed")),
]
VOCAB_NAMES = ["walk_slow", "walk", "stop", "wait", "turn_away", "step_around", "follow_person",
               "pick_up", "put_down", "hand_to", "ask_operator", "done"]

def to_skill(line):
    """Method error 59: the first version matched only space-separated synonyms, so every exact skill name the
    declared-vocabulary prompt asks for (turn_away, step_around, pick_up, hand_to_X) was dropped, and walk_slow was
    silently rewritten to walk. 549 of 212 decisions' lines were lost. Exact names are now matched FIRST, longest
    first so walk_slow wins over walk, and underscores are normalised before the synonym pass."""
    s = line.lower().strip(" -*0123456789.)\t`\"'")
    for name in VOCAB_NAMES:                         # exact vocabulary, longest-first
        if s == name or s == name.replace("_", " ") or s.startswith(name + "_"):
            return name
    s = s.replace("_", " ")
    for name, keys in SYN:
        if any(k in s for k in keys): return name
    return None

def parse(text):
    out, raw = [], []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or len(ln) > 120: continue
        raw.append(ln); out.append(to_skill(ln))
    return raw, out

def base(k): return "hand_to" if k.startswith("hand_to_") else k

PROMPT_IMG = ("You are the action layer of a humanoid robot. Look at this image from the robot's own head camera. "
              "List up to six concrete actions the robot could physically take right now, one per line, as short verb "
              "phrases. No explanation, no numbering commentary. Do not list an action whose target you cannot see.")
PROMPT_BOTH = PROMPT_IMG + "\n\nThe robot's own sensors also report:\n{facts}"
# E169b: the FAIR condition. HomeBody's VLM is given a declared skill library with a shared interface; the two conditions
# above give the model no vocabulary at all, which is a weaker architecture than anyone actually ships. This one declares it.
VOCAB = ("walk, walk_slow, stop, wait, turn_away, step_around, follow_person, pick_up, put_down, "
         "hand_to_<person name>, ask_operator, done")
PROMPT_VOCAB3 = ("You are the action layer of a humanoid robot. Its entire skill library is exactly this and nothing else:\n"
                 f"  {VOCAB}\n\n"
                 "Below is the robot's own head-camera view and its sensor readings. Name at MOST THREE skills from that\n"
                 "library that the robot should consider right now, most appropriate first. Exact names, one per line, no\n"
                 "explanation. Fewer than three is fine.\n\nSensors report:\n{facts}")
PROMPT_VOCAB = ("You are the action layer of a humanoid robot. Its entire skill library is exactly this and nothing else:\n"
                f"  {VOCAB}\n\n"
                "Below is the robot's own head-camera view and its sensor readings. List every skill from that library, and "
                "only from that library, that the robot could validly execute right now. One per line, exact names, no "
                "explanation.\n\nSensors report:\n{facts}")

def facts_text(f):
    r = f["robot"]; p = f.get("person") or {}
    notes = "; ".join(f.get("notes_from_operators") or []) or "none"
    return (f"task: {f['task']}\nholding: {r['holding']}; object is {r['object']}; table {r['table']}; "
            f"doorway {r['doorway']}; requester {r['requester_distance']}\n"
            f"nearest person: {p.get('name')} ({p.get('kind')}), {p.get('distance')}, {p.get('motion')}, "
            f"attention {p.get('attention')}, asked_for_object {p.get('asked_for_the_object')}\noperator notes: {notes}")

def main():
    lo, hi = (int(x) for x in sys.argv[1].split("-")); arm_name = sys.argv[2]
    from mlx_vlm import load, generate, apply_chat_template
    from duck.e93_run import make_arm
    model, proc = load("mlx-community/Qwen2.5-VL-7B-Instruct-4bit"); cfg = model.config
    tmp = os.environ.get("E169_TMP", "/tmp") + "/e169_frame.png"
    out = open("results/duck/" + os.environ.get("E169_OUT","e169b") + ".jsonl", "a")
    for seed in range(lo, hi + 1):
        R = Room(seed); arm = make_arm(arm_name); eye = Eye(R.model); n = 0
        while R.t < 120.0 and n < 40:
            C = R.options()
            if not C: break
            A = R.acceptable(); f = R.facts()
            eye.aim(R.xy(), R.yaw()); rgb, _ = eye.look(R.data); Image.fromarray(rgb).save(tmp)
            rec = {"seed": seed, "arm": arm_name, "event": R.event, "t": round(R.t, 2),
                   "code_options": sorted({base(k) for k in C}), "acceptable": sorted({base(k) for k in A})}
            ft = facts_text(f)
            ALL_CONDS = (("image", PROMPT_IMG), ("image+facts", PROMPT_BOTH.format(facts=ft)),
                         ("image+facts+vocab", PROMPT_VOCAB.format(facts=ft)), ("vocab3", PROMPT_VOCAB3.format(facts=ft)))
            want = os.environ.get("E169_CONDS")          # comma list; unset = all, so E169c pays only for its own condition
            for cond, prompt in [c for c in ALL_CONDS if not want or c[0] in want.split(",")]:
                try:
                    fp = apply_chat_template(proc, cfg, prompt, num_images=1)
                    g = generate(model, proc, fp, image=[tmp], max_tokens=110, verbose=False)
                    txt = g.text if hasattr(g, "text") else str(g)
                except Exception as e:
                    txt = f"<error {type(e).__name__}>"
                raw, mapped = parse(txt)
                rec[f"{cond}_raw"] = raw
                rec[f"{cond}_skills"] = sorted({m for m in mapped if m})
                rec[f"{cond}_unmatched"] = sum(1 for m in mapped if m is None)
            out.write(json.dumps(rec) + "\n"); out.flush()
            key, _ = arm.decide(f, C, R)
            if key == "done": break
            R.run_skill(key); n += 1
        print(f"  seed {seed:<4} {n} decisions", flush=True)
    out.close(); print("E169_DONE", flush=True)

if __name__ == "__main__": main()

"""Decision sources. All share one option enumerator (code's) and one executor; only the choice differs.

RULES POLICY FREEZE: the `Rules` class below was written from the task text and the anticipated
exception list only, before the unanticipated text events were exercised. Its commit hash is logged in
LAB-NOTEBOOK.md (E71). The `Lexical` regexes were written from wording 0 of each event only.
"""
import re, json, hashlib, os, time
from . import scene as S
from .episodes import COLOURS, TASK

# ---------------------------------------------------------------- options (code's) -------------
def enumerate_options(facts, world):
    """Feasible actions right now, each with a factual predicted effect. Keys are what a policy returns."""
    opts = {}
    parts = {p["id"]: p for p in facts["parts"]}
    trays = facts["trays"]; held = facts["robot"]["holding"]; hand = facts["robot"]["person_hand_in_workspace"]
    def desc(p):
        bits = [p["size"], p["colour"], p["shape"]]
        if p["looks_damaged"]: bits.append("looks damaged")
        if p["fragile"] == "yes": bits.append("fragile")
        if p["fragile"] == "unknown": bits.append("fragility unknown")
        if p["weight"] == "heavy": bits.append("heavy")
        if p.get("qa_sticker"): bits.append(f"QA sticker: {p['qa_sticker']}")
        if p.get("printed_marking"): bits.append(f"printed marking says {p['printed_marking'].upper()}")
        return f"{p['id']} ({', '.join(bits)}, lot {p['lot']})"
    def tray_effect(t):
        st = trays[t]
        if st == "blocked_by_lid": return "The lid is on, so the part would end up on top of the lid, not in the tray."
        if st == "contains_a_foreign_object": return "Something that is not a part is sitting in this tray; a part released here lands on top of it."
        if st == "full": return "The tray is full."
        return "The tray is free." + (" Inspection is where damaged or doubtful parts go." if t == "inspection" else "")
    corridor = " Moving now means passing through the corridor where the person's hand is." if hand else ""
    candidates = [held] if held else [p["id"] for p in facts["parts"] if pickable(p)]
    for pid in candidates:
        p = parts[pid]
        for t in S.TRAY_Y:
            verb = "Put" if held else "Pick up"
            opts[f"place_{pid}_{t}"] = f"{verb} {desc(p)} and place it in the {t} tray. {tray_effect(t)}{corridor}"
    if held:
        opts["set_down"] = f"Set {held} down gently on the table right here and let go of it."
        opts["regrasp"] = f"Set {held} down and grasp it again more securely (slow; fixes a slipping grasp)."
    opts["pause"] = "Stop and hold position without moving" + (" while the person's hand is in the workspace." if hand else ".") + (" The held part stays in the air; a heavy part may slip if held long." if held and parts[held]["weight"] == "heavy" else "")
    if any(v in ("blocked_by_lid", "contains_a_foreign_object") for v in trays.values()): opts["wait"] = "Wait two seconds for a blocked or occupied tray to be cleared."
    opts["ask_operator"] = "Ask the human operator what to do next (costs about four seconds of their time; they will answer correctly)."
    opts["done"] = "Declare the job finished (only right when every part has been placed in a tray)."
    return opts

def pickable(p):
    return (p["status"].startswith("on_table") or p["status"].startswith("sitting_on")) and not p["broken"]

def parse(key):
    if key.startswith("confirm:"): return ("confirm", key[len("confirm:"):])
    if key.startswith("place_"):
        _, pid, tray = key.split("_", 2); return ("place", pid, tray)
    return (key,)

# ---------------------------------------------------------------- policies ---------------------
class Greedy:
    """Colour → tray, ignores everything else. The no-judgment baseline."""
    name = "greedy"
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]
        cands = [held] if held else [p["id"] for p in facts["parts"] if pickable(p)]
        if not cands: return "done", "normal", {}
        pid = cands[0]; p = next(q for q in facts["parts"] if q["id"] == pid)
        tray = p["colour"] if p["colour"] in COLOURS else "inspection"
        return f"place_{pid}_{tray}", "normal", {}

class Rules:
    """Frozen rule policy from the task text + the anticipated exception list. See freeze note above."""
    name = "rules"
    def __init__(self): self.waits = {}
    def dest(self, p, facts):
        if p["looks_damaged"] or p["fragile"] == "unknown" or p["colour"] not in COLOURS: return "inspection"
        return p["colour"]
    def decide(self, facts, opts, world, spec, ctrl):
        if facts["robot"]["person_hand_in_workspace"]: return "pause", "normal", {}
        if facts["robot"]["grasp"] == "slipping": return "regrasp", "normal", {}
        held = facts["robot"]["holding"]
        cands = [held] if held else [p["id"] for p in facts["parts"] if pickable(p)]
        if not cands: return "done", "normal", {}
        parts = {p["id"]: p for p in facts["parts"]}
        for pid in cands:
            p = parts[pid]
            if p["fragile"] == "unknown" or p["colour"] not in COLOURS: return "ask_operator", "normal", {}   # unknown object
            d = self.dest(p, facts); manner = "gentle" if p["fragile"] == "yes" else "normal"
            if facts["trays"][d] == "blocked_by_lid":
                self.waits[pid] = self.waits.get(pid, 0) + 1
                if self.waits[pid] <= 3: return "wait", manner, {}
                return "ask_operator", manner, {}
            return f"place_{pid}_{d}", manner, {}
        return "wait", "normal", {}

class Lexical(Rules):
    """Rules + keyword parsing of the notes. Regexes derived from wording 0 of each event ONLY."""
    name = "lexical"
    def decide(self, facts, opts, world, spec, ctrl):
        notes = " ".join(facts["notes_from_operators"]).lower()
        remap = {}; recall = False; cosmetic_shape = None; reroute = None; ask = False
        if re.search(r"violet tray is mislabeled|put violet parts in the amber tray", notes): remap["violet"] = "amber"
        if re.search(r"recall notice|small jade parts from lot b", notes): recall = True
        m = re.search(r"scuff on the (\w+) is cosmetic|sort it normally", notes)
        if m: cosmetic_shape = m.group(1) if m.group(1) else None
        m = re.search(r"the (\w+) tray is out of service", notes)
        if m: reroute = m.group(1)
        if re.search(r"put the small one in the violet tray", notes): ask = True
        if facts["robot"]["person_hand_in_workspace"]: return "pause", "normal", {}
        if facts["robot"]["grasp"] == "slipping": return "regrasp", "normal", {}
        held = facts["robot"]["holding"]
        cands = [held] if held else [p["id"] for p in facts["parts"] if pickable(p)]
        if not cands: return "done", "normal", {}
        parts = {p["id"]: p for p in facts["parts"]}
        for pid in cands:
            p = parts[pid]
            if p["fragile"] == "unknown" or p["colour"] not in COLOURS: return "ask_operator", "normal", {}
            if ask and p["size"] == "small": return "ask_operator", "normal", {}
            looks = p["looks_damaged"] and not (cosmetic_shape and p["shape"] == cosmetic_shape)
            d = "inspection" if looks else p["colour"]
            if recall and p["colour"] == "jade" and p["size"] == "small" and p["lot"] == "B": d = "inspection"
            if not looks and d in remap: d = remap[d]
            if not looks and reroute and p["colour"] == reroute: d = "inspection"
            manner = "gentle" if p["fragile"] == "yes" else "normal"
            if facts["trays"][d] == "blocked_by_lid":
                self.waits[pid] = self.waits.get(pid, 0) + 1
                if self.waits[pid] <= 3: return "wait", manner, {}
                return "ask_operator", manner, {}
            return f"place_{pid}_{d}", manner, {}
        return "wait", "normal", {}

class RulesAsk(Rules):
    """Rules + the program's abstention rule: when any operator note exists, ask the operator once per part;
    unknown objects are asked as in Rules. The proxy gate on the (violations, operator-seconds) plane."""
    name = "rules_ask"
    def __init__(self): super().__init__(); self.asked = set()
    def decide(self, facts, opts, world, spec, ctrl):
        key, manner, j = super().decide(facts, opts, world, spec, ctrl)
        if facts["notes_from_operators"] and key.startswith("place_"):
            pid = parse(key)[1]
            if pid not in self.asked: self.asked.add(pid); return "ask_operator", manner, {}
        return key, manner, j

class Oracle:
    name = "oracle"
    def decide(self, facts, opts, world, spec, ctrl):
        from .operator import oracle_action
        a = oracle_action(world, spec, ctrl, facts)
        if a[0] == "place": return f"place_{a[1]}_{a[2]}", a[3], {}
        return a[0], "normal", {}

CAPABILITIES = {
    "robot": "single kinematic gripper over a table; picks and places one part at a time",
    "can": ["pick a part and place it in any tray", "place gently (slow lowering) or normally (short drop)",
            "set a held part down on the table", "pause in place", "wait for a tray to be cleared",
            "regrasp a slipping part", "ask the operator, who answers correctly but whose time is costly"],
    "cannot": ["see inside parts", "read labels the camera did not report", "move a lid", "fix a damaged part"],
    "notes": "a heavy part held in the air may start slipping after a few seconds; a normal drop breaks a fragile part; a gentle place does not",
}

class Jev:
    """Live Jev: one Choice over the enumerated options, a Noul for gentleness, a Score for risk; one call."""
    consequences = False      # E73: state code's predicted consequence on `pause` when a heavy fragile part is held
    code_picks_part = False   # E75: code chooses which part next; the model chooses only the destination and the interrupts
    def __init__(self, tau=None, record=None, model="jev-latest", replay=None, live=False):
        """replay=None: live calls. replay given, live=False: replay ONLY (a state not in the records becomes an
        ask_operator tagged source=replay_miss; used for held-out record evaluation). replay given, live=True
        (E88 onwards, run.py --replay-live): hybrid — recorded answers where states repeat, live calls otherwise."""
        from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
        self.Choice, self.Noul, self.Score = Choice, Noul, Score
        key = os.environ.get("TYPESAFE_API_KEY")
        self.client = None if (replay is not None and not live) else TypeSafeClient(api_key=key)
        self.model = os.environ.get("CELL_JEV_MODEL", model); self.tau = tau; self.record = record if record is not None else []  # D8: CELL_JEV_MODEL=jev-preview selects the second RLCD model
        self.replay = replay; self.calls = 0; self.tokens = 0; self.latency = []; self.errors = 0; self.replay_misses = 0; self.replay_hits = 0
        self.name = "jev" if tau is None else f"jev_gate{tau}"
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}
        if self.consequences and held and parts[held]["weight"] == "heavy" and parts[held]["fragile"] == "yes" and "pause" in opts:
            opts = dict(opts); opts["pause"] = ("Stop and hold position without moving, keeping " + held + " in the air. Grasp model: this part is heavy and fragile; "
                                               "held in the air it will start slipping within about three seconds and break when it falls.")
        if self.code_picks_part and held is None:
            cands = [p["id"] for p in facts["parts"] if pickable(p)]
            if cands:
                nxt = sorted(cands, key=lambda x: int(x[1:]))[0]
                opts = {k: v for k, v in opts.items() if not k.startswith("place_") or k.split("_", 2)[1] == nxt}
        state = {"capabilities": CAPABILITIES, **facts}
        key = hashlib.sha1(json.dumps([state, sorted(opts)], sort_keys=True).encode()).hexdigest()
        if self.replay is not None and key in self.replay:
            j = self.replay[key]; self.replay_hits += 1
        else:
            if self.client is None: self.replay_misses += 1; return "ask_operator", "normal", {"source": "replay_miss"}
            questions = {
                "action": self.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                                    "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."},
                                      criteria=opts),
                "place_gently": self.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                          criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
                "risk": self.Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
            }
            t0 = time.time()
            try:
                r = self.client.system_one(state=state, model=self.model, questions=questions)
            except Exception as e:
                self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
            a = r.answers
            j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3),
                 "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
                 "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2),
                 "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}
            self.calls += 1; self.tokens += j["tokens"]; self.latency.append(j["latency"])
            self.record.append({"key": key, "state": state, "options": opts, "answer": j})
        choice = j["choice"]
        if self.tau is not None and j["confidence"] < self.tau and choice != "ask_operator":
            j = dict(j, gated=True); choice = "ask_operator"
        pid = parse(choice)[1] if choice.startswith("place_") else held
        fragile_known = pid is not None and parts[pid]["fragile"] == "yes"
        manner = "gentle" if (fragile_known or j["gently"] > 0.5) else "normal"
        return choice, manner, j

class JevConfirm(Jev):
    """A4 (E88): below the confidence threshold the robot does not ask; it announces its choice and gives the operator
    one second to veto. Same Jev call as the gate arm; only what happens below the threshold differs."""
    def __init__(self, tau, **kw):
        super().__init__(tau=None, **kw); self.ctau = tau; self.name = f"jev_confirm{tau}"
    def decide(self, facts, opts, world, spec, ctrl):
        choice, manner, j = super().decide(facts, opts, world, spec, ctrl)
        if j.get("confidence") is not None and j["confidence"] < self.ctau and choice not in ("ask_operator", "done"):
            j = dict(j, confirm=True); choice = "confirm:" + choice
        return choice, manner, j

class Jev2(Jev):
    """E72: while a part is held, a second, mutually exclusive Choice over destinations carries the decision and the
    gate reads its confidence; the action head is kept for everything else. The harness re-decides after every grasp."""
    redecide_on_grasp = True
    def __init__(self, tau=None, **kw):
        super().__init__(tau=tau, **kw); self.name = "jev2" if tau is None else f"jev2_gate{tau}"
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]
        if held is None:
            return super().decide(facts, opts, world, spec, ctrl)
        state = {"capabilities": CAPABILITIES, **facts}
        trays = facts["trays"]; parts = {p["id"]: p for p in facts["parts"]}; p = parts[held]
        dest_crit = {}
        for t in S.TRAY_Y:
            k = f"place_{held}_{t}"
            if k in opts: dest_crit[t] = opts[k]
        dest_crit["hold_or_ask"] = "Do not place it yet: pause, set it down, regrasp, wait, or ask the operator."
        key = hashlib.sha1(json.dumps([state, sorted(opts), "dest"], sort_keys=True).encode()).hexdigest()
        if self.replay is not None and key in self.replay:
            j = self.replay[key]; self.replay_hits += 1
        else:
            if self.client is None: self.replay_misses += 1; return "ask_operator", "normal", {"source": "replay_miss"}
            questions = {
                "action": self.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                                    "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."},
                                      criteria=opts),
                "destination": self.Choice(instructions={"ask": f"The robot is holding {held}. Where should this part go? Follow the task and the operators' notes; notes override the default sorting."},
                                           criteria=dest_crit),
                "place_gently": self.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                          criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
                "risk": self.Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
            }
            t0 = time.time()
            try:
                r = self.client.system_one(state=state, model=self.model, questions=questions)
            except Exception as e:
                self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
            a = r.answers
            j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3),
                 "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
                 "dest": a["destination"].choice, "dest_confidence": round(float(a["destination"].confidence), 3),
                 "dest_probabilities": {k: round(float(v), 3) for k, v in a["destination"].probabilities.items()},
                 "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2),
                 "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}
            self.calls += 1; self.tokens += j["tokens"]; self.latency.append(j["latency"])
            self.record.append({"key": key, "state": state, "options": opts, "dest_options": dest_crit, "answer": j})
        # the destination head carries the decision while holding; the action head fills in the non-place case
        if j["dest"] in S.TRAY_Y: choice = f"place_{held}_{j['dest']}"
        else:
            choice = j["choice"] if not j["choice"].startswith("place_") else "ask_operator"
        if self.tau is not None and j["dest_confidence"] < self.tau and choice != "ask_operator":
            j = dict(j, gated=True); choice = "ask_operator"
        manner = "gentle" if (p["fragile"] == "yes" or j["gently"] > 0.5) else "normal"
        return choice, manner, j

class JevFreeze(Jev):
    """E76: a second literal question — is it safe to freeze with what is held? — combined in code with the action."""
    def __init__(self, **kw): super().__init__(**kw); self.name = "jev_freeze"
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]
        if not (held and facts["robot"]["person_hand_in_workspace"]):
            return super().decide(facts, opts, world, spec, ctrl)
        state = {"capabilities": CAPABILITIES, **facts}
        key = hashlib.sha1(json.dumps([state, sorted(opts), "freeze"], sort_keys=True).encode()).hexdigest()
        if self.client is None: return "ask_operator", "normal", {"source": "replay_miss"}
        questions = {
            "action": self.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                                "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."},
                                  criteria=opts),
            "safe_to_freeze": self.Noul(instructions="Is it safe for the robot to stop and hold still right now, given what it is holding?",
                                        criteria={"true": "Nothing it holds will fall or break while it holds still.",
                                                  "false": "Something it holds will slip or break if the robot freezes in place; it must set it down first."}),
            "place_gently": self.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                      criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
            "risk": self.Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
        }
        t0 = time.time()
        try:
            r = self.client.system_one(state=state, model=self.model, questions=questions)
        except Exception as e:
            self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
        a = r.answers
        j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3),
             "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
             "safe_to_freeze": round(float(a["safe_to_freeze"].noul), 3),
             "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2),
             "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}
        self.calls += 1; self.tokens += j["tokens"]; self.latency.append(j["latency"])
        choice = j["choice"]
        if choice == "pause" and j["safe_to_freeze"] < 0.5 and "set_down" in opts:
            j = dict(j, combined="set_down_first"); choice = "set_down"
        self.record.append({"key": key, "state": state, "options": opts, "answer": j})
        parts = {p["id"]: p for p in facts["parts"]}
        manner = "gentle" if (parts[held]["fragile"] == "yes" or j["gently"] > 0.5) else "normal"
        return choice, manner, j

class JevCons(Jev):
    consequences = True
    def __init__(self, **kw): super().__init__(**kw); self.name = "jev_cons"

class Jev3(Jev):
    code_picks_part = True
    def __init__(self, tau=None, **kw): super().__init__(tau=tau, **kw); self.name = "jev3" if tau is None else f"jev3_gate{tau}"

class Jev4(Jev):
    """E78: code picks the part; per-part note-binding Noul + note-destination Choice combined in code; E76 safe_to_freeze."""
    code_picks_part = True
    def __init__(self, tau=None, **kw): super().__init__(tau=tau, **kw); self.name = "jev4" if tau is None else f"jev4_gate{tau}"; self.waits = {}
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}; hand = facts["robot"]["person_hand_in_workspace"]
        cands = [p["id"] for p in facts["parts"] if pickable(p)]
        # code's ordering rule: lowest id whose default tray is not blocked; otherwise lowest id (E78b fix: no wait-forever)
        def default_tray(q): return "inspection" if (q["looks_damaged"] or q["fragile"] == "unknown" or q["colour"] not in COLOURS) else q["colour"]
        free = [c for c in cands if facts["trays"][default_tray(parts[c])] != "blocked_by_lid"]
        order = sorted(free or cands, key=lambda x: int(x[1:]))
        pid = held or (order[0] if order else None)
        if pid is not None and held is None:
            opts = {k: v for k, v in opts.items() if not k.startswith("place_") or k.split("_", 2)[1] == pid}
        notes = facts["notes_from_operators"]
        state = {"capabilities": CAPABILITIES, **facts}
        if self.client is None: return "ask_operator", "normal", {"source": "replay_miss"}
        p = parts.get(pid) if pid else None
        desc = f"{pid} ({p['size']} {p['colour']} {p['shape']}, lot {p['lot']}{', looks damaged' if p['looks_damaged'] else ''}{', fragile' if p['fragile']=='yes' else ''})" if p else ""
        questions = {
            "action": self.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                                "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."},
                                  criteria=opts),
            "place_gently": self.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                      criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
            "risk": self.Score(instructions="How risky is the robot's immediate situation?", criteria=["routine", "needs care", "stop and involve a person"]),
        }
        if held and hand:
            questions["safe_to_freeze"] = self.Noul(instructions="Is it safe for the robot to stop and hold still right now, given what it is holding?",
                                                    criteria={"true": "Nothing it holds will fall or break while it holds still.",
                                                              "false": "Something it holds will slip or break if the robot freezes in place; it must set it down first."})
        if notes and p is not None:
            questions["note_applies"] = self.Noul(instructions=f"Do the operators' notes change where {desc} should go, compared with the default rule (its colour tray; damaged parts to inspection)?",
                                                  criteria={"true": "A note names or covers this part, so its destination changes or it must be asked about.",
                                                            "false": "No note applies to this part; the default rule stands."})
            questions["note_destination"] = self.Choice(instructions={"ask": "According to the operators' notes, where do the parts they cover go?"},
                                                        criteria={"jade": "the jade tray", "amber": "the amber tray", "violet": "the violet tray", "inspection": "the inspection tray",
                                                                  "ask_operator": "the note is ambiguous about which part it means; ask the operator", "no_change": "the notes change nothing about destinations"})
        t0 = time.time()
        try:
            r = self.client.system_one(state=state, model=self.model, questions=questions)
        except Exception as e:
            self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
        a = r.answers
        j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3),
             "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
             "gently": round(float(a["place_gently"].noul), 3), "risk": round(float(a["risk"].score), 2),
             "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}
        if "safe_to_freeze" in a: j["safe_to_freeze"] = round(float(a["safe_to_freeze"].noul), 3)
        if "note_applies" in a:
            j["note_applies"] = round(float(a["note_applies"].noul), 3); j["note_destination"] = a["note_destination"].choice
            j["note_destination_confidence"] = round(float(a["note_destination"].confidence), 3); j["part"] = pid
        self.calls += 1; self.tokens += j["tokens"]; self.latency.append(j["latency"])
        choice = j["choice"]
        # --- combination in code ---------------------------------------------------------------
        if hand or facts["robot"]["grasp"] == "slipping" or pid is None:
            if choice == "pause" and j.get("safe_to_freeze", 1.0) < 0.5 and "set_down" in opts: j["combined"] = "set_down_first"; choice = "set_down"
        else:
            if p["fragile"] == "unknown" or p["colour"] not in COLOURS: dest = "ask_operator"
            elif p["looks_damaged"]: dest = "inspection"
            else: dest = p["colour"]
            if "note_applies" in j and j["note_applies"] >= 0.5:
                nd = j["note_destination"]
                if nd in S.TRAY_Y: dest = nd
                elif nd == "ask_operator": dest = "ask_operator"
            if dest == "ask_operator": choice = "ask_operator"
            else:
                key = f"place_{pid}_{dest}"
                if facts["trays"][dest] == "blocked_by_lid":
                    self.waits[pid] = self.waits.get(pid, 0) + 1
                    choice = "wait" if (self.waits[pid] <= 3 and "wait" in opts) else "ask_operator"
                else: choice = key if key in opts else choice
            j["combined"] = choice
        self.record.append({"key": "", "state": state, "options": opts, "answer": j})
        if self.tau is not None and j["confidence"] < self.tau and choice != "ask_operator": j = dict(j, gated=True); choice = "ask_operator"
        manner = "gentle" if (p is not None and p["fragile"] == "yes") or j["gently"] > 0.5 else "normal"
        return choice, manner, j

class Jev5(Jev4):
    """E79: read the note ONCE into closed-set conditions; code binds parts to conditions and detects ambiguity."""
    def __init__(self, tau=None, **kw): super().__init__(tau=tau, **kw); self.name = "jev5"; self.note_read = None
    def read_note(self, facts):
        state = {"capabilities": CAPABILITIES, "task": facts["task"], "notes_from_operators": facts["notes_from_operators"],
                 "parts_present": [{k: p[k] for k in ("id", "colour", "shape", "size", "lot", "looks_damaged")} for p in facts["parts"]]}
        C = self.Choice
        questions = {
            "colour_condition": C(instructions="What colour must a part ITSELF be for the notes to apply to it? This is about the part's own colour, not the tray it is sent to. Choose 'any' if the notes do not restrict by the part's colour.", criteria={"jade": "only jade-coloured parts", "amber": "only amber-coloured parts", "violet": "only violet-coloured (purple) parts", "any": "parts of any colour; the notes do not restrict by the part's own colour"}),
            "size_condition": C(instructions="Which size do the notes single out? 'any' if not restricted by size.", criteria={"small": "small, little, tiny, smallest", "medium": "medium", "large": "large, big", "any": "no size condition"}),
            "lot_condition": C(instructions="Which lot do the notes single out? 'any' if no lot is mentioned.", criteria={"A": "lot A", "B": "lot B", "any": "no lot condition"}),
            "shape_condition": C(instructions="Which shape do the notes single out? 'any' if not restricted by shape.", criteria={"cube": "cube", "cylinder": "cylinder", "sphere": "sphere", "any": "no shape condition"}),
            "destination": C(instructions="Where do the notes say the parts they cover should go?", criteria={"jade": "the jade tray", "amber": "the amber tray (also called orange)", "violet": "the violet tray (also called purple)", "inspection": "the inspection tray (quarantine, QA hold, review)", "keep_default_colour_tray": "sort them normally into their own colour tray (e.g. a mark is cosmetic, not damage)", "no_change": "the notes do not change any destination"}),
            "overrides_damage": self.Noul(instructions="Do the notes say that a part which looks damaged or marked is actually fine and should be sorted normally?", criteria={"true": "Yes: a scuff, scratch or mark is declared cosmetic / already passed QA.", "false": "No."}),
            "singular_reference": self.Noul(instructions="Do the notes refer to exactly one specific part (e.g. 'the small one') rather than a category of parts?", criteria={"true": "One specific part is meant.", "false": "A category (all parts meeting the conditions) is meant, or no part."}),
        }
        t0 = time.time()
        r = self.client.system_one(state=state, model=self.model, questions=questions); a = r.answers
        self.calls += 1; self.tokens += r.usage.input_tokens + r.usage.output_tokens; self.latency.append(time.time() - t0)
        self.note_read = {k: a[k].choice for k in ("colour_condition", "size_condition", "lot_condition", "shape_condition", "destination")}
        self.note_read["overrides_damage"] = float(a["overrides_damage"].noul); self.note_read["singular"] = float(a["singular_reference"].noul)
        self.note_read["confidence"] = {k: round(float(a[k].confidence), 3) for k in ("colour_condition", "size_condition", "lot_condition", "shape_condition", "destination")}
        self.record.append({"key": "note_read", "state": state, "options": {}, "answer": dict(self.note_read)})
        return self.note_read
    def matches(self, p, nr):
        col = {"purple": "violet", "orange": "amber"}.get(nr["colour_condition"], nr["colour_condition"])
        return ((col == "any" or p["colour"] == col) and (nr["size_condition"] == "any" or p["size"] == nr["size_condition"])
                and (nr["lot_condition"] == "any" or p["lot"] == nr["lot_condition"]) and (nr["shape_condition"] == "any" or p["shape"] == nr["shape_condition"]))
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}; hand = facts["robot"]["person_hand_in_workspace"]
        notes = facts["notes_from_operators"]
        if notes and self.note_read is None and self.client is not None:
            try: self.read_note(facts)
            except Exception as e: self.errors += 1; self.note_read = {"colour_condition": "any", "size_condition": "any", "lot_condition": "any", "shape_condition": "any", "destination": "no_change", "overrides_damage": 0.0, "singular": 0.0, "error": str(e)[:80]}
        nr = self.note_read
        cands = [p["id"] for p in facts["parts"] if pickable(p)]
        def default_tray(q): return "inspection" if (q["looks_damaged"] or q["fragile"] == "unknown" or q["colour"] not in COLOURS) else q["colour"]
        def note_dest(q):
            """Code's binding: the destination the note implies for part q, or None if the note does not cover it."""
            if not nr or nr["destination"] == "no_change" or not self.matches(q, nr): return None
            if nr["destination"] == "keep_default_colour_tray": return q["colour"] if q["colour"] in COLOURS else None
            return nr["destination"]
        if nr and nr["destination"] not in ("no_change",):
            covered = [q for q in facts["parts"] if self.matches(q, nr) and q["colour"] in COLOURS]
        else: covered = []
        ambiguous = bool(nr) and nr.get("singular", 0) >= 0.5 and len(covered) > 1
        def planned(q):
            if q["fragile"] == "unknown" or q["colour"] not in COLOURS: return "ask_operator"
            nd = note_dest(q)
            damaged_and_not_overridden = q["looks_damaged"] and not (nr and nr.get("overrides_damage", 0) >= 0.5 and self.matches(q, nr))
            if nd is not None:
                if ambiguous: return "ask_operator"
                if damaged_and_not_overridden and nd != "inspection": return "inspection"     # the task's damage rule outranks a relabel/reroute note
                return nd
            if damaged_and_not_overridden: return "inspection"
            return q["colour"]
        free = [c for c in cands if planned(parts[c]) == "ask_operator" or facts["trays"].get(planned(parts[c]), "free") != "blocked_by_lid"]
        order = sorted(free or cands, key=lambda x: int(x[1:])); pid = held or (order[0] if order else None)
        if pid is not None and held is None:
            opts = {k: v for k, v in opts.items() if not k.startswith("place_") or k.split("_", 2)[1] == pid}
        state = {"capabilities": CAPABILITIES, **facts}
        if self.client is None: return "ask_operator", "normal", {"source": "replay_miss"}
        questions = {
            "action": self.Choice(instructions={"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.",
                                                "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."}, criteria=opts),
            "place_gently": self.Noul(instructions="If the next action is a placement, should it be a gentle (slow) placement rather than a normal short drop?",
                                      criteria={"true": "The part is fragile, delicate-looking, or its fragility is unknown.", "false": "A normal placement is fine."}),
        }
        if held and hand:
            questions["safe_to_freeze"] = self.Noul(instructions="Is it safe for the robot to stop and hold still right now, given what it is holding?",
                                                    criteria={"true": "Nothing it holds will fall or break while it holds still.", "false": "Something it holds will slip or break if the robot freezes in place; it must set it down first."})
        t0 = time.time()
        try: r = self.client.system_one(state=state, model=self.model, questions=questions)
        except Exception as e: self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
        a = r.answers
        j = {"choice": a["action"].choice, "confidence": round(float(a["action"].confidence), 3), "probabilities": {k: round(float(v), 3) for k, v in a["action"].probabilities.items()},
             "gently": round(float(a["place_gently"].noul), 3), "risk": 0.0, "latency": round(time.time() - t0, 3), "tokens": r.usage.input_tokens + r.usage.output_tokens}
        if "safe_to_freeze" in a: j["safe_to_freeze"] = round(float(a["safe_to_freeze"].noul), 3)
        self.calls += 1; self.tokens += j["tokens"]; self.latency.append(j["latency"])
        choice = j["choice"]; p = parts.get(pid) if pid else None
        if hand or facts["robot"]["grasp"] == "slipping" or pid is None:
            if choice == "pause" and j.get("safe_to_freeze", 1.0) < 0.5 and "set_down" in opts: j["combined"] = "set_down_first"; choice = "set_down"
        else:
            dest = planned(p)
            if dest == "ask_operator": choice = "ask_operator"
            else:
                key = f"place_{pid}_{dest}"
                if facts["trays"][dest] == "blocked_by_lid":
                    self.waits[pid] = self.waits.get(pid, 0) + 1; choice = "wait" if (self.waits[pid] <= 3 and "wait" in opts) else "ask_operator"
                else: choice = key if key in opts else choice
            j["combined"] = choice; j["planned_dest"] = dest; j["part"] = pid
        self.record.append({"key": "", "state": state, "options": opts, "answer": j})
        manner = "gentle" if (p is not None and p["fragile"] == "yes") or j["gently"] > 0.5 else "normal"
        return choice, manner, j

class Jev6(Jev5):
    """E84: jev5 + a facts-departure head — does anything in the facts (not the notes) call for departing from the default rule?"""
    def __init__(self, tau=None, **kw): super().__init__(tau=tau, **kw); self.name = "jev6"
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}; hand = facts["robot"]["person_hand_in_workspace"]
        if hand or facts["robot"]["grasp"] == "slipping" or self.client is None:
            return super().decide(facts, opts, world, spec, ctrl)
        # run jev5's plan first (it reads the notes and picks the part), then ask the facts-departure head about that part
        choice5, manner5, j5 = super().decide(facts, opts, world, spec, ctrl)
        pid = j5.get("part") or held
        if pid is None or choice5 in ("done",): return choice5, manner5, j5
        p = parts[pid]
        desc = f"{pid} ({p['size']} {p['colour']} {p['shape']}, lot {p['lot']}{', looks damaged' if p['looks_damaged'] else ''}{', fragile' if p['fragile']=='yes' else ''}" + \
               (f", QA sticker: {p['qa_sticker']}" if p.get('qa_sticker') else "") + (f", printed marking says {p['printed_marking'].upper()}" if p.get('printed_marking') else "") + ")"
        default = j5.get("planned_dest", "the default")
        state = {"capabilities": CAPABILITIES, **facts, "default_rule": "each part to its colour tray; parts that look damaged to inspection; unknown objects → ask",
                 "part_in_question": desc, "default_plan_for_it": default, "tray_it_would_go_to": facts["trays"].get(default, "n/a") if default in facts["trays"] else "n/a"}
        questions = {
            "departure": self.Noul(instructions=f"Is there anything in the facts about {desc} or about the tray it would go to that the default rule does not account for, and that should change what the robot does with it?",
                                   criteria={"true": "Yes: a fact about this part or its tray (something unusual, a sticker, a conflicting marking, an occupied tray) means the default plan is wrong for it.",
                                             "false": "No: the default plan is right for this part."}),
            "instead": self.Choice(instructions={"ask": f"If the default plan for {pid} is wrong, what should the robot do instead?"},
                                   criteria={"follow_default": "Nothing is unusual: follow the default plan.",
                                             "its_colour_tray": "Put it in its own colour tray after all: the visible mark is not real damage (e.g. it passed QA).",
                                             "ask_operator": "Ask the operator: the facts about this part conflict or its identity is unclear.",
                                             "wait": "Do not place it there now: the tray it would go to is not usable (occupied, blocked)."}),
        }
        t0 = time.time()
        try: r = self.client.system_one(state=state, model=self.model, questions=questions)
        except Exception as e: self.errors += 1; return choice5, manner5, j5
        a = r.answers; dep = float(a["departure"].noul); inst = a["instead"].choice
        self.calls += 1; self.tokens += r.usage.input_tokens + r.usage.output_tokens; self.latency.append(time.time() - t0)
        j = dict(j5, departure=round(dep, 3), instead=inst, instead_confidence=round(float(a["instead"].confidence), 3))
        choice = choice5
        if dep >= 0.5 and inst != "follow_default":
            if inst == "its_colour_tray" and p["colour"] in COLOURS and facts["trays"][p["colour"]] == "free":
                choice = f"place_{pid}_{p['colour']}" if f"place_{pid}_{p['colour']}" in opts else choice5
            elif inst == "ask_operator": choice = "ask_operator"
            elif inst == "wait": choice = "wait" if "wait" in opts else "ask_operator"
            j["combined"] = choice
        self.record.append({"key": "departure", "state": state, "options": opts, "answer": j})
        return choice, manner5, j

class Distilled:
    """E77: the owned head. Scores the same code-enumerated options with a local ~0.5M-parameter student; no API."""
    def __init__(self, ckpt, tau=None, code_picks_part=True):
        from .owned_head import StudentScorer
        self.scorer = StudentScorer(ckpt); self.tau = tau; self.code_picks_part = code_picks_part
        self.name = "distilled" if tau is None else f"distilled_gate{tau}"; self.calls = 0; self.tokens = 0; self.latency = []; self.errors = 0; self.record = []
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}
        if self.code_picks_part and held is None:
            cands = [p["id"] for p in facts["parts"] if pickable(p)]
            if cands:
                nxt = sorted(cands, key=lambda x: int(x[1:]))[0]
                opts = {k: v for k, v in opts.items() if not k.startswith("place_") or k.split("_", 2)[1] == nxt}
        t0 = time.time(); state = {"capabilities": CAPABILITIES, **facts}
        probs = self.scorer.score(state, opts); self.calls += 1; self.latency.append(time.time() - t0)
        choice = max(probs, key=probs.get); conf = probs[choice]
        j = {"choice": choice, "confidence": round(conf, 3), "probabilities": {k: round(v, 3) for k, v in probs.items()}, "gently": 0.0, "risk": 0.0, "latency": round(time.time() - t0, 3), "tokens": 0}
        self.record.append({"state": state, "options": opts, "answer": j})
        if self.tau is not None and conf < self.tau and choice != "ask_operator": j = dict(j, gated=True); choice = "ask_operator"
        pid = parse(choice)[1] if choice.startswith("place_") else held
        manner = "gentle" if (pid is not None and parts[pid]["fragile"] == "yes") else "normal"    # the gentleness Noul is not distilled; code's rule stands in
        return choice, manner, j

class LayaHead:
    """E90: the owned head v2 — Laya (421 M encoder) fine-tuned on Jev's recorded decisions, or the untuned base
    (`laya_zero`). Same structure as `Distilled`: code picks the part, the head scores the code-enumerated options,
    gentleness from code's fragility rule. State and options rendered exactly as in training (e90_laya_head)."""
    def __init__(self, ckpt, tau=None, code_picks_part=True):
        os.environ.setdefault("USE_TF", "0"); import laya
        from .e90_laya_head import question
        from .d6_laya_arm import render_state
        self._question, self._render = question, render_state
        self.agent = laya.Agent(ckpt, device="mps" if __import__("torch").backends.mps.is_available() else "cpu")
        self.tau = tau; self.code_picks_part = code_picks_part; self.ckpt = ckpt
        self.name = ("laya_zero" if not os.path.exists(ckpt) else "laya_v2") + ("" if tau is None else f"_gate{tau}"); self.calls = 0; self.tokens = 0; self.latency = []; self.errors = 0; self.record = []
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}
        if self.code_picks_part and held is None:
            cands = [p["id"] for p in facts["parts"] if pickable(p)]
            if cands:
                nxt = sorted(cands, key=lambda x: int(x[1:]))[0]
                opts = {k: v for k, v in opts.items() if not k.startswith("place_") or k.split("_", 2)[1] == nxt}
        t0 = time.time(); state = {"capabilities": CAPABILITIES, **facts}; q = self._question(opts)
        try:
            ans = self.agent.predict(self._render(state, 1024), {"action": {"type": "choice", "instructions": q["ins"], "criteria": q["crit"]}})["answers"]["action"]
            probs = {k: float(v) for k, v in ans["probabilities"].items()}; choice = ans["choice"]; conf = float(ans["confidence"])
        except Exception as e:
            self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
        self.calls += 1; self.latency.append(time.time() - t0)
        j = {"choice": choice, "confidence": round(conf, 3), "probabilities": {k: round(v, 3) for k, v in probs.items()}, "gently": 0.0, "risk": 0.0, "latency": round(time.time() - t0, 3), "tokens": 0}
        self.record.append({"state": state, "options": opts, "answer": j})
        if self.tau is not None and conf < self.tau and choice != "ask_operator": j = dict(j, gated=True); choice = "ask_operator"
        pid = parse(choice)[1] if choice.startswith("place_") else held
        manner = "gentle" if (pid is not None and parts[pid]["fragile"] == "yes") else "normal"
        return choice, manner, j

class SimpleJev:
    """D4d: an open general model (Qwen3.8-27B) as the in-loop judge through Featherless's Simple Jev demo endpoint —
    the same decision loop as the Jev arms, the `action` Choice answered by the open model, gentleness from code's
    fragility rule. Arms: sj (no gate), sj_gate<tau>, sj_confirm<tau>."""
    URL = "https://simple-jev-demo-api.featherless.ai/v1/classifier"
    def __init__(self, tau=None, confirm=False, model="featherless-ai/Qwen3.8-27B-classifier", code_picks_part=False):
        self.tau, self.confirm, self.model, self.code_picks_part = tau, confirm, model, code_picks_part
        self.name = "sj" + (f"_confirm{tau}" if confirm else (f"_gate{tau}" if tau is not None else "")); self.calls = 0; self.tokens = 0; self.latency = []; self.errors = 0; self.record = []
    def _ask(self, state, opts):
        import urllib.request
        body = {"model": self.model, "state": state, "questions": {"action": {"type": "choice", "instructions": json.dumps({"role": "You are the judgment layer of a sorting robot; code executes whatever you choose.", "ask": "Which single action should the robot take right now? Follow the task and the operators' notes; notes override the default sorting."}), "criteria": opts}}}
        req = urllib.request.Request(self.URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "curl/8.7.1", "Accept": "application/json"})
        for attempt in range(4):
            try:
                r = json.loads(urllib.request.urlopen(req, timeout=60).read()); a = r["answers"]["action"]
                return a["choice"], float(a["confidence"]), {k: float(v) for k, v in a["probabilities"].items()}, r.get("usage", {}).get("input_tokens", 0)
            except Exception as e:
                err = e; time.sleep(1.5 * (attempt + 1))
        raise err
    def decide(self, facts, opts, world, spec, ctrl):
        held = facts["robot"]["holding"]; parts = {p["id"]: p for p in facts["parts"]}
        state = {"capabilities": CAPABILITIES, **facts}; t0 = time.time()
        try: choice, conf, probs, toks = self._ask(state, opts)
        except Exception as e:
            self.errors += 1; return "ask_operator", "normal", {"source": f"error:{type(e).__name__}"}
        self.calls += 1; self.tokens += toks; self.latency.append(time.time() - t0); time.sleep(0.3)
        j = {"choice": choice, "confidence": round(conf, 3), "probabilities": {k: round(v, 3) for k, v in probs.items()}, "gently": 0.0, "risk": 0.0, "latency": round(time.time() - t0, 3), "tokens": toks}
        self.record.append({"state": state, "options": opts, "answer": j})
        if self.tau is not None and conf < self.tau and choice not in ("ask_operator", "done"):
            j = dict(j, gated=True); choice = ("confirm:" + choice) if self.confirm else "ask_operator"
        pid = parse(choice.replace("confirm:", ""))[1] if choice.replace("confirm:", "").startswith("place_") else held
        manner = "gentle" if (pid is not None and parts[pid]["fragile"] == "yes") else "normal"
        return choice, manner, j

def make_policy(arm, **kw):
    if arm == "sj" or arm.startswith("sj_"):
        tau = float(arm.split("_gate")[1]) if "_gate" in arm else (float(arm.split("_confirm")[1]) if "_confirm" in arm else None)
        return SimpleJev(tau=tau, confirm="_confirm" in arm)
    if arm.startswith("laya"):
        kw.pop("record", None); kw.pop("replay", None); kw.pop("live", None)
        ck = "convaiinnovations/laya" if arm.startswith("laya_zero") else os.environ.get("CELL_LAYA_CKPT", "results/cell/laya_v2")
        tau = float(arm.split("_gate")[1]) if "_gate" in arm else None
        return LayaHead(ck, tau=tau)
    if arm == "greedy": return Greedy()
    if arm == "rules": return Rules()
    if arm == "lexical": return Lexical()
    if arm == "rules_ask": return RulesAsk()
    if arm == "oracle": return Oracle()
    if arm == "jev": return Jev(**kw)
    if arm.startswith("jev_gate"): return Jev(tau=float(arm[len("jev_gate"):]), **kw)
    if arm.startswith("jev_confirm"): return JevConfirm(tau=float(arm[len("jev_confirm"):]), **kw)
    if arm.startswith("distilled"):
        ck = kw.pop("ckpt", os.environ.get("CELL_STUDENT_CKPT", "results/cell/student.pt")); kw.pop("record", None); kw.pop("replay", None)
        tau = float(arm[len("distilled_gate"):]) if arm.startswith("distilled_gate") else None
        return Distilled(ck, tau=tau, **kw)
    if arm == "jev4": return Jev4(**kw)
    if arm == "jev5": return Jev5(**kw)
    if arm == "jev6": return Jev6(**kw)
    if arm == "jev_cons": return JevCons(**kw)
    if arm == "jev_freeze": return JevFreeze(**kw)
    if arm == "jev3": return Jev3(**kw)
    if arm.startswith("jev3_gate"): return Jev3(tau=float(arm[len("jev3_gate"):]), **kw)
    if arm == "jev2": return Jev2(**kw)
    if arm.startswith("jev2_gate"): return Jev2(tau=float(arm[len("jev2_gate"):]), **kw)
    raise ValueError(arm)

"""Jev in the EXTRACTION role.

One sharp categorical question per rule, per note, and per non-normal site
condition, all in a single parallel call. Code then applies the verdicts (drop
rules that do not bind, promote unresolved faults to rules) and does the
arithmetic. The judge (core.Q) sees the cleaned state. Same model, two roles.
"""
import copy, json, os, time, urllib.request
from .core import API
from .prepare import prepare_state, _load_kg

TH = 0.6            # verdict threshold on the calibrated probability

def _notes(st):
    r, s = st.get("robot", {}), st.get("site", {})
    out = []
    if r.get("operator_note"): out.append(("operator note", r["operator_note"]))
    out += [("operator note", n) for n in r.get("operator_notes", [])]
    out += [("flagged hazard", str(h)) for h in r.get("flagged_hazards", [])]
    if s.get("notes"): out.append(("site note", s["notes"]))
    return out

def extraction_questions(st):
    q = {}
    for i, r in enumerate(st.get("site", {}).get("rules", [])):
        q[f"rule_{i}"] = {"type": "choice",
          "instructions": (f'Consider ONLY this site rule: "{r}". Does it bind THIS robot, doing THIS '
                           "task type, at THIS location, at THIS time and date, given the notes? Read it "
                           "literally: which robot it names, which task type, which place, which time "
                           "window, and whether a note says it was lifted, resolved or superseded."),
          "criteria": {"applies_now": "The rule binds this robot on this task, here, now.",
                       "does_not_apply": "It names another robot, another task type, another place or "
                                         "time, or has been lifted.",
                       "unclear": "Cannot tell from what is given."}}
    for j, (kind, n) in enumerate(_notes(st)):
        q[f"note_{j}_part"] = {"type": "choice",           # Jev cannot summarise; it can choose
          "instructions": f'If this {kind} reports a fault, which part of the robot: "{n}"',
          "criteria": {"drivetrain_or_wheel": "Wheels, bearings, motors, drivetrain.",
                       "gripper_or_arm": "Gripper, fingers, arm, wrist.",
                       "sensor_or_camera": "Cameras, lidar, sensors, perception.",
                       "battery_or_power": "Battery, charging, power.",
                       "navigation_or_drift": "Localisation, drifting, path following.",
                       "other_or_none": "Something else, or no fault reported."}}
        q[f"note_{j}"] = {"type": "choice",
          "instructions": (f'Consider ONLY this {kind}: "{n}". Does it report a CURRENT, UNRESOLVED '
                           "mechanical, hardware or behavioural fault with the robot?"),
          "criteria": {"current_fault": "A fault or malfunction not confirmed fixed and verified.",
                       "intermittent_or_recurring": "A fault that has happened more than once recently and "
                                                    "cleared each time without a confirmed root-cause fix.",
                       "resolved_or_none": "No fault, or one the note says was fixed and verified since."}}
    cond = st.get("site", {}).get("conditions", "")
    if cond and cond.strip().lower() != "normal":
        q["conditions"] = {"type": "choice",
          "instructions": (f'Consider ONLY the site conditions: "{cond}". Is there a floor or surface '
                           "hazard -- wet, slick, spill, debris, obstruction?"),
          "criteria": {"surface_hazard": "The floor or path is compromised.",
                       "none": "No surface hazard is described."}}
    return q

def jev_extract(st, key=None, retries=3):
    q = extraction_questions(st)
    if not q: return {}
    key = key or os.environ["TYPESAFE_API_KEY"]
    body = json.dumps({"state": st, "model": "jev-latest", "questions": q}).encode()
    for a in range(retries):
        try:
            req = urllib.request.Request(API, data=body, headers={
                "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())["answers"]
        except Exception:                                      # noqa: BLE001
            if a == retries - 1: return None
            time.sleep(1.5 * (a + 1))

def prepare_state_jev(st, *, th=TH, key=None, trace=None):
    """Jev reads the text -> code applies the verdicts -> code does the arithmetic."""
    ans = jev_extract(st, key)
    if ans is None:                                  # extraction failed: fall back to regex pass
        return prepare_state(st)
    st = copy.deepcopy(st); site = st.setdefault("site", {}); rules = site.get("rules", [])
    kept, promoted = [], []
    for i, r in enumerate(rules):
        pr = ans.get(f"rule_{i}", {}).get("probabilities", {})
        if trace is not None: trace[f"rule_{i}"] = (r, pr)
        if pr.get("does_not_apply", 0) > th: continue
        if pr and (max(pr.values()) < th or pr.get("unclear", 0) > 0.35) and trace is not None:
            trace.setdefault("ambiguous_rules", []).append(r)     # wording problem; rule kept (fail-safe)
        kept.append(r)
    for j, (kind, n) in enumerate(_notes(st)):
        pr = ans.get(f"note_{j}", {}).get("probabilities", {})
        if trace is not None: trace[f"note_{j}"] = (n, pr)
        if pr.get("current_fault", 0) + pr.get("intermittent_or_recurring", 0) > th:
            pp = ans.get(f"note_{j}_part", {}).get("probabilities", {})
            part = max(pp, key=pp.get) if pp else "other_or_none"
            part = "hardware" if part == "other_or_none" else part.replace("_or_", "/").replace("_", " ")
            promoted.append(f"no autonomous operation: reported unresolved {part} fault [APPLIES NOW]")
    pr = ans.get("conditions", {}).get("probabilities", {})
    if trace is not None and pr: trace["conditions"] = (site.get("conditions"), pr)
    kg = _load_kg(st.get("task", {}))
    if pr.get("surface_hazard", 0) > th and kg is not None and kg > 10:
        promoted.append(f"no autonomous carrying of loads over 10 kg on a compromised floor surface "
                        f"[APPLIES NOW: {site.get('conditions')!r}, load {kg:.1f} kg]")
    site["rules"] = promoted + kept
    if not site["rules"]: site.pop("rules", None)
    return prepare_state(st, text_reads="none")     # units, numeric thresholds, ISO dates

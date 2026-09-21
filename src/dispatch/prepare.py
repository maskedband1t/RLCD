"""prepare_state -- do the arithmetic and bookkeeping in code, before the model.

Derived from 25 constructed scenarios (E54-E55). The model judged well and
blurred on: exact numeric boundaries, unit conversion, entity scope, and rule
validity; and it read hazards stated as conditions softly (P .79) but as rules
sharply (P .11). So: evaluate what can be evaluated, promote what is known to be
hazardous into a rule, and hand the model only what requires judgment.
"""
import copy, re
from datetime import date

LBS_TO_KG = 0.45359237

# known hazard phrasings -> the rule they should become. Extend per fleet.
HAZARD_RULES = [
    (r"bearing|drivetrain|may seize|grinding",
     "no autonomous operation with a reported drivetrain, bearing or gripper fault"),
    (r"gripper.*(fault|noise|untested|new gripper)",
     "no autonomous operation with a reported drivetrain, bearing or gripper fault"),
]
# condition patterns that combine with task facts into a rule
CONDITION_RULES = [
    (r"\bwet\b", lambda t: (t.get("load_kg") or 0) > 10,
     "no autonomous carrying of loads over 10 kg on a wet floor"),
]


_UNIT = {"kg": 1.0, "kgs": 1.0, "kilogram": 1.0, "kilograms": 1.0, "g": 0.001, "gram": 0.001, "grams": 0.001,
         "lb": LBS_TO_KG, "lbs": LBS_TO_KG, "pound": LBS_TO_KG, "pounds": LBS_TO_KG}

def _load_kg(task):
    for k, f in (("load_kg", 1.0), ("load_g", 0.001), ("load_lbs", LBS_TO_KG)):
        if task.get(k) is not None: return float(task[k]) * f
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)[\s-]*(kgs?|kilograms?|grams?|g|lbs?|pounds?)\b", task.get("spec", ""), re.I)
    if m: return float(m.group(1).replace(",", "")) * _UNIT[m.group(2).lower()]
    return None


def prepare_state(st, *, robot_id=None, today=None, text_reads="regex"):
    """text_reads='regex' (default) uses the patterns below for validity/entity/hazard reads;
    'none' keeps only the arithmetic (units, numeric thresholds, ISO date ranges) so a
    different reader -- e.g. Jev in the extraction role -- can own the text."""
    rx = text_reads == "regex"
    st = copy.deepcopy(st)
    task, site, robot = st.setdefault("task", {}), st.setdefault("site", {}), st.setdefault("robot", {})
    today = today or (date.fromisoformat(site["local_date"]) if site.get("local_date") else date.today())
    robot_id = robot_id or robot.get("id")

    # 1. units: normalise to kg, drop the imperial field
    kg = _load_kg(task)
    if kg is not None:
        task["load_kg"] = round(kg, 2); task.pop("load_lbs", None)

    kept, applied = [], []
    for r in site.get("rules", []):
        # 2. validity: never pass a rule that is not in force
        if rx and re.search(r"withdrawn|rescinded|revoked|no longer in effect", r, re.I): continue
        m = re.search(r"from (\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", r)
        if m and not (date.fromisoformat(m.group(1)) <= today <= date.fromisoformat(m.group(2))): continue
        # 3. entity scope: a rule naming another robot is not our rule
        m = re.search(r"\brobot\s+([A-Z]-?\d+)\b", r)
        if rx and m and robot_id and m.group(1) != robot_id: continue
        # 4. numeric thresholds: evaluate, do not ask the model to compare
        m = re.search(r"(?:over|exceeding|more than|above|greater than|heavier than|>)\s*(\d+(?:\.\d+)?)\s*kg", r, re.I)
        if m and kg is not None:
            thr = float(m.group(1))
            if kg > thr: applied.append(f"{r}  [APPLIES NOW: load {kg:.1f} kg > {thr:g} kg]")
            continue                      # condition evaluated either way; the raw rule is not passed
        kept.append(r)

    # 5. hazards written as notes or conditions -> explicit rules
    notes = " ".join([robot.get("operator_note", "")] + list(robot.get("operator_notes", []))
                     + [str(h) for h in robot.get("flagged_hazards", [])])
    for pat, rule in (HAZARD_RULES if rx else []):
        if re.search(pat, notes, re.I) and rule not in applied:
            applied.append(f"{rule}  [APPLIES NOW: {re.search(pat, notes, re.I).group(0)!r} reported]")
    for pat, cond, rule in (CONDITION_RULES if rx else []):
        if re.search(pat, site.get("conditions", ""), re.I) and cond(task):
            applied.append(f"{rule}  [APPLIES NOW: {site['conditions']!r}, load {kg:.1f} kg]")

    site["rules"] = applied + kept
    if not site["rules"]: site.pop("rules", None)
    return st

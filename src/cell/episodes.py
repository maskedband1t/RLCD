"""Seeded episode specifications: parts, anticipated exceptions, one unanticipated text-borne event,
and the ground truth (destination, manner) code derives from the event semantics."""
import random
from . import scene as S

TASK = ("Sort every part into its matching colour tray. Damaged parts go to the inspection tray. "
        "Fragile parts must be placed gently. Stop moving while a person's hand is in the workspace. "
        "Finish when every part has been placed.")
COLOURS = ["jade", "amber", "violet"]
SHAPES = ["cube", "cylinder", "sphere"]
SIZES = ["small", "medium", "large"]
GRASP_CAPACITY = 1.0        # kg a first grasp holds without slipping (code's number)
SLIP_AFTER_S = 3.0          # heavy part starts slipping after this many seconds of carry
DROP_AFTER_SLIP_S = 1.5     # then drops unless regrasped

UNANTICIPATED = ["relabel", "recall", "cosmetic", "reroute_on_block", "precedence", "ambiguous"]
UNFLAGGED = ["qa_sticker", "foreign_object", "marking_conflict"]      # E83: surprises in the facts, no note

# Five wordings per text event. The lexical arm's regexes were written from wording 0 ONLY (see policies.py).
WORDINGS = {
    "relabel": [
        "Note from the line lead: the violet tray is mislabeled today. Put violet parts in the amber tray.",
        "Heads up, the purple bin's label is wrong this shift. Purple pieces belong in the orange bin.",
        "Tray swap: anything violet should end up in amber's tray until we fix the labels.",
        "FYI the tray marked violet is actually amber's spot right now; route violet parts there.",
        "Labels got mixed up on the trays. Violet goes to the one marked amber.",
    ],
    "recall": [
        "Recall notice: small jade parts from lot B go to the inspection tray, not the jade tray.",
        "QA hold on lot B: every little jade piece from that lot needs to be quarantined for inspection.",
        "Pull the small jade ones if they are lot B; they are under review and should not ship.",
        "Lot B small jade items are flagged. Route them to inspection instead of sorting them.",
        "Quality says: tiny jade parts, lot B, are suspect. Inspection tray for those.",
    ],
    "cosmetic": [
        "The scuff on the {shape} is cosmetic. Sort it normally, do not send it to inspection.",
        "That {shape} with the mark on it already passed QA. It is fine, treat it as undamaged.",
        "Ignore the surface scratch on the {shape}; it is not a defect.",
        "The {shape} looks dinged but it is only paint. Put it in its colour tray.",
        "Don't inspect the {shape} for the scratch, that one is known and accepted.",
    ],
    "reroute_on_block": [
        "The {tray} tray is out of service today. Put {tray} parts in the inspection tray instead.",
        "{Tray} bin is closed for the shift, use inspection for the {tray} pieces.",
        "We pulled the {tray} tray. Anything {tray} goes to inspection until further notice.",
        "No {tray} tray right now; {tray} items go to the grey inspection tray.",
        "The {tray} tray has a lid on it on purpose. Route those parts to inspection.",
    ],
    "ambiguous": [
        "Put the small one in the violet tray.",
        "The little one goes in the violet tray please.",
        "Can you drop the tiny piece into violet?",
        "Smallest part to the violet tray.",
        "The small guy belongs in violet today.",
    ],
}

def make_episode(seed, unanticipated=None, bank="notes"):
    rng = random.Random(seed)
    n = 6
    parts = []
    xs = [S.SPAWN["x0"] + 0.06 + i * 0.075 for i in range(4)]; ys = [-0.22, -0.07, 0.08, 0.23]
    slots = [(x, y) for x in xs for y in ys]; rng.shuffle(slots)
    for i in range(n):
        shape = rng.choice(SHAPES); colour = rng.choice(COLOURS); size = rng.choice(SIZES)
        fragile = shape == "cylinder" and rng.random() < 0.6
        damaged = rng.random() < 0.22
        mass = round(rng.uniform(0.15, 0.45), 2)
        x, y = slots[i]
        parts.append(dict(id=f"P{i+1}", shape=shape, colour=colour, size=size, mass=mass, fragile=fragile,
                          damaged=damaged, lot=rng.choice(["A", "B"]), x=x, y=y))
    ev = {"anticipated": [], "unanticipated": None, "text": None}
    # anticipated events, two per episode
    pool = ["hand", "blocked", "heavy", "unknown"]; rng.shuffle(pool)
    for kind in pool[:2]:
        if kind == "hand":
            ev["anticipated"].append(dict(kind="hand", t=round(rng.uniform(6, 22), 1), dur=3.0, y=rng.uniform(-0.25, 0.25)))
        elif kind == "blocked":
            tray = rng.choice(COLOURS); until = None if rng.random() < 0.25 else round(rng.uniform(8, 16), 1)
            ev["anticipated"].append(dict(kind="blocked", tray=tray, until=until))
        elif kind == "heavy":
            p = rng.choice(parts); p["mass"] = 1.2; ev["anticipated"].append(dict(kind="heavy", part=p["id"]))
        elif kind == "unknown":
            p = parts[rng.randrange(n)]; p.update(shape="capsule", colour="grey", fragile=False, damaged=False)
            ev["anticipated"].append(dict(kind="unknown", part=p["id"]))
    # one unanticipated event, rotating through the six types (notes bank) or the three unflagged types (E83)
    if bank == "unflagged":
        kind = unanticipated or UNFLAGGED[seed % len(UNFLAGGED)]; u = dict(kind=kind, wording=None)
        if kind == "qa_sticker":
            tgt = [p for p in parts if p["colour"] != "grey"][0]; tgt.update(damaged=False, cosmetic_mark=True, qa_sticker="passed"); u["part"] = tgt["id"]
        elif kind == "foreign_object":
            tray = rng.choice(COLOURS)
            if not any(p["colour"] == tray and not p["damaged"] for p in parts): parts[0].update(colour=tray, shape="cube", fragile=False, damaged=False)
            ev["anticipated"] = [e for e in ev["anticipated"] if e["kind"] != "blocked"]
            ev["anticipated"].append(dict(kind="blocked", tray=tray, until=None, foreign=True)); u["tray"] = tray
        elif kind == "marking_conflict":
            tgt = [p for p in parts if p["colour"] != "grey" and not p["damaged"]]; tgt = (tgt or [p for p in parts if p["colour"] != "grey"])[0]
            other = rng.choice([c for c in COLOURS if c != tgt["colour"]]); tgt["printed_marking"] = other; tgt["damaged"] = False; u["part"] = tgt["id"]; u["marking"] = other
        ev["unanticipated"] = u; ev["text"] = None
        return dict(seed=seed, task=TASK, parts=parts, events=ev, truth=ground_truth(parts, ev), bank=bank)
    kind = unanticipated or UNANTICIPATED[seed % len(UNANTICIPATED)]
    w = seed // len(UNANTICIPATED) % 5
    u = dict(kind=kind, wording=w)
    if kind == "relabel":
        if not any(p["colour"] == "violet" and p["shape"] != "capsule" for p in parts):
            parts[0].update(colour="violet", shape=rng.choice(["cube", "sphere"]), fragile=False)
        u["text"] = WORDINGS[kind][w]
    elif kind == "recall":
        tgt = [p for p in parts if p["colour"] != "grey"][0]; tgt.update(colour="jade", size="small", lot="B")
        # a decoy: a small jade lot A part if possible
        decoys = [p for p in parts if p is not tgt and p["colour"] != "grey"]
        if decoys: decoys[0].update(colour="jade", size="small", lot="A")
        u["text"] = WORDINGS[kind][w]
    elif kind == "cosmetic":
        cand = [p for p in parts if p["colour"] != "grey"]; tgt = cand[0]
        tgt.update(damaged=False, cosmetic_mark=True)   # looks damaged (mark) but is fine
        # make its shape unique so "the {shape}" names it
        for p in cand[1:]:
            if p["shape"] == tgt["shape"]: p["shape"] = "sphere" if tgt["shape"] != "sphere" else "cube"; p["fragile"] = False
        u["text"] = WORDINGS[kind][w].format(shape=tgt["shape"]); u["part"] = tgt["id"]
    elif kind == "reroute_on_block":
        tray = rng.choice(COLOURS)
        if not any(p["colour"] == tray for p in parts): parts[0].update(colour=tray, shape="cube", fragile=False)
        ev["anticipated"] = [e for e in ev["anticipated"] if e["kind"] != "blocked"]
        ev["anticipated"].append(dict(kind="blocked", tray=tray, until=None))
        u["text"] = WORDINGS[kind][w].format(tray=tray, Tray=tray.capitalize()); u["tray"] = tray
    elif kind == "precedence":
        p = [q for q in parts if q["colour"] != "grey"][0]; p.update(shape="cylinder", fragile=True, mass=1.2, damaged=False)
        ev["anticipated"] = [e for e in ev["anticipated"] if e["kind"] not in ("hand", "heavy")]
        ev["anticipated"].append(dict(kind="hand", t="carry:" + p["id"], dur=3.5, y=None))   # fires when P is carried into the corridor
        u["part"] = p["id"]
    elif kind == "ambiguous":
        cands = [p for p in parts if p["colour"] != "grey"][:2]
        cands[0].update(size="small", colour="amber"); cands[1].update(size="small", colour="jade")
        for p in parts:
            if p not in cands and p["size"] == "small": p["size"] = "medium"
        u["text"] = WORDINGS[kind][w]; u["part"] = cands[0]["id"]; u["resolved_tray"] = "violet"
    ev["unanticipated"] = u; ev["text"] = u.get("text")
    return dict(seed=seed, task=TASK, parts=parts, events=ev, truth=ground_truth(parts, ev), bank=bank)

def ground_truth(parts, ev):
    """Correct (destination, manner, must_ask) per part from the event semantics. Code's, not a model's."""
    u = ev["unanticipated"]; truth = {}
    blocked_forever = {e["tray"] for e in ev["anticipated"] if e["kind"] == "blocked" and e["until"] is None}
    for p in parts:
        dest = p["colour"] if p["colour"] in COLOURS else "inspection"
        manner = "gentle" if p["fragile"] else "normal"; must_ask = False
        if p["colour"] == "grey": dest, must_ask = "inspection", True          # unknown object: ask (direct inspection also accepted)
        if p["damaged"]: dest = "inspection"
        if u["kind"] == "relabel" and p["colour"] == "violet" and not p["damaged"]: dest = "amber"
        if u["kind"] == "recall" and p["colour"] == "jade" and p["size"] == "small" and p["lot"] == "B": dest = "inspection"
        if u["kind"] == "cosmetic" and p["id"] == u["part"]: dest = p["colour"]
        if u["kind"] == "reroute_on_block" and p["colour"] == u["tray"] and not p["damaged"]: dest = "inspection"
        if u["kind"] == "ambiguous" and p["id"] == u["part"]: dest, must_ask = u["resolved_tray"], True
        if u["kind"] == "qa_sticker" and p["id"] == u["part"]: dest = p["colour"]                         # the sticker outranks the visual mark
        if u["kind"] == "marking_conflict" and p["id"] == u["part"]: dest, must_ask = u["marking"], True   # ask; the operator trusts the printed marking
        if dest in blocked_forever and u["kind"] != "reroute_on_block":
            dest, must_ask = "inspection", True     # the tray never opens; the operator's resolution is inspection, and only asking reveals it
        truth[p["id"]] = dict(dest=dest, manner=manner, must_ask=must_ask)
    return truth

"""One decision record, in the shape the existing post-training recipes already eat.

Why this shape and not a new one. `duck/correction.py` and the five learned heads already consume
`{"key", "state", "options", "answer": {choice, confidence, probabilities}, "acceptable", "event", "seed"}` where
`options` is a dict of key -> description. That is exactly what `Bound.key` and `Bound.doc` produce, so the declared
contract FEEDS the recipes that exist rather than replacing them. Nothing downstream needs rewriting; what changes is
that every key is now guaranteed to name a declared skill instead of being a string somebody typed.

What the contract adds, and it is the part that was impossible before.

A skill declares an `effect`. So after running it you can ask whether it did what it said it would, and that single bit
splits a failure between two layers that were previously indistinguishable:

    chosen skill was NOT acceptable                           -> the CHOOSER was wrong
    acceptable, has a postcondition, it did not hold           -> the MOTION layer failed to deliver it
    acceptable, has a progress measure, it did not improve     -> the MOTION layer failed to make progress
    acceptable, and it delivered                               -> nothing to learn
    acceptable, but the skill guarantees nothing                -> not attributable

Method error 62 lives here. `postcondition` and `goal` were one field, so `walk` -- whose goal (arrive) is approached
over many executions and guaranteed by none -- read as a motion failure on every step. The oracle, which always picks
an acceptable skill, came back 137 of 161 decisions "motion failure". Only four skills guarantee a postcondition after
one run; two carry a progress measure instead; six guarantee nothing and can never be held to account.

This matters because it routes the supervision. An operator takeover on a chooser failure is a label for the decision
layer; the same takeover on a motion failure is a trajectory for the policy, and writing it into the wrong one teaches
the wrong thing. E123/E144 measured that the FORM of an intervention decides what is learned; this decides which model
learns from it at all. Before effects were declared, every takeover went into one undifferentiated pile.
"""
from typing import Dict, Any, List, Optional

CHOOSER, MOTION, OK, NA = "chooser", "motion", "ok", "not_attributable"

def open_record(seed: int, room, facts: Dict[str, Any], opts: Dict[str, str], key: str,
                probs: Optional[Dict[str, float]], acceptable, arm: str, enum_name: str,
                planner_name: str, op_name: str, subgoal=None) -> Dict[str, Any]:
    """Built at decision time, before the skill runs. `probs` is whatever the chooser stated, or None for arms that
    state nothing -- recorded as None rather than as a fabricated 1.0, because a rule program has no probability and
    writing one in would make an uncalibrated arm look calibrated."""
    from stack.skills import resolve
    b = resolve(key, room)
    return {"key": f"{seed}:{room.t:.2f}", "seed": seed, "t": round(room.t, 2), "event": room.event,
            "state": facts, "options": dict(opts),
            "answer": {"choice": key, "confidence": (None if probs is None else round(float(probs.get(key, 0.0)), 4)),
                       "probabilities": (None if probs is None else {k: round(float(v), 4) for k, v in probs.items()})},
            "acceptable": sorted(acceptable), "chose_acceptable": key in acceptable,
            "arm": arm, "enumerator": enum_name, "planner": planner_name, "operator": op_name,
            "subgoal": (subgoal or {}).get("goal") if isinstance(subgoal, dict) else subgoal,
            "skill": (b.skill.name if b else None), "args": (b.kwargs if b else {}),
            "accountable": bool(b and (b.skill.postcondition is not None or b.skill.progress is not None)),
            "post_before": (b.achieved(room) if b else None),
            "progress_before": (b.distance(room) if b else None),
            "post_after": None, "progress_after": None, "attribution": None, "unresolved_proposals": None}

def close_record(rec: Dict[str, Any], room, eps: float = 0.02) -> Dict[str, Any]:
    """Called after the skill has run. A wrong pick is the chooser's regardless of what happened next; only a RIGHT pick
    can expose the motion layer. `eps` is the metres of progress a walking skill must make in one decision to count as
    having worked -- 0.02 m is well under the ~0.17 m a slow walk covers in half a second, so it is a floor on motion,
    not a performance target."""
    from stack.skills import resolve
    b = resolve(rec["answer"]["choice"], room)
    if not rec["chose_acceptable"]: rec["attribution"] = CHOOSER; return rec
    if b is None or not rec["accountable"]: rec["attribution"] = NA; return rec
    rec["post_after"] = b.achieved(room); rec["progress_after"] = b.distance(room)
    if rec["post_after"] is not None:
        rec["attribution"] = OK if (rec["post_after"] or rec["post_before"]) else MOTION
    elif rec["progress_after"] is not None and rec["progress_before"] is not None:
        rec["attribution"] = OK if (rec["progress_before"] - rec["progress_after"]) > eps else MOTION
    else:
        rec["attribution"] = NA
    return rec

def summarise(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Where the failures live, by layer. The denominator matters: only decisions whose skill declares an effect can be
    attributed at all, so both are reported."""
    n = len(records)
    att = {k: sum(1 for r in records if r["attribution"] == k) for k in (CHOOSER, MOTION, OK, NA)}
    attributable = sum(1 for r in records if r["accountable"] and r["chose_acceptable"])
    return {"decisions": n, "attributable": attributable,
            "chooser_failures": att[CHOOSER], "motion_failures": att[MOTION], "clean": att[OK],
            "not_attributable": att[NA],
            "motion_share_of_attributable": (round(att[MOTION] / attributable, 4) if attributable else None)}

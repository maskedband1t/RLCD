"""Decision-level evaluation of recorded Jev calls: was the chosen action in the acceptable set the ground
truth defines for that state? Gives per-decision accuracy and the confidence→correctness AUROC (P71.7).
Post-hoc in the sense that the acceptable set is computed from the recorded facts + the seed's ground truth."""
import json, sys, collections
import numpy as np
from .episodes import make_episode, COLOURS
from .policies import parse

def signature(parts):
    norm = lambda s: "unfamiliar_shape" if s in ("capsule", "unfamiliar_shape") else s
    return tuple((p["id"], p["colour"], norm(p["shape"]), p["size"], p["lot"]) for p in parts)

def seed_index(max_seed=280):
    idx = {}
    for s in range(max_seed):
        e = make_episode(s); idx[signature(e["parts"])] = (s, e)
    return idx

def acceptable(facts, spec):
    """The set of action keys the ground truth accepts in this state."""
    truth = spec["truth"]; parts = {p["id"]: p for p in facts["parts"]}; specp = {p["id"]: p for p in spec["parts"]}
    held = facts["robot"]["holding"]; hand = facts["robot"]["person_hand_in_workspace"]; trays = facts["trays"]
    acc = set()
    if hand:
        acc.add("pause")
        if held and specp[held]["fragile"] and specp[held]["mass"] >= 1.0: acc.add("set_down")
        return acc
    if facts["robot"]["grasp"] == "slipping": return {"regrasp"}
    def dest_ok(pid):
        d = truth[pid]["dest"]; blocked = trays[d] == "blocked_by_lid"
        keys = set()
        if not blocked: keys.add(f"place_{pid}_{d}")
        else: keys.add("wait")
        if truth[pid]["must_ask"]: keys.add("ask_operator")
        return keys
    if held: return dest_ok(held)
    pick = [p["id"] for p in facts["parts"] if (p["status"].startswith("on_table") or p["status"].startswith("sitting_on")) and not p["broken"]]
    if not pick: return {"done"}
    for pid in pick: acc |= dest_ok(pid)
    return acc

def auroc(scores, labels):
    pos = [s for s, l in zip(scores, labels) if l]; neg = [s for s, l in zip(scores, labels) if not l]
    if not pos or not neg: return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg); return wins / (len(pos) * len(neg))

def main(path):
    idx = seed_index(); rows = [json.loads(l) for l in open(path)]
    out = collections.defaultdict(list); unmatched = 0
    for r in rows:
        sig = signature(r["state"]["parts"])
        if sig not in idx: unmatched += 1; continue
        seed, spec = idx[sig]; acc = acceptable(r["state"], spec); a = r["answer"]
        ok = a["choice"] in acc
        deferred = (not ok) and a["choice"] == "ask_operator"     # asking when not required: costly, not wrong
        arm = r.get("arm", "jev"); out[arm].append((a["confidence"], ok, a["choice"], sorted(acc), r["state"]["robot"]["person_hand_in_workspace"], deferred))
    print(f"records {len(rows)}, unmatched {unmatched}")
    for arm, L in out.items():
        conf = [x[0] for x in L]; ok = [x[1] for x in L]; deferred = [x[5] for x in L]
        wrong = [not o and not d for o, d in zip(ok, deferred)]
        print(f"{arm}: decisions {len(L)}, acceptable {100*np.mean(ok):.1f}%, deferred-to-operator (not required) {100*np.mean(deferred):.1f}%, wrong {100*np.mean(wrong):.1f}%, AUROC(confidence→not wrong) {auroc(conf, [not w for w in wrong]):.3f}")
        # calibration-ish: acceptable rate by confidence bin
        bins = [(0, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)]
        for lo, hi in bins:
            sel = [o for c, o in zip(conf, ok) if lo <= c < hi]
            if sel: print(f"   conf [{lo:.1f},{hi:.1f}): n={len(sel):>4} acceptable {100*np.mean(sel):5.1f}%")
        wc = collections.Counter((x[2].split('_')[0], 'hand' if x[4] else 'nohand') for x in L if not x[1] and not x[5])
        print("   most common wrong choices:", wc.most_common(6))


def dest_eval(path):
    """E72: the destination head. Acceptable destination = ground-truth tray if not blocked; 'hold_or_ask' when the
    hand is present, the grasp is slipping, the tray is blocked, or the part is a must-ask item."""
    idx = seed_index(); rows = [json.loads(l) for l in open(path) if '"dest"' in l]
    out = collections.defaultdict(list)
    for r in rows:
        sig = signature(r["state"]["parts"])
        if sig not in idx: continue
        seed, spec = idx[sig]; f = r["state"]; held = f["robot"]["holding"]
        if held is None: continue
        t = spec["truth"][held]; acc = set()
        blocked = f["trays"][t["dest"]] == "blocked_by_lid"
        if not blocked: acc.add(t["dest"])
        if blocked or t["must_ask"] or f["robot"]["person_hand_in_workspace"] or f["robot"]["grasp"] == "slipping": acc.add("hold_or_ask")
        a = r["answer"]; ok = a["dest"] in acc
        out[r.get("arm", "jev2")].append((a["dest_confidence"], ok, a["dest"], sorted(acc)))
    for arm, L in out.items():
        conf = [x[0] for x in L]; ok = [x[1] for x in L]
        print(f"{arm}: held-part destination decisions {len(L)}, acceptable {100*np.mean(ok):.1f}%, AUROC(dest confidence → acceptable) {auroc(conf, ok):.3f}")
        for lo, hi in [(0, .3), (.3, .5), (.5, .7), (.7, .9), (.9, 1.01)]:
            sel = [o for c, o in zip(conf, ok) if lo <= c < hi]
            if sel: print(f"   conf [{lo:.1f},{hi:.1f}): n={len(sel):>4} acceptable {100*np.mean(sel):5.1f}%")
        wc = collections.Counter((x[2], x[3][0] if x[3] else '-') for x in L if not x[1])
        print("   most common wrong (chosen, first acceptable):", wc.most_common(6))

if __name__ == "__main__":
    main(sys.argv[1])
    dest_eval(sys.argv[1])

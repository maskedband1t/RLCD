"""E107: what a local 2B decider decides, read off jev_robot's published logs (third_party/jev_robot/benchmarks).
Usage: PYTHONPATH=src python src/field/e107_jev_robot.py"""
import json, glob, os, collections, numpy as np
sys_root = "third_party/jev_robot/benchmarks"

def rule(s):
    """a state machine over the Boolean facts, written from the method doc before looking at agreement"""
    if s.get("last_execution_error"): return "observe_scene"
    if s.get("arm_withdrawn") or (s.get("release_executed") and s.get("cube_seen_inside_tray")): return "done" if s.get("arm_withdrawn") else "retreat"
    if s.get("release_executed"): return "retreat"
    if s.get("object_held"):
        if s.get("at_release_height"): return "open_gripper"
        if s.get("over_place_target"): return "lower_to_place"
        if s.get("at_carry_height"): return "move_over_place"
        return "lift"
    if s.get("gripper_closed") and not s.get("object_held"): return "open_gripper"   # missed grasp: let go and re-observe
    if not s.get("target_visible") and not s.get("target_location_recent"): return "observe_scene"
    if s.get("target_changed_since_last_approach"): return "approach_target"
    if s.get("at_grasp_height") and s.get("over_target"): return "close_gripper"
    if s.get("over_target"): return "descend_to_target"
    return "approach_target"

def load(pattern):
    out = []
    for p in sorted(glob.glob(pattern, recursive=True)):
        try: d = json.load(open(p))
        except Exception: continue
        results = d.get("results") if isinstance(d, dict) else None
        if results is None and isinstance(d, dict) and "llm_choices" in d: results = [d]
        if results is None and isinstance(d, list): results = d
        if not results: continue
        for r in results:
            for c in r.get("llm_choices", []) or []:
                dec = c.get("decision") or {}
                if not dec.get("probabilities"): continue
                out.append({"file": p, "seed": r.get("seed"), "state": c.get("state", {}), "skill": dec.get("skill"), "conf": float(dec.get("confidence", max(dec["probabilities"].values()))), "probs": dec["probabilities"], "status": c.get("status"), "error": c.get("error")})
    return out

def auroc(p, y):
    p, y = np.asarray(p, float), np.asarray(y, int); pos, neg = p[y == 1], p[y == 0]
    return float((np.sum(pos[:, None] > neg[None, :]) + 0.5 * np.sum(pos[:, None] == neg[None, :])) / (len(pos) * len(neg))) if len(pos) and len(neg) else float("nan")

frozen = load(f"{sys_root}/dynamic/summary.json")
print(f"frozen batch: {len(frozen)} decisions, statuses {dict(collections.Counter(d['status'] for d in frozen))}, skills {dict(collections.Counter(d['skill'] for d in frozen))}")
agree = [rule(d["state"]) == d["skill"] for d in frozen]; print(f"P107.1 rule agreement: {np.mean(agree):.3f} ({sum(agree)}/{len(agree)})")
dis = collections.Counter((rule(d["state"]), d["skill"]) for d in frozen if rule(d["state"]) != d["skill"]); print("  disagreements (rule -> decider):", dict(dis.most_common(8)))
conf = np.array([d["conf"] for d in frozen]); print(f"P107.2 mean top-1 {conf.mean():.3f} | median {np.median(conf):.3f} | min {conf.min():.3f} | below .35: {(conf < .35).sum()} | below .7: {(conf < .7).sum()}")
post = np.array([bool(d["state"].get("target_changed_since_last_approach")) or bool(d["state"].get("last_execution_error")) for d in frozen])
print(f"P107.3 post-disturbance/error decisions: n {post.sum()} median conf {np.median(conf[post]):.3f} vs routine n {(~post).sum()} median {np.median(conf[~post]):.3f} (gap {np.median(conf[~post]) - np.median(conf[post]):+.3f})")
by = collections.defaultdict(list)
for d in frozen: by[d["skill"]].append(d["conf"])
print("  mean confidence by chosen skill:", {k: round(float(np.mean(v)), 3) for k, v in sorted(by.items())})
dev = load(f"{sys_root}/development/**/*.json")
if dev:
    st = collections.Counter(d["status"] for d in dev); print(f"\ndevelopment batches: {len(dev)} decisions, statuses {dict(st)}")
    rej = np.array([str(d["status"]).lower() not in ("accepted", "executed", "ok", "applied", "completed", "success") for d in dev]); c2 = np.array([d["conf"] for d in dev])
    if rej.any() and (~rej).any(): print(f"P107.4 confidence separates accepted from rejected: AUROC {auroc(c2, ~rej):.3f} | rejected n {rej.sum()} median conf {np.median(c2[rej]):.3f} | accepted n {(~rej).sum()} median {np.median(c2[~rej]):.3f}")
    else: print("P107.4 not scorable: no rejected decisions with probabilities in the development logs")
    ag = [rule(d["state"]) == d["skill"] for d in dev]; print(f"  rule agreement on development decisions: {np.mean(ag):.3f} ({sum(ag)}/{len(ag)})")
else: print("\nno development decision logs with probabilities found")

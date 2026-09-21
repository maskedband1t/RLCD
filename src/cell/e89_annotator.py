"""E89 · Jev as the annotator of teleop hours, scored against the cell's ground truth.

Runs `rules` episodes with a per-step logger (end-effector position, gripper content, person-hand flag, and the
executor's skill + phase as ground truth), cuts the log into 0.5 s windows, writes proprioception-only
categorical facts per window, asks Jev for the sub-action label (Choice) and a boundary flag (Noul), asks one
Score per episode for trainability, and scores everything against the truth beside a rule baseline that reads
the same facts. Pre-registered in the notebook (E89)."""
import os, json, os, sys, time, argparse, collections
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cell.harness import episode
from cell.decision_eval import auroc

LABELS = {
    "approach": "The empty gripper is moving toward a part to pick it up (typically heading toward the spawn area).",
    "grasp": "The empty gripper is descending onto a part and closing on it.",
    "lift": "The gripper is holding a part and rising away from the table.",
    "carry": "The gripper is holding a part and moving it toward its destination at carry height.",
    "lower_and_release": "The gripper is holding a part, lowering it into a tray, and letting go.",
    "return": "The gripper has just released a part into a tray and is rising or moving away, empty, within about a second of the release.",
    "set_down": "The gripper is putting a held part back down on the table (not in a tray).",
    "regrasp": "The gripper is re-taking a part that was slipping.",
    "pause_for_person": "The robot is holding still because a person's hand is in the workspace.",
    "wait": "The robot is holding still with nothing to do yet (for example, a blocked tray).",
    "ask_operator": "The robot is holding still while an operator is consulted.",
    "idle": "The robot is finished or has not started; nothing is happening.",
}
WIN = 10  # steps of 1/20 s

def gt_label(name, phase):
    if name is None: return "idle"
    if name.startswith("place_"):
        return ["approach", "grasp", "lift", "carry", "lower_and_release"][phase] if phase <= 4 else "return"
    if name == "set_down": return "set_down" if phase <= 1 else "return"
    if name == "regrasp": return "regrasp"
    if name == "pause": return "pause_for_person"
    if name == "wait": return "wait"
    if name == "ask_operator": return "ask_operator"
    if name == "confirm": return "wait"
    return "idle"

def collect(seeds, out_path):
    episodes = []
    for seed in seeds:
        steps = []
        def on_step(world, st, skill, ctrl):
            hp = world.hand_pos().copy()
            steps.append({"t": round(world.t, 2), "x": float(hp[0]), "y": float(hp[1]), "z": float(hp[2]), "held": world.held,
                          "hand": bool(ctrl["hand_seen"]), "grasp": ctrl["grasp"], "zone": world.zone(hp[0]), "blocked": sorted(world.blocked),
                          "skill": (skill.name if skill is not None else None), "phase": (int(getattr(skill, "phase", 0)) if skill is not None else 0),
                          "operator_consulted": bool(skill is not None and skill.name == "ask_operator")})
        r = episode(seed, "rules", on_step=on_step)
        episodes.append({"seed": seed, "clean": bool(r["violations"] == 0 and r["broken"] == 0 and r["floor"] == 0), "violations": r["violations"], "broken": r["broken"], "floor": r["floor"], "steps": steps})
        print(f"seed {seed}: {len(steps)} steps, clean={episodes[-1]['clean']}", flush=True)
    json.dump(episodes, open(out_path, "w")); return episodes

def windows(ep):
    S = ep["steps"]; out = []; prev_gt = None
    # gripper event history from the log itself (grasped / released and when) — a field any teleop log carries
    events = []; last = None
    for k, s_ in enumerate(S):
        if s_["held"] != last:
            events.append((k, ("grasped " + s_["held"]) if s_["held"] is not None else ("released " + str(last)))); last = s_["held"]
    def last_event(k):
        ev = [e for e in events if e[0] <= k]
        return ("none", None) if not ev else (ev[-1][1], round((k - ev[-1][0]) / 20.0, 1))
    for i in range(0, len(S) - WIN + 1, WIN):
        w = S[i:i + WIN]; z0, z1 = w[0]["z"], w[-1]["z"]
        path = sum(np.hypot(np.hypot(b["x"] - a["x"], b["y"] - a["y"]), b["z"] - a["z"]) for a, b in zip(w, w[1:]))
        speed = path / (WIN / 20.0)
        held = w[-1]["held"]; released = any(a["held"] is not None and b["held"] is None for a, b in zip(w, w[1:]))
        gripper = "released_this_window" if released else ("empty" if held is None else f"holding {held}")
        vert = "rising" if z1 - z0 > 0.02 else ("lowering" if z0 - z1 > 0.02 else "level")
        facts = {"zone": collections.Counter(s["zone"] for s in w).most_common(1)[0][0],
                 "height": "table_level" if np.mean([s["z"] for s in w]) < 0.06 else ("low" if np.mean([s["z"] for s in w]) < 0.15 else "carry_height"),
                 "motion": "still" if speed < 0.02 else "moving", "vertical": vert, "gripper": gripper,
                 "grasp_state": w[-1]["grasp"], "person_hand_in_workspace": any(s["hand"] for s in w), "blocked_trays": w[-1]["blocked"],
                 "last_gripper_event": last_event(i + WIN - 1)[0], "seconds_since_last_gripper_event": last_event(i + WIN - 1)[1],
                 "heading": ("toward_trays" if w[-1]["x"] - w[0]["x"] > 0.02 else ("toward_spawn_area" if w[0]["x"] - w[-1]["x"] > 0.02 else "none")),
                 "operator_consulted": any(s.get("operator_consulted") for s in w)}
        gts = [gt_label(s["skill"], s["phase"]) for s in w]; gt = collections.Counter(gts).most_common(1)[0][0]
        out.append({"i": i // WIN, "t": w[0]["t"], "facts": facts, "gt": gt, "gt_boundary": (prev_gt is not None and gt != prev_gt)}); prev_gt = gt
    return out

def rule(facts):
    g = facts["gripper"]; v = facts["vertical"]; m = facts["motion"]
    if facts["person_hand_in_workspace"]: return "pause_for_person"
    if facts.get("operator_consulted"): return "ask_operator"
    if g == "released_this_window": return "lower_and_release"
    if g.startswith("holding"):
        if facts["grasp_state"] == "slipping": return "regrasp"
        if v == "lowering": return "lower_and_release"
        if v == "rising": return "lift"
        return "carry" if m == "moving" else "wait"
    if v == "rising": return "return"
    if v == "lowering": return "grasp"
    if m == "moving":
        h = facts.get("heading", "none")
        if h == "toward_spawn_area": return "approach" if facts.get("last_gripper_event", "none") != "none" or True else "approach"
        if h == "toward_trays": return "return" if facts.get("last_gripper_event", "none").startswith("released") and (facts.get("seconds_since_last_gripper_event") or 99) < 1.0 else "approach"
        return "return" if (facts.get("last_gripper_event", "none").startswith("released") and (facts.get("seconds_since_last_gripper_event") or 99) < 1.5) else "approach"
    return "idle"

def annotate(episodes, out_path, sample_every=10):
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
    client = TypeSafeClient(api_key=os.environ.get("TYPESAFE_API_KEY")); rows = []; ep_scores = []
    for ep in episodes:
        W = windows(ep); prev = "none"; hist = collections.Counter(); n_release = 0; n_pause = 0
        for w in W:
            state = {"window_seconds": 0.5, "robot_facts": w["facts"], "previous_window_label": prev}
            qs = {"subaction": Choice(instructions={"role": "You label a teleoperation log of a sorting robot into sub-actions, one label per half-second window.",
                                                    "ask": "Which sub-action is the robot performing in this window?"}, criteria=LABELS),
                  "boundary": Noul(instructions="Does a new sub-action begin in this window (different from the previous window's label)?",
                                   criteria={"true": "This window starts a new sub-action.", "false": "This window continues the previous sub-action."})}
            ans = call(client, state, qs)
            if ans is None: continue
            lab = ans["subaction"].choice; conf = float(ans["subaction"].confidence); bnd = float(ans["boundary"].noul)
            row = {"seed": ep["seed"], "i": w["i"], "t": w["t"], "gt": w["gt"], "gt_boundary": w["gt_boundary"], "rule": rule(w["facts"]), "jev": lab, "conf": conf, "boundary": bnd}
            if w["i"] % sample_every == 0:  # consistency subsample: repeat, and reversed option order
                rep = call(client, state, qs); rev = call(client, state, {**qs, "subaction": Choice(instructions=qs["subaction"].instructions, criteria=dict(reversed(list(LABELS.items()))))})
                row["repeat"] = rep["subaction"].choice if rep else None; row["reversed"] = rev["subaction"].choice if rev else None
            rows.append(row); prev = lab; hist[lab] += 1; n_release += lab == "lower_and_release"; n_pause += lab == "pause_for_person"
        summary = {"windows": len(W), "label_counts": dict(hist), "releases": n_release, "pause_windows": n_pause,
                   "releases_outside_tray_area": sum(1 for r_ in rows if r_["seed"] == ep["seed"] and r_["jev"] == "lower_and_release" and False)}
        sq = {"trainable": Score(instructions="Judging only from this summary of the annotated demonstration, how usable is it as training data?",
                                 criteria=["not trainable: interrupted, messy or incomplete", "usable after cleaning", "clean demonstration"])}
        sa = call(client, {"demonstration_summary": summary}, sq)
        ep_scores.append({"seed": ep["seed"], "clean": ep["clean"], "score": float(sa["trainable"].score) if sa else None})
        print(f"seed {ep['seed']}: {len(W)} windows annotated; trainability score {ep_scores[-1]['score']} (clean={ep['clean']})", flush=True)
        json.dump({"rows": rows, "episodes": ep_scores}, open(out_path, "w"))
    return rows, ep_scores

def call(client, state, qs):
    for attempt in range(3):
        try: return client.system_one(state=state, model=os.environ.get("CELL_JEV_MODEL", "jev-latest"), questions=qs).answers  # E89c: CELL_JEV_MODEL=jev-preview
        except Exception as e: err = e; time.sleep(1.5 * (attempt + 1))
    print("call failed:", str(err)[:100]); return None

def evaluate(path):
    d = json.load(open(path)); rows = d["rows"]; eps = d["episodes"]
    gt = np.array([r["gt"] for r in rows]); jv = np.array([r["jev"] for r in rows]); rl = np.array([r["rule"] for r in rows]); conf = np.array([r["conf"] for r in rows])
    print(f"windows {len(rows)} | episodes {len(eps)}")
    print(f"label accuracy: Jev {np.mean(jv == gt):.1%} | rule baseline {np.mean(rl == gt):.1%} | previous-label baseline {np.mean([rows[i-1]['gt'] == rows[i]['gt'] for i in range(1, len(rows))]):.1%}")
    print(f"completeness: windows with confidence >= .7: {np.mean(conf >= .7):.1%} | accuracy above .7: {np.mean(jv[conf >= .7] == gt[conf >= .7]):.1%} | below .7: {np.mean(jv[conf < .7] == gt[conf < .7]):.1%}")
    # boundaries within +-1 window
    by_seed = collections.defaultdict(list)
    for r in rows: by_seed[r["seed"]].append(r)
    tp = fp = fn = 0
    for s, R in by_seed.items():
        R.sort(key=lambda r: r["i"]); truth = {r["i"] for r in R if r["gt_boundary"]}; pred = {r["i"] for r in R if r["boundary"] >= .5}
        tp += sum(1 for p in pred if any(abs(p - t) <= 1 for t in truth)); fp += sum(1 for p in pred if not any(abs(p - t) <= 1 for t in truth)); fn += sum(1 for t in truth if not any(abs(p - t) <= 1 for p in pred))
    print(f"boundaries (+-1 window): recall {tp/max(1,tp+fn):.1%} precision {tp/max(1,tp+fp):.1%} (true boundaries {tp+fn}, predicted {tp+fp})")
    rep = [r for r in rows if r.get("repeat")]; rev = [r for r in rows if r.get("reversed")]
    if rep: print(f"consistency on {len(rep)} sampled windows: repeat agreement {np.mean([r['repeat'] == r['jev'] for r in rep]):.1%} | reversed-order agreement {np.mean([r['reversed'] == r['jev'] for r in rev]):.1%}")
    print("per-label accuracy (Jev / rule / n):", {l: (round(float(np.mean(jv[gt == l] == l)), 2), round(float(np.mean(rl[gt == l] == l)), 2), int((gt == l).sum())) for l in LABELS if (gt == l).sum()})
    conf_pairs = collections.Counter((g, j) for g, j in zip(gt, jv) if g != j).most_common(6); print("top confusions (truth -> Jev):", conf_pairs)
    sc = [e for e in eps if e["score"] is not None]
    if len({e["clean"] for e in sc}) == 2: print(f"trainability: AUROC(score -> clean) {auroc([e['score'] for e in sc], [e['clean'] for e in sc]):.3f} on {len(sc)} episodes ({sum(e['clean'] for e in sc)} clean)")
    else: print("trainability: all episodes share one clean label; AUROC undefined", collections.Counter(e["clean"] for e in sc))
    print("E89_DONE", flush=True)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seeds", default="0-19"); ap.add_argument("--traj", default="results/cell/e89_trajectories.json"); ap.add_argument("--out", default="results/cell/e89_annotations.json"); ap.add_argument("--eval-only", action="store_true"); a = ap.parse_args()
    if not a.eval_only:
        lo, hi = a.seeds.split("-"); eps = collect(list(range(int(lo), int(hi) + 1)), a.traj); annotate(eps, a.out)
    evaluate(a.out)

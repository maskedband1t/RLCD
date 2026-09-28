"""A measured skill table — the movement layer as data instead of physics.

We are not studying navigation or balance, so simulating them manufactures failures that are not the
research question and then costs hours to explain away (see METHOD-ERROR-76/77 and S1-E12). Instead:
run the real physics once, measure what each skill actually does from each kind of situation, and then
sample from those measurements.

What it deliberately KEEPS is the consequence of choosing speed near a solid workspace — S1-E12's
finding — because the bucket carries distance-to-table and the skill carries the speed. What it throws
away is the path simulation, which was the confound.

  harvest:  PYTHONPATH=src USE_TF=0 DUCK_BODY=g1 DUCK_CONTACT=1 DUCK_CONTACT_PROPS=all \
            python src/duck/skill_table.py harvest --episodes 120 --out results/duck/skills.jsonl
  build:    python src/duck/skill_table.py build --in results/duck/skills.jsonl --out results/duck/skills.json
"""
import os, sys, json, random, argparse, time
from collections import defaultdict

sys.path.insert(0, "src")

# The state the outcome is assumed to depend on. Deliberately small: every extra field splits the
# counts and a bucket with five samples in it is a rumour, not a measurement.
def bucket(f, prev=None, speed=None):
    """The state the outcome is assumed to depend on.

    `prev` and `speed` are NOT optional detail. A first version without them was built on 2026-09-27
    and was measurably wrong: it reported p(fall) near 0.00 for walking beside the table, while the
    real physics falls in 100% of episodes for a policy that walks repeatedly. Falls are a property of
    action SEQUENCES -- one step at walking pace is harmless, ten in a row build the momentum that
    topples the robot into a solid surface. A bucket that cannot see "was I already moving" deletes
    exactly the finding the table exists to preserve.
    """
    r = f.get("robot", {})
    p = f.get("person", {})
    sp = "?" if speed is None else ("fast" if speed > 0.45 else "slow" if speed > 0.15 else "still")
    return "|".join([
        "hold:" + str(r.get("holding", "?")),
        "table:" + str(r.get("table", "?")),
        "person:" + str(p.get("distance", "?")),
        "moving:" + sp,
        "prev:" + str(prev),
    ])


def harvest(n_episodes, out, seeds, policy="mix"):
    """Harvest from a MIXTURE of policies, not from random play.

    A random policy almost never falls, because falling needs sustained momentum and random choice
    keeps interrupting it. Harvesting only from random therefore measures p(fall) near 0.00 for
    exactly the situations where a committed walker falls every time -- the same covariate-shift trap
    as training an apprentice only on the expert's states. The mixture includes the policies whose
    states the table will actually be asked about.
    """
    from duck import e93_run as R
    rng = random.Random(0)
    arms = {}
    if policy == "mix":
        for nm in ("rules", "oracle"):
            try: arms[nm] = R.make_arm(nm)
            except Exception: pass
    rows = 0
    t0 = time.time()
    with open(out, "a") as fh:
        for i in range(n_episodes):
            seed = seeds[i % len(seeds)]
            room = R.Room(seed)
            room.physics(int(1.0 / room.cdt))
            fell0 = False; prev = None
            while room.t < R.MAX_T and not room.fell:
                f = room.facts(); opts = sorted(room.options()); acc = room.acceptable()
                if not opts:
                    break
                key = bucket(f, prev, room.body_speed())
                # sample uniformly over the LEGAL options so every skill is measured in every bucket,
                # not only the ones a good policy would pick
                # cycle the behaviour generating the states: a committed walker and the scripted
                # arms visit the momentum-heavy states that random play never reaches
                mode = ("walker", "random", "rules", "oracle")[i % 4] if policy == "mix" else "random"
                if mode == "walker" and "walk" in opts and rng.random() < 0.85:
                    skill = "walk"
                elif mode in arms:
                    try: skill = arms[mode].decide(f, room.options(), room)[0]
                    except Exception: skill = rng.choice(opts)
                    if skill not in opts: skill = rng.choice(opts)
                else:
                    skill = rng.choice(opts)
                prev_for_next = skill
                t_before = room.t
                viol_before = (room.near_contact_events + room.child_zone_events + room.door_collisions
                               + room.cut_offs + room.kicks + getattr(room, "wrong_handovers", 0))
                held_before = room.holding
                room.run_skill(skill)
                fell = room.fallen()
                viol_after = (room.near_contact_events + room.child_zone_events + room.door_collisions
                              + room.cut_offs + room.kicks + getattr(room, "wrong_handovers", 0))
                fh.write(json.dumps({
                    "seed": seed, "bucket": key, "skill": skill,
                    "dt": round(room.t - t_before, 3),
                    "fell": bool(fell),
                    "dviol": int(viol_after - viol_before),
                    "acceptable": skill in acc,
                    "picked_up": bool(held_before is None and room.holding is not None),
                    "delivered": bool(room.delivered_to is not None),
                    "next": bucket(room.facts(), prev_for_next, room.body_speed()),
                }) + "\n")
                rows += 1
                prev = skill
                if fell:
                    fell0 = True; break
            if (i + 1) % 10 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{n_episodes} episodes, {rows} transitions, {el:.0f}s "
                      f"({rows/max(el,1e-9):.1f} transitions/s)", flush=True)
            fh.flush()
    print(f"harvested {rows} transitions -> {out}")


def build(inp, out, min_n):
    agg = defaultdict(lambda: {"n": 0, "fell": 0, "dviol": 0, "dt": 0.0, "acc": 0,
                               "picked": 0, "delivered": 0, "next": defaultdict(int)})
    for line in open(inp):
        r = json.loads(line)
        a = agg[(r["bucket"], r["skill"])]
        a["n"] += 1; a["fell"] += int(r["fell"]); a["dviol"] += r["dviol"]
        a["dt"] += r["dt"]; a["acc"] += int(r["acceptable"])
        a["picked"] += int(r["picked_up"]); a["delivered"] += int(r["delivered"])
        a["next"][r["next"]] += 1

    table, thin = {}, 0
    for (b, s), a in agg.items():
        n = a["n"]
        if n < min_n:
            thin += 1
            continue
        table.setdefault(b, {})[s] = {
            "n": n,
            "p_fall": round(a["fell"] / n, 4),
            "p_violation": round(a["dviol"] / n, 4),
            "p_acceptable": round(a["acc"] / n, 4),
            "p_pickup": round(a["picked"] / n, 4),
            "mean_dt": round(a["dt"] / n, 3),
            "next": {k: round(v / n, 4) for k, v in sorted(a["next"].items(), key=lambda kv: -kv[1])[:6]},
        }
    with open(out, "w") as fh:
        json.dump({"min_n": min_n, "buckets": table}, fh, indent=1)
    cells = sum(len(v) for v in table.values())
    print(f"built {cells} (bucket, skill) cells across {len(table)} buckets  "
          f"[dropped {thin} cells with n < {min_n}]  -> {out}")
    return table


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["harvest", "build"])
    ap.add_argument("--episodes", type=int, default=120)
    ap.add_argument("--seeds", default="40-59")
    ap.add_argument("--in", dest="inp", default="results/duck/skills.jsonl")
    ap.add_argument("--out", default="results/duck/skills.jsonl")
    ap.add_argument("--min-n", type=int, default=8)
    ap.add_argument("--policy", default="mix", choices=["mix","random"])
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-")
    seeds = list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    os.makedirs("results/duck", exist_ok=True)
    if a.cmd == "harvest":
        harvest(a.episodes, a.out, seeds, a.policy)
    else:
        build(a.inp, a.out, a.min_n)

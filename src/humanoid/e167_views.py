"""E167: what does a viewpoint that is not the robot's head buy?

E166 measured the ego view and it is worse than anyone assumed: the nearest person is visible at 25.7 % of decisions and
the carried object at 0 %, because a head camera at 1.25 m with a 58 degree cone cannot see its own hands and cannot see
anyone who is not roughly in front of it. This asks what a second viewpoint recovers, and deliberately includes the cheapest
possible one: a fixed camera on the wall, which a warehouse or a home already has."""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from humanoid.fetch_sim import Room
from humanoid.eye import Eye, HEAD_Z, ROOM_POS, DOOR_POS

def band(d): return "touching <0.5" if d < 0.5 else ("close <1.0" if d < 1.0 else ("near <1.8" if d < 1.8 else "far"))

def views(R, eye, names):
    out = {}
    eye.aim(R.xy(), R.yaw()); out["head"] = eye.visible(R.data, names)
    w = R.data.body(R.model.body("right_wrist_yaw_link").id).xpos.copy() if "right_wrist_yaw_link" in [R.model.body(i).name for i in range(R.model.nbody)] else None
    if w is not None:
        f = np.array([math.cos(R.yaw()), math.sin(R.yaw()), -0.25])
        eye.aim_at(w, w + f * 0.8); out["wrist"] = eye.visible(R.data, names)
    eye.aim_at(ROOM_POS, (2.5, 0.0, 0.9)); out["room"] = eye.visible(R.data, names)
    eye.aim_at(DOOR_POS, (2.0, 0.0, 0.9)); out["door"] = eye.visible(R.data, names)
    return out

def run(seed, arm_name, out, max_dec=400):
    from duck.e93_run import make_arm
    R = Room(seed); arm = make_arm(arm_name); eye = Eye(R.model); n = 0
    names = [p.name for p in R.people] + ["parcel"]
    while R.t < 120.0 and n < max_dec:
        o = R.options()
        if not o: break
        V = views(R, eye, names)
        near = R.nearest(); d = R.dist(near.xy)
        key, _ = arm.decide(R.facts(), o, R)
        rec = {"seed": seed, "arm": arm_name, "event": R.event, "t": round(R.t, 2),
               "nearest": near.name, "nearest_dist": round(d, 3), "nearest_band": band(d), "holding": R.holding is not None}
        for v, m in V.items():
            rec[f"near_{v}"] = bool(m[near.name]["visible"]); rec[f"obj_{v}"] = bool(m["parcel"]["visible"])
        out.write(json.dumps(rec) + "\n"); out.flush()
        if key == "done": break
        R.run_skill(key); n += 1
    return n

if __name__ == "__main__":
    lo, hi = (int(x) for x in sys.argv[1].split("-"))
    with open("results/duck/e167.jsonl", "a") as out:
        for a in sys.argv[2].split(","):
            for s in range(lo, hi + 1):
                print(f"  {a:<8} seed {s:<4} {run(s, a, out)} decisions", flush=True)
    print("E167_DONE", flush=True)

"""E166 stage 1: at each decision, is the entity the decision layer's facts describe actually in the robot's head view?"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.fetch_sim import Room
from humanoid.eye import Eye

def band(d): return "touching <0.5" if d < 0.5 else ("close <1.0" if d < 1.0 else ("near <1.8" if d < 1.8 else "far"))

def run(seed, arm_name, out, max_dec=400):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "duck"))
    from duck.e93_run import make_arm
    R = Room(seed); arm = make_arm(arm_name); eye = Eye(R.model)
    n = 0
    while R.t < 120.0 and n < max_dec:
        f = R.facts(); opts = R.options()
        if not opts: break
        eye.aim(R.xy(), R.yaw())
        names = [p.name for p in R.people] + ["parcel"]
        vis = eye.visible(R.data, names)
        near = R.nearest(); d = R.dist(near.xy)
        key, _ = arm.decide(f, opts, R)
        out.write(json.dumps({
            "seed": seed, "arm": arm_name, "event": R.event, "t": round(R.t, 2), "decision": key,
            "nearest": near.name, "nearest_dist": round(d, 3), "nearest_band": band(d),
            "nearest_visible": vis[near.name]["visible"], "nearest_px": vis[near.name]["pixels"],
            "requester": R.req.name, "requester_visible": vis.get(R.req.name, {}).get("visible", False),
            "holding": R.holding is not None, "object_visible": vis["parcel"]["visible"], "object_px": vis["parcel"]["pixels"],
        }) + "\n"); out.flush()
        if key == "done": break
        R.run_skill(key); n += 1
    return n

if __name__ == "__main__":
    lo, hi = (int(x) for x in sys.argv[1].split("-"))
    arms = sys.argv[2].split(",")
    with open("results/duck/e166.jsonl", "a") as out:
        for a in arms:
            for s in range(lo, hi + 1):
                n = run(s, a, out)
                print(f"  {a:<8} seed {s:<4} {n} decisions", flush=True)
    print("E166_DONE", flush=True)

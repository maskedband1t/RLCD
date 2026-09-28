"""Does a released progress estimator see the livelock that confidence cannot?

S1-E15: the calibrated arm spent 37 seconds repeating `step_around`/`walk` with the person frozen at
0.45 m, every action outside the acceptable set, and confidence never left 0.52-0.66. Per-decision
confidence is blind to it because the failure is a property of the sequence.

X-Planner-9B natively reports `progress_percent` per subtask and an `execution_decision`. Those are
embodiment-agnostic even though its planning is not. This replays an episode and asks it, at every
decision, from a rendered view of the actual scene, whether execution should continue.

  PYTHONPATH=src USE_TF=0 DUCK_BODY=g1 DUCK_CONTACT=1 DUCK_CONTACT_PROPS=all DUCK_TABLE_STANDOFF=1.05 \
  python src/duck/progress_probe.py --arm laya --seeds 40,41 --out results/duck/progress_probe.jsonl
"""
import os, sys, json, base64, time, argparse, urllib.request
sys.path.insert(0, "src")

URL = os.environ.get("XPLANNER_URL", "http://127.0.0.1:8891/v1/chat/completions")
ASK = ("Robot skills: ask_operator, done, hand_to, pick_up, stop, walk, walk_slow, wait, turn_away, "
       "step_around, put_down.\nTask: fetch the object from the table and hand it to the person who "
       "asked for it.\nGiven this view, output the plan JSON including execution_decision.")


def query(png_bytes, timeout=120):
    b64 = base64.b64encode(png_bytes).decode()
    body = json.dumps({"messages": [{"role": "user", "content": [
        {"type": "text", "text": ASK},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}}]}],
        "temperature": 0, "max_tokens": 220,
        "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        out = json.load(urllib.request.urlopen(req, timeout=timeout))
        txt = out["choices"][0]["message"]["content"]
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:80]}", "latency": round(time.time() - t0, 2)}
    rec = {"raw": txt[:400], "latency": round(time.time() - t0, 2)}
    try:
        d = json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
        rec["execution_decision"] = d.get("execution_decision")
        rec["decision_detail"] = d.get("decision_detail")
        progs = []
        for s in d.get("subtasks", []) or d.get("initial_plan", []):
            sk = s.get("skill") or s.get("action") or {}
            if isinstance(sk, dict) and sk.get("progress_percent") is not None:
                progs.append(sk["progress_percent"])
        rec["progress"] = progs
        rec["schema"] = "subtasks" if "subtasks" in d else ("initial_plan" if "initial_plan" in d else "other")
    except Exception:
        rec["execution_decision"] = None
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="laya")
    ap.add_argument("--seeds", default="40,41")
    ap.add_argument("--out", default="results/duck/progress_probe.jsonl")
    ap.add_argument("--max-steps", type=int, default=40)
    a = ap.parse_args()

    import numpy as np, mujoco
    from PIL import Image
    import io
    from duck import e93_run as R
    from humanoid.fetch_sim import Room, TABLE

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "a") as fh:
        for seed in [int(s) for s in a.seeds.split(",")]:
            room = Room(seed); room.physics(int(1.0 / room.cdt))
            arm = R.make_arm(a.arm)
            m = room.model; m.vis.global_.offwidth = 640; m.vis.global_.offheight = 480
            ren = mujoco.Renderer(m, 480, 640); cam = mujoco.MjvCamera()
            prev_pd = None; frozen = 0; prev_key = None; run_len = 0
            print(f"\n=== seed {seed} · event={room.event} · arm={a.arm} ===", flush=True)
            print(f"{'t':>6} {'action':<14}{'ok':<4}{'persD':>7}{'frozen':>7}{'run':>5}  {'decision':<12}{'progress'}", flush=True)
            for step in range(a.max_steps):
                f = room.facts(); opts = room.options(); acc = room.acceptable()
                key, j = arm.decide(f, opts, room)
                pd = room.person_dist()
                frozen = frozen + 1 if (prev_pd is not None and abs(pd - prev_pd) < 0.10) else 0
                run_len = run_len + 1 if key == prev_key else 0
                bx, by = float(room.data.qpos[0]), float(room.data.qpos[1])
                cam.lookat[:] = [bx, by, 0.8]; cam.distance = 3.0; cam.elevation = -15
                cam.azimuth = float(np.degrees(np.arctan2(TABLE[1] - by, TABLE[0] - bx))) + 180
                ren.update_scene(room.data, cam)
                buf = io.BytesIO(); Image.fromarray(ren.render()).save(buf, format="PNG")
                res = query(buf.getvalue())
                rec = dict(seed=seed, event=room.event, arm=a.arm, step=step, t=round(room.t, 1),
                           action=key, acceptable=key in acc, person_dist=round(pd, 3),
                           frozen_steps=frozen, action_run_length=run_len, **res)
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                print(f"{room.t:>6.1f} {key:<14}{'y' if key in acc else 'N':<4}{pd:>7.2f}{frozen:>7}{run_len:>5}  "
                      f"{str(res.get('execution_decision'))[:11]:<12}{res.get('progress')}", flush=True)
                if key == "done": break
                prev_pd, prev_key = pd, key
                room.run_skill(key)
                if room.fallen():
                    print(f"   -> FELL at t={room.t:.1f}", flush=True); break
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()

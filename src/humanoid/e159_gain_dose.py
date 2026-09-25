"""E159: the dose-response of each perturbation family below the +/-30 % already measured, mapped onto what the field
actually randomises. Isaac Lab ships randomize_actuator_gains and its G1 locomotion env never calls it; MuJoCo Playground's
G1 policy was trained without gain randomisation either. Its base velocity env randomises base mass by +/-5 kg, which on
this 33.34 kg robot is +/-15 % of the whole. So: at the magnitudes the field does randomise, does it matter which family?"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from humanoid.g1_loco_env import evaluate
from humanoid.g1_policy_torch import load_from_onnx, Runner

POLICIES = [("shipped", load_from_onnx().act),
            ("direct", Runner("results/humanoid/g1_pt/best.pt").pol.act),
            ("edit", Runner("results/humanoid/g1_edit/best.pt").pol.act)]
GRID = [("gain", d) for d in (0.10, 0.15, 0.20, 0.25)] + [("mass", d) for d in (0.15, 0.20)] + [("friction", d) for d in (0.15, 0.20)]
N = int(os.environ.get("E159_N", "100"))
out = open("results/humanoid/e159.jsonl", "a")
print(f"E159_START {time.strftime('%H:%M %Z')}", flush=True)
for fam, d in GRID:
    for name, act in POLICIES:
        t0 = time.time()
        r = evaluate(act, n_episodes=N, perturb_delta=d, perturb_params=(fam,))
        r.update(policy=name, family=fam, delta=d, wall_s=round(time.time() - t0, 1))
        out.write(json.dumps(r) + "\n"); out.flush()
        print(f"  {fam:<9} d={d:.2f}  {name:<8} falls {r['fall_rate']:.2f}  rmse {r['rmse_vx']:.3f}  ({r['wall_s']}s)", flush=True)
print(f"E159_ALL_DONE {time.strftime('%H:%M %Z')}", flush=True)

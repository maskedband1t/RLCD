"""Contact probe for the humanoid benches (method error 76).

The G1 scene is `scene_mjx_feetonly_flat_terrain.xml`: collision is carried by FIVE explicit
<pair> elements (floor-feet, foot-foot, thigh-hand) and every geom's contype/conaffinity is 0.
So nothing else in the world can ever touch the robot, and setting furniture geoms solid has no
effect — there is no mask for them to match. The room is decoration.

This probe turns contact ON with a bitmask that keeps the robot's own self-collision behaviour
intact, then drives the robot into the counter and reports whether the shipped walking policy
survives it.

  robot  group-3 colliders : contype=2 conaffinity=4
  room / furniture geoms   : contype=4 conaffinity=2

  robot x furniture -> (2&2)|(4&4) != 0   collide
  robot x robot     -> (2&4)|(2&4) == 0   unchanged, still governed by the explicit pairs
  furn  x furn      -> (4&2)|(4&2) == 0   no internal churn
  robot x floor     -> (2&1)|(1&4) == 0   unchanged, feet still stand via pair 0/1

  PYTHONPATH=src USE_TF=0 python src/humanoid/probe_contact.py
"""
import sys, os
sys.path.insert(0, "src")
import numpy as np, mujoco

ROOM_BODIES = ("kitchen", "glass", "carton", "mug", "drawer", "medicine")
# The G1 has NO torso collider: its group-3 primitives are feet (z~0.03), thighs (~0.50) and hands
# (~0.68). The counter occupies z[0.80,1.31] and the torso z[0.74,1.16] — the one band that overlaps
# is the one band with no collision geometry, so a humanoid physically cannot bump into a counter.
# Promote the torso/pelvis visual meshes to colliders (their convex hulls are the right shape).
TORSO_BODIES = ("pelvis", "waist_yaw_link", "waist_roll_link", "torso_link")


def enable_contact(r):
    """Give the robot's collision primitives and the room a matching contact mask. Returns counts."""
    m = r.model
    nrob = nroom = 0
    for g in range(m.ngeom):
        b = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, int(m.geom_bodyid[g])) or ""
        if b == "world":
            continue
        if b in ROOM_BODIES:
            m.geom_contype[g] = 4; m.geom_conaffinity[g] = 2; nroom += 1
        elif int(m.geom_group[g]) == 3 or b in TORSO_BODIES:
            m.geom_contype[g] = 2; m.geom_conaffinity[g] = 4; nrob += 1
    return nrob, nroom


def _contacts(r):
    m = r.model; out = []
    for i in range(r.data.ncon):
        c = r.data.contact[i]
        n1 = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(c.geom1)) or f"g{c.geom1}"
        n2 = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, int(c.geom2)) or f"g{c.geom2}"
        out.append((n1, n2))
    return out


def run(contact, steps=30, place="counter", verbose=True):
    from humanoid.kitchen_sim import KitchenRoom
    r = KitchenRoom(0)
    tag = "CONTACT" if contact else "GHOST  "
    if contact:
        nrob, nroom = enable_contact(r)
        if verbose: print(f"  enabled: {nrob} robot colliders, {nroom} room geoms")
    for _ in range(3): r.run_skill("stand(seconds=0.5)")
    for _ in range(3): r.run_skill(f"turn_to(place={place})")
    z0 = float(r.data.qpos[2])
    nonfoot, fell, first = set(), False, None
    for i in range(steps):
        r.run_skill(f"move_to(place={place},speed=normal)")
        z = float(r.data.qpos[2])
        for a, b in _contacts(r):
            if "foot" not in a or "foot" not in b:
                if "floor" not in (a, b) or ("foot" not in a and "foot" not in b):
                    nonfoot.add(f"{a}<->{b}")
                    if first is None: first = (i, f"{a}<->{b}")
        if verbose and i % 5 == 0:
            print(f"    step {i:>2} xy=({r.data.qpos[0]:5.2f},{r.data.qpos[1]:5.2f}) z={z:.3f} ncon={r.data.ncon}")
        if z < 0.45:
            fell = True; break
    xy = r.data.qpos[:2]
    print(f"{tag} z {z0:.3f}->{float(r.data.qpos[2]):.3f}  xy=({xy[0]:.2f},{xy[1]:.2f})  "
          f"fell={fell}  ncon={r.data.ncon}  non-foot contacts={len(nonfoot)}")
    if first: print(f"         first non-foot contact at step {first[0]}: {first[1]}")
    for c in sorted(nonfoot)[:6]: print(f"           {c}")
    return dict(fell=fell, xy=xy.copy(), z=float(r.data.qpos[2]), nonfoot=sorted(nonfoot))


if __name__ == "__main__":
    from humanoid.kitchen_sim import COUNTER, START
    print(f"start {START} -> counter {COUNTER}\n")
    a = run(False); print(); b = run(True)
    print("\nVERDICT")
    if not b["nonfoot"]:
        print("  INCONCLUSIVE — the robot never touched the room even with contact on.")
    elif b["fell"] and not a["fell"]:
        print("  Contact is REAL and the shipped policy FALLS on it. Enabling it changes every humanoid result.")
    elif b["nonfoot"] and not b["fell"]:
        print("  Contact is REAL and the shipped policy SURVIVES it. Safe to enable on the humanoid benches.")

"""Bench 6: the sorting task inside HomeBody's scanned kitchen, with the simulator supplying correct facts.

Perception is a CONTROLLED LEVEL here, not the research question. Level 0 is "assume perception works" -- the simulator
hands over correct typed facts -- so the thing under test is the decomposition of the question put to the calibrated
model, with everything else held fixed. E189 measured level 1 (facts from the head camera) at identity 1 of 11 and is
recorded as a scope limit on every result above it; making a VLM recognise objects is a different research problem and
HomeBody, SAM and others are on it.

Same room, same body, same walking policy, same skills as bench 5b. The only change is where it all happens.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, mujoco
from humanoid.fetch_sim import assets, G1_DIR, CMD_FAST, CMD_SLOW, DECISION_S
from humanoid.sort_sim import SortRoom

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tools"))
from hb_kitchen import (kitchen_xml, COUNTER, COUNTER_Z, DRAWER, BIN_XY, START, OBJECTS, IN_DRAWER, LIFT)

TEX = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                   "third_party", "homebody", "tex_scene")
DEST_K = {"glass": "counter", "mug": "counter", "carton": "bin", "medicine": "counter"}
REACH_K = 1.10


class KitchenRoom(SortRoom):
    """Clear the counter: crockery stays put on the far end, packaging goes in the bin. The drawer holds the medicine."""

    def build(self):
        tex_asset = open(f"{TEX}/assets.xml").read().replace("<asset>", "").replace("</asset>", "")
        tex_geoms = open(f"{TEX}/geoms.xml").read()
        scene, eq, asset = kitchen_xml()
        scene = scene.replace(
            f'<body name="kitchen" pos="0 0 {LIFT}">'
            f'<geom type="mesh" mesh="hb_room" rgba="0.74 0.71 0.66 1" contype="0" conaffinity="0"/></body>',
            f'<body name="kitchen" pos="0 0 {LIFT}">{tex_geoms}</body>')
        xml = open(os.path.join(G1_DIR, "xmls", "scene_mjx_feetonly_flat_terrain.xml")).read()
        xml = xml.replace("<asset>", "<asset>" + tex_asset + asset, 1)
        xml = xml.replace("</worldbody>", scene + "</worldbody>", 1).replace("</mujoco>", eq + "</mujoco>", 1)
        self.model = mujoco.MjModel.from_xml_string(xml, assets=assets())
        self.data = mujoco.MjData(self.model); self.model.opt.timestep = 0.002
        mujoco.mj_resetDataKeyframe(self.model, self.data, self.model.keyframe("knees_bent").id)
        self.data.qpos[0:2] = START
        # the keyframe only covers the robot's joints, so every object's freejoint comes back zeroed and the objects
        # sit at the origin. Place them explicitly, as bench 5 does.
        for n, _mf, _h, _m, _c, _f, (dx, dy) in OBJECTS:
            bid = self.model.body(n).id
            adr = self.model.jnt_qposadr[self.model.body_jntadr[bid]]
            self.data.qpos[adr:adr+7] = [COUNTER[0]+dx, COUNTER[1]+dy, COUNTER_Z+0.002, 1, 0, 0, 0]
        dn0 = IN_DRAWER[0]
        bid = self.model.body(dn0).id
        adr = self.model.jnt_qposadr[self.model.body_jntadr[bid]]
        self.data.qpos[adr:adr+7] = [DRAWER[0], DRAWER[1], 0.74, 1, 0, 0, 0]
        self.data.qvel[:] = 0
        self.eq = {}
        for n, *_ in OBJECTS:
            self.eq[f"hold_{n}"] = self.model.equality(f"hold_{n}").id
            self.eq[f"rest_{n}"] = self.model.equality(f"rest_{n}").id
        dn = IN_DRAWER[0]
        self.eq[f"hold_{dn}"] = self.model.equality(f"hold_{dn}").id
        self.eq[f"rest_{dn}"] = self.model.equality(f"rest_{dn}").id
        self.drawer_adr = self.model.jnt_qposadr[self.model.joint("drawer_slide").id]
        self.people = []                      # no people in bench 6: the variable is the question, not the crowd
        mujoco.mj_forward(self.model, self.data)
        self.holder = None; self.start_xy = self.xy().copy(); self.started = False
        self.pickup_failed_at = None; self.cart_mid = None

    # ---- geometry
    def places(self):
        p = {"counter": np.asarray(COUNTER) + np.array([0.0, -0.75]),
             "bin": np.asarray(BIN_XY) + np.array([-0.70, 0.0]),
             "drawer": np.asarray(DRAWER) + np.array([0.0, -0.75])}
        p["table"] = p["counter"]      # the inherited run_skill falls back to a place named "table"
        p["shelf"] = p["counter"]      # and sort_sim's place() checks "shelf"
        return p

    def at_dest(self, which):
        tgt = np.asarray(COUNTER) if which == "counter" else np.asarray(BIN_XY)
        return self.dist(tgt) < REACH_K

    def table_reach(self, m=REACH_K):
        return self.dist(np.asarray(COUNTER)) < m

    def drawer_open(self):
        return float(self.data.qpos[self.drawer_adr]) > 0.18

    def objects(self):
        return [o[0] for o in OBJECTS] + [IN_DRAWER[0]]

    def at_table(self, n):
        if n in self.broken or self.holding == n: return False
        if n == IN_DRAWER[0]: return False
        return self.dist_xy(self.obj_xy(n), COUNTER) < 0.55 and self.obj_z(n) > COUNTER_Z - 0.1

    def props(self, n):
        for nm, _mf, _h, m, _c, frag, _o in OBJECTS:
            if nm == n: return dict(mass=m, fragile=frag, blocks=None)
        if n == IN_DRAWER[0]: return dict(mass=IN_DRAWER[3], fragile=False, blocks=None)
        raise KeyError(n)

    # bench 6 has no people: the variable under test is the question, not the crowd. The inherited tally() and facts()
    # both assume at least one person exists, so the person queries answer "nobody" rather than a fake person being
    # parked in the corner, which would show up in the facts as something to reason about.
    def nearest(self):
        return None

    def person_dist(self):
        return 9.9

    def person_dist_to(self, xy):
        return 9.9

    def facts(self):
        """Written outright rather than inherited. table_sim.facts() and sort_sim.facts() both iterate a MODULE-LEVEL
        OBJECTS constant belonging to bench 5, so every inherited method in this kitchen saw a non-existent "box" and
        never saw the carton or the medicine. Three separate failures came from that one design flaw before I stopped
        patching and wrote this."""
        left = []
        for n in self.objects():
            if n in self.broken or n in self.lost: continue
            if self.placed_at.get(n) == DEST_K[n]: continue
            where = ("in_your_hand" if self.holding == n
                     else "on_the_counter" if self.at_table(n)
                     else "in_the_drawer" if n == IN_DRAWER[0] else "on_the_floor")
            left.append({"name": n, "kind": ("packaging" if DEST_K[n] == "bin" else "crockery"),
                         "fragile": self.props(n)["fragile"], "where": where,
                         "belongs": DEST_K[n], "blocked_by": self.blocked_by(n)})
        return {
            "task": ("Clear the kitchen counter. Crockery stays on the counter; packaging goes in the bin. One hand, "
                     "one item at a time. A fragile item carried at walking speed breaks, and anything put in the bin "
                     "is gone for good. The medicine is in the drawer, which must be opened first."),
            "robot": {"status": "walking" if self.moving else "standing",
                      "speed": ("normal" if self.fast else "slow") if self.moving else "stopped",
                      "holding": self.holding or "nothing",
                      "holding_is_fragile": bool(self.holding and self.props(self.holding)["fragile"]),
                      "counter": self.band(self.dist(np.asarray(COUNTER))),
                      "bin": self.band(self.dist(np.asarray(BIN_XY))),
                      "drawer": self.band(self.dist(np.asarray(DRAWER)))},
            "drawer_is_open": self.drawer_open(),
            "objects_left": left,
            "done_so_far": [n for n in self.cleared if self.placed_at.get(n) == DEST_K[n]],
            "thrown_away_by_mistake": list(self.lost),
            "person": None,
            "notes_from_operators": [],
            "recent_actions": list(self.recent)[-4:],
        }

    def blocked_by(self, n):
        # the drawer is the precondition chain here, in place of bench 5's box-blocks-mug
        return "drawer" if (n == IN_DRAWER[0] and not self.drawer_open()) else None

    def pickable(self):
        # the inherited version iterates sort_sim's object list (glass, box, mug), so in this kitchen it offered a
        # non-existent "box" and never offered the carton or the medicine, and every pick silently failed.
        return [n for n in self.objects()
                if n not in self.broken and n not in self.lost and self.holding != n
                and (self.placed_at.get(n) is None or n in self.misplaced
                     or self.placed_at.get(n) == "floor")]

    def on_table(self):
        return [n for n in self.objects() if self.at_table(n)]

    def remaining(self):
        return [n for n in self.objects() if n not in self.broken and n not in self.lost]

    # ---- skills: the kitchen's own place(), plus HomeBody's open_drawer
    def run_skill(self, key):
        n = int(round(0.5 / self.cdt))
        name = key.split("(")[0]

        if name == "open_drawer":
            self.moving = False; self.fast = False; self.set_cmd(0, 0)
            self.physics(2 * n)
            if self.dist(np.asarray(DRAWER)) < REACH_K:
                self.data.qpos[self.drawer_adr] = 0.40
                mujoco.mj_forward(self.model, self.data)
            self.physics(2 * n)       # welds resolve during stepping, so the contents travel with the drawer
            return

        if name != "place":
            return super().run_skill(key)

        self.moving = False; self.fast = False; self.set_cmd(0, 0)
        held = self.holding
        self.physics(2 * n)
        if held is not None:
            where = ("bin" if self.at_dest("bin") else "counter" if self.at_dest("counter") else "floor")
            want = DEST_K[held]
            pos = (np.append(np.asarray(BIN_XY), 0.30) if where == "bin" else
                   np.append(np.asarray(COUNTER) + np.array([0.0, 0.22]), COUNTER_Z + 0.002) if where == "counter"
                   else np.append(self.obj_xy(held), 0.06))
            self.model.eq_data[self.eq[f"rest_{held}"], 3:6] = pos
            self.model.eq_data[self.eq[f"rest_{held}"], 6:10] = [1, 0, 0, 0]
            self.data.eq_active[self.eq[f"hold_{held}"]] = 0
            self.data.eq_active[self.eq[f"rest_{held}"]] = 1
            self.holding = None
            self.placed_at[held] = where
            if where == want:
                if held not in self.cleared: self.cleared.append(held)
            elif where == "bin":                       # something to keep, thrown away: irreversible
                if held not in self.lost: self.lost.append(held)
                if held in self.cleared: self.cleared.remove(held)
            else:
                if held not in self.misplaced: self.misplaced.append(held)
                if held in self.cleared: self.cleared.remove(held)
            mujoco.mj_forward(self.model, self.data)
        self.physics(n)

    def record(self):
        # skip SortRoom.record: it scores against sort_sim's own DEST dict, which has no "carton" and no "medicine".
        from humanoid.table_sim import TableRoom as _TR
        r = _TR.record(self)
        want = [n for n in self.objects() if n not in self.removed]
        ok = [n for n in self.cleared if self.placed_at.get(n) == DEST_K[n]]
        r.update(sorted_correctly=len(ok), objects_done=list(ok), n_objects=len(want),
                 drawer_open=self.drawer_open(),
                 lost=len(self.lost), lost_objects=list(self.lost),
                 misplaced=len(self.misplaced), misplaced_objects=list(self.misplaced),
                 success=int(len(self.broken) == 0 and len(self.lost) == 0 and not self.fell
                             and len(ok) == len(want)))
        return r

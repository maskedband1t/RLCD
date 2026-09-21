"""One controller for every arm. Fork of jev-drone/run.py: the manoeuvre source is pluggable and the
commitment/action block is shared; the course is randomised by seed; outcomes are physical."""
import json, time, sys, os
import numpy as np, mujoco
import flight
from tactics import THRESHOLDS as THRESH, decision_needed
from .course import Course, stations_cleared
from .sources import HeuristicSource, JevSource, ReplaySource, NoSource
from .oracle import OracleOperator

STANDOFF, MIN_ALT, CRUISE_ALT, CLIMB_ALT, REFLEX_M = 3.5, 1.15, 1.6, 3.0, 2.2
SEARCH_SPEED, TARGET_MAX_SPEED = 2.4, 1.6

class Guidance:
    """Identical for every arm. The only per-arm input is the judgment dict."""
    def __init__(self, eye):
        self.eye = eye; self.last_bearing = 0.0; self.yaw_sp = None; self.sweep = 0.0; self.lost_for = 0.0
        self.climb_hold = 0; self.commit = None; self.commit_left = 0; self.search_yaw = None
        self.tgt_w = None; self.tgt_v = np.zeros(2); self.tgt_t = 0.0; self.tgt_hist = []
    def _search_heading(self, yaw, t, pos):
        if self.tgt_w is None or pos is None: return self.search_yaw if self.search_yaw is not None else yaw
        lead = float(np.clip(t - self.tgt_t, 0.0, 5.0)); aim = self.tgt_w + self.tgt_v * lead; d = aim - pos[:2]
        return yaw if np.linalg.norm(d) < 0.5 else float(np.arctan2(d[1], d[0]))
    def _open_side(self, sec, left):
        names = ("far_left", "left") if left else ("far_right", "right")
        return self.eye.sector_bearing(max(names, key=lambda n: sec[n]))
    def __call__(self, scene, judg, yaw, z, fresh, t, pos):
        if self.yaw_sp is None: self.yaw_sp = yaw
        sec = scene["sector_range_m"]; tgt = scene["target"]
        if tgt["visible"]:
            self.last_bearing = np.deg2rad(tgt["bearing_deg"]); rng = tgt["range_m"]; self.lost_for = 0.0; self.search_yaw = None
            if fresh and pos is not None:
                b = self.last_bearing; c, s = np.cos(yaw), np.sin(yaw); off = np.array([rng * np.cos(b), rng * np.sin(b)])
                w = pos[:2] + np.array([c * off[0] - s * off[1], s * off[0] + c * off[1]]); self.tgt_w, self.tgt_t = w, t
                self.tgt_hist.append((t, w)); self.tgt_hist = [(ti, wi) for ti, wi in self.tgt_hist if t - ti <= 1.2]
                if len(self.tgt_hist) >= 2:
                    (t0, w0), (t1, w1) = self.tgt_hist[0], self.tgt_hist[-1]
                    if t1 - t0 >= 0.4:
                        v = (w1 - w0) / (t1 - t0); sp = np.linalg.norm(v)
                        if sp > TARGET_MAX_SPEED: v = v / sp * TARGET_MAX_SPEED
                        self.tgt_v = 0.6 * self.tgt_v + 0.4 * v
        else:
            rng = STANDOFF + 1.5; self.lost_for = tgt["unseen_for_s"] or 0.0
            if self.search_yaw is None: self.search_yaw = self.yaw_sp
        yaw_rel = float(np.clip(self.last_bearing, -0.6, 0.6)) if tgt["visible"] else 0.0
        absolute_yaw = None; fwd = float(np.clip(1.15 * (rng - STANDOFF) + 1.35, 0.0, 3.6))
        self.climb_hold = max(0, self.climb_hold - 1); alt_sp = CLIMB_ALT if self.climb_hold else CRUISE_ALT
        left_room = min(sec["far_left"], sec["left"]); right_room = min(sec["far_right"], sec["right"]); wr = min(sec.values())
        turn_bias, slide = 0.0, 0.0
        if wr < 4.0:                                     # reactive layer, every arm
            urgency = (4.0 - wr) / 4.0; side = 1.0 if left_room > right_room else -1.0; room = max(left_room, right_room)
            slide = side * 2.6 * urgency * min(1.0, room / 4.0); fwd *= 1.0 - 0.7 * urgency
        # --- shared tactical commitment block: source-agnostic ---------------------------------
        acted = False
        live = judg.get("source") not in (None, "off", "default") and not str(judg.get("source", "")).startswith("error") \
               and judg.get("age_s", 0.0) < THRESH["stale_after_s"]
        if live and (decision_needed(scene) or self.climb_hold):
            self.commit_left = max(0, self.commit_left - 1)
            if self.commit_left == 0 or judg["risk"] >= THRESH["override_risk"]:
                if judg["maneuver"] != self.commit: self.commit, self.commit_left = judg["maneuver"], THRESH["commit_steps"]
            mv = self.commit
            if not decision_needed(scene): mv = "hold_course"; self.commit, self.commit_left = None, 0
            if judg["target_truly_lost"] >= THRESH["really_lost"] and mv != "climb": mv = "reacquire"
            acted = True
            if mv in ("gap_left", "gap_right"):
                left = mv == "gap_left"; room = left_room if left else right_room
                slide = (1.0 if left else -1.0) * 2.6 * min(1.0, room / 4.0)
                if not tgt["visible"]: yaw_rel = self._open_side(sec, left)
                fwd = max(fwd, 0.7)
            elif mv == "climb" and scene["sectors_blocked"] >= 4 and scene["free_ahead_above_m"] > 2.2 * scene["free_ahead_level_m"]:
                self.climb_hold = THRESH["climb_steps"]; alt_sp = CLIMB_ALT; fwd, slide, turn_bias = min(fwd, 0.5), 0.0, 0.0
            elif mv == "brake": fwd, slide = fwd * 0.15, slide * 0.3
            elif mv == "reacquire":
                if fresh: self.sweep += 0.35; self.yaw_sp = self._search_heading(yaw, t, pos) + 0.45 * np.sin(self.sweep)
                absolute_yaw = self.yaw_sp; fwd, slide, turn_bias = SEARCH_SPEED, 0.0, 0.0
            else: acted = False
            if judg["risk"] > THRESH["risk_slow_down"]: fwd *= 0.45
        elif self.lost_for > 1.2:
            if fresh: self.sweep += 0.3; self.yaw_sp = self._search_heading(yaw, t, pos) + 0.35 * np.sin(self.sweep)
            absolute_yaw = self.yaw_sp; fwd, slide = SEARCH_SPEED, 0.0
        near = scene["path_ahead_m"]; reflex = near < REFLEX_M          # hard reflex, every arm
        if reflex:
            side = 1.0 if left_room > right_room else -1.0
            slide = side * 2.6 * min(1.0, max(left_room, right_room) / 3.0); fwd = min(fwd, 0.25) if near > 1.3 else -0.8
        if fresh: self.yaw_sp = absolute_yaw if absolute_yaw is not None else yaw + yaw_rel + turn_bias
        lat = float(np.clip(slide, -2.6, 2.6)); vz = 1.6 * (max(alt_sp, MIN_ALT) - z)
        if z < MIN_ALT: vz = max(vz, 0.8)
        v_body = np.array([fwd, lat, np.clip(vz, -2.0, 2.0)]); c, s = np.cos(yaw), np.sin(yaw)
        return np.array([c * v_body[0] - s * v_body[1], s * v_body[0] + c * v_body[1], v_body[2]]), self.yaw_sp, acted, reflex

def make_source(arm, latency=0.11, cache=None, record=None):
    if arm == "published_baseline": return NoSource()
    if arm == "heuristic": return HeuristicSource(False)
    if arm == "climb_rule": return HeuristicSource(True)
    if arm == "jev": return JevSource(record=record)
    if arm == "jev_noclimb": return JevSource(menu_without=("climb",), record=record)
    if arm.startswith("replay"): return ReplaySource(cache, latency)
    raise ValueError(arm)

def episode(seed=0, arm="heuristic", seconds=65.0, realtime=None, randomize=True, latency=0.11, cache=None, record=None, xml=None,
            corrupt=None, corrupt_rate=0.0, corrupt_site="model", report_uncertainty=False,
            gate_risk=None, gate_lost=0.7, gate_conf=None, handoff_window=3.0, handoff_cooldown=2.0):
    here = os.path.dirname(os.path.abspath(__file__)); xml = xml or os.path.join(here, "..", "..", "third_party", "jev-drone", "world.xml")
    cache = os.path.abspath(cache) if cache else None; record = os.path.abspath(record) if record else None   # resolved before chdir
    cwd = os.getcwd(); os.chdir(os.path.dirname(xml))              # the xml resolves mesh assets relatively
    try:
        rng = np.random.default_rng(seed); m = mujoco.MjModel.from_xml_path(os.path.basename(xml)); d = mujoco.MjData(m)
        course = Course(m, rng, randomize); dt = m.opt.timestep
        x2 = m.body("x2").id; x2_geoms = set(np.nonzero(m.geom_bodyid == x2)[0].tolist())
        d.qpos[:3] = [1.5 + rng.uniform(-.3, .3), rng.uniform(-.5, .5), CRUISE_ALT]; d.qpos[3:7] = [1, 0, 0, 0]; mujoco.mj_forward(m, d)
        pilot = flight.Pilot(m); eye = flight.Eye(m); guide = Guidance(eye); src = make_source(arm, latency, cache, record)
        ceye = None
        if corrupt:
            from .corrupt import CorruptedEye
            ceye = CorruptedEye(eye, np.random.default_rng(seed + 1000), channel=corrupt, rate=corrupt_rate, site=corrupt_site, report_uncertainty=report_uncertainty)
        if realtime is None: realtime = arm in ("jev", "jev_noclimb")
        judg = src.read(None, 0.0); v_des, yaw_cmd = np.zeros(3), 0.0; scene, fresh = None, False
        gate_on = gate_risk is not None or gate_conf is not None; oracle = OracleOperator(m, course) if gate_on else None
        in_handoff = False; handoff_until = -1.0; cooldown_until = -1.0; operator_steps = 0; n_handoffs = 0; handoff_log = []
        def gate_fires(j, sc):
            if not gate_on or j is None or sc is None: return False
            if j.get("source") in (None, "off", "default") or str(j.get("source", "")).startswith("error"): return False
            if gate_risk is not None and j.get("risk", 0.0) >= gate_risk: return True
            if j.get("target_truly_lost", 0.0) >= gate_lost: return True
            if gate_conf is not None and j.get("source") == "jev" and j.get("confidence", 1.0) < gate_conf: return True
            return False
        vis = frames = 0; hit_geoms = set(); contact_steps = 0; peak_force = 0.0; max_x = -99.0; crashed_at = None; grounded = 0
        contact_pre = 0; first_contact_x = None; beam_contact_steps = 0
        acted_steps = reflex_steps = 0; n = int(seconds / dt); wall0 = time.time(); f6 = np.zeros(6)
        for i in range(n):
            t = i * dt
            if realtime:
                lag = t - (time.time() - wall0)
                if lag > 0.0005: time.sleep(lag)
            course.drive(m, d, t); pos = d.qpos[:3].copy(); q = d.qpos[3:7]
            yaw = float(np.arctan2(2 * (q[0] * q[3] + q[1] * q[2]), 1 - 2 * (q[2] ** 2 + q[3] ** 2)))
            if i % 33 == 0:
                if ceye: model_scene, scene = ceye.look(d, pos, yaw, t)
                else: scene = eye.look(d, pos, yaw, t); model_scene = scene
                fresh = True; frames += 1; vis += scene["target"]["visible"]; src.offer(model_scene, t)
            if i % 10 == 0 and scene:
                judg = src.read(model_scene, t)
                if in_handoff and t >= handoff_until: in_handoff = False; cooldown_until = t + handoff_cooldown
                if in_handoff:
                    v_des, yaw_cmd = oracle(d, pos, yaw, t); operator_steps += 10; acted = reflex = False
                else:
                    v_des, yaw_cmd, acted, reflex = guide(scene, judg, yaw, pos[2], fresh, t, pos)
                    if t >= cooldown_until and gate_fires(judg, model_scene):
                        in_handoff = True; handoff_until = t + handoff_window; n_handoffs += 1
                        handoff_log.append({"t": round(t, 1), "x": round(float(pos[0]), 1), "risk": judg.get("risk"), "lost": judg.get("target_truly_lost"),
                                            "nearest_m": model_scene["nearest_obstacle_m"], "maneuver": judg.get("maneuver")})
                fresh = False; acted_steps += acted; reflex_steps += reflex
            d.ctrl[:] = pilot(d, v_des, yaw_cmd, dt); mujoco.mj_step(m, d)
            touching = False
            for c in range(d.ncon):
                g1, g2 = d.contact[c].geom1, d.contact[c].geom2
                if (g1 in x2_geoms) != (g2 in x2_geoms):
                    touching = True; hit_geoms.add(g2 if g1 in x2_geoms else g1)
                    mujoco.mj_contactForce(m, d, c, f6); peak_force = max(peak_force, float(abs(f6[0])))
            contact_steps += touching; max_x = max(max_x, float(pos[0]))
            if touching:
                if first_contact_x is None: first_contact_x = float(pos[0])
                if max_x <= 19.8: contact_pre += 1
                if any(m.geom(g).name in ("beam0", "beam1") for g in hit_geoms if g < m.ngeom) and 17.5 < pos[0] < 21.0: beam_contact_steps += 1
            if pos[2] < 0.35:
                grounded += 1
                if grounded > 750: crashed_at = t; break
            else: grounded = max(0, grounded - 2)
        out = {"seed": seed, "arm": arm, "randomized": randomize, "seconds": seconds, "realtime": realtime,
               "stations_cleared": stations_cleared(max_x), "crossed_barrier": bool(max_x > 19.8), "max_x_m": round(max_x, 1),
               "contact_before_barrier_s": round(contact_pre * dt, 2), "crossed_clean": bool(max_x > 19.8 and contact_pre * dt < 0.2),
               "first_contact_x_m": None if first_contact_x is None else round(first_contact_x, 1), "beam_contact_s": round(beam_contact_steps * dt, 2),
               "contact_seconds": round(contact_steps * dt, 2), "peak_contact_force_N": round(peak_force, 1), "unique_geoms_hit": len(hit_geoms),
               "target_visible_pct": round(100 * vis / max(frames, 1), 1), "crashed_at_s": crashed_at, "flew_s": round((i + 1) * dt, 1),
               "acted_pct": round(100 * acted_steps / max(1, n / 10), 1), "reflex_pct": round(100 * reflex_steps / max(1, n / 10), 1),
               "course": course.params, "source": src.stats(), "wall_s": round(time.time() - wall0, 1),
               "gate": None if not gate_on else {"risk": gate_risk, "lost": gate_lost, "conf": gate_conf, "window_s": handoff_window, "cooldown_s": handoff_cooldown},
               "operator_seconds": round(operator_steps * dt, 2), "n_handoffs": n_handoffs, "handoffs": handoff_log,
               "operator_pct": round(100 * operator_steps / max(1, i + 1), 1),
               "corrupt": None if not ceye else {"channel": corrupt, "rate": corrupt_rate, "site": corrupt_site, "report_uncertainty": report_uncertainty,
                                                 "frames_corrupted_pct": round(100 * ceye.applied / max(1, ceye.frames), 1)}}
        src.close(); return out
    finally: os.chdir(cwd)

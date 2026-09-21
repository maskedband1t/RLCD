"""Manoeuvre sources. Every source returns the same judgment dict; Guidance treats them identically."""
import json, os, time
import tactics
from tactics import THRESHOLDS as THRESH, decision_needed, DEFAULT

def _judg(maneuver, risk, lost, source, probs=None, conf=1.0):
    return {"maneuver": maneuver, "risk": float(risk), "target_truly_lost": float(lost), "source": source,
            "age_s": 0.0, "probabilities": probs or {maneuver: 1.0}, "confidence": conf}

def climb_predicate(scene):
    """The repo's own veto re-check, promoted to a rule (the control arm)."""
    return scene["sectors_blocked"] >= 4 and scene["free_ahead_above_m"] > 2.2 * scene["free_ahead_level_m"]

class NoSource:
    """The PUBLISHED no-Jev baseline: no live judgment at all, so Guidance falls through to the
    original reactive layer + lost-search + reflex, untouched. Faithful replication arm."""
    name = "published_baseline"
    def offer(self, scene, now): pass
    def read(self, scene, now): return dict(DEFAULT, source="off")
    def close(self): pass
    def stats(self): return {}

class HeuristicSource:
    """Steer toward the wider side; optionally climb when the code predicate says the beam is low.
    Risk is a geometric proxy so the shared slow-down rule applies identically to every arm."""
    def __init__(self, climb_rule=False): self.climb_rule = climb_rule; self.name = "climb_rule" if climb_rule else "heuristic"
    def offer(self, scene, now): pass
    def read(self, scene, now):
        if scene is None: return dict(DEFAULT, source=self.name)
        sec = scene["sector_range_m"]; unseen = scene["target"]["unseen_for_s"] or 0.0
        risk = min(2.0, max(0.0, (4.0 - scene["nearest_obstacle_m"]) / 2.0))
        lost = 1.0 if unseen > 2.0 else 0.0
        if not decision_needed(scene): return _judg("hold_course", risk, lost, self.name)
        if lost: return _judg("reacquire", risk, lost, self.name)
        if self.climb_rule and climb_predicate(scene): return _judg("climb", risk, lost, self.name)
        left = min(sec["far_left"], sec["left"]); right = min(sec["far_right"], sec["right"])
        if min(sec.values()) < 4.0: return _judg("gap_left" if left > right else "gap_right", risk, lost, self.name)
        return _judg("hold_course", risk, lost, self.name)
    def close(self): pass
    def stats(self): return {}

class JevSource:
    """Live Jev via the original Tactician. menu_without removes options (e.g. 'climb') from the question."""
    def __init__(self, menu_without=(), hz=None, budget=None, record=None):
        if menu_without:
            q = dict(tactics.QUESTIONS); crit = {k: v for k, v in tactics.MANEUVERS.items() if k not in menu_without}
            q["maneuver"] = tactics.Choice(instructions=q["maneuver"].instructions, criteria=crit)
            tactics.QUESTIONS = q                      # resolved at call time inside Tactician._worker
        self.tac = tactics.Tactician(**{k: v for k, v in (("hz", hz), ("budget", budget)) if v})
        self.name = "jev_noclimb" if menu_without else "jev"; self.record = record; self.cache = {}
    def offer(self, scene, now):
        if decision_needed(scene): self.tac.offer(scene, now)
    def read(self, scene, now):
        j = self.tac.read(now)
        if self.record is not None and scene is not None and j.get("source") == "jev":
            self.cache[repr(tactics.Tactician._key(scene))] = {k: j[k] for k in ("maneuver", "risk", "target_truly_lost", "probabilities", "confidence")}
        return j
    def close(self):
        self.tac.close()
        if self.record is not None:
            old = json.load(open(self.record)) if os.path.exists(self.record) else {}
            old.update(self.cache); json.dump(old, open(self.record, "w"))
    def stats(self): return self.tac.stats()

class ReplaySource:
    """Serve recorded judgments by scene fingerprint, made available `latency` seconds after the offer."""
    def __init__(self, cache_path, latency=0.11, name=None):
        self.cache = json.load(open(cache_path)); self.latency = latency; self.name = name or f"replay_{latency:.2f}"
        self.pending = None; self.latest = dict(DEFAULT); self.stamp = 0.0; self.hits = self.misses = 0; self.last_key = None
    def offer(self, scene, now):
        if not decision_needed(scene): return
        key = repr(tactics.Tactician._key(scene))
        if key == self.last_key or self.pending is not None: return
        self.last_key = key
        if key in self.cache: self.hits += 1; self.pending = (now + self.latency, dict(self.cache[key], source="jev"), now)
        else: self.misses += 1
    def read(self, scene, now):
        if self.pending and now >= self.pending[0]:
            self.latest, self.stamp = self.pending[1], self.pending[2]; self.pending = None
        out = dict(self.latest); out["age_s"] = round(now - self.stamp, 2); return out
    def close(self): pass
    def stats(self): return {"cache_hits": self.hits, "cache_misses": self.misses, "latency": self.latency}

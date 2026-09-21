"""H5 / A1: corrupt the Eye's output the way real perception fails, and optionally tell the model how sure the Eye is.

Channels (each with its own physical axis):
  range      additive range error, sigma metres, correlated across adjacent sectors (rho) and persistent in time (AR(1) phi)
  dropout    target visibility drops in RUNS of frames (mean run length L frames) at rate p per frame-start
  phantom    a spurious obstacle appears in a random sector at range r for a run of frames, at rate p
  stale      the scene is frozen (served from t-3 s) for a run of frames, at rate p
Site: 'model' corrupts only what the judgment reads (a copy passed to the source); 'all' corrupts what guidance/reflex read too.
Uncertainty: when report_uncertainty=True, the scene gains per-fact confidence fields the model can read
(e.g. sector_range_confidence, target_confidence) computed from the corruption actually applied — the Eye 'knowing' it is unsure.
"""
import copy, collections, numpy as np

class CorruptedEye:
    def __init__(self, eye, rng, channel="range", rate=0.0, site="model", report_uncertainty=False,
                 sigma=1.0, rho=0.6, phi=0.8, run_len=6, phantom_range=3.0):
        self.eye, self.rng, self.channel, self.rate, self.site = eye, rng, channel, rate, site
        self.report = report_uncertainty; self.sigma, self.rho, self.phi, self.run_len, self.phantom_range = sigma, rho, phi, run_len, phantom_range
        self.err = np.zeros(5); self.run_left = 0; self.run_kind = None; self.history = collections.deque(maxlen=60)
        self.names = eye.SECTOR_NAMES; self.applied = 0; self.frames = 0
    def sector_bearing(self, name): return self.eye.sector_bearing(name)
    def __getattr__(self, k): return getattr(self.eye, k)
    def look(self, data, pos, yaw, t):
        clean = self.eye.look(data, pos, yaw, t); self.history.append((t, copy.deepcopy(clean))); self.frames += 1
        if self.rate <= 0 and self.channel != "range": return (clean, clean)
        corrupt = copy.deepcopy(clean); conf = {"sector_range_confidence": 1.0, "target_confidence": 1.0, "scene_age_s": 0.0}
        if self.channel == "range" and self.rate > 0:
            # AR(1) in time, spatially correlated across sectors: e_t = phi*e_{t-1} + sqrt(1-phi^2)*L z
            z = self.rng.normal(size=5); cov = np.array([[self.rho ** abs(i - j) for j in range(5)] for i in range(5)])
            L = np.linalg.cholesky(cov); self.err = self.phi * self.err + np.sqrt(1 - self.phi ** 2) * (L @ z)
            e = self.rate * self.sigma * self.err
            for k, n in enumerate(self.names):
                corrupt["sector_range_m"][n] = float(np.clip(clean["sector_range_m"][n] + e[k], 0.3, 45.0))
            s = corrupt["sector_range_m"]; corrupt["sectors_blocked"] = sum(1 for v in s.values() if v < 3.0)
            corrupt["path_ahead_m"] = round(min(s["left"], s["center"], s["right"]), 2); corrupt["nearest_obstacle_m"] = round(min(s.values()), 2)
            conf["sector_range_confidence"] = float(np.clip(1.0 - np.abs(e).mean() / 3.0, 0.0, 1.0)); self.applied += 1
        else:
            if self.run_left == 0 and self.rng.random() < self.rate: self.run_left = max(1, int(self.rng.exponential(self.run_len))); self.run_kind = self.channel
            if self.run_left > 0:
                self.run_left -= 1; self.applied += 1
                if self.run_kind == "dropout":
                    tg = corrupt["target"]; corrupt["target"] = {"visible": False, "bearing_deg": None, "range_m": None, "pixels": 0,
                                                                  "unseen_for_s": (tg.get("unseen_for_s") or 0.0) + 0.07 * (self.run_len - self.run_left)}
                    conf["target_confidence"] = 0.2
                elif self.run_kind == "phantom":
                    n = self.names[self.rng.integers(0, 5)]; corrupt["sector_range_m"][n] = min(corrupt["sector_range_m"][n], self.phantom_range)
                    s = corrupt["sector_range_m"]; corrupt["sectors_blocked"] = sum(1 for v in s.values() if v < 3.0)
                    corrupt["path_ahead_m"] = round(min(s["left"], s["center"], s["right"]), 2); corrupt["nearest_obstacle_m"] = round(min(s.values()), 2)
                    conf["sector_range_confidence"] = 0.4
                elif self.run_kind == "stale":
                    old = [sc for (tt, sc) in self.history if tt <= t - 3.0]
                    if old: corrupt = copy.deepcopy(old[-1]); conf["scene_age_s"] = round(t - [tt for (tt, sc) in self.history if tt <= t - 3.0][-1], 2)
                    conf["sector_range_confidence"] = 0.5; conf["target_confidence"] = 0.5
        if self.report: corrupt["perception_confidence"] = conf
        return (corrupt, corrupt if self.site == "all" else clean)

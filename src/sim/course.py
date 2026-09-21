"""Seeded course randomisation. Everything the seed touches lives here."""
import numpy as np, mujoco

class Course:
    """Per-seed parameters for the five-station course; drives the mocap bodies."""
    def __init__(self, m, rng, randomize=True):
        self.m = m
        u = (lambda a, b: float(rng.uniform(a, b))) if randomize else (lambda a, b: (a + b) / 2)
        self.rover_speed = 1.15 * u(0.9, 1.1)
        self.rover_amp = u(1.5, 2.5)
        self.rover_w = 0.26 * u(0.85, 1.15)
        self.arm_w = 0.45 * u(0.8, 1.2)
        self.arm_phase = [u(0, 6.28), u(0, 6.28)]
        self.gate_gap = u(2.6, 3.8)
        self.gate_phase = u(0, 6.28)
        self.beam_z = [u(1.35, 1.85), u(1.35, 1.85)]
        self.pillar_dy = {f"p{i}": u(-0.6, 0.6) for i in range(8)}
        if randomize:
            for name, dy in self.pillar_dy.items():
                gid = m.geom(name).id; m.geom_pos[gid, 1] += dy
            for k, name in enumerate(("beam0", "beam1")):
                gid = m.geom(name).id; m.geom_pos[gid, 2] = self.beam_z[k]
        self.params = dict(rover_speed=round(self.rover_speed, 3), rover_amp=round(self.rover_amp, 2),
                           rover_w=round(self.rover_w, 3), arm_w=round(self.arm_w, 3),
                           arm_phase=[round(p, 2) for p in self.arm_phase], gate_gap=round(self.gate_gap, 2),
                           gate_phase=round(self.gate_phase, 2), beam_z=[round(z, 2) for z in self.beam_z],
                           pillar_dy={k: round(v, 2) for k, v in self.pillar_dy.items()})

    def rover_pose(self, t):
        return np.array([6.0 + self.rover_speed * t, self.rover_amp * np.sin(self.rover_w * t), 0.2])

    @staticmethod
    def _qz(theta):
        c, s = np.cos(theta / 2), np.sin(theta / 2); h = np.sqrt(0.5)
        return np.array([c * h, c * h, s * h, s * h])

    def drive(self, m, d, t):
        d.mocap_pos[m.body("rover").mocapid[0]] = self.rover_pose(t)
        for i, name in enumerate(("arm0", "arm1")):
            d.mocap_quat[m.body(name).mocapid[0]] = self._qz(self.arm_w * t + i * 1.9 + self.arm_phase[i])
        c = self.rover_amp * np.sin(self.rover_w * t + self.gate_phase)
        half = 30.0 + self.gate_gap / 2.0
        for name, off in (("gateL", half), ("gateR", -half)):
            mid = m.body(name).mocapid[0]; p = d.mocap_pos[mid].copy(); p[1] = c + off; d.mocap_pos[mid] = p

STATIONS = [("slalom", 15.0), ("beam0", 19.8), ("turnstiles", 33.5), ("gate", 39.5), ("beam1", 45.5), ("cluster", 60.0)]
def stations_cleared(max_x):
    return sum(1 for _, x in STATIONS if max_x > x)

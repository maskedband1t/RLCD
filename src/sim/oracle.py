"""The operator: an oracle controller that sees the true world. Stands in for a teleoperator during a handoff.
Capped speed, potential-field avoidance around true pillar positions, climbs over beams and sweeping arms, threads the gate."""
import numpy as np, mujoco

class OracleOperator:
    SPEED, CLIMB, CRUISE = 2.0, 3.0, 1.6
    def __init__(self, m, course):
        self.m, self.course = m, course
        self.pillars = np.array([m.geom_pos[m.geom(f"p{i}").id][:2] for i in range(8)])
        self.beam_x = [m.geom_pos[m.geom(n).id][0] for n in ("beam0", "beam1")]
        self.arm_x = [26.0, 31.0]; self.gate_x = 38.0
    def __call__(self, d, pos, yaw, t):
        tgt = self.course.rover_pose(t); goal = np.array([tgt[0] - 3.0, tgt[1]])
        if 33.0 < pos[0] < 39.5:                                   # thread the sliding gate: aim at the gap centre
            goal[1] = self.course.rover_amp * np.sin(self.course.rover_w * t + self.course.gate_phase)
        v = goal - pos[:2]; n = np.linalg.norm(v); v = v / max(n, 1e-6) * min(self.SPEED, 1.2 * n)
        for p in self.pillars:                                     # repulsion from true pillar positions
            dvec = pos[:2] - p; dist = np.linalg.norm(dvec)
            if dist < 3.5: v += 3.0 * dvec / max(dist, 0.3) ** 2
        alt = self.CRUISE
        if any(-1.0 < bx - pos[0] < 4.0 for bx in self.beam_x) or any(-1.0 < ax - pos[0] < 5.0 for ax in self.arm_x): alt = self.CLIMB
        sp = np.linalg.norm(v)
        if sp > self.SPEED: v = v / sp * self.SPEED
        vz = 1.6 * (alt - pos[2]); yaw_cmd = float(np.arctan2(tgt[1] - pos[1], tgt[0] - pos[0]))
        return np.array([v[0], v[1], np.clip(vz, -2.0, 2.0)]), yaw_cmd

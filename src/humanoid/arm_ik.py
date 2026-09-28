"""S1-E31 — damped least-squares IK for the FFW arms, so manipulation is solved rather than scripted.

Before this, every bench in this repo "grasped" by teleporting the object to the palm. That makes the
arm decorative: an agent could be scored on a pick it never physically performed. This solves the 7
arm joints plus the lift column so the palm SITE actually arrives at a target point, and reports the
residual so a caller can tell a reach from a miss.

Damped least squares (Levenberg-Marquardt) rather than the pseudo-inverse: near a singularity the
pseudo-inverse asks for enormous joint velocities and the arm flails. The damping term trades a
little accuracy for a solution that stays inside the joint limits and converges.
"""
import numpy as np
import mujoco

ARM_JOINTS = {s: [f"arm_{s}_joint{i}" for i in range(1, 8)] for s in ("l", "r")}


class ArmIK:
    def __init__(self, model, data, side="r", use_lift=True, damping=0.12):
        self.m, self.d, self.side = model, data, side
        self.site = model.site(f"{'right' if side=='r' else 'left'}_palm").id
        names = list(ARM_JOINTS[side]) + (["lift_joint"] if use_lift else [])
        self.jids, self.qadr, self.dofs, self.lims = [], [], [], []
        for n in names:
            j = model.joint(n)
            self.jids.append(j.id)
            self.qadr.append(model.jnt_qposadr[j.id])
            self.dofs.append(model.jnt_dofadr[j.id])
            self.lims.append(model.jnt_range[j.id] if model.jnt_limited[j.id] else np.array([-np.pi, np.pi]))
        self.lims = np.array(self.lims)
        self.damping = damping

    def palm(self):
        return self.d.site_xpos[self.site].copy()

    def solve(self, target, iters=220, tol=2e-3, step=0.55):
        """Move the joints so the palm reaches `target`. Returns the final residual in metres.

        Operates on a scratch copy so a failed solve leaves the live state untouched — a caller that
        cannot reach should not be left with a half-extended arm."""
        m = self.m
        d = mujoco.MjData(m)
        d.qpos[:] = self.d.qpos
        d.qvel[:] = 0
        mujoco.mj_forward(m, d)
        tgt = np.asarray(target, float)
        jacp = np.zeros((3, m.nv))
        jacr = np.zeros((3, m.nv))
        for _ in range(iters):
            mujoco.mj_forward(m, d)
            err = tgt - d.site_xpos[self.site]
            if np.linalg.norm(err) < tol:
                break
            mujoco.mj_jacSite(m, d, jacp, jacr, self.site)
            J = jacp[:, self.dofs]                       # 3 x n over the joints we control
            JT = J.T
            # damped least squares: dq = J^T (J J^T + lambda^2 I)^-1 e
            A = J @ JT + (self.damping ** 2) * np.eye(3)
            dq = JT @ np.linalg.solve(A, err) * step
            q = d.qpos[self.qadr] + dq
            d.qpos[self.qadr] = np.clip(q, self.lims[:, 0], self.lims[:, 1])
        mujoco.mj_forward(m, d)
        self.q = d.qpos[self.qadr].copy()
        return float(np.linalg.norm(tgt - d.site_xpos[self.site]))

    def apply(self, ctrl_map, act):
        """Write the solved joint angles to the position actuators."""
        names = [f"arm_{self.side}_joint{i}" for i in range(1, 8)] + ["lift_joint"]
        for n, v in zip(names, self.q):
            a = act.get(n)
            if a is not None:
                lo, hi = self.m.actuator_ctrlrange[a]
                ctrl_map[a] = float(np.clip(v, lo, hi))

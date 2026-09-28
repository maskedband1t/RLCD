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
    def __init__(self, model, data, side="r", use_lift=True, damping=0.08, slide_weight=0.15):
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
        self.slide_weight = slide_weight

    def palm(self):
        return self.d.site_xpos[self.site].copy()

    def solve(self, target, iters=260, tol=5e-3, step=0.5, restarts=6):
        """Move the joints so the palm reaches `target`. Returns the final residual in metres.

        WEIGHTED damped least squares. S1-E34: the lift is a SLIDER in metres while the arm joints are
        HINGES in radians, so the lift's Jacobian column is ~1 m per unit against ~0.4 m per radian for
        a hinge. An unweighted solve therefore rides the lift to its limit -- nailing the target's
        HEIGHT exactly and never using the arm for x/y. Measured symptom: palm at [1.284, 1.306, 0.975]
        for a target at [1.51, 2.00, 0.975], i.e. z exact and 73 cm out horizontally, with the palm
        BEHIND the base. W de-weights the lift so the arm does the reaching.

        Restarts because DLS is a local method and the shoulder has a large null space: a target near
        the edge of the envelope is easy to approach from a bad initial pose and impossible to finish.

        Operates on a scratch copy, so a failed solve leaves the live state untouched.
        """
        m = self.m
        n = len(self.dofs)
        W = np.ones(n)
        for i, jid in enumerate(self.jids):
            if m.jnt_type[jid] == mujoco.mjtJoint.mjJNT_SLIDE:
                W[i] = self.slide_weight
        rng = np.random.RandomState(0)
        tgt = np.asarray(target, float)
        jacp = np.zeros((3, m.nv)); jacr = np.zeros((3, m.nv))
        best_q, best_res = None, np.inf
        q_start = self.d.qpos[self.qadr].copy()
        for attempt in range(restarts):
            d = mujoco.MjData(m)
            d.qpos[:] = self.d.qpos
            d.qvel[:] = 0
            if attempt:                       # perturb within limits, keep the first try deterministic
                lo, hi = self.lims[:, 0], self.lims[:, 1]
                d.qpos[self.qadr] = np.clip(q_start + rng.uniform(-1.2, 1.2, n) * (hi - lo) * 0.25, lo, hi)
            for _ in range(iters):
                mujoco.mj_forward(m, d)
                err = tgt - d.site_xpos[self.site]
                if np.linalg.norm(err) < tol:
                    break
                mujoco.mj_jacSite(m, d, jacp, jacr, self.site)
                J = jacp[:, self.dofs] * W                    # weighted columns
                A = J @ J.T + (self.damping ** 2) * np.eye(3)
                dq = (J.T @ np.linalg.solve(A, err)) * W * step
                d.qpos[self.qadr] = np.clip(d.qpos[self.qadr] + dq, self.lims[:, 0], self.lims[:, 1])
            mujoco.mj_forward(m, d)
            res = float(np.linalg.norm(tgt - d.site_xpos[self.site]))
            if res < best_res:
                best_res, best_q = res, d.qpos[self.qadr].copy()
            if best_res < tol:
                break
        self.q = best_q
        return best_res

    def apply(self, ctrl_map, act):
        """Write the solved joint angles to the position actuators."""
        names = [f"arm_{self.side}_joint{i}" for i in range(1, 8)] + ["lift_joint"]
        for n, v in zip(names, self.q):
            a = act.get(n)
            if a is not None:
                lo, hi = self.m.actuator_ctrlrange[a]
                ctrl_map[a] = float(np.clip(v, lo, hi))

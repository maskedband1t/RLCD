"""E195's arms. Every one sees the same evidence and answers: commit to this grounding, or close the distance first."""
import math, os
import numpy as np
from stack.ground import Grounder, counter_positions, approach_pose, viewpoint, APPEARANCE, BIN_BOUND

WALK_SPEED = 0.7           # m/s, the same figure bench 5's walking policy is commanded with
VERIFY_STEP = 0.6          # m closer per verification
VERIFY_FLOOR = 1.0         # m: closer than this and the far end of the counter leaves a 69-degree lens

# The first version verified by walking STRAIGHT IN, 1.0 m at a time, with no floor. That made verification actively
# harmful -- `always_verify` scored 168/300 against `always_commit`'s 256/300 and took twice the irreversible losses --
# because at 0.6 m with a lateral offset the row subtends more than the field of view and objects leave the frame
# entirely. The grounder then picks from whatever is left, confidently.
#
# The effect is real and worth keeping as a constraint, but it is not what verification means. A robot that re-examines
# a target re-positions to see it SQUARELY: that is what HomeBody's visual servoing does, correcting alignment during
# the approach. So a verification also halves the lateral offset and the heading error, and stops at a standoff where
# the whole counter still fits in frame.
COST_IRREVERSIBLE = 120.0  # seconds of human time to undo a binned object: it cannot be undone, so this prices the loss
COST_MISPLACED = 12.0      # seconds to move something put in the wrong (recoverable) place


def episode(seed, arm, max_verify=2):
    """One grounding decision, with the option to walk closer first. Returns cost, whether it was right, and how long."""
    pos = counter_positions()
    names = [k for k in pos if k != "medicine"]
    so, lat, ye = viewpoint(seed)
    intended = names[seed % len(names)]
    t = 0.0
    for step in range(max_verify + 1):
        xy, yaw = approach_pose(so, lat, ye)
        g = Grounder(seed * 17 + step, names, pos, xy, yaw)
        ev, ok, got = g.attempt(intended)
        ev = dict(ev); ev["intended"] = intended
        ev["this_step_is_irreversible"] = (APPEARANCE[intended]["belongs"] == "bin")
        ev["verifications_left"] = max_verify - step
        if step == max_verify or not arm.verify(ev):
            break
        moved = max(VERIFY_FLOOR, so - VERIFY_STEP)
        t += (abs(so - moved) + abs(lat) * 0.5) / WALK_SPEED
        so, lat, ye = moved, lat * 0.5, ye * 0.5
    irreversible = (not ok) and APPEARANCE[intended]["belongs"] == "bin"
    misplaced = (not ok) and not irreversible
    cost = t + (COST_IRREVERSIBLE if irreversible else 0.0) + (COST_MISPLACED if misplaced else 0.0)
    return dict(seed=seed, intended=intended, chosen=ev.get("_truth_chosen"), correct=int(ok),
                irreversible=int(irreversible), misplaced=int(misplaced),
                verifies=step, t_verify=round(t, 2), cost=round(cost, 2),
                p=getattr(arm, "last_p", None), bin_bound=int(APPEARANCE[intended]["belongs"] == "bin"))


class AlwaysCommit:
    """Floor. Acts on every grounding. This is what an architecture with no applicability check does."""
    name = "always_commit"
    calls = errors = 0
    def verify(self, ev): return False


class AlwaysVerify:
    """Ceiling on accuracy, and the price of refusing to judge: spends every verification it is allowed."""
    name = "always_verify"
    calls = errors = 0
    def verify(self, ev): return ev["verifications_left"] > 0


class MarginRule:
    """What deployed systems actually do: commit when the top-two score gap clears a constant.

    The threshold is FITTED on the training bank rather than chosen by me, so that the comparison is against the best
    version of this idea and not a strawman I tuned badly."""
    name = "margin_rule"
    calls = errors = 0
    def __init__(self, tau=1.0): self.tau = tau; self.last_p = None
    def verify(self, ev): return ev["verifications_left"] > 0 and ev.get("score_margin", 9) < self.tau


class FittedLogistic:
    """THE CONTROL THAT DECIDES THE CLAIM (E195.3). Logistic regression on the evidence, fitted on labelled attempts.

    Claim 2.8 measured this shape elsewhere: a zero-shot calibrated judge reached .676 AUROC where a model fitted on
    1,200 labels reached .772. If the fitted model matches or beats the calibrated one here, the honest finding is that
    you need labels, and what zero-shot buys is the labelling, not the judgement."""
    name = "fitted_logistic"
    calls = errors = 0
    # The derived comparison features are given to the control too. A control that is denied the information the model
    # gets is not a control, it is a strawman, and the whole point of this arm is to be the best version of "just fit it
    # on labels" so that beating it means something.
    FEATS = ("score_margin", "degrees_from_pointer", "apparent_size_deg", "range_m",
             "colour_distance_to_runner_up", "candidates_the_pointer_touches", "nearest_edge_of_frame_deg",
             "pointer_inside_chosen", "objects_in_view",
             "width_error", "height_error", "colour_error")

    @staticmethod
    def derive(ev):
        e = dict(ev)
        e["width_error"] = abs(float(ev.get("measured_width_m", 0)) - float(ev.get("expected_width_m", 0)))
        e["height_error"] = abs(float(ev.get("measured_height_m", 0)) - float(ev.get("expected_height_m", 0)))
        mc = ev.get("measured_colour_rgb") or [0, 0, 0]; xc = ev.get("expected_colour_rgb") or [0, 0, 0]
        e["colour_error"] = float(sum((a - b) ** 2 for a, b in zip(mc, xc)) ** 0.5)
        e["pointer_inside_chosen"] = float(bool(ev.get("pointer_inside_chosen")))
        return e

    def __init__(self): self.w = None; self.b = 0.0; self.mu = None; self.sd = None; self.last_p = None

    def fit(self, rows):
        X = np.array([[float(self.derive(r[0]).get(f, 0.0)) for f in self.FEATS] for r in rows])
        y = np.array([float(r[1]) for r in rows])
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        w = np.zeros(Z.shape[1]); b = 0.0
        for _ in range(4000):                                  # plain gradient ascent; no sklearn dependency
            p = 1 / (1 + np.exp(-(Z @ w + b)))
            g = y - p
            w += 0.05 * (Z.T @ g) / len(y) - 1e-4 * w
            b += 0.05 * g.mean()
        self.w, self.b = w, b
        return self

    def prob(self, ev):
        d = self.derive(ev)
        x = np.array([float(d.get(f, 0.0)) for f in self.FEATS])
        z = (x - self.mu) / self.sd
        return float(1 / (1 + np.exp(-(z @ self.w + self.b))))

    def verify(self, ev):
        self.last_p = self.prob(ev)
        if ev["verifications_left"] <= 0: return False
        return expected_cost_says_verify(self.last_p, ev)


def expected_cost_says_verify(p, ev):
    """E195.5's mechanism. Commit when the expected cost of being wrong is below the cost of another look.

    This is the one thing a raw score cannot imitate: it needs p to MEAN something, because it is multiplied by a cost in
    seconds. E53 measured hand-set gates costing 3x more than this on identical answers, on real fleet data."""
    loss = COST_IRREVERSIBLE if ev.get("this_step_is_irreversible") else COST_MISPLACED
    return (1.0 - p) * loss > VERIFY_STEP / WALK_SPEED

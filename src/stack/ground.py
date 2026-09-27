"""Bench 7: the grounding-commitment seat.

WHY THIS BENCH EXISTS, and why bench 5 could not be repaired into it. The harness preflight's first check is that an arm
which never calls a model must fail, and on bench 5 such an arm clears the table 24 times in 25. That is not an instrument
defect; it says the bench contains no question a model is needed for. The question has to come from the stack.

Reading HomeBody and IMLE-VLA back to back on 26-27 September says where it lives. HomeBody's frontier model points at a
PIXEL, once, and a classical loop -- segmentation, stereo depth, SAMURAI tracking, visual servoing -- closes on that point
without asking again. IMLE-VLA keeps a VLA and makes it 55 Hz, and its whole justification is that conditional IMLE
"provably preserves multimodal action coverage", a statement about a distribution that is then read only for an action.
Neither system has anything in the seat between them, and the decision that belongs there is the same in both:

    **is this grounding good enough to commit to, or should I gather more evidence first?**

That question is not computable from the grounding, because the grounding is the thing in doubt. It needs a number the
layer above can spend, because the cost of being wrong is wildly asymmetric. And it is needed per attempt, so a frontier
call will not do. All three clauses of the seat test hold, which is the first time on this programme they have.

WHAT IS REAL HERE, AND WHAT IS SIMULATED. The confusion is not invented. HomeBody's own published assets give the kitchen
its colours, and mug and carton are `0.92 0.92 0.90` and `0.90 0.88 0.82` -- two pale objects 0.16 m apart on a counter.
From across the room they subtend a small angle and a pointer lands between them. That is a real confusion between two
real meshes, and it is the CONSEQUENTIAL one, because the carton belongs in the bin and the mug does not: confusing them
throws the mug away, and the bin is irreversible.

What is simulated is the grounder itself. We have no segmentation network, and E189 measured a real one at identity 1 in
11, far worse than anything modelled here, so a result from this bench is conditional on a grounder much better than any
that exists. That is stated wherever the numbers are, not buried."""
import math
import numpy as np

# METHOD ERROR 78. The colours below are HomeBody's, and so is the third number in their asset table -- but that number
# is the object's HEIGHT, not a half-width, and reading it as a half-width inverted the whole experiment. It made the
# carton the largest target on the counter (0.185) when it is in fact the narrowest, and since a larger silhouette
# absorbs more pointing error, the bin-bound object became the most reliably grounded thing in the scene. The
# irreversible channel measured 0.5 % and the bench was unfalsifiable. Half-widths here are measured off the meshes:
#
#   glass   0.074 x 0.074 x 0.115   half-width 0.037
#   carton  0.070 x 0.070 x 0.185   half-width 0.035   <- a tall narrow milk carton, the SMALLEST target
#   mug     0.116 x 0.084 x 0.095   half-width 0.058   <- widest, because of the handle
#
# So the object whose mistake cannot be undone is also the hardest one to point at, which is not a convenience -- it is
# what the assets say, and it is why this confusion is worth building a bench around at all.
APPEARANCE = {
    "glass":    dict(rgb=(0.82, 0.90, 0.96), alpha=0.45, half=0.037, height=0.115, belongs="counter"),
    "carton":   dict(rgb=(0.90, 0.88, 0.82), alpha=1.00, half=0.035, height=0.185, belongs="bin"),
    "mug":      dict(rgb=(0.92, 0.92, 0.90), alpha=1.00, half=0.058, height=0.095, belongs="counter"),
    "medicine": dict(rgb=(0.85, 0.72, 0.25), alpha=1.00, half=0.026, height=0.086, belongs="counter"),
}
POINT_NOISE_DEG = 2.4     # the pointer's angular error, 1 sigma; a VLM pointing at a 1000-wide normalised image
CAM_H = 1.25              # head-camera height: a RealSense D435i on a G1, the mount HomeBody actually carries
FOV_H_DEG = 69.0          # the D435i's horizontal field of view, from its datasheet
FOV_V_DEG = 42.0          # and vertical
APPEAR_W = 8.0            # degrees of edge distance one unit of colour distance is worth; mug-vs-carton is 0.092 -> 0.7 deg

# WHY VISIBILITY HAD TO BE MODELLED. Pointing noise alone gives a nonzero error rate that varies sensibly with range, so
# the aggregate dose gate passes -- and the bench still measures nothing, because the CONSEQUENTIAL error never occurs.
# The only irreversible act in this task is putting something in the bin, which happens when the plan intends the carton
# and the grounder returns something else. The carton is the largest object HomeBody puts on that counter, so a pointer
# aimed at it strays outside its silhouette least often, and in 2400 attempts it was never once mis-grounded.
#
# The failure that does produce it is the one both papers are actually built around: the intended object is OUT OF VIEW
# or OCCLUDED, and a grounder with no precondition returns its best visible candidate instead of saying it cannot see the
# thing. HomeBody's option set is constant, size five, always fully available, with no applicability check anywhere --
# so nothing in their architecture can decline. Their answer to occlusion is remembered geometry, which is right until
# the world moves. This is that failure, in its cheapest form.


def colour_distance(a, b):
    return float(np.linalg.norm(np.array(APPEARANCE[a]["rgb"]) - np.array(APPEARANCE[b]["rgb"])))


class Grounder:
    """Turns an intended object into a grounding, the way a pointer plus an appearance matcher would.

    The pointer lands near the intended object with angular noise. Every visible object is then scored by how close it is
    to the pointer in the image and how well its appearance matches what was asked for. Top-1 is the grounding. Whether
    top-1 is the intended object is the ground truth, and it is exact, which is the whole reason to do this in a
    simulator: the thing a real system can never label is free here."""

    def __init__(self, seed, objects, positions, cam_xy, cam_yaw):
        self.rng = np.random.default_rng(80_000 + seed)
        self.objects = list(objects)
        self.pos = dict(positions)              # name -> (x, y, z)
        self.cam = np.array([cam_xy[0], cam_xy[1], CAM_H], float)
        self.yaw = float(cam_yaw)

    def bearing(self, name):
        """Angular position of an object in the camera frame: (azimuth, elevation) in degrees."""
        d = np.array(self.pos[name], float) - self.cam
        az = math.degrees(math.atan2(d[1], d[0]) - self.yaw)
        az = (az + 180) % 360 - 180
        el = math.degrees(math.atan2(d[2], float(np.linalg.norm(d[:2]))))
        return az, el

    def range_to(self, name):
        return float(np.linalg.norm(np.array(self.pos[name], float) - self.cam))

    def visible(self, name):
        """In frame and not hidden behind a nearer object. Returns (bool, occluding-object-or-None)."""
        az, el = self.bearing(name)
        if abs(az) > FOV_H_DEG / 2 or abs(el) > FOV_V_DEG / 2: return False, "out_of_frame"
        r = self.range_to(name)
        for o in self.objects:
            if o == name: continue
            oaz, oel = self.bearing(o)
            if self.range_to(o) >= r: continue
            if math.hypot(oaz - az, oel - el) < 0.5 * self.angular_size(o): return False, o
        return True, None

    def angular_size(self, name):
        """How large the object appears, in degrees. A small object far away is a small target for a pointer."""
        return math.degrees(2 * math.atan(APPEARANCE[name]["half"] / max(0.2, self.range_to(name))))

    def attempt(self, intended):
        """One grounding attempt. Returns the evidence a commitment decision would see, plus the exact truth."""
        iaz, iel = self.bearing(intended)
        n = POINT_NOISE_DEG
        paz = iaz + float(self.rng.normal(0, n))
        pel = iel + float(self.rng.normal(0, n))

        scored = []
        for o in self.objects:
            vis, _by = self.visible(o)
            if not vis: continue              # a grounder scores what it can see, and nothing else
            az, el = self.bearing(o)
            ang = math.hypot(az - paz, el - pel)                 # degrees from the pointer to the object's centre
            # Distance to the object's SILHOUETTE, not to its centre scaled by its size. The first version used
            # `ang / angular_size`, which hands a permanently larger object a permanent advantage even when the pointer
            # is nowhere near it -- the carton became an attractor that swallowed 716 of 719 errors and drove the
            # aggregate error to 40 % while staying flat in range. A segmenter asks whether the pointer falls ON the
            # instance; only when it falls on nothing does nearest-edge decide.
            edge = max(0.0, ang - 0.5 * self.angular_size(o))
            appear = colour_distance(intended, o)                # 0 for the intended object's own colour
            score = -(edge + APPEAR_W * appear)                  # higher is better
            scored.append((score, o, ang, edge, appear))
        if not scored:
            return {"chosen": None, "nothing_visible": True}, False, None
        scored.sort(reverse=True)
        top, second = scored[0], (scored[1] if len(scored) > 1 else scored[0])
        ivis, iby = self.visible(intended)
        self.last_intended_visible = ivis
        self.last_hidden_by = iby

        # METHOD ERROR 79. The evidence used to report `chosen` and `runner_up` as TRUE identities, next to the name of
        # the object that was asked for -- so the answer was literally `chosen == asked_for` and the calibrated model
        # scored AUROC 1.000 on held-out data by reading it off. Same species as the option-set leak found this morning:
        # I handed over the thing the model was supposed to infer.
        #
        # A real grounder does not know what it selected. It reports "I found the carton" because a region matched the
        # carton's description, and the open question is whether that region IS the carton. So the report carries the
        # MEASURED properties of the selected region and the EXPECTED properties of the requested object, with sensor
        # noise on the measurements, and the judgement is whether they are consistent. That is a genuinely hard call
        # here, because the glass and the carton are 0.074 m and 0.070 m wide and nearly the same colour.
        rng = self.rng
        mw = APPEARANCE[top[1]]["half"] * 2 * (1 + float(rng.normal(0, 0.10)))
        mh = APPEARANCE[top[1]]["height"] * (1 + float(rng.normal(0, 0.10)))
        mc = tuple(round(float(c + rng.normal(0, 0.035)), 3) for c in APPEARANCE[top[1]]["rgb"])
        exp = APPEARANCE[intended]
        ev = {
            "requested_object": intended,
            "measured_width_m": round(mw, 3),
            "measured_height_m": round(mh, 3),
            "measured_colour_rgb": list(mc),
            "expected_width_m": round(exp["half"] * 2, 3),
            "expected_height_m": round(exp["height"], 3),
            "expected_colour_rgb": list(exp["rgb"]),
            "score_margin": round(float(top[0] - second[0]), 3),
            "degrees_from_pointer": round(float(top[2]), 2),
            "degrees_between_top_two": round(abs(float(top[2] - second[2])), 2),
            "apparent_size_deg": round(self.angular_size(top[1]), 2),
            "range_m": round(self.range_to(top[1]), 2),
            "colour_distance_to_runner_up": round(colour_distance(top[1], second[1]), 3),
            "_truth_chosen": top[1],        # underscore: scoring only, stripped before any model sees the state
            "pointer_inside_chosen": bool(top[3] <= 0.0),
            "candidates_the_pointer_touches": int(sum(1 for s in scored if s[3] <= 0.0)),
            "objects_in_view": len(scored),
            "nearest_edge_of_frame_deg": round(float(FOV_H_DEG / 2 - abs(self.bearing(top[1])[0])), 1),
        }
        return ev, (top[1] == intended), top[1]


def counter_positions(spacing=0.16, z=0.95):
    """The kitchen counter as HomeBody lays it out: glass, carton, mug in a row along the counter, medicine in the
    drawer below. The offsets are theirs (tools/hb_kitchen.py), so the three objects are spread ALONG the counter."""
    return {"glass": (2.0 - spacing, 0.0, z), "carton": (2.0, 0.0, z),
            "mug": (2.0 + spacing, 0.0, z), "medicine": (2.0, 0.0, 0.55)}


def approach_pose(standoff, lateral=0.0, yaw_err=0.0):
    """Where the robot stands to look at the counter, and which way it faces.

    The first version put the camera ON the counter's own axis, so the three objects sat at the same azimuth and
    differed only in depth -- collinear with the eye, a viewpoint nobody occupies, which made the whole result an
    artefact of one object being nearer. A robot approaches a counter from the FRONT, so the row spreads laterally.

    `lateral` and `yaw_err` matter for the same reason the start-pose jitter mattered on bench 5 (E194): a robot does not
    stop on the same square twice, and off-centre is where the interesting geometry lives. Straight on, three objects in
    a row at equal depth can never occlude one another and never leave the frame. Standing to one side, the row
    foreshortens, near objects begin to hide far ones, and at close range the far end of the counter falls outside a
    69-degree lens. Those are the conditions under which the intended object is not visible at all -- and a grounder with
    no precondition answers anyway."""
    cx, cy = 2.0 + lateral, -standoff
    yaw = math.atan2(0.0 - cy, 2.0 - cx) + yaw_err
    return (cx, cy), yaw


BIN_BOUND = "carton"      # the only object whose destination is irreversible; HomeBody's own task shape


def viewpoint(seed):
    """A seeded approach: where the robot happened to stop, and how squarely it happened to face the counter."""
    g = np.random.default_rng(50_000 + seed)
    return (float(g.uniform(0.9, 3.4)),                   # standoff
            float(g.uniform(-0.9, 0.9)),                  # lateral offset along the counter
            float(g.normal(0, 0.16)))                     # heading error, radians


def sweep(seeds=600, verbose=True):
    """DOSE GATE, before any arm exists, and it is checked on the CONSEQUENTIAL channel rather than in aggregate.

    An aggregate error rate that varies sensibly is not enough: the first version had one, and the only irreversible act
    in the task -- binning the wrong object -- still never occurred, because the bin-bound carton is the largest target
    on the counter and pointing noise alone never strays off it. So the gate requires BOTH that grounding fails overall
    AND that it fails on the object whose mistake cannot be undone."""
    from collections import defaultdict
    pos = counter_positions()
    names = [k for k in pos if k != "medicine"]
    conf = defaultdict(int)
    band = defaultdict(lambda: [0, 0])
    tot = [0, 0]; cons = [0, 0]; invis = 0
    hid = defaultdict(int); hid_err = defaultdict(int)
    for s in range(seeds):
        so, lat, ye = viewpoint(s)
        xy, yaw = approach_pose(so, lat, ye)
        g = Grounder(s, names, pos, xy, yaw)
        for intended in names:
            ev, ok, got = g.attempt(intended)
            if got is None: invis += 1; continue
            if not getattr(g, "last_intended_visible", True):
                hid[g.last_hidden_by] += 1
                if not ok: hid_err[g.last_hidden_by] += 1
            b = round(min(3.5, max(1.0, so)) * 2) / 2
            band[b][0] += int(ok); band[b][1] += 1
            tot[0] += int(ok); tot[1] += 1
            if intended == BIN_BOUND:
                cons[0] += int(ok); cons[1] += 1
            if not ok: conf[(intended, got)] += 1
    if verbose:
        print(f"{'standoff m':>11}{'grounded right':>17}{'error':>9}")
        for b in sorted(band):
            ok, n = band[b]
            if n: print(f"{b:>11.1f}{ok:>12}/{n:<4}{1 - ok / n:>8.1%}")
        print(f"\n  overall              {tot[0]}/{tot[1]}  error {1 - tot[0] / tot[1]:.1%}")
        print(f"  CONSEQUENTIAL ({BIN_BOUND}, bin-bound)  {cons[0]}/{cons[1]}  "
              f"error {1 - cons[0] / cons[1]:.1%}   <- the irreversible channel")
        print(f"  attempts where nothing was visible at all: {invis}")
        print(f"  attempts where the INTENDED object was not visible: {sum(hid.values())}")
        for k, v in sorted(hid.items(), key=lambda kv: -kv[1]):
            print(f"      hidden by {str(k):<14} {v:>5}   of which mis-grounded {hid_err.get(k, 0):>5}")
        print("\n  confusions (intended -> grounded):")
        for (a, b2), c in sorted(conf.items(), key=lambda kv: -kv[1])[:8]:
            tag = "  IRREVERSIBLE: wrong object binned" if a == BIN_BOUND else ""
            print(f"    {a:>9} -> {b2:<9} {c:>5}   colour distance {colour_distance(a, b2):.3f}{tag}")
    rates = [1 - band[b][0] / band[b][1] for b in sorted(band) if band[b][1]]
    agg_ok = min(rates) >= 0.0 and max(rates) - min(rates) > 0.05
    cons_ok = cons[1] > 0 and (1 - cons[0] / cons[1]) > 0.02
    return (agg_ok and cons_ok), rates, (1 - cons[0] / cons[1] if cons[1] else 0.0)


if __name__ == "__main__":
    ok, rates, cons = sweep()
    print(f"\n  dose gate: {'PASS' if ok else 'FAIL'} -- aggregate error varies "
          f"({min(rates):.1%} to {max(rates):.1%}), irreversible-channel error {cons:.1%}")

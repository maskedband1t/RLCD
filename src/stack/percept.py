"""Bench 5 with perception in the loop, and the one decision code cannot compute for itself.

WHY THIS EXISTS. E191 ran a `code_only` arm on bench 5 -- zero model calls, both judgements computed from the
simulator's state -- and it tied the best model framing at 12/12 while being the fastest arm on the board. That result
is correct and it is damning: every fact bench 5's chooser needed was handed to it, already true, by the simulator.
Code can compute anything it can observe. So bench 5 measured the COST of asking a model, never the VALUE.

E189 measured what a real robot's facts cost instead: VLM object identity 1 correct in 11, a drawer reported closed
while it stood open. Under perception the chooser's facts are estimates, and the decision that appears is not "how
fast" but "is my reading good enough to act on, or should I look again?". That decision is not computable from the
reading, because the reading is what is in doubt -- a hand-written consistency check only covers the failure modes its
author had already seen.

WHAT IS FAITHFUL HERE. The corruption changes only what the chooser is TOLD. The physics underneath are untouched:
if the glass is mislabelled as the mug and therefore carried at walking speed, the real glass really breaks, through
the same `_fragile_risk` path as every earlier bench. No consequence is scored by hand. Masses and widths in the
evidence rows are the model's own numbers from OBJECTS, not invented.

THE FIVE MODES, and the honest seam. Three are declared ANTICIPATED and get hand-written checks in `Code3`. Two are
HELD OUT: their signatures sit in evidence fields those checks do not read. `CodeAll` is the control that keeps this
from being rigged -- it reads every field, one rule per mode, and shows exactly what perfect anticipation buys. If
`CodeAll` matches the model, the finding is "a model saves you writing the rules", not "a model does what code cannot".
That is a weaker claim and it is the one the evidence would support, so the control ships with the bench."""
import os, random
from contextlib import contextmanager
from stack.table_run import options_for

# What one closer look costs, charged as real clock time. MEASURED against the locomotion policy, not chosen: see E192f.
# A sweep of pause durations from 0.5 s to 12.0 s in 0.5 s steps found EXACTLY ONE unstable value -- 3.0 s topples the
# robot on 5 of 5 seeds while it is carrying, and all 23 other values are clean on all 5. My original arbitrary 3.0
# landed on it, which is how 15 of 25 `code_3` episodes and 25 of 25 `code_all` episodes ended on the floor in a run
# that was supposed to be measuring perception. 2.0 s is stable on the sweep and is also defensible on its own terms as
# roughly one vision round trip.
LOOK_S = 2.0
UNSTABLE_PAUSES = (3.0,)                    # from the E192f sweep; a pause here is a locomotion bug, not a choice
assert LOOK_S not in UNSTABLE_PAUSES, f"LOOK_S={LOOK_S} is a measured-unstable pause duration"
EXPECT = {"glass": (0.25, 0.090), "box": (1.20, 0.140), "mug": (0.35, 0.100),
          "cup": (0.35, 0.100)}                 # kg, width m -- from OBJECTS; "cup" is the mislabel's wrong label
# A mislabel has to use a label that does NOT collide with a real object's, and the option set must never mention the
# true name. Reporting the glass as "mug" put two rows called "mug" in the report while the option list still offered
# `look_closer(object=glass)` from the plan -- so the mismatch between report and options WAS the answer, handed over for
# free. Claim 7 cuts both ways: the option set is the signal, so anything it reveals is something the model did not have
# to infer. The glass is reported as a "cup" instead, and a reported label is mapped back to the real object only when
# the look is executed, inside the simulator, where the chooser cannot see it.
WRONG_LABEL = "cup"
# METHOD ERROR 75 (see LAB-NOTEBOOK). The first five modes were invented from what a camera gets wrong, without
# checking that any of them could reach this bench's scoring. `success` has exactly THREE failure channels -- a broken
# object, a workspace violation, an object left uncleared -- and three of the five modes reached none of them:
# `stale_clear` was inert because the plan already picks the blocking box before the mug it blocks, and `duplicate`
# changed no physical quantity whatsoever. A `null_trust` smoke run scored 4/5 and the bench was measuring nothing.
#
# The five modes below therefore each declare the CHANNEL they reach, and `validate_doses()` refuses to run the bench
# until a trust-everything arm actually fails on every one. Signature and channel are separated on purpose: the two
# held-out modes reuse a channel already proven to bite, and differ only in which evidence field carries the tell.
# That is what makes it a generalisation test rather than two different experiments.
MODES = ["mislabel", "ghost_done", "unlisted_person", "low_conf", "ghost_done_quiet"]
ANTICIPATED = MODES[:3]                     # Code3 was written against these and only these
CHANNEL = {"mislabel": "break", "ghost_done": "uncleared", "unlisted_person": "violation",
           "low_conf": "break", "ghost_done_quiet": "uncleared"}
SIGNATURE = {"mislabel": "measured_mass_kg", "ghost_done": "times_detected",
             "unlisted_person": "motion_sensor", "low_conf": "detector_confidence",
             "ghost_done_quiet": "position_age_s"}


class Perceived:
    """A proxy round the room. `facts`, `props` and `people` are what perception reports; everything else delegates to
    the real room, so the simulator keeps scoring the truth. One mode fires per episode, chosen by seed."""

    def __init__(self, room, seed):
        self._room = room
        # `seed % 5` also selects the room's disruption, so keying the mode the same way made mode and disruption
        # perfectly correlated -- every `low_conf` episode would have carried the same physical disruption, and no
        # effect could be separated from it. `seed // 5` decorrelates them: over 25 seeds each mode meets all five
        # disruptions exactly once. Part of method error 75.
        self.mode = MODES[(seed // len(MODES)) % len(MODES)]
        self.resolved = set()               # objects a closer look has cleared
        self.looks = 0
        self._rng = random.Random(90_000 + seed)
        self.target = "glass" if self.mode in ("mislabel", "low_conf") else \
                      "box" if self.mode in ("ghost_done", "ghost_done_quiet") else None

    def __getattr__(self, k):
        """Anything not overridden here is the real room's. Queries that walk the person list INSIDE the real room --
        `predicted_dist` above all -- have to be run with the hidden person actually removed, or the corruption never
        reaches the decision: the chooser's own proximity computation would keep seeing the person it was not told
        about. That is why `unlisted_person` measured zero violations before this existed."""
        a = getattr(self._room, k)
        if k in ("predicted_dist", "nearest", "min_person_dist") and callable(a):
            def wrapped(*args, **kw):
                with self._hidden(): return a(*args, **kw)
            return wrapped
        return a

    @contextmanager
    def _hidden(self):
        """Removes the unreported person from the real room for the duration of a QUERY. `run_skill` is never wrapped,
        so the simulator still counts the violation against a person the robot genuinely failed to see."""
        if self.mode != "unlisted_person" or not self._live():
            yield; return
        real = self._room.people
        try:
            self._room.people = self.people
            yield
        finally:
            self._room.people = real

    def real_of(self, reported):
        """Maps a reported label back to the object it actually is. Used only when a look is EXECUTED, never exposed."""
        if reported == WRONG_LABEL and self.mode in ("mislabel", "low_conf"): return self.target
        return reported

    def _live(self):
        """Is the corruption still in force? A closer look at the affected object retires it."""
        if self.mode == "unlisted_person": return "person" not in self.resolved
        return self.target not in self.resolved

    # ---- what perception reports ------------------------------------------------------------------------------
    @property
    def people(self):
        """Drops the NEAREST person, not an arbitrary one. Dropping `p[1:]` left the close person visible on most seeds,
        so the mode could not reach the violation channel -- part of method error 75."""
        p = self._room.people
        if self.mode == "unlisted_person" and self._live() and p:
            near = min(p, key=lambda q: self._room.dist(q.xy))
            return [q for q in p if q is not near]
        return p

    @property
    def cleared(self):
        """The ghost modes report an object already finished. The real room never cleared it, so `record()` scores the
        episode a failure on the uncleared channel -- the belief is wrong and nothing in the physics was faked."""
        c = list(self._room.cleared)
        if self._live() and self.mode in ("ghost_done", "ghost_done_quiet") and self.target not in c:
            c.append(self.target)
        return c

    @property
    def placed_at(self):
        d = dict(self._room.placed_at)
        if self._live() and self.mode in ("ghost_done", "ghost_done_quiet"):
            d[self.target] = "tray"
        return d

    def props(self, n):
        p = dict(self._room.props(n))
        if self._live() and self.mode == "mislabel" and n == self.target:
            p.update(self._room.props("mug"))       # reported as the mug: not fragile
        if self._live() and self.mode == "low_conf" and n == self.target:
            p["fragile"] = False                    # the label is wrong and the detector half-knows it
        return p

    def remaining(self):
        return [n for n in self._room.remaining() if n not in self.cleared]

    def evidence(self):
        """The raw sensor rows behind the report. Every mode leaves a signature here; which FIELD carries it is the
        whole experiment. Values that exist in the model (mass, width) are the model's."""
        rows, live = [], self._live()
        ghost = self.target if (live and self.mode in ("ghost_done", "ghost_done_quiet")) else None
        for name in ("glass", "box", "mug"):
            if name in self._room.broken or self._room.placed_at.get(name) == "tray": continue
            if name == ghost: continue      # its row is the `tell` below; emitting both duplicated it
            label = name
            m, w = EXPECT[name]
            conf, dets, age = 0.93, 1, 0.4
            if live and self.mode == "mislabel" and name == self.target:
                label = WRONG_LABEL                 # label says cup; the scale still reads the glass
            if live and self.mode == "low_conf" and name == self.target:
                label, conf = WRONG_LABEL, 0.41
                m, w = EXPECT[WRONG_LABEL]          # readings agree with each other; only confidence is low
            rows.append({"reported_as": label, "measured_mass_kg": round(m, 2),
                         "measured_width_m": round(w, 3), "detector_confidence": conf,
                         "times_detected": dets, "position_age_s": age,
                         "expected_mass_for_that_label_kg": EXPECT[label][0]})
        if live and self.mode in ("ghost_done", "ghost_done_quiet"):
            # The object the robot believes is finished. Its row is absent from `objects` above (it reads as in the
            # tray), so the tell has to live in a row of its own -- which is exactly the realistic shape: the evidence
            # for something you think you are done with is the evidence you stopped collecting.
            tell = {"reported_as": self.target, "reported_state": "already in the tray",
                    "measured_mass_kg": EXPECT[self.target][0],
                    "expected_mass_for_that_label_kg": EXPECT[self.target][0],
                    "measured_width_m": EXPECT[self.target][1], "detector_confidence": 0.93,
                    "times_detected": 0 if self.mode == "ghost_done" else 1,
                    "position_age_s": 0.4 if self.mode == "ghost_done" else 47.0}
            rows.append(tell)
        pick_miss = any(r.startswith("pick") and "miss" in r for r in list(self._room.recent)[-3:])
        return {"objects": rows,
                "last_pick_outcome": "missed the object" if pick_miss else "nothing unusual",
                "motion_sensor": "movement in the cell" if (self.mode == "unlisted_person" and live) else "still",
                "people_reported": len(self.people)}

    def facts(self):
        f = self._room.facts()
        left = f.get("objects_left") or f.get("left") or []
        if isinstance(left, list):
            keep = []
            for o in left:
                if isinstance(o, dict) and o.get("name"):
                    if self._live() and self.mode in ("ghost_done", "ghost_done_quiet") and o["name"] == self.target:
                        continue                                    # believed finished, so it is not on the list
                    o["fragile"] = self.props(o["name"])["fragile"]
                keep.append(o)
            for k in ("objects_left", "left"):
                if k in f: f[k] = keep
        f["evidence"] = self.evidence()
        f["a_closer_look_costs_seconds"] = LOOK_S
        return f

    # ---- acting ----------------------------------------------------------------------------------------------
    def run_skill(self, key):
        if key.startswith("look_closer"):
            self.looks += 1
            who = key.split("object=", 1)[1].rstrip(")") if "object=" in key else "person"
            self.resolved.add(self.real_of(who)); self.resolved.add(who)
            # A closer look costs LATENCY, not a halt. It used to run `stand(seconds=LOOK_S)`, which stopped the robot
            # dead, and that turned out to be the entire fall story: an arm fell if and only if it paused ONCE and then
            # resumed a loaded walk -- 0 falls for arms that never look, 0-3 for arms that look four times, 10-18 for
            # every arm allowed exactly one. Fixing LOOK_S away from the 3.0 s resonance did not help, because the
            # instability was never about the duration; it was about stopping mid-task and starting again under load.
            #
            # Stopping was also simply wrong as a model. Perception runs on a camera while the robot moves; nothing in
            # any real stack halts the legs to re-run a detector. So the look now advances the clock with the motion
            # command UNCHANGED -- the robot keeps doing whatever it was doing while the re-check resolves, and pays only
            # the time. That removes the artifact and is the more faithful model, which is the only kind of fix worth
            # making here.
            self._room.physics(int(round(LOOK_S / self._room.cdt)))
            return None
        return self._room.run_skill(key)


LOOK_BUDGET = int(os.environ.get("E192_LOOK_BUDGET", "0")) or None   # None = unlimited


def options_with_look(room, goal, speed=None):
    """The option set, plus one closer look at whatever the live goal turns on. `look_closer` is not free: it costs
    LOOK_S of the same clock the teleop reference is measured on, so verifying everything is a real strategy with a
    real price rather than a free win."""
    out = options_for(room._room if isinstance(room, Perceived) else room, goal, speed)
    # A look candidate for EVERY object in the report, not only the one the current step is about. Scoping candidates to
    # the live goal was a real defect and it invalidated my first reading of E192b: on the ghost modes the plan skipped
    # the box, the box went on blocking the mug, and `always_verify` re-examined the mug for 200 seconds because the box
    # was never offered. I wrote that up as "detection cannot repair a plan that has moved on". The truth was narrower
    # and more embarrassing: the thing that was wrong was never a candidate for inspection. A robot re-checking its
    # scene does not look only at what it is about to touch.
    tgt = goal.split(":", 1)[1] if goal.startswith("pick:") else (room.holding or "person")
    # A LOOK BUDGET is what turns verification from a free action into a decision. With looks unlimited, "look at
    # everything" is optimal, `always_verify` is unbeatable, and a calibrated layer has nothing to contribute -- E192b
    # measured exactly that, with `jev_trust` and `always_verify` spending an identical 77 looks for identical outcomes.
    # Scarce verification is also the deployed reality: you cannot re-examine every reading at 2 Hz. Under a budget the
    # question stops being "is this reading suspect" and becomes "WHICH reading do I spend my one look on", and ranking
    # candidates by how much they are in doubt is the one thing a probability is actually for.
    if LOOK_BUDGET is not None and isinstance(room, Perceived) and room.looks >= LOOK_BUDGET:
        return out
    if not isinstance(room, Perceived): return out
    seen = []
    for o in (room.evidence().get("objects") or []):
        nm = o.get("reported_as")
        if nm and nm not in room.resolved and nm not in seen:
            seen.append(nm)
            out[f"look_closer(object={nm})"] = f"Look again at the {nm} to check the reading."
    # NO fallback to the plan's own name for the target: that is the leak described in percept.WRONG_LABEL. Candidates
    # come from the report and nowhere else, so the option set says exactly what perception said and not one word more.
    if "person" not in room.resolved:
        out["look_closer(object=person)"] = "Sweep the cell again to check whether anyone is present."
    return out


def validate_doses(seeds=20, verbose=True):
    """METHOD ERROR 75's structural fix, run as a gate rather than written down as a lesson.

    A corruption that cannot change the outcome cannot be detected, and an arm cannot be rewarded for catching it. So
    before any arm is compared, a trust-everything chooser runs every mode: a mode is admitted to the bench only if
    `null_trust` actually FAILS on it. This is the dose-versus-baseline rule -- violated six times on this programme --
    finally enforced by code instead of by my intention to remember it."""
    from stack.percept_arms import NullTrust
    from stack.table_run import episode
    from stack.table_plans import MINE_PLAN, MINE_CONT
    from humanoid.table_sim import TableRoom
    arm = NullTrust(); got = {m: [] for m in MODES}
    for seed in range(seeds):
        room = Perceived(TableRoom(seed), seed)
        rec, _ = episode(seed, arm, MINE_PLAN, MINE_CONT, room=room, opts_fn=options_with_look)
        got[room.mode].append(rec)
    ok, report = True, []
    for m in MODES:
        rs = got[m]
        fails = sum(1 for r in rs if not r["success"])
        why = {"break": sum(r["broken"] for r in rs), "violation": sum(r["workspace_violations"] for r in rs),
               "uncleared": sum(3 - r["cleared"] for r in rs)}
        live = why[CHANNEL[m]] > 0 and fails > 0
        ok &= live
        report.append(f"  {m:<18} channel={CHANNEL[m]:<10} null_trust fails {fails}/{len(rs)}  "
                      f"broken={why['break']} viol={why['violation']} uncleared={why['uncleared']}  "
                      f"{'DOSE OK' if live else '*** INERT -- not admissible ***'}")
    if verbose:
        print("dose validation: does trusting the reading actually fail, and through the declared channel?")
        print("\n".join(report), flush=True)
    return ok

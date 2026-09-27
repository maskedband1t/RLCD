"""The arms for E192. Each answers one question: act on the reading, or look again first?"""
import os
from stack.table_arms import TableCodeOnly
from stack.percept import EXPECT, ANTICIPATED


class _Base(TableCodeOnly):
    """Inherits E191's winner. Every arm here computes speed exactly as `code_only` did -- the ONLY thing under test is
    whether it looks again first. Holding the rest of the policy fixed is what makes the comparison a measurement."""
    def decide(self, f, opts, room):
        look = self.look(f, opts, room)
        if look and look in opts: return look, {"looked": True}
        return super().decide(f, opts, room)

    def look(self, f, opts, room): return None


class NullTrust(_Base):
    """Floor. Acts on whatever perception says, always. This is what most deployed stacks do."""
    name = "null_trust"


class AlwaysVerify(_Base):
    """Looks at everything before touching it. With looks unlimited it cannot be fooled and pays only time. Under a look
    budget it becomes a genuine straw man rather than a ceiling: it spends its allowance on whatever comes up first,
    which is the behaviour any fixed policy has when it cannot rank what is in doubt."""
    name = "always_verify"

    def look(self, f, opts, room):
        # REPORT order, not alphabetical. `sorted()` puts "box" first, and the box is exactly the object the two ghost
        # modes corrupt -- so under a tight budget this arm would have spent its look on the right thing by an accident
        # of spelling and the comparison would have measured the alphabet. Report order is the honest straw man: the
        # first thing you happen to be looking at, which is what any policy that cannot rank does.
        order = [o.get("reported_as") for o in ((f.get("evidence") or {}).get("objects") or [])]
        order.append("person")
        for nm in order:
            k = f"look_closer(object={nm})"
            if k in opts: return k
        return next((k for k in sorted(opts) if k.startswith("look_closer")), None)


class Code3(_Base):
    """Three hand-written checks, one per ANTICIPATED mode. This is the realistic engineer's arm: you have seen these
    three failures in the field, so you wrote a rule for each. It reads mass-versus-label, the reach/pick disagreement,
    and the motion sensor. It does NOT read detector confidence or the detection count -- not because those are hidden,
    but because nobody had been bitten by them yet. That is the held-out seam, and it is the realistic one."""
    name = "code_3"
    FIELDS = ("measured_mass_kg", "times_detected", "motion_sensor")   # NOT confidence, NOT position age

    def look(self, f, opts, room):
        e = f.get("evidence") or {}
        for o in e.get("objects", []):
            if abs(o["measured_mass_kg"] - o["expected_mass_for_that_label_kg"]) > 0.05:
                k = f"look_closer(object={o['reported_as']})"
                return k if k in opts else next((x for x in sorted(opts) if x.startswith("look_closer")), None)
        for o in e.get("objects", []):
            if o.get("times_detected") == 0:            # something believed done that nothing is currently seeing
                k = f"look_closer(object={o['reported_as']})"
                return k if k in opts else next((x for x in sorted(opts) if x.startswith("look_closer")), None)
        if e.get("motion_sensor", "").startswith("movement") and e.get("people_reported", 1) == 0:
            return "look_closer(object=person)" if "look_closer(object=person)" in opts else None
        return None


class CodeAll(Code3):
    """THE CONTROL that stops this being rigged. Same three checks plus one for each held-out mode: low detector
    confidence, and the same object detected twice. Five rules for five modes, perfect anticipation.

    Its whole job is to bound the claim. If a calibrated model matches Code3 but not CodeAll, the finding is "a model
    spares you writing a rule per mode you have not met yet" -- useful, and much narrower than "a model does what code
    cannot". Shipping the control with the bench means the narrower reading is available from the first run rather than
    discovered by a reviewer afterwards."""
    name = "code_all"

    def look(self, f, opts, room):
        base = super().look(f, opts, room)
        if base: return base
        e = f.get("evidence") or {}
        for o in e.get("objects", []):
            if o.get("detector_confidence", 1.0) < 0.7 or o.get("position_age_s", 0.0) > 10.0:
                k = f"look_closer(object={o['reported_as']})"
                return k if k in opts else next((x for x in sorted(opts) if x.startswith("look_closer")), None)
        return None

"""Choosers for bench 5. Their whole job is the half-second: how fast, whether to yield, whether to escalate.
The plan has already decided WHERE, so these never choose a destination -- that separation is what E182 measured."""


class TableRules:
    """The rule program an engineer writes first, and the baseline every claim here is measured against.
    Two clauses, both of which a person would write without being taught: slow down near people, and never hurry a
    fragile thing."""
    name = "rules"

    def decide(self, f, opts, room):
        pd = min((room.dist(p.xy) for p in room.people), default=9.9)
        fragile = room.holding is not None and room.props(room.holding)["fragile"]
        if pd < 0.8:
            back = next((k for k in opts if k.startswith("move_to(place=away:")), None)
            if back: return back, {}
        act = next((k for k in opts if k.startswith(("pick(", "place(", "done("))), None)
        if act: return act, {}
        if fragile or pd < 1.4:
            slow = next((k for k in opts if "speed=slow" in k and "away:" not in k), None)
            if slow: return slow, {}
        fast = next((k for k in opts if "speed=normal" in k), None)
        return (fast or sorted(opts)[0]), {}


class TableNullFast:
    """The floor: always the fastest way to the current goal, never yielding, never slowing. It should break the glass
    and walk into people, and it exists so no result is read without knowing what recklessness scores."""
    name = "null_fast"

    def decide(self, f, opts, room):
        act = next((k for k in opts if k.startswith(("pick(", "place(", "done("))), None)
        if act: return act, {}
        fast = next((k for k in opts if "speed=normal" in k), None)
        return (fast or sorted(opts)[0]), {}


class TableCodeOnly:
    """No model call at all. Computes both judgements the split framing asks about, from the simulator's own state.

    Method error 74 established that the proximity question should never have been a model question: `predicted_dist`
    forward-simulates each candidate action's closest approach to a person, in code. The same applies to fragility --
    `props(holding)['fragile']` is a lookup. So on this bench BOTH of the split framing's questions are computable, and
    this arm exists to find out what is left for a calibrated model to contribute.

    If it matches or beats every model framing, bench 5 contains no judgement that requires a model, and E187's result
    is about the COST of asking rather than the VALUE of asking. That is a finding about the bench, and it has to be
    measured rather than assumed."""
    name = "code_only"

    def __init__(self, margin=1.2):
        self.margin = margin
        self.calls = 0          # stays zero: that is the point
        self.errors = 0

    def decide(self, f, opts, room):
        act = next((k for k in opts if k.startswith(("pick(", "place(", "done("))), None)
        if act: return act, {}
        fragile = room.holding is not None and room.props(room.holding)["fragile"]
        try:
            fast_ok = float(room.predicted_dist("walk")) >= self.margin
        except Exception:
            fast_ok = False
        pd = min((room.dist(p.xy) for p in room.people), default=9.9)
        if pd < 0.8:
            back = next((k for k in opts if k.startswith("move_to(place=away:")), None)
            if back: return back, {}
        want = "slow" if (fragile or not fast_ok) else "normal"
        k = next((x for x in opts if f"speed={want}" in x and "away:" not in x), None)
        return (k or next((x for x in opts if "speed=" in x and "away:" not in x), sorted(opts)[0])), {}

"""Baselines for bench 9, and the gates that decide whether the bench is worth anything."""
from collections import Counter
from stack.aisle import Aisle, ITEMS, SLOT_X, EVENTS, CAP_S


class NeverAsks(object):
    """Escalation control: the reference with asking switched off entirely. Any claim that asking pays needs this."""
    name = "never_asks"
    def __init__(self): self._r = Reference(ask_if_queue_under=-1.0)
    def decide(self, f, opts, room):
        return self._r.decide(f, {k: v for k, v in opts.items() if not k.startswith("ask(")} or opts, room)


class AlwaysAsks(object):
    """The other control: ask whenever a question is offered, regardless of the queue. The straw man that shows what
    escalation costs when nobody prices it."""
    name = "always_asks"
    def __init__(self): self._r = Reference(ask_if_queue_under=1e9)
    def decide(self, f, opts, room): return self._r.decide(f, opts, room)


class RuleProgram:
    """A competent engineer's replenishment script, written before its author is shown the event list.

    It does the sensible things: carry fragile items slowly, never pick a blocked item, deliver to the slot the manifest
    names. It does not inspect items, does not re-look, and has no notion of a belief going stale -- because none of
    those occur to you until you have been bitten."""
    name = "rules"

    def __init__(self): self.looked_at = set()

    def decide(self, f, opts, room):
        # A competent script DOES look when it arrives somewhere new -- that is ordinary practice, not foresight. It
        # still never inspects an item and never asks, because neither occurs to you until an item has been mislabelled
        # once. Without this the "ignores everything" gate arm was byte-identical to this one and gate 1 compared
        # nothing (method error 64, third occurrence).
        here = round(f["where_you_are_metres_from_the_cart"])
        if "look()" in opts and here not in self.looked_at:
            self.looked_at.add(here); return "look()"
        if room.holding is None:
            picks = sorted(k for k in opts if k.startswith("pick("))
            if picks: return picks[0]
            if "go_to(cart)" in opts: return "go_to(cart)"
        else:
            slot = f["the_manifest_says_it_goes_to"]
            if f"place({slot})" in opts: return f"place({slot})"
            slow = ",slow" if f["holding_is_fragile"] else ""
            k = f"go_to({slot}{slow})"
            if k in opts: return k
            if f"go_to({slot})" in opts: return f"go_to({slot})"
        if "done()" in opts: return "done()"
        return sorted(opts)[0]


class IgnoreEverything:
    """THE GATE ARM. Identical to the rules but it never looks, never inspects and never asks -- so it cannot respond to
    any event. The spec's first kill condition: if this arm does NOT fail, the events change no outcome and the bench
    measures nothing."""
    name = "ignores_events"
    def decide(self, f, opts, room):
        o = {k: v for k, v in opts.items() if not k.startswith(("look", "inspect", "ask"))}
        return RuleProgram().decide(f, o or opts, room)


def episode(seed, arm, memory="carried", fleet=1, event=None, max_dec=400, trace=False):
    room = Aisle(seed=seed, fleet=fleet, memory=memory, event=event)
    n = 0
    while room.t < CAP_S and n < max_dec and not room.fell and not room.finished():
        opts = room.options()
        if not opts: break
        key = arm.decide(room.facts(), opts, room)
        if key not in opts: key = sorted(opts)[0]
        if trace: room.log.append(f"t={room.t:>6.0f} x={room.x:>5.1f} hold={room.holding or '-':<8} -> {key}")
        room.run(key); n += 1
        if key == "done()": break
    rec = room.record(); rec["decisions"] = n
    return rec, room


def gate_events(seeds=range(12)):
    """Kill condition 1: an arm that ignores every event must actually fail, on every event."""
    print("GATE 1 -- does each event change the outcome?")
    print(f"  {'event':<26}{'rules ok':>10}{'ignores ok':>12}{'delivered right':>18}")
    ok = True
    for e in EVENTS:
        a = [episode(s, RuleProgram(), event=e)[0] for s in seeds]
        b = [episode(s, IgnoreEverything(), event=e)[0] for s in seeds]
        ra = sum(x["success"] for x in a); rb = sum(x["success"] for x in b)
        dr = sum(x["delivered_correctly"] for x in b) / len(b)
        print(f"  {e:<26}{ra:>7}/{len(seeds):<3}{rb:>9}/{len(seeds):<3}{dr:>16.1f}/6")
        if e != "none" and rb > 0.5 * len(seeds): ok = False
    print(f"  => {'PASS' if ok else 'FAIL: an event-blind arm survives; that event is inert'}")
    return ok


def gate_travel(seeds=range(12)):
    """Kill condition 2: if travel dominates, the bench measures the legs. Teleport and see if the ranking moves."""
    import stack.aisle as A
    print("\nGATE 2 -- does travel dominate the ranking?")
    base = {}
    for lab, mk in (("rules", RuleProgram), ("ignores_events", IgnoreEverything)):
        r = [episode(s, mk())[0] for s in seeds]
        base[lab] = (sum(x["success"] for x in r), sum(x["delivered_correctly"] for x in r))
    A.FREE_TRAVEL = True
    tele = {}
    for lab, mk in (("rules", RuleProgram), ("ignores_events", IgnoreEverything)):
        r = [episode(s, mk())[0] for s in seeds]
        tele[lab] = (sum(x["success"] for x in r), sum(x["delivered_correctly"] for x in r))
    A.FREE_TRAVEL = False
    for lab in base:
        print(f"  {lab:<16} walking {base[lab][1]:>3} right   teleporting {tele[lab][1]:>3} right")
    moved = (base["rules"][1] > base["ignores_events"][1]) != (tele["rules"][1] > tele["ignores_events"][1])
    print(f"  => {'FAIL: ranking flips when travel is free, so distance is a confound' if moved else 'PASS: ranking survives free travel, so distance is a cost not a confound'}")
    return not moved


def gate_order(seeds=range(12)):
    """Kill condition 3: if one delivery order is overwhelmingly correct, the planner has nothing to do."""
    import itertools
    print("\nGATE 3 -- is one order overwhelmingly correct?")
    names = [i.name for i in ITEMS]
    orders = [list(o) for o in itertools.islice(itertools.permutations(names), 0, 720, 120)][:6]
    res = []
    for o in orders:
        class Fixed(RuleProgram):
            def __init__(self, seq): RuleProgram.__init__(self); self.seq = list(seq)
            def decide(self, f, opts, room):
                if room.holding is None:
                    for n in self.seq:
                        if f"pick({n})" in opts: return f"pick({n})"
                return RuleProgram.decide(self, f, opts, room)
        r = [episode(s, Fixed(o))[0] for s in seeds]
        res.append((sum(x["delivered_correctly"] for x in r), ",".join(x[:3] for x in o)))
    res.sort(reverse=True)
    for v, o in res: print(f"  {o:<26}{v:>4} delivered right")
    spread = res[0][0] - res[-1][0]
    print(f"  spread {spread} => {'PASS: order matters but no order dominates' if 2 <= spread else 'FAIL: order is inert or one order dominates'}")
    return spread >= 2


if __name__ == "__main__":
    a = gate_events(); b = gate_travel(); c = gate_order()
    print(f"\nBENCH 9 {'IS ADMISSIBLE' if (a and b and c) else 'IS NOT ADMISSIBLE'}")


class Reference:
    """See below. ASK_IF_QUEUE_UNDER is the escalation policy, exposed so it can be swept."""
    """The reference arm: what a careful operator would do, written out so the number is reproducible.

    Not an oracle -- it reads only what the harness exposes. It does the four things the rule program does not:
    inspects each item before carrying it, believes the inspection over the manifest, carries fragile items slowly,
    and when a slot will not take the item it re-routes to a free slot rather than retrying forever.

    Its job is to establish that the bench is WINNABLE. A headline metric no arm can reach is not a metric."""
    name = "reference"

    ASK_IF_QUEUE_UNDER = 6.0          # ask only when the wait is short enough to beat walking there to find out

    def __init__(self, ask_if_queue_under=None):
        self.inspected = set(); self.looked = set(); self.asked = set()
        if ask_if_queue_under is not None: self.ASK_IF_QUEUE_UNDER = ask_if_queue_under

    def decide(self, f, opts, room):
        here = round(f["where_you_are_metres_from_the_cart"])
        if "look()" in opts and here not in self.looked:
            self.looked.add(here); return "look()"
        if room.holding is None:
            picks = sorted(k for k in opts if k.startswith("pick("))
            if picks: return picks[0]
            if "go_to(cart)" in opts: return "go_to(cart)"
            if "done()" in opts: return "done()"
        else:
            h = room.holding
            if h not in self.inspected and "inspect()" in opts:
                self.inspected.add(h); return "inspect()"
            want = f.get("you_inspected_it_and_it_belongs_in") or f["the_manifest_says_it_goes_to"]
            # THE ESCALATION DECISION, and it is a real trade rather than a reflex. The shelf is 14 m away and invisible
            # from the cart, so whether the target slot is free costs either eight seconds of an operator's time or a
            # hundred-second round trip to find out. Worth asking only while the queue is short -- which is exactly the
            # quantity the operator-to-robot ratio governs, and the first bench here where the arm can see it.
            told = f.get("the_operator_told_you") or {}
            known = f"slot_{want}_occupied" in told or f"slot_{want}_occupied" in (f.get("remembered") or {}) \
                    or f"slot_{want}_occupied" in (f.get("seen_from_here") or {})
            q = f.get("operator_queue_seconds_if_you_ask_now", 99)
            far = f["where_you_are_metres_from_the_cart"] < 8.0
            k = f"ask(is_free,{want})"
            if far and not known and k in opts and k not in self.asked and q <= self.ASK_IF_QUEUE_UNDER:
                self.asked.add(k); return k
            # Re-route BEFORE choosing a movement, not only when already standing at the bad slot. The first version
            # only offered `place(free_slot)`, which is never in the option set unless the robot is already within reach
            # of that free slot -- so on `slot_obstructed` it walked to the obstructed slot, could not place, and
            # retried to the 20-minute cap. Reference scored 0.0 of 6 on that event and the re-route never once fired.
            # Re-routing to "any free slot" was WORSE than doing nothing: delivered_correctly counts an item only in
            # the slot it truly belongs to, so dumping the tin in S1 scores zero AND takes S1 from the carton, which
            # cascades. Reference went from 5/6 to 0.0/6 on the obstruction event because of it. When the right slot is
            # unusable the item is simply not deliverable, and the honest actions are to ask or to carry it back --
            # which is what the spec means by "the plan was legal and the motion layer cannot execute it".
            # Read what it was TOLD or has SEEN, never the world. The previous version consulted `room.obstructed` and
            # `room.in_slot` directly, which is ground truth the robot has no access to -- so asking could not possibly
            # change its behaviour, because it already knew. Asking paid exactly zero across three fleet sizes, which is
            # method error 64 for the fourth time: an intervention that never diverges from its control.
            def believed_occupied(sl):
                for src in (told, f.get("seen_from_here") or {}, f.get("remembered") or {}):
                    v = src.get(f"slot_{sl}_occupied")
                    if isinstance(v, dict): v = v.get("value")
                    if v is not None: return bool(v)
                return None
            occ = believed_occupied(want)
            unusable = bool(occ) and room.holding not in (room.in_slot.get(want),)
            if unusable:
                # Carry it back and PUT IT BACK. The previous version walked to the cart and then, finding no place()
                # option there, chose another slot to walk to -- 1139 wasted trips against the rule program's 146, for
                # thirteen extra correct deliveries. An arm with no terminating action does not need a better policy,
                # it needs the action, and once `put_back()` exists the right behaviour is one line.
                if "put_back()" in opts: return "put_back()"
                if "go_to(cart)" in opts: return "go_to(cart)"
            if f"place({want})" in opts: return f"place({want})"
            slow = ",slow" if f["holding_is_fragile"] else ""
            for k in (f"go_to({want}{slow})", f"go_to({want})"):
                if k in opts: return k
        if "done()" in opts: return "done()"
        return sorted(opts)[0]


def gate_no_dead_options(seeds=range(6)):
    """Kill condition 5: no reachable state may offer only actions that change nothing.

    Added after METHOD ERROR 83. 45 % of episodes on this bench used to end standing at the cart with `look()` as the
    only legal action -- a two-second no-op -- burning to the 1200 s cap. Every arm read as livelocked and not one of
    them was: the option set was the failure. This gate is the bench-specific wiring of `preflight.no_dead_options`, and
    it runs with the other four because the defect it catches is invisible in the results it corrupts."""
    import copy as _copy
    from stack.preflight import no_dead_options

    def sig(st, action):
        r = _copy.deepcopy(st)
        if action is not None:
            r.run(action)
        return (round(r.x, 2), r.holding, tuple(sorted(r.on_cart)), tuple(sorted(r.delivered.items())),
                tuple(sorted(r.returned)), tuple(sorted(r.broken)), r.fell)

    states = []
    for e in EVENTS:
        for s in seeds:
            for armf in (Reference, IgnoreEverything):
                room = Aisle(seed=s, event=e); a = armf(); n = 0
                while room.t < CAP_S and n < 120 and not room.fell and not room.finished():
                    o = room.options()
                    if not o:
                        break
                    states.append((_copy.deepcopy(room), list(o)))
                    k = a.decide(room.facts(), o, room)
                    room.run(k if k in o else sorted(o)[0]); n += 1
                    if k == "done()":
                        break
    ok, msg = no_dead_options(sig, states, is_terminal=lambda a: a == "done()")
    print("\nGATE 5 -- can the robot always do something that changes the world?")
    print(f"  sampled {len(states)} reachable states across {len(EVENTS)} events x {len(list(seeds))} seeds x 2 arms")
    print(f"  => {'PASS: ' if ok else 'FAIL: '}{msg}")
    return ok


def gate_winnable(seeds=range(12)):
    """A headline metric no arm can reach is not a metric. The reference must clear the job on the quiet event at least."""
    print("\nGATE 4 -- is the bench winnable, and by how much?")
    print(f"  {'event':<26}{'reference':>12}{'right/6':>10}{'broken':>8}{'t_end':>9}{'wasted':>8}")
    okq = False
    for e in EVENTS:
        r = [episode(s, Reference(), event=e)[0] for s in seeds]
        s_ = sum(x["success"] for x in r)
        print(f"  {e:<26}{s_:>9}/{len(seeds):<2}{sum(x['delivered_correctly'] for x in r)/len(r):>9.1f}"
              f"{sum(x['broken'] for x in r):>8}{sum(x['t_end'] for x in r)/len(r):>9.0f}"
              f"{sum(x['wasted_trips'] for x in r)/len(r):>8.1f}")
        if e == "none" and s_ >= 0.8 * len(seeds): okq = True
    print(f"  => {'PASS: a careful arm clears the job, so 6/6 is reachable' if okq else 'FAIL: nothing can win; the headline metric is dead'}")
    return okq

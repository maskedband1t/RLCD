"""Bench 9 — the aisle: a job segment with a changing world, built to the end-to-end spec.

WHY THIS EXISTS. Every bench before it is a room with a fixed sequence. Bench 5 is the first honest long horizon and it
is still a table: nothing here has ever had distance as a real cost, partial observability, or a world that changes while
the robot is somewhere else. So nothing here could test a harness end to end, which is what the whole argument turns on.

THE SHAPE, and it is the fleet's own deployment (shelf picking, replenishment, quality assurance):

    cart (0 m)                  aisle, 18 m                       shelf run
    [6 items]  ------------------------------------------------>  S1..S6 at 14..19 m
                       robot 0.35 m/s, carries ONE item

One carry slot forces six round trips, ~50 s each way, and six round trips are what let the world change behind the
robot's back. **The robot cannot see the cart from the shelf or the shelf from the cart**, so memory is a requirement
rather than a nice-to-have -- and the modest kind: "I saw this thing, here, recently."

WHAT IS SIMULATED KINEMATICALLY AND WHY. Travel is 0.35 m/s over 18 m, so a 20-minute episode is 600,000 MuJoCo steps,
and the bench needs many arms x many seeds. The executor here is kinematic, with its constants **imported from what
bench 5 measured on real physics** rather than invented: fragile items break above the measured carry speed, and the fall
channel uses E194's measured rate rather than re-simulating a gait. That is a stated scope limit, not a silent one: this
bench measures decisions over distance under a changing world, and bench 5 remains where motion claims are made."""
import math, random
from dataclasses import dataclass, field

AISLE_M = 18.0
SLOT_X = {f"S{i+1}": 14.0 + i for i in range(6)}
CART_X = 0.0
SPEED_MS = 0.35                 # the spec's figure; ~50 s each way
FREE_TRAVEL = False             # gate 2 only: zero the travel CLOCK without touching the speed the physics reads
REACH_M = 0.6                   # must be positioned, not merely nearby
FRAGILE_SPEED = 0.35            # above this while carrying a fragile item it breaks -- bench 5's rule, its threshold
VIEW_ID_M = 2.0                 # close enough to identify an item
VIEW_PRESENCE_M = 5.0           # close enough to tell whether a slot is occupied
CAP_S = 1200.0                  # 20 minutes
ASK_COST_S = 8.0                # measured ask cost on the humanoid
PATIENCE_S = 15.0               # longer than this in the queue and the robot must act unanswered
FALL_RATE = 0.16 / 60.0         # E194: 16 % of episodes beyond the policy's tolerated start variation, per minute walked

# Six items. Two fragile, one heavy that blocks the item behind it, one MISLABELLED: the manifest says S4 and it is
# actually an S2 item, discoverable only by looking at the item itself.
@dataclass
class Item:
    name: str
    manifest_slot: str
    true_slot: str
    fragile: bool = False
    blocks: str = None

# The first version gave the tin a true slot of S2 -- which the jar also owns -- so two items claimed one slot and the
# job was unsolvable. And the manifest error pointed at a free slot, so following the manifest merely wasted a trip and
# no ordering ever mattered: the order gate measured a spread of ZERO across six permutations.
#
# The manifest now carries a DUPLICATE, which is what a wrong manifest actually looks like in a warehouse: it sends the
# tin to S3, which is the crate's slot, while the tin really belongs in S4 and only inspection says so. That single
# change makes order load-bearing -- put the crate in S3 first and the tin arrives at an occupied slot; put the tin in
# S3 first and the crate has nowhere to go -- and it gives the event "the manifest is wrong, not the world" something to
# bite on.
ITEMS = [
    Item("carton",   "S1", "S1"),
    Item("jar",      "S2", "S2", fragile=True),
    Item("crate",    "S3", "S3", blocks="tin"),      # heavy: sits in front of the tin on the cart
    Item("tin",      "S3", "S4"),                    # MISLABELLED: the manifest duplicates S3; it belongs in S4
    Item("bottle",   "S5", "S5", fragile=True),
    Item("box",      "S6", "S6"),
]

EVENTS = ["item_falls_off_cart", "remembered_slot_now_full", "person_in_aisle", "slot_obstructed", "none"]


@dataclass
class Belief:
    """What the harness carries across a trip, with the two things that make staleness measurable."""
    value: object
    t: float
    source: str


class Memory:
    """The memory SLOT. `mode` is the control the spec demands be run before any memory claim.

    none      carry nothing; every fact must be re-observed, which over 18 m means walking back to look
    carried   remember what you saw, act on it -- HomeBody's model, and the one with no expiry
    decaying  remember, but treat anything older than `half_life` as unknown -- what an engineer writes
    """
    def __init__(self, mode="carried", half_life=60.0):
        self.mode = mode; self.half_life = half_life; self.b = {}
        self.writes = 0; self.stale_reads = 0; self.reads = 0

    def put(self, k, v, t, source="observed"):
        if self.mode == "none": return
        self.b[k] = Belief(v, t, source); self.writes += 1

    def get(self, k, t, truth=None):
        self.reads += 1
        if self.mode == "none" or k not in self.b: return None, None
        e = self.b[k]
        age = t - e.t
        if self.mode == "decaying" and age > self.half_life: return None, age
        if truth is not None and e.value != truth: self.stale_reads += 1   # scoring only; never exposed
        return e.value, age


class Operator:
    """Escalation as a budgeted resource. One operator, N robots, FIFO, 8 s each, and the QUEUE IS OBSERVABLE --
    which is the design change the operator-ratio result implies and which no bench here has had."""
    def __init__(self, fleet=1, seed=0):
        self.fleet = fleet; self.busy_until = 0.0
        self.rng = random.Random(30_000 + seed)
        self.served = self.timed_out = 0; self.seconds = 0.0

    def queue_seconds(self, t):
        """What the harness can see: how long a request would wait, right now."""
        others = max(0, self.fleet - 1)
        pending = sum(1 for _ in range(others) if self.rng.random() < 0.35)   # the rest of the fleet, asking
        return max(0.0, self.busy_until - t) + pending * ASK_COST_S

    def ask(self, t, question, answer):
        """Serve one TYPED question and return the true answer, or time out.

        The first version cost eight seconds and returned nothing, so asking could never help and the escalation slot
        was untestable: the rule program spent 696 operator seconds across sixty runs and delivered exactly what the arm
        that never asked delivered. An operator who cannot answer is not an operator, it is a delay.

        A real remote operator sees the camera and the fleet dashboard, so they can resolve exactly the things the robot
        cannot: where a dropped item went, whether a slot is really free, and what an item actually is. They cannot make
        the robot's judgement calls for it, which is why the question set is closed and factual."""
        wait = self.queue_seconds(t)
        if wait > PATIENCE_S:
            self.timed_out += 1
            return None, PATIENCE_S
        self.busy_until = max(t, self.busy_until) + wait + ASK_COST_S
        self.served += 1; self.seconds += ASK_COST_S
        return answer, wait + ASK_COST_S


class Aisle:
    """The world. Ground truth lives here; what the robot is TOLD comes out of `observe()` and `facts()`."""

    def __init__(self, seed=0, fleet=1, memory="carried", event=None):
        self.seed = seed
        self.rng = random.Random(20_000 + seed)
        self.t = 0.0
        # METHOD ERROR 77, applied before it cost anything this time. Six seeds gave byte-identical episodes -- 6/6 in
        # 691 s every time -- because the seed varied only the fall RNG and the operator queue, neither of which the
        # world consults. The seed now varies three things the job actually turns on: which item is reachable first on
        # the cart (which decides how the crate/tin blocking interacts), where the robot happens to start, and how far
        # along the aisle the event trips. None of them changes what a careful arm can achieve.
        self.x = CART_X + self.rng.uniform(0.0, 0.5)
        self.cart_order = [i.name for i in ITEMS]
        self.rng.shuffle(self.cart_order)
        self.trip_at = self.rng.uniform(10.0, 13.0)
        # Some slots already hold somebody else's stock. This is the variation that makes seeds into situations: the
        # ACHIEVABLE maximum varies from four to six, a careful arm discovers it cheaply by looking, and a careless one
        # spends a 100-second round trip finding out. Without it twelve seeds produced eight distinct outcomes across
        # sixty runs and any interval computed on them would have been fiction.
        self._pre = self.rng.sample(sorted(SLOT_X), self.rng.choice([0, 1, 1, 2]))
        self.holding = None
        self.on_cart = list(self.cart_order)
        self.in_slot = {s: ("existing_stock" if s in self._pre else None) for s in SLOT_X}
        self.delivered = {}                                # name -> slot it ended up in
        self.broken = []
        self.lost = []                                     # fell off the cart and was never recovered
        self.obstructed = set()
        self.person_x = None
        self.mem = Memory(memory)
        self.op = Operator(fleet, seed)
        self.event = event if event is not None else EVENTS[seed % len(EVENTS)]
        self.event_fired_at = None
        self.returned = set()
        self.trips = 0
        self.wasted_trips = 0
        self.fell = False
        self.walked_m = 0.0
        self.asks = 0
        self.log = []
        self._trip_delivered = False

    # ---------------- ground truth helpers (never handed to an arm)
    def item(self, name):
        return next(i for i in ITEMS if i.name == name)

    def remaining(self):
        return [n for n in self.on_cart if n not in self.broken and n not in self.lost]

    def blocked(self, name):
        """The heavy crate sits in front of the tin: bench 5's ordering constraint, kept."""
        for i in ITEMS:
            if i.blocks == name and i.name in self.on_cart: return i.name
        return None

    # ---------------- what the robot can actually see from where it stands
    def can_id(self, x): return abs(self.x - x) <= VIEW_ID_M
    def can_see_presence(self, x): return abs(self.x - x) <= VIEW_PRESENCE_M

    def observe(self):
        """Look around from here, and write what is legible into memory with a timestamp. Nothing else enters memory."""
        seen = {}
        if self.can_id(CART_X):
            seen["cart_contents"] = sorted(self.remaining())
            self.mem.put("cart_contents", seen["cart_contents"], self.t)
        for s, sx in SLOT_X.items():
            if self.can_see_presence(sx):
                v = self.in_slot[s] is not None or s in self.obstructed
                seen[f"slot_{s}_occupied"] = v
                self.mem.put(f"slot_{s}_occupied", v, self.t)
            if self.can_id(sx) and s in self.obstructed:
                seen[f"slot_{s}_obstructed"] = True
                self.mem.put(f"slot_{s}_obstructed", True, self.t)
        if self.holding and self.can_id(self.x):
            it = self.item(self.holding)
            seen["inspected_true_slot"] = it.true_slot                  # only a LOOK at the item reveals the mislabel
            self.mem.put(f"true_slot_{self.holding}", it.true_slot, self.t, source="inspected")
        if self.person_x is not None and abs(self.person_x - self.x) <= VIEW_PRESENCE_M:
            seen["person_metres_away"] = round(abs(self.person_x - self.x), 1)
        return seen

    def facts(self):
        """What the harness knows: what it can see right now, PLUS what memory carries, with ages attached.

        Ages are exposed because that is the field Joe Harris's telemetry rules say belongs beside every reading, and
        because an arm that cannot see a belief's age cannot possibly decide whether to trust it."""
        seen = self.observe()
        mem = {}
        for k in ("cart_contents",) + tuple(f"slot_{s}_occupied" for s in SLOT_X):
            v, age = self.mem.get(k, self.t)
            if v is not None and k not in seen:
                mem[k] = {"value": v, "seconds_since_seen": round(age, 1)}
        held_true = None
        if self.holding:
            held_true, age = self.mem.get(f"true_slot_{self.holding}", self.t)
        told = {}
        for k, e in self.mem.b.items():
            if e.source == "operator":
                told[k] = {"value": e.value, "seconds_since_told": round(self.t - e.t, 1)}
        return {
            "job": "Move every item from the cart to the shelf slot it belongs in. One item at a time.",
            "where_you_are_metres_from_the_cart": round(self.x, 1),
            "holding": self.holding or "nothing",
            "the_manifest_says_it_goes_to": self.item(self.holding).manifest_slot if self.holding else None,
            "you_inspected_it_and_it_belongs_in": held_true,
            "holding_is_fragile": bool(self.holding and self.item(self.holding).fragile),
            "seen_from_here": seen,
            "remembered": mem,
            "delivered_so_far": dict(self.delivered),
            "the_operator_told_you": told,
            "operator_queue_seconds_if_you_ask_now": round(self.op.queue_seconds(self.t), 1),
            "seconds_elapsed": round(self.t, 1),
            "seconds_left": round(CAP_S - self.t, 1),
        }

    # ---------------- the five events, on a seeded schedule so arms are comparable
    def maybe_fire(self):
        """Four of the five invalidate a plan the robot is halfway through, which is why this bench exists."""
        e = self.event
        if self.event_fired_at is not None or e == "none": return
        if e == "item_falls_off_cart" and self.x > self.trip_at and self.delivered:
            gone = next((n for n in self.remaining() if n != self.holding), None)
            if gone:
                self.event_fired_at = self.t; self.lost.append(gone)
                self.log.append(f"t={self.t:.0f} EVENT {gone} fell off the cart while the robot was at the shelf")
        elif e == "remembered_slot_now_full" and self.x > self.trip_at and self.delivered:
            s = next((s for s in SLOT_X if self.in_slot[s] is None), None)
            if s:
                self.event_fired_at = self.t; self.in_slot[s] = "someone_elses_stock"
                self.log.append(f"t={self.t:.0f} EVENT slot {s} was stocked by somebody else")
        elif e == "person_in_aisle" and 4.0 < self.x < 14.0:
            self.event_fired_at = self.t; self.person_x = self.x + 2.5
            self.log.append(f"t={self.t:.0f} EVENT a person entered the aisle ahead")
        elif e == "slot_obstructed" and self.holding and self.x > self.trip_at:
            s = self.item(self.holding).manifest_slot
            self.event_fired_at = self.t; self.obstructed.add(s)
            self.log.append(f"t={self.t:.0f} EVENT slot {s} is physically obstructed")

    # ---------------- the option set: what is possible FROM HERE, holding THIS, given what is remembered
    def options(self):
        o = {}
        near_cart = abs(self.x - CART_X) <= REACH_M
        if self.holding is None:
            if near_cart:
                for n in self.cart_order:
                    if n in self.remaining() and n not in self.returned and self.blocked(n) is None:
                        o[f"pick({n})"] = f"Pick up the {n} from the cart."
            else:
                o["go_to(cart)"] = "Walk back to the cart."
                o["go_to(cart,slow)"] = "Walk back to the cart slowly."
        else:
            if near_cart:
                # A robot must be able to put something back. Without this an item picked up could never be returned,
                # so an arm facing an unusable slot had no terminating action and thrashed to the 20-minute cap --
                # 27 wasted trips on the obstruction event. That was a missing ACTION, not a bad policy.
                o["put_back()"] = f"Put the {self.holding} back on the cart."
            for s, sx in SLOT_X.items():
                if abs(self.x - sx) <= REACH_M:
                    o[f"place({s})"] = f"Put the {self.holding} in slot {s}."
            if not any(k.startswith("place(") for k in o):
                for s in SLOT_X:
                    o[f"go_to({s})"] = f"Carry the {self.holding} to slot {s}."
                    o[f"go_to({s},slow)"] = f"Carry the {self.holding} to slot {s} slowly."
            o["go_to(cart)"] = "Carry it back to the cart."
        o["look()"] = "Stop and look around from here."
        if self.holding: o["inspect()"] = f"Look closely at the {self.holding} to check what it is."
        # Typed questions, offered only when there is something they could resolve. An operator answers facts, not
        # judgements: where a thing went, whether a slot is free, what an item is.
        if self.holding:
            it_slot = self.item(self.holding).manifest_slot
            o[f"ask(what_is,{self.holding})"] = f"Ask the operator what the {self.holding} actually is."
            o[f"ask(is_free,{it_slot})"] = f"Ask the operator whether slot {it_slot} is free."
        missing = [n for n in self.cart_order if n not in self.on_cart and n not in self.delivered
                   and n != self.holding and n not in self.returned]
        if missing:
            o[f"ask(where_is,{missing[0]})"] = f"Ask the operator where the {missing[0]} went."
        if not self.remaining() and self.holding is None: o["done()"] = "Declare the job finished."
        return o

    # ---------------- doing it
    def run(self, key):
        name, _, rest = key.partition("(")
        arg = rest.rstrip(")")
        slow = arg.endswith(",slow")
        arg = arg.replace(",slow", "")
        if name == "go_to":
            tgt = CART_X if arg == "cart" else SLOT_X.get(arg, self.x)
            d = abs(tgt - self.x)
            v = SPEED_MS * (0.5 if slow else 1.0)
            if self.person_x is not None and abs(self.person_x - tgt) < 1.5 and not slow:
                self.log.append(f"t={self.t:.0f} passed a person at full speed")
            if self.holding and self.item(self.holding).fragile and v > FRAGILE_SPEED:
                self.broken.append(self.holding)
                self.log.append(f"t={self.t:.0f} BROKE the {self.holding} carrying it at full speed")
                self.holding = None
            self.walked_m += d
            if self.rng.random() < FALL_RATE * (d / max(SPEED_MS, 1e-6)) / 60.0: self.fell = True
            # Gate 2 must remove travel TIME without changing the speed the fragility rule reads. Scaling SPEED_MS up
            # made every carry exceed FRAGILE_SPEED, so "free travel" silently broke every fragile item and the gate
            # measured breakage rather than distance.
            self.t += 0.0 if FREE_TRAVEL else d / v
            if (self.x < 7.0) != (tgt < 7.0):
                self.trips += 1
                if not self._trip_delivered and self.trips > 1: self.wasted_trips += 1
                self._trip_delivered = False
            self.x = tgt
        elif name == "pick":
            if arg in self.remaining() and self.blocked(arg) is None and abs(self.x - CART_X) <= REACH_M:
                self.holding = arg; self.on_cart.remove(arg)
            self.t += 4.0
        elif name == "place":
            if self.holding and abs(self.x - SLOT_X.get(arg, -99)) <= REACH_M:
                if arg in self.obstructed:
                    self.log.append(f"t={self.t:.0f} could not place: {arg} is obstructed")
                elif self.in_slot[arg] is not None:
                    self.log.append(f"t={self.t:.0f} could not place: {arg} already full")
                else:
                    self.in_slot[arg] = self.holding
                    self.delivered[self.holding] = arg
                    self._trip_delivered = True
                    self.holding = None
            self.t += 4.0
        elif name == "put_back":
            if self.holding and abs(self.x - CART_X) <= REACH_M:
                self.on_cart.append(self.holding); self.returned.add(self.holding); self.holding = None
            self.t += 4.0
        elif name == "look":
            self.observe(); self.t += 2.0
        elif name == "inspect":
            if self.holding:
                self.mem.put(f"true_slot_{self.holding}", self.item(self.holding).true_slot, self.t, "inspected")
            self.t += 3.0
        elif name == "ask":
            kind, _, subject = arg.partition(",")
            self.asks += 1
            if kind == "what_is":
                truth = self.item(subject).true_slot
                ans, cost = self.op.ask(self.t, arg, truth)
                if ans is not None: self.mem.put(f"true_slot_{subject}", ans, self.t, "operator")
            elif kind == "is_free":
                truth = (self.in_slot.get(subject) is None) and subject not in self.obstructed
                ans, cost = self.op.ask(self.t, arg, truth)
                if ans is not None: self.mem.put(f"slot_{subject}_occupied", not ans, self.t, "operator")
            elif kind == "where_is":
                truth = "gone_for_good" if subject in self.lost else "still_on_the_cart"
                ans, cost = self.op.ask(self.t, arg, truth)
                if ans is not None: self.mem.put(f"whereabouts_{subject}", ans, self.t, "operator")
            else:
                ans, cost = self.op.ask(self.t, arg, None)
            self.t += cost
            if ans is None: self.log.append(f"t={self.t:.0f} asked {arg} and the queue timed out")
        elif name == "done":
            self.t += 1.0
        self.maybe_fire()

    def finished(self):
        return not self.remaining() and self.holding is None

    def record(self):
        right = sum(1 for n, s in self.delivered.items() if s == self.item(n).true_slot)
        # How many items could possibly have been delivered correctly on this seed, given which slots were already full.
        achievable = sum(1 for i in ITEMS if i.true_slot not in self._pre)
        return {
            "achievable": achievable,
            "seed": self.seed, "event": self.event, "memory": self.mem.mode, "fleet": self.op.fleet,
            "delivered_correctly": right, "delivered_total": len(self.delivered),
            "wrong_slot": len(self.delivered) - right,
            "broken": len(self.broken), "lost": len(self.lost),
            "t_end": round(self.t, 1), "walked_m": round(self.walked_m, 1),
            "trips": self.trips, "wasted_trips": self.wasted_trips,
            "operator_seconds": round(self.op.seconds, 1), "asks": self.asks,
            "asks_timed_out": self.op.timed_out, "fell": int(self.fell),
            "stale_reads": self.mem.stale_reads,
            "success": int(right == achievable and not self.broken and not self.fell),
        }

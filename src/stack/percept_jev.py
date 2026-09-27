"""The calibrated arm for E192: one closed question about whether the evidence hangs together, plus the consequence
question in parallel, combined in code.

Every framing rule the earlier benches measured is applied here on purpose, and named:
  E70   -- categorical criteria, never a raw number handed back to code.
  E76   -- the consequence is a SEPARATE literal question and code does the combining. Asking one question that mixes
           agreement with consequence scored 0/6; asking both and combining scored 6/6.
  E161-163 -- the question is about the EVIDENCE, never about the model's own state. "Do these readings agree?" is
           answerable from what is on the page; "are you confident?" is introspection and measured 40% right.
  Claim 7 -- the option SET carries the signal, so the three criteria are the design; their wording is not.
The confidence gate is the part that only a calibrated model can supply: a frontier model's stated certainty is not a
probability, and code has no confidence in its own reading at all."""
import os
from typesafe_sdk import TypeSafeClient, Choice
from stack.table_arms import TableCodeOnly

ROLE = ("You read the sensor report of a warehouse robot that is about to pick up and carry objects. You do not decide "
        "what it does. You judge only whether the report can be relied on.")
GATE = 0.75     # act on an agreeing reading only when the answer is this certain AND a mistake is recoverable


class PerceptJev(TableCodeOnly):
    name = "jev_trust"

    def __init__(self, model=None, gate=GATE):
        super().__init__()
        self.client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
        self.model = model or os.environ.get("CELL_JEV_MODEL", "jev-latest")
        self.gate = gate
        self.calls = self.errors = 0
        self.first_error = None
        self.probs, self.gated = [], 0

    def _ask(self, f):
        q = {
            "agreement": Choice(
                instructions={"role": ROLE,
                              "ask": "Do the readings in this sensor report agree with one another?"},
                criteria={"agree": "Every reading is consistent with the others.",
                          "contradiction": "At least one reading contradicts another reading.",
                          "poor_quality": "A reading is low quality, or the same thing is reported more than once."}),
            "consequence": Choice(
                instructions={"role": ROLE,
                              "ask": "If the report is wrong about what the robot is about to handle, what follows?"},
                criteria={"permanent": "Something would be broken or someone hurt, and it could not be undone.",
                          "recoverable": "The robot would lose time and try again."}),
        }
        self.calls += 1
        a = self.client.system_one(state=f, model=self.model, questions=q).answers
        ag, cq = a["agreement"], a["consequence"]
        p = float(getattr(ag, "confidence", 0.0) or 0.0)
        self.probs.append(p)
        return ag.choice, cq.choice, p

    def look(self, f, opts, room):
        if not any(k.startswith("look_closer") for k in opts): return None
        try:
            ag, cq, p = self._ask(f)
        except Exception as e:                       # METHOD ERROR 73: a bare except once turned one indexing bug into
            self.errors += 1                        # 720 silent failures and a clean-looking 0/12. Record and surface.
            if self.first_error is None: self.first_error = f"{type(e).__name__}: {e}"
            return None
        suspect = ag != "agree"
        if not suspect and cq == "permanent" and p < self.gate:
            suspect = True; self.gated += 1          # the calibration payoff, counted separately so it can be audited
        if not suspect: return None
        return next((k for k in sorted(opts) if k.startswith("look_closer")), None)

    def decide(self, f, opts, room):
        look = self.look(f, opts, room)
        if look: return look, {"looked": True}
        return TableCodeOnly.decide(self, f, opts, room)


class PerceptJevRank(PerceptJev):
    """The framing a look budget actually calls for: not "is something wrong" but "WHICH reading do I spend my one look
    on". Two questions in one call -- whether the readings hang together, and which single reading is least trustworthy
    -- with code doing the combining.

    The second question's option set is the list of candidate readings, which is the design decision rather than the
    wording of it (claim 7: the option set carries the signal, the option text is close to noise). And it is the one
    question on this programme that could not be a code check even in principle: code can test a reading against a rule,
    but ranking several readings none of which trips a rule requires a number attached to each, which is what a
    calibrated model returns and a frontier model's stated certainty is not."""
    name = "jev_rank"

    def _rank(self, f, cands):
        q = {
            "agreement": Choice(
                instructions={"role": ROLE,
                              "ask": "Do the readings in this sensor report agree with one another?"},
                criteria={"agree": "Every reading is consistent with the others.",
                          "contradiction": "At least one reading contradicts another reading.",
                          "poor_quality": "A reading is low quality, or a reading is old, or something is reported "
                                          "without being currently seen."}),
            "weakest": Choice(
                instructions={"role": ROLE,
                              "ask": "You may re-examine exactly one of these. Which reading is least trustworthy?"},
                criteria={c: f"The reading for the {c}." for c in cands}),
        }
        self.calls += 1
        a = self.client.system_one(state=f, model=self.model, questions=q).answers
        ag, wk = a["agreement"], a["weakest"]
        p = float(getattr(wk, "confidence", 0.0) or 0.0)
        self.probs.append(p)
        return ag.choice, wk.choice, p

    def look(self, f, opts, room):
        looks = [k for k in sorted(opts) if k.startswith("look_closer")]
        if not looks: return None
        cands = [k.split("object=", 1)[1].rstrip(")") for k in looks]
        try:
            ag, wk, p = self._rank(f, cands)
        except Exception as e:
            self.errors += 1
            if self.first_error is None: self.first_error = f"{type(e).__name__}: {e}"
            return None
        if ag == "agree" and p < self.gate:
            self.gated += 1                       # readings look fine but the ranking itself is uncertain: spend a look
        elif ag == "agree":
            return None                           # readings agree and the model is certain which is weakest: proceed
        k = f"look_closer(object={wk})"
        return k if k in opts else looks[0]

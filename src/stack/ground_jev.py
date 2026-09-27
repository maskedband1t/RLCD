"""The calibrated arm for bench 7. ONE question, and code owns everything code can compute.

Today's lesson applied before building rather than after: `code_only` won bench 5 because both questions it asked were
computable. So the consequence question is NOT asked here. Whether this step is irreversible is a lookup -- the carton
goes in the bin, the bin is final -- and code holds it. The model is asked the one thing code cannot get: whether the
report identifies the object that was asked for.

Framing rules, each applied on purpose and named:
  E70       categorical criteria; no raw number comes back for code to interpret.
  E76       the consequence is combined in code, not folded into the question. Mixing them scored 0/6; separating them 6/6.
  E161-163  the question is about the EVIDENCE, never the model's own state. "Do these readings identify it?" is
            answerable from the page; "are you confident?" is introspection and measured 40 % right.
  Claim 7   the option SET is the design. Three criteria, chosen so the middle one is where a threshold can live."""
import os
from typesafe_sdk import TypeSafeClient, Choice
from stack.ground_arms import expected_cost_says_verify

ROLE = ("You read the output of a robot's object-recognition system. It was asked to find one named object on a kitchen "
        "counter and it has reported which one it believes that is, with the measurements behind that report. You do not "
        "decide what the robot does. You judge only whether the report has identified the right object.")


class GroundJev:
    name = "jev_ground"

    def __init__(self, model=None):
        self.client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])
        self.model = model or os.environ.get("CELL_JEV_MODEL", "jev-latest")
        self.calls = self.errors = 0
        self.first_error = None
        self.last_p = None
        self.probs = []

    def prob(self, ev):
        # Strip anything the grounder could not know: the true identity of what it selected (underscore-prefixed),
        # the plan's own bookkeeping, and the consequence, which code owns because code can compute it.
        state = {k: v for k, v in ev.items()
                 if not k.startswith("_") and k not in ("intended", "this_step_is_irreversible",
                                                        "verifications_left")}
        q = {"identity": Choice(
            instructions={"role": ROLE,
                          "ask": "Do these measurements identify the object that was asked for?"},
            criteria={"confident_match": "The measurements single out the object that was asked for.",
                      "ambiguous": "The measurements fit the object that was asked for and at least one other "
                                   "object about equally well.",
                      "likely_wrong": "The measurements fit a different object better than the one that was "
                                      "asked for."})}
        self.calls += 1
        a = self.client.system_one(state=state, model=self.model, questions=q).answers["identity"]
        pr = getattr(a, "probabilities", None) or {}
        p = float(pr.get("confident_match", 1.0 if a.choice == "confident_match" else 0.0))
        self.probs.append(p)
        return p

    def verify(self, ev):
        try:
            self.last_p = self.prob(ev)
        except Exception as e:
            self.errors += 1
            if self.first_error is None: self.first_error = f"{type(e).__name__}: {e}"
            return False
        if ev["verifications_left"] <= 0: return False
        return expected_cost_says_verify(self.last_p, ev)

"""S1-E42 — CLM-8B in the kitchen seat, and the head-to-head that matters:
ESCALATE ON LOW CONFIDENCE  vs  ESCALATE ON PREDICTION ERROR.

Why this experiment. On the send date @acrosson published the same architecture we have been building --
a calibrated model in the PLANNING layer rather than in control, deciding what to do with each
object, "if its unsure, the systems asks a human for input". Independent arrival, same week. So the
architecture is no longer the contribution. The TRIGGER is.

His trigger is uncertainty. We measured (S1-E25) that uncertainty is blind to the failure that
matters: CLM-8B sat at a stable 0.55 confidence while choosing `stop` 218 times in a row and
delivering nothing. Each decision was individually defensible; the sequence was fatal. Confidence
cannot see a failure of PROGRESS, because progress is a property of the sequence.

Our trigger is prediction error: did the world become what the action predicted. Same model, same
seeds, same inner policy -- only the gate differs.
"""
import os, time
import numpy as np

ROLE = ("You are a robot tidying a kitchen. You are given the task, what you are holding, what is "
        "still on the counter, and how far you are from things. Choose ONE action.")


class KitchenCLM:
    """CLM-8B choosing over the kitchen's option set. gate=None | 'confidence' | 'surprise'."""

    def __init__(self, gate=None, tau=0.45):
        from typesafe_sdk import Choice
        from duck.e93_run import _shared
        from duck.clm_local import ClmLocalClient
        self.Choice = Choice
        self.client = _shared(("clm", os.environ.get("CLM_CKPT", ""), os.environ.get("CLM_ENCODER", "")),
                              ClmLocalClient)
        self.model = "clm"
        self.gate = gate
        self.tau = tau
        self.name = "clm" + (f"+{gate}" if gate else "")
        self.calls = 0
        self.latency = []
        self.surprises = 0
        self.low_conf = 0
        self._expected = None

    # the world model: three lines, and the whole point of the comparison
    def _predict(self, skill):
        if skill.startswith("pick_up:"):
            return {"holding": skill.split(":", 1)[1]}
        if skill == "put_in_bin":
            return {"holding": "nothing"}
        return None

    def observe(self, f_after):
        """Escalate if the world did not become what the last action predicted."""
        if self.gate != "surprise" or not self._expected:
            self._expected = None
            return False
        pred = self._expected
        self._expected = None
        for k, v in (pred or {}).items():
            if str(f_after.get(k)) != str(v):
                self.surprises += 1
                return True
        return False

    def decide(self, f, opts, room):
        opts = sorted(opts)
        if len(opts) == 1:
            return opts[0], {"confidence": 1.0, "source": "single-option"}
        q = {"action": self.Choice(instructions={"role": ROLE, "question": "Which action now?"},
                                   criteria={o: o for o in opts})}
        t0 = time.time()
        r = self.client.system_one(state=f, model=self.model, questions=q)
        self.calls += 1
        self.latency.append(round(time.time() - t0, 3))
        a = r.answers["action"]
        key = a.choice if a.choice in opts else "stop"
        conf = float(a.confidence)
        j = {"choice": key, "confidence": round(conf, 3)}

        if self.gate == "confidence" and conf < self.tau and "ask_operator" in opts:
            self.low_conf += 1
            return "ask_operator", dict(j, gated="low_confidence")
        if self.gate == "surprise":
            self._expected = self._predict(key)
        return key, j

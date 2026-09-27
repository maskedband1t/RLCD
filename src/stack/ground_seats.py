"""E196: three different models in the same seat, same question, same state, same recalibration.

The open 27B goes through Featherless's Simple Jev demo endpoint, the same route the duck bench's D4d arm used, so the
readout is identical and the only thing varying is the model behind it."""
import json, os, time, urllib.request
from stack.ground_jev import GroundJev, ROLE
from stack.ground_arms import expected_cost_says_verify

CRITERIA = {
    "confident_match": "The measurements single out the object that was asked for.",
    "ambiguous": "The measurements fit the object that was asked for and at least one other object about equally well.",
    "likely_wrong": "The measurements fit a different object better than the one that was asked for.",
}
ASK = "Do these measurements identify the object that was asked for?"


def _state(ev):
    return {k: v for k, v in ev.items()
            if not k.startswith("_") and k not in ("intended", "this_step_is_irreversible", "verifications_left")}


class OpenSeat:
    """A dense open 27B in the same seat. Same state, same question, same criteria -- only the model differs."""
    URL = "https://simple-jev-demo-api.featherless.ai/v1/classifier"

    def __init__(self, model="featherless-ai/Qwen3.8-27B-classifier"):
        self.model = model; self.name = "open27b"
        self.calls = self.errors = 0; self.first_error = None
        self.last_p = None; self.latency = []

    def prob(self, ev):
        body = {"model": self.model, "state": _state(ev),
                "questions": {"identity": {"type": "choice",
                                           "instructions": json.dumps({"role": ROLE, "ask": ASK}),
                                           "criteria": CRITERIA}}}
        req = urllib.request.Request(self.URL, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "curl/8.7.1", "Accept": "application/json"})
        t0 = time.time(); err = None
        for attempt in range(4):
            try:
                r = json.loads(urllib.request.urlopen(req, timeout=60).read())
                a = r["answers"]["identity"]; break
            except Exception as e:
                err = e; time.sleep(1.2 * (attempt + 1))
        else:
            self.errors += 1
            if self.first_error is None: self.first_error = f"{type(err).__name__}: {err}"
            raise RuntimeError(f"open seat failed: {err}")
        self.calls += 1; self.latency.append(time.time() - t0)
        pr = a.get("probabilities") or {}
        return float(pr.get("confident_match", 1.0 if a.get("choice") == "confident_match" else 0.0))

    def verify(self, ev):
        try: self.last_p = self.prob(ev)
        except Exception: return False
        if ev["verifications_left"] <= 0: return False
        return expected_cost_says_verify(self.last_p, ev)


class TimedJev(GroundJev):
    """GroundJev with per-call latency recorded, so E196.5 is measured rather than assumed."""
    def __init__(self, model=None):
        super().__init__(model=model); self.latency = []; self.name = f"jev/{self.model}"
    def prob(self, ev):
        t0 = time.time(); p = super().prob(ev); self.latency.append(time.time() - t0); return p


def seats():
    return [("jev-latest", lambda: TimedJev("jev-latest")),
            ("jev-preview", lambda: TimedJev("jev-preview")),
            ("open27b", lambda: OpenSeat())]

"""The ceiling arm: a frontier model in the decision seat.

**Why this exists.** Every comparison in this programme has been against a frozen rule program
(a floor nobody ships) and an oracle (unreachable). If the premise is that a frontier model can
already do the long-horizon task and is merely too slow, then *the frontier model is the ceiling*
and the harness's job is to remove its calls without losing what it could do. That number has never
been measured here: the README says outright "we did not run a frontier model in the seat."

**What it reports, and this is the point.** Not just whether it succeeded. `calls`, `cached`,
`latency` and `spend_s` per episode, so capability can be traded against calls removed. A harness
result is `capability retained per frontier call removed`, and nothing in this repository has had a
denominator for that until now.

**The cache is deliberate, and follows E68.** E68 replayed a recorded fingerprint->judgment cache at
synthetic latency so the latency curve was reproducible without an API key. Same here: one paid pass
populates `results/frontier_cache.jsonl`, and every later run of the same states is free and
deterministic. That makes the ceiling arm cheap to re-run and the comparison stable.

Backends, chosen by env var, checked in this order. No credential is read or printed by this module
beyond handing it to the provider's own client:

  FRONTIER_BACKEND=anthropic   ANTHROPIC_API_KEY   FRONTIER_MODEL (default claude-sonnet-4-6)
  FRONTIER_BACKEND=openai      OPENAI_API_KEY      FRONTIER_MODEL
  FRONTIER_BACKEND=openrouter  OPENROUTER_API_KEY  FRONTIER_MODEL
  FRONTIER_BACKEND=openclaw    (no key; shells `openclaw agent`, needs a valid openclaw config)
  FRONTIER_BACKEND=cache       replay only -- fails on a cache miss, so a sweep cannot silently bill
  FRONTIER_BACKEND=pending     replay, and on a miss LOG the state and substitute a declared fallback,
                               so an episode completes and every unanswered state is collected in one
                               pass. This is how a closed loop gets batched: the states visited depend
                               on the decisions made, so they cannot be collected in advance. Run,
                               answer the batch, re-run. Each round the trajectory shifts but overlaps
                               heavily with the last, so it converges in a handful of rounds rather
                               than one round trip per decision. Substitutions are COUNTED, never
                               hidden, and a run with `substituted > 0` is not a ceiling run.

Usage as an arm, matching every other arm's interface:

    from frontier_arm import FrontierArm
    arm = FrontierArm()                 # or FrontierArm(tau=0.7) for a gate variant
    key, j = arm.decide(facts, options, room)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

CACHE_PATH = os.environ.get("FRONTIER_CACHE", "results/frontier_cache.jsonl")
PENDING_PATH = os.environ.get("FRONTIER_PENDING", "results/frontier_pending.jsonl")

ROLE = ("You are the judgment layer of a robot working alongside people. Code has already decided "
        "which actions are possible right now. Choose exactly one, following the task and any "
        "operator notes, and keep people safe and comfortable before making progress.")


# Fields dropped from BOTH the prompt and the cache key. `recent_actions` is a growing list, so
# including it made every tick a unique state (524 unique states in three episodes) and a cache
# useless. Dropping it is not only a practical fix, it is the honest ceiling: **a frontier model in
# the seat with no harness around it has no memory.** Supplying history is the harness's job, so an
# arm that measures the model alone must decide each situation fresh. A `frontier+memory` arm is a
# separate, later comparison -- and the difference between them is exactly what memory is worth.
DROP_FIELDS = ("recent_actions",)


def _seen(facts):
    return {k: v for k, v in facts.items() if k not in DROP_FIELDS}


def _fingerprint(facts, opts) -> str:
    return hashlib.sha1(json.dumps([_seen(facts), sorted(opts)], sort_keys=True, default=str).encode()).hexdigest()


def _render(facts, opts) -> str:
    return (f"SITUATION\n{json.dumps(_seen(facts), indent=1, default=str)}\n\n"
            f"OPTIONS (choose exactly one key)\n"
            + "\n".join(f"  {k}: {v}" for k, v in sorted(opts.items()))
            + '\n\nReply with ONLY a JSON object: {"choice": "<one key above>", "confidence": <0..1>}')


class FrontierArm:
    """A frontier model behind the same typed interface every other arm uses."""

    def __init__(self, tau=None, confirm=False, model=None, backend=None):
        self.tau, self.confirm = tau, confirm
        self.backend = backend or os.environ.get("FRONTIER_BACKEND", "cache")
        self.model = model or os.environ.get("FRONTIER_MODEL", "claude-sonnet-4-6")
        self.name = "frontier" + ("" if tau is None else (f"_confirm{tau}" if confirm else f"_gate{tau}"))
        self.calls = self.cached = self.errors = self.substituted = 0
        self.latency: list[float] = []
        self.spend_s = 0.0          # wall-clock actually spent in the provider, the thing being removed
        self._cache = self._load_cache()
        self._client = None

    # ---------------------------------------------------------------- cache
    def _load_cache(self) -> dict:
        c = {}
        if os.path.exists(CACHE_PATH):
            for line in open(CACHE_PATH):
                try:
                    r = json.loads(line)
                    c[r["key"]] = r["answer"]
                except Exception:
                    continue
        return c

    def _remember(self, key, answer):
        self._cache[key] = answer
        os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
        with open(CACHE_PATH, "a") as f:
            f.write(json.dumps({"key": key, "answer": answer, "model": self.model,
                                "backend": self.backend}) + "\n")

    # -------------------------------------------------------------- backends
    def _ask_anthropic(self, prompt):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        r = self._client.messages.create(model=self.model, max_tokens=200, system=ROLE,
                                         messages=[{"role": "user", "content": prompt}])
        return r.content[0].text

    def _ask_openai(self, prompt):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        r = self._client.chat.completions.create(model=self.model, max_tokens=200,
                                                 messages=[{"role": "system", "content": ROLE},
                                                           {"role": "user", "content": prompt}])
        return r.choices[0].message.content

    def _ask_openrouter(self, prompt):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=os.environ["OPENROUTER_API_KEY"],
                                         base_url="https://openrouter.ai/api/v1")
        r = self._client.chat.completions.create(model=self.model, max_tokens=200,
                                                 messages=[{"role": "system", "content": ROLE},
                                                           {"role": "user", "content": prompt}])
        return r.choices[0].message.content

    def _ask_openclaw(self, prompt):
        import subprocess
        out = subprocess.run(["openclaw", "agent", "--agent", "main", "--json",
                              "--message", ROLE + "\n\n" + prompt],
                             capture_output=True, text=True, timeout=180)
        if out.returncode != 0:
            raise RuntimeError(f"openclaw agent failed: {out.stderr.strip()[:300]}")
        return out.stdout

    def _ask(self, prompt):
        fn = {"anthropic": self._ask_anthropic, "openai": self._ask_openai,
              "openrouter": self._ask_openrouter, "openclaw": self._ask_openclaw}.get(self.backend)
        if fn is None:
            raise SystemExit(
                f"FRONTIER_BACKEND={self.backend!r} cannot make calls. Set it to one of "
                "anthropic|openai|openrouter|openclaw with the matching key, or leave it as "
                "'cache' to replay only. Refusing to guess a backend.")
        return fn(prompt)

    # ---------------------------------------------------------------- parse
    @staticmethod
    def _parse(text, opts):
        m = re.search(r"\{[^{}]*\}", text or "", re.S)
        choice, conf = None, None
        if m:
            try:
                d = json.loads(m.group(0))
                choice, conf = d.get("choice"), d.get("confidence")
            except Exception:
                pass
        if choice not in opts:                      # fall back to any option name it mentioned
            for k in sorted(opts, key=len, reverse=True):
                if k in (text or ""):
                    choice = k
                    break
        try:
            conf = float(conf)
        except Exception:
            conf = None
        return choice, conf

    # --------------------------------------------------------------- decide
    def decide(self, facts, opts, room):
        if len(opts) == 1:
            k = next(iter(opts))
            return k, {"choice": k, "confidence": 1.0, "probabilities": {k: 1.0},
                       "source": "single-option"}

        key = _fingerprint(facts, opts)
        if key not in self._cache and self.backend == "pending":
            # log the unanswered state, substitute, and count it. The substitute is the most
            # conservative option present, so a substituted decision never looks like a win.
            self.substituted += 1
            os.makedirs(os.path.dirname(PENDING_PATH) or ".", exist_ok=True)
            with open(PENDING_PATH, "a") as f:
                f.write(json.dumps({"key": key, "facts": _seen(facts), "options": opts}, default=str) + "\n")
            for sub in ("stop", "wait", "walk_slow"):
                if sub in opts:
                    return sub, {"choice": sub, "confidence": None, "source": "substituted"}
            k = next(iter(opts))
            return k, {"choice": k, "confidence": None, "source": "substituted"}
        if key in self._cache:
            self.cached += 1
            a = dict(self._cache[key])
            a["source"] = "cache"
            ch = a.get("choice") if a.get("choice") in opts else "stop"
            return ch, a

        t0 = time.time()
        try:
            text = self._ask(_render(facts, opts))
        except SystemExit:
            raise
        except Exception as e:
            self.errors += 1
            return "stop", {"choice": "stop", "confidence": None,
                            "source": f"error:{type(e).__name__}: {str(e)[:160]}"}
        dt = time.time() - t0
        self.calls += 1
        self.latency.append(dt)
        self.spend_s += dt

        choice, conf = self._parse(text, opts)
        if choice is None:
            self.errors += 1
            choice = "stop"
        answer = {"choice": choice, "confidence": conf,
                  "probabilities": {choice: conf} if conf is not None else {},
                  "latency": round(dt, 3), "model": self.model, "source": self.backend}
        self._remember(key, answer)

        if self.tau is not None and conf is not None and conf < self.tau:
            return ("confirm:" + choice) if self.confirm else "ask_operator", answer
        return choice, answer


def stats(arm) -> dict:
    """The numbers a ceiling arm exists to produce."""
    import statistics as st
    return {"calls": arm.calls, "cached": arm.cached, "errors": arm.errors,
            "substituted": arm.substituted,
            "is_ceiling_run": arm.substituted == 0,
            "spend_s": round(arm.spend_s, 1),
            "latency_median": round(st.median(arm.latency), 3) if arm.latency else None,
            "model": arm.model, "backend": arm.backend}


if __name__ == "__main__":
    a = FrontierArm()
    facts = {"task": "Walk to the goal without troubling the person.",
             "notes_from_operators": ["A child is playing in the room; keep one metre away."],
             "robot": {"status": "standing", "goal_distance": "far"},
             "person": {"kind": "child", "distance": "near", "motion": "standing_still"}}
    opts = {"walk_fast": "Walk to the goal at normal speed.",
            "walk_slow": "Walk to the goal slowly.",
            "wait": "Stand still and wait two seconds.",
            "ask_operator": "Ask the operator (four seconds of their time)."}
    print(f"backend={a.backend} model={a.model} cache={len(a._cache)} entries")
    print("decide ->", a.decide(facts, opts, None))
    print("stats  ->", json.dumps(stats(a)))

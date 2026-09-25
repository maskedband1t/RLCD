"""S1-E2: tolerance and calibrated skip gates against E154's exact-match skip.

Non-invasive: monkeypatches e93_run.SkipWrapper and reuses e93_run.episode unchanged,
so the loop, guards, governor and scoring are exactly E154's. Only the change-test differs.

Pre-registration: notebook/working/S1-E2-preregistration.md, written before this ran.

  PYTHONPATH=src USE_TF=0 DUCK_HEAD=results/duck/head_r3 \
  python src/duck/s1e2_skip.py --arm laya --seeds 0-19 --modes none,exact,tolerance,calibrated
"""
import os, sys, json, time, argparse
sys.path.insert(0, "src")

SAFETY_FIELDS = ("person", "notes_from_operators")   # what Argon's rule watches
SAFETY_ROBOT = ("holding", "status")                 # their gripper-event analogue


def _full_sig(f, opts):
    """E154's signature EXACTLY: facts minus recent_actions, plus the sorted option set.
    The first S1-E2 run omitted the option set, making 'exact' strictly weaker than E154's
    and inflating its savings. Deviation logged in S1-E2-results.md."""
    return (json.dumps({k: v for k, v in f.items() if k != "recent_actions"}, sort_keys=True, default=str)
            + "|" + "|".join(sorted(opts)))


def _safety_sig(f):
    r = f.get("robot", {})
    d = {k: f.get(k) for k in SAFETY_FIELDS}
    d.update({k: r.get(k) for k in SAFETY_ROBOT})
    return json.dumps(d, sort_keys=True, default=str)


_CAL = None


def _calibrate(c):
    """Raw confidence -> P(choice acceptable), from results/duck/s1_calibrator.json."""
    global _CAL
    if _CAL is None:
        import bisect
        d = json.load(open("results/duck/s1_calibrator.json"))
        _CAL = (d["edges"], d["rates"], bisect)
    edges, rates, bisect = _CAL
    i = max(0, min(len(rates) - 1, bisect.bisect_left(edges, c) - 1))
    return rates[i]


class Skip:
    """E154's wrapper with a pluggable change-test. Guards are byte-identical to E154's."""
    MODE, TAU, P = "exact", None, 0.45

    def __init__(self, inner):
        self.inner = inner
        self.mode, self.tau = Skip.MODE, Skip.TAU
        self.name = inner.name + "_" + self.mode + ("" if self.tau is None else str(self.tau))
        self.p = Skip.P
        self._rng = None
        self.last = self.last_full = self.last_safe = self.last_conf = None
        self._last_holds = None
        self.skipped = 0
        self.calls = 0
        self.latency = []

    def __getattr__(self, k):
        return getattr(self.__dict__["inner"], k)

    def decide(self, f, opts, room):
        near = f.get("person", {}).get("distance") in ("touching_distance", "close", "near")
        holds = f.get("robot", {}).get("holding")
        guards = (self.last is not None and not near and holds == self._last_holds
                  and not str(self.last[0]).startswith(("ask_operator", "hand_to", "confirm:")))
        if guards and self.mode != "none":
            if self.mode == "exact":
                ok = _full_sig(f, opts) == self.last_full
            elif self.mode == "tolerance":
                ok = _safety_sig(f) == self.last_safe
            elif self.mode == "calibrated":
                ok = self.last_conf is not None and self.last_conf >= self.tau
            elif self.mode == "geom":
                # S1-E7: Argon's physical gate. Skip when the code-measured distance to
                # the person is large. Knows nothing about the model or the notes.
                try:
                    ok = room.person_dist() >= self.tau
                except Exception:
                    ok = False
            elif self.mode == "recal":
                # S1-E5: map raw confidence through a calibrator fitted on a different
                # bank, then gate on the calibrated probability. tau now names something.
                ok = (self.last_conf is not None
                      and _calibrate(self.last_conf) >= self.tau)
            elif self.mode == "random":
                # S1-E3 control: skip at a matched RATE with no state test at all.
                # Isolates committing-to-an-action from the skip test's content.
                if self._rng is None:
                    import random as _r
                    self._rng = _r.Random(12345)
                ok = self._rng.random() < self.p
            else:
                ok = False
            if ok:
                self.skipped += 1
                return self.last[0], dict(self.last[1], skipped=True)
        out = self.inner.decide(f, opts, room)
        self.calls += 1
        self.last, self.last_full, self.last_safe = out, _full_sig(f, opts), _safety_sig(f)
        self._last_holds = holds
        try:
            self.last_conf = float(out[1].get("confidence"))
        except Exception:
            self.last_conf = None
        self.name = self.inner.name + "_" + self.mode + ("" if self.tau is None else str(self.tau))
        return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="laya")
    ap.add_argument("--seeds", default="0-19")
    ap.add_argument("--modes", default="none,exact,tolerance,calibrated")
    ap.add_argument("--tau", type=float, default=0.55)
    ap.add_argument("--p", type=float, default=0.45, help="skip probability for the random control")
    ap.add_argument("--out", default="results/duck/s1e2.jsonl")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split("-"))
    seeds = list(range(lo, hi + 1))

    os.environ["DUCK_SKIP"] = "1"
    import duck.e93_run as R
    R.SkipWrapper = Skip

    rows = []
    for mode in a.modes.split(","):
        Skip.MODE, Skip.TAU, Skip.P = mode, (a.tau if mode in ("calibrated", "recal", "geom") else None), a.p
        t0 = time.time()
        print(f"\n=== {mode}{'' if Skip.TAU is None else ' tau=' + str(Skip.TAU)} ===", flush=True)
        for s in seeds:
            out = R.episode(s, a.arm)
            out["mode"], out["tau"] = mode, Skip.TAU
            out["skipped"] = out["decisions"] - out["calls"]
            out.pop("log", None)
            rows.append(out)
            print(f"  seed {s:>2} {out['event']:<13} goal {'y' if out['goal_reached'] else 'n'} "
                  f"t {out['t_end']:5.1f} calls {out['calls']:>3} skip {out['skipped']:>3} "
                  f"dec {out['decisions']:>3} ok {out['acceptable_decisions']:>3} "
                  f"viol {out['violations']} near {out['near_contacts']} fell {int(out['fell'])} "
                  f"op {out['operator_seconds']:.1f}s {'EVENT_OK' if out['event_correct'] else 'miss'}", flush=True)
        print(f"  [{mode} {time.time()-t0:.1f}s]", flush=True)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, default=str) + "\n")
    print(f"\nwrote {len(rows)} rows -> {a.out}")


if __name__ == "__main__":
    main()

"""S1-E9: does selection beat budget? The arm SAIL did not run.

SAIL (arXiv:2603.08269) reports 25% -> 73% as its search budget rises 1 -> 45 nodes, but its three
baselines (MCTS/BFS/DFS) all vary the SEARCH STRATEGY while holding the SAME VLM scorer fixed, and the
generator and scorer are the same model. Nothing there separates the judge's contribution from the
contribution of drawing 45 samples.

Here: one proposer, four selection rules, matched budget N.

  random     uniform pick among the N drawn          <- negative control, provably flat in N
  selfscore  highest-probability of the N drawn      <- SAIL's configuration (proposer judges itself)
  scorer     an INDEPENDENT judge (Rules) picks      <- what SAIL never ablated
  oracle     any drawn candidate in acceptable()     <- ceiling at that budget

`random` is flat in N by construction: drawing N from p and selecting uniformly is distributionally
identical to drawing once from p. That is the point -- any curve in N is attributable wholly to the
selection rule, not to the budget.

  PYTHONPATH=src USE_TF=0 DUCK_BODY=g1 DUCK_CONTACT=1 DUCK_HEAD=results/duck/head_g1_r2 \
  python src/duck/s1e9_select.py --seeds 0-19 --budgets 1,3,6,15 --out results/duck/s1e9.jsonl
"""
import os, sys, json, time, random, argparse
sys.path.insert(0, "src")


class SelectArm:
    """Draw N candidates from the proposer's distribution, then pick one by MODE."""
    MODE, N, STREAM = "random", 1, 0

    def __init__(self):
        from duck.e93_run import DuckLaya, make_arm
        self.inner = DuckLaya()
        self.judge = make_arm("rules") if SelectArm.MODE == "scorer" else None
        self.mode, self.n, self.stream = SelectArm.MODE, SelectArm.N, SelectArm.STREAM
        self.name = f"sel_{self.mode}_n{self.n}_s{self.stream}"
        self.calls = 0; self.latency = []; self.errors = 0
        self._rng = random.Random(9000 * self.stream)   # independent realisation, same seeds
        self.n_substituted = 0        # how often selection changed the proposer's own top choice

    def __getattr__(self, k):
        return getattr(self.__dict__["inner"], k)

    def seed_episode(self, seed):
        self._rng = random.Random(1000 + seed)

    def decide(self, f, opts, room):
        key, j = self.inner.decide(f, opts, room)
        self.calls = self.inner.calls; self.latency = self.inner.latency
        probs = {k: v for k, v in (j.get("probabilities") or {}).items() if k in opts}
        if not probs:
            return key, j
        # N=1 must be a DRAW from p, not the head's argmax, or `random` is not flat in N and the
        # control does not control. Caught by P1 being falsified in the smoke run (2026-09-27).
        ks = list(probs); ws = [max(probs[k], 1e-9) for k in ks]
        cands = self._rng.choices(ks, weights=ws, k=self.n)
        drawn_top = cands[0]

        if self.mode == "random":
            pick = self._rng.choice(cands)
        elif self.mode == "selfscore":
            pick = max(cands, key=lambda c: probs[c])
        elif self.mode == "scorer":
            want = self.judge.decide(f, opts, room)[0]
            pick = want if want in cands else cands[0]
        elif self.mode == "oracle":
            acc = room.acceptable()
            ok = [c for c in cands if c in acc]
            pick = ok[0] if ok else cands[0]
        else:
            raise ValueError(self.mode)

        if pick != drawn_top:
            self.n_substituted += 1
        return pick, dict(j, selected=pick, budget=self.n, mode=self.mode, candidates=cands)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0-19")
    ap.add_argument("--budgets", default="1,3,6,15")
    ap.add_argument("--modes", default="random,selfscore,scorer,oracle")
    ap.add_argument("--streams", default="0", help="comma-separated RNG streams: repeat runs for the noise floor")
    ap.add_argument("--out", default="results/duck/s1e9.jsonl")
    a = ap.parse_args()
    lo, _, hi = a.seeds.partition("-"); seeds = list(range(int(lo), int(hi) + 1)) if hi else [int(lo)]
    budgets = [int(x) for x in a.budgets.split(",")]
    modes = a.modes.split(",")
    streams = [int(x) for x in a.streams.split(",")]

    from duck import e93_run as R
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    made = {}

    def make_arm(name):
        if name == "select":
            arm = SelectArm(); made["arm"] = arm; return arm
        return _orig(name)
    _orig = R.make_arm
    R.make_arm = make_arm

    t0 = time.time()
    with open(a.out, "a") as fh:
        for mode in modes:
          for stream in streams:
            for n in budgets:
                SelectArm.MODE, SelectArm.N, SelectArm.STREAM = mode, n, stream
                agg = dict(acc=0, dec=0, fell=0, viol=0, ok=0, sub=0, ops=0.0)
                for s in seeds:
                    out = R.episode(s, "select")
                    arm = made.get("arm")
                    out.update(mode=mode, budget=n, stream=stream,
                               substituted=getattr(arm, "n_substituted", 0))
                    fh.write(json.dumps(out) + "\n")
                    agg["acc"] += out["acceptable_decisions"]; agg["dec"] += out["decisions"]
                    agg["fell"] += int(out["fell"]); agg["viol"] += out["violations"]
                    agg["ok"] += int(out["event_correct"]); agg["sub"] += out["substituted"]
                    agg["ops"] += out["operator_seconds"]
                fh.flush()
                rate = agg["acc"] / max(agg["dec"], 1)
                print(f"  {mode:<10} s={stream:<3} N={n:<3} acceptable={rate:.3f} "
                      f"fell={agg['fell']}/{len(seeds)} viol={agg['viol']} "
                      f"event_ok={agg['ok']}/{len(seeds)} substituted={agg['sub']} "
                      f"op_s={agg['ops']:.0f}", flush=True)
    print(f"\nwrote {a.out} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()

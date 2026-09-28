"""E198 -- interventional recoverability on bench 9, against three baselines that cost nothing.

The quantity, from Kintsugi-VLA (arXiv 2609.31048), whose design this is and which got here first:

    R(s) = P( task completed | the simulator is restored to state s, then a FIXED competent policy runs )

estimated by Monte Carlo continuations with pointwise Wilson intervals. It is a number about the STATE, not about the
policy that produced the state, which is the whole point: it separates "the robot is somewhere bad" from "the robot is
choosing badly".

Two implementation facts that decide whether this measures anything at all:

  1. RESEEDING. `Aisle` carries a `random.Random`. A deepcopy carries its internal state too, so continuations from one
     restored snapshot would replay byte-identically and R would be 0 or 1 with no variance -- a step function that
     looks like a clean result and is an artefact of forgetting one line. Every continuation gets a fresh stream.
     `assert_reseeding_matters()` refuses to run the experiment until it has shown identical copies diverge.

  2. A FRESH EXPERT. Each continuation gets a new `Reference`, so it re-looks and re-inspects rather than inheriting the
     failing arm's knowledge. Declared approximation: this costs a few seconds of clock and therefore UNDER-estimates R
     slightly. It is the conservative direction, and it is what "what could a careful policy still achieve from here"
     means if the expert is not allowed to read the other arm's mind.
"""
import copy
import json
import os
import random
import sys

from cell.analyze import wilson
from stack.aisle import CAP_S, Aisle
from stack.aisle_arms import IgnoreEverything, NeverAsks, Reference, RuleProgram

TAU = 0.5            # the recoverability threshold a frontier is defined against
N_CONT = 50          # continuations per decision point (P4 predicted >= 50 is needed; measured below, not assumed)
MAX_DEC = 400


# ----------------------------------------------------------------- the machinery
def run_from(room, n_cont, base_seed, max_dec=MAX_DEC):
    """Restore-and-branch: run `n_cont` continuations of a FIXED competent policy from this exact state.

    Returns (successes, n, per-continuation records). The room passed in is never mutated."""
    ok = 0
    recs = []
    for j in range(n_cont):
        r = copy.deepcopy(room)
        # (1) above. Without this every continuation is the same episode.
        r.rng = random.Random(900_000 + base_seed * 1000 + j)
        arm = Reference()                       # (2) above: a fresh expert, no inherited knowledge
        n = 0
        while r.t < CAP_S and n < max_dec and not r.fell and not r.finished():
            opts = r.options()
            if not opts:
                break
            key = arm.decide(r.facts(), opts, r)
            if key not in opts:
                key = sorted(opts)[0]
            r.run(key)
            n += 1
            if key == "done()":
                break
        rec = r.record()
        recs.append(rec)
        ok += rec["success"]
    return ok, n_cont, recs


def characterise_R(verbose=True):
    """Three questions, and only the third can stop the experiment.

    1. Is restoration exact? Unreseeded copies must give ONE outcome, or deepcopy is not a snapshot.
    2. Is R stochastic or deterministic? Originally this was written as a pass/fail on "reseeding changes something",
       which was wrong: determinism is a PROPERTY OF THE BENCH to report, not a fault. `FALL_RATE` works out to
       p ~ 0.0023 per full-length move, so R here is close to a predicate. If it is deterministic, N = 1 suffices and
       Wilson intervals are decoration that must not be printed.
    3. Is R non-trivial -- 1 somewhere and 0 somewhere? If the expert never wins, R = 0 everywhere and no frontier
       exists. **This is the one that stops the run**, and it is what stopped it the first time: METHOD ERROR 83.
    """
    room = Aisle(seed=0, event="none")
    same = []
    for _ in range(6):
        r = copy.deepcopy(room)
        a = Reference(); n = 0
        while r.t < CAP_S and n < MAX_DEC and not r.fell and not r.finished():
            o = r.options()
            if not o:
                break
            k = a.decide(r.facts(), o, r)
            r.run(k if k in o else sorted(o)[0]); n += 1
            if k == "done()":
                break
        same.append((r.record()["success"], r.record()["t_end"]))
    exact = len(set(same)) == 1

    ok0, n0, recs0 = run_from(room, 50, base_seed=11)
    spread = len(set((x["success"], x["t_end"], x["fell"]) for x in recs0))
    falls = sum(x["fell"] for x in recs0)

    # non-triviality: a fresh winnable state vs a deliberately broken one
    doomed = Aisle(seed=0, event="none")
    doomed.broken.append(doomed.cart_order[0])          # success requires `not broken`; this state is unwinnable
    okd, nd, _ = run_from(doomed, 8, base_seed=13)

    if verbose:
        print("  characterising R")
        print(f"    restoration exact:      {exact}  ({len(set(same))} distinct outcome(s) in 6 unreseeded copies)")
        print(f"    R at a fresh state:     {ok0}/{n0}   distinct outcomes {spread}, falls {falls}")
        print(f"    R at a doomed state:    {okd}/{nd}")
        print(f"    => R is {'STOCHASTIC' if spread > 1 else 'DETERMINISTIC'}; "
              f"{'Wilson intervals are meaningful' if spread > 1 else 'N=1 suffices, intervals are decoration'}")
    if not exact:
        print("    => restoration is not exact; restore-and-branch is unsound. Stopping.")
        return None
    if ok0 == 0:
        print("    => the expert cannot win from a fresh state; R is 0 everywhere and no frontier exists. Stopping.")
        return None
    if okd != 0:
        print("    => a deliberately doomed state still scores R > 0; the success criterion is not what it claims.")
        return None
    return {"exact": exact, "stochastic": spread > 1, "R_fresh": ok0 / n0, "falls_in_50": falls}


def noise_floor(seed=3, event="person_in_aisle", depth=14, blocks=6, n_each=50):
    """P4. Estimate R at ONE fixed state with `blocks` disjoint continuation-seed blocks, and report the spread.

    Nothing downstream may claim a frontier located more finely than this."""
    room = Aisle(seed=seed, event=event)
    arm = IgnoreEverything()
    for _ in range(depth):
        opts = room.options()
        if not opts:
            break
        k = arm.decide(room.facts(), opts, room)
        room.run(k if k in opts else sorted(opts)[0])

    print(f"  noise floor at one fixed state (seed {seed}, {event}, depth {depth}), {blocks} disjoint blocks:")
    for n in (10, 20, n_each):
        est = []
        for b in range(blocks):
            ok, tot, _ = run_from(room, n, base_seed=50_000 + b * 97)
            est.append(ok / tot)
        lo, hi = min(est), max(est)
        p = sum(est) / len(est)
        _, wlo, whi = wilson(round(p * n), n)
        print(f"    N={n:<4} R in [{lo:.2f}, {hi:.2f}] across blocks (spread {hi - lo:.2f}); "
              f"mean {p:.2f}; Wilson half-width at N {((whi - wlo) / 2):.2f}")
    return True


# ----------------------------------------------------------------- the trajectory sweep
def trace_episode(seed, arm_fn, event=None, n_cont=N_CONT, max_dec=MAX_DEC):
    """Run one episode of a failing arm; at EVERY decision point, measure R by restore-and-branch.

    Also records the three free baselines at the same points, so nothing is compared across different runs."""
    room = Aisle(seed=seed, event=event)
    arm = arm_fn()
    pts = []
    n = 0
    last_delivered = 0
    since_progress = 0
    while room.t < CAP_S and n < max_dec and not room.fell and not room.finished():
        opts = room.options()
        if not opts:
            break
        ok, tot, _ = run_from(room, n_cont, base_seed=seed * 7919 + n)
        p, lo, hi = wilson(ok, tot)
        d = len(room.delivered)
        if d > last_delivered:
            last_delivered = d
            since_progress = 0
        pts.append({
            "k": n, "t": round(room.t, 1), "R": round(p, 4), "R_lo": round(lo, 4), "R_hi": round(hi, 4),
            # the three free baselines, read at this same instant
            "irreversible": int(bool(room.broken) or bool(room.fell)),
            "clock": round(room.t / CAP_S, 4),
            "no_progress": since_progress,
        })
        key = arm.decide(room.facts(), opts, room)
        if key not in opts:
            key = sorted(opts)[0]
        room.run(key)
        n += 1
        since_progress += 1
        if key == "done()":
            break
    rec = room.record()
    rec["decisions"] = n
    return pts, rec


def frontier(pts, tau=TAU):
    """The terminal low-recoverability frontier: the first k after which R never again reaches tau."""
    last_above = None
    for p in pts:
        if p["R"] >= tau:
            last_above = p["k"]
    if last_above is None:
        return pts[0]["k"] if pts else None
    after = [p for p in pts if p["k"] > last_above]
    return after[0]["k"] if after else None


def first_cross(pts, field, thresh, ge=True):
    for p in pts:
        v = p[field]
        if (v >= thresh) if ge else (v <= thresh):
            return p["k"]
    return None


def nonmonotonic(pts, delta=0.10):
    """P3: did R fall by >= delta and later rise by >= delta?"""
    lo_after_drop = None
    peak = pts[0]["R"] if pts else 0.0
    for p in pts:
        r = p["R"]
        if lo_after_drop is None:
            if peak - r >= delta:
                lo_after_drop = r
            peak = max(peak, r)
        else:
            if r - lo_after_drop >= delta:
                return True
            lo_after_drop = min(lo_after_drop, r)
    return False


ARMS = {"ignores": IgnoreEverything, "never_asks": NeverAsks, "rules": RuleProgram}


def main():
    out = os.environ.get("OUT", "results/stack/e198_recoverability.json")
    seeds = [int(x) for x in os.environ.get("SEEDS", "0,1,2,3,4,5").split(",")]
    events = os.environ.get("EVENTS", "person_in_aisle,slot_obstructed,remembered_slot_now_full").split(",")
    arm_name = os.environ.get("ARM", "ignores")
    n_cont = int(os.environ.get("N", N_CONT))

    print("E198 -- interventional recoverability, bench 9")
    print("  method from Kintsugi-VLA (arXiv 2609.31048); it is theirs, not ours.\n")

    char = characterise_R()
    if char is None:
        sys.exit(1)
    print()
    noise_floor()
    print()

    rows = []
    for ev in events:
        for s in seeds:
            pts, rec = trace_episode(s, ARMS[arm_name], event=ev, n_cont=n_cont)
            if not pts:
                continue
            rows.append({
                "seed": s, "event": ev, "arm": arm_name, "success": rec["success"],
                "broken": rec["broken"], "fell": rec["fell"], "t_end": rec["t_end"],
                "decisions": rec["decisions"],
                "frontier_R": frontier(pts),
                "first_irreversible": first_cross(pts, "irreversible", 1),
                "clock_half": first_cross(pts, "clock", 0.5),
                "nonmonotonic": nonmonotonic(pts),
                "pts": pts,
            })
            f = rows[-1]
            print(f"  {ev:<26} seed {s}  success={rec['success']}  broken={rec['broken']}  "
                  f"frontier@{f['frontier_R']}  irrev@{f['first_irreversible']}  clock.5@{f['clock_half']}  "
                  f"decisions={rec['decisions']}")

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rows, fh)
    print(f"\n  wrote {out} ({len(rows)} episodes)")


if __name__ == "__main__":
    main()

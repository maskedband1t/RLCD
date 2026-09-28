"""Harness preflight: the assertions that make a result interpretable, checked BEFORE an experiment runs.

Every check here was earned by a specific defect that reached a printed number first. They are in the order the defects
were found, and each names its method error so the check cannot be quietly relaxed later without confronting what it cost.

The principle is the one this programme keeps relearning: an instrument property I intend to remember is a property I
will forget. Six defects in one day were found downstream, by luck or by the author asking a direct question. A precondition
in code is the only version of a lesson that holds."""
import statistics
from collections import defaultdict


def zero_model_arm_fails(run_fn, seeds, threshold=0.5):
    """CHECK 1 (E191). A bench must contain a question a model is needed for.

    `code_only` made zero model calls and tied the best of four framings on bench 5, because both questions the bench
    asked were computable -- a forward simulation and a table lookup. A whole sweep measured the COST of asking when it
    was meant to measure the VALUE. So: run an arm that never calls a model, and if it succeeds, the bench is not
    measuring what it claims to."""
    ok = sum(run_fn(s)["success"] for s in seeds)
    rate = ok / max(1, len(seeds))
    return (rate < threshold,
            f"zero-model arm scores {ok}/{len(seeds)} ({rate:.0%}); a bench where it succeeds has no model-shaped question")


def distinct_outcomes(run_fn, seeds, min_fraction=0.6):
    """CHECK 2 (method error 77). Seeds must produce distinct situations.

    25 seeds produced 12 distinct outcome signatures, and on three of five disruptions all five replicates were the SAME
    episode to the decimal -- because the only thing the seed varied besides the disruption was a person who never came
    near. Five of seven 'fall episodes' in E193 were one fall counted five times. Any interval computed on the nominal
    seed count is too narrow by whatever this ratio is."""
    sigs = defaultdict(list)
    for s in seeds:
        r = run_fn(s)
        sigs[(r["success"], r["cleared"], r["broken"], r["fell"], round(r["t_end"], 1))].append(s)
    n = len(sigs); frac = n / max(1, len(seeds))
    dupes = {k: v for k, v in sigs.items() if len(v) > 1}
    detail = "; ".join(f"seeds {v} identical" for v in list(dupes.values())[:3])
    return (frac >= min_fraction,
            f"{len(seeds)} seeds -> {n} distinct outcomes ({frac:.0%}); effective n is {n}, not {len(seeds)}"
            + (f". {detail}" if dupes else ""))


def reference_is_runnable(constant, measure_fn, tol=0.10):
    """CHECK 3 (method error 76). A reference value ships as an arm you can re-run, or it does not ship.

    `TELEOP_REF_S = 62.5` carried the comment "measured, not assumed: a human picks the order and the speed". No human
    ever drove the robot; I scripted it, and the script was not kept. Rebuilt as a real arm it measures 45.0 s, so every
    time ratio published that day was inflated 1.389x in the robot's favour. The constant is the divisor: being generous
    with it flatters everything downstream."""
    live = measure_fn()
    off = abs(live - constant) / max(1e-9, constant)
    return (off <= tol,
            f"reference constant {constant:.1f}s vs live measurement {live:.1f}s ({off:+.0%}); "
            f"a constant no arm reproduces is a guess with a decimal point")


def no_unstable_parameter(params, unstable, tol=1e-6):
    """CHECK 4 (E192f). A timing parameter must not sit on a measured-unstable value.

    Sweeping pause duration 0.5-12.0 s found EXACTLY ONE bad value: 3.0 s topples the robot on 5 of 5 seeds while it is
    carrying, and the 23 others are clean. `LOOK_S` was 3.0 because it is a round number. That single choice put 25 of 25
    episodes on the floor in a run meant to measure perception."""
    bad = [(k, v) for k, v in params.items() if any(abs(v - u) < tol for u in unstable)]
    return (not bad, f"parameters on measured-unstable values: {bad}" if bad
            else f"{len(params)} timing parameters clear of {list(unstable)}")


def no_leak_in_options(opts, visible_names):
    """CHECK 5 (the option-set leak). The option set may not name what the facts are hiding.

    Under `mislabel` the report called the glass a "mug" while the option builder still offered a look at the "glass",
    taking the name from the plan. The mismatch between report and options WAS the answer, handed over free. Claim 7 says
    the option set carries the signal, which cuts both ways: whatever it reveals is something the model never inferred."""
    leaked = sorted({n for k in opts for n in _entities(k)} - set(visible_names))
    return (not leaked, f"option set names entities absent from the facts: {leaked}" if leaked
            else f"option set names only entities the facts expose ({len(visible_names)})")


def no_dead_options(step_fn, states, is_terminal=None):
    """Every reachable state must offer an action that CHANGES the state or ENDS the episode.

    METHOD ERROR 83. Bench 9 could reach a state whose only legal action was `look()`, a two-second no-op: the robot
    stood at the cart, nothing was pickable, `go_to` was offered only in the `else` of "am I at the cart", and `done()`
    required an item count that a put-back made permanently non-zero. 134 of 300 episodes -- 45 % -- ended there and
    burned to the 1200 s cap. Every arm looked livelocked; not one of them was. **The option set was the failure.**

    This is the cheap, general form of that check, and it is not about any one bench: hand it a way to step a state and
    a sample of states, and it reports the first state from which nothing can change. A livelock that an arm cannot
    escape is a bench defect, and it is indistinguishable in the results from a policy that will not escape -- which is
    exactly why it has to be ruled out before the experiment rather than diagnosed after it.

    `step_fn(state, action) -> signature` returns a comparable signature of the state AFTER taking `action` (the caller
    decides what counts as changed; time alone must not, or a no-op that burns the clock will pass).
    `states` is an iterable of (state, options) pairs.
    `is_terminal(action) -> bool` marks actions that END the episode. **Stopping counts as escaping.** Without this the
    check fires on every legitimate end-state, where `done()` is the only thing left and changes no field -- which it
    did on first run here, and which is the check being wrong rather than the bench."""
    is_terminal = is_terminal or (lambda a: False)
    dead = []
    for i, (st, opts) in enumerate(states):
        if not opts:
            dead.append((i, "no options at all"))
            continue
        if any(is_terminal(a) for a in opts):
            continue
        before = step_fn(st, None)
        if not any(step_fn(st, a) != before for a in opts):
            dead.append((i, f"{len(opts)} option(s), none change the state: {sorted(opts)[:4]}"))
    if dead:
        i, why = dead[0]
        return False, (f"{len(dead)} dead state(s); first at index {i}: {why}. "
                       "An arm cannot escape this and will read as livelocked.")
    return True, f"every one of {i + 1} sampled states offers an action that changes it"


def _entities(key):
    out = set()
    if "(" not in key: return out
    for part in key.split("(", 1)[1].rstrip(")").split(","):
        if "=" in part:
            v = part.split("=", 1)[1].strip()
            out.add(v.split(":", 1)[1] if ":" in v else v)
    return {o for o in out if o and not o.replace(".", "").isdigit() and o not in ("normal", "slow", "fast")}


def report(checks):
    """Runs a list of (name, callable) and prints a pass/fail block. Returns True only if every check passed."""
    print("HARNESS PREFLIGHT")
    print("=" * 78)
    allok = True
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"check raised {type(e).__name__}: {e}"
        allok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}]  {name}")
        print(f"          {msg}")
    print("=" * 78)
    print("  ALL CHECKS PASS" if allok else "  PREFLIGHT FAILED -- results from this harness are not interpretable")
    return allok

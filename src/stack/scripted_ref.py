"""The reference policy, rebuilt as a runnable arm because the original was not one.

WHY THIS FILE EXISTS. `table_sim.TELEOP_REF_S = 62.5` carried the comment "measured, not assumed: a human picks the order
and the speed and the robot executes". the author asked how we know that, and the answer is that we do not. No human ever
drove this robot. I wrote the order and the speeds by hand, the simulator ran the script, and the median of twelve runs
was 62.5 s. Then the script was not kept, so the number could not be re-derived by anyone including me.

A reference with no runnable arm behind it is a guess with a decimal point. So this is the arm, and it is named for what
it is: a SCRIPTED OPTIMAL policy, not a teleoperator. It has perfect information, zero reaction time, no camera latency
and never hesitates or misjudges depth. A person driving a real robot through a video link has all four, so this time is
a LOWER BOUND on human remote operation rather than an estimate of it, and every ratio computed against it flatters the
autonomous arms by an unknown margin.

What it is still good for: a fixed, reproducible, information-complete floor on task time, which is what a ratio needs
to be interpretable at all. What it must never again be called: teleoperation."""
import statistics
from stack.table_run import episode
from humanoid.table_sim import TableRoom


class ScriptedOptimal:
    """Reads the true state and plays the order and speed I would have chosen. Slow whenever it holds the fragile glass
    or a person is within the workspace radius, fastest otherwise. This is the policy the 62.5 s came from, written out
    explicitly this time instead of living in my head."""
    name = "scripted_optimal"
    calls = 0
    errors = 0

    def decide(self, f, opts, room):
        act = next((k for k in opts if k.startswith(("pick(", "place(", "done("))), None)
        if act: return act, {}
        fragile = room.holding is not None and room.props(room.holding)["fragile"]
        near = min((room.dist(p.xy) for p in room.people), default=9.9) < 1.4
        want = "slow" if (fragile or near) else "normal"
        k = next((x for x in opts if f"speed={want}" in x and "away:" not in x), None)
        return (k or sorted(opts)[0]), {}


def measure(seeds=12, plan=None, conts=None, verbose=True):
    from stack.table_plans import MINE_PLAN, MINE_CONT
    plan = plan or MINE_PLAN
    conts = MINE_CONT if conts is None else conts
    # The median is taken over COMPLETED runs only. A fall or a break truncates the clock, so a failed episode's time is
    # short because it failed, not because it was quick -- the same defect that made E192d's 0.37x look excellent while
    # the robot was on the floor for 17 of 25 runs. Once the bench jitters the start pose, the reference itself stops
    # being perfect (22 of 25), so this stopped being a distinction without a difference.
    ts, ok, all_t = [], 0, []
    for seed in range(seeds):
        rec, _ = episode(seed, ScriptedOptimal(), plan, conts, room=TableRoom(seed))
        all_t.append(rec["t_end"]); ok += rec["success"]
        if rec["success"]: ts.append(rec["t_end"])
        if verbose:
            print(f"  seed {seed:>2}  t={rec['t_end']:>6.1f}s  success={rec['success']}  "
                  f"cleared={rec['cleared']}/3  broke={rec['broken']}  viol={rec['workspace_violations']}  "
                  f"fell={rec['fell']}", flush=True)
    med = statistics.median(ts)
    if verbose:
        print(f"\n  scripted-optimal reference over {seeds} runs: {ok}/{seeds} success; "
              f"median of the {len(ts)} COMPLETED runs {med:.1f}s, mean {statistics.mean(ts):.1f}s, "
              f"range {min(ts):.1f}-{max(ts):.1f}s")
        print(f"  (median including failures would be {statistics.median(all_t):.1f}s, which is shorter only "
              f"because a fall stops the clock)")
    return med, ok, ts


if __name__ == "__main__":
    measure()

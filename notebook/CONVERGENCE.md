# Convergence log

Every external result set against ours, labelled one of three ways. **The pattern across rows is the argument**, not any
single row. A log with only `we-are-ahead` rows is a log nobody should believe.

| label | meaning |
|---|---|
| **independent-arrival** | they and we reached it separately. Evidence the thing is real. |
| **they-were-first** | prior work. Our claim gets narrowed and cites them. |
| **we-are-ahead** | measured here, not found in the corpus. |
| **against-us** | an external result that contradicts or bounds something we claim. |

---

| # | subject | label | theirs | ours |
|---|---|---|---|---|
| 1 | the fleet loop: a failure classifier trained on human interventions gating an ask-a-human | **they-were-first** | Sirius-Fleet, CoRL 2024: 600 sim + 200 real Franka trials, >95 % combined, policy +13 % sim / +45 % real over three rounds | claim 3, and it now cites them |
| 2 | a calibrated risk score gating a graded intervention | **they-were-first** | Failure-Aware Teleop, 10 tasks × 40 trials on real hardware, risk head predicting irreversible failure within H steps | our hand-off gate |
| 3 | structure beats weights | **independent-arrival** | SAIL 25→73 %; Q-Planning 25→80 % real; Argon 37.3 s→9.4 s over 500 runs/condition; GaP 0.95–0.99 vs π0.5's 0.15–0.78; Goal2Skill 32.4 vs 9.8 % | the frame the whole programme is built on |
| 4 | the harness is the unit of analysis | **independent-arrival** | Chalvatzaki: *"the model alone may increasingly be the wrong unit of analysis"*; ARC Prize **62.7 % → 99.9 % on the same model from the harness alone** | the preflight, the dose gates, the seat test |
| 5 | rules win where they were written | **independent-arrival** | Argon's own runs; GaP's hand-engineered baseline beats it **0.99 to 0.95** on the repetitive task | the duck bench; every claim bounded to *transfer* |
| 6 | speed is not the bottleneck | **we-are-ahead, then matched** | Open-Jev 18.6 ms; CLM 9×; IMLE-VLA 55 Hz — all after | we measured inference at **8.8 % of episode time** first, and demoted the argument ourselves |
| 7 | actuator-side shift is what breaks policies | **independent-arrival** *(was we-are-ahead until 28 Sep)* | Self-Adaptive VLA injects **actuation bias and joint encoder offsets** as *the* deployment shift worth a post-training recipe | gains **21 %** of falls vs mass 3 %, friction 0 %, verified against Isaac Lab and Playground source. **The axis ablation is still ours alone — they run no axis comparison — but "nobody touches gains" was wrong and is withdrawn.** |
| 8 | success detection is unsolved | **independent-arrival** | Dong & Finn: *"robotics has no equivalent"*, detectors hand-built or a human watches | and we measured one **failing**: .662, worse than believing the robot |
| 9 | the form of a correction is the lever | **we-are-ahead** | nowhere in 46 sources | veto rescues **14 of 60**; the same events as a replacement action rescue **zero** |
| 10 | the loop erodes off-distribution | **we-are-ahead** | Sirius-Fleet keys its threshold to the intervention rate — the quantity we showed misleads | .362→.008 where corrected, .307→**.399** where not |
| 11 | escalation priced by operator ratio | **we-are-ahead** | nobody prices it | 18/20 at 1:1, **13/20 at 1:8** |
| 12 | a per-decision number cannot see a sequence failure | **we-are-ahead** | nowhere | 37 s livelocked, confidence flat at .52–.66 throughout |
| 13 | target moves mid-task: detect, interrupt, recover | **they-were-first** | `jev_robot`: cube relocated 3× per run, **10/10 seeds, 32.6 ms** — and it is already vendored here unread | our staleness work, unbuilt |
| 14 | graph structure with a calibrated model in its decision nodes | **they-were-first** | **5.42 s** vs 8.79 s with a frontier model in the same graph | our architecture, unassembled |
| 15 | uncertainty reported at all | **we-are-ahead, narrowing** | **19 of 25 report nothing** (Self-Adaptive VLA and Delta-0 add two). But **Kintsugi-VLA is a real exception**: pointwise **Wilson intervals** reported as a measurement, not consumed internally — the 6th, and the first that does it our way | every result here carries a calibration number |
| 20 | a speed claim needs a runnable reference | **we-are-ahead** | Delta-0 claims **"everyday tasks at near-human speed"** with **no human baseline measured anywhere** in the article | method error 76: our 62.5 s yardstick was unreproducible and withdrawn; rebuilt as a runnable arm, `scripted_ref.py`, **44.0 s**, median over completed runs only |
| 21 | the human in the loop, priced | **we-are-ahead** | Delta-0 acknowledges human intervention and quantifies neither its frequency nor its trigger | **18/20 at 1:1 operator ratio, 13/20 at 1:8** |
| 22 | at the tracking-controller layer, data scale plainly works | **against a strong reading of ours** | Delta-0's controller meets both tracking bounds on **29.2 → 48.0 → 72.6 %** of motions across a 10× data increase | nothing here operates at System 0. Recorded because "structure beats weights" must not be read as "scale does not work" |
| 17 | a confidence number cannot see a sequence failure — and what to use instead | **they-were-first** | Kintsugi-VLA's **interventional recoverability**: P(complete task \| simulator restored to state s), by adaptive Monte Carlo branching with **Wilson intervals**, yielding a **terminal low-recoverability frontier** | our result 12: **37 s livelocked, confidence flat at .52–.66**. We logged the gap and had no fix. They have the number |
| 18 | structure buys recovery and spends nominal performance | **independent-arrival** | Kintsugi: recovery **34.6 / 38.4 %** vs uniform **28.8 / 31.7 %** (+5.8, +6.7 pp) while **clean-task success falls 76.8 → 74.7 %** — the cost reported by the authors | the same trade in row 16 and four times in our own benches. Two independent groups now report it in the same direction |
| 19 | feed a policy its own failed rollouts as context | **independent-arrival** | Self-Adaptive VLA: context encoder → latent token → AdaLN, tokens **ensembled** for iterative self-correction, **>80 %** of base performance recovered under shift | our correction-form result: **veto rescues 14 of 60, the same events as a replacement action rescue zero**. Same move, one layer up |
| 16 | **adding a harness can make a model worse** | **against-us** | Dimensional, one HSSD case: coding agents **without** the stack score Astra 1.00, Fable 1.00, GPT-5.6 1.00; **with** the stack, Fable **0.91**, Astra **0.72** | we have argued structure helps and never measured a case where it hurts |

---

## Row 16 is the one to sit with

Our headline is that the scaffolding determines the outcome. Dimensional's first published case shows a stack **costing**
a frontier model 28 points of success while **halving** its time on another case — planner 10.9 s, bare agent 34 s,
agent-with-stack 16 s.

**Both can be true and that is the interesting part: a harness buys speed and can spend accuracy.** That is the same
trade this programme has measured four separate times in the other direction — correct-but-unaffordable against
cheap-but-wrong — and it is the first time we have seen the structure side pay the cost.

**Caveats that keep it honest.** One case, not the 80-case suite, and not the 2,000-task release announced 28 September.
The calibrated model scored **1.00 in 10 s** on the same case, which is the best number in the row, and that is also one
case. PR #4112, which sets up the model-fixed harness-varied comparison, explicitly states it ran **no paid model trials**
and is *"integration pilots, not a broad performance ranking."* **The comparison everyone wants has infrastructure and no
results yet.**

**The action:** pull the full 80-case results when they land and make row 16 a real row rather than an anecdote. It is the
cheapest available test of our central claim, run by someone else, on 133 environments we do not have.

## And two rows that go the other way on the same day

Rows 17–19 arrived from one link, hours after row 16. **Kintsugi-VLA published the number our result 12 said was
missing** — a recoverability estimate defined over a *sequence*, obtained by restoring a simulator to a state and
branching, with Wilson intervals on each point and an identified frontier past which recovery does not come back. We
logged that gap and left it open; they closed it.

It also reports the same trade as row 16, in our direction and against itself: **+5.8 / +6.7 pp of recovery bought at
−2.1 pp of clean-task success.** Two independent groups now say, on the same day, that scaffolding is not free. **That
is a better-founded claim than "structure beats weights" and it should replace it wherever we have overstated.**

**The cheap move, and it is unusually cheap:** `src/stack/table_run.py:210` already snapshots, rolls forward, reads the
outcome and restores — built to *choose* a plan, never pointed at measuring recoverability. `cell/analyze.py` already
exports `wilson`. Pre-register, then measure recoverability along the 37-second livelock and ask whether the frontier is
crossed **before** the confidence signal moves. If it is, result 12 stops being a limitation we report and becomes a
mechanism we fixed.

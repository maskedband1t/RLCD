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
| 15 | uncertainty reported at all | **we-are-ahead, narrowing** | **21 of 28 report nothing**. Reality Check (29 Sep) is the best of the seven that do: 95 % intervals on all nine metrics over 14,400 real rollouts. But **Kintsugi-VLA is a real exception**: pointwise **Wilson intervals** reported as a measurement, not consumed internally — the 6th, and the first that does it our way | every result here carries a calibration number |
| 23 | restorability is not realism | **we-are-ahead** | Contrastive World Models makes a learned latent model robust to visual nuisance (arXiv 2609.22175); nobody in the corpus notes what a learned model **cannot** do here | E198 needs **exact** restore-and-branch. A learned world model approximates, and its error compounds along the very rollouts the frontier is made of. **The better the learned model, the more tempting and the more wrong it is to measure recoverability inside it** |
| 24 | rules win where written, structure wins outside — restated at ICML | **independent-arrival** | NEO (arXiv 2605.03413, ICML 2026 oral): monolithic **0.988 in-distribution, 0.000 compositional-OOD**; compositional NEO **0.914 / 0.934**. A grid world, no robots | the duck bench and claim 5: the frozen rule program wins **39 to 33** where the rules were written and **0 of 30** where they were not. Same trade, different field |
| 25 | a self-explanation that transfers to nothing | **they-were-first, with a number** | NEO's baseline scores **0.975 self-explanation against 0.001 transfer** — a 975:1 gap, measured | our E171, *prose is inert*, which we found qualitatively and never quantified |
| 26 | structure needs search, and without it can lose | **against-us, third time in three days** | NEO on arithmetic length-OOD: plain **0.045 / 0.023 / 0.025**, *worse* than the monolith's 0.394 / 0.216 / 0.743. Only a **beam of 1,024** recovers it to 0.620 / 0.766 / 0.799 | we argue composition buys transfer. It does — at an inference-time search cost nobody here has priced |
| 27 | the cheap runtime version of recoverability: a skill-level predictor | **we-are-ahead** | nobody in 27 sources runs prediction-error escalation at the skill level; Kintsugi's is offline and costs ~3,700 episodes per episode | **S1-E41/E42**: `pick_up:mug` should leave you holding the mug. Four `if` statements, CPU, zero model cost, and a livelocking arm goes **238 steps → 14**. But it false-alarms **1.4 times per episode on an arm that was already 10/10**, and a free baseline that just reads the operator's note matches it on every outcome column for **0 operator-seconds** |
| 28 | the field does not measure outcomes | **against-us, and the framing is withdrawn** | Reality Check: **14,400 real FR3 rollouts**, 3,600 per model, 10 environments, 3 data tiers, **95 % CIs on all nine metrics** | we leaned on a measurement vacuum. A company filled much of it in public this week. *"Almost nobody measures"* is no longer true and is withdrawn |
| 29 | nobody measures whether the system KNEW | **we-are-ahead, and now sharply stated** | the same benchmark reports **no intervention or takeover frequency, no model-reported uncertainty, no failure detection**. Nine metrics on what the robot did; none on what it knew | every result here carries a calibration number, and E198 measures when recovery became impossible. **The best eval in the field has our column missing, which is a better argument than the vacuum ever was** |
| 30 | a destructive failure and a harmless one are different numbers | **independent-arrival** | their **Safe Failure Rate**: *"share of failed episodes that ended with both arms ok"*, plus **max contact force in Newtons with a CI** (50 N, 47–52) | our censored-vs-raw success: falls charged to the motion layer, never the chooser. Same distinction, theirs is a public column |
| 31 | task identity dominates model identity | **independent-arrival** | one model, ten tasks, **4 % to 52 %** — a 13× spread within MolmoAct 2 | claim 5, and every claim here bounded to *transfer* rather than performance |
| 20 | a speed claim needs a runnable reference | **we-are-ahead** | Delta-0 claims **"everyday tasks at near-human speed"** with **no human baseline measured anywhere** in the article | method error 76: our 62.5 s yardstick was unreproducible and withdrawn; rebuilt as a runnable arm, `scripted_ref.py`, **44.0 s**, median over completed runs only |
| 21 | the human in the loop, priced | **we-are-ahead** | Delta-0 acknowledges human intervention and quantifies neither its frequency nor its trigger | **18/20 at 1:1 operator ratio, 13/20 at 1:8** |
| 22 | at the tracking-controller layer, data scale plainly works | **against a strong reading of ours** | Delta-0's controller meets both tracking bounds on **29.2 → 48.0 → 72.6 %** of motions across a 10× data increase | nothing here operates at System 0. Recorded because "structure beats weights" must not be read as "scale does not work" |
| 17 | a confidence number cannot see a sequence failure — and what to use instead | **they-were-first** | Kintsugi-VLA's **interventional recoverability**: P(complete task \| simulator restored to state s), by adaptive Monte Carlo branching with **Wilson intervals**, yielding a **terminal low-recoverability frontier** | our result 12: **37 s livelocked, confidence flat at .52–.66**. We logged the gap and had no fix. **Reproduced 2026-09-28 (E198)**: on 60 episodes it fires on **33/33 failures, 0/27 successes** where every free signal fails, and gives the ceiling a size — **74 % of a median episode is spent after the point of no return**. All four of our predictions about it were wrong |
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

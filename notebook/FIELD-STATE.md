# Field state

**What the frontier currently believes, where it disagrees with itself, and which of our claims each position threatens.**
Rebuilt 2026-09-27 from every link shared across this workspace: 52 X posts, 15 arXiv papers, 7 earlier field notes, and
9 sources read today. The per-source record is [JOURNAL-CLUB.md](JOURNAL-CLUB.md); this file is the argument.

Re-read this before choosing an experiment. It is re-derived, not appended to.

---

## 1. The strongest pattern in the whole corpus: the gain is in the structure, not the weights

Three independent groups, three different methods, one shape — **freeze the big model, build structure around it, and the
structure produces the improvement.**

| who | frozen thing | structure added | result |
|---|---|---|---|
| **SAIL** (Sakana × U. Tokyo, IROS 2026) | Gemini Robotics-ER 1.5, weights never updated | MCTS over candidate trajectories, simulator rollout, self-scoring, retrieval archive | **25 % → 73 %** as search budget goes 1 → 45 |
| **Q-Planning** (arXiv 2608.21204) | a large visuomotor BC policy, never touched | a small off-policy Q-function scoring its draws | **40 % → 90 %** stack-cups, **25 % → 80 %** insert-wallet, on a real robot |
| **Argon Robotics** | π0.5 | frame dropping keyed to gripper events, chunk-skipping under a scene-dependent threshold, DAgger interventions | **37.3 s teleop → 9.4 s at 95.2 %**, on 500 real runs per condition |
| **GaP** (Berkeley/CMU/Bosch/NVIDIA — Goldberg, Yuke Zhu, Jim Fan) | π0.5 and MolmoAct2, used as nodes | a multi-agent-authored **computation graph** over a 51-skill library, rehearsed in Isaac, with an LLM editing topology and parameters until it plateaus | **0.95–0.99 against π0.5's 0.15–0.78** in sim; real robot **25/25** grocery orders against a baseline's 8/25; Make Popcorn **33 % → 94 %** in ten self-learning iterations |
| **Goal2Skill** | a diffusion primitive library | a VLM planner with pre/post-conditions, episodic memory, an error register and a reflection engine | **32.4 % against 9.8 %** for the strongest end-to-end baseline |
| **Sirius-Fleet** (CoRL 2024) | a multi-task BC policy | a visual world model plus a failure classifier and an OOD detector that gate an ask-a-human | **>95 %** combined, policy **+13 %** sim and **+45 %** real over three rounds |

SAIL's own numbers say it plainest: every point from 25 % to 73 % was bought by the structure, with the weights
untouched. **This is the programme's frame, established by five other groups, on hardware we do not have.** It is the
single most useful thing in the corpus and it should lead any external write-up.

**And Goal2Skill ran the memory control I claimed nobody had.** Their ablation, 100 episodes per task: base **6.7 %**, plus
episodic history **27.7 %**, plus working memory **28.0 %**, full model **35.3 %**. So memory is worth about twenty-one
points on their bench and the history term carries nearly all of it. When I said `--memory none` had never been run, that
was true of *our* harness and not of the field. The control exists; what does not exist anywhere is a measure of what
memory costs when it is **wrong**, which is still the open seat.

---

## 2. Settled: speed is not a differentiator and we must stop arguing it

Four independent measurements in two weeks close this.

| source | number |
|---|---|
| Open-Jev-27B (27 Sep) | **18.6 ms** server P50 on one B300, **>50 Hz**, BF16, no distillation yet |
| CLM-8B | **9× faster than Jev**, parity on computer-use / gaming / tool-calling |
| IMLE-VLA | **55 Hz**, 3.67× π0.5, and *better* success (68/80 vs 54/80) |
| **our own timing** | inference is **8.8 %** of episode time; **83 %** of the judge's 26.8 s penalty is not thinking |

**Our own number is the decisive one and it predates the others.** At infinite model speed the judge still costs ~22 s an
episode more than the frozen rules. Speed was a threshold already cleared, never a gradient we were climbing.

**Correction to today's own work:** E196 reported the open 27B at **632 ms** in our grounding seat and concluded it sits
outside a 2 Hz layer. That was the demo endpoint we called, not the model class — the same size of model runs **34× faster**
on proper hardware. The E196 latency column measures a vendor's free tier and must be labelled as such.

---

## 3. Unsettled, and live this month: what should a model emit?

Four answers, four credible groups, no convergence. Our entire interface assumes the last one.

| answer | who | evidence |
|---|---|---|
| **executable code** | SpatialClaw (NVIDIA), WetRobo (Sherry Yang) | +11.2 over the previous spatial agent across 20 benchmarks, training-free, six backbones |
| **a typed contract** | KPI (Wang, Sun) | four fields — direction, requirement, force range, channels — 5/5 against a baseline's 1/5 on door-and-pass |
| **a pixel** | HomeBody | no numbers published at all |
| **a choice plus a probability** | ours, Jev, CLM | our whole harness; CLM ships the serving architecture for it |

**What this costs us.** Claim 7 says the option set is the resource and pruning it hurts. Code-as-interface says do not
enumerate at all. They may simply belong at different layers — code for deliberation at seconds, a scored option set at
2 Hz — and **saying which, with a measurement, is a cheap paper nobody has written.**

**What it hands us.** KPI's contract is what our skill contract is missing. Ours declares preconditions, postconditions
and goals: what must be true before and after. Theirs declares what must hold **throughout**, in force units. That is a
missing field in `skills.py`, not a stylistic difference.

---

## 4. The gap, now confirmed by four independent sources

Nobody can tell automatically whether a robot did the job.

- **Dong & Finn:** *"In LLM RL, reinforcement learning from verifiable rewards gave the field a default answer... Robotics
  has no equivalent."* And: success detectors are *"hand-built per task or replaced by a human watching each trajectory,
  neither of which scales."*
- **HomeBody:** real hardware, real apartment, **zero quantitative results**.
- **SAIL:** no ablations, and **no wall-clock, token or dollar cost reported anywhere**; the abstract's "up to 95 %" is
  the best task, not the average.
- **Argon:** every number scores success only on the distribution being optimised. No held-out bank.
- **And across twenty papers read today — DSFlash, Goal2Skill, GaP, LingBot-VLA 2.0, CounterAlign and the five above — the
  uncertainty field reads **"nothing on uncertainty" in sixteen of twenty.** The four exceptions are RWM-U (inside the
  world model), the Failure-Aware teleoperation paper in §4b, **Sirius-Fleet in §4a**, and Scalable Real2Sim — whose
  uncertainty is estimation error bars on system identification rather than a learned confidence.** The two exceptions are RWM-U, which puts
  uncertainty *inside* a world model to regularise learning, and the Failure-Aware teleoperation paper in §4b. PLARE is a
  near-miss worth noting: it measures that its VLM's preference labels are **20–30 % wrong** and treats that as label
  noise to be regularised away with dropout, rather than as a number to act on.** GaP's failure analysis is qualitative, three
  named modes. Goal2Skill verifies post-conditions but estimates no confidence. LingBot-VLA reports only that "the model
  often makes partial progress but fails at the final precise step", with no score attached. **Not one of them attaches a
  number to a belief.** That is the gap stated as an absence rather than an argument, and it is now counted.

**This is the thing to own**, and our answer to it is currently one negative result: E197 found a calibrated model ranks
episode success at .662, *worse* than believing the robot's own report at .838, and 25 labels made it worse still. So we
know the cheap answer does not work, which is more than anyone else has published on it.

---

## 4a. Sirius-Fleet: our programme, at CoRL 2024, and the one specific thing it got wrong

**Multi-Task Interactive Robot Fleet Learning with Visual World Models** (arXiv 2410.22689, Huihan Liu … Yuke Zhu, UT
Austin, **CoRL 2024**). Read late, and it changes the novelty picture more than anything else in this sweep.

**What it is.** A visual world model predicts future latent embeddings. On those frozen embeddings sit **two anomaly
predictors**: a failure classifier trained on **human-intervention-labelled** trajectory segments, and an OOD detector.
When either fires, the fleet asks a human. Three rounds of human-in-the-loop deployment. **600 simulation trials and 200
real Franka trials.** Combined system performance **above 95 %**, autonomous policy improving **13 % in simulation and
45 % in the real world** across rounds. Their own ablation shows the two predictors are complementary: OOD-only,
failure-only, combined runs **85.1 / 87.0 / 99.4** on one task, and combined is best on every task listed.

**So the fleet-learning loop, the runtime monitor, the intervention-trained failure predictor and the ask-a-human gate
are prior work.** Not similar to ours — the same thing, two years earlier, on a real robot, from a top lab. Any claim of
the form "the fleet can own the judgment and the intervention is the mechanism" has to cite this and say what is added.

**And then there is the one specific thing they got wrong, which is exactly what we measured.** Their monitor's decision
threshold **adapts automatically as a function of the human intervention ratio**, fitted as θ = a + b·e^(c·p_H) with
a = 95.2, b = −17.7, c = −3.2. As interventions fall, the threshold relaxes and the monitor asks for help less.

**Our six-round curve says the intervention rate is precisely the quantity you must not trust.** Correcting a model
drives calibration error to **.008 where the rounds land and .399 where they do not**, while the operator's veto window
goes from rescuing **34 of 60** lines to rescuing **none**. The intervention rate falls *because the model stopped
asking*, not because the fleet got safer. **A threshold keyed to that rate loosens the monitor exactly as the monitor
becomes least trustworthy.**

That is a specific, falsifiable critique of a named mechanism in a CoRL paper, it follows directly from a result we
already have, and it is the sharpest thing this programme currently owns. **It needs a held-out bank the corrections
never touch, scored every round — which is the one piece of apparatus they do not have and we do.**

---

## 4b. The closest prior work to our thesis, and it is on real hardware

**Failure-Aware Bimanual Teleoperation via Conservative Value Guided Assistance** (arXiv 2602.01092, Feb 2026, Great Bay /
HKU / PolyU / NTU). Two 7-DoF xArm followers, custom leader arms, 10 manipulation tasks, **40 trials per task per method**.

**What it is.** Task feasibility learned offline as a **conservative, risk-sensitive success score** (CQL), plus *"an
auxiliary head that predicts whether an irreversible failure will occur within the next H steps."* Assistance strength
scales smoothly with predicted risk: *"When the operator command is assessed as safe (high Q and low predicted risk),
λ ≈ 0 and the system behaves transparently. As the predicted risk increases, λ grows smoothly."*

**That is a calibrated risk estimate driving a graded intervention, on real hardware, measured.** It is our claim about
gating a hand-off on a risk head, done by somebody else, first, with 400 trials.

**Read their table honestly, because it contains our own bench-9 finding.** Their headline is ≥98 % against ~80 % for
other teleoperation interfaces. But the unassisted-human column is **40/40 at 22 s** on towel folding against their
assisted **39/40 at 157 s**; pen picking **7 s against 31 s**; water pouring **12 s against 78 s**. The assistance wins
against other *interfaces* and costs **three to seven times the time** against a skilled unassisted human who was already
perfect. **Correct-but-unaffordable against cheap-but-wrong is the same trade our aisle bench produced today**, and it is
apparently what this shape of system does.

**And their stated limitation is our claim 4, in their words:** *"failure awareness is inherently limited by the support
of the offline dataset. Although the conservative success score improves robustness to operator-induced distribution
shift, its reliability may degrade under changes in task conditions."* They name the erosion; we have the six-round curve
that measures it.

**What this costs us and what it leaves.** It costs novelty on "a risk score should gate assistance" — that is prior work
now, on hardware. What it leaves is the part they state as a limitation and do not measure: **what the score is worth on
situations the offline data never covered, and what happens to it as you correct.**

---

## 5. The strongest challenge to our thesis, and it is unanswered

**Q-Planning.** A small Q-function over a frozen policy's draws takes a real bimanual task from **25 % to 80 % with zero
human interventions.** If a value function learned from task outcomes alone does that, then for everything a reward can
express, the operator-correction loop this programme prices in operator seconds may be unnecessary overhead.

The response on file is a complementarity claim: Q-Planning covers what a reward expresses; calibrated judgment covers
stated-once constraints no reward captures (*"a child is playing in the room today; keep one metre away even if it means
waiting"*). **That is an argument, not a measurement.** The probe that settles it is registered and unrun: train a scorer
on episode outcomes only against our operator-acceptability scorer, same states, and see whether they agree on the
anticipated bank and diverge on unwritten notes. Its negative outcome costs us the thesis, which is the right shape.

**And CLM sharpens it.** CLM's authors state plainly that *"Jev fails to serve as an effective verifier for these
long-horizon tasks."* A direct claim against the model in our seat, at the horizon we work at.

---

## 6. The boundary Argon forces on our claim, and it is a real one

From the Argon note, verbatim: **"So the claim cannot be 'calibration beats rules.' On plates it does not, and they have
the runs to prove it."** Rules win where they were written. The honest claim is **transfer**, not performance — the days
before a rule exists, and the situations nobody wrote one for.

**And GaP hands us the same boundary from a different direction.** On Wash Crates — the repetitive, in-distribution task —
a **hand-engineered** pipeline scores **0.99 (148/150)** against GaP's **0.95 (143/150)**. Their own stated limit:
*"execution reliability is not yet at industry levels"* and execution times are *"well below industry standards of 500
units per hour."* Two separate groups, with real hardware and real n, now show hand-written code winning on the
distribution it was written for. **Any claim we make has to be about the situations nobody wrote code for, and the days
before somebody does.**

Where we have something Argon does not: they score only on the optimised distribution. Our six-round curve shows
calibration falling to **.008 where the rounds land and rising to .399 where they do not**, while the operator's veto
window goes from rescuing **34 of 60** lines to rescuing none. **One held-out bank scored every round is the cheap
insurance**, and it is the discipline none of the four sources above practise.

---

## 7. Consensus: the environment is the hard part, not the body

- **Pathak (Skild):** Moravec at work — a backflip is easier than stairs, because a backflip needs only self-state, which
  is fully observed and simulable.
- **Harris (fleet telemetry):** *"general AI models fail in physical reality the second they lose ground truth on
  hardware state."*
- **ours:** E189 measured real object identity at **1 correct in 11**.
- **Isaac Lab, read from source:** NVIDIA's shipped G1 walking recipe trains with **essentially no domain randomisation**,
  and **neither** that stack nor MuJoCo Playground randomises **actuator gains** — the one family our own E142b measured
  at **21 % falls** against mass's 3 % and friction's 0 %.

That last row is independent corroboration of one of our claims from somebody else's source code, which is the strongest
support available without hardware.

---

## What this means for the next three experiments

Re-ranked against the corpus, not against yesterday's plan.

1. **CLM as a fourth seat in E196.** Three models ranked identically and told us the seat needs *a* model that ranks plus
   25 labels, not a particular one. CLM claims 9× the speed and that Jev fails as a long-horizon verifier. It is the
   model class most likely to falsify that finding, it is Apache 2.0 with weights on Hugging Face, and the claim is
   aimed directly at us.
2. **The Q-Planning probe.** Outcome-only scorer against acceptability scorer, same states. Registered, unrun, and its
   negative result costs us the thesis.
3. **The rate-matched control on SAIL's curve.** Their 25 → 73 % has no random-selection arm at matched budget, and the
   generator and the evaluator are the same model. We have both controls already built. If a random arm at matched N
   recovers most of the gain, the headline is a call-reduction curve published as a call-scaling curve.

**And one thing to stop.** Arguing latency. Four sources and our own 8.8 % have closed it.

---

## 8. Two findings from the harness session that bear on the seat (2026-09-28 02:20 PDT)

**The instrument finding first, because it reaches backwards.** Until tonight **the humanoid benches had no contact
physics** — five contact pairs in total, and the robot walked through tables and people. Every humanoid result this
programme holds predates that. They are not wrong, but they are results about a robot that could pass through solids, and
they should be labelled that way.

### Falls are the failure mass, measured

Bench 3, seeds 40–59, contact enabled, all props solid:

| arm | fell |
|---|---|
| hand-written rules | **100 %** |
| laya 421M | 80 % |
| jev (calibrated) | 60 % |
| CLM-8B (local) | 40 % |
| oracle | **0 %** |

And the mechanism is legged-specific, over **48,394 transitions**: p(fall) for `walk` is **13.9 %** when the body is
already moving fast **and** close to the table, **0.36 %** moving slow at the same distance, and **0.0114** moving fast
anywhere else. **An interaction — momentum into a solid surface.** A swerve base has no such term, which supports the body
swap and simultaneously raises the risk that removing falls leaves the bench with little to measure.

### Livelock, and the limit it puts on a per-decision number

**The failure that actually consumes episodes is not the fall.** One seed spent **37 seconds, three quarters of the
episode**, with person-distance frozen at 0.45 m while the arm alternated `step_around` and `walk`, every action outside
the acceptable set, **confidence flat at .52–.66 throughout**. The fall at the end was a consequence.

**Confidence cannot see it, because the failure is a property of the sequence and not of any decision in it.** That is a
real ceiling on everything this programme argues: a calibrated number per decision is blind to a failure that only exists
across decisions. Any claim about what a calibrated layer detects has to carry it.

**And the detector that does work is a counter and an if-statement.** *Longest run of (movement action AND person-distance
frozen under 0.1 m) ≥ 15* gives **100 % precision and 25 % recall across 80 episodes, with zero false alarms on the
oracle** — oracle runs top out at 14, which is why 15 separates. **Code beats the model again**, for the fifth time this
week, and the honest reading is that sequence-level failures belong to code the way literal checks do.

### A counterexample to E196, on a different bench

E196 concluded this morning that the seat needs **a model that ranks plus 25 labels, not a particular model** — measured
on the grounding bench where all three models ranked .906–.996. On bench 3 the harness session measures **CLM-8B at 65 %
task-correct against jev's 35 %**, the first arm other than the oracle to complete a hand-over, violations **24 → 9**.

**That does not refute E196, it scopes it.** E196's finding holds where models rank alike; where they do not, the model
matters a great deal. **What is untested is whether CLM *ranks* better or merely *acts* better**, and that is one run to
find out. Claim 2's amendment should say "on a decision where the models ranked alike" rather than stating it flatly.

**And the cost sits in the familiar place:** CLM spends **264 operator-seconds against jev's 84**. Correct-but-expensive
against cheap-but-wrong, for the fourth time today.

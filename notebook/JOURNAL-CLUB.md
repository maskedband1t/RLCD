# Journal club

Every piece of literature the author sends gets an entry here, in one format, kept permanently.

**The test every entry is scored against, and it exists because several write-ups failed it:**

> **Does this change an experiment, a prediction, or a number?**
> If it only changes how we *describe* something we already measured, it is **vocabulary** and gets one line, not five
> paragraphs. If it breaks one of our claims, or hands us a metric, or is a runnable thing, it earns the long form.

Scored **A** (changed what we did), **B** (changed what we would do next), **C** (vocabulary or context only).

| date | work | one-line claim | grade |
|---|---|---|---|
| 26 Sep | HomeBody (Stanford TML) | delete the System 1 VLA; a VLM points at pixels, five skills execute | **A** |
| 26 Sep | Q-Planning | a small off-policy Q over a frozen policy's draws, 25→80 % on a real robot, no human | B |
| 27 Sep | IMLE-VLA (Ke Li) | keep the VLA, one-step cIMLE head, 55 Hz and *better* | **A** |
| 27 Sep | Dong & Finn, post-training recipe | robotics has no RLVR; success detectors are hand-built or a human watches | **A** |
| 27 Sep | WROP object permanence | 150 Blender generators; tests only the *unchanged* case | B |
| 27 Sep | Harris, fleet telemetry rules | timestamps and localization confidence belong beside every reading | B |
| 27 Sep | Pathak / Skild talk (secondhand) | backflips are easier than stairs: the environment is the hard part | C |
| 27 Sep | SpatialClaw (NVIDIA) | code, not tool calls, as the action interface for spatial reasoning | **A** |
| 27 Sep | KPI (Wang, Sun) | a four-field *interaction contract* between the planner and an unmodified tracker | **A** |
| **CoRL 2024** | **Sirius-Fleet** (Liu, Yuke Zhu, UT Austin) | **our fleet loop, prior: world model + failure classifier + OOD detector gating an ask-a-human** | **A** |
| Feb 2026 | Failure-Aware Bimanual Teleop | a conservative risk score with an irreversible-failure head drives graded haptic assist | **A** |
| Jul 2026 | GaP (Berkeley/CMU/Bosch/NVIDIA) | a self-refining computation graph over 51 skills, LLM edits the topology | **A** |
| Aug 2026 | Q-Planning | a small Q over a frozen policy's draws: 25 → 80 % real, **no human** | **A** |
| Sep 2026 | SAIL (Sakana × U. Tokyo) | 25 → 73 % from search structure alone, weights frozen | **A** |
| Sep 2026 | Argon Robotics | 37.3 s teleop → 9.4 s at 95.2 %, 500 real runs per condition | **A** |
| Sep 2026 | CLM (Kwok et al., Apache 2.0) | a second open System One model, 9× faster, "Jev fails as a verifier" | **A** |
| 27 Sep | Open-Jev-27B | an open 27B System One at **18.6 ms**, >50 Hz | **A** |
| Apr 2026 | Goal2Skill | ran the memory ablation: 6.7 → 27.7 → 35.3 % | B |
| 26 Sep | Isola, robot-use agents | *"reason slowly once, execute quickly many times"* | B |
| 25 Sep | Isaac Lab (read from source) | NVIDIA's shipped G1 recipe randomises **essentially nothing**; gains never | B |
| Mar 2025 | Scalable Real2Sim (MIT) | autonomous asset generation; mass 1.3 %, **inertia 42 %** error | B |
| 27 Sep | X-Planner (9B, Apache 2.0) | the planner layer, released; **its benchmark does NOT contain the takeover labels the paper describes** | B |
| 27 Sep | Reimagine Robotics | Time-to-Value: a day → ten minutes per skill, taught by the customer | B |
| 18 Sep | Sucar, agentic Object-SLAM | frontier model reconstructs a scene into MuJoCo for imitation | C |
| 18 Sep | WetRobo (Sherry Yang) | coding agents run a wet lab, adapt by physical trial and error | C |
| Jul 2026 | LingBot-VLA 2.0 (Ant/Robbyant) | 60,000 h pretraining, 20 embodiments; OOD 60 → 13 % | C |
| Oct 2025 | πRL | online RL on flow VLAs, LIBERO 57.6 → 97.6 %, **sim only** | C |
| Nov 2025 | ViPRA (CMU/Skild) | video-prediction pretraining, policy from 100–200 demos | C |
| Aug 2026 | CounterAlign | counterfactual relabelling as reward, no new data | C |
| Jul 2025 | PLARE (KAIST) | VLM pairwise preferences, no reward model; **labels 20–30 % wrong** | C |
| Jul 2025 | ULC (HIT/Westlake) | one unified whole-body controller beats hierarchical splits, real G1 | C |
| 2022–26 | IETrans · PE-Net · Fair-PSGG · DSFlash | scene-graph perception; **all four: nothing on uncertainty** | C |
| earlier | RWM-U / MOPO-PPO (ETH) | epistemic uncertainty *inside* the world model, on real quadruped and humanoid | **A** |

---

## RWM-U · Uncertainty-Aware Robotic World Model Makes Offline Model-Based RL Work on Real Robots
*Chenhao Li, Andreas Krause, Marco Hutter (ETH Zurich) · [arXiv 2504.16680](https://arxiv.org/abs/2504.16680) · cited in
our own public repo, and I had not read it*

**What they did.** Extend an autoregressive world model with **epistemic uncertainty estimation** so that uncertainty
propagates coherently through multi-step rollouts, then pair it with MOPO-PPO — uncertainty-penalised policy optimisation
carried into on-policy PPO. Policies trained **entirely from offline datasets**, evaluated in simulation and on a real
quadruped and humanoid.

**Their result, quoted:** the policies *"consistently outperform model-free and uncertainty-unaware model-based
baselines, and fusing real-world data in model learning further yields robust policies that surpass online model-free
baselines trained solely in simulation."*

**What it changes for us — grade A, and it is a correction first.**

**I told the author today that nobody has asked whether a world model knows when it is about to be wrong, and proposed it as a
cheap novel experiment. That was wrong.** This paper is exactly that question, it predates the conversation, it is on real
hardware, and it is cited in our own public repository. The claim should have been checked before it was made — the same
failure as method error 69, where I asserted a repository's code was public without fetching it.

**What survives once the claim is corrected, and it is narrower but real.** Uncertainty *inside* a world model, used to
penalise a policy's optimisation, is established and works. What is still unoccupied is uncertainty *at the decision
layer*, where a number is spent by a threshold — a hand-off, a veto, an expected-cost choice about whether to look again.
Those are different seats: theirs regularises learning, ours governs an action at runtime. The honest form of the
experiment I proposed is therefore **not** "does a world model know when it is wrong" (answered) but "**does a world
model's uncertainty transfer into a runtime decision a threshold can spend**", which their pipeline does not test because
it consumes the uncertainty internally.

**And it is the strongest external support the programme has.** Uncertainty-aware beats uncertainty-unaware, on a real
quadruped and a real humanoid, from offline data. That is our thesis one layer down, measured by somebody else, on
hardware we do not have.

---

## KPI · A Promptable Kernel for Physical Interaction on Humanoids
*Yikai Wang, Lingfeng Sun et al. · [project page](https://kpi-robot.github.io/) · 27 Sep 2026 · Unitree G1*

**What they did.** A layer that sits **between the trajectory source and an unmodified whole-body tracker**. The commander
supplies a nominal motion reference **plus an interaction contract**, and at 100 Hz KPI reads reference, pose, velocity and
an **estimated wrench**, then optimises stiffness, damping, reference and feedforward to satisfy the contract.

**The contract is four typed fields**, and this is the part to copy:

| field | what it says |
|---|---|
| direction | a trajectory tangent, its normal subspace, a plane tangent or normal, or a direction in a declared frame |
| requirement | tracking, compliant, or constrained |
| force range | lower and upper bounds; equal bounds mean a target force |
| channels | gain, reference, feedforward, selected jointly |

**Numbers.** Three tasks, five trials each. Winch to hoist a second robot 5/5. Door open and pass through **5/5 against a
baseline's 1/5**. Box transport at 0.85 kg succeeded where baselines failed to maintain contact. Lifts 3 kg near and mid,
and "both methods fail at 3 kg far." Baselines: SONIC native control and an admittance-control integration.

**Their stated limit, quoted:** *"A force range can be unattainable at the current deflection; adaptation remains bounded
by the controller's limits."* No code release.

**What it changes for us — grade A.**
1. **It is the System 1.5 seat, filled.** Not by a learned policy and not by a calibrated model, but by a control-theoretic
   adapter driven by measured wrench. We have been saying that seat is empty; on the contact axis it is not, and this is
   what occupying it looks like.
2. **A frontier model emitting a typed contract rather than an action is exactly our interface argument**, implemented and
   working on hardware. Their VLM writes the motion *and* the contract, no task-specific code.
3. **It makes our skill contract look thin.** Ours declares preconditions, postconditions and goals. Theirs declares what
   the *interaction* must be, in force units, and a layer beneath adapts to satisfy it. A postcondition says what should
   be true afterwards; a contract says what must hold *throughout*. That is a missing field in `skills.py`.
4. **And it has no notion of confidence.** The contract is satisfied or it is not, and when it is unattainable the paper
   says adaptation is bounded — it does not say the robot knows that in advance. That is the seat we work on, sitting one
   layer above theirs.

---

## SpatialClaw · Rethinking the Action Interface for Agentic Spatial Reasoning
*NVIDIA Research · [paper](https://arxiv.org/html/2606.13673v1) · [code](https://github.com/NVlabs/SpatialClaw)*

**What they did.** Instead of a VLM choosing among tool calls, give it a **persistent Python kernel** pre-loaded with SAM3
segmentation, Depth-Anything-3 reconstruction, geometry utilities and NumPy/SciPy/Matplotlib. It writes **one code cell per
step**; masks, reconstructions, plots and variables persist, and the next cell is conditioned on the previous output plus
rendered intermediate images.

**Numbers.** Training-free. **59.9 % average across 20 spatial benchmarks, +11.2 over the previous spatial agent**,
consistent across six VLM backbones from two model families, with no benchmark- or model-specific adaptation.

**What it changes for us — grade A.**
1. **A direct challenge to claim 7.** We argue the option set is the resource and pruning it hurts. This argues for no
   option set at all at the deliberative layer. It beats tool-calling, which is what our typed-choice interface is a form
   of, by 11 points on spatial reasoning.
2. **It cannot touch the fast seat**, and for the recurring reason: running a code cell takes seconds, and **a model that
   writes code returns no probability**. Nothing to threshold, so no hand-off, no veto, no expected-cost decision.
3. **It is a released, training-free grounder** — the System 1.5 our benches simulate. Our grounder being simulated is the
   weakest assumption in everything we have, and this is a way to stop simulating it.
4. **Runnable experiment it unlocks:** *does a code-writing spatial agent know when its spatial answer is wrong?* They
   publish accuracy only, the twenty benchmarks have ground truth, and the code is public.

**The tension worth recording.** SpatialClaw and KPI land the same week with opposite answers to "what should a frontier
model emit": **executable code** against **a typed contract**. Our programme has been arguing the second. The first beats
tool-calling on reasoning; the second runs at 100 Hz on hardware. They may simply belong at different layers, and saying
which is a cheap paper.

---

## Dong & Finn · What will be the RLHF moment for robotics?
*Perry Dong, Chelsea Finn · [post](https://pd-perry.github.io/posts/post-training.html) · 23 Sep 2026*

**The framing, in their words.** *"Complex behavior does not equal reliability. A robot that loads dishes correctly 95 % of
the time will break something every week."* And: *"RL is not yet a recipe. It's a craft."*

**Their algorithm, EXPO-FT.** A lightweight edit policy nudges a frontier model's sampled actions toward higher value;
successful edits are absorbed back. **30/30 success on six manipulation tasks in an average of 19 minutes of online
interaction**, with a human supervising and intervening throughout.

**The two sentences this programme exists for:**
> *"In LLM RL, reinforcement learning from verifiable rewards gave the field a default answer: check the answer, check the
> tests. **Robotics has no equivalent.**"*
> *"Today, success detectors are either hand-built per task or replaced by a human watching each trajectory and calling
> it, **neither of which scales**."*

**What it changes for us — grade A.** It named our gap from inside the field's leading group, and it made E197 worth
running. **E197 then failed**, which is the most useful thing here: a calibrated model ranked success detection at .662,
worse than believing the robot's own report at .838, and twenty-five labels made it *worse* (74 % → 38 %). So the
25-labels-per-task answer to their scaling problem **is not supported**, and we know that for the price of one run instead
of a quarter. Calibration, uncertainty and knowing-when-you-are-wrong appear nowhere in their post; a human watching is
their only mechanism.

---

## IMLE-VLA · one-step conditional IMLE in place of flow matching
*Ke Li's group · [project](https://kianhk6.github.io/IMLE-VLA/) · IROS 2026*

**What they did.** π0.5's action head runs ten denoising steps; they replace it with a **single-step conditional IMLE
generator** on the same frozen backbone, running the same 300M action expert **once** instead of ten times. Their stated
reason it works: cIMLE *"provably preserves multimodal action coverage — avoiding mode collapse — while eliminating
multi-step sampling entirely."*

**Numbers.** 55 Hz against 15. Real Franka Panda, four tasks × 20 episodes: **68/80 against 54/80**. LIBERO 40 tasks × 50
episodes: 98.0 % against 97.5 %. Proprioceptive jerk **2.2–3.0× lower**. Wall clock per episode 3.9–6.6× faster.

**What it changes for us — grade A.**
1. **It cost us a leg of our own argument.** We had been saying the calibrated seat exists partly because it is faster than
   a frontier call. Our layer runs at **2 Hz**; a VLA at 55 Hz is 27× faster. Latency no longer separates us from the layer
   we claimed to sit above. What survives is that a VLA emits motion, not a number a gate can spend.
2. **It handed us a metric we ran the same day.** Jerk. We applied it to our own falls: 3.89× the episode median in the
   last two seconds of a fall against 1.34 when upright — and then the dumb baseline, commanded speed, reached .754 AUROC
   against jerk's .857, so it was mostly a speed result. That control is why the finding did not ship.
3. **The opening is inside their mechanism.** Their whole case is a *distribution* property, from an author whose handle is
   the KL divergence, and the multimodality is preserved and then read only for an action. A head that provably keeps its
   modes is a head a calibrated number could be read off.

---

## HomeBody · a VLM over five skills, no VLA
*Stanford TML · [project](https://tml.stanford.edu/homebody/) · repo says "Code coming soon"*

**What they did.** Replace the three-stage pipeline (System 2 VLM → System 1 VLA → System 0 controller) with a **direct
connection from a frontier VLM to a five-skill library**: pick, place, open drawer, pick from drawer, navigate. Targets are
bound by **pointing at pixels** (an image point normalised 0–1000) or a 3D point in the torso frame. Every camera is on the
robot; occlusion is solved with **remembered geometry** — a Real2Sim twin built during exploration, Super Odometry and ICP
for localisation, SAM 2.1 with SAMURAI for tracking, visual servoing to correct the approach. All on one laptop with a
4090. Recovery is bounded local retries, then the reason goes back up to the VLM.

**Numbers.** **None.** No success rates, no trial counts, no timings, no baselines. Two demonstration rollouts.

**What it changes for us — grade A.** It is the architecture our layer is designed for and the one with the largest hole.
**No preconditions anywhere**, so nothing can decline; **no typed record of any decision**, so nothing in their system can
be scored, corrected or distilled — the improvement loop we price cannot run on it as built. Their escalation tops out at
the frontier model with nothing beneath it. And their answer to occlusion is memory, which is correct exactly until the
world moves. We took their room mesh and object meshes (46 MB of geometry, all they publish) and their task shape; we could
take nothing that runs.

**Correction logged:** an earlier note of ours claimed their code was public. It is not — method error 69.

---

## WROP · Training Object Permanence in World Models
*Hokin Deng · [site](https://object-permanence.world) · arXiv 2609.28654 · CC BY-NC 4.0*

**What they did.** 150 hand-built Blender generators in six families — Baillargeonian occlusion, static occlusion,
container permanence (shell games, rotating cups), obstruction, drop, collision — randomising lighting, speed and camera
angle while holding the cognitive structure fixed, 10,000+ samples per task. A 300-question exam, 14 video models, scored
by **twenty crowd raters doing blind pairwise comparisons** into a Bradley-Terry Elo. Their fine-tuned 16B Cosmos3-Nano
ranks third overall and first among true-continuation models.

**The sentence that matters, from the paper:** the tasks test **persistence of unchanged objects only**. They do not test
scenarios where occluded objects change, move or disappear. Nothing anywhere about a model knowing its belief might be
stale.

**What it changes for us — grade B.** They built the capability benchmark and left the failure mode untouched, and **the
failure mode is the robotics one**: a robot is not hurt by forgetting the ball is behind the wall, it is hurt by believing
it when somebody moved it. The generators are the expensive part and they are licensed; OP-3 already produces containers
that move and swap, and the violation variant is a change to the ground truth rather than new machinery. Caveat on
transfer: these are *video generation* models scored by human Elo, which is a different object from a robot's belief state.

---

## Harris · fleet telemetry rules before an agent touches the stack
*Joe Harris · opinion post, no data*

Four rules: deterministic coordinate transforms with **strict timestamp alignment**; decode CAN and fieldbus **at the
edge**; **bounded loops with hard timeouts** and a deterministic fallback for every action proposal; and unified mission
context, because *"a timestamp without joint states, localization confidence, and error registers is just noise."*
Closing: *"general AI models fail in physical reality the second they lose ground truth on hardware state."*

**What it changes for us — grade B.** It settles a design question rather than opening one: **localization confidence is
already a telemetry field**, so a staleness estimator's inputs are things a competent fleet logs, not sensors somebody must
add. Any gate we build should read *those* fields — reading age, localization confidence, error registers — rather than
ones we invent, or the result will not transfer. His third rule is also a constraint on us: a calibrated layer may gate and
may propose, but must never be the last line.

---

## Pathak / Skild · why robotics might be stuck
*secondhand summary of a talk, not the talk*

Moravec's paradox at work: a backflip is easier than climbing stairs, because a backflip needs only self-state, which is
fully observed and simulable, while stairs need environment information. Data needs scalability, diversity and closeness to
the robot; no method has all three and their weaknesses do not overlap. And a contrarian read on demos: laundry folding is
tolerant of error, where putting AirPods in a case needs real gripper-orientation precision — **the impressive-looking
tasks are often the tolerant ones.**

**Grade C, and honestly.** The Moravec framing is a *name* for something we had already measured: a zero-model arm cleared
bench 5 twenty-four times in twenty-five, which tells us per bench what the framing tells us in general. One claim we drew
from it — that the calibrated layer's job is entirely on the environment side — **is contradicted by our own E197**, where
an environment question scored .662. The demo-tolerance point is the only thing worth carrying, and it is a conversational
asset rather than a research one.


---

# Compact entries — the rest of the corpus

Written after the full sweep of every link shared across this workspace. Grade-A items whose full argument lives in
[FIELD-STATE.md](FIELD-STATE.md) are summarised here and cross-referenced rather than duplicated.

## Sirius-Fleet · Multi-Task Interactive Robot Fleet Learning with Visual World Models — **A**
*Huihan Liu … Yuke Zhu, UT Austin · CoRL 2024 · arXiv 2410.22689 · project page only, no code link found*

A visual world model predicts future latent embeddings; a **failure classifier trained on human-intervention labels**
and an **OOD detector** sit on the frozen embeddings and gate an ask-a-human. Three deployment rounds. **600 simulation
trials, 200 real Franka trials.** Combined system **>95 %**; autonomous policy **+13 % sim, +45 % real**. Ablation: OOD-only
/ failure-only / combined = **85.1 / 87.0 / 99.4** on one task, combined best on all. Threshold adapts as
**θ = 95.2 − 17.7·e^(−3.2·p_H)** in the human intervention ratio. Limits: quasi-static tasks, five operators, one
embodiment. **This is our fleet loop, prior.** The specific critique — that keying a threshold to the intervention rate
loosens the monitor exactly as it becomes least trustworthy — is in FIELD-STATE §4a and is the sharpest thing we own.

## Failure-Aware Bimanual Teleoperation via Conservative Value Guided Assistance — **A**
*Great Bay / HKU / PolyU / NTU · arXiv 2602.01092 · no code*

CQL success critic plus *"an auxiliary head that predicts whether an irreversible failure will occur within the next H
steps"*; assist strength scales with risk, transparent when risk is low. Two xArm 7 followers, 10 tasks, **40 trials per
task per method**. ≥98 % against ~80 % for other teleop interfaces — **but unassisted human is 40/40 at 22 s against their
39/40 at 157 s**. Their limit is our claim 4: *"failure awareness is inherently limited by the support of the offline
dataset."* See FIELD-STATE §4b.

## GaP · Graph-as-Policy — **A**
*Berkeley / CMU / Bosch / NVIDIA (Goldberg, Yuke Zhu, Jim Fan) · arXiv 2607.05369 · CC BY 4.0, site promised*

Multi-agent-authored computation graphs over a **51-skill library**, rehearsed in Isaac, with an LLM editing topology and
parameters until performance plateaus. **5,500 sim trials.** GaP 0.93–0.99 where π0.5 sits 0.15–0.78. Real: grocery orders
**25/25** vs 8/25; packing 28/30; popcorn 18/20. Popcorn self-learning **33 % → 94 %** in ten iterations. **And on the
repetitive task a hand-engineered pipeline still wins, 0.99 against 0.95.** Their limit: *"execution reliability is not yet
at industry levels."* Nothing on uncertainty; three qualitative failure modes.

## Q-Planning · Beyond Imitation — **A**
*arXiv 2608.21204 · the strongest external challenge on file*

A small off-policy Q-function scores a frozen BC policy's draws; only the Q is fine-tuned. LIBERO-10 93 → 99 %; RoboTwin
83.8 → 91.4 %; **real robot stack-cups 40 → 90 %, insert-wallet 25 → 80 %, with zero interventions.** 1.7–3.2× faster than
smoothed MPPI. **If a value function from task outcomes alone does that, the operator loop may be overhead for anything a
reward expresses.** The registered probe that settles it — outcome-scorer against acceptability-scorer on the same states
— is unrun, and its negative result costs us the thesis.

## SAIL · Scaling In-Context Imitation Learning — **A**
*Sakana AI × U. Tokyo · IROS 2026 · arXiv 2603.08269*

Frozen Gemini Robotics-ER 1.5 proposes trajectories; a second instance of the same model scores rendered rollouts; MCTS
searches; an archive is retrieved by scene similarity. Budget vs success: **1 → 25 %, 6 → 55 %, 15 → 65 %, 30 → 71 %,
45 → 73 %.** Strategy at 15 nodes: MCTS 65 %, BFS 51 %, DFS 37 %. Real SO-101: 5/6 on one task. **No ablations. No
wall-clock, token or dollar cost anywhere.** The abstract's "up to 95 %" is the best task, not the average. Missing
control: no rate-matched random arm, and **generator and evaluator are the same model** — self-grading, which is what our
independence test exists to attack.

## Argon Robotics · Scaling and speeding up robots in the real world — **A**
*argonrobotics.ai/research · bimanual PiPER, π0.5, **500 real runs per condition***

Three levers: frame-dropping keyed to gripper events, inference chunk-skipping under a scene-dependent displacement
threshold, and sped-up DAgger intervention data. **37.3 s teleop at 100 % → 9.4 s at 95.2 %.** Uniform dropping collapses
(94 → 53 % at 2×, 9 % at 4×); gripper-aware dropping gives 3.41× at 95.6 %. Thresholds **2 cm clean, 0.3 cm with a person
present** — a model output moving a safety margin exactly where being wrong hurts. **200 interventions → 97.2 % at 3.92×**,
intervention data worth ~30× ordinary teleop per frame. **Their boundary on our claim, verbatim from our own note:** *"the
claim cannot be 'calibration beats rules.' On plates it does not, and they have the runs to prove it."*

## CLM · Contrastive Language Model — **A**
*Kwok, Kang, Suresh, Saad-Falcon, Pavone, Ré, Mirhoseini · Apache 2.0 · weights on HF*

A frozen Qwen3-8B encoder with two 20M projection heads, scored by cosine similarity, trained with bidirectional InfoNCE
on 60M pairs. Serves the same typed questions behind a compatible endpoint. Parity with Jev on computer-use / gaming /
tool-calling at **up to 9× faster**; as a verifier **87.6 % Terminal-Bench 2.1, 81.6 % DeepSWE**. Two things aim at us:
they state **"Jev fails to serve as an effective verifier for these long-horizon tasks"**, and their serving architecture
**caches state and action embeddings separately for settings "where the state evolves continuously while the action set
remains fixed"** — a precise description of our harness. **This is the fourth seat E196 now needs.**

## Open-Jev-27B — **A**
*Zhaoran Wang / Yiqi Lyu · 27 Sep*

**18.6 ms server P50 on one B300, >50 Hz**, still BF16 with no distillation. Follows the author's own prediction that
*"'big models are too slow for robotics' is about to age badly."* **Corrects E196**: our 632 ms measurement of an open 27B
was a free demo endpoint, not the model class, and the same size runs 34× faster on real hardware.

## Goal2Skill — **B**
*BUPT / InspireOmni / Tsinghua · arXiv 2604.13942 · no code*

VLM planner with pre/post-conditions, episodic memory, an error register and a reflection engine, over a diffusion
primitive library. **32.4 % against 9.8 %** for the strongest end-to-end baseline, 100 episodes per task. **The memory
ablation nobody here had run**: base 6.7 % → +history 27.7 % → +working memory 28.0 % → full 35.3 %. History carries
almost all of it. Recovery ablation: 8.0 → 17.5 (+verify) → 24.0 (+reflect) → 28.0. Nothing on confidence; verification is
post-condition checking.

## Isola · robot-use agents — **B**
Four named problems, each already measured here: latency, distillation, reliability, skill management. The essay's closing
question is the best one-line description of this architecture anyone has written: **"how do we get to: reason slowly
once, execute quickly many times?"** Worth adopting as external vocabulary. The genuine gap it exposes: we have measured
when to hand off and when to re-decide, but **never when to re-plan**.

## Isaac Lab, read from source — **B**
Could not be run (needs CUDA ≥13; this machine is Apple silicon), so the recipe was read instead. **NVIDIA's shipped G1
walking config randomises essentially nothing**: friction ranges are degenerate constants, and `push_robot`,
`add_base_mass` and `base_com` are all set to `None` for G1. **Neither Isaac Lab nor MuJoCo Playground randomises actuator
gains** — the one family our own E142b measured at **21 % falls** against mass's 3 % and friction's 0 %. Independent
corroboration of one of our claims, from somebody else's source code.

## Scalable Real2Sim — **B**
*Pfaff, Fu, Isola, Tedrake (MIT) + Amazon Robotics · arXiv 2503.00370 · code + 20-asset benchmark released*

A Kuka arm rotates an object in front of one RGBD camera; SAM2 masks it, BundleSDF tracks pose, and an excitation
trajectory identifies inertial parameters from joint torques alone. Mesh error **0.80–5.58 mm**. Parameters: **mass 1.34 %,
centre of mass 2.15 %, inertia tensor 42.35 %** (and **358.6 %** on the end-to-end test). Relevant to claim 5: the field
can now generate sim assets automatically, and **inertia is by far the worst-identified quantity** — which is the family
adjacent to the actuator gains we showed matter most.

## X-Planner — **B**
*X-Square Robot · 9B Qwen-series VLM · Apache 2.0 model, MIT code, benchmark on HF*

The planner layer, released. Decomposes instructions into event-level subtasks with an implicit continuous chain-of-thought
("Staircase Decoding"), interfacing directly with a downstream VLA or world-action model. Real-robot task progress
**71.60** reasoning / **53.75** generalization; second of four on offline scores. Benchmark: **1,500 episodes, 3,490
synchronized videos, 167 source datasets.** The paper describes *"takeover-time annotations and human-designed failures supervise error recognition"*, and I relayed
that as "its benchmark is labelled takeover data". **It is not. The released artefact was inspected and contains no such
labels** — `episodes.parquet` (1,500 rows, 15 columns) and `metadata/manifest.jsonl` carry instruction, task, subtask,
scene, camera and complexity fields and **no takeover, intervention or failure keys of any kind**. What is actually
released is 1,500 episodes of human-written subtask decomposition with synchronized multi-view video: good planner
training data, with no human takeovers in it. **The paper and the release do not match.** Method error 82.

Still a drop-in candidate for the planner slot on the strength of the model, which does run — the harness session has it
at ~36 tok/s in 4-bit on Metal, grounding correctly on rendered frames, though it plans for a tabletop arm and emits
free-text rather than skill names. Its useful parts are the native `progress_percent` and `execution_decision` fields.

## Reimagine Robotics · deployment is the best teacher — **B**
ReTrace learns a task from a single demonstration; a force-teaching device in the end-effector lets a factory worker
correct in place as a motion or a force. **12 sub-tasks at one customer, ~2/3 production-ready from one demonstration,
teaching per skill ~1 day → ~10 minutes**; 0.4 mm precision from one demonstration elsewhere. No baselines, no trial
counts, "production-level performance" undefined. **Two things for us:** Time-to-Value is a metric above ours in the
buyer's hierarchy, and their correction is a **replacement action**, which our own label-form result says teaches a model
to act rather than to ask — consistent with their having **no failure detection beyond a human watching**.

## The rest, compactly — **C**

- **Sucar, agentic Object-SLAM** — a frontier model reconstructs and tracks tabletop objects and hand pose into MuJoCo for
  a robot to copy. The source of use case 20 in our README, already recorded as an idea.
- **WetRobo (Sherry Yang)** — coding agents observe a wet lab, write and execute robot programs, adapt by physical trial
  and error. Third instance of code-as-action-interface. Framing worth noting: academia's advantage is *"robots doing real
  science in physical labs."*
- **LingBot-VLA 2.0 (Ant/Robbyant)** — 60,000 h pretraining across 20 embodiments, 55-dim unified action, MoE action
  expert. Real-robot gains modest (34.4 vs 32.2 % success) and **OOD collapses: 60 % in-domain → 13.3 % out**. Code and
  checkpoints released. Nothing on uncertainty.
- **πRL** — online RL fine-tuning of flow VLAs via two tractable-likelihood formulations. LIBERO **57.6 → 97.6 %**,
  one-trajectory SFT 43.9 → 94.0 %. **Simulation only**, and semantic OOD barely moves (4.8 → 6.6 %). Code released.
- **ViPRA (CMU / Skild / Pathak)** — video-prediction pretraining on actionless human video, then a policy from 100–200
  demos. SIMPLER 69.8 % vs π0's 27.1 %; real world 54.1 vs 41.8 %. Nothing on uncertainty.
- **CounterAlign** — counterfactual relabelling of existing demonstrations into a discriminator reward, no new data.
  Position-perturbation robustness 0.53 → 0.60 against π0.5; real robot 4 tasks. Nothing on uncertainty.
- **PLARE (KAIST, IROS 2025)** — VLM pairwise preferences train a policy directly, no reward model. MetaWorld 70.0 % vs
  61.7 % for the best VLM baseline. **Measures its own VLM labels at 20–30 % wrong and regularises the noise away with
  dropout rather than acting on it** — the closest near-miss in the corpus.
- **ULC (HIT / Westlake)** — one unified whole-body RL policy beats hierarchical upper/lower splits on a real G1 under
  2 kg load and command delay. Code released. Nothing on uncertainty.
- **IETrans (ECCV 2022) · PE-Net (CVPR 2023) · Fair-PSGG · DSFlash** — scene-graph perception, the grounder's raw
  material. DSFlash runs at **56 fps** with 30.90 mR@50. Fair-PSGG's finding is methodological and ours in spirit: the
  standard protocol let models inflate recall with duplicate masks, and fixing it **reversed the field's conclusion** that
  one-stage beats two-stage. **All four: nothing on uncertainty.**

---

## Status of the record

**Covered: 33 sources.** Everything above plus the nine long entries.

**Not yet read by anyone: 36 X posts** shared in earlier sessions. X is reachable only through the browser extension, one
post at a time, so these have to be worked by hand. They are listed in `/tmp/xlinks.txt` and are the remaining gap.

**The count that matters:** of the 22 sources with enough substance to judge, **seventeen report nothing on uncertainty at
all.** The exceptions are Sirius-Fleet, the Failure-Aware teleoperation paper, RWM-U, Scalable Real2Sim (estimation error
bars, not learned confidence) and PLARE (measures its own label noise, then regularises it away).

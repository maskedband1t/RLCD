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
| 6 Oct | ml-engineering (Bekman) | a cluster-scale engineering book; its latency standard makes our 90 ms the one number with no interval and no tail | B |

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

---

# Batch two — the older links, worked by hand

## Chalvatzaki · "What Are We Actually Seeing with GPT-6 Astra?" — **A, and the strongest external support this programme has**
*Georgia Chalvatzaki · 19 Sep 2026 · an essay, 80k views · cites HARBOR (arXiv 2606.08610) and Nautilus (arXiv 2605.11665)*

**A professor spending five thousand words arguing that the harness is the unit of analysis.** Her sentence, and it is
ours: *"the model alone may increasingly be the wrong unit of analysis. We need to understand what is contributed by the
model, what is contributed by the representations and algorithms around it, and how these components interact."*

**The number to take from it, and it is the most dramatic in the whole corpus.** ARC Prize report Astra at **62.7 % with
their Standard harness and 99.9 % with the Provider Adapter harness.** *Same model.* **37 points from the interface
alone.** Nothing we have measured comes close to making the point that cleanly.

**Her methodological demand is our preflight, stated by somebody with a podium:** *"Prompt, context, retrieval, tool
access, action interface, feedback, and harness configuration should therefore be treated as experimental methodology.
Without this information, a successful demonstration establishes that the complete setup worked. It tells us
considerably less about why."*

**Her proposed experiments are our ablation design.** Vary prior exposure and information access; **vary external
structure while holding the model fixed**; vary internal representational structure; vary physical interaction —
embodiment, coordinate conventions, mass, friction, contact, perturbations mid-execution.

**Two published harness frameworks we did not know existed and should read:**
- **HARBOR** (arXiv 2606.08610) — a harness for agentic robot RL, decomposed into bounded stages with **explicit
  validation gates and persistent experimental artifacts**, across six benchmarks and sixteen tasks, transferring to real
  robots. *Validation gates* is our preflight under another name.
- **Nautilus** (arXiv 2605.11665) — one prompt to a reproducible robot-learning workflow. *"Typed interfaces, procedural
  priors, and validation gates can substantially change whether the workflow succeeds at all."* **Typed interfaces** is
  our vocabulary, arriving from a different direction.

**And the gap she names is the one our benches are built on.** *"Human-robot interaction is absent from these evaluations
altogether. There is no person inside the workspace whose behavior changes in response to the robot."* Every bank in this
programme has a person in it. That is not a coincidence we should leave unstated.

Her safety line is our claim 5 verbatim in spirit: *"Some safety constraints should clearly remain externally enforceable
regardless of how capable the model becomes."*

Numbers worth keeping: RoboCurve block-into-bowl **Astra 19/20 against Fable 8/20**, and puzzle insertion **2/20 for
both** — where she notes 20 trials separate 19 from 8 but say nothing about 2 versus 2. StationeryBench: Astra completes
**7 of 100** trials, mean progress 46/100.

## Dimensional · a third-party benchmark of the model in our seat — **B**
*stash (@stash_pomichter) · 18 Sep · 29.7k views*

**120 real and simulated tasks and environments**, benchmarking Jev against Dimcode, Astra, Fable, Opus and 5.6, graded on
**speed, cost, tokens, collisions and path quality**, with code, data and paper promised the following day. An independent
evaluation of the model in our seat, across a task count an order of magnitude beyond ours. **The release should exist by
now and nobody here has checked** — that is a concrete follow-up.

## RobotKit · Jev and Astra on a real arm, notebooks open — **B**
*Michal Kubenka · 19 Sep*

Both models on a real AgileX PiPER arm, **eight runs open-sourced as notebooks**. Same loop each time: *"the model picks
the next skill, a governor checks it, the arm moves."* That is our architecture, on hardware, with the runs published.
Their own headline: **"the speed gap was not where we expected it"** — consistent with our 8.8 % inference finding.

## Saito · a 4B head distilled from a frontier judge in 26 hours — **B**
*Taro L. Saito · 18 Sep · 504k views*

Distilled DeepSeek V4 Flash's judgments onto a **4B model in 26 hours on a DGX Spark**: at one-twentieth the size it
**beats the teacher's instant-response mode at about 22 ms per judgment.** And the framing in his earlier post is exactly
what this programme argues about the interface: a local engine hits 40 ms *"simply by abandoning text/JSON generation and
specializing solely in judgment."* Distillation into an owned head is our claim 3, being done publicly by individuals on
desktop hardware.

## CUA-S1 · a third System One model family — **B**
*Cua · 18 Sep · 1.2M views · open source*

A **family** of small specialised System One models for computer use, first release CUA-S1-FORMS. After Jev and CLM this
is the third. The seat is being commoditised, which strengthens rather than weakens the argument that the value is in the
loop around it rather than the model in it.

## Inverted Lambda · Real2Sim from whatever cameras were already there — **B**
*21 Sep*

An SDK that captures a robot's own cameras, sensors and LiDAR — or a phone — and turns **its actual deployment
environment** into simulation, with contributors rewarded for environments they add. *"Policies train in the places they
will actually deploy, captured by whatever was already there."* Relevant because our benches are rooms we invented, and
the gap analysis says the deployment contains fixtures we do not model.

## OpenRoboto · three models, one apple, one plate — **C**
Jev against GPT-6 Astra and GPT-4.1 mini in MuJoCo, each choosing intent then an X/Y/Z direction and a gripper state.
Already covered in the 19 September field note; listed here so the record is complete.

## Zhaoran Wang · the prefill prediction — **C, already covered**
The parent post of the Open-Jev result: *"'big models are too slow for robotics' is about to age badly."* Its answer
arrived two days later at 18.6 ms. A reply worth noting for honesty — Siva (@ergodicthought) asks *"what makes you think
robotics, especially long horizon planning, is a prefill-type problem rather than a decode-type problem?"* and the thread
does not answer it.

## Anto Patrex · a trainability scorer running on real deployment data — **B**
*19 Sep · humanoid teleop data from their own deployment sites*

Ran the calibrated eval model over teleoperation data and report **99 % label consistency, 91 % annotation completeness,
sub-action segmentation and frame-accurate timing.** Their framing is the argument: **"Robot data sells by the hour. Hours
don't tell you if it's trainable."**

That is use case 16 in our README — scoring whether a demonstration is clean enough to learn from before it enters the
training set — being run commercially on real deployment footage. We measured it on 13,451 household demonstrations at
AUROC .78 zero-shot against a rule's .64 and a fitted logistic's .88. **Somebody is now selling it**, which is
confirmation of the use case and a reason to state ours in their units: hours of data against hours of *trainable* data.

## Kubenka · why everyone else's robot demo takes minutes — **B**
*19 Sep*

**"Most 'LLM runs a robot' posts this week are sim, and most send every camera frame to the big model. That is why a
cube-into-tray takes minutes."** On a real AgileX arm at 10 % speed: **27 s against 1 m 11 s** for the frontier model.

The useful part is not the ratio, it is the diagnosis: the cost is **sending every frame to the big model**, not the big
model's own latency. That is our architecture's premise — code enumerates, the fast layer picks, the frontier model is
called once per skill — stated by somebody with a real arm and published notebooks.

## Carrabre · the typed-question pattern outside robotics — **C**
*18 Sep*

Natural language to camera movement in a browser video tool: the model answers **a few calibrated multiple-choice
questions** (move kind, plus direction and magnitude band per axis), code assembles keyframes into a structured
trajectory, and the trajectory is **checked before rendering** so the result is the move that was asked for. ~230× faster
planning. Not robotics, but it is our exact interface — closed-set questions, code composes, verify before committing —
working in a different domain, which is mild evidence the pattern is general rather than a robotics quirk.

Its quoted parent carries the origin claim for the model class: *"After co-inventing ChatGPT, I kept asking myself: why
have superhuman chat models not led to AGI?"* — two years in stealth on RLCD, released as Jev at "20-200× faster,
40-400×" cheaper.

## Hu · what happens when the target moves mid pick-and-place — **A**
*xiao hu · 21 Sep · [github.com/Hu-xiao-max/jev_robot](https://github.com/Hu-xiao-max/jev_robot) · **already vendored at `third_party/jev_robot`***

A local **2B** model driving a PiPER arm in MuJoCo, where **the cube is relocated three times per run** and the robot must
detect it, interrupt, and recover. **10 of 10 seeds succeed, 32.6 ms median decision latency.**

**This is our subject, built by somebody else, open, with a number.** A belief going stale mid-task, detected, and
recovered from — the thing the 2026 deployed-systems audit says nobody demonstrates. It is a short-horizon tabletop
version rather than an 18 m aisle, and 10/10 means the bench does not discriminate, but **the detect-interrupt-recover
loop exists in public and we should read the code before building ours.**

## Jacob · graph-as-policy with a calibrated model in the decision nodes — **A**
*Deborah Jacob · 21 Sep · quoting Ken Goldberg*

Somebody has already composed the two things we have been discussing separately. In a moving-cube sim, median pickup
time: **5.42 s with GaP plus a custom Rust executor plus Jev, against 8.79 s for native GaP with a frontier model.** Her
framing is exactly the division this programme argues: *"GaP gives you explicit decision nodes, dependencies and parallel
execution. Jev makes decisions inside that graph much faster."*

**Structure supplies the graph; the calibrated model occupies its decision nodes.** That is our architecture, assembled by
a third party, measured, at a 1.6× gap. And the post she quotes is **Ken Goldberg calling it a paradigm shift** —
*"Goosebumps: a Paradigm Shift is Occurring in Robotics... A new approach — Agentic Robotics — is a game changer."*

## Montoya · our stack, built independently — **B**
*jpmonty · 22 Sep*

A G1 in a virtual kitchen: a VLM plus depth maps the room, **a path planner produces candidate routes, the calibrated
model chooses which move to make next**, and a pretrained walking policy handles locomotion, reaching the stove in ~64 s
of sim time. Planner proposes, fast layer chooses, policy executes. **Nobody coordinated this**, which is the most
useful thing about it.

## Laya · a fourth System One model, claiming to beat the third — **B**
*ricky b · 19 Sep · laya.convaiinnovations.com*

**33 ms**, typed decisions (choice, score, noul) across 100+ languages in a single forward pass with calibrated
probabilities, and it states plainly that it **"outperforms TypeSafe Jev."** Notable because **we already use Laya** — our
distilled 421M owned head is built on it. So the base of our own student is now marketed as a competitor to our teacher,
and E196's three-model comparison has a fourth candidate sitting in the repo.

## Eidon · a company winding down and releasing everything — **B**
*Daniel van Strien · 21 Sep · CC-BY-4.0 on Hugging Face*

**1,274 hours of egocentric video with paired 7-IMU arm tracking, 13,451 recordings, 9 TB** — people doing laundry,
cleaning, dishes and cooking — released in full as the company shut down. **This is where our own E97 data came from**
(the trainability scorer, AUROC .78 zero-shot against a fitted logistic's .88). Worth recording that the provenance is a
company failing, which is also the most honest available comment on robot data economics.

## SAM 3.1 on a hosted API · the grounder as a phone call — **B**
*Meta for Developers · 18 Sep*

Detection, segmentation and **identity-preserving video tracks** from a short phrase, in a single API call. The grounder
component we do not have, available as a service. **"Identity-preserving"** is the staleness-adjacent capability: it is
precisely the claim that the thing you are tracking is still the thing you think it is.

## Gundala · a 1B RLCD model, open-sourced in two hours — **B**
*Harsha Gundala · 16 Sep*

**Qwen-2.5-1B-RLCD**, open-sourced, 5× faster on-device inference for type-safe workloads, later shown playing Doom
on-device at **150 ms on a 1B model**. The smallest seat candidate in the corpus and it runs on a laptop.

## Kinsley · the market asking our question out loud — **B**
*Harrison Kinsley (Sentdex) · 18 Sep · 23k views*

**"is anyone using jev with robotics rn and willing to vouch for it being useful?"**

A well-known ML educator asking, in public, whether this model class is actually useful in robotics — and the replies did
not settle it. **That question is what this entire record answers**, with 165 pre-registered experiments and roughly one
negative result in four. Worth knowing that the demand for the answer is explicit rather than assumed.

## Dimensional · a benchmark of harnesses, not models, and the first row that cuts against us — **A**
*Stash Pomichter · 28 Sep · open dataset + code · `dimensionalOS/dimos`*

**"How far are LMs from zero-shotting complex real-time control tasks?"** — 2,000+ navigation tasks across **133 real and
simulated environments**, models *and harnesses* varied, everything open. The unit of analysis is ours: not a model, but a
model inside a scaffold.

The numbers published so far cover **one** HSSD case (stool, 3 m), and they run the wrong way for us:

| arm | success | note |
|---|---|---|
| MLS planner alone | 0.91 | with pre-computed navmesh ground truth |
| calibrated agent | **1.00** | 10 seconds — best in the table |
| Astra, **no** stack | 1.00 | raw `world_state` / `cmd_vel` / `finished` |
| Fable, **no** stack | 1.00 | |
| GPT-5.6, **no** stack | 1.00 | |
| Opus, **no** stack | 0.91 | |
| Fable, **with** stack | **0.91** | −9 pp |
| Astra, **with** stack | **0.72** | **−28 pp** |

**The harness cost two frontier models accuracy.** On a second case it bought time instead: planner 10.9 s, bare agent
34 s, agent-with-stack **16 s**. A scaffold that halves latency and spends success is a real finding and it is the
mirror image of the trade we have measured four times in the other direction.

**What keeps it from being fatal, stated fairly:** one case, not the 80-case suite (10 HSSD scenes) and not the
2,000-task release. The calibrated model's 1.00-in-10 s is also one case. And **PR #4112, which builds the
model-fixed/harness-varied comparison, ran no paid model trials at all** — it says so: *"integration pilots, not a broad
performance ranking."* The comparison everybody wants has infrastructure and no results.

**Action:** pull the 80-case results when they land. It is the cheapest available third-party test of our central claim,
on 133 environments we do not have. Logged as `CONVERGENCE.md` row 16, **against-us**.

## Self-Adaptive VLA · the shift axis we said nobody touches — **A**
*Hongxin Zhang (UMass Amherst) et al · arXiv 2609.30092 · posted 28 Sep*

**"Most VLAs are memoryless: when a robot's hardware drifts, the policy repeats the same failure every trial."**

A post-training recipe for **deployment-time hardware shift**. Rollouts are collected under *deliberately injected*
shifts; the base policy's training data is rewritten into **shift-conditioned expert demonstrations** by pre-compensating
expert actions for the known shift; a plug-in **context encoder** compresses visual observation, proprioception and
actions into one **latent context token** that modulates the policy through **AdaLN**. Context tokens **ensemble**, so
the policy iteratively self-corrects across attempts. **Recovers >80 % of base-policy performance** on four
precision-critical bi-manual and dexterous tasks.

**The shifts are actuation bias and joint encoder offsets.** We measured actuator gains as **21 % of falls against mass
3 % and friction 0 %**, checked Isaac Lab's and Playground's source, and wrote down that nobody randomises gains. The
ablation ranking is still ours alone — they run no axis comparison — but **the diagnosis is not**, and the framing has to
be corrected rather than defended. `CONVERGENCE.md` row 7 downgraded **we-are-ahead → independent-arrival**.

**Read honestly:** ">80 % recovery" is the only number in the abstract, no per-task table, no trial counts, no shift
magnitudes, and **no uncertainty measure of any kind** — the tally is now **18 of 23 sources reporting none**. Whether
the robot is physical is not established by the abstract, so this record does not claim it.

**Why it lands anyway:** it is the memory argument on the actuator side. Their fix for a memoryless policy is to feed it
its own failed rollouts as context — structurally the same move as our correction-form work, one layer down.

## Kintsugi-VLA · the number that answers our livelock — **A**
*arXiv 2609.31048 · surfaced alongside the above*

The most directly useful paper of the 54 read here, because it solves a problem this record has logged as open.

**Result 12 of ours:** a robot livelocked for **37 seconds** while its per-decision confidence sat flat at **.52–.66**.
A number attached to each decision cannot see a failure that lives in the *sequence*. We logged it and had no fix.

Kintsugi's fix: **interventional recoverability** — *the probability of completing the original task after the simulator
is restored to a given state*. Estimated by **adaptive Monte Carlo continuations with pointwise Wilson intervals**,
branching from exact restored states along failed trajectories. It evolves **non-monotonically**, and there is an
observed **terminal low-recoverability frontier — the point after which recoverability stays below threshold**.

**That frontier is a thresholdable number defined over a sequence, measured by branching instead of asked of a model.**
It passes our own seat test from the other direction: code *can* compute it, given a simulator you can restore.

Their use of it is data selection: pick recovery-training start states near the frontier. **SmolVLA recovery success
34.6 %** (difficulty-matched) and **38.4 %** (frame-budget matched) against uniform sampling's **28.8 %** and **31.7 %**
— **+5.8 and +6.7 pp**, small, and matched two ways. Same ordering under disturbed execution and under shifted clutter
and physics. **And they report the cost: clean-task success falls 76.8 % → 74.7 %.** Structure bought recovery and spent
2.1 points of nominal performance — row 16's trade again, admitted by the authors. Simulation only, one Franka task.

**Why this is cheap for us, specifically:** `src/stack/table_run.py:210` already snapshots, rolls a candidate forward,
reads the outcome and restores — we built that to *choose* a plan. `cell/analyze.py` already exports `wilson`. The
mechanism and the statistic are both already in the repo; nobody has pointed them at recoverability. **Probe: measure
recoverability along the 37-second livelock and see whether the frontier is crossed before the confidence signal moves.**
Pre-register before running. Logged as `CONVERGENCE.md` rows 17–18, **they-were-first**.

## Delta-0 · a 69-DoF whole-body humanoid, and the speed claim we learned not to make — **A**
*Delta Intelligence · 28 Sep · `deltai.com/en/blog/delta-0` · no paper, no weights, no data*

**"One generalist policy. 69 degrees of freedom. Everyday tasks at near-human speed."** Whole-body loco-manipulation:
turntable, bed-making, picking from the floor, dishwasher, step-pedal bin, sitting on a sofa.

**Credit where the artefact earns it.** Unlike the site and the launch post, the blog does carry numbers, and some are
raw counts rather than percentages — better practice than most of this corpus:

- **10,000 hours** of paired human data in pretraining; a **3 h 31 min** motion dataset; a **180-dimensional** padded
  action space of which **154** are arm and hand.
- A **controller data-scaling curve with a declared threshold**: **29.2 %, 48.0 %, 72.6 %** of motions meet *both*
  tracking bounds at **10 %, 40 %, 100 %** of motion training data — bounds being mean wrist position error **≤ 2 cm**
  and mean global root position error **≤ 15 cm**.
- **Dishwasher, out of distribution: 20 % (4/20) → 65 % (13/20) after reinforcement learning.**

**Three things it does not have, and the third is ours.**

1. **No success rate for any of the six demonstrated tasks** — the tasks in the video, the ones that carry the claim, have
   no numbers. The one task with numbers is an ablation, not a demo.
2. **No uncertainty of any kind.** Tally **19 of 25**.
3. **"Near-human speed" with no human measured.** This is exactly the claim **method error 76** was logged for: this
   record once carried "a human takes 62.5 s" as a yardstick, could not reproduce where it came from, and was caught.
   The fix was to rebuild the reference as a **runnable arm** — `src/stack/scripted_ref.py`, median over completed runs
   only, **44.0 s** — so the yardstick can be re-measured by anyone. **Delta-0 makes the speed claim with no reference
   arm at all.** Nothing here says they are wrong; it says the claim is not checkable, which is the whole point of that
   error.

**And the human is in the loop, unpriced.** The article acknowledges human intervention without quantifying its
frequency or what triggers it. That is claim 11's territory — we price escalation by operator ratio (**18/20 at 1:1,
13/20 at 1:8**) and nobody else does.

**The honest tension:** their biggest controller gain comes from *more data* (29.2 → 72.6 % across a 10× data increase),
which is a weights lever, not a structure lever. It is at the tracking-controller layer — System 0, below where anything
here operates — so it does not contradict the thesis. But it belongs in the record as a place where scale plainly worked.

## Contrastive World Models · the right idea, reported without a single number — **B**
*arXiv 2609.22175 · surfaced by alphaXiv, 27 Sep · 22.9k views*

**"If a world model has to reconstruct every pixel, it'll waste most of its capacity modeling irrelevant background
noise."** So they delete Dreamer's pixel decoder and replace reconstruction with a **Deep InfoMax-like lower bound**
maximising mutual information between state-action sequences and **local patch features** of future observations. The
latent keeps what predicts the future and drops what merely renders it.

**What it shows, in the authors' own words, because there is nothing else to quote:** on default DMC "all three methods
eventually reach comparable asymptotic performance"; with simple distractors InfoMax "matches or exceeds Dreamer on two
tasks" — **which means on the third it does not** — while the momentum-prediction baseline "collapses across all three";
with natural-video backgrounds it "substantially outperforms both baselines on every task". Training is "consistently
substantially faster in wall-clock time per training step", with no figure attached to *substantially*.

**The scale, stated plainly: 3 tasks (finger-spin, cheetah-run, walker-walk), 1 M env steps, 3 seeds per condition, and
results presented only as curves — no table, no error bars, no numbers anywhere in the paper.** Our own E130 measured
five runs of one arm on one bench spanning **20 to 23**; three seeds cannot carry "matches" or "substantially
outperforms" without a band. **Uncertainty tally: 20 of 26 sources report none.**

**Credit where it is due:** the limitations section is honest in a way most are not — *"limited to small-scale
experiments built on top of an older architecture (RSSM) on a relatively established benchmark"*. They are not
overclaiming scale; they are underreporting evidence, which is a different and more fixable failure.

**Where it touches this record — and it is a tension, not a fit.** E198's recoverability needs **exact** state
restoration: save the world, branch, restore, byte-identical. That is why bench 9 works for it (pure Python, `deepcopy`)
and why Kintsugi uses a simulator. **A learned world model cannot give you that**, however robust its latent — it gives
an approximation whose error compounds along exactly the long rollouts recoverability depends on. So the better the
learned model gets, the more tempting and the more wrong it becomes to measure recoverability inside it. **Restorability
and realism are different properties, and only one of them is what the frontier is made of.**

**Not acted on, deliberately.** `PLAN.md` for this fortnight says it in one line — *"four days went into making a world
model sharper. The thing standing between the author and this job is not model sharpness"* — and marks the demo **done, stop
polishing**. Today is day 13 of 14. This paper is a good answer to a question that was consciously closed, and reopening
it the day before the conversation would be the exact mistake that plan was written to prevent. **Filed, not built.**

## Neural Theorizer (NEO) · our result shape, in a domain with no robots in it — **A**
*Baek, Lee, Baek, Lee, Ahn (KAIST) · arXiv 2605.03413 · ICML 2026 **oral**, 0.7 % of submissions · 108k views*

**"Today's world models are trained to predict the future... But is prediction enough?"** The argument: understanding is
not prediction, it is **theory-building** — discover reusable primitives, compose them into *executable* explanations,
transfer those to novel phenomena. A theory here is literally **a compositional program**, induced as a latent "Language
of Thought" and run through a shared transition model. No language supervision, no LLM.

Three domains, none of them robotics: **GridWorld** (primitives are Up/Down/Left/Right), **arithmetic factorization**,
**image editing**, under their own OTIB benchmark. 3 runs per condition, **no error bars** — tally **21 of 27**.

#### The table is the reason this is an A

GridWorld, α = 0.33, *compositional* and *length* out-of-distribution:

| method | in-distribution | compositional OOD | length OOD |
|---|---|---|---|
| Disc-Mono (monolithic) | **0.988** | **0.000** | **0.000** |
| Cont-Mono | 0.975 | 0.431 | 0.053 |
| Cont-Mono-Opt | **0.994** | 0.726 | 0.209 |
| **NEO** (compositional) | 0.914 | **0.934** | **0.853** |
| NEO-S (beam 64) | 0.993 | 0.995 | 0.978 |

**The monolithic model scores 0.988 where it was trained and exactly 0.000 one step outside.** NEO gives up ~7 points
in-distribution and holds at 0.934 / 0.853 outside. **That is this record's central trade, measured by someone else, in a
grid world, at ICML.** It is the duck bench's result restated: the frozen rule program wins 39 to 33 where the rules were
written and scores 0 of 30 where they were not.

#### Two columns that are worth more than the headline

**1. "Explains itself" and "transfers" are different things, and they measured the gap.** Cont-Mono scores **0.975 on ID
Self-Explanation and 0.001 on ID Transfer** — it produces a fluent account of its own observations that is worth nothing
applied anywhere else. **That is E171 (prose is inert) in a different domain, with a number on it.** Ours was a
qualitative finding; theirs is a 975-to-1 ratio.

**2. The structured method's advantage is bought with inference-time search, and on one domain plain NEO is *worse* than
the monolith.** Arithmetic, length OOD: **NEO 0.045, 0.023, 0.025** across the three data regimes — against
Cont-Mono-Opt's **0.394, 0.216, 0.743**. Only NEO-S, with a **beam of 1,024**, recovers to 0.620 / 0.766 / 0.799.
**Composition alone loses; composition plus a thousand-wide search wins.** That is the third independent "structure is
not free" result in three days, after Dimensional's harness costing 28 points and Kintsugi's 2.1-point clean-task bill.

#### Their limitations, verbatim, and why this is filed rather than built on

> *"The current formulation assumes a relatively small, discrete set of primitives and short program lengths, which
> limits its scalability to domains with long-horizon, continuous, or highly structured dynamics."*

**Long-horizon, continuous, structured dynamics is exactly and only what we work on.** They say so themselves and name
real-world environments with stochastic dynamics as future work. The direction is right and the evidence does not yet
reach us. **Filed; the convergence rows are the value.**

## Reality Check / PAW-GEN-10 · the best-measured robot benchmark there is, and the column it does not have — **A**
*Poke & Wiggle (Nicolas Keller, ex-Meshcapade/Epic, ex-Franka) · 29 Sep · `pokeandwiggle.com/leaderboard` · not open*

**"The Era of Evals is coming to AI robotics."** 14,400 **real-world** rollouts on Franka FR3 stations — 3,600 per model
— across 10 environments, three data tiers, two placement conditions, **with 95 % confidence intervals on every number.**

#### The headline number is brutal and useful

| model | overall | evaluations |
|---|---|---|
| MolmoAct 2 | **28 %** | 3,600 |
| Pi 0.5 | 21 % | 3,600 |
| DiT-Flow | 19 % | 3,600 |
| GR00T N1.7 | **12 %** | 3,600 |

**The best open VLA scores 28 %.** At its most generous tier — D300, ~300 demonstrations per environment — MolmoAct 2
reaches **44 % (95 % CI 40–48)** and Pi 0.5 **33 % (29–37)**. This record's opening line says a robot that works 95 % of
the time breaks something weekly. **On real hardware across ten tasks the state of the art is not at 95 %, it is at
28 %,** and that reframes the product argument rather than weakening it.

**Per-task spread on one model, MolmoAct 2:** tools into a standing toolbox **4 %**, sort screws **10 %**, DC jack 15 %,
open toolbox 18 %, route cable 21 %, clamp component 24 %, datum alignment 44 %, place loaded boxes 42 %, pour screws
**52 %**, bimanual spray-bottle handover **52 %**. A 13× spread within one model. **Task identity dominates model
identity**, which is claim 5 again from a completely different direction.

#### Two of their nine metrics are ours, built by someone else

- **Safe Failure Rate** — *"share of failed episodes that ended with both arms ok."* **That is the censored-vs-raw
  distinction, in a public leaderboard.** We charge falls to the motion layer and never to the chooser precisely so a
  destructive failure and a harmless one are not one number; they made it a column.
- **Max Contact Force**, in Newtons with a CI (Pi 0.5: **50 N, 95 % CI 47–52**). Irreversibility priced in physical units.

Plus SPARC smoothness, jerk at 10 Hz, progress, execution quality, execution speed. **Nine metrics, all with intervals.**

#### The column that is not there, and it is the whole programme

The benchmark reports **no human-intervention or takeover frequency, no model-reported uncertainty or confidence, and no
failure-detection metric.** Nine metrics measuring what the robot *did*, and **not one asking whether the robot knew.**

**That is the sharpest statement of our gap that exists**, and it comes from the most rigorous eval in the field rather
than from us. The claim that needed weakening was *"almost nobody measures"* — plainly false as of today. The claim that
survives, and is now much better founded, is ***nobody measures whether the system knew***.

#### Against us, stated plainly

This record leans on a measurement vacuum. **A company just filled a large part of it**, publicly, with 14,400 real
rollouts and intervals on everything — where the median source here reports 10 to 40 trials and no band at all. The
outcome-measurement gap is closing in public and our framing has to move with it. **Uncertainty tally: 21 of 28 report
nothing, and this is comfortably the best of the seven that do.**

**The one reservation, and it is not small:** unlike Dimensional's release the same week, **there is no mention of open
data or code**, and the models were *"fine-tuned by us on the target tasks"* — so the tuning that produced these numbers
is not inspectable, and a leaderboard nobody can reproduce is a claim rather than an instrument. M100 (mid-training on
100 h of embodiment data) is listed as coming soon.

## Argus · the operator-recovery labels we said did not exist, open-sourced — **A**
*Pantheon Industries · 1 Oct · Apache-2.0 code, **CC-BY-4.0 labels** · `Pantheon-Industries-Inc/argus`*

A VLM annotation and quality pipeline for robot-learning data, run over **3,546 episodes / 66.5 hours across nine public
datasets** (MolmoAct2, ABC-130k, Galaxea, HABIT, FastUMI, RealOmin, Egocentric-100K, Gen-HumanEgo, OpenAoE). Reads
LeRobot, MCAP or plain video. Recommends GPT-6 Astra, runs on other VLMs. **≈ $26 per footage-hour** on teleop, which at
a 71 s median episode is about **$0.51 an episode**.

#### Why this is an A and not a tool announcement

Per episode it emits a dense timeline that includes **"operator mistakes, and whether and how the operator recovered."**

**That is the label set this record said the field did not have, and being wrong about it once is already logged as
method error 82** — I asserted another benchmark carried takeover labels from reading its paper, and a peer downloaded
the release and found none. The rule that followed was *a claim about what an artefact contains must come from the
artefact*. Here the artefact has them, across nine datasets, **CC-BY-4.0**.

**It bears directly on our strongest single finding.** The form of a correction is the lever: a one-second veto rescues
**14 of 60** where the same operator input as a replacement action rescues **zero**. That was measured entirely in
simulation. Argus's labels are real recoveries by real operators, licensed for reuse. **The probe is obvious: do real
recoveries divide into the two forms our benches distinguish, and does the ratio survive?** Pre-register before looking.

#### The architecture is ours, arrived at independently

*"Deterministic checks run alongside the model to catch what a model should not be trusted to judge."* Five of them:

| check | what it catches |
|---|---|
| `stream_pairing` | camera files swapped between arms, by comparing image motion to recorded arm motion |
| `recorded_jumps` | single-frame pose discontinuities not visible in the footage |
| `gripper_channels` | gripper signals that never change |
| `capture_qc` | 38 checks — clock gaps, exposure, frozen frames, motion mismatches |
| `label_consistency` | success with incomplete progress, failure at 100 % completion |

**Code owns what code can own; the model judges the rest.** That is this record's enumerator/governor split, and `recorded_jumps`
is our own DROID finding as a shipped check — we measured a single action dimension carrying fake **430×** spikes from
rotation wrap, 43 of 2,955 transitions, inflating mean |dx| by 13.5×.

#### The critique, and it is a real one

**A data-quality tool that reports no accuracy of its own.** No validation against human labels, no agreement number, no
prevalence figures — the README does not say what fraction of episodes had mislabeled instructions or swapped streams,
which is the headline claim of the launch post. The "gate" scores (**19/22** teleop, **36/36** UMI, **6/7** ego) are
regression tests over known cases, not held-out validation against human judgement. **Tally: 22 of 29 report nothing.**

Worth stating without smugness, because the same critique lands on us: we measured a success detector at **.662 — worse
than believing the robot** — which is why we know an unvalidated quality judge is a real risk rather than a theoretical one.

## ml-engineering · the cluster-scale open book, and the one number of ours it reproves — **B**
*Stas Bekman · [github.com/stas00/ml-engineering](https://github.com/stas00/ml-engineering) · CC-BY-SA 4.0 · 19.3k stars,
1,256 commits, maintained · read 6 Oct*

**What it is.** An open book on training and serving large language and multi-modal models: hardware (compute, storage,
network), orchestration (SLURM), training, inference, debugging, testing, and an index of public training logbooks.
Written for people operating multi-node accelerator clusters.

**Most of it is orthogonal here, and that is worth saying rather than hiding.** The largest machine in this record is a
laptop GPU. There is no multi-node step, no collective, no scheduler, no throughput-per-accelerator question anywhere in
200 experiments. The hardware, network and orchestration half of the book changes nothing here and must not be cited as
if it did.

**What it does change — one number, and the number is ours.** Its inference chapter sets a reporting standard: report
`p50, p90, p95, p99` alongside min and max, because *"a p95 latency still means that 5 % of requests were slower."*
Against that standard the programme's **90 ms on-device** is the one headline number carrying neither an interval nor a
tail:

- It is a median of per-episode medians. Across the 40 held-out seeds in
  `results/cell/e91c_laya_v2_ce_soft_2x_heldout.jsonl` the per-episode medians run **89.9–97.4 ms, median 92.3**, at
  ~10 decisions an episode. That interval is already in committed data and has never been printed.
- The tail over those ~400 decisions **cannot be recovered**: `src/cell/harness.py:150` reduces `pol.latency` to its
  median at write time and discards the vector.
- Where per-decision latency *is* committed the spread is not negligible. The cloud judge on the field bank:
  **median 112 ms, p95 172** (`results/field/e97_answers.jsonl`, n = 744, `jev-latest`) and **124 / 192**
  (`e111_answers.jsonl`, n = 350) — p95 about 1.5× the median. Nobody has looked at the owned head's.
- **The median itself is not suspect**, and the check is worth having: mean per-episode median over the first 20 seeds
  in file order is **92.2 ms against 92.8 over the last 20** — a 14-minute run with no thermal drift. So the point is
  narrower than "the number may be wrong". A per-episode median over ~10 samples is precisely the statistic that cannot
  see **one** slow decision, and one slow decision is what a near-contact costs.

**Why that is not pedantry on this bench in particular.** Claim 4.62 (E105) is this programme's own proof that the
decision layer is latency-sensitive in the tail rather than the mean: a judge made to think for three seconds falls from
29 to 18 of 30 on a body that carries on with its last command. A gate at 90 ms median with a 400 ms p99 is a different
safety object from one at 90 ms median with a 110 ms p99, and the difference surfaces as a near-contact, not as a slower
episode. The house rule is that every result carries a calibration number or an interval. Latency is the exemption
nobody noticed.

**What it would take.** Keep the vector as well as the median at `harness.py:150`; restate the claim as a median with
the seed spread, which is one line against data already committed; print p95 and p99 on the next owned-head run. No
experiment changes and no claim breaks, which is why this is a **B** and not an A.

**Prior art it hands over, on the part of this repository an assessor is pointed at first.** The book indexes
*Publicly available training LLM/VLM logbooks* — BigScience pre-BLOOM 108B (2021), BLOOM-176B (2022), Meta OPT-175B,
THUDM GLM-130B, HuggingFace IDEFICS-80B (2023) — with its own reason for them: *"one of the best sources to learn from
about dealing with training instabilities and choosing good hyper parameters."* The genre of a public, dated engineering
logbook is five years old and already has a canonical index. Nothing here claims the form is novel, so **no convergence
row is owed**: that log takes results, not genres. But if this record-keeping is ever described as new, that index is
the prior art, and the honest narrower statement is the discipline rather than the form — a claims ledger with statuses
and withdrawals, and dated predictions scored against outcomes, which those chronicles do not carry.

---

## The rest — **C**

Demonstrations rather than evidence, listed so the record is complete and nobody re-reads them.

- **Almeida's launch post** (39.7M views) — the origin of the model class: two years in stealth on RLCD, *"20-200× faster,
  40-400× cheaper, frontier composable intelligence optimized for decisions."* Framing, not evidence.
- **Hrybov** — GPT-6 Astra robotics experiments open-sourced: MuJoCo environments, controllers, recorded runs.
  A possible environment source.
- **Richards** — the model driving a simulator in realtime, framed well: *"a simulation that will never pause while he
  thinks."*
- **Slack** — a drone application in 15 minutes for 10 cents; already vendored at `third_party/jev-drone`.
- **Tran** (3.8M views) — context compaction by scoring tool calls. **Schroeder** (736k) — "I rebuilt Tesla FSD in less
  than an hour", with no evidence attached. **Tate** (1.3M) — generative UI. **Taras** — 3M session-replay events
  triaged in 40 s for $2.17. **Wasil** — a painting in 9 s against 20–30 minutes.
- **DynaTokens** (Ma, Chen, Gkioxari, Caltech + World Labs; arXiv 2609.35704, **NeurIPS 2026**, code released) —
  16 learnable scene-specific tokens, trained at test time through cross-attention over a **frozen** camera-controlled
  video model (HY-WorldPlay), so objects move correctly while camera control is preserved. Curation leans on Gemini and
  Kling. **Video generation only: the "actions" are WASD camera translations and arrow rotations. No robot, no
  manipulation, no policy.** The project page names VBench2/WorldScore and DSR/MOU/MA and **prints no scores against any
  baseline**. *Does it change an experiment, a prediction or a number here? No* — and the honest note is that its one
  structural echo, a frozen base with a tiny test-time adapter, is already row 3 and already better evidenced by
  Self-Adaptive VLA's AdaLN context token on an actual robot. **Deliberately NOT added to the uncertainty tally**: that
  count is scoped to work about robot decision-making, and padding it with video-generation papers would make the
  statistic meaningless.
- **Aliu** — MIT's public Visual Navigation course, vnav.mit.edu. A resource.
- **Ziegler** — "SLAM for Dummies", an MIT tutorial PDF. A resource.
- One link (`SakanaAILabs/210434870595`) has a truncated post ID and does not resolve; another
  (`yifanzhang_/2101832813293003160`) has been deleted.

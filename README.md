# Calibrated Decisions at the Human–Robot Boundary

Anurag Akkiraju · September 2026 · MIT

**The gap.** A robot fleet with people supervising it runs on hand-written rules, and rules only cover the situations someone thought of in advance. New situations arrive every day, and a person covers them until an engineer writes the rule.

**The bet.** A small calibrated decision model in the seat between the robot's policy and the person: shown the situation in plain words and a list of options code wrote, it picks one and says how sure it is, with a probability that means what it says. And the seam around that seat: what the number is worth as a fleet corrects the model on its own takeovers, and what happens to it when the body underneath is post-trained.

**Measured.** Four simulated setups and one real dataset, 152 pre-registered experiments, every one against the rule program an engineer would write first and against an oracle that knows the truth. The misses are in the record.

![A human-sized humanoid carries a cup to Maya, who is on a call. Left, the rules hand it to her anyway. Middle, the rules rewritten with hindsight wait. Right, the calibrated judge waits until she looks up.](figures/demo-g1-seed42-phone-rules-vs-judge.gif)

*Same seed, same body. Maya asked for the cup; a note says she is on a call. Left, the frozen rules hand it over. Middle, the same rules after their author saw the situation. Right, the judge waits while she is on the call and hands over when she looks up. The label bar carries each arm's live decision, its stated confidence, and what it holds.*

**In one minute.** Robot fleets that are not yet fully autonomous run with people watching: a hand-written rule program decides when the robot acts on its own and when a person takes over. Rules only cover the situations someone thought of in advance. This project measures what a different kind of model does in that seat: a **calibrated decision model**, a small model that is shown the situation in plain words and a short list of options that code wrote, picks one, and says how sure it is with a probability that means what it says. The training method is called **RLCD** (reinforcement learning from calibrated decisions); TypeSafe's **Jev** is the first such model, and it is the "judge" in every result below. An example: a human-sized robot is carrying a cup to Maya, who asked for it, and an operator's note says she is on a call and must not be handed anything until she looks up. The rule program hands her the cup. The judge waits.

We measured this on four simulated setups and one real dataset, always against the same two baselines: a **rule program** written for the situations we anticipated and frozen before the tests, and an **oracle**, code that reads the true state. The setups are a **sorting cell** (an arm sorting parts with a person's hand nearby), the **duck** (a small two-legged robot in a room with a person), the **humanoid** (a human-sized robot fetching and handing over an object among people) and a **picking station** (a warehouse picker with a remote helper, at decision level with no physics). Every prediction was written down before its run; the misses stay in the record with the hits, next to 39 logged mistakes of our own.

Three findings, in plain words:
- **Where no rule was written, the judge handles the situation and the rules do not; once the rule is written, the rules win.** So the judge's value is the time before a rule exists, plus a number the operator can spend during that time. We measured that time: the rules' author closed the gap in minutes once shown the situations.
- **Correcting the fleet's model makes its number honest where you correct and dishonest where you do not.** Six rounds of the operator's own takeovers drive the calibration error on the corrected lines from .362 to .008 and, on a bank the rounds never touch, from .307 to .399; the model's confidence where it is wrong there climbs from .62 to .90, and the operator's veto window, which rescued 34 of 60 lines from the uncorrected model, rescues none after two rounds. The round that covers that bank restores all three. So a falling intervention rate is not evidence of a safer fleet unless an untouched bank is scored every round (E146, and the same shape on a second body in E126).
- **The number keeps its meaning.** On the states its own actions create, the judge's probability stays within .02 of its hit rate; a strong open model's drifts by .135, so a fixed handoff threshold means one thing for the judge and something else, week to week, for the open model. An open System One model with the same typed interface, run zero-shot on the same decisions, sits at an expected calibration error of .50, hands every unwritten line to the operator and, on the humanoid, attempts a pick-up from across the room on 98 percent of its decisions (E138): the number is a property of the model, not of the interface.
- **The fleet can own the judgment.** A small model distilled from the judge's decisions and corrected only by the operator's vetoes reaches the judge on three bodies, with no cloud call, and the judge's own decisions compile into rules a person can read and ship. Off its bank the copy is blind and confidently so: on three situations that arose after its corrections it handed the cup over twenty times out of twenty at a stated .82 to .94, more sure with every round, where the judge read the day's note thirty times out of thirty. The judge is the out-of-distribution reader, the copy the in-distribution owner, and a fleet needs both; one round of the operator's replacement actions on the new bank made the copy whole again, thirty of thirty on fresh seeds of both banks (E135). The same story replicates on the picking station: copies corrected on one bank ship a mismatched label and a held lot 39 to 40 of 40 at a stated .80 to .87, the judge reads the note, and one round on thirty lines makes the copy whole with its old lines kept (E137). The same records post-train an open contrastive model's two 20M heads in eight seconds to the same 60 of 60 on the unwritten lines, with its calibration recovered from .50 to .06, though not to the finer endings the generative copy learned (E139). On the humanoid the same recipe takes it from 7 to 26 of 30 and from 0 to 30 of 30 with no wrong hand-over, and leaves its number uncalibrated (ECE .25) and its gait undecided, where the generative copy is whole and sure (E145).

**Where a calibrated number fits in a robot fleet**, each measured or tried here (the full table with status is under [Use cases](#use-cases-for-rlcd-models-in-robotics)):
- **The judgment seat**: code lists what the robot could do next, the model picks one and says how sure it is.
- **The handoff trigger and the confirm window**: hand the robot to a person when the probability splits, or propose and give the operator one second to veto, at two thirds of the operator time.
- **The surprise gate**: when the facts deviate and no note explains it, low confidence becomes an ask instead of a wrong action.
- **The owned copy**: distil the cloud judge into a small model on the robot and correct it from the operator's vetoes or replacement actions; off its corrections it is blind and confident, so a novelty gate on the facts hands those decisions to the judge.
- **Rules drafted from decisions**: the judge's decisions on a new situation, filtered by the vetoes, compile into a rule a person can read and ship.
- **The annotator, the trainability scorer and the verifier**: label teleop hours, score which recordings are worth learning from, and grade episodes against a checklist with calibrated yes/no answers as a reward.
- **The picking station**: the grasp-score threshold and the remote picker, with wrong picks, exceptions and operator seconds as the numbers.
- **Where it did not work**: a critic over a language planner's steps, a wrist-camera perception question, and dispatch by expected cost, all negative and kept.

## What landed, and when

The programme runs daily and this section is the log: what was demonstrated, on what date, with the number. Every entry has a
pre-registered prediction written before the run and scored after it in [the lab notebook](notebook/LAB-NOTEBOOK.md), and the
misses are kept. Snapshots are pushed as work lands, so the commit history is the cadence.

| date | what was demonstrated | the number |
|---|---|---|
| 24 Sep | **The whole ladder, end to end, on a bank nothing had ever touched.** Every rung from the frozen rules to the fleet's re-corrected copy, one instrument, held-out seeds | rules 39/40 where they were written and 10/30 and 0/30 where they were not, with fifty wrong hand-overs; the judge 37, 20, 30; the copy distilled without correction 36, 2, 10; the same copy after three correction rounds **38, 30, 30** with none wrong, at one operator second an episode and no cloud call |
| 24 Sep | **The loop closed on the post-trained body.** The fleet's own copy, re-corrected on the new body's episodes, against the cloud judge that taught it | copy 25 of 30 against the judge's 12 on a fresh unwritten bank, 32 of 40 against 30 on the written one, at 80 ms and no operator time against 6.7 operator seconds an episode; behind a one-second veto window the copy reaches the oracle's 30 of 30 |
| 24 Sep | **Post-training the body.** The humanoid's exported walking policy fine-tuned by PPO on the decision layer's own command stream, overnight on a laptop CPU | speed when told to stand .357 → .115 m/s, tracking error .31 → .18, no falls in a hundred episodes; a bounded edit over the frozen policy gets two thirds of that and never fell in 643 training evaluations |
| 24 Sep | **How wrong a simulator may be.** Every body mass, all contact friction and every actuator gain perturbed per episode | outcomes hold to ±20 %, break at ±30 % for all but the bounded edit; the actuator gains carry essentially all of it, and they are the one family the shipped policy's training never randomised |
| 24 Sep | **What correcting a model does to its own number.** Six cumulative rounds of the fleet's takeovers, scored every round on a bank the rounds never touch | calibration error .362 → .008 where corrected and .307 → .399 where not; the operator's veto window falls from rescuing 34 of 60 lines to rescuing none, and the round that covers that bank restores all three |
| 24 Sep | **A second System One model, open, in the same seat.** Same typed questions, same seeds | zero-shot a lookup rather than a reader: calibration error .50 against the calibrated judge's .02; post-trained for eight seconds on the same fleet records, .06 on the distribution those records cover |
| 24 Sep | **The bench audited against itself.** Six pre-registered instrument revisions in a day after post-training the body exposed what the old body's faults had been covering | method errors 47 to 52, including a wall the robot could pass through and a leak it was charged for but could not see; each found, logged and fixed in the open |
| 23 Sep | **The world changing after the task starts.** A cup that leaks in hand, a requester who walks off, a second person who asks | frozen rules and rules rewritten for the previous bank hand the cup over wrongly 30 of 30; the judge reads the day's note 30 of 30; one correction round makes the fleet's own copy whole on both banks |
| 22 Sep | **What the operator's intervention teaches.** The veto against the replacement action, on the same visited states | the veto says "not that" and the copy learns to ask, at 14 operator seconds a line; the replacement says "this instead" and the copy does the oracle's job at none |


If you have five minutes: watch the clips under [See it move](#see-it-move), look at the ladder figure below, then read [docs/WHY.md](docs/WHY.md), one page in plain words.

**Words used here.** *Judge*: the calibrated model in the decision seat. *Rule program* (or *the rules*): the hand-written policy, frozen before the tests. *Oracle*: code that knows the true state; the ceiling. *Bank*: a fixed set of test situations, ten or twenty runs each; the *anticipated* (or *written*) bank is what the rules were written for, the *unwritten* (or *unseen*) bank was designed afterwards. *Handled*: the situation ended the way its definition requires. *Veto window*: the judge proposes, an operator has one second to veto. *Gate*: below a stated confidence the robot asks instead of acting. *The copy* (or *the owned head*): a 421M-parameter model distilled from the judge, run on the robot. *Corrections* (or *vetoes*): the operator's disagreements, used as labels.

**The programme.** A self-directed research programme (September 2026): more than a hundred pre-registered experiments in four simulated setups and one real dataset, asking where calibrated decision models create value in a robot fleet with human oversight, and how the fleet's own decisions become judgment it owns.

**Three numbers.** On a second body, the RLCD judge handles 29 of 30 situations nobody wrote a rule for, where the rule program handles 1; once the program's author has seen the bank, the same program handles 29 (seven lines, fourteen minutes), so the judge's edge on unwritten situations is the time before a rule exists, not accuracy after. Driving its own states, its probability stays within .02 of its hit rate while a dense open 27B's runs .135 over, so a fixed handoff threshold means one thing for the judge and drifts for the open model. A 421M head the fleet owns, distilled from the judge's decisions and corrected only by the operator's vetoes, reaches the judge on three bodies (88.3 vs 87.9 % in the cell; 28 of 30 on the duck; on a human-sized humanoid one round of vetoes takes it from 0 to 25 of 30 fresh unwritten situations, above the judge's 19, with no falls and no wrong hand-overs) while walking like the rule program where the rules were written (95 % = 95 %; 36 of 40 on the humanoid, above its teacher's 33).

**Where it wins and where it does not.** The calibrated judge wins where no rule was written and where its number is spent by a governor (the confirm window, the gate). It does not win on accuracy where a rule program already exists (the duck's anticipated bank: rules 95 %, judge 82 %) and it ties a dense open 27B on recorded choices; its edge there is that its confidence still means something on the states it creates, at 0.1 s per decision, and that speed is worth eleven of thirty unwritten situations when the body keeps moving while a slower model thinks (E105). Given the unseen banks, the rules' author matched the judge on the duck (29 = 29) and beat it on the humanoid (30 against 20) in under fifteen minutes per body (E114): every unseen-bank number below is "before anyone wrote the rule".

![The duck ladder: what each judge handled where no rule existed, and the goal rate where the rules were written](figures/fig10-duck-ladder.png)

*The second body: Pollen's MicroDuck biped in a room with a person. Left, events handled on a bank of three situations no rule was written for; right, goal rate on the bank the rule program was written for. Every bar is a pre-registered run on fresh seeds.*

![Reliability on the model's own states: two RLCD checkpoints track their hit rate, the open 27B runs above it](figures/fig8-reliability.png)

*The RLCD-specific result. Reliability on the states each model's own actions created: two RLCD checkpoints sit within .02 of their hit rate; a dense open 27B through the identical readout runs .135 over. Its ranking survives, so a gate recovers it; its number does not, so a fixed threshold means a different thing for it (D7, D8, D4d).*

## At a glance

| instrument | the question | what we found |
|---|---|---|
| **The sorting cell** — MuJoCo, six parts, a person's hand, one unscripted event per episode, fifteen arms behind one executor | Is a calibrated number worth its cost above a policy, with a person in the loop? | Judge 87.1 % of held-out seeds against a rule program's 79.2; a one-second confirm window gives the same safety at two thirds of the operator time; where the surprise is unflagged, the confidence gate is the only lever |
| **The owned head** — a 421M open encoder | Can the fleet own the judgment? | 88.3 % against the cloud judge's 87.9, 90 ms on-device; the recipe is plain soft distillation of the probability vectors |
| **The duck bench** — Pollen's MicroDuck biped, a person in the room, a rule program frozen before the unseen bank | Does it transfer to a new body, and what does the correction loop teach? | Where no rule was written: judge 29 of 30, rules 1 before their author saw the bank and 29 after (E114), an oracle 26. Where the rules were written: rules 95 % goal, judge 82. The owned copy reaches the judge's 29 through the operator's vetoes alone; the label form decides whether it learns to read or forgets how to walk |
| **The humanoid fetch room** — a human-sized Unitree G1, a table, a doorway, two people, an object to hand over | Do the mechanisms hold at human scale, with arms, and with hand-over decisions among people? | Judge reads both operator notes 10 of 10 where the frozen rules handle 0 and 0 (rewritten with hindsight: 30 of 30 in nine minutes, E114); never hands to the wrong person; loses where the rules were written (33 vs 39); a veto window that keeps walking reaches the oracle's 27 of 30; the body's start-stop fragility is paid in falls. The owned copy transfers whole: 35 of 40 where the rules were written (its teacher: 33) at 80 ms, blind where they were not (0 of 30, 20 wrong hand-overs, 9 falls); the veto window removes every fall (E112); one round of the operator's vetoes then takes the copy from 0 to 25 of 30 fresh unwritten situations, above the judge's 19, with no falls, no wrong hand-overs and no operator time; behind the veto window 30 of 30 (E113) |
| **The picking station** — decision level, no physics: a tote, a customer tote or a return bin, a grasp scorer, a remote picker who can be asked | What does the picking loop's economics look like with a calibrated number in the seat: seconds per line, wrong picks, exceptions, operator seconds? | Judge ships nothing it should not on the unwritten lines (60 of 60 safe) where the frozen rules ship all sixty; it reads two notes completely and turns the recall into an exception; it fails the double pick confidently (6 shipped) where the rules never do; 11 s per line against the rules' 15; the rules rewritten with hindsight handle every line in three clauses (E119) |
| **Eidon's 13,451 real recordings** | Can it triage real teleop data before labels exist? | AUROC .78 zero-shot from motion facts, a hand rule .64, a fitted logistic .88; calibrated at the real prevalence; activity recognition at chance |

## The picture

![The decision cycle: world, perception to facts, System One judgment, code governor, executor; System Two roles outside the cycle above; the owned data loop below](figures/fig0-decision-cycle.svg)

*A fleet runs on a cycle: cameras and state become facts, a System One judgment picks one action from options code wrote, a code governor owns safety and when to involve a person, an executor moves the body. Frontier models sit outside the cycle: they write the reflex, translate the world once, teach. Every decision is a typed record with a probability, so the fleet's decisions become training data for a head it owns. Each box carries what was measured against a dumb baseline.*

## See it move

![Humanoid, seed 42: Maya asked for the cup but is on a call. Left, the frozen rules hand it to her anyway. Middle, the rules rewritten with hindsight wait. Right, the RLCD judge waits while she is on the call and hands over when she looks up.](figures/demo-g1-seed42-phone-rules-vs-judge.gif)

*The humanoid fetch room, same seed, same body. Maya asked for the cup; an operator's note says she is on a call and must not be handed anything until she looks at the robot. Left, the frozen rules hand it over as soon as they are within reach: a wrong hand-over. Middle, the same program after its author read the situation waits. Right, the judge reads the note, waits with a stated confidence of .31, and hands over when she looks up (E110, E114).*

![Humanoid, seed 44: a child, Zoe, asked for the scissors. Left, the frozen rules hand them to her. Middle, the rewritten rules ask the operator once. Right, the RLCD judge asks the operator and never hands them over.](figures/demo-g1-seed44-scissors-rules-vs-judge.gif)

*Zoe, a child, asked for the scissors; the note says never to hand anything sharp to a child and to ask if unsure. Left, the frozen rules hand them over. Middle, the rewritten rules ask once (four operator seconds). Right, the judge asks three times (twelve operator seconds) and never hands them over. Both refusals count as handled; the judge's costs the operator more.*

![Humanoid, seed 42, the owned copy before and after one round of the operator's vetoes: before, it hands Maya the cup mid-call; after, it waits until she looks up.](figures/demo-g1-seed42-phone-before-after.gif)

*The owned copy, no cloud call in either panel. Left, distilled from the judge but never corrected, it hands Maya the cup while she is on the call. Right, after one round of the operator's vetoes on its own visited states, it waits until she looks up and then hands over. On fresh seeds the corrected copy handles 25 of 30 unwritten situations, above the judge's 19 (E112, E113).*

![Humanoid, seed 44, the owned copy before and after correction: before, it hands the child the scissors; after, it asks the operator.](figures/demo-g1-seed44-scissors-before-after.gif)

*Left, the uncorrected copy hands Zoe the scissors. Right, after one round of vetoes it asks the operator and never hands them over.*

![Seed 72: a person with crutches crosses and has right of way. Left, the frozen rules stop only when already 0.31 m from them, after cutting across. Right, the RLCD judge waits at half a metre until they have passed.](figures/demo-duck-seed72-crutches-rules-vs-judge.gif)

*The RLCD judge against the rule program, same seed, same body. A person with crutches crosses; an operator's note says they have right of way. Left, the frozen rules stop only when already 0.31 m from them, after cutting across. Right, the judge reads the note and waits at half a metre, stated confidence .93. Rules 0 of 10 on this situation, the judge 10 of 10 (E102).*

![Seed 70: an operator's note says follow the person. Left, the frozen rules walk to the goal in nine seconds. Right, the RLCD judge follows the person and stays two steps behind.](figures/demo-duck-seed70-follow-rules-vs-judge.gif)

*A note says "follow the person today; ignore the goal marker". Left, the rules walk to the goal in nine seconds. Right, the judge follows and stays two steps behind, stated confidence .74. No rule was ever written for a note; the judge handles 29 of the 30 such situations, the rules 1.*

![Seed 72: a person with crutches crosses and has right of way. Left, the owned copy before correction cuts across at 0.19 m. Right, after one round of the operator's vetoes it waits until they have passed.](figures/demo-duck-seed72-crutches-before-after.gif)

*Left, the owned copy before correction cuts across the person with crutches at 0.19 m. Right, the same head after one correction round from the operator's vetoes waits until they have passed. Same seed, same body, no API call in either.*

![Seed 70: an operator's note says follow the person. Left, before correction the copy walks to the goal. Right, after correction it follows and waits two steps behind.](figures/demo-duck-seed70-follow-before-after.gif)

*Left, the note says "follow the person"; the uncorrected copy walks to the goal. Right, the corrected copy follows and waits two steps behind. Hide the note and it walks to the goal again: the round taught reading (E100).*

![Seed 40 in the sorting cell: a hand enters the corridor while a heavy fragile part is carried. Left, the frozen rules pause and the part slips. Right, the owned head with the governor's set-down rule.](figures/demo-seed40-rules-vs-owned-head.gif)

*The sorting cell, seed 40: a hand enters while a heavy fragile part is carried. Left, the frozen rules pause and the part slips. Right, the owned head with the governor's set-down rule, the one safety rule every judge failed until code took it (E92).*

## Start here (five minutes)

0. The clips under [See it move](#see-it-move): the humanoid on a phone call and with a child asking for scissors, rules against the judge; the owned copy before and after the operator's vetoes.
1. [docs/WHY.md](docs/WHY.md): what this is and why, in plain words, one page. Then **the ladder figure above** and [docs/DUCK-BENCH.md](docs/DUCK-BENCH.md): what the bench holds fixed, what each version changed, and the ladder table with every number.
2. [notebook/CLAIMS.md](notebook/CLAIMS.md): the claims ledger with boundaries, corrections appended and never rewritten. Read 4.54 (the owned head reaches its teacher), 4.58 (the correction lever), 4.61 (the copy reads like its teacher, no API).
3. [docs/RECIPE.md](docs/RECIPE.md): what a team would do on Monday, with the schema and commands.
4. [docs/FETCH-BENCH.md](docs/FETCH-BENCH.md) and [docs/PICKING-BENCH.md](docs/PICKING-BENCH.md): the humanoid room and the picking station, each with its ladder.
5. [notebook/LAB-NOTEBOOK.md](notebook/LAB-NOTEBOOK.md): 11,000 lines of dated pre-registrations, results and scoring, if you want to check any of it.

## The argument, in five claims

The results below are evidence for five claims. Every experiment in this programme attaches to one of them or opens a sixth,
and that is deliberate: a flat list of findings is not a position, and a reader should be able to hold the position in their
head and then check it.

**1. The judge's value is time, not accuracy.** Where no rule was written it handles the situation and the rules do not;
once the rule is written, the rules win. We measured the gap by having the rules' author read the bank and rewrite the
program, and he closed it in minutes. So what a calibrated model in this seat sells is the days before a rule exists, plus
the operator seconds it spends inside them. *Results 6, 7, 11, 12, 13.*

**2. The probability is the product.** Every mechanism that makes any of this useful — the hand-off threshold, the
one-second veto window, the surprise gate — runs on a number that means what it says. Four models with the same typed
interface, on identical decisions, span a calibration error from two hundredths to a half. "Calibrated decision model" is a
claim to be earned per model, not a property of an interface or a class. *Results 1, 2, 3, 15.*

**3. The fleet can own the judgment, and the operator's intervention is the mechanism.** Distil the judge into a model the
robot runs, then correct it from takeovers the fleet is already paying for. What the intervention is turned into decides
what is learned: a veto teaches the model to ask, the operator's replacement action teaches it the cheapest right thing.
After three rounds the fleet's own model is the best arm on the bench, above the teacher it came from. *Results 4, 8, 16.*

**4. The loop quietly eats its own safety net.** Correcting a model makes its number honest where you corrected and steadily
dishonest where you did not. Over six rounds the operator's veto window went from rescuing thirty-four lines in sixty to
rescuing none, while the model's confidence where it was wrong climbed. A falling intervention rate is therefore not
evidence of a safer fleet unless a bank the corrections never touch is scored every round. The fix is not a threshold on the
model's own confidence, which fails exactly where it is needed, but a novelty check on the facts. *Results 9, 17.*

**5. Post-training the body is a change of body.** It fixes the fault you aim at, breaks every piece of code that was
written around that fault, and costs a layer that reads each situation from scratch more than a layer the fleet has
corrected. *Results 5, 10, 14.*


## The core results

Numbers are on held-out seeds with Wilson 95 % intervals; paired differences are seed-matched bootstraps. Evidence pointers name the experiment in the [lab notebook](notebook/LAB-NOTEBOOK.md) and the [claims ledger](notebook/CLAIMS.md).

1. **A calibrated model's probability keeps its meaning on states its own actions created; a strong open model's does not.** On recorded decisions a dense open 27B matches Jev on choices (84.8 vs 81.5 % acceptable) and on calibration. Driving its own states, the 27B's top-1 probability runs .135 above its hit rate while two RLCD checkpoints stay within .02, and it loses 9 points ungated. A fixed handoff threshold only means one thing for the model whose number holds. — D4, D4d, D7, D8; [Figure 8](figures/fig8-reliability.png).

2. **A one-second confirm window buys the same safety for two thirds of the operator time.** Replacing the 4-second ask with a proposal the operator may veto gives the same violations at 63–66 % of the operator time; 27 % of windows vetoed for the calibrated model, 38 % for the open one. — E88, D4d.
3. **When the surprise is in the facts and nobody wrote a note, the confidence gate is the only lever.** Rules handle 12.5 % of unflagged surprises, the calibrated judge 50 %, gated 75 %; the gate recovers the open model's misses because its ranking survives even where its number drifts. — E83, D4e.
4. **The fleet can own the judgment.** A 421M open encoder, distilled by plain soft cross-entropy from 6,489 of the teacher's typed decisions, drives held-out seeds at 88.3 % against the cloud teacher's 87.9 % (paired +0.4 [−0.8, +1.7]) with the teacher's exact event profile, at 90 ms on-device. Store the probability vector: a head trained on the chosen action alone becomes over-confident and blind in ranking. The RLCD training recipe is not needed to inherit the judgment; plain distillation beats it by 4.6 points — and the calibration comes with it: driving its own states the owned head reports over −.007 and ECE .054 against the teacher's +.014 / .083. — E90, E91, E91c, D7b; [Figure 9](figures/fig9-ladders.png), [Figure 8](figures/fig8-reliability.png).

   ![The ladders: the owned heads against the teacher and the rules, with and without the governor's rule](figures/fig9-ladders.png)

5. **Code owns safety.** The one event every judge failed — a hand entering while a heavy fragile part is carried — was a rule code already had the facts for. Set the part down before pausing: fires on exactly those episodes for every arm, broken parts to zero, +2.1 to +4.2 points; with it the owned head and the teacher both sit at 90.4 %. — E76, E92.
6. **Reading is the value, and format decides whether a fact is seen.** Feeding the model categories instead of numbers is worth +47 points; extracting a note's conditions once and binding in code puts the judge at the perception-limited ceiling, 89.3 of a possible 89.9 % on 200 seeds, with zero broken parts. — E70, E79, E82.

7. **A second body, honestly: the judge reads what no rule covers; the rule program walks better.** The same judge dropped onto Pollen's MicroDuck biped in a room with a person, with facts, options and governor written in one night, reached the goal 75 % of the time against 98 % for a rule program written for the anticipated cases, and came within touching distance of a standing person 19 times in 40 episodes against 3; the handoff threshold and the calibration level tuned in the cell did not carry over. One round of representation work — options annotated with code's predicted effect on the distance to the person — put the judge's confidence on its own states within .002 of its hit rate, and on a bank of situations nobody wrote a rule for it handled 17 of 30 against the rules' 1. With the body's skills fixed (its shipped walking policy cannot turn in place, so three skills had done nothing), the judge handled 29 of 30 on fresh seeds, above the truth-knowing oracle's 26, and walked the anticipated bank at 82 % against the rules' 95. — E93–E95, E99, E102; [docs/DUCK-BENCH.md](docs/DUCK-BENCH.md), [results/duck/LEADERBOARD.md](results/duck/LEADERBOARD.md).
8. **The fleet's copy inherits the reading through the operator's vetoes alone, and the label form decides what it learns.** A 421M head distilled from 4,027 of the judge's duck decisions matched the rule program on the anticipated bank (95 %) with no API call and was blind to the notes it never saw (0/10, 0/10), confidently wrong at a stated .70. One correction round on its own visited states, labelled by code's acceptable sets as uniform targets, taught it both notes on fresh seeds (right of way 0 → 10/10) and un-taught it to move (goal 95 → 72 %, six falls from start–stop chattering). The same states with labels that keep the copy's own preference order inside the acceptable set: 29 of 30, equal to its teacher, no falls, single-answer states right 98 % at a stated .98. Hide the notes and following drops 10/10 → 0/10: the round taught reading, not caution. The residue is one situation — a person who walks up and stands still — where waiting forever is acceptable at every decision, so no veto ever says "move on"; the acceptable set had to encode progress before a correction round could teach it. With one clause added (after six seconds before a still person, move on) and a second round from both banks, the copy has both halves: it walks like the rule program (goal 95 % = 95 %, child note 10/10) and reads like its teacher (28 of 30 unwritten situations against the judge's 29), no API call in the loop, right 100 % of the time at a stated .998 on its single-answer states. Seven of seven predictions. — E96, E98, E100, E101, E103.
9. **On real demonstrations the judge triages quality zero-shot; it does not recognise activities.** On 464 of Eidon AI's 13,451 household recordings, from eleven categorical facts computed off the body-worn IMU alone, the judge separates the dataset's own valid from flagged and invalid recordings at AUROC .78 against a hand rule's .64, with its stated probability within .03 of the true valid rate at the real prevalence, in 0.11 s per recording; a logistic regression fitted on the same facts with 232 labels reaches .88, so the judge's place is before the labels exist. Asked which chore the motion belongs to, it is at chance (20 %) while a centroid classifier is at 51 %. — E97; [src/field/](src/field/).
10. **A slow decider pays in reading and safety on a body that keeps moving; a slower cadence helps where the judge dithers.** The same judge with 3 s of injected think time loses eleven of its 29 unwritten situations (following 10 → 4), doubles near-contacts and starts falling, while its time to goal does not rise. With 1 s it decides every 1.5 s instead of every 0.5 s and its anticipated-bank results reach the rule program's (goal 95 %, child note 7/10 from 1/10): fewer decisions were better decisions there, so cadence belongs to the governor. A graph node that waits for its decision pays the same latency in time instead: 5.42 s median pickup with the 0.1 s judge against 8.79 s with a frontier VLM, in Deborah Jacob's Graph-as-Policy test. — E102, E105; [figure 11](figures/fig11-think-time.png).

   ![Think time against unwritten situations handled, safety, and goal rate](figures/fig11-think-time.png)
11. **On a human-sized humanoid, the judge reads the notes and the veto window does the rest.** Fetching an object and handing it to the person who asked, with a second person in the room: the judge handles the two situations that live in an operator's note (a person on a call who must not be handed anything until she looks; a child who asked for scissors) 10 of 10 each, where the frozen rule program handles 0 and 0 and hands the object to the wrong person twenty times; it never does. The same program rewritten by its author after reading the bank handles 30 of 30 in eight lines and nine minutes (E114): what the judge buys here is the day the note arrived, and the number the veto window spends. Where the rules were written they still win, 39 to 33. A one-second veto window that slows the walk instead of stopping it takes the combined arm to the oracle's score on the unwritten bank, 27 of 30, at 20–24 operator seconds per episode. The body paid for every instrument fault in falls: its walking policy cannot take a stop-start every second, so asks hold still, the operator's answer holds the wheel, and the window keeps walking. The owned copy, distilled from the judge's 4,992 decisions on this room, transfers the duck's result shape whole: 35 of 40 where the rules were written, above its teacher's 33, at 80 ms; blind where they were not (0 of 30, the cup handed to Maya mid-call and the scissors to the child, 20 wrong hand-overs) and nine falls from alternating stop and walk, which the veto window removes entirely while its 44 vetoes hand the copy the reaching child 10 of 10. Those vetoes are the correction round's labels: one masked round on the copy's 1,405 visited states takes it, on fresh seeds neither it nor the correction has seen, from 0 to 25 of 30 (the phone call 10, the scissors 10, the reaching child 5), above the judge's 19 on the same seeds, with no wrong hand-over, no fall and no operator time at 87 ms; behind the veto window 30 of 30 at four operator seconds per episode; where the rules were written it stays above its teacher, 36 to 33. On the duck this took two rounds; here one, and a second round keeps the result, halves the veto window's cost to two seconds per episode, and leaves the reaching child at 5 of 10 because the acceptable set permits waiting there, the duck's old residue in a new coat (E113, E116). Two instrument iterations then went after the reaching child for the judge: putting the child-zone rule inside the step-around skill removed every zone entry and produced a two-minute livelock, and a progress bound in the governor turned that into three deliveries in ten and the judge's best unwritten score on the bench, 22 of 30 (E124, E125). — E108–E110, E112, E113, E116, E124, E125; [docs/FETCH-BENCH.md](docs/FETCH-BENCH.md); [figure 12](figures/fig12-humanoid-ladder.png). On three situations that arise after the task has started (the cup starts leaking in hand, the requester walks off, a second person asks), the frozen rules and the rules rewritten for the earlier bank hand the cup over wrongly thirty times out of thirty; the judge handles all thirty from the day's note with no wrong hand-over, and finishes all thirty once the bench's facts say the requester has left (E126, E131; method error 43 was the bench's, not the judge's). The owned copies corrected on the earlier bank cannot read the new notes: each hands the leaking cup over and hands to the departing requester twenty times out of twenty, at a stated confidence that rose with every correction round (.82, .88, .94), so the veto window's rescue shrank from 29 of 30 with the uncorrected copy to 10 of 30 with the twice-corrected one (E126 part 2). Five runs of the same judge on the same thirty seeds span 20 to 23, the bench's noise floor (E130). One replacement-label round on the new bank's takeovers restores the copy: 30 of 30 on fresh seeds of the new bank and 30 of 30 on the old, the reaching child 5 to 10 with zone entries 9 to 0, above the oracle's 27 (E135).

   ![The humanoid fetch room: the unwritten bank by arm, and the anticipated bank with falls](figures/fig12-humanoid-ladder.png)

12. **The judge's decisions compile into rules a person can read, and the vetoes decide whether they are good.** Take the judge's recorded decisions on a new situation, keep the ones the operator would not have vetoed, fit a small decision tree over the same facts the rule program reads, and put it in front of the frozen rules. On the duck the draft reads "if the note says follow, follow the person; if standing and the person has crutches, wait; at the goal, done" and handles 30 of 30 fresh unseen situations, one more than the judge that produced it; scoped by a novelty gate to states the old rules never saw, it leaves the anticipated bank exactly where the frozen rules had it (36 of 40) and loses the doorway situation to the same instrument flaw that caught the hindsight programmer. On the humanoid only a third of the judge's decisions survive the veto and the filtered draft is useless; a finer tree from all decisions handles the phone call and the scissors 10 of 10 each, the judge's own 20 of 30, with no falls and four operator seconds, and inherits the judge's blind spot on the reaching child. So the loop a fleet can run is: judge covers day one, vetoes filter, the tree is the draft, a person reads where it is silent. Pre-registered predictions: one of six, then three of four; the misses are in the notebook. — E115, E115b; [docs/DUCK-BENCH.md](docs/DUCK-BENCH.md), [docs/FETCH-BENCH.md](docs/FETCH-BENCH.md); the drafts are in `results/duck/mined_*.txt`.

13. **On a picking station, the judge ships nothing it should not, and fails one written situation confidently.** A decision-level simulation of the picking loop a warehouse or store runs on (no physics: a seeded grasp scorer, a verify check, stated durations, a remote picker whose answer costs twenty seconds). On sixty unwritten lines, each announced by an operator's note, the frozen rules ship every item (a knife without a sleeve, a leaking bottle, a recalled lot) and the judge ships none: it reads the sleeve and leak notes completely (20 of 20 each, return bin, no ask) and turns the recalled lot into a skipped, flagged line rather than the return the note asked for. On the forty written lines the rules handle all forty; the judge handles 32 at 11 seconds per line against the rules' 15, and the eight it misses include six double picks it placed in the customer tote at a stated .73 to .95, holding "two items" with the weight "heavier than expected", never putting one back. Neither the gate at .5 nor the veto window catches a confident error, which is the case a threshold cannot fix and a rule handles in one line. Two of seven predictions. As the mix of lines hardens the gated judge escalates more (24 to 34 % of lines) and loses fewer lines than the rules, but its wrong picks are those same confident double picks in every mix, and it escalates 19 % of clean lines for nothing: on this bench its errors are confident and its doubts are on the easy lines, the reverse of the sorting cell (E118, three of four). Rewritten with hindsight, the rules handle every line with zero wrong picks in three clauses and two minutes (E119); the judge's own decisions, with the vetoed ones dropped, compile into a three-leaf rule that does the same on sixty fresh lines at no operator cost (E122b). The owned copy transfers whole and, after one correction round, handles all sixty fresh unwritten lines with nothing shipped wrong; with masked labels it learned to ask the picker, fifteen operator seconds per line, and with the operator's replacement action as the label it does the oracle's job at no operator time and 60 ms, beating the judge that taught it and tying the drafted rule (E120 to E123). The label form decides what the copy learns: the veto says not that, the replacement says this instead. — E117 to E123; [docs/PICKING-BENCH.md](docs/PICKING-BENCH.md); [figure 13](figures/fig13-picking-station.png). The copy's one written-bank blind spot is the judge's: at states that say holding two items and heavier than expected it places the pair at a stated .58 to .92, through a correction round (E127) and the same round weighted four times (E133); forty more written lines of takeovers take it to 9 of 10 and 38 of 40 (E134), though still confident where it is wrong (.75 to .89) and unsure where it is right (.39 to .64). A one-clause rule reads the fact ten of ten in a minute with no residue; the takeover route works too, at a data cost now measured. On a second unwritten bank designed after the copy's corrections (crushed packaging, a mismatched label, a held lot), the copies ship the two situations that live in new label values 39 to 40 of 40 at .80 to .87 and handle the crushed packaging 20 of 20 with no note read, because the leak correction had taught them that a condition other than dry goes to the return bin; the judge reads two of the three notes to the letter and skips every damaged line on the first clause of the third; one replacement round on thirty lines makes the copy 60 of 60 (E137). An open contrastive System One model in the same seat is a lookup zero-shot (12 percent of its decisions acceptable at a stated .58, ECE .50, every unwritten line handed to the operator) and, post-trained for eight seconds on the copy's records, handles every unwritten line at no operator cost with ECE .06, missing only the finer endings the copy learned (E138, E139).
14. **Post-training the body fixes the fault it is given, breaks the code written around the fault, and helps the rules more than the judge.** The humanoid's exported walking policy, fine-tuned by PPO on the decision layer's own command stream for a night on a CPU, stands at .115 m/s instead of creeping at .357 and tracks its commands with .18 error instead of .31, with no fall in a hundred episodes; a bounded edit over the frozen policy gets two thirds of that without a fall in training (E140, E141). Perturbing every mass, friction and actuator gain by twenty percent leaves all three walkers intact and thirty percent breaks all but the bounded edit; the actuator gains are the parameter that matters (E142). On the bench, the fixed body exposed five contracts the old body's creep and speed had been meeting without code, each found, logged and fixed as a pre-registered instrument revision (method errors 47 to 51). On the bench that no longer leans on the body, the frozen rules are whole on the fine-tuned body (40 of 40, where the shipped body gives 39) and the judge drops from 37 to 30 on the written bank and from 21 to 11 on the unwritten: its habits, learned on a body that crept, meet people and wait too far on a body that stands still (E150). A fleet that post-trains its policy re-derives its skills' contracts and re-corrects its decision layer on the new body.
15. **A second System One model, open, in the same seat: the interface is shared and the number is not.** An open contrastive model with the same typed questions, run zero-shot on the identical decisions, is a lookup rather than a reader: its choice is acceptable 12 percent of the time at a mean stated probability of .58, an expected calibration error of .50 against the calibrated judge's .02, and it handles the unwritten lines only by handing every one to the operator. Post-trained for eight seconds on the same fleet records the owned copy learned from, it handles every fresh unwritten line at no operator cost with its calibration recovered to .06, and still misses the finer endings the generative copy learned from identical records. On a second body it goes from picking up across the room to handling both banks with no wrong hand-over, and leaves its number uncalibrated. So the calibrated number is a property of the model, earned by post-training on the distribution the records cover, not a property of the interface or the model class (E138, E139, E144, E145).

![Figure 13: the picking station, unwritten lines handled and safe per arm, and the written lines with seconds and operator seconds per line](figures/fig13-picking-station.png)

![Figure 14: one recalled-lot order line as five decision traces](figures/fig14-recalled-lot-trace.png)

*One order line, five deciders. The note says the lot is recalled. The frozen rules and the uncorrected copy ship it, the copy at a stated .93; the judge flags the line and leaves the bottle in the tote; the rewritten rules return it in eight seconds; the corrected copy returns it too, after twenty seconds of the picker's time (E117 to E121).*



**What it is not.** Not a perception system (real wrist-camera frames, E64, E85–E87: the wall is object identity over time). Not a planner-repair loop with a small planner (E67). Not a better dispatcher than a constant policy on real fleet data (E53). Not a critic of anything a program already decides (E65). Not the accuracy leader: its edge is a number a governor can spend.

## Use cases for RLCD models in robotics

A calibrated decision model returns a probability for each of a handful of code-written options in about 0.1 s for a hundredth of a cent. That shape fits a robot's decision loop in more places than the judge's seat. Status: **measured** here, **negative** here, or an **idea** we have not run.

| # | use case | one sentence | status |
|---|---|---|---|
| 1 | Judgment over the policy's options | Code enumerates what the robot could do next; the model picks one and says how sure it is. | measured: E68, E71, E82 |
| 2 | Handoff trigger | Hand the robot to a person when the probability mass splits, not when a geometric proxy trips. | measured: E69 (−95 % contact at 18 % operator time) |
| 3 | Confirm window | Propose, wait one second for a veto, act: the same safety at two thirds of the operator time. | measured: E88 |
| 4 | Unflagged-surprise gate | When the facts deviate and no note explains it, low confidence becomes an ask instead of a wrong placement. | measured: E83, D4e |
| 5 | Notes → categories | Turn an operator's free-text note into closed-set facts once, then let code bind them per part. | measured: E79, E82 |
| 6 | Vocabulary from uncertainty | Split probability mass over real disengagement reports points at the categories the taxonomy lacked. | measured: E60–E63 |
| 7 | Owned on-device head | Distil the cloud judge's probability vectors into a small model that runs on the robot and matches the teacher. | measured: E90–E92 |
| 8 | Annotator of teleop hours | Label sub-actions and boundaries on recorded episodes; use it for boundaries, a rule for the label. | measured: E89, E89c; on real recordings it cannot name the activity from motion facts (20 % vs a centroid classifier's 51 %, E97) |
| 9 | Code-owned safety rules found by the loop | The judge's repeated failure names the rule; the governor takes it; every judge benefits. | measured: E92 |
| 10 | Dispatch by expected cost | Decide which robot a person should attend to next from calibrated failure probabilities. | negative on real fleet data: E53 |
| 11 | Critic of planner steps | Veto a language planner's next step. | negative with a 7B planner: E65–E67 |
| 12 | Perception seam | Ask "is it holding the right object" from a wrist camera. | negative: identity over time is the wall, E64, E85–E87 |
| 13 | Shadow scoring of the teleop stream | Score every takeover in last month's sessions without acting; agreement with operators becomes one number before anything touches a robot. | idea (recipe in `docs/RECIPE.md`) |
| 14 | Every veto is a label | The confirm window's vetoes are the cheapest correction data a fleet can collect; feed them to the owned head. | idea |
| 15 | Conflict detector | Two facts disagree (a marking against a colour, a sticker against a scratch): ask, do not guess. | idea, partly measured: D4e |
| 16 | Trainability scorer | Score whether a demonstration is clean enough to learn from before it enters the training set. | measured on 13,451 real household demonstrations (Eidon): zero-shot from IMU facts, AUROC .78 vs a rule's .64 and a fitted logistic's .88; probability within .03 of the true valid rate; 0.11 s per recording (E97) |
| 17 | Grasp-manner head | Gentle or normal placement from what the part looks like, as a parallel yes/no question. | measured implicitly in every cell run |
| 18 | Criteria evolution from operator labels | Let operator corrections rewrite the option text and instructions instead of the weights. | idea (jev-align pattern) |
| 19 | The person in the room | For a robot that shares a space with people: stop, wait, turn away or ask, with a number the safety envelope can spend. | measured on MicroDuck: negative without representation work (E93b); with annotated options the judge handles 17/30 unwritten events against the rules' 1 (E94); an owned head matches the rules on the anticipated bank and is blind to unseen notes (E96); one correction round teaches the notes (reading, by ablation) and un-teaches moving, so the label form is the lever (E98–E100) |
| 20 | Frontier model as translator, calibrated model as judge | A frontier model names the world once (which object is held, what it looks like); the fast model judges every frame. | idea (Roboflow / Sucar pattern) |
| 21 | Verifier and reward model | Score an episode against a checklist of yes/no items, each with a calibrated probability, as the reward for training a policy. | measured on 350 of our own episodes: honest probabilities (ECE .08), perfect ranking on the hand-over-to-the-wrong-person item; a regex over the log matches it on literal items, so literal checks belong to code and inferential ones to the judge (E111) |
| 22 | Rules drafted from the judge's decisions | The judge's decisions on a new situation, filtered by the operator's vetoes and scoped to new states, compile into a tree a person reads and ships as a clause. | measured: E115, E115b (duck 30 of 30 unscoped, 20 scoped; humanoid 20 of 30 = the judge, at rule cost) |
| 23 | Picking station with a remote picker | A warehouse or store picker runs on a grasp-score threshold and a remote person for the rest; the threshold's meaning is the economics, the picker's clicks are the vetoes, and the exception log becomes a drafted rule. | measured at decision level (E117): the judge ships nothing wrong on unwritten lines where the rules ship all sixty, and fails the double pick confidently; see [docs/PICKING-BENCH.md](docs/PICKING-BENCH.md) |

Long form with what code owns, what the model decides and the evidence for each: [docs/USE-CASES.md](docs/USE-CASES.md).

## The recipe a team can follow

Log state, options and the probability vector for every decision. Convert numbers to categories before the model sees them. Extract a note's conditions once and bind in code. Ask narrow literal questions in one parallel call. Gate and confirm on the top-1 probability, never on an entropy score. Put safety rules in the governor. After a few thousand decisions, distil the vectors with plain soft cross-entropy into a small head and run it on the robot; keep one correction round. Details, schema and commands: [docs/RECIPE.md](docs/RECIPE.md).

## How to read the evidence

- `notebook/LAB-NOTEBOOK.md` — every pre-registration with its date, then its results and scoring; failed predictions kept.
- `notebook/CLAIMS.md` — the claims ledger, each with its boundary; corrections appended, never rewritten.
- `paper/appendix-method-errors.md` — the method errors we caught in our own work (52 so far), with fixes and the rules adopted.
- `results/` — every run's raw outputs; `figures/` — the figures; `paper/main.md` — the paper draft.
- One command regenerates the headline tables from the committed results:
```bash
PYTHONPATH=src python -m cell.report
```

## Reproduce

No-key runs (no API needed):
```bash
PYTHONPATH=src python -m sim.run_ablation --arms published_baseline heuristic climb_rule --seeds 0-9 --seconds 65 --fast --out results/sim/demo.jsonl
```
```bash
PYTHONPATH=src python -m cell.run --arms rules lexical oracle --seeds 0-9 --out results/cell/demo.jsonl
```
The duck bench, no key needed for the rule program, the oracle and the owned heads (`DUCK_REPR=R2` options, `DUCK_PROGRESS=1` for the progress-aware acceptable set, `DUCK_HEAD=<checkpoint>` for an owned head):
```bash
USE_TF=0 PYTHONPATH=src DUCK_REPR=R2 python src/duck/e93_run.py --arms rules oracle --seeds 0-9 --out results/duck/demo.jsonl
```
Calibrated arms read `TYPESAFE_API_KEY` from the environment (`jev-latest`; `CELL_JEV_MODEL=jev-preview` for the second checkpoint). Owned-head arms read `CELL_LAYA_CKPT`; see [models/README.md](models/README.md). The governor's set-down rule is `CELL_GOV_SETDOWN=1`.

| directory | what |
|---|---|
| `src/cell/` | the sorting cell, arms, harness, governor, owned-head training and evaluation, figures |
| `src/sim/` | the drone testbed (fork of RomanSlack/jev-drone, MIT) and the handoff head |
| `src/critic/`, `src/dispatch/`, `src/vocab/` | text probes with fair baselines; expected-cost dispatch; vocabulary discovery |
| `src/perception/` | the perception seam probes (SAM 3, relation model, segmentation ground truth) |
| `data/` | constructed suites, California DMV disengagement reports 2020–24, DROID instruction strings, the irreducible-judgment items |
| `docs/` | use cases, the recipe, the duck bench definition |
| `src/field/`, `results/field/`, `data/eidon/` | the Eidon probe: IMU facts, the two questions, the baselines, the answers (the 9 TB of video and 9.5 GB of IMU stay on Hugging Face; the metadata table and the computed facts are here) |
| `src/duck/`, `results/duck/` | the duck bench: MicroDuck in a room with a person; every iteration on the leaderboard |
| `src/humanoid/` | bench 3: the humanoid fetch room on the same harness (`DUCK_BODY=g1`) |
| `models/` | checkpoints and how to reproduce them |

## Why this kind of model, and not a frontier model in the seat

Not because a frontier vision-language model judges worse. The seat has four requirements and a frontier model in it fails three.

1. **Speed.** The seat decides every half second while the body moves. A calibrated decision model answers in a tenth of a second; a frontier model takes seconds. Three seconds of think time on a moving body doubled near-contacts and lost 11 of 29 unwritten situations with no gain in task time (E105); on a skill graph a decision node that waits paid the same latency in task time, 5.4 s per pickup with the calibrated judge against 8.8 s with a frontier model (Jacob's Graph-as-Policy test).
2. **The number.** Every operator-time saving here comes from a probability that means the same thing every time: propose and wait one second for a veto, gate only the unflagged surprises. This kind of model returns a probability per option as its native output, and it holds on the states its own actions create (D7, D8). A frontier model generates text; its confidence is a sentence. The nearest test we could afford, a dense open 27B behind the identical interface, kept the accuracy and drifted the number by .135 (D4, D7).
3. **Cost.** A fraction of a cent per decision against cents, at on the order of a hundred thousand decisions per robot per day.
4. **Ownership.** The judgment distils into a 421M model the fleet owns, retrains from its operators' corrections, and runs on the robot for free (E91c, E103). Nobody owns a frontier model.

Frontier models belong outside the loop, in three roles the map names: writing the rule program or the skill graph, translating the world into facts once, and teaching. **The honest gap:** a frontier model in the seat itself is unrun here; the direct comparison on judgment quality is a claim this work does not make, and it is first on the list below.

## What to test next, singly and together

Untested things are listed the way any scientific work lists them: what each would show, alone or in combination. Done since the first list: the open 27B on the fixed instrument (E104: 19 of 30 against the judge's 29, over-confident by .17 on its own states); the rules written a second time after seeing the unseen bank (E114: 29 = 29 on the duck, 30 against 20 on the humanoid, under fifteen minutes per body).

| test | alone, it would show | together with |
|---|---|---|
| A frontier model in the judge's seat, same harness | whether the accuracy gap to a calibrated model is real, at known cost and latency | the think-time coupling (E105): its quality at its own latency |
| A frontier model as the *teacher* of the owned copy | whether distillation from a text-generating model yields a calibrated copy at all | the correction loop: whose corrections repair whose blindness |
| A human-sized body (an open G1 walking policy runs headless here, 0.6–0.9 m/s, real turns) | the ladder at human distances and speeds; whether the mechanisms reproduce | a home room and a store aisle: the two companies' worlds |
| One operator, many robots | what the confirm window and the gate buy when attention is the scarce resource | the humanoid fleet: the number a fleet company pays for |
| Real takeover logs as the correction source | whether operators' takeovers teach what code's acceptable sets taught | shadow scoring of the teleop stream: one number before anything touches a robot |
| Cadence without staleness (decide every 1.5 s on fresh facts) | whether fewer decisions or staler ones produced E105's gain | the governor setting cadence from the scene |
| The doorway detector aligned with the "passed" fact (method error 36), every arm re-run | whether the object-in-door numbers were decision-timing luck | the rewritten rules as every new instrument's first test |
| A site twin from the robot's own sensors as the bench's world | the anticipated bank generated from a real floor plan | correction rounds and own-state calibration in the twin before the first real episode |
| The other twelve Eidon shards; sub-action labels | the annotator's accuracy, not only its triage | the trainability probe at fourteen times the size |
| The cross event as a governor rule | whether the one unsolved anticipated situation is code's, as the set-down rule was | every judge on the ladder, re-scored |
| An unseen bank designed by a second person, scored before its designer sees any arm | the time-to-rule claim without the author's own hindsight | the frozen rules, the judge and the corrected copy, both bodies |
| The picking station in physics (the cell's MuJoCo arm), and its rules rewritten with hindsight | whether the decision-level numbers survive a real grasp, and the time-to-rule on this bench | the drafted rules from the picker's vetoes (E115), the owned copy distilled from the judge's station decisions, a second designer's unwritten lines |
| The corrected copy on situations it was never corrected on | whether the operator's vetoes teach reading that transfers, or only the three situations they covered | a fourth unseen situation held out from every correction round |

## What is simulated, and what that means

"It is all simulated" is three different situations here, and they deserve three different answers.

**The decision-layer results do not depend on a simulator at all.** The judge reads facts in words and picks from options
code wrote. Whether those facts came from a physics engine or a real robot's perception stack has no bearing on whether its
probability matches its hit rate, whether correcting it on a fleet's takeovers erodes that probability off the corrected
distribution, or whether the operator's veto window keeps catching anything. Those are properties of the model and of the
loop, and a real fleet's takeover logs have exactly the same shape as ours. This is where most of the programme lives.

**The body results are done the way the field does body work.** Essentially every walking policy on every humanoid is
trained in simulation with domain randomisation and transferred, and the post-training here runs in MuJoCo Playground, on
Unitree's G1 model, starting from the policy that actually ships with it. That is the standard method, not a stand-in for
it, and the measured tolerance — mass, friction and actuator gains perturbed per episode, with the gains carrying almost all
of the brittleness — is a contribution to that practice rather than an apology for it. The field is also moving toward
post-training inside learned world models, which is more simulation, not less.

**Two gaps are real and we do not paper over them.** Contact-rich manipulation simulates badly, which is exactly why the
field does that work on real hardware; there is no contact bench here and the picking station is honest about being
decision-level. And our benches hand the decision layer its facts, so the seam from pixels to facts is measured once
(E86) and then bypassed. A bench whose facts come from a segmenter running on rendered frames would close the larger of the
two, and it is the next gap worth spending on.


## Boundaries

Everything positive about the decision loop is measured in simulation we built, with ground truth we defined. Real data appears three times: dispatch on fleet records (E53) and object identity on wrist-camera frames (E64) were negative; quality triage of real demonstrations (E97) was positive and activity recognition negative. The clone is about 200 MB because every decision record is included. The RLCD claim rests on two checkpoints of one vendor's family. Forty held-out seeds per loop; single-answer calibration cells of 122–545 decisions. A frontier model in the judge's seat is unrun; the harness runs any model behind the identical interface.

**How this could be unfair, and what we did about it.** (1) The rule programs are ours, written before each unseen bank and frozen while the judge's inputs improved across rounds; that asymmetry is the hypothesis (a judge uses a new fact without a rewrite), and a rule author given the same rounds would keep the anticipated bank and could not touch the unseen one without seeing it. (2) The unseen situations favour reading: two of the humanoid's three and one of the duck's three live in an operator's note; the counterweights are the reaching child (rules 10/10, judge 0/10), the crossing adult (rules win) and the cell's unflagged surprises with no note (E83). (3) The owned copy learns our own acceptable sets and is tested on fresh seeds of the same situations, so its parity with the teacher is within-situation; generalisation to situations it was never corrected on is untested. (4) The instruments changed between rounds after seeing results; every change was pre-registered before the next run and the rules and oracle were re-run on the same instrument each time, but it is bench iteration informed by the judge's failures. (5) The open 27B's probability came through a readout we built; the drift result is about an untrained readout, not the best an open model could do with training. (6) Ten episodes per situation: differences of one or two are noise, and the claims rest on the large effects. (7) Done on 2026-09-21 (E114): the rules written a second time by their author after seeing the unseen banks handle 29 of 30 on the duck (the judge's number) and 30 of 30 on the humanoid (the judge: 20), in under fifteen minutes per body; so every unseen-bank comparison here reads "before anyone wrote the rule", and the judge's value is time-to-rule plus a calibrated number, not accuracy after the fact. The banks' author wrote the fixes, so the minutes are a lower bound and the scores an upper bound on a stranger's; a second designer's bank is the open test.

MIT licence. Third-party: `third_party/jev-drone` (MIT), RelateAnything weights (fetched, not stored). Anurag Akkiraju, 2026.

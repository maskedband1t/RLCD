# Calibrated Decisions at the Human–Robot Boundary

Anurag Akkiraju · September 2026 · MIT

**RLCD use cases in robotics, measured.** A self-directed research programme (September 2026): more than a hundred pre-registered experiments in three simulated instruments and one real dataset, asking where calibrated decision models — RLCD-trained "System One" models, of which TypeSafe's Jev is the first — create value in a robot fleet with human oversight, and how the fleet's own decisions become judgment it owns. Every prediction was dated before its run; failed predictions and 36 method errors stay in the record next to the results.

**Three numbers.** On a second body, the RLCD judge handles 29 of 30 situations nobody wrote a rule for, where the rule program handles 1; once the program's author has seen the bank, the same program handles 29 (seven lines, fourteen minutes), so the judge's edge on unwritten situations is the time before a rule exists, not accuracy after. Driving its own states, its probability stays within .02 of its hit rate while a dense open 27B's runs .135 over, so a fixed handoff threshold means one thing for the judge and drifts for the open model. A 421M head the fleet owns, distilled from the judge's decisions and corrected only by the operator's vetoes, reaches the judge on both bodies (88.3 vs 87.9 % in the cell; 28 of 30 on the duck) while walking like the rule program where the rules were written (95 % = 95 %).

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
| **The humanoid fetch room** — a human-sized Unitree G1, a table, a doorway, two people, an object to hand over | Do the mechanisms hold at human scale, with arms, and with hand-over decisions among people? | Judge reads both operator notes 10 of 10 where the frozen rules handle 0 and 0 (rewritten with hindsight: 30 of 30 in nine minutes, E114); never hands to the wrong person; loses where the rules were written (33 vs 39); a veto window that keeps walking reaches the oracle's 27 of 30; the body's start-stop fragility is paid in falls. The owned copy transfers whole: 35 of 40 where the rules were written (its teacher: 33) at 80 ms, blind where they were not (0 of 30, 20 wrong hand-overs, 9 falls); the veto window removes every fall and hands it the reaching child 10 of 10 (E112); its correction round is running |
| **Eidon's 13,451 real recordings** | Can it triage real teleop data before labels exist? | AUROC .78 zero-shot from motion facts, a hand rule .64, a fitted logistic .88; calibrated at the real prevalence; activity recognition at chance |

## The picture

![The decision cycle: world, perception to facts, System One judgment, code governor, executor; System Two roles outside the cycle above; the owned data loop below](figures/fig0-decision-cycle.svg)

*A fleet runs on a cycle: cameras and state become facts, a System One judgment picks one action from options code wrote, a code governor owns safety and when to involve a person, an executor moves the body. Frontier models sit outside the cycle: they write the reflex, translate the world once, teach. Every decision is a typed record with a probability, so the fleet's decisions become training data for a head it owns. Each box carries what was measured against a dumb baseline.*

## See it move

![Humanoid, seed 42: Maya asked for the cup but is on a call. Left, the frozen rules hand it to her anyway. Middle, the rules rewritten with hindsight wait. Right, the RLCD judge waits at about a metre, stated confidence .31, and hands over when she looks up.](figures/demo-g1-seed42-phone-rules-vs-judge.gif)

*The humanoid fetch room, same seed, same body. Maya asked for the cup; an operator's note says she is on a call and must not be handed anything until she looks at the robot. Left, the frozen rules hand it over as soon as they are within reach: a wrong hand-over. Middle, the same program after its author read the situation waits. Right, the judge reads the note, waits with a stated confidence of .31, and hands over when she looks up (E110, E114).*

![Humanoid, seed 44: a child, Zoe, asked for the scissors. Left, the frozen rules hand them to her. Middle, the rewritten rules ask the operator once. Right, the RLCD judge asks the operator and never hands them over.](figures/demo-g1-seed44-scissors-rules-vs-judge.gif)

*Zoe, a child, asked for the scissors; the note says never to hand anything sharp to a child and to ask if unsure. Left, the frozen rules hand them over. Middle, the rewritten rules ask once (four operator seconds). Right, the judge asks three times (twelve operator seconds) and never hands them over. Both refusals count as handled; the judge's costs the operator more.*

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

0. [docs/WHY.md](docs/WHY.md): what this is and why, in plain words, one page.
1. **The ladder figure above**, then [docs/DUCK-BENCH.md](docs/DUCK-BENCH.md): what the bench holds fixed, what each version changed, and the ladder table with every number.
2. [notebook/CLAIMS.md](notebook/CLAIMS.md): the claims ledger with boundaries, corrections appended and never rewritten. Read 4.54 (the owned head reaches its teacher), 4.58 (the correction lever), 4.61 (the copy reads like its teacher, no API).
3. [docs/RECIPE.md](docs/RECIPE.md): what a team would do on Monday, with the schema and commands.
4. The clips under [See it move](#see-it-move): the owned copy before and after the operator's vetoes, and the sorting cell's set-down rule.
5. [notebook/LAB-NOTEBOOK.md](notebook/LAB-NOTEBOOK.md): 11,000 lines of dated pre-registrations, results and scoring, if you want to check any of it.

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
11. **On a human-sized humanoid, the judge reads the notes and the veto window does the rest.** Fetching an object and handing it to the person who asked, with a second person in the room: the judge handles the two situations that live in an operator's note (a person on a call who must not be handed anything until she looks; a child who asked for scissors) 10 of 10 each, where the frozen rule program handles 0 and 0 and hands the object to the wrong person twenty times; it never does. The same program rewritten by its author after reading the bank handles 30 of 30 in eight lines and nine minutes (E114): what the judge buys here is the day the note arrived, and the number the veto window spends. Where the rules were written they still win, 39 to 33. A one-second veto window that slows the walk instead of stopping it takes the combined arm to the oracle's score on the unwritten bank, 27 of 30, at 20–24 operator seconds per episode. The body paid for every instrument fault in falls: its walking policy cannot take a stop-start every second, so asks hold still, the operator's answer holds the wheel, and the window keeps walking. The owned copy, distilled from the judge's 4,992 decisions on this room, transfers the duck's result shape whole: 35 of 40 where the rules were written, above its teacher's 33, at 80 ms; blind where they were not (0 of 30, the cup handed to Maya mid-call and the scissors to the child, 20 wrong hand-overs) and nine falls from alternating stop and walk, which the veto window removes entirely while its 44 vetoes hand the copy the reaching child 10 of 10. Those vetoes are the correction round's labels (E113, running). — E108–E110, E112; [docs/FETCH-BENCH.md](docs/FETCH-BENCH.md); [figure 12](figures/fig12-humanoid-ladder.png).

   ![The humanoid fetch room: the unwritten bank by arm, and the anticipated bank with falls](figures/fig12-humanoid-ladder.png)

12. **The judge's decisions compile into rules a person can read, and the vetoes decide whether they are good.** Take the judge's recorded decisions on a new situation, keep the ones the operator would not have vetoed, fit a small decision tree over the same facts the rule program reads, and put it in front of the frozen rules. On the duck the draft reads "if the note says follow, follow the person; if standing and the person has crutches, wait; at the goal, done" and handles 30 of 30 fresh unseen situations, one more than the judge that produced it; scoped by a novelty gate to states the old rules never saw, it leaves the anticipated bank exactly where the frozen rules had it (36 of 40) and loses the doorway situation to the same instrument flaw that caught the hindsight programmer. On the humanoid only a third of the judge's decisions survive the veto and the filtered draft is useless; a finer tree from all decisions handles the phone call and the scissors 10 of 10 each, the judge's own 20 of 30, with no falls and four operator seconds, and inherits the judge's blind spot on the reaching child. So the loop a fleet can run is: judge covers day one, vetoes filter, the tree is the draft, a person reads where it is silent. Pre-registered predictions: one of six, then three of four; the misses are in the notebook. — E115, E115b; [docs/DUCK-BENCH.md](docs/DUCK-BENCH.md), [docs/FETCH-BENCH.md](docs/FETCH-BENCH.md); the drafts are in `results/duck/mined_*.txt`.



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
| 23 | Picking station with a remote picker | A warehouse or store picker runs on a grasp-score threshold and a remote person for the rest; the threshold's meaning is the economics, the picker's clicks are the vetoes, and the exception log becomes a drafted rule. | mapped onto the sorting cell's numbers (E71, E83, E88, E115); the picking bench is listed under what to test next |

Long form with what code owns, what the model decides and the evidence for each: [docs/USE-CASES.md](docs/USE-CASES.md).

## The recipe a team can follow

Log state, options and the probability vector for every decision. Convert numbers to categories before the model sees them. Extract a note's conditions once and bind in code. Ask narrow literal questions in one parallel call. Gate and confirm on the top-1 probability, never on an entropy score. Put safety rules in the governor. After a few thousand decisions, distil the vectors with plain soft cross-entropy into a small head and run it on the robot; keep one correction round. Details, schema and commands: [docs/RECIPE.md](docs/RECIPE.md).

## How to read the evidence

- `notebook/LAB-NOTEBOOK.md` — every pre-registration with its date, then its results and scoring; failed predictions kept.
- `notebook/CLAIMS.md` — the claims ledger, each with its boundary; corrections appended, never rewritten.
- `paper/appendix-method-errors.md` — the method errors we caught in our own work (32 so far), with fixes and the rules adopted.
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
| A picking station on the cell harness: a tote of items with attributes, a customer tote or a return bin, a remote picker who can be asked | picks and escalations per hour, wrong picks, operator seconds, and how far the escalation rate moves when the item mix changes: the numbers a picking company asks for | the drafted rules from the picker's vetoes (E115), the confidence gate (E83), the owned copy |
| The corrected copy on situations it was never corrected on | whether the operator's vetoes teach reading that transfers, or only the three situations they covered | a fourth unseen situation held out from every correction round |

## Boundaries

Everything positive about the decision loop is measured in simulation we built, with ground truth we defined. Real data appears three times: dispatch on fleet records (E53) and object identity on wrist-camera frames (E64) were negative; quality triage of real demonstrations (E97) was positive and activity recognition negative. The clone is about 200 MB because every decision record is included. The RLCD claim rests on two checkpoints of one vendor's family. Forty held-out seeds per loop; single-answer calibration cells of 122–545 decisions. A frontier model in the judge's seat is unrun; the harness runs any model behind the identical interface.

**How this could be unfair, and what we did about it.** (1) The rule programs are ours, written before each unseen bank and frozen while the judge's inputs improved across rounds; that asymmetry is the hypothesis (a judge uses a new fact without a rewrite), and a rule author given the same rounds would keep the anticipated bank and could not touch the unseen one without seeing it. (2) The unseen situations favour reading: two of the humanoid's three and one of the duck's three live in an operator's note; the counterweights are the reaching child (rules 10/10, judge 0/10), the crossing adult (rules win) and the cell's unflagged surprises with no note (E83). (3) The owned copy learns our own acceptable sets and is tested on fresh seeds of the same situations, so its parity with the teacher is within-situation; generalisation to situations it was never corrected on is untested. (4) The instruments changed between rounds after seeing results; every change was pre-registered before the next run and the rules and oracle were re-run on the same instrument each time, but it is bench iteration informed by the judge's failures. (5) The open 27B's probability came through a readout we built; the drift result is about an untrained readout, not the best an open model could do with training. (6) Ten episodes per situation: differences of one or two are noise, and the claims rest on the large effects. (7) Done on 2026-09-21 (E114): the rules written a second time by their author after seeing the unseen banks handle 29 of 30 on the duck (the judge's number) and 30 of 30 on the humanoid (the judge: 20), in under fifteen minutes per body; so every unseen-bank comparison here reads "before anyone wrote the rule", and the judge's value is time-to-rule plus a calibrated number, not accuracy after the fact. The banks' author wrote the fixes, so the minutes are a lower bound and the scores an upper bound on a stranger's; a second designer's bank is the open test.

MIT licence. Third-party: `third_party/jev-drone` (MIT), RelateAnything weights (fetched, not stored). Anurag Akkiraju, 2026.

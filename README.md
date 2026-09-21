# Calibrated Decisions at the Human–Robot Boundary

**RLCD use cases in robotics, measured.** A self-directed research programme (September 2026): 92 pre-registered experiments in two simulated instruments, asking where calibrated decision models — RLCD-trained "System One" models, of which TypeSafe's Jev is the first — create value in a robot fleet with human oversight, and how the fleet's own decisions become judgment it owns. Every prediction was dated before its run; failed predictions and 27 method errors stay in the record next to the results.

![Seed 40: a hand enters the corridor while a heavy fragile part is carried. Left, the frozen rules pause and the part slips. Right, the owned head with the governor's set-down rule.](figures/demo-seed40-rules-vs-owned-head.gif)

*The sorting cell: six parts, colour and inspection trays, a person's hand that enters the corridor, blocked trays, slipping parts, unknown objects, and one unscripted event per episode. Fifteen arms share one executor, perception stack and option enumerator.*

## The core results

Numbers are on held-out seeds with Wilson 95 % intervals; paired differences are seed-matched bootstraps. Evidence pointers name the experiment in the [lab notebook](notebook/LAB-NOTEBOOK.md) and the [claims ledger](notebook/CLAIMS.md).

1. **A calibrated model's probability keeps its meaning on states its own actions created; a strong open model's does not.** On recorded decisions a dense open 27B matches Jev on choices (84.8 vs 81.5 % acceptable) and on calibration. Driving its own states, the 27B's top-1 probability runs .135 above its hit rate while two RLCD checkpoints stay within .02, and it loses 9 points ungated. A fixed handoff threshold only means one thing for the model whose number holds. — D4, D4d, D7, D8; [Figure 8](figures/fig8-reliability.png).
2. **A one-second confirm window buys the same safety for two thirds of the operator time.** Replacing the 4-second ask with a proposal the operator may veto gives the same violations at 63–66 % of the operator time; 27 % of windows vetoed for the calibrated model, 38 % for the open one. — E88, D4d.
3. **When the surprise is in the facts and nobody wrote a note, the confidence gate is the only lever.** Rules handle 12.5 % of unflagged surprises, the calibrated judge 50 %, gated 75 %; the gate recovers the open model's misses because its ranking survives even where its number drifts. — E83, D4e.
4. **The fleet can own the judgment.** A 421M open encoder, distilled by plain soft cross-entropy from 6,489 of the teacher's typed decisions, drives held-out seeds at 88.3 % against the cloud teacher's 87.9 % (paired +0.4 [−0.8, +1.7]) with the teacher's exact event profile, at 90 ms on-device. Store the probability vector: a head trained on the chosen action alone becomes over-confident and blind in ranking. The RLCD training recipe is not needed to inherit the judgment; plain distillation beats it by 4.6 points — and the calibration comes with it: driving its own states the owned head reports over −.007 and ECE .054 against the teacher's +.014 / .083. — E90, E91, E91c, D7b; [Figure 9](figures/fig9-ladders.png), [Figure 8](figures/fig8-reliability.png).
5. **Code owns safety.** The one event every judge failed — a hand entering while a heavy fragile part is carried — was a rule code already had the facts for. Set the part down before pausing: fires on exactly those episodes for every arm, broken parts to zero, +2.1 to +4.2 points; with it the owned head and the teacher both sit at 90.4 %. — E76, E92.
6. **Reading is the value, and format decides whether a fact is seen.** Feeding the model categories instead of numbers is worth +47 points; extracting a note's conditions once and binding in code puts the judge at the perception-limited ceiling, 89.3 of a possible 89.9 % on 200 seeds, with zero broken parts. — E70, E79, E82.

7. **A second body, honestly.** The same judge dropped onto Pollen's MicroDuck biped in a room with a person, with facts, options and governor written in one night, reaches the goal 75 % of the time against 98 % for a rule program written for the anticipated cases, and comes within touching distance of a standing person 19 times in 40 episodes against 3; the handoff threshold and the calibration level tuned in the cell did not carry over. One round of representation work (options annotated with code's predicted effect on the distance to the person) put the judge's confidence on its own states within .002 of its hit rate, and on a bank of events nobody wrote a rule for it handled 17 of 30 against the rules' 1 and an oracle's 19, reading a note about crutches in 9 of 10 episodes. An owned 421M head distilled from 4,027 of those decisions then matched the rule program on the anticipated bank (95 %) and beat its own teacher there, with no API call in the loop; on the notes it never saw it was blind (0/10 and 0/10) and confidently wrong (right 8 % of the time at a stated .70): distillation transfers behaviour, not reading. The confirm window bought back a third of that (16/30) at 15 operator seconds per episode, and every veto is a labelled state for the next round. One correction round on those states, labelled by code's acceptable sets, taught the copy both notes on fresh seeds (right of way 0 → 10/10, above an oracle's 8) and un-taught it to move (anticipated-bank goal 95 → 72 %, six falls from start–stop chattering): the label form is the lever. With the body's skills fixed (its shipped policy cannot turn in place, so three skills had done nothing) the corrected copy handled 22 of 30 unseen events against its uncorrected twin's 10, and hiding the notes dropped following from 10/10 to 0/10: the round taught reading, not caution alone. — E93–E100; `docs/DUCK-BENCH.md`, `results/duck/LEADERBOARD.md`; [the ladder](figures/fig10-duck-ladder.png); `src/duck/`; [clip](figures/demo-duck-seed1-approach.gif).

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
| 8 | Annotator of teleop hours | Label sub-actions and boundaries on recorded episodes; use it for boundaries, a rule for the label. | measured: E89, E89c |
| 9 | Code-owned safety rules found by the loop | The judge's repeated failure names the rule; the governor takes it; every judge benefits. | measured: E92 |
| 10 | Dispatch by expected cost | Decide which robot a person should attend to next from calibrated failure probabilities. | negative on real fleet data: E53 |
| 11 | Critic of planner steps | Veto a language planner's next step. | negative with a 7B planner: E65–E67 |
| 12 | Perception seam | Ask "is it holding the right object" from a wrist camera. | negative: identity over time is the wall, E64, E85–E87 |
| 13 | Shadow scoring of the teleop stream | Score every takeover in last month's sessions without acting; agreement with operators becomes one number before anything touches a robot. | idea (recipe in `docs/RECIPE.md`) |
| 14 | Every veto is a label | The confirm window's vetoes are the cheapest correction data a fleet can collect; feed them to the owned head. | idea |
| 15 | Conflict detector | Two facts disagree (a marking against a colour, a sticker against a scratch): ask, do not guess. | idea, partly measured: D4e |
| 16 | Trainability scorer | Score whether a demonstration is clean enough to learn from before it enters the training set. | idea, weak signal: E89 |
| 17 | Grasp-manner head | Gentle or normal placement from what the part looks like, as a parallel yes/no question. | measured implicitly in every cell run |
| 18 | Criteria evolution from operator labels | Let operator corrections rewrite the option text and instructions instead of the weights. | idea (jev-align pattern) |
| 19 | The person in the room | For a robot that shares a space with people: stop, wait, turn away or ask, with a number the safety envelope can spend. | measured on MicroDuck: negative without representation work (E93b); with annotated options the judge handles 17/30 unwritten events against the rules' 1 (E94); an owned head matches the rules on the anticipated bank and is blind to unseen notes (E96); one correction round teaches the notes (reading, by ablation) and un-teaches moving, so the label form is the lever (E98–E100) |
| 20 | Frontier model as translator, calibrated model as judge | A frontier model names the world once (which object is held, what it looks like); the fast model judges every frame. | idea (Roboflow / Sucar pattern) |

Long form with what code owns, what the model decides and the evidence for each: [docs/USE-CASES.md](docs/USE-CASES.md).

## The recipe a team can follow

Log state, options and the probability vector for every decision. Convert numbers to categories before the model sees them. Extract a note's conditions once and bind in code. Ask narrow literal questions in one parallel call. Gate and confirm on the top-1 probability, never on an entropy score. Put safety rules in the governor. After a few thousand decisions, distil the vectors with plain soft cross-entropy into a small head and run it on the robot; keep one correction round. Details, schema and commands: [docs/RECIPE.md](docs/RECIPE.md).

## How to read the evidence

- `notebook/LAB-NOTEBOOK.md` — every pre-registration with its date, then its results and scoring; failed predictions kept.
- `notebook/CLAIMS.md` — the claims ledger, each with its boundary; corrections appended, never rewritten.
- `paper/appendix-method-errors.md` — 27 errors we caught in our own work, with fixes and the rules adopted.
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
Calibrated arms read `TYPESAFE_API_KEY` from the environment (`jev-latest`; `CELL_JEV_MODEL=jev-preview` for the second checkpoint). Owned-head arms read `CELL_LAYA_CKPT`; see [models/README.md](models/README.md). The governor's set-down rule is `CELL_GOV_SETDOWN=1`.

| directory | what |
|---|---|
| `src/cell/` | the sorting cell, arms, harness, governor, owned-head training and evaluation, figures |
| `src/sim/` | the drone testbed (fork of RomanSlack/jev-drone, MIT) and the handoff head |
| `src/critic/`, `src/dispatch/`, `src/vocab/` | text probes with fair baselines; expected-cost dispatch; vocabulary discovery |
| `src/perception/` | the perception seam probes (SAM 3, relation model, segmentation ground truth) |
| `data/` | constructed suites, California DMV disengagement reports 2020–24, DROID instruction strings, the irreducible-judgment items |
| `docs/` | use cases, the recipe, the duck bench definition |
| `src/duck/`, `results/duck/` | the duck bench: MicroDuck in a room with a person; every iteration on the leaderboard |
| `models/` | checkpoints and how to reproduce them |

## Boundaries

Everything positive here is measured in simulation we built, with ground truth we defined. The only real-data results (E53, E64) are negative. The RLCD claim rests on two checkpoints of one vendor's family. Forty held-out seeds per loop; single-answer calibration cells of 122–545 decisions. A frontier model in the judge's seat is unrun; the harness runs any model behind the identical interface.

MIT licence. Third-party: `third_party/jev-drone` (MIT), RelateAnything weights (fetched, not stored). the author Akkiraju, 2026.

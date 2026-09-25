# Appendix A — Method errors logged during this work

Each was logged when found, with its fix, in the lab notebook; numbers are in order of discovery. Errors 1–10 belong to the world-model line that preceded this paper's experiments and are kept because the protocol is the same; 15–18 concern results that had already been reported in earlier drafts and were corrected in the record.

1. I conflated two different "confidence" questions (logged as a method correction, before numbering)
2. A naming bug that would have failed silently at the end (logged as a method note)
3. The third instance of one bug, which makes it a pattern (logged as a method note)
4. The index that addressed the latents was overwritten
5. The rollout harness fed the model actions it was never trained on
6. The headline comparison was between two different rulers
7. I mis-set the instrument, and the first scores were junk
8. The smoke test caught two flaws that would have faked a null
9. E36 probed at fractions of the episode, which leaks the answer
10. I shipped a signal without checking it discriminated
11. one phrasing per category (tiers 5–6)
12. "obvious in pixels" (E46) was asserted, not looked at
13. generalised from 13 hand-checked questions
14. the rule judge accepted diagnostics that contain an action word
15. the falsifier's baseline could not fire
16. a judge aligned to the model under test
17. mechanism inferred from an aggregate
18. A baseline depressed by my own prompt format (string scoring lost the mass on letter-prefixed continuations); caught by a re-check declared before the number was trusted
19. An ablation keyed on a field some records lacked. The recall-ablation student excluded training records by their `seed` tag; the 1,351 E71 records were written before tagging existed and carry none, so every E71 recall decision stayed in the "ablated" set (710 recall records existed; 479 were removed). The ablated student's 5/7 on recall items was leakage, not generalisation. Found by asking why an ablation had no effect; fixed by matching records on the parts signature; the true ablation re-run with the same pre-registered prediction.
20. My combination code reproduced the rule policy's failure mode inside the judgment arm (E78, first run). Code picked the lowest-numbered part; when that part's tray was blocked the combination returned `wait` without a cap, so the robot never reached the other parts and parts-correct fell to 78 %. Found by reading the decision logs (decisions per episode had doubled), not from the outcome table; fixed with the same wait cap and skip rule the frozen rules already had; re-run as E78b (90.0 %).
21. An extraction question whose wording let the model attach the destination's colour to the part's condition (E79, first run). "Which colour do the notes single out?" returned violet for "put the small one in the violet tray", so the code-side ambiguity check never fired (0/6). Stating the exact condition — the part's own colour, not the tray — gave 6/6 (E79b). The vendor's documented literal-reading remedy, needed on my own question.

Instrument-development notes that did not reach the outcome table (2026-09-18, sorting cell): tray contents classified by height, so piled parts read as "rim" and were re-picked in a loop; airborne parts pickable; contact charged to a paused robot; an inconsistent ground truth for blocked-forever trays. Two full 40-seed runs were discarded before analysis when these surfaced in the logs.

**22. Replay-only mode mistaken for hybrid replay (E88, first run, 2026-09-19).** The first E88 runs were
launched with `--replay` (E83/E71 records) expecting recorded answers where states repeated and live calls
where they diverged. The policy's contract was replay *only*: a state absent from the records returned
`ask_operator` tagged `source=replay_miss`, and the oracle operator then acted. Every arm therefore showed
`jev_calls = 0`, the confirm arms made exactly one confirm per episode before diverging, and the "fewer
violations, more operator time" pattern was the operator doing the work. Caught in evaluation by the zero call
counts and the 250 : 40 ask : confirm ratio. Fix: an explicit `--replay-live` hybrid mode, replay-miss and
replay-hit counters in every episode summary and in the run log, and the invalid results kept on disk under
`*_invalid_replayonly` for the record. Lesson for the method: any arm summary with zero model calls is a
failed run, not a result; the evaluation now prints the call count beside every arm.

**23. The calibration target event, and a mis-carried number (D4 → D7, 2026-09-19/20).** (a) Every decision-level
calibration figure scored the top-1 confidence against "the choice is in the acceptable set", with acceptable sets
averaging three actions (a third are singletons). A confidence is a claim about one option; a label that accepts
several makes every model look under-confident in proportion to the set size, and unequally — a model that spreads
mass over equivalent options looks worse. D7 reports the singleton subset (one acceptable action) as the primary
measure and the strict measure alongside. (b) The D4 and E90 pre-registrations and claim 4.46 quoted Jev's
AUROC(confidence → acceptable) as .81 on the compared decisions. No such number exists for those decisions: P71.7
recorded .618 on the E71 decisions, and the .81 traces to a subset figure (.809, "while holding", n 165, "not
wrong" label). Recomputed on D4's decisions Jev is .658 strict / .816 singleton against the 27B's .676 / .876. The
"calibration gap on records" is withdrawn; the corrected finding — calibration under closed-loop shift — is claim
4.49. Rule adopted: every comparative number in a pre-registration is computed on the compared set by the same
script, and the singleton event is the default target for calibration.

**24. A chain that could not fail loudly, and an interpreter removed from under it (E91, 2026-09-20).** The
overnight E91 chain printed its stage markers unconditionally, so when the project's virtual environment lost its
interpreter mid-run (Homebrew's python@3.13 was uninstalled by an operation outside the session; only python@3.14
remained), both trainings had completed but every evaluation and closed-loop step failed in under a second and
the chain still printed `E91_EVALS`, `E91_LOOP_*` and `E91_ALL_DONE`. Caught by reading the log rather than the
markers. Fix: python@3.13 reinstalled (the venv resolves through `/opt/homebrew/opt/python@3.13`, so its packages
were intact); the re-run script checks each step's exit status under `pipefail` and prints `E91T_FAILED` and
stops on the first failure. Rule adopted: a marker means a step *succeeded*, never that it was *attempted*; every
chain checks its interpreter before starting.

**25. Two residuals called one (D4e reading, 2026-09-20).** The D4e write-up and claim 4.50 called the unflagged
`qa_sticker` failure "the same residual as the precedence note in E90/E90b". They are different mechanisms. The
notes-bank `precedence` event is not a note at all: a hand enters the corridor while the robot carries a heavy
fragile part, and the conflict is between the literal safety instruction (pause) and a physical consequence (the
part slips and breaks); E76 showed the remedy is a parallel literal question combined in code, and the teacher used
for the owned head's records (jev3) lacks it, so teacher and heads all score 0/7 by inheritance. The `qa_sticker`
case is a precedence between two visual cues (a passed sticker outranks a cosmetic mark) with no time pressure.
Caught while designing E92 from the event's code. Corrected in the notebook and claim 4.50; E92 is redesigned
around the actual mechanism.

**26. A prediction on an arm that cannot respond (E91b, P91b.2, 2026-09-20).** The refit heads' closed loops were
predicted to pause less. The `laya_v2` arm is ungated: it acts on the argmax, and a scalar temperature cannot move an
argmax, so the refit loops reproduced the unrefit loops to the decision (84.2 = 84.2, 88.3 = 88.3). The prediction was
unfalsifiable as run — the refit's effect exists only where confidence is spent (gate, confirm, calibration tables).
Two loops of compute wasted; caught on reading the identical tables. Rule: before predicting a behavioural change,
name the mechanism by which the changed quantity reaches an action.

**27. Three "confidences" compared as one (D7, E91, E91b, E91c; found 2026-09-20 07:20).** The calibration analysis
scored each model's *reported* confidence field against its hit rate. Those fields are different quantities: the
open models' field is the top-1 probability; Jev's API field sits ~.03 below its top-1 probability; Laya's field
is a normalised-entropy score, 1 − H(p)/log k, which is not a probability and runs ~.15 below the top-1 probability
for these option counts. Every statement that the owned heads were "under-confident by .13–.20" measured that score,
not their probabilities. Found by the budgeted look at why the head seemed calibrated on one record set and not
another: it was the same head and the same probabilities, read through two fields. Fix: calibration is now measured
on the top-1 probability for every model that returns a distribution (`d7_calibration.py`), the affected readings are
corrected in place with dated notes, and the E91b refit — which fitted the probability, already calibrated — is
re-read as unnecessary. Rule: name the quantity a "confidence" is before comparing two of them, and gate on a
probability.

**28. Two instrument faults that made a new body look like a model failure (E93, 2026-09-20).** (a) *A scripted deadlock.*
The scripted person paused whenever the robot came within 0.45 m, and the acceptable set said stop or wait whenever a person
was within 0.5 m, so any cautious policy and the person waited for each other until the clock ran out. The oracle itself sat
at 0.45 m for 80 s in seven episodes, which is where its 33/40 came from; the rule program escaped only because its author's
six-second timeout walks through a standing person. (b) *Misattributed violations.* A child-zone entry was counted whenever
the distance fell below a metre, including when the child walked up to a robot that was standing still exactly as the note
asked. Fixed for E93b: the person pauses only for a *moving* robot, and a zone entry counts only when the robot is moving.
**A bench that charges an arm for standing still will always prefer the arm that does not stop.**

**29. A skill that promised motion and delivered six millimetres (E94, 2026-09-21).** (a) `step_aside` commanded the walking
policy's lateral velocity, which moves that body 6 mm in four seconds — measured only after the run. Both the oracle and the
judge chose it near a paused person, because it was acceptable and its option text promised distance, and the person stayed
paused because the robot counted as "moving": error 28's deadlock in a new form, now for the oracle too. (b) The follow
target sat behind the doorway posts, wedging the oracle in five of ten follow episodes. (c) The cut-off detector fired on
acceptable decisions. Fixed for R2: a real detour verified to move the body *before* the run, the person pauses at most two
seconds, the follow target moved in front of the door line, and the detector made strictly narrower than the rule.
**Every option's text is a promise about the world; measure that the skill keeps it before an arm is scored on choosing it.**

**30. A dead judge that kept scoring (E95, 2026-09-21).** The TypeSafe account ran out of API credits during the R2 run.
The duck harness mapped every failed call to `ask_operator` with a `source: error` tag and carried on; the two judge
arms completed all 140 episodes asking nineteen times per episode, and the scoring script tabulated them as results
(15 % goal, 77 operator seconds). Caught because the confirm arm's numbers were identical to the ungated arm's and no
judge record carried a probability. Fix: API errors are counted per episode and three in a row abort the arm; the
dead-judge episodes are quarantined in `e95_jev_invalid_apicredits.jsonl`. Rule: an arm that cannot reach its model
has no result, and a harness must refuse to produce one.

**31. The teacher's unseen records admitted into a correction round (E98, 2026-09-21).** A `--seeds 0-69` filter let the
judge's unseen-bank decisions into the copy's training set; the run was killed at minute three and relaunched with a separate
`--extra` path for corrections. Rule: the teacher's data for the copy is the anticipated bank only; the unseen bank is for testing.

**32. Turn-in-place was a no-op on the shipped walking policy (bench 2 R5, E99, 2026-09-21).** The duck's policy turns two
degrees a second in place, so turn-away, follow and step-aside did nothing for four rounds, and the scripted person walked
through the robot. Fix: turns became arcs at slow walk; the person detours. Rule: measure every skill's effect on the body
before any arm is scored on it.

**33. A circular split (E107, 2026-09-21).** One prediction split the field logs by the governor's own confidence threshold,
the quantity under test. Reported as circular, with a correction paragraph. Rule: a split variable must never be the thing measured.

**34. A stop-start every second topples the humanoid (bench 3, E108–E109, 2026-09-21).** The G1's walking policy cannot
take a halt each cycle; asks and stops became falls. Fix: per-skill stands (ask at zero command, stop and wait at the
creep-cancelling reverse, confirm as a slow walk) and the operator's answer holding the wheel for two seconds. Rule: a body's
fragility belongs in the instrument, not in the judge's score.

**35. A checklist item that mixed two questions (E111, 2026-09-21).** Item one's truth conflated two conditions; the literal
truth was reported. Rule: one item, one condition.

**36. The doorway fact fires inside the kick zone (bench 2, found by E114, 2026-09-22).** "Passed" reads at ten centimetres
past the door line; the kick detector counts a fast step to fifteen. Every arm ran under it; the judge's and the oracle's
object-in-door scores were partly decision-timing luck; the deterministic rewritten rule exposed it. Fix planned as R8. Rule:
run every new instrument against the rewritten rules first.

**37. Placing while a hand is in the source tote counted as unacceptable (bench 4, E117, 2026-09-22).** The set forbade a
placement that touches nothing. Fix: R1; no outcome changed. Rule: acceptable sets describe contact, not proximity.

**38. The drafted-rule arms had no station variant (E122, 2026-09-22).** They fell through to the duck's program and crashed
on a missing fact before a line ran. Fix: a station variant. Rule: every arm is body-aware or refuses to run.

**39. The drafting tool never saw a body's facts (E122, 2026-09-22).** Its features were six note keywords and the duck's
fact keys; on the station the novelty gate found nothing new on the leak and recall lines and the frozen rules shipped them
(20 of 60). Fix: every fact dict flattened, notes as a bag of words (60 of 60). Rule: a compiler must be shown every fact the
judge saw.

**40. Single-option decisions in the copy's training set (bench 4, E120, 2026-09-22).** A third of the station's teacher
records were "done"-only states, which the trainer cannot index and which carry nothing to learn. Fix: the trainer drops
them and the copy answers a single-option state without the head. Rule: a training record needs at least two options.

**41. An escape action without a progress bound (bench 3, E124, 2026-09-22).** The child-aware step-around removed every
zone entry and produced a livelock: the judge circled the reaching child for the whole clock, 0 of 10 delivered, because the
acceptable set permitted the escape action forever. Fix (R3b): three step-arounds in a row withdraw the option and count as a
set entry. Rule: an acceptable set that permits an escape action needs a progress bound, or it is not an instrument for a
situation that requires delivery.

**42. A handled criterion that does not require the task to end (bench 3, bank v2, E126, 2026-09-22).** The pre-registered
criterion for the requester leaving counted a correct put-down as handled; the judge put the cup down and then walked for
the rest of the clock, never saying done, ten times out of ten, and scored 10 of 10. The scoring stands as registered;
"finished" is reported beside "handled" from then on, and the wording of the done option, which names delivery and refusal
but not a put-down, is tested as an instrument change (E129) rather than patched quietly. Rule: a handled criterion states
how the episode ends.

**43. A departing requester who never departs (bench 3, bank v2, E126/E129, 2026-09-22).** The "requester leaves" situation
walked Maya to the far corner of the room and stopped her there, so after the correct put-down the facts said in the room,
standing still, and the task line still said hand it to Maya; the judge rated done at zero and kept walking, and a wording
test of the done option (E129) changed nothing. The judge was reading the facts; the bench had ended the task on a story its
facts did not tell. Fix (bank v2.1): she walks out through the doorway and the facts say she is gone. Rule: a situation's
facts must tell the story its note and its acceptable set assume.

**44. Replication before the split (bench 4, E133, 2026-09-23).** Weighting the correction records by writing each four
times, then splitting train and validation at random, put identical records on both sides; validation agreement rose from
89.8 to 96.9 % while the copy's behaviour on fresh lines did not change. The fresh-line tests were unaffected. Fix: the
trainer drops from validation any item whose rendered text is in the training set. Rule: replicate after the split, or
weight the loss. *Amendment (E134):* dropping leaked items after the split left 19 of 532 validation items; the trainer now splits on
unique texts before anything is replicated.

**45. A fact key rendered only for the new bank's events (bench 3, bank v2, E136, 2026-09-23).** The object-condition fact
was rendered only on bank v2's episodes, so its resting value "intact" marked every v2 episode as new to a novelty gate from
the first decision, the second asker included, before anything had happened; the gate's fact-level test was confounded.
In a fleet a new field appears on every episode once deployed. Fix for the test: the field's resting value counts as
known, so the gate can fire only on a value or a person state the copy never saw. Rule: a new fact key must not be a proxy
for the bank.

**46. The model reloaded once per episode (tooling, E138/E139, 2026-09-24).** The harness constructs the arm at the start
of every episode, and the arm's constructor loaded its model: the 16 GB encoder behind the local CLM client and the 421M
owned head, once per episode, so a station line set whose model time summed to 10–20 minutes took 60–227 minutes of wall
clock, and the "option embeddings cached once" property was lost at every episode boundary. Decisions were unaffected (the
models are deterministic given the text). Fix: the heavy object is a process-level singleton keyed by its checkpoint; the arm
wrapper, with its per-episode counters, is still built per episode. Rule: build the model once, the arm per episode; record
wall clock beside model latency so a fivefold gap is seen the day it appears.

**47. Contracts satisfied by the body's fault (bench 3, E143, 2026-09-24).** The shipped walking policy creeps forward at
0.13 m/s on a zero command. Three of the fetch room's contracts were met by that creep and not by code: the judge chose the
pick-up from two to three metres away, out of reach, and the failed attempt's stand let the creep carry the robot in, so the
same premature choice succeeded on the next try; the judge's chosen waiting distance sat
outside the requester's 2.5 m noticing radius and the creep carried it in; the departure trigger (within 3 m while holding)
followed from the first. A post-trained body that truly stands failed the pick-up on 602 of 646 attempts and the phone
situation 0 of 10, with nothing else wrong. Fix (R5): the pick-up skill responsible for its own approach when the table is in the room, so a
premature pick-up walks in instead of repeating; the waiting distance left as a measurement of the judge's. Rule: a skill's success conditions are met by
the skill's code, never by a body's fault, and a bench states which of its results the fault carried.

**48. A leak the robot could not see (bench 3, bank v2, E147, 2026-09-24).** The cup's leak began three to six seconds
after the pick-up and the hand-over was scored on the state at the end of its two-second skill, so a body that reached the
requester ten seconds after the pick-up handed over a cup that was intact at the decision and leaking at the scoring: seven
of ten, every one decided on "intact". Earlier results on this situation depended on the body arriving after the leak. Fix
(R6): the onset triggered by the approach, half a second to a second after the robot comes within three metres holding the
cup, so it is visible before the hand-over range on any body; the hand-over scored on the state at the decision. Rule: a
decision is scored on what the robot saw when it decided.

**49. Events on the clock (bench 3, E147, 2026-09-24).** The crossing person started at a clock time, the cart cleared the
door at a clock time, and the child reached at a clock time, so a change in the body's speed moved the crossing into the
robot's path (closest approach three centimetres, two falls) and the door and the child into the bounded-edit body's way.
Maya's departure and her looking up were already triggered by the robot's state; the rest were not. Fix (R6): every
scripted event triggered by the robot's progress. Rule: a bench for a decision layer triggers its events on the robot's
state, never on the clock, or the body's speed becomes a hidden factor in every result.

**50. A skill that moved without saying so (bench 3, E148, 2026-09-24).** The pick-up fix (R5) made a premature pick-up walk
toward the table, but the option the judge read still said "only works within reach", and the approach walked whether or
not a person was crossing: in the shipped body's crossing episodes the judge chose stop, then step around, then pick up as
the person came within two steps, and the pick-up walked into her (four falls in ten). Fix (R5b): the approach never moves
with a person within the near zone, and the option text says the skill walks up first. Rule: a skill's motion is part of
its description, and any motion the governor adds obeys the same person rule the bench scores.

**51. An option's text changed between runs meant to compare bodies (bench 3, E149, 2026-09-24).** Told that the pick-up
would walk up to the table first, the judge chose it from across the room twice as often (248 against 119 premature choices
on the written bank), and with the approach guarded near people it stood repeating the choice beside them: the shipped body
crept into the child's zone and the crossing person (26 of 40, three falls). The change was made to describe a skill
honestly; it changed the judge's policy instead, and the runs no longer compared bodies. Fix (R5c): the original text, no
hidden motion, and a failed pick-up withdrawn from the next decision, the progress-bound pattern of R3b. Rule: hold the
judge's inputs fixed across an instrument revision that compares bodies; bound a failing action by withdrawing it, not by
making it move.

**52. Scenery that could not be touched (bench 3, found 2026-09-24 by looking at a published clip).** The room's walls and the
cart were given collision flags and had none of the effect they were given them for. MuJoCo Playground's feet-only training
scene sets **every** robot geom to contype 0 and conaffinity 0 and provides contact through five explicit pairs (each foot to
the floor, and three self-collisions), because that is what makes it fast on a GPU. Any scenery added to such a scene is
decorative: the robot walked through the wall panels on its way to a requester standing off the doorway's axis, and the
episode recorded no contact. The door-collision metric was a proximity proxy (inside the doorway zone while the cart was
present), so the numbers looked sensible while no physics ever happened. Nothing in the acceptable sets, the notes or the
hand-over scoring depended on it, and the people and the table are deliberately non-colliding with proximity scored instead;
the walls and cart were not, and are the bug. Fix (R7): explicit contact pairs from each foot to each wall and to the cart,
verified to leave mass and inertia untouched; driven at a wall panel the robot now contacts it and falls, and the doorway
gap passes cleanly. Rule: in a scene built for speed, adding a geom does not add a constraint — assert the contact you
intend, and never trust scenery you have not driven the robot into. *Amendment (same day):* making the walls real was tried
and reverted. With the contacts in place every arm fell in nearly every episode, because the requester stands off the
doorway's axis, the gap is narrower than where she stands, and the governor steers straight at its target on a body with no
lateral velocity; a two-stage waypoint through the gap did not help, since the robot has two metres of travel to correct
1.6 m of offset. A physical doorway needs a navigation layer this bench does not have. What shipped instead is a rendering
fix: the room is drawn as it is simulated, two door posts rather than solid panels, verified to leave every outcome, fall
and episode length identical on eight seeds across four situations. The doorway remains what it always was, a fact in the
state. Second rule: when a bench's picture claims a constraint its model does not enforce, either enforce it or stop
drawing it — and prefer the change that provably moves no number.

**53. A speed-up that was a failure rate in disguise (2026-09-25 00:00 PDT).** I read episode seconds off E153 per arm and reported the copy
as 2.3× faster than the judge on the fresh bank. The arms have different failure rates and failures are the expensive
episodes (122 s against 25 s), so the average was dominated by how often each arm failed, not by how fast it decided. Paired
on the twenty seeds both arms handle, the copy is 4.1 s *slower* and faster on ten of twenty. **Any speed comparison between
arms with different success rates must be paired on shared successful episodes, and the unpaired average reported separately
and labelled as a fleet cost rather than a decision speed.** The re-correction result survived the pairing (17/19 and 27/30);
the distillation result did not. Caught within the hour, before the claim left the notebook.

**53, continued (audit, 2026-09-25 00:17 PDT).** Applied to the whole archive: 88 arm pairs across every results file would mislead if
compared unpaired. In the cases that reached the README the direction survives and the magnitude is 1.7–2.5× overstated; one
published number (the station's written bank, "11 s per line against the rules' 15") was amended in place to the paired
11.1 against 13.7. Real sign flips exist (oracle vs rules on the duck; E151's judge vs copy; E123's copy vs rules) and none
had been quoted, which is luck rather than method. The diagnostic that decides whether pairing matters is the within-arm
handled-against-missed time: 122 s against 25 s on the humanoid (pairing mandatory), 10.2 against 11.1 on the station (no
asymmetry, because a decision-level bench charges nothing for failing). The asymmetry belongs to embodied episodes.

**54. A judgment finding from an arm that never exercised the judgment (2026-09-25 08:47 PDT).** On E158's contradicting-note situation the
veto-window arm scored 0 of 12 and I wrote that the window "destroys" the situation, with a mechanism about its proposals
being motion-shaped. The decision records say the arm never picked the object up in any episode, so the hand-over the
situation needs was offered in **0 of its 289 decisions**. It ran out of clock before reaching the table. **Before explaining
why an arm failed a situation, check whether the action that situation requires was ever in its option set.** One line over
the records. The rescue result on the other situation, where the judgment was exercised in two decisions, is unaffected.

**55. A handled criterion that rewards the action and not the ending (E158/E160, 2026-09-25 15:57 PDT).** `sling_note`'s criterion was
`put_down and not given and wrong_handovers == 0`. Two arms satisfied it and then ran to the 120-second ceiling at over 200
decisions, putting the object down correctly and never declaring themselves finished, and the bench scored that as a clean
handle. **A criterion whose subject is an action must also require the episode to end,** or doing the right thing and then
dithering for two minutes is indistinguishable from doing the right thing and stopping. Found by comparing episode seconds
across arms that scored identically.

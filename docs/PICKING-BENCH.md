# Bench 4: the picking station, at decision level

A warehouse or store picker runs on a grasp-score threshold and a remote person for the rest. This bench measures the decision
layer of that loop and nothing else: **there is no physics here.** One order line per episode: pick the named item out of a
tote and place it in its destination, a customer tote (it ships) or the return bin (a person sorts it later), at a station
with a remote picker who can be asked. The grasp scorer, the verify check and the clock are explicit, seeded stochastic models
(`src/picking/station.py`): a grasp succeeds with probability .25, .60 or .90 at a low, mid or high score; a double pick shows
as a weight heavier than expected; every action has a stated duration (grasp 4 s, regrasp 6 s, place 3 s, scan 2 s, the
picker's answer 20 s of their time) and the line's time is the sum. The picker's answer resolves what the robot could not: it
reads the label, marks a grasp point, says where the item goes. Facts, options, acceptable sets, skills, events and banks
follow the duck room's contract, so the harness, the judge arms, the owned copy and the rule-drafting tools run unchanged
with `DUCK_BODY=pick`.

**What is fixed.** The written bank (seeds 0–39, ten lines each) is what the rule program was written for: a grasp failure
(low scores), a double pick, a person's hand in the tote, an unreadable label. The rules: wait for a hand, put back a double,
scan twice then ask, regrasp a low score, ask after three attempts, place in the order's destination; they read no notes. The
unwritten bank (seeds 40–99, twenty lines each) was designed after the rules froze and each line carries an operator's note:
a sharp item ordered into a customer tote when the station has no sleeves (return bin), an item that turns out wet after the
grasp (return bin), a recalled lot on the label (return bin). Seeds 1000 and up are clean picks with no complication (E118).

**What a picking company asks for.** Seconds per line, wrong picks (anything that ships and should not: a double pick, a
sharp item without a sleeve, a wet item, a recalled lot), exceptions (lines skipped and flagged), asks and operator seconds
per line, and how those move when the mix of lines changes (E118).

## Results (E117, 100 lines per arm)

| arm | written lines handled (of 40) | s per line | operator s per line | wrong picks | unwritten lines handled (of 60) | safe (nothing wrong ships) | s per line | operator s per line | exceptions |
|---|---|---|---|---|---|---|---|---|---|
| frozen rules | **40** | 15.4 | 1.5 | 0 | 0 | 0 | 8.7 | 0 | 0 |
| rules + ask once on a note | 40 | 15.4 | 1.5 | 0 | 0 | 0 | 28.7 | 20.0 | 0 |
| oracle | 40 | 14.4 | 0.5 | 0 | 60 | 60 | 8.7 | 0 | 0 |
| rules rewritten with hindsight (E119: three clauses, two minutes) | 40 | 15.4 | 1.5 | 0 | **60** | 60 | 8.7 | 0 | 0 |
| owned copy, distilled from the judge's written-line decisions, no correction (E120; fresh lines) | 33 (double pick 4 of 10) | 9.8 | 0 | 6 | 0 | 0 | 9.2 | 0 | 0 |
| owned copy after one masked correction round (E121; fresh lines) | 33 | 9.8 | 0 | 6 | **60** | 60 | 23.9 | **14.7** | 0 |
| owned copy after one round with the operator's replacement as the label (E123; fresh lines) | 33 | 10.8 | 0 | 5 | **60** | 60 | **9.0** | **0** | 0 |
| owned copy after a further round on the written lines, replacement labels (E127; fresh lines) | 33 | 10.7 | 0 | 4 | **60** | 60 | 8.7 | **0** | 0 |
| the same, every correction record counted four times (E133; fresh lines) | 34 | 11.0 | 0 | 5 | **60** | 60 | 8.7 | **0** | 0 |
| the same with forty more written lines' takeovers, 33 put-back records ×4 (E134; fresh lines) | **38** | 12.1 | 0 | **9** | **60** | 60 | 8.7 | **0** | 0 |
| judge | 32 (double pick 4 of 10) | **10.9** | 0 | **6** double picks shipped | 40 (recall 0 of 20) | **60** | 13.0 | 6.7 | 20 |
| judge gated at .5 | 34 | 20.4 | 10.0 | 6 | 40 | 60 | 13.3 | 7.0 | 20 |
| judge + one-second veto window | 34 | 17.3 | 7.0 | 6 | 40 | 60 | 13.0 | 6.7 | 20 |

![Figure 13: the picking station](../figures/fig13-picking-station.png)

![Figure 14: one recalled-lot line as five decision traces: the frozen rules ship it, the rewritten rules return it, the judge flags the line, the uncorrected copy ships it at .93, the corrected copy asks the picker and returns it](../figures/fig14-recalled-lot-trace.png)

*One order line, five deciders. The note says the lot is recalled and must go to the return bin. The frozen rules and the uncorrected copy ship it, the copy at a stated .93; the judge skips the line and leaves the bottle in the tote; the rewritten rules return it in eight seconds; the corrected copy returns it too, after twenty seconds of the picker's time.*

**Reading.** Same shape as the other three benches, with two sharp edges. The judge reads two of the three notes completely
(the sleeve and the leak: 20 of 20 each, return bin, no ask) where the frozen rules ship all sixty; on the recalled lot it skips
the line and flags it without touching the item, which ships nothing wrong but leaves the bottle in the tote against the
note's instruction, so it is safe by the fleet's count and unhandled by the note's. And it fails one written situation
confidently: holding two items with the weight reading heavier than expected, it places in the customer tote six times in
seven at a stated .73 to .95, never putting one back; the gate at .5 and the veto window let all six through. That is this
bench's crossing adult: the fact is in plain words, the rules handle it in one line, the judge does not read it. Two of seven
pre-registered predictions held; the notebook has the misses. Rewritten by its author after reading the unwritten lines, the
rule program handles every line with zero wrong picks at its own speed, in three clauses and two minutes (E119): the judge's
value on this bench was the interval before those six lines existed. Method error 37 (the acceptable set forbade placing in the
destination while a hand was in the source tote) is fixed in the bench's next version before anything else runs on it.

**The copy on the station (E120, E121).** Distilled from the judge's decisions on written lines, the owned copy is the judge where the rules were written (33 of 40, the same double-pick blind spot) and the rules where they were not (blind, sixty wrong picks, at 60 ms). One masked correction round on its vetoed decisions takes it to 60 of 60 fresh unwritten lines with nothing shipped wrong, at fifteen operator seconds per line: the veto taught it which action was wrong, not which acceptable action is cheapest, and it chose to ask the picker. Noise floor (E132): three repeat runs of the judge on the same sixty fresh unwritten lines gave identical outcomes to the line (40/60, 22 asks, 0 wrong, every line the same), so differences in this table are real down to one line; the same API jitter that moves the humanoid's thirty-seed totals by two or three (E130) changes nothing here because no decision sits near a tie and there is no physics to amplify one. With masked labels the copy is the better-safe-than-cheap owner; with the operator's replacement action as the label at every visited state (E123) it does the oracle's job on sixty fresh unwritten lines with nothing shipped wrong, no asks and no operator time, beating the judge that taught it (40 of 60 at seven operator seconds) and tying the hindsight programmer and the drafted rule. The label form decides what the copy learns: the veto says not that, the replacement says this instead, and a fleet's takeover logs carry the second for free. In simulation the replacement is the oracle's action; in a fleet it is what the operator did. The copy's one written-bank blind spot, the double pick, is inherited from the judge and resisted a correction round (E127): at the failing states it reads holding two items and heavier than expected and still places the pair at a stated .58 to .84, where put back is the only acceptable action; twenty-four counterexamples against a thousand records of the teacher's strongest habit did not move it, and a veto window at .5 catches none of the six. Weighting every correction record four times fits the corrected states (val agreement 96.9 %, a leaky number: method error 44) and changes nothing on fresh lines, 5 of 10 at a stated .58 to .92 (E133). Twice the takeover data does move it: with thirty-three put-back records instead of twenty-four (forty more written lines, about ten more double picks) the copy handles 9 of 10 and 38 of 40 written lines, the unwritten sixty still at no operator time (E134). Its calibration on the pattern is inverted, .39–.64 where it puts back and .75–.89 where it still places the pair, so a handoff line would send right answers to the picker and no wrong ones. The one-clause rule over the verify check remains the cheaper owner, a minute to write and no residue; the takeover route works too, at a data cost now measured. Division of labour: the rule for what the sensor says, the judge for what the note says, the copy for what the corrections covered.

## The item-mix drift (E118)

Seventy clean lines (no complication) were added and three mixes composed from per-line results: easy (70 % clean, 30 %
written), mixed (30 / 40 / 30 % clean / written / unwritten), hard (10 / 40 / 50 %).

| arm · easy → mixed → hard | ask rate | wrong picks per line | operator s per line | lines handled |
|---|---|---|---|---|
| frozen rules | .03 → .02 | 0 → .30 → .50 | .8 → .7 | 1.00 → .50 |
| judge | 0 → .10 → .17 | .045 → .060 → .060 | 0 → 3.3 | .94 → .75 |
| judge gated at .5 | .24 → .31 → .34 | .045 → .060 → .060 | 6.4 → 8.0 | .95 → .77 |
| oracle | .01 | 0 | .1 | 1.00 |

The gate escalates more as the mix hardens and loses fewer lines than the rules, but its wrong picks are the same six confident
double picks in every mix, which it never sees, while it escalates 19 % of clean lines for nothing. On this bench the judge's
errors are confident and its doubts are on the easy lines, the reverse of the sorting cell: a threshold is worth what the
number's ranking is worth. Three of four predictions held.

## Rules drafted from the judge's decisions (E122b)

The judge's 165 decisions on the unwritten lines, compiled into a decision tree over the station's facts and the words of the
notes, scoped to states the written bank never showed, and placed in front of the frozen rules; tested on sixty fresh unwritten
lines. From all decisions: 40 of 60, copying the judge's habit of skipping the recalled line (eight operator seconds per line).
With the vetoed decisions dropped, or replaced by the operator's answer: **60 of 60**, nothing shipped wrong, no operator time,
9.3 s per line, a three-leaf rule that ties the oracle and the programmer with hindsight. The learned clause reads "a note and
the item in hand → return bin", true of this bank's three notes and not of notes in general; a person reviewing the tree sees
that in one line. Three of four predictions; the first attempt (E122) found that the drafting tool had never been shown the
station's facts (method error 39) and handled 20 of 60.

## A second System One model in the seat (E138)

CLM-8B (Kwok et al., 2026; open weights, the same typed questions as Jev; a frozen Qwen3-8B encoder with two small
projection heads, a softmax over scaled cosines) was run zero-shot on the same seeds, states and options as Jev, through a
local client on the engine's own schema. On the sixty fresh unwritten lines it "handles" 60/60 with nothing shipped wrong,
by asking the operator on every line after twenty-odd wrong decisions of its own (20 operator seconds a line against Jev's
7.3; 18 % of its decisions acceptable); on the written lines 35/40 with two wrong; on bank v2 16/60 with six wrong picks
where Jev handles 40 with none. Over 3,906 decisions its choice was acceptable 12 % of the time at a mean stated probability
of .58 (over-confidence +.46, ECE .50), the curve inverted in the middle. A contrastive lookup rewards words the state and
the option share (a label that reads lot 42 pulls "scan the label again"); it does not read the clause of a note. The
calibrated number is a property of the model, not of the interface (claim 4.86). Post-training the heads on the fleet's records
recovers it, on what the records cover (E139): trained for eight seconds on the same records as the copy r5 (538 unique
texts embedded once), the heads handle every fresh unwritten line on two line sets at no operator cost, ECE .50 → .06, and
miss the finer endings the copy learned from identical records (bank v2 35 against 60: they put the wrong item and the
held lot in the return bin where the note asks for a put-back and a skip; written lines 27 against 37). Behind the veto
window, now informative, bank v2 reaches 54 at nineteen operator seconds a line (claim 4.88).

![Four models in the seat](../figures/fig18-two-architectures.png)

The label form on the second architecture (E144): E123's 776 correction states as uniform, masked and replacement targets,
each post-training the heads in seconds. All three handle the sixty fresh unwritten lines with nothing shipped wrong, at
10, 13 and 0 operator seconds a line; the replacement is slightly over-confident, the masked slightly under, the
uniform under-confident by 0.10: the veto keeps the habit of asking, the replacement replaces it, flat targets un-teach the
head's confidence. The same result as the copy's on the same states (E123), so it is about the intervention data (claim 4.90).

What the rounds do to the number (E146). Six cumulative heads, each scored on the lines its rounds cover and on bank v2, which
none of the first five touches: the expected calibration error falls .362 → .047 → .013 → .008 where the corrections land and
rises .307 → .331 → .374 → .399 where they do not; the stated probability at its wrong decisions on the untouched bank rises
.62 → .81 → .87 → .90; and the operator's veto window, which rescued 34 of 60 lines from the uncorrected model, rescues none
after two rounds. The round that finally covers that bank restores all three (ECE .117, handled 20 → 35, rescue +19).
Correction makes the number honest where it corrects and dishonest where it does not, and the operator's safety net is what
degrades: a falling intervention rate is not evidence of a safer fleet unless an untouched bank is scored every round
(claim 4.94).

![What correction rounds do to the number](../figures/fig21-calibration-rounds.png)

## Bank v2: situations that arrived after the copy was corrected

Three more unwritten situations (seeds 4000–4999; twenty fresh lines each on 4030–4089), designed after the copies had been
corrected on bank v1 and the written lines, each with the operator's note: crushed packaging (return bin), a label that
names a different item (put it back and ask), a lot on hold (leave it in the tote, tell the picker). No new fact keys and no
new options, only new values, so a novelty gate cannot read the bank off a key.

| arm | handled / 60 | damaged / wrong item / hold lot | wrong picks | operator s per line |
|---|---|---|---|---|
| frozen rules, and the rules rewritten for bank v1 | 1 | 0 / 0 / 1 | **59** | .3 |
| oracle | 60 | 20 / 20 / 20 | 0 | 13.3 |
| judge | 40 | **0** / 20 / 20 | **0** | 6.7 |
| owned copy r2r, r4 (corrected on bank v1 and the written lines) | 21, 20 | **20** / 0 / 0–1 | **39, 40** at a stated .80–.87 | 0 |
| **owned copy r5, one replacement round on thirty v2 lines** | **60** | 20 / 20 / 20 | **0** | 13.3 (the note says tell the picker) |
| CLM-8B zero-shot (an open contrastive System One model, Jev's interface; E138) | 16 | 16 / 0 / 0 | **6** | 42.0 (126 asks) |
| CLM-8B zero-shot + veto window | 53 | 20 / 17 / 16 | 0 | 32.4 |
| CLM-8B heads post-trained 8 s on the copy's records (E139) | 35 | 20 / 9 / 6 | 0 | 5.0 (15 asks) |
| the same + veto window | 54 | 20 / 19 / 15 | 0 | 19.5 |

The humanoid's story (E126, E135, E136) replicates here where the new situation lives in facts the copy's corrections never
touched: the copies ship the mismatched item and the held lot at .80–.87, the judge reads the note, one round makes the copy
whole (old lines kept: 37/40, 60/60), and r4's training vocabulary flags every v2 decision and none of its old ones. Two
twists. The copies handle crushed packaging 20/20 with no note read: bank v1's leak correction taught "condition other than
dry → return bin", and the new value fell under it, so blindness is about facts, not banks. And the judge reads "must not
ship" and skips every damaged line, nothing shipped and nothing put in the return bin as the note's second clause asks: 0 of
20 by the registered criterion, 0 wrong by the fleet's ledger (E137, claim 4.85).

## How to run

```bash
USE_TF=0 PYTHONPATH=src DUCK_BODY=pick python src/duck/e93_run.py --arms rules oracle --seeds 0-9 --out results/duck/demo_pick.jsonl
```
Judge arms need `TYPESAFE_API_KEY`. Scoring: `python src/duck/e93_eval.py e117 anticipated|unseen`; the picking numbers
(wrong picks, seconds per line, exceptions) are in the notebook's E117 entry and the figure script `tools/fig13_picking.py`.

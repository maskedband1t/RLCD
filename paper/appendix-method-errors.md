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

**30. A dead judge that kept scoring (E95, 2026-09-21).** The TypeSafe account ran out of API credits during the R2 run.
The duck harness mapped every failed call to `ask_operator` with a `source: error` tag and carried on; the two judge
arms completed all 140 episodes asking nineteen times per episode, and the scoring script tabulated them as results
(15 % goal, 77 operator seconds). Caught because the confirm arm's numbers were identical to the ungated arm's and no
judge record carried a probability. Fix: API errors are counted per episode and three in a row abort the arm; the
dead-judge episodes are quarantined in `e95_jev_invalid_apicredits.jsonl`. Rule: an arm that cannot reach its model
has no result, and a harness must refuse to produce one.

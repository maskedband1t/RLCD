# The recipe: a calibrated judge in the loop, and a head you own

What worked here, in the order a team would build it. Every step names the experiment that earned it.

**1. Write the facts, not the numbers (E70, E79).** Code converts every measurement into a category before the model sees it ("weight: heavy", "tray: blocked_by_lid", "status: on_table_left"). Extract an operator note's conditions once per episode into closed-set fields and let code bind them per part. Numbers-in, categories-out was worth +47 points; extraction-once put the judge at the perception ceiling.

**2. Enumerate the options in code (E68, E75).** The model never invents an action. Code lists what the robot could do now — place P4 in the violet tray, pause, set down, regrasp, wait, ask — with one operational sentence each. Where code knows which part comes next, let code pick it and ask the model only what it cannot know.

**3. Ask narrow literal questions in one parallel call.** One choice over the options; one yes/no for grasp manner; one score for situational risk (`src/cell/policies.py`, class `Jev`). Add a literal question for any time-critical conflict you discover (E76's "is it safe to hold still right now?"), and combine the answers in code.

**4. Spend the probability, not a score (D7, method error 27).** Gate and confirm on the top-1 *probability*. Some heads report an entropy-based "confidence" that runs ~.15 below the probability; a threshold on it will over-ask. Check what your model's confidence field is before you set τ.

**5. Give the governor the safety rules (E71, E92).** Safety, geometry, order, waits and *when to ask* belong to code. When the judge fails an event repeatedly, look for the rule in the facts you already have: "hand present and holding a heavy fragile part → set it down before pausing" fired on exactly the episodes it was written for and took broken parts to zero for every judge.

**6. Use the confirm level (E88).** Below τ, propose and wait one second for a veto instead of asking. Same violations, two thirds of the operator time. Count vetoes; if they exceed a third of windows, your judge's number is drifting (the open 27B: 38 %).

**7. Log the vector (E91).** Every decision: state, options, the full probability vector, the outcome, the governor's action. A log of chosen actions alone trains a head that is over-confident and blind in ranking.

**8. Distil plainly (E91, E91c).** After a few thousand decisions, fine-tune a pretrained typed-decision encoder (we used Laya, 421M, Apache 2.0) with plain soft cross-entropy against the teacher's vectors. Three epochs, AdamW 2.5e-5 / 1e-4, cosine, clipping at 1.0; fit per-bucket temperatures on validation. The RLCD-style policy-gradient recipe was not needed and cost 4.6 points at this scale. Command:
```bash
USE_TF=0 PYTHONPATH=src python src/cell/e90_laya_head.py train --recipe ce_soft --out results/cell/my_head --extra-records path/to/more_records.jsonl
```

**9. Evaluate in the loop, never only on records (E77, D4d).** Agreement with the teacher on recorded states did not predict closed-loop competence for a 527k student (85 % → 59 %) nor for a 27B (parity → −9). Hold out seeds; score parts correct, violations, operator seconds; pair by seed; bootstrap.

**10. Run one correction round, then measure what remains (E80, E90).** The teacher labels the states the student actually visited. It fixes drift (pausing, collapse onto one action). What it does not fix is the residual to name: which events the teacher itself misses.

**11. Deploy on the robot (E91c).** 90 ms per decision on a laptop-class GPU, no API call. Keep the cloud judge as teacher and arbiter; keep the governor identical.

**Schema for the record** (`results/cell/*_record.jsonl`): `{"key": sha1(state, options), "state": {...facts...}, "options": {key: sentence}, "answer": {"choice", "confidence", "probabilities": {key: p}, "gently", "risk", "latency", "tokens"}}`.

**Shadow mode, for a fleet that wants one number before anything touches a robot.** Replay recorded sessions; at every takeover ask the judge what it would have done; write its answer and probability beside what the operator did. Agreement and the confidence-vs-agreement curve are the deliverable. Cost at $0.042 per million tokens: about 2 cents per 300-decision session.

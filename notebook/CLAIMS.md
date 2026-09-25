# Claims audit — working backwards from the page

Every sentence the finished page will assert, and whether we can currently
back it. Written before the page, because drafting the artifact is the fastest
way to discover which experiments are missing.

Status key: **HAVE** evidence in hand · **RUNNING** · **GAP** nothing yet ·
**CUT** decided against

---

## Part 1 — (withheld from the public snapshot: company-specific context)

## Part 2 — what looking at the data found

| # | claim | status | evidence |
|---|---|---|---|
| 2.1 | Filtering DROID on "has a task label" deletes every failure | HAVE | 99.9% vs 20.0% success, n=95,658 |
| 2.2 | One action dimension carries fake 430x spikes (rotation wrap) | HAVE | 43/2,955 transitions, 13.5x inflation of mean |dx| |
| 2.3 | DROID is broad not deep; scene density must be built | HAVE | 564 scenes; final slice 910 eps / 4.58 h / one camera |
| 2.4 | Camera extrinsics are a bad proxy for "same scene" | HAVE | merged two kitchens; `building` column is ground truth |
| 2.5 | A stopwatch scores 80.7% on the full set — but only +11.3 over the class prior, and 58.3% on a balanced set | HAVE | n=910 unbalanced (69.3% majority baseline); n=60 balanced. **Never quote the 80.7% beside a balanced-set number** (method error 6). |
| 2.6 | Neither a 7B vision model nor a stopwatch can judge these episodes on balanced data (55.0% vs 58.3%, chance 50%) | HAVE |
| 2.7 | Nine action-stream features + logistic regression judge success at 0.772 AUC, n=800 held out | HAVE | E23; survives truncation (E23b): -1s costs 0.005, end-features removed still 0.705 |
| 2.8 | A zero-shot calibrated judge reaches 0.676 AUC with no labels at all, vs 0.772 for a model fitted on 1,200 | HAVE |
| 2.9 | Episode length does not predict success across scenes (r=+0.028, n=6,846) | HAVE |
| 2.10 | Task progress is estimable without vision; a proprioceptive judge adds +0.057 r over an elapsed-time clock | HAVE | E30 + replication on 300 fresh episodes, clustered bootstrap, CI [+0.037,+0.080] |
| 2.11 | An elapsed-time clock reaches r=0.72-0.77 on progress estimation — a baseline the visual-progress literature does not report | HAVE |
| 2.13 | A cheap proprioceptive trigger catches 24% of failures at a 10% alarm budget (4x random) but is NOT a high-recall gate | HAVE | E36 v2, fixed wall-clock probes; kills the cascade cost argument, supports an advisory signal |
| 4.6 | With a cost model, decide by expected cost from P(success) — hand-set confidence gates cost 3x more on the same answers ($44.33 vs $14.37 per 100) | HAVE | E53; the one place calibration did a job an uncalibrated score could not |
| 4.8 | The dispatch shell reads rules precisely in both directions (fires at 0.96 when met, 0.13–0.18 when time/distance/staleness says not met; 8/8) | HAVE | E54 scenario suite, answers correct by construction |
| 4.9 | The same hazard moves P(success) 0.79 → 0.11 when stated as a rule instead of a condition — encode hazards as rules | HAVE | E54 tier 5 A/B, single variable |
| 4.11 | The model evaluates rule conditions on time, distance, dates, staleness and contradiction correctly, but blurs at an exact numeric boundary (0.57 at 10.0 vs "over 10"), does not convert units (22 lbs fires a kg rule at 0.85), and lets a rule about another robot depress P(success) by 18 points | HAVE | E54–E55, 25 constructed scenarios |
| 4.12 | Division of labour: code evaluates thresholds, units, entity scope, validity; the model judges. Irrelevant state is not neutral to a calibrated estimate | HAVE | E55 R-3/R-7 case |
| 4.10 | A rule annotated as withdrawn still fires (0.52); revocations must be filtered in code, never parsed by the model | HAVE | E54 tier 5 |
| 4.7 | The dispatch shell responds to rules, conditions and notes (rule conflict 0.13→0.96, action flips) but is NOT validated — DROID has 3 sites, 2 operators, no heterogeneous state | **GAP** | E53; needs fleet data. Say so wherever it appears. |
| 2.16 | Label disagreement across filers is ~0 where the cause is obviously external (other road user, weather, protocol) and 0.25–0.49 sd in every category where the system might have self-detected | HAVE | E52 audit, 1,245 texts, 36 groups, $0.02. **The "1% self-detected perception" line in E42 is withdrawn** — it averaged incompatible definitions. |
| 2.17 | A fixed-taxonomy zero-shot categoriser applied to every record is a label auditor — the use none of the fifteen predictive framings tested | HAVE | E52; requires fixed option space + zero-shot + near-zero cost together |
| 2.14 | The CA DMV "initiated by" label is a company convention: identical perception failures are 0% AV-initiated at Apple/Toyota/Waymo and 100% at Aurora | HAVE | E51 diagnostic, 5 years, 66 manufacturers |
| 2.15 | Bag-of-words recovers to 0.791 cross-manufacturer when trained on 39 companies; E42's below-chance result was a few-company artefact | HAVE | E51 round 1 — **corrects the transfer claim in E42; the categorisation findings there stand** |
| 2.12 | An open 7B vision model reaches r=0.28 on progress estimation — worse than the clock — while proprioception reaches 0.80 at 1/258th the cost | HAVE | E31b, native 320x180, 12 frames, non-degenerate output. Claim is about a 4-bit 7B model, NOT about vision generally. | E30; the criticism has a number behind it | E28 scoring pass; the stopwatch heuristic fails to generalise, not just to discriminate | E23 arms 3-4; the honest framing is "before you have labels", not "better" | 50.0% at 128x72/6fr (degenerate); 55.0% at 320x180/12fr, 95% CI 42-68%, n=384 needed to separate from chance; stopwatch 80.7% |

## Part 3 — what the model work found

| # | claim | status | evidence |
|---|---|---|---|
| 3.1 | The encoder erases small objects; error is 3x worse on them | HAVE | E1/E4, corrected metric |
| 3.2 | Where you spend latent numbers beats how many you have | HAVE | fine vs wide at equal budget, 28% |
| 3.3 | Knowing the arm's movement is worth 2.3 pts at 1/15 s and 10.4 pts at 1/5 s | HAVE | E3 + E18b/E18d, video-only control at both steps. The original 2.3 stands for its own setting; as a general claim it was wrong. |
| 3.9 | 3.3x the parameters buys 10% at 3 s, less than changing the time step | HAVE | E16, 0.2476 -> 0.2225, both on the fixed harness |
| 3.10 | The model is never told the action that produces the frame it predicts | HAVE | training pairs action i with context frame i; the target's action is withheld |
| 3.11 | Where the arm goes is 82-91% inferable from what it just did; the gripper is not (R² 0.24) | HAVE | E19, n=60,000 held-out windows, unweighted mean R² 0.716 |
| 3.12 | The gripper is 71.7% of action variance and moves in 4.1% of frames | HAVE | E19, measured on the windows training uses |
| 3.13 | Aligning the action to the frame it produces is worth 5% at 3 s, for free | HAVE | E18, 0.2476 -> 0.2353, same model/data/steps |
| 3.14 | Six levers measured; none closes the gap, best is 17% against 3.6x | HAVE | time step 17%, size 10%, alignment 5%, sampling ~0, resolution ~0, self-forcing negative |
| 3.15 | Gripper frames are harder for the model AND for the dumb baseline, in the same proportion | HAVE | E21, 1.34x vs baseline's 1.36x; explains 42.8% vs 41.6% |
| 3.16 | 7x the data at fixed compute is 11.9% WORSE; data needs compute with it | HAVE | E17, scored on real pixels, identical baseline both arms |
| 3.4 | ~~Conditioning earns its keep at direction change~~ — **REVERSED at a longer step** | HAVE | at 1/15 s: 8.3% smooth → 12.7% sharp. At 1/5 s: 31.7% smooth → 24.4% sharp. Both measured; the general claim I made from the first is not supported. |
| 3.17 | The value of action conditioning rises with prediction horizon (0.7 pts at 1/15 s, 10.4 at 1/5 s) and its shape inverts | HAVE | E22, controlled: same encoder, same data, only the step differs. Buckets 8.4/11.3/12.7 at 1/15 s vs 31.7/28.5/24.4 at 1/5 s. |
| 3.5 | One-step accuracy hides rollout failure (flat vs 21x) | HAVE | E5 curves |
| 3.6 | The model's own blur is the distribution shift | HAVE | E5 interpretation + the frame strip |
| 3.7 | Step Forcing / stride recover N% of that | RUNNING | E6 |
| 3.8 | The headline metric and the useful metric disagree | RUNNING | E6 prediction 3 — the best claim on the page if it holds |

## Part 4 — the demo itself

| # | claim | status | evidence |
|---|---|---|---|
| 4.1 | Runs in a browser at drivable speed | HAVE | E7, 20.4 fps WebGPU |
| 4.2 | Real and dreamed side by side, same actions | HAVE | E7 page renders both |
| 4.3 | You can drive it yourself | **HAVE** | `web/drive.html`, keys + touch pad, tested at 375px |
| 4.4 | A confidence signal rises before the picture degrades | **GAP** | M3 not started |
| 4.5 | Validated against 279 real failures never trained on | **GAP** | M3 |
| 4.6 | Works on a phone | **PARTIAL** | layout + controls verified at 375x812; real iOS Safari (WebGPU support, Float16Array) still untested on hardware |

## Part 5 — the calibration record

| # | claim | status |
|---|---|---|
| 5.1 | Predictions logged before results, never edited | HAVE — notebook, 6 right / 2 wrong / 2 partial |
| 5.2 | Method errors logged rather than fixed quietly | HAVE — two logged (extrinsics proxy, bent metric) |
| 5.3 | Every result shown next to its dumb baseline | HAVE — throughout |

---

## What the audit changes

**Six gaps. Three matter.**

1. **4.4 + 4.5 — the confidence signal.** The largest hole, and the thing that
   makes the demo more than a pretty rollout. This is M3 and it has not
   started. It is also the piece closest to the RL framing (a confidence head
   is a value-function-shaped object), so it carries weight beyond the demo.
2. **3.4 — where the action earns its keep.** Asserted twice in conversation
   and never measured. Cheap: bucket E3's validation error by how much the
   arm's direction changed. Should be done before it is said on a page.
3. **4.3 — driving it.** The difference between a video and a demo. Needs the
   action normalisation shipped to the page and an input loop.

**Two to soften rather than fix.** 1.4 and 1.7 are arguments and inferences,
not evidence, and should read that way on the page.

**One to cut.** 4.6 — do not claim phone support without testing on a phone.
Either test it or say "desktop browser".

## Revised order of work

1. finish E6 (running)
2. **3.4 bucketed action analysis** — cheap, closes a claim we have already
   been making out loud
3. **M3 confidence signal** — biggest gap, and the one with the most leverage
4. **4.3 driving loop** — turns video into demo
5. M2.5 VLM judge — still an insurance policy, but now clearly below the above
6. M5 page + work log


---

## Draft written 2026-09-15 — `web/log.html`

Drafting the page early, as intended, to find out which claims cannot yet be
written honestly. Three things the draft forced:

1. **Neutral naming changed the framing for the better.** The page cannot name
   the company, so the selection chain had to be written about the *class* of
   problem — teleoperated fleets becoming autonomous — rather than about one
   firm. That reads as a work sample rather than a pitch, and it is reusable.
   The specificity moves to the email, which was the decision anyway.
2. **Claim 1.7 ("the work is unowned") did not survive contact.** It is an
   inference off a job board and there is no way to write it without sounding
   like a stranger explaining someone's org chart to them. Cut entirely rather
   than softened.
3. **The "what is honestly not done" section is load-bearing**, not a
   disclaimer. Four bullets: holds for about a second rather than three,
   confidence signal designed but unvalidated, one scene only, 128x72. A page
   that claimed otherwise would be caught in about ninety seconds by anyone
   who has built one of these.

Still blocked on results: the confidence section (M3) and any claim that the
rollout holds long enough to be worth driving (M2).


---

## Status after the overnight run (2026-09-15)

**Three experiments, three negative results, and they converge.**

- E11 flow head: does not fix the blur, and the metric I used to judge it was
  rigged against sampling — caught and logged.
- E12 integration steps: inconclusive, noise larger than the effect at n=8.
- E13 VLM judge: exactly chance, leak-checked, and 2.5x the pixels did not
  move it.

**What the page can now claim that it could not yesterday:** that dropping in
a vision-language model as an automatic success detector does not work at this
fidelity, measured against two baselines with a leak check. That is claim 2.6
and it is a *finding*, not a gap.

**What is still blocked:** M2 (the rollout), and therefore M3 (confidence),
which turned out to depend on it — a structural mistake in the original plan,
since a model whose errors are systematic rather than stochastic has no
uncertainty to read off.

**The honest shape of the artifact right now:** four measured findings, five
logged method errors, a calibration record that is roughly even, and a demo
that runs but does not yet wow. The work log is strong. The hero shot is not
there.

**4.13 — The dispatch shell's failures were in the code-evaluable layer, not in the model's judgment.**
A preprocessing pass that normalises units, filters rule validity and entity scope, evaluates numeric thresholds in code, and promotes hazard phrasings/conditions to explicit rules took the same 25 scenarios from 17/25 to 24/25 with the model, questions and scenarios unchanged (7 fixed, 0 broken). The remaining failure is a judgment call where the model's answer is defensible. **Caveat:** patterns were written after seeing the failures — mechanism is established, coverage is not (E56). Status: SUPPORTED (mechanism) / GAP (coverage: needs held-out scenarios and fleet phrasings).

**4.14 — Jev in an extraction role replaces pattern-matching on fleet text with no loss and no regressions.**
One `choice` question per rule / note / condition, sent in parallel, with all regex text-reads off, matched the regex arm exactly (31/34 stable) and read held-out rewordings the regexes could not (lifted → does-not-apply 1.00; unit R-7 → 1.00; recalibrated-and-verified → resolved 1.00; dock rule in force → applies 0.98). Because the model cannot generate, a second categorical question ("which part?") stands in for summarisation and yields one-line rules; that restored the margins the quoted-note rules had lost (buried hazard P .37 → .09). Known misses: recurrence ("seized up twice, freed both times") read as resolved 0.86; run-to-run noise in P(success) ±0.08 on identical inputs (E58, E58b). Status: SUPPORTED on 34 constructed scenarios, one phrasing per category / GAP for paraphrase sets and fleet text.

**4.15 — On resolved-fault notes, pattern-matching is worse than no preprocessing; Jev extraction is not.**
Five wordings × 2 repeats: raw 10/10, regex pass-one 6/10, Jev pass-one 10/10. A pattern that matches a component word ("bearing", "gripper") in a note about a *repaired* component promotes a false rule and the calibrated judge obeys it. Across seven categories × 5 wordings × 2 repeats the arms score raw 50, regex 53, Jev 63 of 70; Jev wins or ties every category; pass/fail flips on repeat in 4 of 210 trials (E59). Status: SUPPORTED on constructed paraphrase sets / GAP for fleet-written text.

**4.16 — A category the question did not offer looked like a model failure; offering it fixed the read with no collateral.**
"Seized up twice, freed by hand both times" read as resolved (0.89) until `intermittent_or_recurring` was added as a choice. On six fresh recurring wordings × 2 repeats: judge alone 2/12, Jev extraction 12/12 (recurring ≥ .95 on every wording); on ten control wordings that mention past recurrence but say root-caused-and-fixed: 0/10 promoted, resolved 1.00 on every one (E60). Generalisation: most E55–E59 "model failures" were vocabulary the questions lacked; with a non-generative model the vocabulary is the engineering. Status: SUPPORTED on 16 fresh wordings / GAP for fleet-written notes.

**4.17 — On real operator text, the model's split verdicts point at missing vocabulary, and offering it resolves half of them with a 2% noise floor.**
1,233 unique DMV disengagement descriptions through a 9-way cause question: 6.8% split (no option > .5), 1.9% unclear-top, 57% decisive above .9; split rate is a property of the writer (formulaic 0%, narrative 16–21%). Three categories proposed from half the splits (anticipatory takeover, expectation mismatch, ODD exit) resolved 21/42 of the held-out half (re-asking the original question: 1/42), with 173/200 non-split controls unchanged and 24 of the 27 changes being absorption into the new categories (E62–E63). The residue names the next round (mechanism-vs-cause; system-initiated fallback). Status: SUPPORTED on one round / GAP for a second round and for robot-fleet notes rather than AV reports.

**4.18 — The place-vs-drop blind spot is not visible in the wrist camera; decoded-vision-to-Jev was killed at the decoder, before Jev.**
Blind hand-check on 48 release/+1 s wrist frames (24 place / 24 drop): 45% accuracy, 1 of 24 drops caught — a failed release mostly looks like a successful one (object resting on a surface); the difference is where it was supposed to go, i.e. the task spec, i.e. the label. Qwen2.5-VL-7B (4-bit) at 320×180 was degenerate on the same frames (gripper "closed" on 92% of frames where it is open by construction). E46's "identical in motion statistics and obvious in pixels" is withdrawn for this camera (method error 12). A fair test needs exterior views and can only score spec-free distinctions (E64). Status: NEGATIVE / GAP for exterior cameras.

**4.19 — As a critic over a language planner's candidate next steps, Jev beats the planner's own logits on accuracy, calibration, and ambiguity reporting.**
1,200 four-way questions over real DROID "put X in/on Y" instructions, one distractor type per question. Jev: 96.8 % on the base tier (skip-ahead 84, repeat/wrong-object/irrelevant/post-failure 100), ECE .020, AUROC .970, confidence .63 on its errors vs .97 when right; gating at ≥ .95 gives 82 % coverage at 100 %. Qwen2.5-7B-Instruct on the same content: 85.8 % (skip-ahead 40), ECE .120, AUROC .814, .92 confident when wrong; confirmed by a free-answer readout (84.8 %). When two candidates are both acceptable both models place all mass on the pair; the 7B then commits at .93, Jev reports .71. Lexical overlap: 100 % on word-level distractors, 4 % / 0 % on the state-level ones. Jev's own wall: it does not infer state from raw numbers ("force reads 0.0 N" → 16 %); the same fact stated categorically → 100 % (E65–E65d). **Caveats:** candidates and plan templates are constructed by me, not generated by a planner; the baseline is a 7B on-board-class planner, not a frontier model; every remaining Jev error inspected was a defensible alternative ordering. Status: **ARTIFACT-RISK (council 2026-09-16)** — a 12-line canonical-plan tracker scores 100 % on this suite; temperature scaling closes most of the ECE gap and inverts the ambiguity result; five-query vs one-pass interface asymmetry. Survives: AUROC ranking gap. Pending the baseline suite in research-plan v2.

**4.20 — Over candidates a real planner generates, Jev is a strong critic on ordinary prefixes and a weak one after failure reports unless the criteria name progress.**
150 next-step questions on real DROID tasks with Qwen2.5-7B as planner. Ordinary prefixes: veto on the planner's proposal AUROC .970, Jev picks an acceptable step 97.5 % of the time one exists; the planner's samples fail together (an acceptable alternative exists in 1 % of cases where the greedy is wrong), so the critic can veto but not rescue. After a categorical failure report, original criteria: veto AUROC .685, Jev lets diagnostic non-actions ("inspect the gripper to confirm grasp") through; a progress criterion raises veto AUROC to .78 on 60 fresh prefixes (E66b) and, applied to the main set, to .984 with 62 % acceptable picks and 94 % when one exists (E66c); overall veto AUROC .983, 97 % pick-when-exists, 2 % false vetoes. Judge: rules validated by blind hand-check at 92 % after correcting a leniency that had accepted diagnostics containing an action word (method error 14). Status: **ARTIFACT-RISK (council 2026-09-16)** — the .984 is in-sample under criteria revised after seeing model output (method error 16); out-of-sample .778. Pending independent judge.

**4.21 — One critic round (veto → categorical reason → re-plan) adds nothing with a 7B planner: the critic is a precise filter, not yet a loop.**
Corrected judge: 54.7 % → 54.0 % acceptable executed steps over 150 prefixes; 2 false vetoes among 82 acceptable proposals; reasons correct (35 × "ignores the reported failure", 18 × "repeats a completed step"). The planner converted the reason into an acceptable step 0/20 times on ordinary prefixes and 1/37 after failures — it answers "you ignored the failure" with "inspect the gripper". Pre-registered falsifier (gain < 8) fired; an earlier +10 was a judge artefact and is retracted (E67). Status: NEGATIVE as a loop with this planner / GAP for a planner that can use feedback.

**4.22 — With the controller held fixed, most of the published "structurally incapable baseline" gain is two named categories; the judgment's residual value sits at the stations a rule cannot express.**
Drone course in MuJoCo, randomised by seed (40 seeds), one shared guidance loop, pluggable manoeuvre source, physical outcomes. Clean barrier crossing: published baseline 10 % [4,23] → heuristic with sustained commitment 62 % [47,76] → + climb rule 80 % [65,90] → Jev 98 % [87,100]; stations (median) 1 → 3 → 4 → 6. Paired by seed, Jev − climb rule: +17 points clean crossing [+5,+33], +1.25 stations [+0.68,+1.85], contact +0.34 s [−4.30,+4.53]. The arms separate at the sliding gate (60 % vs 80 %) and beyond it (28 % vs 78 % at the second beam). Jev's failure mode is pinning against the gate (5/40 episodes > 10 s contact). The pre-registered "climb rule matches Jev within 10 points" failed in the model's favour. Replication of the published pair as released: 12 % cross, 5 % clean on the fixed course (the published "never" is 88 %). Latency 0.116 s median, 88 calls/episode (E68). Option ablation: Jev with climb removed clears the beam cleanly on 38 % [24,53] — 25 points *below* the heuristic [−45,−3] — because its criteria brake at a fully blocked beam while the heuristic's committed slide rounds the beam's end; Jev − Jev-minus-climb = +60 clean [+45,+75], +2.85 stations. The value is the category named and timed. Caveats: one sim, one course family, sim-supplied perception. Status: SUPPORTED (closed loop, controlled) / GAP for other embodiments.

**4.23 — The same fact as a raw number is nearly invisible to the judge; as a code-evaluated category it is read perfectly — and a program owns the number anyway.**
Paired factorial, 160 base items × 2 formats (critic setting) and 15 threshold/unit items (dispatch setting). Jev: numeric failure items 6.2 % vs categorical 100 %, gain +46.9 points [+39.4,+54.4]; benign items 100 % in both formats (the number is ignored, not misread); dispatch numeric 66.7 % vs categorical 100 %, +33 [+13,+60]. Program arm 100 % in every cell (E70). The 7B letter readout gains only +5.6 [+2.5,+9.4]: 0 % numeric, 11 % categorical — it never retries in either format. The categorical fact is necessary for a judge to act on it, not sufficient; the pre-registered falsifier (any model < +15) fired. Status: SUPPORTED for Jev / NOT SHARED by a 7B / 72B pending.

**4.24 — In the closed loop, 200 ms of judgment latency is free and 300 ms costs; recorded-judgment replay reproduces the live arm and makes the latency curve reproducible without an API key.**
Recorded fingerprint→judgment cache replayed at synthetic latency, 40 seeds per point: replay at 0.10 s matches live Jev (84 vs 86 % completion; paired stations −0.15 [−0.72,+0.40]); at 0.30 s −0.47 stations [−0.93,−0.05] and contact 3.6 → 4.1 s; at 0.50 s −0.85 [−1.50,−0.25], contact 6.5 s, crashes 7/40 (E68). Fingerprint hit rate 65 %; misses fall back to hold-course and are not decisive. Status: SUPPORTED (one course family).

**4.25 — Gating handoff on the judge's calibrated risk head removes 95 % of contact for 18 % operator time and dominates a geometric-proxy gate on operator time, contact and completion at once.**
Drone course, controller held fixed, oracle operator during a 3 s handoff window. Jev gated at risk ≥ 1.6, 20 seeds paired with ungated: contact 3.92 → 0.21 s (−3.72 [−8.29,−0.04]), completion 86 → 95 %, stations +0.55 [−0.20,+1.25], 3.9 handoffs/episode, 95 % fired by the risk head, 83 % within 4 m of an obstacle; zero heavy-contact episodes (ungated: 5/40 pinned at the gate). The geometric-proxy gate on the heuristic arms fires 5–8×/episode for 15–22 operator-seconds at every threshold with contact mostly *rising*; Jev's point Pareto-dominates all of them (E69). Predictions: contact −50 % → −95 % hit; operator time 5–15 % → 18 % miss; P-H2 evaluated as Pareto dominance by a fallback declared before the numbers existed. Caveats: n=20 per threshold; an imperfect oracle operator, frozen, that pins itself at the turnstiles when handed off too eagerly (τ=1.2). Status: SUPPORTED (one course family, one operator model).

### 4.26 · SUPPORTED (E71, 2026-09-18) — In a fleet-shaped sorting cell with situational exceptions, a calibrated judgment head over code-enumerated options reads unanticipated operator notes that a frozen rule policy and a lexical parser do not.
Parts correct 87.1 % [82.2, 90.7] vs lexical 82.5 % vs rules 79.2 %; paired jev − lexical +4.6 [+1.7, +7.5]; unanticipated bank 76 % vs 39 % vs 21 %; operator time 7.7 % of the episode, same as rules. 40 seeds, 240 parts per arm, rules frozen at 0fc9493. Not the predicted ≥ 92 %.

### 4.27 · NEGATIVE (E71) — Confidence-gated handoff does not dominate a program's flag-based abstention rule in the cell.
At matched operator time (~33 % of the episode) the gate leaves .55 violations per episode vs .40 for "ask whenever a note exists"; AUROC(confidence → not wrong) .618. Mechanism: probability mass spread over substitutable options (which part next) and surprises that arrive flagged. Contrasts with E69 (drone), where the proxy had no flag and the gate dominated.

### 4.28 · NEGATIVE (E71) — Abstention is not free when the hazard is faster than the handoff.
Precedence case (hand appears while a fragile heavy part is carried): Jev pauses (the literal instruction) at confidence .53–.68; gating converts the split into a 4 s ask, during which the part slips and breaks. 0/6 for every Jev arm; oracle 6/6 by setting the part down first.

### 4.29 · SUPPORTED (E73 → E76, 2026-09-18) — For a time-critical conflict between a literal instruction and a physical consequence, stating the consequence in the option text does not change the model's choice (0/6), but a parallel literal question combined in code does (6/6 parts saved).
Pause chosen at .41–.68 either way; `safe_to_freeze` Noul .25–.32 on all six; code sets the part down before pausing. Six seeds, one event type; the remedy is the vendor's documented one, tested here in a closed loop.

### 4.30 · PARTIAL (E75, 2026-09-18) — Letting code choose the part and asking the model only for the destination halves the operator cost of confidence-gated handoff at unchanged accuracy, but calibration rises only from .62 to .66.
jev3 86.7 % vs jev 87.1 % (paired −0.4 [−2.1, +1.2]); gate τ=.7 at 8.9 operator-seconds vs 17.0 for the E71 gate at a similar violation level; residual wrong decisions are confident misreadings of notes, which confidence does not flag. Below the interpolated program line for budgets under ~12 s; meets it at the flag rule's own point.

### 4.31 · SUPPORTED (E78b, 2026-09-18) — The assembled judgment stack (code picks the part; per-part note-binding and destination heads combined in code; safe-to-freeze check) reaches the perception-limited ceiling of the sorting cell at the rules' operator time.
Parts correct 90.0 % [85.6, 93.2] against a facts-only ceiling of ≈ 91.2 % (21 of 240 parts have uncorrected perception errors); paired +3.3 [+1.2, +5.8] over the single-Choice Jev arm, +7.5 over rules + parser; violations .60 per episode (Jev .78, rules 1.25); zero broken parts; 3.5 operator-seconds (rules_ask 20.4 for 93.3 %, which exceeds the ceiling only by buying the operator's ground truth). 40 seeds; the recall condition remains the binding head's weak type (AUROC .53 in E78's first run).

### 4.32 · SUPPORTED (E79b, 2026-09-18) — Extracting a note's conditions into closed-set heads once per episode and binding parts in code brings the sorting cell to its perception-limited ceiling with zero judgment errors.
Parts correct 91.2 % [87.0, 94.2] vs ceiling ≈ 91.2 %; 19 of 21 remaining misses are perception false alarms or missed damage, 2 are physics; bank 35/38 (recall 7/7, cosmetic 7/7, ambiguous 6/6 by code-detected ambiguity → ask); zero broken parts; +4.2 [+1.7, +7.1] over the single-Choice Jev arm; operator time 7.9 % of the episode (rules_ask 32.8 % for 93.3 %, the two extra points being the operator's ground truth about damage). 40 seeds; **replicated at n = 200 (E82, seeds 80–279): 89.3 % [87.5, 91.0] vs ceiling 89.9 %, paired +5.3 [+3.6, +7.0] over the single-Choice arm, zero broken parts in 200 episodes, judgment misses 0.92 % of parts.** The extraction question's wording mattered: 0/6 → 6/6 on the ambiguous type after stating the exact condition.

### 4.33 · NEGATIVE with mechanism (E77, 2026-09-18) — A 527k-parameter student distilled from 3.8k recorded Jev decisions agrees with the teacher on 85 % of held-out records and reaches 74 % parts-correct on seen seeds but 59 % on held-out seeds (teacher 88 %), because it collapses onto `pause` in states without a hand (615 of 887 held-out decisions) and drifts.
Record-level agreement does not predict closed-loop competence; the failure is covariate shift, the DAgger problem. Latency 8–10 ms per decision. E80 (teacher labels the student's states) and E81 (twice the teacher data) pre-registered to separate the distributional from the data-quantity explanation.

### 4.34 · SUPPORTED (E80, 2026-09-19) — One DAgger round, the teacher labelling the 834 states the student actually visited, lifts the owned head from 59.2 % to 75.8 % [70.0, 80.8] on held-out seeds (paired +16.7 [+6.7, +27.5]) and removes the pause collapse (615 → 10 spurious pauses); the remaining −12.1 [−18.8, −6.2] against the teacher is reading (relabel 0/7, cosmetic 2/6) and over-asking (16 % of decisions deferred), not drift.

### 4.35 · SUPPORTED (E80 vs E81, 2026-09-19) — For the owned head, teacher labels on the student's own visited states beat twice the teacher's own data: 75.8 % vs 63.7 % on held-out seeds (paired −12.1 [−21.7, −3.8] for the data-doubled student), and only the labelled-states round removes the pause collapse (615 → 10 vs 615 → 541 spurious pauses).
The distributional explanation of the E77 failure is confirmed against the data-quantity explanation; the correction loop is the sovereignty mechanism.

### 4.36 · SUPPORTED (D1-cell, 2026-09-19) — On 400 recorded sorting-cell decisions, a plain 7B behind the same typed interface chooses acceptably 37.5 % of the time against Jev's 81.5 %, never pauses for a person's hand (0/24), and places 87 % of its answers on two letter positions regardless of content.
Decision-level, seeded subsample declared before the run. The interface transfers to a small open model; the judgment does not.

### 4.37 · SUPPORTED (E83, 2026-09-19) — When the surprise arrives in the facts with no note, the program's "ask when flagged" rule is identical to the frozen rules (65.0 %, paired +0.0), the single-Choice judgment head gains +19.2 [+10.8, +28.7] over them, and the confidence gate is the only lever that reduces violations further (.93 → .68) — at 20 operator-seconds per episode. The extraction design, which reads notes only, falls to the rules' level (65.0 %). The E71 finding against the gate was a property of flagged surprises, not of the gate.

### 4.38 · NEGATIVE with mechanism (E84, 2026-09-19) — A generic "does anything in the facts call for departing from the default?" head added to the extraction design fires on 25 % of decisions, mostly as wait or ask, costs 3.3 points [1.2, 5.4] on the notes bank and handles the unflagged bank no better than the single-Choice head (45 % vs 50 %); the QA-sticker case is not recovered even when asked narrowly, and asks not bound to a part lose their resolution.

**4.39 (E86, 2026-09-19).** On the sorting cell with ground-truth regions from the segmentation renderer, an
open 53 M-parameter relation model (RelateAnything, ONNX, CPU 0.41 s/frame) reads "part inside tray" at AUROC
.995 (14,276 pairs, 30 episodes); on pairs where box containment is uninformative (.548) it reaches .898, and
it separates in-tray from held-above (.904 vs .643 for a two-feature geometric rule) and from on-lid (.986 vs
.584), while geometry separates neighbouring trays better (.985 vs .896). "Holding" ranks .980 overall but
.666 where boxes overlap; its calibrated scores stay below .5. Rendered scene; regions exact; real footage owed.

**4.40 · NEGATIVE with mechanism (E87, 2026-09-19).** On the 96 real wrist frames with regions from a weak detector
(SAM 3 LiteText "robot arm" box + "small object" boxes), the relation model's "holding" score does not separate
the release frame (object in the jaws) from the frame one second later (jaws open): AUROC .565, 20 paired tiles.
Mechanism: "holding" is not read for a gripper (E86 showed the same on rendered frames), and 39 of 96 frames
lack both boxes. A place-vs-drop lead (.745 [.54, .91], 28 of 48 tiles, evaluability-biased toward drops that
stayed in view) is recorded as a lead only. E64's conclusion stands.

**4.41 · SUPPORTED with a boundary (D5, 2026-09-19).** On 400 recorded sorting-cell decisions, reversing the option
order changes Jev's argmax in 16.0 % of cases against 5.5 % for a same-order repeat (difference +10.5 points
[+6.8, +14.2]); the recorded top option's probability moves .116 vs .030. The flips sit where the model's own
confidence is low: 50 % below .5, 11.6 % in [.5, .7), 1.7 % in [.7, .9), 0 % at ≥ .9. Order sensitivity exists
and is confined to the region the confidence gate already routes to a person; above .7 it is absent.

**4.42 · SUPPORTED with a boundary (E88, 2026-09-19).** A confirm level (below the confidence threshold the robot
announces its action and gives the operator one second to veto; a veto costs a full ask) matches the ask gate's
violations on both banks (−.03 [−.15, +.10] per episode, unflagged, τ = .7) at 63–66 % of its operator time
(−7.4 s [−9.0, −5.8] per episode), across thresholds .6–.8, with unanticipated-correct .70 vs .75. With a 25 %
veto-miss rate violations rise +.10 [+.03, +.20]. The saved time is bounded by the model's error rate below
the threshold (27 % of proposals vetoed). It does not save the time-critical precedence case (0/6, as the ask).
*Addendum (D5b):* averaging probabilities over four random option orders does not recover acceptable choices below
confidence .7 (+0.0 points [−3.0, +3.0] in [.5, .7); −6.5 [−16.3, +3.3] below .5); the order-fragile decisions
are uncertain, not mis-ordered, and belong to the gate.

**4.43 · LEAD, not a claim (E85e, 2026-09-19).** With the official SAM 3 and the gripper named by appearance ("black
robotic claw": box in 88 % of 96 real wrist frames; every "gripper" phrasing 0 %), the geometric feature
"top small-object box below the claw box" separates place from drop one second after release at AUROC .790
[.646, .916], 73 % leave-one-out, on 48 tiles — at a post hoc gripper threshold (.3; pre-registered .5 gives .599).
Overlay inspection shows the measured box is the manipulated object in 3 of 8 frames; the mechanism is
unverified. Object identity (tracking from the release frame) is the prerequisite for any seam claim on real frames.

**4.44 · NEGATIVE with mechanism (D6, 2026-09-19).** An open RL-trained typed-decision encoder (Laya, 421 M,
Apache 2.0) run zero-shot behind our interface on the 400 recorded sorting-cell decisions chooses acceptably
28.0 % of the time (compact rendering) / 27.8 % (raw JSON) / 31.5 % (multilingual, 1,024 window), against the
plain 7B's 37.5 % and Jev's 81.5 %; its confidence is uninformative (AUROC .48). The interface transfers, the
judgment does not, and the rendering does not matter because the state is not being read. D6 is the zero-shot
baseline for the owned-head-v2 fine-tune.

**4.45 · NEGATIVE with mechanism (E89/E89b, 2026-09-19).** As a sub-action annotator over proprioception-only facts
on 1,624 ground-truthed half-second windows, Jev reproduces the field's consistency figures (98.8 % on repeat and
reversed-order re-asks) while labelling 57.8 % of windows correctly against a rule's 66.2 % from the same facts;
adding a heading fact lifts both (70.3 % vs 75.5 %). Boundaries are sharp (91 % recall, 96 % precision) and the
confidence separates (85 % accuracy above .7, 28 % below). Consistency is not accuracy; the label is a function of
the facts, and code writes the facts.


**4.46 · SUPPORTED, falsifying our own prediction (D4, 2026-09-19).** On the 400 recorded sorting-cell decisions, a
dense open 27B (Qwen3.8) read through a Jev-shaped label-logit interface chooses acceptably 84.8 % of the time
against Jev's 81.5 % (+3.2 points, [-0.5, +7.0]); its confidence ranks correctness at .654
against Jev's .81, and 32 % of its answers change when the options are reversed (20 % even above confidence .7)
against Jev's 16 % (1.7 % above .7). The interface is commodity and the argmax is matched; calibration, order
stability, latency and cost are where the calibrated-decision model differs. The 7B-vs-27B gap is confounded
with the readout method.
*Addendum (D4c):* small models through the same readout sit at chance (RWKV-small 26.8 %, RWKV-std 22.0 %, with
83–92 % of answers flipping under reordering), so the 27B's 84.8 % is capability, not the readout.

**4.47 · SUPPORTED (D4d, 2026-09-19).** The open 27B that matched Jev's argmax on recorded decisions (D4) loses 9.2
points [4.6, 14.2] to Jev when it drives the sorting cell itself (75.0 vs 84.2 % parts correct, 40 unflagged-bank
seeds), re-decides twice as often, asks on its own 20× less, and handles the unflagged surprise 12 % of the
time against Jev's 50 %. Under a confidence gate the gap closes to −1.3 [−4.2, +1.7]; under the confirm level
the 27B vetoes 38 % of its proposals against Jev's 27 % and sits at .85 violations for 9.3 operator-seconds where
Jev's confirm sits at .65 for 12.3 and the 27B's gate at .75 for 12.3. Agreement on records is not closed-loop
competence, at 27 B parameters as at 527 k.

**4.48 · SUPPORTED with a boundary (E90, 2026-09-19).** A 421 M pretrained typed-decision encoder (Laya) fine-tuned
with its own RLCD recipe on 3,827 of Jev's recorded sorting-cell decisions drives 40 unseen seeds at 79.6 %
[74.0, 84.2] parts correct (teacher 87.9; byte student trained on the same data 59.2; zero-shot 27.5), at 0.09 s
per decision locally; one correction round on 437 of its own visited states halves its spurious pausing and
leaves parts-correct unchanged (79.2 %, −0.4 [−3.3, +3.3]). The residual is the notes it does not read
(precedence 0/7, relabel 5/7), not distribution drift; validation agreement 93.8 % beside a flat loop is the
third measurement here that agreement on records is not closed-loop competence.

*Correction (D7, 2026-09-20) to 4.46:* the clause "its confidence ranks correctness at .654 against Jev's .81"
compared the 27B's figure on the D4 decisions with a subset figure that was never Jev's on those decisions
(method error 23). On the same decisions Jev ranks at .658 (strict) and .816 on the 126 single-answer decisions,
against the 27B's .676 and .876; ECE .070 against .028. On records the 27B is at least as calibrated as Jev. The
order-stability, latency and cost clauses stand; the calibration clause moves to 4.49.

*Addendum (E90b, 2026-09-20) to 4.48:* twice the teacher data (6,489 records) gives 83.3 % [78.1, 87.5] in the
loop, +3.7 [−3.3, +11.7] paired over the 1× head; recall 7/7, reroute 6/6, ambiguous 6/7, cosmetic 4/6, relabel
4/7, precedence 0/7. The reading residual does not move with data volume at this scale.

**4.49 · SUPPORTED (D7, 2026-09-20).** Calibration on records is not calibration in the loop, and the failure has a
direction. On the single-answer decisions each model steered into, Jev's stated confidence stays within .03–.07 of
its accuracy (ECE .08–.10; 545 and 123 decisions on two banks); the open 27B that was calibrated on Jev's recorded
states (ECE .028) becomes over-confident by .135 on its own (ECE .153; accuracy 88 → 72 %; 387 decisions); the owned
Laya head is under-confident by .18 on both (ECE .20–.22). The 27B's ranking stays excellent in its own states
(AUROC .90): below .7 it is right 19 % of the time, above .7 90 % — which is why a .7 gate recovers it (D4d, D4e).
Over-confidence is paid in violations, under-confidence in operator time; a fixed threshold means one thing only
for the model whose number holds under the shift. Boundary: 122–545 decisions per cell; the in-loop scorer treats
a foreign-object tray as blocked (declared); top-2 margin and entropy never beat top-1 confidence as a veto
predictor (free attack closed).

**4.50 · SUPPORTED, descriptive (D4e, 2026-09-20).** The unflagged surprises split by type. Ungated, Jev handles
foreign_object 10/13 and marking_conflict 8/13 where the 27B handles 2/13 and 1/13; both, and the rules, handle
qa_sticker (a precedence between two attributes) 2/14. Every surprise the ungated 27B handles, Jev handles (5/5);
Jev handles 15 the 27B misses. A .7 gate adds +11 foreign_object and +9 marking_conflict to the 27B and +1
qa_sticker; the oracle 40/40. Precedence between two cues is the reading residual in facts as in notes (E90b 0/7).

**4.51 · NEGATIVE with mechanism (E91, 2026-09-20).** The RLCD training recipe is not what the owned head needs.
On the same 421M encoder, records, seed and schedule, plain soft cross-entropy on the teacher's probability vector
agrees more with the teacher (91.7 vs 87.9 %) and drives held-out seeds 4.6 points better [+1.7, +8.3] than the
noisy-logit policy-gradient recipe (84.2 vs 79.6 %), with 40 % fewer pauses and more surprises handled (70 vs 62 %).
With soft targets the proper-scoring optimum coincides with the cross-entropy optimum; the sampled noise is
variance. Boundary: one encoder, 4,252 records, 3 epochs; the recipe may matter at other scales or with hard labels.

**4.52 · SUPPORTED (E91, 2026-09-20).** Store the distribution, not the label. A head trained on the teacher's
argmax as a one-hot label is calibrated in level (single-answer ECE .09, over-confidence +.02, after validation
temperatures of 1.3–1.6) and uninformative in ranking (AUROC .58 against .73–.79 for soft-target heads; two thirds
of its decisions above .9; wrong with median confidence .93), and drives worst (77.9 %, 8.65 pauses per episode).
The ranking a governor spends travels in the probability vector; a label log discards it. Addendum to 4.48: the
best owned head is now 84.2 % on held-out seeds, 3.7 points under the cloud teacher, at 90 ms on-device; every head
still reads the precedence note 0/7. A temperature fitted on validation or on new-seed teacher states halves the
heads' under-confidence (−.18 → −.09 to −.13) without moving the ranking (E91b, E91b2).

**4.53 · SUPPORTED with a boundary (D8, 2026-09-20).** The closed-loop calibration property is not a property of one
checkpoint. A second RLCD model from the same API (`jev-preview`), behind the identical request, matches
`jev-latest` on recorded decisions (82.2 vs 81.5 %, paired +0.6 [−0.8, +2.2]; 95 % agreement), is calibrated on
single-answer records (over-confidence −.06, ECE .10), and in its own states stays at **−.06** (ECE .08; 214
decisions) where the open 27B drifts to +.135; gated at .7 it handles the identical 30 of 40 surprises and lands
at 89.6 vs 88.8 %. Ungated it is slightly worse (82.5 vs 84.2 %, −1.7 [−3.3, −0.4]; 40 vs 50 % surprises; 21 vs
16 % order flips). Boundary: the two checkpoints are siblings from one vendor's family; this is evidence for the
family's training regime, not for every RLCD-trained model. Addendum to 4.49: two RLCD checkpoints on one side of
the shift, one open model on the other.

*Correction (method error 25, 2026-09-20) to 4.50:* the last sentence linked `qa_sticker` to the notes-bank
`precedence` event. They differ: `precedence` is a hand-while-carrying-a-heavy-fragile-part conflict whose remedy
(E76, 4.29) is a code-combined split question the E77 teacher lacks, inherited as 0/7 by every distilled head;
`qa_sticker` is a precedence between two visual cues. The 4.50 finding about the three surprise types stands.

*Addendum (E89c, 2026-09-20) to 4.45:* a second RLCD checkpoint (`jev-preview`) reproduces the annotator result to
within 0.2 points (70.5 vs 70.3 % window accuracy; boundaries 92.4 / 96.3; consistency 98.2 %) with the identical
confusions; the rule stays ahead at 75.5 %. The result is a property of the facts, not the checkpoint.

**4.54 · SUPPORTED (E91c, 2026-09-20).** The owned head reaches the cloud teacher. A 421M pretrained typed-decision
encoder distilled by plain soft cross-entropy from 6,489 of the teacher's typed records (4,252 + 1,800 on new seeds +
437 correction labels) drives 40 held-out seeds at **88.3 % [83.7, 91.8]** against the teacher's 87.9 %, paired **+0.4
[−0.8, +1.7]**, with the teacher's decisions per episode (10.4), pauses (1.27 vs 1.20), surprises handled (72 %) and
per-event profile exactly, at 90 ms on-device with no API call. Two independent levers added: soft distillation over
the RLCD recipe (+4.6 at 1×) and twice the records (+3.7 for the recipe head). Boundary: one head family, one cell,
40 seeds; the head inherits the teacher's one failure (precedence 0/7 — a governor rule, E92) and stays under-confident
by .09 on single-answer decisions after a validation refit; a temperature changes nothing in an ungated arm.

*Correction (method error 27, 2026-09-20) to 4.49, 4.52 and 4.54:* the owned head's "under-confidence by .18 / .09"
measured Laya's normalised-entropy score, not a probability. On the top-1 probability the soft-target heads are
calibrated within ±.06 on single-answer held-out decisions (the 2× head within .015, ECE .05, the teacher .04),
and the label-only head is over-confident (+.067, ECE .084) with the worst ranking (AUROC .56). The in-loop
finding of 4.49 (open 27B +.135; RLCD checkpoints within .02) is unchanged and is now stated on one quantity.
The 4.54 boundary "stays under-confident by .09" is withdrawn; the head's probabilities match its hit rate.

**4.55 · SUPPORTED (E92, 2026-09-20).** The one event every judge failed was a code-owned safety rule, and the rule
composes with every judge. A hand entering the corridor while a heavy fragile part is carried defeated the teacher
and every distilled head (0/7: they pause, the part slips). The governor rule "set the part down before pausing when
the held part is heavy and fragile and a hand is present" — written from facts the eye already emits — fires in
exactly those seven episodes for every arm, saves the part in all seven, adds +2.5 [+0.8, +4.6] to the teacher
(87.9 → 90.4 %), +4.2 [+0.8, +9.2] to the 1× plain-distilled head and +2.1 [+0.4, +3.8] to the 2× head, cuts
violations by a fifth, takes broken parts from .17 per episode to zero, and moves no other event. With the rule the
2× owned head equals the teacher with the rule, 90.4 = 90.4 (paired +0.0 [−1.3, +1.3]), on-device at 90 ms. The
event still scores 5/7 for every arm because the saved part is then sent to the wrong tray in the same two seeds — a
destination judgment, the next residual. Boundary: one rule for one event type; the rule was written after the
event was identified, which is the correction loop at the code level.

**4.56 · SUPPORTED (D7b, 2026-09-20).** Calibration transfers through plain distillation, not only accuracy. The
shipped owned head — 421M open encoder, plain soft cross-entropy on the teacher's probability vectors, no RLCD
reward and no temperature refit — is calibrated on the states its own actions created: over −.007, ECE .054 on 127
single-answer held-out decisions, against the cloud teacher's +.014 / .083 on the same bank and the open 27B's
+.135 / .153. Four of four pre-registered predictions held (pre-registered 23:14 PDT, before scoring). Boundary:
n = 127 in one instrument with one teacher; no interval computed on the ECE; the states shift but the world does
not, so this is not evidence about domain shift, which stays an open limit.

**4.56 · NEGATIVE with mechanism (E93, E93b, 2026-09-21).** A calibrated judge does not transfer to a new embodiment
by changing the facts. On a second body (Pollen's MicroDuck biped in a room with a person; the shipped walking policy
as the executor; facts, options and governor written in one night), the same API judge reaches the goal 75 % of the
time against 98 % for a rule program written for the anticipated cases, and comes within touching distance of a
standing person 19 times in 40 episodes against 3, by dithering between waiting and walking slowly toward a paused
person with no detour skill. Two quantities tuned in the cell did not carry over: the handoff threshold (τ = .7 sat at
the 38th percentile of confidence on the duck and paralysed the gated arms) and the calibration level (under-confident
by .13 against ±.03 in the cell). Two did: the confirm window's economics (violations .10 vs the gate's .35 at 60 % of
its operator time, τ set from the domain) and asking at a blocked door (10/10; no rule arm asked). The oracle reaches
100 % and handles 39/40 events, so the instrument is fair after method error 28. Boundary: one night of representation
work on the duck against twenty experiments' worth in the cell; that gap is the mechanism, and the recorded 1,873
decisions are the material to close it.

**4.57 · SUPPORTED with a boundary (E96, 2026-09-21).** On the second body the owned head reaches the rule program on
the bank it was distilled from and beats its teacher there — 95 % goal on the anticipated bank against the rules' 95
and the API judge's 60–75, with an ask at the blocked door in every episode and half the teacher's near-contacts — at
90 ms and no API call, from 4,027 recorded decisions. On the unseen bank it handles the event whose facts it had seen
(object in the doorway, 10/10) and none of the two events that require reading a note it never saw (0/10, 0/10, where
the teacher read them 5/10 and 9/10), and on those states it is confidently wrong (hit rate 8 % at a stated .70).
Distillation transfers behaviour, not reading. The confirm window recovers a third of the unseen events (16/30) at
15.5 operator seconds per episode, and its 73 vetoes are the correction data for the next round. Boundary: one head,
one body, thirty unseen episodes; the head's own-state probability is under by .23 on the anticipated bank.

**4.58 · SUPPORTED with mechanism (E98, 2026-09-21).** One correction round on the owned head's own visited states,
labelled by code's acceptable sets as uniform soft targets, teaches the copy the two notes it was blind to — right of
way 0 → 10/10 on fresh seeds (oracle 8/10), follow 0 → the instrument's ceiling (3/10 = oracle) — and un-teaches
decisiveness: the anticipated bank's goal rate falls 95 → 72 % (approach 10 → 1/10: it stands in front of a stopped
person for 90 s), the object event 10 → 2/10, six falls from start–stop chattering, top-1 probability .50 against a
hit rate of .96. The label form is the mechanism: a uniform target over an acceptable set that almost always contains
stop and wait teaches that stopping is as good as moving. Boundary: one head, one round, one body; whether the
right-of-way gain is reading or passivity is E100's question; the masked-target form is E101's remedy under test.

**4.58 addendum · attribution (E100, 2026-09-21).** The gain is reading, not passivity. With the operator notes hidden
from the same head on the same seeds, following drops 10/10 → 0/10 (`follow_person` 80 % → 0 % of decisions) and right
of way 10/10 → 5/10 with cut-offs in five episodes; the object event, which has no note, is unchanged (2/10 = 2/10).
Half of the right-of-way gain is general caution the round installed (5/10 without the note against 0/10 for the rules
and for the uncorrected head); the other half and all of the following are the note. So a correction round labelled
only by acceptable sets teaches the owned copy to read what its teacher read — at the price of decisiveness (4.58),
which the label form is expected to fix (E101).

**4.59 · SUPPORTED with a boundary (E97, 2026-09-21).** On real teleop-style demonstrations (Eidon's release, 13,451
household recordings), the calibrated judge triages recording quality zero-shot from eleven categorical facts computed
off the body-worn IMU alone: AUROC .78 against the dataset's own valid/flagged/invalid label, beside a hand rule at
.64 and the base rate at .50, in 0.11 s per call; at the dataset's real prevalence its stated probability is within
-0.027 of the truth. Boundary, twice: a logistic regression fitted on the same facts with 232 labels reaches .88
(facts beat model wherever code can fit, E89), so the judge's place is before the labels exist and in choosing which
recordings to label; and asked to name the chore from the same facts it is at chance (20 % vs 51 % for a centroid
classifier): the judge reads notes and options, it does not recognise activities from motion statistics.

**4.60 · SUPPORTED (E102, 2026-09-21).** On the second body with its skills fixed, the RLCD judge handles 29 of 30
fresh episodes of three situations no rule was written for (follow a note, yield to crutches, an object in the
doorway), above the truth-knowing oracle's 26 and above its own copy corrected on those very events (22); the rules
handle 1. On the anticipated bank the same judge reaches the goal 82 % against the rules' 95 and its uncorrected
copy's 95, walking into a child's metre in 13 episodes. Reading belongs to the judge and generalises; steady walking
belongs to the distilled copy; one correction round bought the copy reading at the price of walking (4.58). On
single-answer states the judge is right 100 % of the time at a stated .87–.89 on both banks; its copy before
correction is right 6 % at .71. Boundary: one body, one judge checkpoint, thirty fresh episodes per bank.

**4.61 · SUPPORTED with a named residue (E101, 2026-09-21).** A correction round whose targets are the owned head's own
probability vector masked to code's acceptable set (the operator's veto, keeping the head's preference order) gives
the copy its teacher's reading on the second body: 29 of 30 fresh unwritten situations, equal to the API judge (29),
above the truth-knowing oracle (26), with no API call in the loop and no start–stop falls; on single-answer states it
is right 98 % at a stated .98. Residue: the anticipated bank's goal rate stays at 70 % because one situation — a person
who walks up and stands still — is one where waiting forever is acceptable at every decision, so no veto ever says
"move on"; the corrected copy waits 90 s where its uncorrected self walked or asked. Progress is a preference the
acceptable set does not encode, so the correction round cannot teach it (E103 adds the clause). Boundary: one head,
two rounds, one body.

**4.62 · SUPPORTED with mechanism (E105, 2026-09-21).** On a body that carries on with its last command while the judge
thinks, decision latency is paid in reading and safety, not in time: with 3 s of think time the same judge's
unwritten-situation score falls 29 → 18 of 30 (following 10 → 4), near-contacts double and falls appear, while time
to goal does not rise. With 1 s it decides every 1.5 s instead of every 0.5 s and its anticipated-bank results equal
the rule program's (goal 95 %, child note 7/10 from 1/10) because it dithers less — fewer decisions were better
decisions there. Cadence is therefore a governor knob: fast where the scene moves, slow where it does not. The field
number that prompted this (a graph node that waits for its decision: 5.42 s with the 0.1 s judge, 8.79 s with a frontier
VLM) is the same latency paid in time instead. Boundary: one judge, one body; cadence and staleness not yet separated (E106).

**4.63 · SUPPORTED (E103, 2026-09-21).** On the second body, two correction rounds from the operator's vetoes alone — the
owned head's own probability vectors masked to code's acceptable set, with the set able to say "move on" after six
seconds before a still person — give the fleet's copy both halves at once: the rule program's walking on the anticipated
bank (goal 95 % = 95 %, child note 10/10, approach 10/10) and its teacher's reading on the unwritten bank (28 of 30
against the judge's 29, the oracle's 26, the rules' 1), with no API call in the loop and single-answer states right
100 % at a stated .998. Seven of seven predictions. The residue is one anticipated situation, a person crossing the
robot's path (2/10 for copy and teacher alike, 6/10 for the rules), which belongs to the governor. Boundary: one body,
one judge family, thirty fresh episodes per bank; the cross event unsolved.

**4.64 · SUPPORTED with a boundary (E111, 2026-09-21).** As a checklist verifier of 350 of its own episodes, the calibrated
judge answers four yes/no items per transcript in one 0.12 s call with honest probabilities (pooled ECE .08; AUROC 1.00 on
"handed to someone it should not have", .98 on "handed to the asker") and infers the item the transcript never states (a
fall, from the log ending early: 93 % right). Boundary: on every item the log states literally, a regex over the same
text matches or beats it, so a reward model built on the judge should hand literal items to code and keep the
inferential ones — and their calibrated probability — for the judge. One method error (35): a truth that mixed "was it
handed to the asker" with "was that allowed".

**4.65 · SUPPORTED with a boundary (E108–E110, 2026-09-21).** On a human-sized humanoid fetching an object and handing it to
a person, with a second person in the room, the calibrated judge handles the two situations that live in an operator's
note — a person on a call who must not be handed anything until she looks, and a child who asked for scissors — 10 of
10 each, where a rule program written for the anticipated situations handles 0 and 0 and hands the object to the wrong
person twenty times; it never hands the object to the wrong person. Where the rules were written it loses to them
(33–35 of 40 against 39). A one-second veto window that slows the walk instead of stopping it takes the combined arm
to the oracle's score on the unwritten bank (27 of 30) and 36 of 40 on the written one, at 20–24 operator seconds per
episode. Boundaries: one body whose walking policy cannot take a stop-start every second (method error 34), so asks
and dithering are paid in falls; a reaching child the judge alone steps around into (0/10); the owned copy not yet
distilled on this body.

**4.66** (2026-09-21 23:56 PDT, E114) On both bodies the rule programs, rewritten by their author after reading the unseen banks, match or
beat the RLCD judge (duck 29 = 29 on the fresh bank; humanoid 30 against 20) within fifteen minutes and under ten lines, with
the anticipated banks unchanged (95 % = 95 %; 39/40 = 39/40). The judge's value on situations no rule was written for is
time-to-rule plus the calibrated number a governor spends, not accuracy after the fact. Caveat: the banks' author wrote the
fixes; a second designer's bank is the open test. Method error 36 (doorway fact inside the kick zone) found by the rewritten rule.

**4.67** (2026-09-22 01:02 PDT, E115, E115b) The judge's recorded decisions on a new situation compile into a decision tree a person can
read as rules. Filtered by the operator's vetoes it beats the judge that produced it on the duck (30 against 29 on fresh
seeds; 20 scoped, under the doorway flaw) and, with a finer tree, matches the judge on the humanoid (20 = 20) at no
operator cost beyond the one ask a note requires and with no falls. Scoped by a novelty gate to states outside the old
vocabulary, the drafts leave the anticipated banks exactly where the frozen rules had them (36/40, 39/40). Conditions: most
decisions must survive the veto (78 % on the duck; 32 % on the humanoid starves the draft), and the judge's blind spots
compile unless vetoed first. A pre-registered set of six predictions went one of six; the follow-up three of four.

**4.68** (2026-09-22 01:51 PDT, E112) The owned copy transfers to the humanoid with the duck's result shape: distilled from the judge's
4,992 decisions it handles 35 of 40 anticipated situations (its teacher 33) at 80 ms and is blind to all three unwritten ones
(0 of 30, 20 wrong hand-overs); it falls 9 times where the judge fell 2, from alternating stop and walk, and a one-second veto
window removes every fall while its vetoes hand it the reaching child 10 of 10. Four of six predictions; the E96 over-confidence
signature did not appear because this bench's single-answer states are not the note states.

**4.69** (2026-09-22 07:35 PDT, E113) On the humanoid, one round of the operator's vetoes (1,405 visited states, masked targets) takes the
owned copy from 0 to 25 of 30 fresh unwritten situations, above the judge that taught it (19 on the same seeds), with no
wrong hand-over, no fall and no operator time at 87 ms; behind the one-second veto window 30 of 30 at four operator seconds
per episode; where the rules were written it stays above its teacher (36 to 33 of 40). Five of six predictions; the miss is
the reaching child at 5 of 10. The data loop that took two rounds on the duck closes in one on the second body.

**4.70** (2026-09-22 07:58 PDT, E117) On a decision-level picking station the judge ships nothing it should not on sixty unwritten lines
(reads the sleeve and leak notes 20/20 each; turns the recalled lot into a flagged exception) where the frozen rules ship all
sixty, at 11.1 seconds per line against the rules' 13.7 on the written lines, paired on the 32 both handle (amended 2026-09-25 00:17 PDT; the unpaired 10.9 against 15.4 overstated it, method error 53); it fails the double pick confidently (6 of 7 placed in
the customer tote at .73–.95) where the rules never do, and neither the gate nor the veto window catches a confident error.
Two of seven predictions; the bench has no physics and says so.

**4.71** (2026-09-22 08:00 PDT, E118) On the picking station the gated judge's escalation rate rises with the mix's difficulty (.24 → .34)
and its handled rate falls less than the rules' (.95 → .77 against 1.00 → .50), but its wrong picks are the same confident
double picks in every mix and it escalates 19 % of clean lines for nothing: a threshold is worth what the number's ranking is
worth, and here the ranking fails on one written situation. Three of four predictions.

**4.72** (2026-09-22 08:02 PDT, E119) On the picking station the rule program rewritten by its author after reading the unwritten lines
handles all 170 lines (written, unwritten, clean) with zero wrong picks at the frozen rules' speed, in three clauses and two
minutes; it ties the oracle. Two of two predictions. With E114, the time-to-rule reading holds on every bench with a rule program.

**4.73** (2026-09-22 11:01 PDT, E122b) On the picking station the judge's decisions on the unwritten lines, with the vetoed ones dropped
or replaced by the operator's answer, compile into a three-leaf rule that handles all 60 fresh unwritten lines with nothing
shipped wrong and no operator time at the rules' speed, tying the oracle and the programmer with hindsight; the draft from all
decisions copies the judge's exception habit (40/60, eight operator seconds per line). Caveat: the learned clause reads "a note
and the item in hand → return bin", true of this bank's three notes and not of notes in general. Three of four predictions.

**4.74** (2026-09-22 11:35 PDT, E116) A second masked correction round on the humanoid keeps round one's result (25/30 unwritten, 36/40
written, no wrong hand-over, one fall) and halves the veto window's operator cost (2.2 s per episode, 3 vetoes in 50 windows;
the window reaches 30/30), but does not move the reaching child (5/10 in both rounds): the acceptable set permits waiting,
so the labeller cannot teach moving on, the duck's E101 residue again. Four of five predictions.

**4.75** (2026-09-22 15:04 PDT, E120, E121) On the picking station the owned copy transfers whole (33/40 where the rules were written, the
judge's double-pick blind spot included; 0/60 and sixty wrong picks where they were not, at 60 ms), and one masked correction
round takes it to 60/60 on fresh unwritten lines with nothing shipped wrong, at fifteen operator seconds per line, because
the veto teaches which action was wrong and not which acceptable action is cheapest; the copy chose to ask. On this bench the
un-vetoed drafted rule (60/60 at no operator cost) is the better owner of the judgment. Six of six predictions.

**4.76** (2026-09-22 20:13 PDT, E124, E125) Two instrument iterations on the humanoid's one unsolved unwritten situation, the reaching child:
putting the child-zone rule inside the step-around skill removed every zone entry and produced a two-minute livelock (0/10);
adding a progress bound in the governor turned the livelock into three deliveries in ten with one zone entry, and the judge's
best unwritten score on the bench, 22/30. The residue is a preference the judge does not take from the note (slow and
straight, as the oracle does) rather than a missing rule. Two of six, then three of five predictions. *Amendment (2026-09-22 23:14 PDT, E130):* the 22/30 against R2's 20/30 and the reaching child's 3/10 against 0/10 are within the judge's measured run-to-run noise (five runs on these thirty seeds: 20–23; the child 0–3). What stands is structural: under R3 every reaching-child episode circled to the clock and under R3b none does.

**4.77** (2026-09-22 22:39 PDT, E123) On the picking station, one correction round labelled with the operator's replacement action (the
cheapest acceptable move at every visited state) gives the owned copy 60/60 on fresh unwritten lines with nothing shipped
wrong, no asks and no operator time at the rules' speed, where the same states with masked labels gave 60/60 at fourteen
operator seconds per line; the copy now beats the judge that taught it (40/60 at seven operator seconds) and ties the
hindsight programmer and the drafted rule. The label form decides what the copy learns; the veto says not that, the
replacement says this instead. Four of four predictions. Caveat: the replacement is the oracle's action in simulation and
the operator's takeover action in a fleet.

**4.78** (2026-09-22 23:10 PDT, E126 part 1, E129, E131) On the humanoid's bank v2, three situations that arise after the task has started
(the cup starts leaking in hand, the requester walks off, a second person asks for the cup), frozen rules and the rules
rewritten with hindsight for bank v1 hand the cup over wrongly thirty times out of thirty; the judge, reading a note left the
day each situation appeared, handles all thirty with no wrong hand-over and no fall, and once the bench's facts say the
requester has left (v2.1) it finishes all thirty, telling the operator as the note asks, at 2.7 operator seconds per episode.
The judge's ten unfinished episodes under v2 were a bench flaw (method error 43): a departing requester who never departed.
Rewording the done option (E129, four of five) changed nothing; fixing the facts (E131, five of five) changed everything.

**4.79** (2026-09-23 01:21 PDT, E126 part 2) On the humanoid's bank v2, the owned copies corrected on the earlier bank cannot read the new
notes: all three hand the leaking cup over and hand to the departing requester twenty times out of twenty (the third
situation they pass by habit), where the judge handles all thirty on the day the notes appear. Each correction round raised
the copy's stated confidence on situations it had never seen (.82, .88, .94 at the wrong hand-over; unacceptable decisions
under the window's .5 line 108, 36, 4), so the veto window's rescue shrank from 29/30 to 20/30 to 10/30. The calibrated
judge is the out-of-distribution reader, the copy the in-distribution owner, and correction erodes the calibration that
separates them. Six of seven predictions over E126 (the blindness prediction failed by its threshold, not its intent).

**4.80** (2026-09-23 03:23 PDT, E127, E133) The station's copy inherits the judge's double pick: at states that say holding two items and
heavier than expected it places the pair at a stated .58 to .92, through a correction round with replacement labels (4/10)
and the same round weighted four times (5/10), while a one-clause rule reads the fact ten of ten and the veto window at .5
catches none. Where the fact is hard and the pattern rare, the stated number is not a signal and the rule is the cheaper
owner; the judge and its copy own what the notes say and the corrections covered. Two of four and two of five predictions.

**4.81** (2026-09-23 05:46 PDT, E134) The station's copy learns the double pick from takeover data after all: thirty-three put-back records
at the two-items state, each counted four times, take it from 4–5 of 10 (E127, E133 with twenty-four) to 9 of 10 on fresh
written lines, 38 of 40 overall, with the sixty fresh unwritten lines still handled at no operator time. Forty more written
lines was the difference. Its calibration on the pattern is inverted, .39–.64 where it puts back and .75–.89 where it still
places the pair, so a handoff line would send right answers to the picker and no wrong ones; the one-clause rule remains the
cheaper owner with no residue. Four of five predictions. Amends 4.80: "neither learns it from the takeover data we have"
held for the data of E127 and E133 and not for twice that.

**4.82** (2026-09-23 05:48 PDT, analysis of E126 part 2's records) A copy-then-judge cascade on the copy's stated confidence does not work off
the copy's corrections: to route the uncorrected copy's twenty fatal hand-overs on bank v2 to the judge the line must sit at
.85 and send 91 % of all decisions; the twice-corrected copy's twenty are not all caught at any line below one, and at .95
it keeps one decision in twenty. The copy's number separates nothing where it was never corrected, and less with every round.
Descriptive, from records; no prediction was registered. What to test instead: a detector of "outside the corrections" that
is not the copy's own number (the surprise gate; the judge as a sampled auditor).

**4.83** (2026-09-23 10:11 PDT, E135) One replacement-label round on bank v2's takeovers makes the humanoid's copy whole on both banks: 30/30
on fresh v2 seeds with no wrong hand-over and no operator time (r2 on the same seeds 10/30, twenty hand-overs at .96), and
30/30 on v1 (r2 25/30), the reaching child 5 → 10 with zone entries 9 → 0, above the oracle's 27 and the judge's 20–23. Its
mean stated confidence fell on v1 (.77 → .71) rather than rising as the masked rounds had made it; the label form decides
what the copy learns and how sure it becomes. Three of five predictions, both misses in the copy's favour. Open: whether r3
is blind and confident again on a bank it has not seen, which needs a bank written by someone else.

**4.84** (2026-09-23 12:00 PDT, E136) The cascade that works is a novelty gate on the facts, not a line on the copy's number: the humanoid's
copy r2 behind a gate that routes any decision with a feature outside its training vocabulary to the judge handles fresh
bank-v2 seeds 30/30 (every decision routed) and its own bank at the copy's 25/30 with no decision routed, no false alarm in
1,226 decisions. With the notes hidden the judge alone still handles v2 30/30 from the facts (a cup that says leaking, a
requester that says gone), so on this bank the note bought speed, not correctness; the fact-level gate test was confounded
by a fact key rendered only on v2 (method error 45) and is re-run as E136b. Four of five predictions. *E136b:* with the leaked key counted as known and the notes hidden, the fact-level gate fires in every leak episode 17–22 decisions after the pick-up (when the cup turns to leaking), in every departure episode when she is gone, and never on the second asker; behind it the copy's 10/30 becomes 28/30. Three of four; the routed share (85 %) is the judge's slowness without a note, not false alarms.

**4.85** (2026-09-23 17:04 PDT, E137) The humanoid's blind-then-whole story replicates on the picking station where the new situation lives
in facts the copy's corrections never touched: on a mismatched label and a held lot the copies corrected on bank v1 ship
39–40 of 40 lines at a stated .80–.87, the frozen and hindsight rules ship all, the judge handles all forty from the note
with nothing wrong, one replacement round on thirty lines takes the copy to 60/60 with nothing wrong while keeping its old
lines, and a vocabulary gate flags every new-bank decision and none of the old. Two twists: the copies handle crushed
packaging 20/20 with no note read, because bank v1's leak correction taught "condition other than dry → return bin" and
the new value fell under it (blindness is about facts, not banks); and the judge reads "must not ship" and skips every
damaged line, nothing shipped and nothing returned (0/20 by the registered criterion, 0 wrong by the ledger). Four of six.

**4.86** (2026-09-24 03:17 PDT, E138 part 1) An open contrastive System One model (CLM-8B) with Jev's typed interface, run zero-shot on the
station's own decisions, is a lookup in the reader's seat: its choice is acceptable 12 % of the time at a mean stated
probability of .58 (over-confidence +.46, ECE .50, the reliability curve inverted in the middle), it loops on an action the
state's words resemble (scan the label again, 3,118 of 3,906 decisions) and hands every unwritten line to the operator
(60/60 handled, 60 asks, 20 operator seconds a line against Jev's 40/60 at 7.3), and on bank v2 it handles 16/60 with six
wrong picks where Jev handles 40 with none. The same interface, the same questions, ECE .02 against .50: the calibrated
number is a property of the model, not of the model class. Three of four scored predictions (one by the letter only);
whether post-training the heads on the fleet's records recovers it is E139. *Part 2 (humanoid):* zero-shot it chooses pick_up on 4,050 of 4,136 decisions from across the room, handles 7/30 on bank v1 (the operator's) and 0/30 on v2, hit rate 0.00 at a stated .55. Interface parity is not competence parity. E138 in full: three of six, one by the letter.

**4.87** (2026-09-24 07:05 PDT, E140, E141) Post-training the humanoid's exported walking policy by PPO on the decision layer's own command
stream, on a CPU overnight from the exported weights, fixes the fault it was given (standing speed .357 → .115 m/s, tracking
error .31 → .18, plain walking .22 → .12, no falls in a hundred fresh episodes) and breaks the code written around the fault:
under the bench's −0.2 stand command, written for the shipped body's creep, the fixed body walks backwards and the judge
falls from 20–23 to 10 of 30, the rules from 39 to 14 of 40; with the workaround removed the post-trained body makes the
rules whole (40/40, the blocked door handled for the first time). An EXPO-style bounded edit over the frozen policy gets
two thirds of the improvement (.162, .231) with no fall in 643 training evaluations against 44 for the direct fine-tune,
and stays inside the old contracts (rules 39/40 under either instrument). Five of seven and two of five predictions.

**4.88** (2026-09-24 11:14 PDT, E139) Post-trained for eight seconds on the same fleet records as the generative copy (the judge's decisions
plus the operator's replacement actions, embedded once), the open contrastive model's two 20M heads handle every fresh
unwritten line at no operator cost (120/120 on two line sets, where zero-shot they asked on every line and Jev handled 40)
with their calibration recovered from ECE .50 to .06, within .04 of the copy's; from identical records they miss the finer
endings the copy learned (bank v2 35 against 60: they return the wrong item and the held lot where the note asks for a
put-back and a skip; written lines 27 against 37), and behind the veto window reach 54 at nineteen operator seconds a line.
The calibrated number can be earned by the cheaper architecture on the distribution the records cover; resolution beyond it
is what the copy's capacity buys. Four of six predictions.

**4.89** (2026-09-24 11:26 PDT, E142) The simulator's tolerance, measured: with every body mass, all contact friction and every actuator gain
perturbed by up to ±20 % per episode the three walking policies keep their outcomes (falls 9 %, 4 %, 0 %; the stand-speed
ordering unchanged); at ±30 % the shipped policy and the direct fine-tune fall in 28 % and 32 % of episodes while the bounded
edit falls in 5 %; at ±50 % all but the edit fall in most. Post-training without randomization did not narrow the fine-tune
beyond its parent (equal falls at .3 and .5), Playground's randomization did not protect the parent at this range, and the
bounded edit over the frozen base is the most tolerant of model error. For a modeling pipeline: land those three parameters
within about twenty percent and the gait outcomes carry. 1 of six predictions, the misses in the post-trained policies' favour. *E142b (2026-09-24 11:37 PDT):* one family at a time at ±30 %, mass and friction alone cause at most three falls in a hundred for any policy; the actuator gains alone cause 21 % (shipped), 13 % (direct), 3 % (edit) and combine with the others to more than their sum for the fine-tune. Get the actuator model right; mass and friction may be rough. Four of five.

**4.90** (2026-09-24 11:34 PDT, E144) On the contrastive heads, as on the generative copy, the label form of the same 776 correction states
decides the operator's bill and the number's honesty, not the outcome: uniform, masked and replacement targets all handle
the sixty fresh unwritten lines with nothing shipped wrong, at 10, 13 and 0 operator seconds a line; the replacement is
slightly over-confident (+0.06), the masked slightly under, the uniform under-confident by 0.10 (ECE 0.16), a head
that does not believe its own right answers. Held-out agreement (97.2–97.6 %) separates none of them. 4 of six predictions.

**4.91** (2026-09-24 11:34 PDT, E143) With the −0.2 stand patch removed, the directly fine-tuned body still fails the phone situation 0/10 and
both post-trained bodies fail the departing requester (4 and 5 of 10), and the reason is the fault the bench was built on:
the shipped body's creep (0.13 m/s at a zero command) carried the robot inside the requester's 2.5 m noticing radius while the
judge "waited" and, during a failed out-of-reach pick-up's stand, into the pick-up's reach, and a body that truly stands does neither
(602 of 646 pick-up attempts fail: the same state and the same premature choice, seventy times over). Three of the fetch room's contracts were satisfied by the body's fault and not by code (method
error 47); post-training the fault away exposed every place the code leaned on it. The un-patched shipped body sits at the
noise floor on bank v1 (20/30), so the patch was never load-bearing there. Three of six predictions. *E147 (2026-09-24 12:11 PDT):* with the pick-up skill owning its approach the fine-tuned body's departures go 4 to 10 of 10 and its written bank 35 to 38 with the rules whole (40/40), and two more clock couplings surface: the leak onset timed from the pick-up charges a fast approach for a leak it could not see (seven hand-overs decided on an intact cup), and clock-triggered people and events move the cross, blocked and child-note outcomes with the body's speed (method errors 48, 49). Four of seven.

**4.92** (2026-09-24 14:03 PDT, E145) On the humanoid the open contrastive model's heads, post-trained for 21 seconds on the copy's exact
records, go from a lookup that picked up from across the room (7/30 and 0/30) to a copy that handles 26/30 and 30/30 with no
wrong hand-over and no fall, the reaching child included (10/10, from the copy's replacement round), and stay undecided and
uncalibrated: 59 % of decisions are stop, a hundred decisions and 53 s per episode against the copy's 24, 37 % of decisions
acceptable, ECE .25 and over-confidence +.20 where the same recipe gave .06 on the station. The cheap architecture learns
what to do from the fleet's records on both benches and learns how sure to be only where decisions follow from facts, not
from geometry and time; the generative copy learned both. Four of six predictions, one miss in the heads' favour.

**4.93** (2026-09-24 14:13 PDT, E143–E150) On a humanoid bench that no longer leans on the body (events triggered by the robot's state,
decisions scored on what the robot saw, no hidden motion, no stand patch; five revisions in a day, method errors 47–51),
post-training the walking policy makes the frozen rules whole (40/40 on the fine-tuned body against 39 on the shipped, the
blocked door 10/10 for the first time without a patch) and costs the judge: 37 → 30 on the written bank and 21 → 11 on the
unwritten, because its habits, learned on a body that crept (a wait outside the requester's noticing radius, a walk past a
standing person), meet people and wait too far on a body that stands still; the bounded edit sits between. The new-bank
situations are 10/10 with no wrong hand-over on every body. A fleet that post-trains its policy re-derives its skills'
contracts and re-corrects its decision layer on the new body. Five of eight predictions on the final run.

**4.94** (2026-09-24 14:45 PDT, E146) Six cumulative correction rounds of the station's owned model, each scored on the lines the rounds cover
and on a bank none of the first five touches: the expected calibration error on the corrected distribution falls .362 → .047
→ .013 → .008 while on the untouched bank it rises .307 → .331 → .374 → .399, the model's stated probability at its wrong
decisions there rises .62 → .81 → .87 → .90, and the operator's veto window, which rescued 34 of 60 lines from the
uncorrected model, rescues 0 after two rounds. The round that finally covers that bank restores it (ECE .117, handled 20 →
35, the window's rescue +19). Correction makes the number honest where it corrects and dishonest where it does not, and the
operator's safety net is what degrades; a falling intervention rate is therefore not evidence of a safer fleet unless an
untouched bank is scored every round. Five of six predictions; the same shape as the humanoid copy's three rounds (4.79). *E155 (negative):* the lost uncertainty cannot be put back through the loss. Smoothing the correction targets fifteen percent over the acceptable set moves the untouched bank's calibration error only .376 → .339 and the confidence at its wrong decisions .86 → .80, restoring two of the thirty-four lines the veto window used to rescue, and it pays for that by making the covered lines four times worse calibrated (.012 → .048); rewarding entropy does almost nothing. Every training example is by construction a state the model has evidence for, so no loss term can mark the regions it has none for. Support must be measured outside the model's own probability, which is why the novelty gate works. Three of seven.

**4.95** (2026-09-24 19:46 PDT, E151) On the post-trained humanoid the fleet's owned copy beats the cloud judge that taught it: 25/30 against
12/30 on a fresh unwritten bank (the judge fails the phone 0/10 by waiting outside the requester's noticing radius on a body
that no longer drifts in), 30/30 against 30/30 on the second fresh bank, and 32/40 against 30/40 on the written bank, at
80 ms and no operator time against 6.7 operator seconds an episode. The copy corrected on the **old** body already survives
the change; one further round on the new body's own episodes buys decisiveness rather than coverage (acceptable decisions
81 → 95 %, episode time 61 → 28 s), and behind a one-second veto window that copy reaches the oracle's 30/30 at 1.4 operator
seconds. Post-training the body costs a layer that reads from scratch and not a layer the fleet has corrected. Five of seven.

**4.96** (2026-09-24 20:40 PDT, E153) The whole post-training ladder on one humanoid bank never trained on, corrected on or scored before:
the frozen rules own the bank they were written for and nothing else (39/40, 10/30, 0/30, fifty wrong hand-overs); the cloud
judge reads what a note describes (37, 20, 30) at 2.8 operator seconds an episode; the copy distilled from it with no
correction is worse than useless off the written bank (2/30 and 10/30, forty wrong hand-overs); three rounds of the
operator's corrections make that same copy the best arm on the bench (38, 30, 30, no wrong hand-over, one operator second),
above its own teacher. Post-training the body then costs the judge ten episodes across the two fresh banks and the corrected
copy six, and a further round on the new body returns one. Two corrections to earlier claims fall out of the same table: the
copy's advantage over the judge is no cloud call and a third of the operator time, not latency (both are 90 ms per call
here), and the oracle is not the ceiling on the written bank because its own body drifts into the cart while it waits.
Four of eight predictions. *E154:* reusing the last decision when nothing the model reads has changed saves 5–24 % of model calls with every handled count inside the noise floor and no new wrong hand-over, fall or operator second; the saving tracks how much of the episode has a person near the robot (5 % on the people-heavy written bank, 24 % where the scene holds still), the same conclusion Argon reach at the action layer by tightening their skip threshold sevenfold in human-occupied scenes. The number is a property of the deployment's scene mix, not of the method. Five of six.

**4.97** (2026-09-24, analysis of E153 and E151; no new runs; **amended 2026-09-25 00:01 PDT after the paired test, see below**) The
decision seat costs time and correction buys back the time that failure wastes. Paired on the 36 written-bank seeds both arms
handle, putting the judge in the seat costs **+34 s mean and +7.2 s median** an episode over the frozen rules and is faster on
only ten of thirty-six: that is the price of reading, and this programme had never quoted it beside its coverage wins. A miss
is the expensive episode, not the short one — the judge's failures cost 122 s against 25 s for its successes — while the
frozen rules **miss in 15 s, faster than they succeed**, because a wrong rule ships the wrong action without hesitating. The
model's failure mode is dithering; the rule program's is confident wrong action. Correction therefore makes the fleet's cost
per episode fall (57.8 → 25.6 s on the fresh bank) **because it removes failures, not because the copy decides faster** — on
shared handled seeds the corrected copy is 4.1 s slower than its teacher and faster on ten of twenty. The corrected copy does
not reach the ceiling: the oracle is faster on 27 of 30 shared seeds.

**4.98** (2026-09-25 00:01 PDT, paired re-analysis of E153; no new runs) A correction round on a body that has changed underneath buys real
per-episode speed, paired and on two independent banks: **17 of 19** shared handled seeds faster on the fresh v1 bank
(50.5 → 30.3 s) and **27 of 30** on the fresh v2 bank (28.4 → 23.9 s), with decisions per episode falling 115 → 46 while
handled moves 24 → 25, inside the noise floor. The round bought decisiveness rather than coverage. This is the shape Argon
report for intervention data at the action layer, measured here at the decision layer against a paired control rather than an
average. Supersedes the unpaired 2.3× distillation speed-up withdrawn in method error 53.

**4.99** (2026-09-25, E157) The operator's one-second veto window is recoverable after correction has eaten it, and the lever
is the form the intervention is written down in, not a confidence threshold and not more data. Same 1,493 correction records,
same four files, same training, scored on sixty station lines the corrections never touched: the window rescues **+0** lines
for a head trained on the operator's replacement action, **+3** for one trained to ask, and **+14** for one trained on the
operator's veto, which also carries the best calibration of the three (ECE .261 against the replacement head's .376, and
probability at its wrong decisions .71 against .86). The station is deterministic, so this is not noise. It costs 24.3
operator seconds a line, making the capability a priced option rather than a lost one. Amends claim 4 from *lost* to
*recoverable at a price*.

**4.100** (2026-09-25, E157) Training a head to escalate teaches it to escalate but not where. One-hot on `ask_operator` at
exactly the states where the head was vetoed makes it ask on fifteen of sixty untouched lines against the baseline's zero,
and on twenty-eight of the sixty lines it already handles perfectly — so it asks more often where escalation is waste than
where it is needed, and its handled count does not move at all (20/60, exactly the baseline). The bill is 9.3 operator
seconds a line on lines that needed nobody. The ask label teaches *escalate once and stop* (one ask in each of fifteen
episodes); the veto label teaches *that one is wrong, keep trying* (4.7 asks in each of six). Pre-registered P157.1 and
P157.2 both missed; P157.4, which predicted the price would be paid in the wrong place, held.

**4.101** (2026-09-25 08:43 PDT, E158) The headline claim survives a bank its author did not write. On five situations in the humanoid
fetch room, two of them written by a model given only the room, the fact list and the action list, which read no file and
never saw the rule program, the banks, the scoring sets or any result, the judge handles **48 of 60** against the frozen
rules' **24**, with the oracle at 60. On the blind author's two situations alone the judge takes 24 of 24 and the rules 12.
The gap is smaller than on the banks I wrote myself, as pre-registered. **Read as "not overturned", not as "confirmed":**
every cell is 0/12 or 12/12 because seeds within a situation vary only by position jitter, so the effective sample is five
situations, not sixty trials.

**4.102** (2026-09-25 08:43 PDT, E158) A note that contradicts every sensor is still read and still acted on, and it costs. Where the
doorway reads clear, the requester is correctly flagged beyond it, and only the operator's note says the hall is wet, the
judge hands the object to a person in the room who never asked, **12 of 12**, against the frozen rules' 0. I pre-registered
60 % that it would fail this and it did not. The price is 67.0 s and **28.7 operator seconds** an episode against the
oracle's 8.2 s and zero: eight times the time and half a minute of a person's attention to act on one sentence. Every note
situation in this programme before this one *supplemented* what the robot could see; this is the first that *contradicts* it,
and the blind author found that hole in three minutes.

**4.103** (2026-09-25 08:43 PDT, E158) The operator's one-second veto window is a switch on this bank, not a safety net. The same window
takes *someone else is already holding the object* from 0 of 12 to **12 of 12**, and takes the contradicting note from 12 of
12 to **0 of 12**, burning 92.2 operator seconds an episode and hitting the time ceiling on all twelve. It rescues the
failure whose shape is *not asking* and destroys the one whose answer is a hand-over to an unexpected person, because its
proposals are about motion and it keeps re-proposing motion. First time in this programme the window has made an arm strictly
worse on a situation. Whether this is a real interaction or the confirm wrapper's known quarrel with this body's gait (E110)
is unseparated and is the next run. Amends claim 2.

**4.104** (2026-09-25 08:43 PDT, E158) Two authors who could not see each other's work independently wrote the same situation — *someone
else is already holding the object* — and it is the one nothing handles. The frozen rules, the judge and the fleet's own
corrected copy all take 0 of 12, and all three fail identically: they never terminate, running every one of 36 episodes to
the 120 s ceiling at 173 to 239 decisions with **zero asks**. Independent convergence is evidence the gap is real rather than
an artefact of knowing what the rules cover, and the failure mode is one the blind author had named for a different
situation.

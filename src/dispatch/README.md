# Dispatch shell

Decides **autonomous / supervised / hand off** before a task runs, from the
state a fleet already has. Evaluated by **total operating cost** against dumb
dispatchers -- never by accuracy against a label.

## Point it at your data

Build one `TaskState` per pending task. Every block is optional; put in
whatever you actually know. Names matter -- the model reads them.

```python
from dispatch import prepare_state, TaskState, ask, decide_by_cost, cost, evaluate, threshold_on_history

st = TaskState(
  task={"spec": "restock tote 4B, contents fragile", "type": "pick_place",
        "seen_at_this_site_before": False},
  site={"rules": ["no autonomous ops within 3 m of loading dock after 16:00"],
        "conditions": "floor wet near bay 2", "local_time": "16:20"},
  robot={"attempts_this_task_type_here": 20, "succeeded": 17,
         "operator_note": "drifting left since 11:00"},
  operator={"available": 2, "of": 3, "robots_per_operator_now": 8})

ans = ask(st)                      # one call: P(success), action, recoverability, rule conflict
action, why = decide_by_cost(ans)  # argmin expected cost under YOUR cost model -- no thresholds
```

## Do not gate on hand-set confidence thresholds

`decide()` (fixed floors, the docs' pattern) is kept for comparison. On the
DROID smoke test it cost **3x** more than `decide_by_cost()`: thin state gives
low confidence, and a fixed floor routes every uncertain task to the expensive
branch even when the cheap branch has lower expected cost. If you have a cost
model, use the probability *as a probability* and skip thresholds entirely.

## How to write the state — learned from the scenario suite

These came out of `python -m dispatch` (18 constructed scenarios, answers
correct by construction), not from intuition:

1. **Encode hazards as rules, not conditions.** The same wet floor + 18 kg load
   gave P(success) **0.79 as a condition and 0.11 as a rule**. A rule fires at
   ~0.96 when its condition is met and ~0.15 when it is not — including time,
   distance, and staleness — so it is safe to state rules with conditions.
2. **Never pass a rule that is not in force.** A rule annotated "(withdrawn)"
   still fired at 0.52. Filter rules by validity in code before building the
   state; do not ask the model to parse revocations.
3. **Layout does not rescue a buried hazard; a rule does.** The same bearing
   fault scored conflict 0.49 buried in a nine-clause note, 0.63 as the only
   note, and **0.94 with a matching rule in force** — and 0.10 with the rule
   but no fault, so the rule is read against its condition. Keep notes short,
   and have code promote known hazard patterns into rules.
4. **Do the arithmetic in code.** The model read dates, times, distances,
   double negatives and contradicting rules correctly — and blurred at an
   exact boundary (10.0 kg vs "over 10 kg" → 0.57), did not convert units
   (22 lbs fired a kg rule at 0.85), and let a rule about robot R-7 depress
   R-3's P(success) by 18 points without tripping the conflict flag. Evaluate
   thresholds, normalise units, and filter rules by entity and validity
   **before** building the state. Irrelevant information is not neutral.
5. **Keep the model's judgement for what code cannot do.** Time parsing
   ("4:20 PM"), double negatives, and a note that contradicts a strong history
   were all handled. Structural hygiene — which rules apply, what is current —
   is your job.

## Evaluate honestly

```python
eps = [(state, hist_rate, succeeded), ...]   # hist_rate: leave-one-out, no leakage
for d in [always_autonomous, always_handoff, threshold_on_history(0.8), jev_dispatcher()]:
    total, by_action = evaluate(d, eps)
```

Edit `COSTS` to your operator rate, handoff duration and failure cost. They are
stated assumptions and the ranking of dispatchers depends on them -- that is a
feature: it tells you which cost, if any, the model's judgement is worth.

## What the DROID smoke test is

Three sites, two operators, no rules, no notes. State is three numbers. On
three numbers a threshold is the right algorithm and the shell should tie it.
The smoke test proves the harness runs end to end; it validates nothing about
dispatch and is labelled accordingly.


## The two-pass rule, measured

The five state-structuring rules above are implemented in `prepare.py`.
Same 25 scenarios, same model, same questions:

| | pass |
|---|---|
| raw state → model | 17/25 |
| `prepare_state(state)` → model | 24/25 |

Seven fixed, none broken. The one remaining failure is a judgment call the model
arguably gets right. `python -m dispatch` runs with preprocessing by default;
`python -m dispatch --raw` shows the difference.

Extend `HAZARD_RULES` and `CONDITION_RULES` per fleet — the patterns shipped here
match the constructed scenarios, not your operators' phrasing. That is the part
that needs real notes.


## Three layers, one model (E58)

```
state ──► Jev, EXTRACT ──► code ──► Jev, JUDGE ──► argmin expected cost
```

`prepare_state_jev` asks one sharp categorical question per rule (*does it bind
this robot / task / place / time, given the notes?*), per note (*current
unresolved fault? which part?*), and per non-normal condition (*surface
hazard?*) — all in one parallel call. Code drops rules that do not bind,
promotes faults to one-line rules, converts units and evaluates thresholds.
The judge then sees a clean state. `python -m dispatch --jev`.

| arm | pass (34) |
|---|---|
| raw | 24 |
| regex pass one | 31 |
| Jev pass one, no regex | 31 (stable; one knife-edge flip to 32) |

Same count, but the Jev arm needs no patterns and read every held-out
rewording (lifted, unit R-7, recalibrated-and-verified) at ≥ 0.81.

**Because the model cannot generate, use a choice where you would want a
summary.** "Which part?" → `drivetrain/wheel` → a one-line rule. Quoting the
note into the rule re-buried the hazard (P .37 → .09 once fixed).

### Known gaps (do not paper over these)
- Recurrence reads as resolved: "seized up twice, freed by hand both times" →
  `resolved_or_none` 0.86. Needs a third category (intermittent/recurring),
  tested on held-out paraphrases, not a reworded prompt.
- Task-type scope belongs in code on the structured `task.type` field. The
  model sided with the spec text ("move tote" is a carry) over the type field.
- `decide_by_cost` never returns handoff with the shipped costs (supervised is
  always cheaper) and does not read operator availability. The action space
  has no "wait".
- One phrasing per category; run-to-run noise in P(success) is ±0.08. Margin
  claims need paraphrase sets and repeats.


## Where it stands (E61, 2026-09-15)

| set | judge alone | regex pass one | Jev pass one (final) |
|---|---|---|---|
| 34 constructed scenarios | 24 | 31 | **32 / 32** (two repeats) |
| 35 paraphrases × 2 repeats | 50/70 | 53/70 | **66/70** |

The four remaining failures: two constructed answers that are contestable
(first-time-at-site with a 38/40 record; "move tote" typed as pick_place while
a carry rule is in force) and two wordings the shell itself flags as ambiguous
("R7: supervised only…", "the dock restriction was lifted…") — see
`trace["ambiguous_rules"]`. Surface those to whoever writes the rulebook.

### Supply the vocabulary
The largest single fix in this line was not a threshold or a prompt — it was a
missing *category*. "Seized up twice, freed by hand both times" read as resolved
until `intermittent_or_recurring` existed as a choice; then 12/12 fresh
recurring wordings were caught and 0/10 resolved-with-history controls were
touched (E60). When this model looks wrong, check whether the answer it needed
was on the menu. It cannot write the option it is missing; you have to.

### Reading the ambiguity flag
A rule whose verdict is split (no option > .6) or `unclear` > .35 is kept
(fail-safe) and listed in `trace["ambiguous_rules"]`. On the paraphrase set
this flagged exactly the two wordings that failed and none of the 33 that
passed. It is free — it falls out of the extraction call already being made.


## Building the vocabulary from your own notes (E62–E63)

The extraction questions above carry a hand-written menu. A fleet does not need
to write one first. Run a first-draft menu over the notes you already have,
keep the full distribution, and look at the descriptions where no option
clears 0.5: on 1,233 real AV disengagement reports that was 6.8%, and the splits
clustered into three nameable concepts the menu lacked. Proposing them from
half the splits resolved 50% of the other half (re-asking the old menu: 2%)
and left 86% of clear cases untouched. `src/e62_vocab.py`, `src/e63_vocab_heldout.py`.
Split rate is a property of the writer: formulaic notes 0%, narrative 16–21%.

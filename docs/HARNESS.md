# The harness — a walkthrough

What this is, what it is made of, how each piece gets better, and how the loop that makes them better
eats itself if you are not watching.

---

## What a harness is

A robot policy takes an observation and produces motion. That is all it does. It has no memory of what
it was asked to do, no notion of whether the plan still makes sense, and no way to ask for help.

A **harness** is everything around that policy which turns it into a system that can be given a job.
The policy stays frozen — you never retrain it, you may not even own it — and the harness supplies
what it lacks.

The reason to build the harness rather than a better policy: **the policy boundary is moving on its
own.** Reasoning models get better every quarter and so do action models, pushed by labs with orders of
magnitude more compute than anyone reading this has. A harness built around a particular model's limits
is obsolete when that model improves. A harness built properly absorbs the improvement for free.

> **The bet is not "our model is better." It is "our stack gets better when everyone else's models do."**

---

## The composable pieces

Seven responsibilities. Each is a slot with an interchangeable implementation, and each has a specific
failure the whole system inherits if it is missing.

| piece | what it does | what breaks without it |
|---|---|---|
| **Planner** | holds the goal across time and decides the order of work | the system re-decides what it is doing every tick. Measured: a destination supplied by code held for **24 decisions**; a model asked to choose its own target re-picked every **3.1** |
| **Memory** | carries what was observed but is no longer visible | every trip re-observes from scratch, and anything that changed while the robot was elsewhere is invisible |
| **Staleness** | notices that what it believed is no longer true | the plan proceeds confidently against a world that moved |
| **Enumerator** | decides which actions are possible right now | either the right action is never offered, or the set is so narrow that no judgment is possible. A vision-language enumerator offered **no acceptable action on 13.2 %** of decisions |
| **Scorer** | picks one of the offered actions | the system needs a hand-written rule for every situation, and rules only cover what someone anticipated |
| **Escalation** | decides when to involve a person, under a queue | "ask a human" is treated as free and instant. It is a queue with a service rate, and at **one operator to eight robots** a system that asks loses five episodes in twenty while rules that never ask lose none |
| **Governor** | owns safety, and stays code | the safety argument is a model output nobody can read |

**Two things are infrastructure rather than slots**, and both earn their place:

- **The contract.** Every skill declares a name, typed parameters, a precondition, a postcondition, a
  goal and a cost, verified against the bench's own option set on **560 of 560** states. Before it,
  every cross-layer bug was two layers disagreeing about one word.
- **The record.** Every decision is written down with its options, its choice, its confidence and its
  outcome. This is not logging. **It is the training set**, and the next section is why.

---

## The virtuous loop

The loop this whole design exists to create:

```
     the fleet operates
            │
            ▼
   every decision is a typed record ──────┐
            │                             │
            ▼                             │
   failures and operator takeovers        │  free labels — nobody
   become labelled examples               │  annotates anything
            │                             │
            ▼                             │
   the small components post-train ───────┘
            │
            ▼
   fewer interventions needed
            │
            ▼
   one operator covers more robots
            │
            ▼
   more robots deployed ──▶ more records ──▶ (back to the top)
```

**The reason this is affordable: every learnable piece is small, because the big models are frozen by
design.** The frontier model is outside the loop; the body is somebody else's. What is left to learn is
the harness, and the harness is cheap — a 421M scorer head, a binary staleness classifier, a policy
over a queue.

Each piece has its own free label source, which is what makes the loop turn without an annotation
budget:

| piece | where its labels come from, for free |
|---|---|
| Scorer | operator corrections — a veto is a label |
| Staleness | retroactively: the record knows exactly when a belief turned out wrong |
| Enumerator | whether an offered option turned out acceptable **and executable** |
| Planner | episode outcomes, over orderings |
| Escalation | operator seconds spent and violations incurred, under the queue |

Measured, on the scorer: naive distillation from a teacher fails — 85 % agreement with the teacher,
**59 %** on held-out seeds, collapsing onto one action. One round of teacher labels **on the states the
student actually visited** takes it to **75.8 %**. And those visited-state labels beat **twice the
teacher's own data**. Which is the loop's core claim in one result: *the fleet's own trajectory is
worth more than more of the teacher.*

---

## How the loop eats itself, and the fix

This is the part that is usually left out, and it is the most important thing measured here.

**Correcting a model makes its number honest where you corrected and steadily dishonest where you did
not.** Over six rounds of operator corrections, calibration error on the corrected lines fell from
.362 to .008 — and on a bank the corrections never touched it **rose** from .307 to **.399**, while the
model's confidence in the places it was wrong climbed. The operator's veto window went from rescuing
**34 of 60** lines to rescuing **none**.

> **A falling intervention rate is therefore not evidence of a safer fleet.** It is evidence the fleet
> stopped asking about the things it was corrected on, which is not the same thing.

Two fixes, both measured:

1. **Score a bank the corrections never touch, every round.** Without it the loop's own metric improves
   while the system gets worse off-distribution. This is a process requirement, not a model change.
2. **The label form is a lever.** On lines the corrections never touched, a head trained on the
   operator's *replacement action* rescued **+0**; the same interventions written down as **vetoes**
   rescued **+14 of 60**, and carried better calibration. So how an intervention is recorded decides
   whether the safety net survives the next round.

---

## What is built, and what is not

The apparatus exists: one runner takes five swappable slots on a command line — planner, enumerator,
operator, scorer, skill library — with dosed fault injectors for three of them, postcondition
attribution so a failure lands on a named layer, and a gate that refuses to run an experiment until an
arm that ignores the intervention entirely actually fails.

**Four gaps stop it covering the whole harness:**

1. **Memory is not a slot.** It exists on one bench and cannot be swapped or ablated, so the control
   that matters — identical harness, no carried state, re-observe everything — has never been run. Until
   it is, "memory helps" is not a claim.
2. **Staleness is conflated with the planner.** "Held the goal perfectly and never noticed the world
   moved" is a specific, likely failure mode that currently cannot be expressed, let alone measured.
3. **The dose gate covers one slot, not all of them.** It should be a precondition of running rather
   than a convention. The reason this matters: four of five conditions on one bench were found to be
   **inert after six predictions had been registered against them**, and elsewhere 81 model calls bought
   exactly what zero calls bought.
4. **There is no sweep.** Every comparison so far was hand-assembled, which is why several turned out
   not to be matched and had to be withdrawn.

Closing those four is what turns this from a set of experiments into a loop you can iterate in: pick a
slot, swap one implementation, let the rig prove the dose matters or refuse to run, sweep, and read the
attribution.

---

## What this does not claim

Nothing here says what the right implementation of any slot is. Several candidates measured here lost,
and the record says so: a calibrated gate's advantage over a rate-matched control is real on one bench
and unresolved on another; a raw threshold transferred nearly as well as a calibrated one for behaviour;
an attempt to show physical thresholds transfer worse produced an interval spanning zero.

**The harness is the position. What goes in the slots is open — including whether a calibrated decision
model belongs in the scorer slot at all.**

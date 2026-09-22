# What this work is, and why, in plain words

**What we are doing.** Robots that work around people stop when something unexpected happens, and a human takes over.
A company running a fleet of such robots pays for that human attention by the second, and the unexpected situations
are exactly the ones nobody wrote a rule for. We measure whether one kind of model can sit between the robot's
controller and the human operator and make more of those moments go right: a model that reads a short description of
the situation and a small list of allowed actions, picks one, and says how sure it is, honestly. (The training method
behind such models is reinforcement learning from calibrated decisions; the model we test is TypeSafe's Jev.) And we
measure whether the company can then own that judgment: a small model of its own, trained from its robots' own
decisions and its operators' corrections, running on the robot, so it stops paying per decision.

**Why this, and not a bigger model or better rules.**

1. *The number is the product.* A hand-off policy ("ask the human when you are less than 70 percent sure") only works
   if 70 percent means the same thing every time. An open model of similar ability keeps its accuracy but its stated
   sureness drifts by 13 points on the situations its own actions create; this kind holds within 2. Every saving in
   operator time we measured comes from spending that number: propose and wait one second for a veto instead of
   asking, gate only the unflagged surprises.
2. *Rules win where they were written, and only there.* On situations the rule program was built for, it beats the
   model. On situations nobody wrote a rule for, the model handled 29 of 30 and the rules 1 of 30. A fleet's costly
   moments are the second kind.
3. *Every decision is a record, and every takeover is a free label.* The model returns a probability for each option,
   so the fleet's own operation produces training data. The small owned copy reaches the cloud model on both robots we
   tested, and operator corrections alone, written the right way, teach it to read the notes it was blind to.

**How we test it, so a skeptic can check.** Two simulated setups with a person in the scene: a sorting cell where a
hand enters the workspace, and a small walking robot crossing a room. A frozen hand-written rule program is the
opponent. A cheat that sees the true state marks the best possible score. Every prediction is written and dated before
its run; the failed ones stay in the record, along with the mistakes of our own that we caught. More than a hundred
runs.

**What we found, in five lines.**

- The model beats the rules only where no rule was written, and loses to them where one was. That is the honest shape
  of the value.
- Its stated sureness stays honest on the states it creates; an open model's does not.
- The owned copy matches the cloud model on both robots, and after two rounds of operator corrections it walks like the
  rule program and reads like the model, with no cloud call.
- How you write a correction decides what the copy learns: label "all acceptable moves are equal" and it forgets how
  to walk; keep its own preferences and remove only the unacceptable ones and it learns to read.
- On a moving robot, a slow decision costs safety, not time: three seconds of thinking doubled close calls. How often
  to ask the model should itself be a safety decision.

**What it means for a fleet, in practice.** Keep the rules and all safety in code. Put the model in the seat for the
situations no rule covers. Spend its number with a one-second veto window rather than a four-second ask. Log every
decision with its probabilities. Turn every takeover into a correction, written to keep the copy's preferences. Own
the copy.

**What we do not claim.** All positive results are in simulation we built with ground truth we defined. The one
real-data result is quality triage of recorded demonstrations, not control. The model family is one vendor's. It is
not the accuracy leader anywhere; its edge is a number a governor can spend, at a tenth of a second per decision.

Evidence for every sentence: the [README](../README.md), the [claims ledger](../notebook/CLAIMS.md), the
[lab notebook](../notebook/LAB-NOTEBOOK.md).

**Why this kind of model and not a frontier model like Astra.** Not because a frontier model judges worse. The seat needs
four things and a frontier model fails three: speed (a tenth of a second against seconds, and seconds cost safety on a
moving robot), an honest number as its native output (a frontier model's confidence is a sentence), cost (a fraction of
a cent against cents, at a hundred thousand decisions a robot-day), and ownership (a 421-million-parameter copy the
fleet can retrain and run for free). Frontier models belong outside the loop: writing the rules, translating the world
into facts once, teaching. We have not put a frontier model in the seat ourselves; that is the first thing on the list.

**What to test next.** A frontier model in the seat at its own latency; a frontier model as the copy's teacher; a
human-sized body (an open humanoid walking policy already runs here) in a home room and a store aisle; one operator for
many robots; real takeover logs as the corrections; deciding less often on fresh facts; the open 27B on the same body;
a twin of the deployment site as the bench's world; the rest of the real recordings; the one unsolved crossing
situation as a safety rule. Each is listed in the README with what it would show alone and in combination.

**How this could be unfair.** We wrote the rule programs ourselves and froze them while the judge's inputs improved; the
unseen situations lean on notes, which is what the judge reads; the owned copy learns our own labels and is tested on new
runs of the same situations, not on new situations; the benches changed between rounds after we saw results, though every
change was announced before the next run and the baselines were re-run on it; the open 27-billion-parameter model was
tested through a readout we built; and ten runs per situation cannot tell 33 from 35. The claims rest on the effects
that survive all of this: 0 of 10 against 10 of 10, 1 of 30 against 29 of 30, a number that holds within .02 against one
that drifts .135. Next on the list: write the rules a second time after seeing the unseen situations, so the sentence
becomes "the judge handles a situation before its rule exists; once written, the rule wins".

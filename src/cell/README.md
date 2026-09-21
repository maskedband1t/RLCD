# E71 · the sorting cell

A fleet-shaped closed-loop instrument: a tabletop cell in MuJoCo where a kinematic gripper sorts six parts into
colour trays and an inspection tray while situational exceptions arrive — damaged and fragile parts, a person's hand
entering the corridor, a blocked tray, a heavy part that slips, an unknown object — plus one text-borne event per
episode that the frozen rule policy was never written for (a tray relabel, a recall, a cosmetic override, a reroute,
a precedence conflict, an ambiguous instruction). Code owns every number: waypoints, speeds, release heights, the
impact threshold that breaks a fragile part, the slip timing, the pause rule, perception noise and delay.

| file | job |
|---|---|
| `scene.py` | MJCF builder; every geometric constant |
| `world.py` | physics: weld grasp, release, impact-speed breaking, contact with the person hand, tray/rim/floor readout |
| `episodes.py` | seeded episode specs; anticipated exceptions; the unanticipated event bank with five wordings each; ground truth (destination, manner, must_ask) derived from the event semantics |
| `eye.py` | imperfect perception: categorical facts, damage detection P=.85 / false alarm .10, hand detection delay 0.2 s |
| `executor.py` | skills: place (normal or gentle), set down, regrasp, pause, wait, ask |
| `operator.py` | the oracle operator (ground truth) — used as the `oracle` arm and to answer `ask_operator` |
| `policies.py` | one option enumerator (code's, with predicted effects); arms `greedy`, `rules` (frozen at commit 0fc9493), `lexical` (regexes from wording 0 only), `rules_ask` (program's abstention rule), `jev`, `jev_gate<τ>`, `oracle` |
| `harness.py` | the episode loop: events, slip model, interrupts, decision points, metrics |
| `run.py`, `analyze.py`, `decision_eval.py`, `render.py` | CLI, pre-specified analysis, decision-level calibration readout, contact sheets |

Reproduce the no-key arms:
```bash
PYTHONPATH=src python -m cell.run --arms greedy rules lexical rules_ask oracle --seeds 0-39 --out results/cell/e71_baselines.jsonl
PYTHONPATH=src python -m cell.analyze results/cell/e71_baselines.jsonl
```
The Jev arms need `TYPESAFE_API_KEY` in the environment (never in a file); every call is recorded to a jsonl for replay
and for the owned-head experiment (E2). Pre-registration and results: `notebook/LAB-NOTEBOOK.md`, E71.

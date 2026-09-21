# Models

Weights are not stored in git (1.7 GB each). Each checkpoint is reproducible from the committed records with the command shown; a hosted copy will be linked here when uploaded.

| checkpoint | what | held-out loop (seeds 40–79) | reproduce |
|---|---|---|---|
| `laya_v2_ce_soft_2x` | **the owned head** — Laya (ModernBERT-large, 421M) distilled by plain soft cross-entropy from 6,489 teacher records | **88.3 % [83.7, 91.8]**; with the governor rule 90.4 % | `python src/cell/e90_laya_head.py train --recipe ce_soft --out results/cell/laya_v2_ce_soft_2x --extra-records results/cell/e81_jev3_extra_record.jsonl results/cell/e90_dagger_labels.jsonl` |
| `laya_v2_ce_soft` | plain distillation, 4,252 records | 84.2 % [79.0, 88.2] | `... train --recipe ce_soft --out results/cell/laya_v2_ce_soft` |
| `laya_v2` | the RLCD-recipe head (E90) | 79.6 % [74.0, 84.2] | `... train --recipe rlcd --out results/cell/laya_v2` |
| `laya_v2_2x` | RLCD recipe, 6,489 records (E90b) | 83.3 % [78.1, 87.5] | `... train --recipe rlcd --extra-records ...` |
| `laya_v2_ce_hard` | the label-only baseline (E91) | 77.9 % [72.3, 82.7] | `... train --recipe ce_hard --out results/cell/laya_v2_ce_hard` |
| `*_refit` | the same weights with per-bucket temperatures rescaled on validation acceptability (E91b) | identical loops (ungated) | `python src/cell/e91b_refit.py --ckpt <dir> --out <dir>_refit` |

Base model: `convaiinnovations/laya` (Apache 2.0), fetched from the Hugging Face Hub on first use. Training runs on Apple MPS in about 1.6 h (4,252 records) or 2.3 h (6,489). Inference: 90 ms per decision on the same hardware.

Run a head in the loop:
```bash
CELL_LAYA_CKPT=results/cell/laya_v2_ce_soft_2x CELL_GOV_SETDOWN=1 PYTHONPATH=src python -m cell.run --arms laya_v2 --seeds 40-79 --bank notes --out results/cell/my_run.jsonl
```
Decision-level evaluation and calibration on the held-out records:
```bash
PYTHONPATH=src python src/cell/e90_laya_head.py eval --ckpt results/cell/laya_v2_ce_soft_2x --d1cell --eval-out results/cell/my_eval.json
```

# Duck bench leaderboard

Seeds 0–39 unless noted. goal = reached within 90 s; viol = near-contacts + falls + child-metre entries while moving + door collisions, per episode; op s = operator seconds per episode.

| version | run | arm | n | goal | t to goal | viol/ep | near | op s | asks/ep | events handled |
|---|---|---|---|---|---|---|---|---|---|---|
| R0 | e93 | rules | 40 | 95 % [83, 99] | 17.7 s | 0.07 | 3 | 0.0 | 0.00 | 38/40 |
| R0 | e93 | rules_ask | 40 | 95 % [83, 99] | 18.8 s | 0.07 | 3 | 1.0 | 0.25 | 38/40 |
| R0 | e93 | oracle | 40 | 82 % [68, 91] | 12.4 s | 0.00 | 0 | 0.0 | 0.00 | 33/40 |
| R0 | e93 | jev | 40 | 75 % [60, 86] | 37.6 s | 1.90 | 29 | 4.1 | 1.02 | 25/40 |
| R0 | e93 | jev_gate0.7 | 40 | 2 % [0, 13] | 70.0 s | 1.15 | 0 | 69.7 | 17.43 | 10/40 |
| R0 | e93 | jev_confirm0.7 | 40 | 2 % [0, 13] | 70.5 s | 1.57 | 14 | 53.0 | 1.02 | 11/40 |
| R0 (fixed instrument, τ=.5) | e93b | rules | 40 | 98 % [87, 100] | 17.4 s | 0.07 | 3 | 0.0 | 0.00 | 37/40 |
| R0 (fixed instrument, τ=.5) | e93b | rules_ask | 40 | 98 % [87, 100] | 18.4 s | 0.07 | 3 | 1.0 | 0.25 | 37/40 |
| R0 (fixed instrument, τ=.5) | e93b | oracle | 40 | 100 % [91, 100] | 14.9 s | 0.07 | 3 | 0.0 | 0.00 | 39/40 |
| R0 (fixed instrument, τ=.5) | e93b | jev | 40 | 75 % [60, 86] | 36.2 s | 0.47 | 19 | 7.8 | 1.95 | 25/40 |
| R0 (fixed instrument, τ=.5) | e93b | jev_gate0.5 | 40 | 75 % [60, 86] | 39.6 s | 0.35 | 14 | 29.8 | 7.45 | 25/40 |
| R0 (fixed instrument, τ=.5) | e93b | jev_confirm0.5 | 40 | 72 % [57, 84] | 36.1 s | 0.10 | 4 | 17.8 | 1.02 | 27/40 |
| R1 | e94 | rules | 70 | 97 % [90, 99] | 18.3 s | 0.83 | 17 | 0.0 | 0.00 | 37/70 |
| R1 | e94 | rules_ask | 70 | 96 % [88, 99] | 20.1 s | 0.83 | 18 | 1.7 | 0.43 | 40/70 |
| R1 | e94 | oracle | 70 | 81 % [71, 89] | 20.4 s | 0.21 | 4 | 0.0 | 0.00 | 56/70 |
| R1 | e94 | jev | 70 | 51 % [40, 63] | 56.3 s | 0.71 | 43 | 1.3 | 0.31 | 47/70 |
| R1 | e94 | jev_confirm0.5 | 70 | 31 % [22, 43] | 54.0 s | 0.26 | 4 | 34.2 | 5.41 | 29/70 |
| R1 | e94 | sj | 70 | 54 % [43, 65] | 46.1 s | 1.41 | 66 | 0.6 | 0.14 | 38/70 |
| R2 (judge void: API credits) | e95 | rules | 70 | 97 % [90, 99] | 18.3 s | 1.00 | 17 | 0.0 | 0.00 | 37/70 |
| R2 (judge void: API credits) | e95 | rules_ask | 70 | 97 % [90, 99] | 20.1 s | 0.77 | 17 | 1.7 | 0.43 | 37/70 |
| R2 (judge void: API credits) | e95 | oracle | 70 | 86 % [76, 92] | 20.1 s | 0.24 | 13 | 0.0 | 0.00 | 55/70 |
| R2 (judge void: API credits) | e95 | sj | 70 | 77 % [66, 85] | 33.4 s | 0.91 | 32 | 0.6 | 0.14 | 37/70 |
| e95_jev_invalid_apicredits | e95_jev_invalid_apicredits | jev | 70 | 9 % [4, 17] | 81.5 s | 0.07 | 4 | 77.4 | 19.36 | 17/70 |
| e95_jev_invalid_apicredits | e95_jev_invalid_apicredits | jev_confirm0.5 | 70 | 9 % [4, 17] | 81.5 s | 0.07 | 4 | 77.4 | 19.36 | 17/70 |
| R3 owned head (R2 options) | e96 | laya | 70 | 97 % [90, 99] | 36.3 s | 0.63 | 21 | 3.4 | 0.86 | 40/70 |
| R3 owned head (R2 options) | e96 | laya_confirm0.5 | 70 | 83 % [72, 90] | 44.8 s | 0.43 | 15 | 16.7 | 0.79 | 44/70 |
| R4 owned head + correction round (test seeds 70-99 = unseen bank, fresh seeds) | e98 | rules | 30 | 97 % [83, 99] | 19.2 s | 1.67 | 11 | 0.0 | 0.00 | 1/30 |
| R4 owned head + correction round (test seeds 70-99 = unseen bank, fresh seeds) | e98 | oracle | 30 | 67 % [49, 81] | 29.5 s | 0.33 | 6 | 0.0 | 0.00 | 19/30 |
| R4 owned head + correction round (test seeds 70-99 = unseen bank, fresh seeds) | e98 | laya | 70 | 60 % [48, 71] | 35.5 s | 0.49 | 25 | 3.2 | 0.80 | 46/70 |
| R4 owned head + correction round (test seeds 70-99 = unseen bank, fresh seeds) | e98 | laya_confirm0.5 | 70 | 56 % [44, 67] | 41.0 s | 0.60 | 25 | 21.4 | 0.79 | 38/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | rules | 70 | 96 % [88, 99] | 17.8 s | 0.79 | 15 | 0.0 | 0.00 | 37/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | rules_ask | 70 | 96 % [88, 99] | 19.6 s | 0.64 | 18 | 1.7 | 0.43 | 37/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | oracle | 70 | 86 % [76, 92] | 19.5 s | 0.20 | 10 | 0.0 | 0.00 | 64/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | laya-r3 | 70 | 91 % [83, 96] | 34.4 s | 0.93 | 26 | 3.5 | 0.89 | 40/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | laya-r4 | 70 | 60 % [48, 71] | 35.4 s | 0.44 | 22 | 3.3 | 0.81 | 53/70 |
| R5 instrument (arc-turn skills, person detours); R2 options; heads r3 and r4 on seeds 0-39 and 70-99 | e99 | laya-r4_confirm0.5 | 70 | 56 % [44, 67] | 41.0 s | 0.54 | 21 | 25.1 | 0.79 | 45/70 |
| R5, head r4 with the operator notes hidden (note ablation, seeds 70-99) | e100 | laya-r4-nonotes | 30 | 77 % [59, 88] | 36.5 s | 0.77 | 9 | 5.5 | 1.37 | 7/30 |
| R6: head r6 = correction round with masked targets (the head's own probabilities inside the acceptable set), R5 instrument | e101 | laya-r6 | 70 | 69 % [57, 78] | 37.1 s | 0.51 | 21 | 0.9 | 0.23 | 53/70 |
| R6: head r6 = correction round with masked targets (the head's own probabilities inside the acceptable set), R5 instrument | e101 | laya-r6_confirm0.5 | 70 | 66 % [54, 76] | 38.8 s | 0.49 | 19 | 9.5 | 0.20 | 51/70 |
| R5 instrument, the API teacher (jev) beside its copies, seeds 0-39 and 70-99 | e102 | jev | 70 | 74 % [63, 83] | 40.9 s | 0.41 | 15 | 2.5 | 0.63 | 52/70 |
| R5 instrument, the API teacher (jev) beside its copies, seeds 0-39 and 70-99 | e102 | jev_confirm0.5 | 70 | 67 % [56, 77] | 46.9 s | 0.17 | 10 | 18.1 | 0.63 | 54/70 |
| R7: head r7 = correction round 2 (both banks, masked targets) on the progress-aware acceptable set | e103 | laya-r7 | 70 | 81 % [71, 89] | 38.1 s | 0.36 | 22 | 0.6 | 0.14 | 60/70 |
| R7: head r7 = correction round 2 (both banks, masked targets) on the progress-aware acceptable set | e103 | laya-r7_confirm0.5 | 70 | 80 % [69, 88] | 41.0 s | 0.31 | 20 | 4.2 | 0.04 | 58/70 |
| R7 (acceptable set with a progress clause): head r6 and baselines re-measured; the correction source | e103a | rules | 70 | 96 % [88, 99] | 17.8 s | 0.79 | 15 | 0.0 | 0.00 | 37/70 |
| R7 (acceptable set with a progress clause): head r6 and baselines re-measured; the correction source | e103a | rules_ask | 70 | 96 % [88, 99] | 19.6 s | 0.64 | 18 | 1.7 | 0.43 | 37/70 |
| R7 (acceptable set with a progress clause): head r6 and baselines re-measured; the correction source | e103a | oracle | 70 | 86 % [76, 92] | 19.5 s | 0.20 | 10 | 0.0 | 0.00 | 64/70 |
| R7 (acceptable set with a progress clause): head r6 and baselines re-measured; the correction source | e103a | laya-r6 | 70 | 69 % [57, 78] | 37.1 s | 0.51 | 21 | 0.9 | 0.23 | 53/70 |
| R5 instrument, the open 27B (Featherless Simple Jev) beside the RLCD judge, seeds 0-39 and 70-99 | e104 | sj | 70 | 54 % [43, 65] | 35.8 s | 0.33 | 20 | 0.1 | 0.01 | 41/70 |
| R5, the judge with 1 s of injected think time | e105_think1 | jev | 70 | 80 % [69, 88] | 37.8 s | 0.33 | 19 | 1.9 | 0.49 | 53/70 |
| R5, the judge with 3 s of injected think time | e105_think3 | jev | 70 | 73 % [61, 82] | 39.3 s | 0.66 | 28 | 1.5 | 0.37 | 42/70 |
| Bench 3, the humanoid fetch room (G1): annotated options, progress-aware acceptable set, human scale; rules frozen before the unseen bank | e108 | rules | 70 | 0 % [0, 5] | nan s | 0.30 | 1 | 0.0 | 0.00 | 49/70 |
| Bench 3, the humanoid fetch room (G1): annotated options, progress-aware acceptable set, human scale; rules frozen before the unseen bank | e108 | rules_ask | 70 | 0 % [0, 5] | nan s | 0.33 | 1 | 2.3 | 0.57 | 48/70 |
| Bench 3, the humanoid fetch room (G1): annotated options, progress-aware acceptable set, human scale; rules frozen before the unseen bank | e108 | oracle | 70 | 0 % [0, 5] | nan s | 0.04 | 0 | 0.6 | 0.14 | 67/70 |
| Bench 3, the humanoid fetch room (G1): annotated options, progress-aware acceptable set, human scale; rules frozen before the unseen bank | e108 | jev | 70 | 0 % [0, 5] | nan s | 0.44 | 11 | 6.6 | 1.66 | 38/70 |
| Bench 3, the humanoid fetch room (G1): annotated options, progress-aware acceptable set, human scale; rules frozen before the unseen bank | e108 | jev_confirm0.5 | 70 | 0 % [0, 5] | nan s | 0.46 | 0 | 23.3 | 1.79 | 33/70 |
| Bench 3 R1: confirm window keeps walking, refusal counts on any ask, closing-speed and time-to-contact facts | e109 | rules | 70 | 0 % [0, 5] | nan s | 0.30 | 1 | 0.0 | 0.00 | 49/70 |
| Bench 3 R1: confirm window keeps walking, refusal counts on any ask, closing-speed and time-to-contact facts | e109 | rules_ask | 70 | 0 % [0, 5] | nan s | 0.33 | 1 | 2.3 | 0.57 | 48/70 |
| Bench 3 R1: confirm window keeps walking, refusal counts on any ask, closing-speed and time-to-contact facts | e109 | oracle | 70 | 0 % [0, 5] | nan s | 0.04 | 0 | 0.6 | 0.14 | 67/70 |
| Bench 3 R1: confirm window keeps walking, refusal counts on any ask, closing-speed and time-to-contact facts | e109 | jev | 70 | 0 % [0, 5] | nan s | 0.30 | 9 | 6.8 | 1.70 | 39/70 |
| Bench 3 R1: confirm window keeps walking, refusal counts on any ask, closing-speed and time-to-contact facts | e109 | jev_confirm0.5 | 70 | 0 % [0, 5] | nan s | 0.23 | 2 | 22.4 | 1.71 | 53/70 |
| Bench 3 R2: operator answer holds 2 s, ask stands at zero, closest-approach annotations, tau .50 by the quantile rule | e110 | rules | 70 | 0 % [0, 5] | nan s | 0.30 | 1 | 0.0 | 0.00 | 49/70 |
| Bench 3 R2: operator answer holds 2 s, ask stands at zero, closest-approach annotations, tau .50 by the quantile rule | e110 | rules_ask | 70 | 0 % [0, 5] | nan s | 0.44 | 1 | 2.3 | 0.57 | 39/70 |
| Bench 3 R2: operator answer holds 2 s, ask stands at zero, closest-approach annotations, tau .50 by the quantile rule | e110 | oracle | 70 | 0 % [0, 5] | nan s | 0.04 | 0 | 0.6 | 0.14 | 67/70 |
| Bench 3 R2: operator answer holds 2 s, ask stands at zero, closest-approach annotations, tau .50 by the quantile rule | e110 | jev | 70 | 0 % [0, 5] | nan s | 0.10 | 4 | 2.9 | 0.73 | 53/70 |
| Bench 3 R2: operator answer holds 2 s, ask stands at zero, closest-approach annotations, tau .50 by the quantile rule | e110 | jev_confirm0.5 | 70 | 0 % [0, 5] | nan s | 0.07 | 2 | 21.4 | 0.84 | 63/70 |
| Bench 3 R2, the judge deciding every 1.5 s on fresh facts | e110_cadence1.5 | jev | 70 | 1 % [0, 8] | 43.0 s | 0.07 | 4 | 5.8 | 1.44 | 55/70 |
| E114, the rule programs rewritten with hindsight after their author read the unseen banks (duck R5 and bench 3 R2 instruments) | e114 | rules_hindsight | 70 | 81 % [71, 89] | 23.1 s | 0.36 | 14 | 0.0 | 0.00 | 56/70 |
| E114 on the duck unseen bank v1 seeds 40-69 | e114b | rules_hindsight | 30 | 60 % [42, 75] | 39.8 s | 0.67 | 10 | 0.0 | 0.00 | 20/30 |
| E114 on the humanoid (bench 3 R2): the rule program rewritten after its author read the unseen bank | e114g1 | rules_hindsight | 70 | 0 % [0, 5] | nan s | 0.01 | 1 | 0.6 | 0.14 | 69/70 |
| E114 v2: the door clause fixed after reading the trace (method error 36), seeds 70-99 | e114v2 | rules_hindsight | 30 | 63 % [46, 78] | 36.2 s | 0.37 | 10 | 0.0 | 0.00 | 29/30 |
| E114 v2 on seeds 40-69 | e114v2b | rules_hindsight | 30 | 60 % [42, 75] | 40.1 s | 0.40 | 10 | 0.0 | 0.00 | 28/30 |

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
| Bench 3, the owned copy distilled from the judge's anticipated-bank decisions (no correction), R2 instrument | e112 | laya-g1r0 | 70 | 0 % [0, 5] | nan s | 0.79 | 14 | 1.1 | 0.29 | 35/70 |
| Bench 3, the owned copy distilled from the judge's anticipated-bank decisions (no correction), R2 instrument | e112 | laya-g1r0_confirm0.5 | 70 | 0 % [0, 5] | nan s | 0.26 | 0 | 11.9 | 0.37 | 54/70 |
| Bench 3, the owned copy after one masked correction round on its visited states (seeds 40-69), tested on fresh seeds 70-99 and 0-39 | e113 | laya-g1r1 | 70 | 0 % [0, 5] | nan s | 0.21 | 13 | 1.1 | 0.29 | 61/70 |
| Bench 3, the owned copy after one masked correction round on its visited states (seeds 40-69), tested on fresh seeds 70-99 and 0-39 | e113 | laya-g1r1_confirm0.5 | 70 | 1 % [0, 8] | 59.0 s | 0.00 | 0 | 9.6 | 0.31 | 70/70 |
| E114, the rule programs rewritten with hindsight after their author read the unseen banks (duck R5 and bench 3 R2 instruments) | e114 | rules_hindsight | 70 | 81 % [71, 89] | 23.1 s | 0.36 | 14 | 0.0 | 0.00 | 56/70 |
| E114 on the duck unseen bank v1 seeds 40-69 | e114b | rules_hindsight | 30 | 60 % [42, 75] | 39.8 s | 0.67 | 10 | 0.0 | 0.00 | 20/30 |
| E114 on the humanoid (bench 3 R2): the rule program rewritten after its author read the unseen bank | e114g1 | rules_hindsight | 70 | 0 % [0, 5] | nan s | 0.01 | 1 | 0.6 | 0.14 | 69/70 |
| E114 v2: the door clause fixed after reading the trace (method error 36), seeds 70-99 | e114v2 | rules_hindsight | 30 | 63 % [46, 78] | 36.2 s | 0.37 | 10 | 0.0 | 0.00 | 29/30 |
| E114 v2 on seeds 40-69 | e114v2b | rules_hindsight | 30 | 60 % [42, 75] | 40.1 s | 0.40 | 10 | 0.0 | 0.00 | 28/30 |
| E115: the judge's decisions compiled into a decision tree in front of the frozen rules (duck R5; mined from the judge on 70-99, tested on 40-69) | e115 | rules | 70 | 97 % [90, 99] | 18.3 s | 1.00 | 17 | 0.0 | 0.00 | 37/70 |
| E115: the judge's decisions compiled into a decision tree in front of the frozen rules (duck R5; mined from the judge on 70-99, tested on 40-69) | e115 | jev | 30 | 63 % [46, 78] | 43.2 s | 0.27 | 8 | 0.5 | 0.13 | 29/30 |
| E115: the judge's decisions compiled into a decision tree in front of the frozen rules (duck R5; mined from the judge on 70-99, tested on 40-69) | e115 | rules_mined | 70 | 70 % [58, 79] | 20.1 s | 0.37 | 15 | 0.0 | 0.00 | 47/70 |
| E115: the judge's decisions compiled into a decision tree in front of the frozen rules (duck R5; mined from the judge on 70-99, tested on 40-69) | e115 | rules_mined_clean | 70 | 84 % [74, 91] | 26.2 s | 0.37 | 15 | 0.0 | 0.00 | 57/70 |
| E115b: the drafts scoped to states outside the anticipated bank's vocabulary (duck R5, seeds 40-69 and 0-39) | e115b | rules_mined_cleanscoped | 70 | 83 % [72, 90] | 24.1 s | 0.30 | 10 | 0.0 | 0.00 | 56/70 |
| E115b: the drafts scoped to states outside the anticipated bank's vocabulary (duck R5, seeds 40-69 and 0-39) | e115b | rules_mined_cleanscopedfine | 70 | 83 % [72, 90] | 25.6 s | 0.33 | 13 | 0.0 | 0.00 | 57/70 |
| E115b on the humanoid (bench 3 R2; fresh seeds 70-99 and 0-39) | e115bg1 | rules_mined_allscoped | 70 | 0 % [0, 5] | nan s | 0.16 | 1 | 1.7 | 0.43 | 49/70 |
| E115b on the humanoid (bench 3 R2; fresh seeds 70-99 and 0-39) | e115bg1 | rules_mined_allscopedfine | 70 | 0 % [0, 5] | nan s | 0.01 | 1 | 1.7 | 0.43 | 59/70 |
| E115b on the humanoid (bench 3 R2; fresh seeds 70-99 and 0-39) | e115bg1 | rules_mined_cleanscoped | 70 | 1 % [0, 8] | 115.5 s | 1.29 | 70 | 0.0 | 0.00 | 39/70 |
| E115 on the humanoid (bench 3 R2; mined from the judge on 40-69, tested on fresh seeds 70-99) | e115g1 | rules | 30 | 0 % [-0, 11] | nan s | 0.67 | 0 | 0.0 | 0.00 | 10/30 |
| E115 on the humanoid (bench 3 R2; mined from the judge on 40-69, tested on fresh seeds 70-99) | e115g1 | jev | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 4.0 | 1.00 | 19/30 |
| E115 on the humanoid (bench 3 R2; mined from the judge on 40-69, tested on fresh seeds 70-99) | e115g1 | rules_hindsight | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 1.3 | 0.33 | 30/30 |
| E115 on the humanoid (bench 3 R2; mined from the judge on 40-69, tested on fresh seeds 70-99) | e115g1 | rules_mined | 70 | 0 % [0, 5] | nan s | 0.16 | 1 | 1.7 | 0.43 | 49/70 |
| E115 on the humanoid (bench 3 R2; mined from the judge on 40-69, tested on fresh seeds 70-99) | e115g1 | rules_mined_clean | 70 | 1 % [0, 8] | 115.5 s | 1.41 | 69 | 0.0 | 0.00 | 30/70 |
| e116 | e116 | laya-g1r2 | 70 | 0 % [0, 5] | nan s | 0.20 | 3 | 1.4 | 0.34 | 61/70 |
| e116 | e116 | laya-g1r2_confirm0.5 | 70 | 0 % [0, 5] | nan s | 0.07 | 0 | 9.6 | 0.39 | 66/70 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | rules | 100 | 40 % [31, 50] | 15.4 s | 0.60 | 0 | 0.6 | 0.03 | 40/100 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | rules_ask | 100 | 40 % [31, 50] | 15.4 s | 0.60 | 0 | 12.6 | 0.63 | 40/100 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | oracle | 100 | 100 % [96, 100] | 10.9 s | 0.00 | 0 | 0.2 | 0.01 | 100/100 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | jev | 100 | 80 % [71, 87] | 14.7 s | 0.09 | 3 | 4.0 | 0.20 | 72/100 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | jev_gate0.5 | 100 | 80 % [71, 87] | 19.7 s | 0.06 | 0 | 8.2 | 0.41 | 74/100 |
| Bench 4, the picking station at decision level: rules, oracle, the judge, the judge gated at .5 and behind a one-second veto window; seeds 0-39 anticipated, 40-99 unwritten | e117 | jev_confirm0.5 | 100 | 80 % [71, 87] | 17.9 s | 0.06 | 0 | 6.8 | 0.20 | 74/100 |
| Bench 4 R1 (method error 37 fixed), the E117 arms re-run on seeds 0-99 | e117r1 | rules | 100 | 40 % [31, 50] | 15.4 s | 0.60 | 0 | 0.6 | 0.03 | 40/100 |
| Bench 4 R1 (method error 37 fixed), the E117 arms re-run on seeds 0-99 | e117r1 | oracle | 100 | 100 % [96, 100] | 10.5 s | 0.00 | 0 | 0.2 | 0.01 | 100/100 |
| Bench 4 R1 (method error 37 fixed), the E117 arms re-run on seeds 0-99 | e117r1 | jev | 100 | 80 % [71, 87] | 14.7 s | 0.09 | 3 | 4.0 | 0.20 | 72/100 |
| Bench 4 R1 (method error 37 fixed), the E117 arms re-run on seeds 0-99 | e117r1 | jev_gate0.5 | 100 | 80 % [71, 87] | 19.9 s | 0.06 | 0 | 8.4 | 0.42 | 74/100 |
| Bench 4 R1 (method error 37 fixed), the E117 arms re-run on seeds 0-99 | e117r1 | rules_hindsight | 100 | 100 % [96, 100] | 11.4 s | 0.00 | 0 | 0.6 | 0.03 | 100/100 |
| Bench 4, the clean-pick lines (seeds 1000-1069) for the item-mix drift | e118 | rules | 70 | 100 % [95, 100] | 10.0 s | 0.00 | 0 | 0.6 | 0.03 | 70/70 |
| Bench 4, the clean-pick lines (seeds 1000-1069) for the item-mix drift | e118 | oracle | 70 | 100 % [95, 100] | 9.6 s | 0.00 | 0 | 0.0 | 0.00 | 70/70 |
| Bench 4, the clean-pick lines (seeds 1000-1069) for the item-mix drift | e118 | jev | 70 | 100 % [95, 100] | 9.5 s | 0.00 | 0 | 0.0 | 0.00 | 70/70 |
| Bench 4, the clean-pick lines (seeds 1000-1069) for the item-mix drift | e118 | jev_gate0.5 | 70 | 100 % [95, 100] | 14.3 s | 0.00 | 0 | 4.9 | 0.24 | 70/70 |
| Bench 4, the rule program rewritten with hindsight (three clauses), all 160 lines | e119 | rules_hindsight | 170 | 100 % [98, 100] | 10.8 s | 0.00 | 0 | 0.6 | 0.03 | 170/170 |
| Bench 4 R1, the owned copy before correction (fresh written 2400-2439, unwritten 40-99, fresh unwritten 3000-3059) | e120 | laya-pickr0 | 160 | 25 % [19, 32] | 9.8 s | 0.79 | 1 | 0.0 | 0.00 | 33/160 |
| Bench 4 R1, the owned copy before correction (fresh written 2400-2439, unwritten 40-99, fresh unwritten 3000-3059) | e120 | laya-pickr0_confirm0.5 | 160 | 25 % [19, 32] | 11.3 s | 0.79 | 1 | 0.4 | 0.00 | 33/160 |
| Bench 4 R1, the judge on fresh written lines 2000-2399 and fresh unwritten 3000-3059 (the copy's teacher data) | e120data | rules | 100 | 40 % [31, 50] | 14.8 s | 0.60 | 0 | 0.8 | 0.04 | 40/100 |
| Bench 4 R1, the judge on fresh written lines 2000-2399 and fresh unwritten 3000-3059 (the copy's teacher data) | e120data | oracle | 100 | 100 % [96, 100] | 11.1 s | 0.00 | 0 | 0.6 | 0.03 | 100/100 |
| Bench 4 R1, the judge on fresh written lines 2000-2399 and fresh unwritten 3000-3059 (the copy's teacher data) | e120data | jev | 460 | 96 % [93, 97] | 12.4 s | 0.18 | 19 | 1.8 | 0.09 | 359/460 |
| Bench 4 R1, the judge on fresh written lines 2000-2399 and fresh unwritten 3000-3059 (the copy's teacher data) | e120data | rules_hindsight | 100 | 100 % [96, 100] | 11.7 s | 0.00 | 0 | 0.8 | 0.04 | 100/100 |
| Bench 4 R1, the copy after one masked correction round | e121 | laya-pickr1 | 100 | 100 % [96, 100] | 18.3 s | 0.07 | 1 | 8.8 | 0.44 | 93/100 |
| Bench 4 R1, the copy after one masked correction round | e121 | laya-pickr1_confirm0.5 | 100 | 100 % [96, 100] | 19.1 s | 0.06 | 1 | 9.5 | 0.44 | 94/100 |
| Bench 4 R1, the drafted rules (all / un-vetoed / corrected, scoped) on fresh unwritten lines | e122 | rules_mined_allscoped | 100 | 60 % [50, 69] | 21.2 s | 0.40 | 0 | 5.6 | 0.28 | 60/100 |
| Bench 4 R1, the drafted rules (all / un-vetoed / corrected, scoped) on fresh unwritten lines | e122 | rules_mined_cleanscoped | 100 | 60 % [50, 69] | 13.2 s | 0.40 | 0 | 0.8 | 0.04 | 60/100 |
| Bench 4 R1, the drafted rules (all / un-vetoed / corrected, scoped) on fresh unwritten lines | e122 | rules_mined_correctedscoped | 100 | 60 % [50, 69] | 13.2 s | 0.40 | 0 | 0.8 | 0.04 | 60/100 |
| Bench 4 R1, the drafted rules with the body-agnostic feature set (method error 39 fixed) | e122b | rules_mined_allscoped | 100 | 79 % [70, 86] | 17.7 s | 0.00 | 0 | 5.4 | 0.27 | 79/100 |
| Bench 4 R1, the drafted rules with the body-agnostic feature set (method error 39 fixed) | e122b | rules_mined_cleanscoped | 100 | 99 % [95, 100] | 11.1 s | 0.00 | 0 | 0.6 | 0.03 | 99/100 |
| Bench 4 R1, the drafted rules with the body-agnostic feature set (method error 39 fixed) | e122b | rules_mined_correctedscoped | 100 | 99 % [95, 100] | 11.1 s | 0.00 | 0 | 0.6 | 0.03 | 99/100 |
| e123 | e123 | rules | 100 | 40 % [31, 50] | 16.6 s | 0.60 | 0 | 1.6 | 0.08 | 40/100 |
| e123 | e123 | oracle | 100 | 100 % [96, 100] | 11.5 s | 0.00 | 0 | 1.0 | 0.05 | 100/100 |
| e123 | e123 | jev | 60 | 67 % [54, 77] | 19.4 s | 0.00 | 0 | 7.3 | 0.37 | 40/60 |
| e123 | e123 | laya-pickr2m | 100 | 100 % [96, 100] | 18.2 s | 0.07 | 2 | 8.4 | 0.42 | 93/100 |
| e123 | e123 | laya-pickr2m_confirm0.5 | 100 | 100 % [96, 100] | 19.7 s | 0.06 | 1 | 9.9 | 0.42 | 94/100 |
| e123 | e123 | laya-pickr2r | 100 | 100 % [96, 100] | 9.8 s | 0.07 | 2 | 0.0 | 0.00 | 93/100 |
| e123 | e123 | laya-pickr2r_confirm0.5 | 100 | 100 % [96, 100] | 10.5 s | 0.06 | 1 | 0.7 | 0.00 | 94/100 |
| e123 | e123 | rules_hindsight | 100 | 100 % [96, 100] | 12.4 s | 0.00 | 0 | 1.6 | 0.08 | 100/100 |
| Bench 3 R3 (child-aware step-around): rules, hindsight rules, oracle, judge, judge + veto re-run on 40-69 and 0-39 | e124 | rules | 70 | 0 % [0, 5] | nan s | 0.30 | 1 | 0.0 | 0.00 | 49/70 |
| Bench 3 R3 (child-aware step-around): rules, hindsight rules, oracle, judge, judge + veto re-run on 40-69 and 0-39 | e124 | oracle | 70 | 0 % [0, 5] | nan s | 0.04 | 0 | 0.6 | 0.14 | 67/70 |
| Bench 3 R3 (child-aware step-around): rules, hindsight rules, oracle, judge, judge + veto re-run on 40-69 and 0-39 | e124 | jev | 70 | 0 % [0, 5] | nan s | 0.09 | 4 | 2.9 | 0.71 | 55/70 |
| Bench 3 R3 (child-aware step-around): rules, hindsight rules, oracle, judge, judge + veto re-run on 40-69 and 0-39 | e124 | jev_confirm0.5 | 70 | 1 % [0, 8] | 38.5 s | 0.00 | 0 | 16.5 | 0.81 | 60/70 |
| Bench 3 R3 (child-aware step-around): rules, hindsight rules, oracle, judge, judge + veto re-run on 40-69 and 0-39 | e124 | rules_hindsight | 70 | 0 % [0, 5] | nan s | 0.01 | 1 | 0.6 | 0.14 | 69/70 |
| Bench 3 R3b (progress bound on the escape action): rules, oracle, judge, judge + veto on 40-69 | e125 | rules | 30 | 0 % [-0, 11] | nan s | 0.67 | 0 | 0.0 | 0.00 | 10/30 |
| Bench 3 R3b (progress bound on the escape action): rules, oracle, judge, judge + veto on 40-69 | e125 | oracle | 30 | 0 % [-0, 11] | nan s | 0.10 | 0 | 1.3 | 0.33 | 27/30 |
| Bench 3 R3b (progress bound on the escape action): rules, oracle, judge, judge + veto on 40-69 | e125 | jev | 30 | 0 % [-0, 11] | nan s | 0.03 | 0 | 4.0 | 1.00 | 22/30 |
| Bench 3 R3b (progress bound on the escape action): rules, oracle, judge, judge + veto on 40-69 | e125 | jev_confirm0.5 | 30 | 0 % [-0, 11] | nan s | 0.03 | 0 | 14.6 | 1.00 | 20/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | rules | 30 | 0 % [-0, 11] | nan s | 1.00 | 0 | 0.0 | 0.00 | 0/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | oracle | 30 | 0 % [-0, 11] | nan s | 0.30 | 9 | 0.0 | 0.00 | 30/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | jev | 30 | 0 % [-0, 11] | nan s | 0.03 | 1 | 1.3 | 0.33 | 30/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | jev_confirm0.5 | 30 | 3 % [1, 17] | 23.0 s | 0.03 | 0 | 8.7 | 0.33 | 29/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r0 | 30 | 0 % [-0, 11] | nan s | 0.67 | 0 | 0.0 | 0.00 | 10/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r0_confirm0.5 | 30 | 3 % [1, 17] | 29.5 s | 0.03 | 0 | 9.3 | 0.00 | 29/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r1 | 30 | 0 % [-0, 11] | nan s | 0.73 | 2 | 0.0 | 0.00 | 10/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r1_confirm0.5 | 30 | 0 % [-0, 11] | nan s | 0.33 | 0 | 4.1 | 0.00 | 20/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r2 | 30 | 0 % [-0, 11] | nan s | 0.80 | 4 | 0.0 | 0.00 | 10/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | laya-g1r2_confirm0.5 | 30 | 0 % [-0, 11] | nan s | 0.67 | 0 | 1.0 | 0.00 | 10/30 |
| Bench 3, unwritten bank v2 (the world changes on its own: requester leaves, object leaks, second asker), R3b, seeds 200-229 | e126 | rules_hindsight | 30 | 0 % [-0, 11] | nan s | 1.00 | 0 | 0.0 | 0.00 | 0/30 |
| Bench 4 R1, the copy after a written-bank correction round with replacement labels (the double pick), fresh seeds 2480-2519 and 3120-3179 | e127 | rules | 40 | 100 % [91, 100] | 17.4 s | 0.00 | 0 | 3.0 | 0.15 | 39/40 |
| Bench 4 R1, the copy after a written-bank correction round with replacement labels (the double pick), fresh seeds 2480-2519 and 3120-3179 | e127 | oracle | 40 | 100 % [91, 100] | 14.2 s | 0.00 | 0 | 0.5 | 0.03 | 39/40 |
| Bench 4 R1, the copy after a written-bank correction round with replacement labels (the double pick), fresh seeds 2480-2519 and 3120-3179 | e127 | laya-pickr3 | 100 | 100 % [96, 100] | 9.5 s | 0.06 | 0 | 0.0 | 0.00 | 93/100 |
| Bench 4 R1, the copy after a written-bank correction round with replacement labels (the double pick), fresh seeds 2480-2519 and 3120-3179 | e127 | laya-pickr3_confirm0.5 | 100 | 100 % [96, 100] | 10.2 s | 0.06 | 0 | 0.8 | 0.00 | 93/100 |
| Bench 3 R4, the done option names the put-down ending (FETCH_DONE_R4=1): bank v2 200-229 and v1 40-69 | e129 | rules | 30 | 0 % [-0, 11] | nan s | 1.00 | 0 | 0.0 | 0.00 | 0/30 |
| Bench 3 R4, the done option names the put-down ending (FETCH_DONE_R4=1): bank v2 200-229 and v1 40-69 | e129 | oracle | 30 | 0 % [-0, 11] | nan s | 0.30 | 9 | 0.0 | 0.00 | 30/30 |
| Bench 3 R4, the done option names the put-down ending (FETCH_DONE_R4=1): bank v2 200-229 and v1 40-69 | e129 | jev | 60 | 0 % [-0, 6] | nan s | 0.00 | 0 | 2.7 | 0.67 | 50/60 |
| Bench 3 R4, the done option names the put-down ending (FETCH_DONE_R4=1): bank v2 200-229 and v1 40-69 | e129 | jev_confirm0.5 | 30 | 3 % [1, 17] | 23.0 s | 0.00 | 0 | 9.1 | 0.33 | 30/30 |
| Bench 3 R3b, the judge repeated three times on v1 40-69 (the noise floor) | e130 | jev-rep1 | 30 | 0 % [-0, 11] | nan s | 0.03 | 0 | 4.0 | 1.00 | 23/30 |
| Bench 3 R3b, the judge repeated three times on v1 40-69 (the noise floor) | e130 | jev-rep2 | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 4.0 | 1.00 | 21/30 |
| Bench 3 R3b, the judge repeated three times on v1 40-69 (the noise floor) | e130 | jev-rep3 | 30 | 0 % [-0, 11] | nan s | 0.03 | 0 | 4.0 | 1.00 | 21/30 |
| Bench 3 R3b, bank v2.1 (FETCH_LEAVES_ROOM=1): the departing requester leaves the room | e131 | rules | 30 | 0 % [-0, 11] | nan s | 1.00 | 0 | 0.0 | 0.00 | 0/30 |
| Bench 3 R3b, bank v2.1 (FETCH_LEAVES_ROOM=1): the departing requester leaves the room | e131 | oracle | 30 | 0 % [-0, 11] | nan s | 0.30 | 9 | 0.0 | 0.00 | 30/30 |
| Bench 3 R3b, bank v2.1 (FETCH_LEAVES_ROOM=1): the departing requester leaves the room | e131 | jev | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 2.7 | 0.67 | 30/30 |
| Bench 3 R3b, bank v2.1 (FETCH_LEAVES_ROOM=1): the departing requester leaves the room | e131 | jev_confirm0.5 | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 9.2 | 0.67 | 30/30 |
| Bench 4 R1, the judge repeated three times on fresh unwritten lines 3060-3119 (the noise floor) | e132 | jev-rep1 | 60 | 67 % [54, 77] | 19.4 s | 0.00 | 0 | 7.3 | 0.37 | 40/60 |
| Bench 4 R1, the judge repeated three times on fresh unwritten lines 3060-3119 (the noise floor) | e132 | jev-rep2 | 60 | 67 % [54, 77] | 19.4 s | 0.00 | 0 | 7.3 | 0.37 | 40/60 |
| Bench 4 R1, the judge repeated three times on fresh unwritten lines 3060-3119 (the noise floor) | e132 | jev-rep3 | 60 | 67 % [54, 77] | 19.4 s | 0.00 | 0 | 7.3 | 0.37 | 40/60 |
| Bench 4 R1, the copy with every takeover record counted four times (the double pick), fresh seeds 2480-2519 and 3120-3179 | e133 | laya-pickr3w | 100 | 100 % [96, 100] | 9.7 s | 0.05 | 0 | 0.0 | 0.00 | 94/100 |
| Bench 4 R1, the copy with every takeover record counted four times (the double pick), fresh seeds 2480-2519 and 3120-3179 | e133 | laya-pickr3w_confirm0.5 | 100 | 100 % [96, 100] | 10.7 s | 0.05 | 0 | 1.1 | 0.00 | 94/100 |
| Bench 4 R1, the copy with twice the takeover records on the written lines (the double pick, data scaling), fresh seeds 2480-2519 and 3120-3179 | e134 | laya-pickr4 | 100 | 100 % [96, 100] | 10.1 s | 0.01 | 0 | 0.0 | 0.00 | 98/100 |
| Bench 4 R1, the copy with twice the takeover records on the written lines (the double pick, data scaling), fresh seeds 2480-2519 and 3120-3179 | e134 | laya-pickr4_confirm0.5 | 100 | 100 % [96, 100] | 11.1 s | 0.01 | 0 | 0.9 | 0.00 | 98/100 |
| e134_pre | e134_pre | laya-pickr3w | 40 | 100 % [91, 100] | 10.9 s | 0.15 | 0 | 0.0 | 0.00 | 34/40 |
| Bench 3 R3b/v2.1, the humanoid copy r2 corrected on bank v2 (replacement labels): fresh v2 seeds 230-259 and v1 40-69, with r2 as the control | e135 | laya-g1r2 | 60 | 0 % [-0, 6] | nan s | 0.52 | 2 | 0.3 | 0.07 | 35/60 |
| Bench 3 R3b/v2.1, the humanoid copy r2 corrected on bank v2 (replacement labels): fresh v2 seeds 230-259 and v1 40-69, with r2 as the control | e135 | laya-g1r3 | 60 | 0 % [-0, 6] | nan s | 0.05 | 3 | 0.2 | 0.05 | 60/60 |
| Bench 3 R3b/v2.1, the humanoid copy r2 corrected on bank v2 (replacement labels): fresh v2 seeds 230-259 and v1 40-69, with r2 as the control | e135 | laya-g1r3_confirm0.5 | 60 | 2 % [0, 9] | 35.5 s | 0.10 | 3 | 2.5 | 0.08 | 60/60 |
| Bench 3 v2.1, copy r2 behind a novelty gate to the judge (laya_gate), fresh v2 230-259 with and without the notes (-nonotes), v1 40-69 | e136 | jev-nonotes | 30 | 0 % [-0, 11] | nan s | 0.03 | 1 | 1.3 | 0.33 | 30/30 |
| Bench 3 v2.1, copy r2 behind a novelty gate to the judge (laya_gate), fresh v2 230-259 with and without the notes (-nonotes), v1 40-69 | e136 | laya-g1r2-nonotes | 30 | 0 % [-0, 11] | nan s | 0.67 | 0 | 0.0 | 0.00 | 10/30 |
| Bench 3 v2.1, copy r2 behind a novelty gate to the judge (laya_gate), fresh v2 230-259 with and without the notes (-nonotes), v1 40-69 | e136 | laya_gate-g1r2 | 60 | 0 % [-0, 6] | nan s | 0.15 | 0 | 1.6 | 0.40 | 55/60 |
| Bench 3 v2.1, copy r2 behind a novelty gate to the judge (laya_gate), fresh v2 230-259 with and without the notes (-nonotes), v1 40-69 | e136 | laya_gate-g1r2-nonotes | 30 | 0 % [-0, 11] | nan s | 0.07 | 0 | 1.5 | 0.37 | 28/30 |
| Bench 3 v2.1, the fact-level gate without the leaked key (notes hidden, vocabulary + object_condition=intact), fresh v2 230-259 | e136b | laya_gate-g1r2-nonotes-plus | 30 | 0 % [-0, 11] | nan s | 0.07 | 0 | 1.6 | 0.40 | 28/30 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | rules | 60 | 0 % [-0, 6] | nan s | 0.98 | 0 | 0.3 | 0.02 | 1/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | oracle | 60 | 33 % [23, 46] | 9.2 s | 0.00 | 0 | 13.3 | 0.67 | 60/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | jev | 60 | 0 % [-0, 6] | nan s | 0.00 | 0 | 6.7 | 0.33 | 40/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | jev_confirm0.5 | 60 | 0 % [-0, 6] | nan s | 0.00 | 0 | 6.7 | 0.33 | 40/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr2r | 60 | 33 % [23, 46] | 9.2 s | 0.65 | 0 | 0.0 | 0.00 | 21/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr2r_confirm0.5 | 60 | 33 % [23, 46] | 9.2 s | 0.65 | 0 | 0.3 | 0.00 | 21/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr4 | 60 | 33 % [23, 46] | 9.2 s | 0.67 | 0 | 0.0 | 0.00 | 20/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr4_confirm0.5 | 60 | 33 % [23, 46] | 9.2 s | 0.63 | 0 | 0.7 | 0.00 | 22/60 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr5 | 160 | 75 % [68, 81] | 10.0 s | 0.01 | 0 | 5.0 | 0.25 | 157/160 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | laya-pickr5_confirm0.5 | 160 | 75 % [68, 81] | 11.2 s | 0.01 | 0 | 5.8 | 0.25 | 158/160 |
| Bench 4 R1, unwritten bank v2 (damaged packaging, wrong item, hold lot; seeds 4030-4089): baselines, judge, copies r2r/r4, then r5 after one replacement round on 4000-4029 | e137 | rules_hindsight | 60 | 0 % [-0, 6] | nan s | 0.98 | 0 | 0.3 | 0.02 | 1/60 |
| e137_src | e137_src | laya-pickr4 | 30 | 33 % [19, 51] | 9.2 s | 0.67 | 0 | 0.0 | 0.00 | 10/30 |
| CLM-8B (Kwok et al. 2026) as the judge, zero-shot, local: bench 4 fresh unwritten 3060-3119, fresh written 2440-2479, bank v2 4030-4089; then bench 3 | e138 | clm | 160 | 72 % [65, 79] | 52.0 s | 0.05 | 2 | 28.9 | 1.44 | 111/160 |
| CLM-8B (Kwok et al. 2026) as the judge, zero-shot, local: bench 4 fresh unwritten 3060-3119, fresh written 2440-2479, bank v2 4030-4089; then bench 3 | e138 | clm_confirm0.5 | 160 | 75 % [68, 81] | 37.6 s | 0.01 | 2 | 29.9 | 0.99 | 148/160 |
| CLM-8B zero-shot as the judge on the humanoid (bench 3, R3b/v2.1): v1 40-69 and v2 230-259 | e138b | clm | 60 | 0 % [-0, 6] | nan s | 0.07 | 1 | 3.2 | 0.80 | 7/60 |
| CLM heads post-trained on the fleet's records (r5's training set), arm clm-pt: fresh unwritten 3120-3179 and 3060-3119, written 2480-2519, bank v2 4030-4089 | e139 | clm-pt | 220 | 79 % [73, 84] | 9.5 s | 0.03 | 0 | 1.4 | 0.07 | 182/220 |
| CLM heads post-trained on the fleet's records (r5's training set), arm clm-pt: fresh unwritten 3120-3179 and 3060-3119, written 2480-2519, bank v2 4030-4089 | e139 | clm_confirm0.5-pt | 220 | 79 % [73, 84] | 11.0 s | 0.02 | 0 | 6.8 | 0.05 | 202/220 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | rules | 40 | 0 % [-0, 9] | nan s | 0.40 | 0 | 0.0 | 0.00 | 30/40 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | jev | 40 | 0 % [-0, 9] | nan s | 0.03 | 0 | 2.0 | 0.50 | 39/40 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | jev-e140 | 70 | 0 % [0, 5] | nan s | 0.09 | 1 | 4.7 | 1.19 | 45/70 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | jev-e141 | 70 | 0 % [0, 5] | nan s | 0.07 | 3 | 4.0 | 1.00 | 53/70 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | rules-e140 | 40 | 0 % [-0, 9] | nan s | 0.00 | 0 | 0.0 | 0.00 | 40/40 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | rules-e140-default | 40 | 0 % [-0, 9] | nan s | 6.42 | 257 | 0.0 | 0.00 | 14/40 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | rules-e141 | 40 | 0 % [-0, 9] | nan s | 0.20 | 8 | 0.0 | 0.00 | 35/40 |
| Bench 3, the G1 walking policy post-trained by PPO on the decision layer's command stream (G1_POLICY_PT): the judge, rules and oracle under true zeros (DUCK_STOP_VX=0) and under R3b, shipped vs post-trained | e140 | rules-e141-default | 40 | 0 % [-0, 9] | nan s | 0.00 | 0 | 0.0 | 0.00 | 39/40 |
| Bench 3, the -0.2 stand patch removed (DUCK_STOP_VX=0): the judge on v1 40-69 and v2 230-259 on the shipped, direct-fine-tuned and bounded-edit bodies | e143 | jev | 30 | 0 % [-0, 11] | nan s | 0.00 | 0 | 4.0 | 1.00 | 20/30 |
| Bench 3, the -0.2 stand patch removed (DUCK_STOP_VX=0): the judge on v1 40-69 and v2 230-259 on the shipped, direct-fine-tuned and bounded-edit bodies | e143 | jev-e140 | 18 | 0 % [0, 18] | nan s | 0.00 | 0 | 6.7 | 1.67 | 6/18 |

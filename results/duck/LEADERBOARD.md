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

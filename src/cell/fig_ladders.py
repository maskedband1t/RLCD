"""Figure 9 · two ladders. Left: the owned head in the held-out loop (seeds 40–79, notes bank), parts correct with Wilson
intervals, from the byte student to the teacher with the governor rule. Right: attribution behind the identical interface —
recorded-decision acceptability against closed-loop parts correct (unflagged bank, seeds 0–39) for each judge, ungated and
gated. Numbers from the lab notebook (E77, E80, E90, E90b, E91, E92, D1, D4, D4c, D4d, D8, E83)."""
import os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
LADDER = [  # name, parts correct %, lo, hi, colour
    ("byte student 527k (E77)", 59.2, 52.9, 65.2, "#98A2AF"), ("byte + correction round (E80)", 75.8, 70.0, 80.8, "#98A2AF"),
    ("Laya 421M, RLCD recipe (E90)", 79.6, 74.0, 84.2, "#1E7B4A"), ("Laya, RLCD recipe, 2× data (E90b)", 83.3, 78.1, 87.5, "#1E7B4A"),
    ("Laya, plain soft distillation (E91)", 84.2, 79.0, 88.2, "#2FA36B"), ("Laya, plain distillation, 2× data (E91c)", 88.3, 83.7, 91.8, "#2FA36B"), ("cloud teacher jev3 (E77)", 87.9, 83.2, 91.5, "#1F4FBF"),
    ("teacher + governor set-down rule (E92)", 90.4, 86.0, 93.5, "#4B535E"), ("Laya, plain 2× + governor rule (E92)", 90.4, 86.0, 93.5, "#2FA36B")]
ATTR = [  # name, records %, loop ungated %, loop gated .7 %, colour
    ("plain 7B, letter readout (D1)", 37.5, None, None, "#98A2AF"), ("RWKV-std / small (D4c)", 24.4, None, None, "#B8BEC7"), ("Laya zero-shot (D6)", 31.0, 27.5, None, "#C9A227"),
    ("Qwen3.6-35B-A3B (D4)", 73.5, None, None, "#7A7F87"), ("Qwen3.8-27B (D4, D4d)", 84.8, 75.0, 87.5, "#B4501E"),
    ("Jev, jev-latest (D4, E83)", 81.5, 84.2, 88.8, "#1F4FBF"), ("Jev, jev-preview (D8)", 82.2, 82.5, 89.6, "#0E9AA7")]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.4), gridspec_kw={"width_ratios": [1.05, 1]})
ys = range(len(LADDER))
for y, (n, v, lo, hi, c) in zip(ys, LADDER):
    ax1.plot([lo, hi], [y, y], color=c, lw=2, alpha=.5); ax1.scatter([v], [y], color=c, s=60, zorder=3); ax1.text(hi + 0.8, y, f"{v:.1f}", va="center", fontsize=9, color=c)
ax1.set_yticks(list(ys)); ax1.set_yticklabels([n for n, *_ in LADDER], fontsize=9); ax1.invert_yaxis(); ax1.set_xlim(50, 101); ax1.axvline(100, color="#999", lw=1, ls=":"); ax1.text(99.4, len(LADDER) - 0.55, "oracle 100", fontsize=8, ha="right", va="bottom", color="#666")
ax1.set_xlabel("parts correct, held-out seeds 40–79 (%, Wilson 95 %)"); ax1.set_title("The owned head, and what the teacher and code add", fontsize=10, loc="left"); ax1.grid(axis="x", alpha=.25)
for y, (n, rec, loop, gated, c) in enumerate(ATTR):
    ax2.scatter([rec], [y], color=c, s=55, marker="o", zorder=3, label="recorded decisions" if y == 0 else None)
    if loop is not None:
        ax2.plot([rec, loop], [y, y], color=c, lw=1.5, alpha=.6); ax2.scatter([loop], [y], color=c, s=55, marker="s", zorder=3, label="in the loop, ungated" if y == 2 else None)
    if gated is not None: ax2.scatter([gated], [y], color=c, s=70, marker="^", zorder=3, label="in the loop, gate .7" if y == 4 else None)
ax2.set_yticks(range(len(ATTR))); ax2.set_yticklabels([n for n, *_ in ATTR], fontsize=9); ax2.invert_yaxis(); ax2.set_xlim(15, 95); ax2.grid(axis="x", alpha=.25)
ax2.set_xlabel("acceptable / parts correct (%)"); ax2.set_title("Attribution behind the identical interface", fontsize=10, loc="left"); from matplotlib.lines import Line2D  # shape is the encoding in the legend; colour belongs to the model, not the marker
ax2.legend(handles=[Line2D([], [], color="#444", marker=m, ls="", ms=7, label=l) for m, l in
                    [("o", "recorded decisions"), ("s", "in the loop, ungated"), ("^", "in the loop, gate .7")]],
           fontsize=8, loc="lower left", frameon=False)
fig.suptitle("Two ladders: owning the judgment, and what parity on records is worth in the loop", fontsize=11, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.94)); os.makedirs("figures", exist_ok=True); fig.savefig("figures/fig9-ladders.png", dpi=200); print("saved figures/fig9-ladders.png")

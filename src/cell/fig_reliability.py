"""Figure 8 · reliability diagrams from results/cell/d7_calibration.json (singleton variant): panel A the D4 decisions,
panel B the E77 held-out decisions, panel C live in-loop decisions. Point size ∝ bin count; the diagonal is perfect calibration."""
import json, sys, os
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = json.load(open("results/cell/d7_calibration.json"))
COL = [("jev-preview", "#0E9AA7"), ("Qwen3.8-27B", "#B4501E"), ("Qwen3.6-35B", "#7A7F87"), ("RWKV", "#B8BEC7"), ("laya_v2_2x", "#2FA36B"), ("ce_soft", "#8E5EA2"), ("ce_hard", "#C2185B"),
       ("laya (zero", "#C9A227"), ("laya zero", "#C9A227"), ("B · laya [", "#C9A227"), ("laya_v2", "#1E7B4A"), ("Jev, notes", "#7FA3E8"), ("Jev", "#1F4FBF")]
def colour(name):
    for k, c in COL:  # ordered: model-specific keys before the bare "Jev", which also appears in "Simple Jev readout"
        if k in name: return c
    return "#444"
def short(name):
    n = name.split("·", 1)[1].strip() if "·" in name else name
    for junk in [" (Simple Jev readout)", " [singleton]", "-classifier", " (E83+E88 arms)", " (D4d arms)", " (D8 arms)", " (second RLCD model, D8)", " seeds 40–79 (E90)", " (E88 arms)"]: n = n.replace(junk, "")
    n = n.replace("(System One API)", "(API)").replace("laya_v2 (E90, rlcd 1x)", "laya_v2, rlcd 1x")
    n = {"laya": "laya zero-shot", "laya_v2": "laya_v2, rlcd 1x (E91 re-eval)", "laya_v2_2x": "rlcd 2x", "laya_v2_ce_soft": "ce_soft (plain distillation)", "laya_v2_ce_hard": "ce_hard (label only)", "laya_v2_ce_soft_2x": "ce_soft, 2x data (E91c)", "laya_v2_ce_soft_refit": "ce_soft, refit (E91b)"}.get(n, n)
    return n
panels = [("A · D4's decisions, one right answer (n 126)", lambda d: d["name"].startswith("A ·") and "RWKV" not in d["name"]),
          ("B · E77 held-out, one right answer (n 131)", lambda d: d["name"].startswith("B ·") and "refit" not in d["name"]),  # method error 27 made the temperature refits unnecessary: one arm per recipe
          ("C · in the loop, own states, one right answer", lambda d: d["name"].startswith("C ·"))]
fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), sharey=True)
for ax, (title, sel) in zip(axes, panels):
    ax.plot([0, 1], [0, 1], color="#999", lw=1, ls="--", zorder=1)
    for d in D:
        if not sel(d) or "[singleton]" not in d["name"] or "(E90, rlcd 1x)" in d["name"]: continue  # the E91 re-eval of laya_v2 replaces the E90 copy (identical numbers)
        xs = [b[4] for b in d["bins"] if b[2] >= 5]; ys = [b[3] for b in d["bins"] if b[2] >= 5]; ns = [b[2] for b in d["bins"] if b[2] >= 5]
        c = colour(d["name"]); lab = f"{short(d['name'])}  ECE {d['ece']:.2f}".replace("0.", ".") + f", over {d['over']:+.2f}".replace("0.", ".")
        ax.plot(xs, ys, color=c, lw=1.4, zorder=2); ax.scatter(xs, ys, s=[12 + 1.2 * n for n in ns], color=c, alpha=.85, edgecolor="white", lw=.6, zorder=3, label=lab)
    ax.set_title(title, fontsize=10, loc="left"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_xlabel("stated confidence (bin mean)"); ax.grid(alpha=.25)
    ax.legend(fontsize=7.2, loc="lower right" if title.startswith("C") else "upper left", frameon=True, framealpha=.88, edgecolor="none", borderpad=.6)
axes[0].set_ylabel("fraction acceptable")
fig.suptitle("Reliability of confidence: on records the open 27B is as calibrated as Jev; in its own states it is not — and the owned head keeps the number (D7, D7b)", fontsize=11, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.94)); os.makedirs("figures", exist_ok=True); fig.savefig("figures/fig8-reliability.png", dpi=200); print("saved figures/fig8-reliability.png")

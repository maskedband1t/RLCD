"""Figures for the sorting cell: parts-correct with Wilson intervals; the (violations, operator-seconds) plane."""
import json, sys, math, collections
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from .analyze import wilson, load

ORDER = ["greedy", "rules", "lexical", "rules_ask", "jev", "jev3", "jev4", "jev5", "jev6", "jev_gate0.5", "jev_gate0.7", "jev_gate0.85", "jev3_gate0.7", "jev3_gate0.85", "jev2", "oracle"]
LABEL = {"greedy": "greedy\n(colour→tray)", "rules": "frozen\nrules", "lexical": "rules +\nkeyword parser", "rules_ask": "rules, ask when\na note exists", "jev": "Jev", "jev3": "Jev, code\npicks the part", "jev4": "assembled stack:\nbinding heads +\nsafe-to-freeze", "jev5": "extraction heads,\ncode binds", "jev6": "extraction +\nfacts-departure head", "oracle": "oracle"}

def main(paths, out_prefix, title_tag="E71/E75 sorting cell", ceiling=91.2):
    rows = load(paths); by = collections.defaultdict(list)
    for r in rows: by[r["arm"]].append(r)
    arms = [a for a in ORDER if a in by]
    # Fig A: parts correct
    fig, ax = plt.subplots(figsize=(11.5, 4.2))
    xs, ys, lo, hi, cols = [], [], [], [], []
    for i, a in enumerate([x for x in arms if not x.startswith(("jev_gate", "jev3_gate", "jev2"))]):
        R = by[a]; k = sum(r["parts_correct"] for r in R); n = sum(r["n_parts"] for r in R); p, l, h = wilson(k, n)
        xs.append(i); ys.append(100 * p); lo.append(100 * (p - l)); hi.append(100 * (h - p)); cols.append("#2f6f5e" if a.startswith("jev") else "#888888" if a != "oracle" else "#c9a227")
    ax.bar(xs, ys, yerr=[lo, hi], color=cols, capsize=3)
    ax.set_xticks(xs); ax.set_xticklabels([LABEL.get(a, a) for a in [x for x in arms if not x.startswith(("jev_gate", "jev3_gate", "jev2"))]], fontsize=8)
    ax.set_ylabel("parts placed correctly (%)"); ax.set_ylim(0, 100); ax.set_title(f"{title_tag} · 40 seeds · 240 parts per arm · Wilson 95% intervals", fontsize=10)
    for x, y in zip(xs, ys): ax.text(x, y + 3, f"{y:.0f}", ha="center", fontsize=8)
    ax.axhline(ceiling, ls="--", color="#555", lw=1); ax.text(len(xs) - 0.5, ceiling + 1.3, f"facts-only ceiling ≈ {ceiling:.0f}% (perception errors)", ha="right", fontsize=7, color="#555")
    fig.tight_layout(); fig.savefig(out_prefix + "-parts.png", dpi=160); plt.close(fig)
    # Fig B: operating plane
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    def pt(a): R = by[a]; return (sum(r["operator_seconds"] for r in R) / len(R), sum(r["violations"] for r in R) / len(R))
    for a, mk, c in [("greedy", "s", "#888"), ("rules", "s", "#888"), ("lexical", "s", "#888"), ("rules_ask", "D", "#444"), ("jev4", "P", "#1f4f3f"), ("jev5", "X", "#0f3f2f"), ("oracle", "*", "#c9a227")]:
        if a in by: x, y = pt(a); ax.scatter([x], [y], marker=mk, s=70, color=c, zorder=3); ax.annotate(a, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)
    for fam, c, name in [(["jev", "jev_gate0.5", "jev_gate0.7", "jev_gate0.85"], "#2f6f5e", "Jev + confidence gate τ"), (["jev3", "jev3_gate0.7", "jev3_gate0.85"], "#5aa08a", "Jev, code picks part, gate τ")]:
        P = [pt(a) for a in fam if a in by]
        if P: ax.plot([p[0] for p in P], [p[1] for p in P], "-o", color=c, label=name, zorder=4)
        for a in fam:
            if a in by and "gate" in a: x, y = pt(a); ax.annotate("τ=" + a.split("gate")[1], (x, y), textcoords="offset points", xytext=(4, -10), fontsize=7, color=c)
    if "rules" in by and "rules_ask" in by:
        x0, y0 = pt("rules"); x1, y1 = pt("rules_ask"); ax.plot([x0, x1], [y0, y1], "--", color="#aaa", lw=1, label="program's abstention rule (interpolated)")
    ax.set_xlabel("operator seconds per episode"); ax.set_ylabel("violations per episode"); ax.set_title(f"{title_tag} · the handoff operating plane", fontsize=10); ax.legend(fontsize=7); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out_prefix + "-plane.png", dpi=160); plt.close(fig); print("saved", out_prefix + "-parts.png", out_prefix + "-plane.png")

if __name__ == "__main__":
    import os
    tag = os.environ.get("FIG_TAG", "E71/E75 sorting cell"); ceil = float(os.environ.get("FIG_CEILING", "91.2"))
    main(sys.argv[2:], sys.argv[1], title_tag=tag, ceiling=ceil)

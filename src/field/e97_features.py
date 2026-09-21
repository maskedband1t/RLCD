"""E97: per-recording facts from the Eidon IMU stream alone (no video). One pass over a shard, row group by row group.
Usage: PYTHONPATH=src python src/field/e97_features.py data/eidon/imu-0000.parquet data/eidon/e97_features_shard0.parquet"""
import sys, numpy as np, pandas as pd, pyarrow.parquet as pq
SLOTS = {0: "left_hand", 1: "left_forearm", 2: "left_shoulder", 3: "right_hand", 4: "right_forearm", 5: "right_shoulder", 6: "chest"}

def qangle(q):  # angle between consecutive unit quaternions (rad), q: (n,4) as x,y,z,w
    d = np.abs(np.sum(q[1:] * q[:-1], axis=1)); d = np.clip(d, -1.0, 1.0); return 2.0 * np.arccos(d)

def qconj(q): return q * np.array([-1, -1, -1, 1], dtype=q.dtype)
def qmul(a, b):
    x1, y1, z1, w1 = a.T; x2, y2, z2, w2 = b.T
    return np.stack([w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2, w1*w2 - x1*x2 - y1*y2 - z1*z2], axis=1)

def features(df):
    out = {"n_rows": len(df)}; t0, t1 = df.time_ms.min(), df.time_ms.max(); out["duration_s"] = (t1 - t0) / 1000.0
    slots = sorted(df.slot.unique()); out["n_slots"] = len(slots); out["slots_missing"] = ",".join(SLOTS[s] for s in SLOTS if s not in slots)
    per = {}
    for s, g in df.groupby("slot"):
        g = g.sort_values("time_ms"); t = g.time_ms.to_numpy() / 1000.0; q = g[["quat_x", "quat_y", "quat_z", "quat_w"]].to_numpy(np.float64)
        if len(t) < 5: continue
        dt = np.diff(t); ang = qangle(q); speed = ang / np.maximum(dt, 1e-3)   # rad/s
        per[s] = {"t": t[1:], "speed": speed, "q": q, "hz": len(t) / max(1e-3, t[-1] - t[0]), "dropout": float(np.sum(dt[dt > 0.5])) / max(1e-3, t[-1] - t[0]), "orient_var": float(np.var(q, axis=0).sum())}
    out["sample_hz"] = float(np.median([p["hz"] for p in per.values()])) if per else 0.0; out["dropout_frac"] = float(np.max([p["dropout"] for p in per.values()])) if per else 1.0
    for s, name in SLOTS.items():
        p = per.get(s); out[f"speed_{name}"] = float(np.mean(p["speed"])) if p else np.nan; out[f"orient_var_{name}"] = p["orient_var"] if p else np.nan
    # still fraction: 1-s windows in which both hands move slower than 0.15 rad/s (if a hand is missing, use what exists)
    hands = [per[s] for s in (0, 3) if s in per]
    if hands:
        edges = np.arange(t0 / 1000.0, t1 / 1000.0 + 1.0, 1.0); still = np.ones(len(edges) - 1, bool)
        for p in hands:
            idx = np.clip(np.searchsorted(edges, p["t"]) - 1, 0, len(edges) - 2); mx = np.zeros(len(edges) - 1); np.maximum.at(mx, idx, p["speed"]); still &= mx < 0.15
        out["still_frac"] = float(still.mean())
    else: out["still_frac"] = np.nan
    l, r = out.get("speed_left_hand", np.nan), out.get("speed_right_hand", np.nan)
    out["hand_symmetry"] = float(l / (l + r)) if (l == l and r == r and (l + r) > 0) else np.nan   # 0.5 = balanced
    # torso-relative hand pose: variance of chest^-1 * hand (how much the hands move relative to the body)
    if 6 in per:
        for s, name in ((0, "left_hand"), (3, "right_hand")):
            if s in per:
                n = min(len(per[s]["q"]), len(per[6]["q"])); rel = qmul(qconj(per[6]["q"][:n]), per[s]["q"][:n]); out[f"rel_var_{name}"] = float(np.var(rel, axis=0).sum())
    return out

def main(shard, out_path):
    pf = pq.ParquetFile(shard); rows = []; buf = None
    for i in range(pf.metadata.num_row_groups):
        t = pf.read_row_group(i, columns=["recording_id", "time_ms", "slot", "quat_x", "quat_y", "quat_z", "quat_w"]).to_pandas()
        t = t if buf is None else pd.concat([buf, t], ignore_index=True); buf = None
        ids = t.recording_id.to_numpy(); last = ids[-1]
        done = t[ids != last]; buf = t[ids == last]   # the last id may continue in the next row group
        for rid, g in done.groupby("recording_id"): rows.append(dict(recording_id=int(rid), **features(g)))
        if i % 300 == 0: print(f"  row group {i}/{pf.metadata.num_row_groups}, recordings {len(rows)}", flush=True)
    if buf is not None and len(buf):
        for rid, g in buf.groupby("recording_id"): rows.append(dict(recording_id=int(rid), **features(g)))
    df = pd.DataFrame(rows); df.to_parquet(out_path); print(f"features for {len(df)} recordings -> {out_path}")
    print(df.describe().T[["mean", "50%", "min", "max"]].round(3).to_string())

if __name__ == "__main__": main(sys.argv[1], sys.argv[2])

"""S1-E6: capture head_r3 decision records on the WRITTEN bank.

The written-bank records that exist are from heads r6/r7/g1r0; mixing head versions would
confound the calibration-transfer test, so these are captured fresh.
"""
import os, sys, json
sys.path.insert(0, "src")

def main():
    import duck.e93_run as R
    rec = []
    for s in range(0, 20):
        R.episode(s, "laya", record=rec)
        print(f"  seed {s:>2}  cumulative decisions {len(rec)}", flush=True)
    out = "results/duck/s1e6_written_decisions.jsonl"
    with open(out, "w") as f:
        for r in rec:
            a = r.get("answer", {})
            f.write(json.dumps({
                "seed": r["seed"], "event": r.get("event"),
                "choice": a.get("choice"), "conf": a.get("confidence"),
                "acc": r.get("acceptable"),
                "ok": a.get("choice") in (r.get("acceptable") or []),
            }) + "\n")
    print(f"wrote {len(rec)} decisions -> {out}")

if __name__ == "__main__":
    main()

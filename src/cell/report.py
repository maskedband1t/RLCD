"""One command that regenerates the headline tables from the committed results:
    PYTHONPATH=src python -m cell.report
Loop ladder (E77→E92), decision-level calibration (D7 singleton rows), surprise types (D4e), the second checkpoint (D8)."""
import subprocess, sys, os
PY = sys.executable
def run(title, mod, grep=None):
    print(f"\n{'='*100}\n{title}\n{'='*100}")
    out = subprocess.run([PY, mod], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": "src"}).stdout
    if grep: out = "\n".join(l for l in out.splitlines() if any(g in l for g in grep))
    print(out[:12000])
if __name__ == "__main__":
    run("Held-out loop ladder and decision-level heads (E77, E90, E90b, E91, E91c, E92)", "src/cell/e91_eval.py")
    run("Calibration on identical decisions, single-answer rows (D7, D8; top-1 probability)", "src/cell/d7_calibration.py", grep=["[singleton]"])
    run("Unflagged surprises by type (D4e, D8)", "src/cell/d4e_unflagged_types.py")

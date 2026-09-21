"""Run the behavioural scenario suite:  PYTHONPATH=src python -m dispatch  [--raw | --jev]"""
import collections, sys
from dispatch import prepare_state, prepare_state_jev, ask, decide_by_cost
from dispatch.scenarios import S

RAW = "--raw" in sys.argv      # --raw: hand the model the state as written, no code pass
JEV = "--jev" in sys.argv      # --jev: Jev reads the text, code does the arithmetic, Jev judges

def main():
    res = collections.defaultdict(list); fails = []
    for s in S:
        st = s["st"] if RAW else prepare_state_jev(s["st"]) if JEV else prepare_state(s["st"])
        a = ask(st); d, _ = decide_by_cost(a)
        ok = d in s["ok"]; res[s["tier"]].append(ok)
        if not ok: fails.append((s["tier"], s["name"], d, a["p_success"], a["rule_conflict"]))
    for t in sorted(res): print(f"tier {t}: {sum(res[t])}/{len(res[t])}")
    if fails:
        print("\nfailures:")
        for t, n, d, p, c in fails: print(f"  tier {t}  {n:44s} -> {d} (P {p:.2f}, conflict {c:.2f})")
    total = sum(map(sum, res.values())); n = sum(map(len, res.values()))
    print(f"\n{total}/{n} ({'raw' if RAW else 'jev-extract' if JEV else 'prepared'}) — answers are correct BY CONSTRUCTION; "
          "this tests decision logic, not outcomes")
    sys.exit(0 if total == n else 1)

if __name__ == "__main__":
    main()

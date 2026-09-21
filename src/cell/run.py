"""CLI: PYTHONPATH=src python -m cell.run --arms greedy rules lexical oracle --seeds 0-39 --out results/cell/x.jsonl"""
import argparse, json, os, sys, time
from .harness import episode
from .policies import make_policy

def seeds_of(s):
    if "-" in s: a, b = s.split("-"); return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["greedy", "rules", "lexical", "oracle"])
    ap.add_argument("--seeds", default="0-3"); ap.add_argument("--out", default=None)
    ap.add_argument("--record", default=None, help="jsonl of Jev calls (state, options, answer)")
    ap.add_argument("--replay", default=None, help="jsonl of recorded Jev calls to replay instead of calling (replay ONLY unless --replay-live)")
    ap.add_argument("--replay-live", action="store_true", help="hybrid: replay recorded states, call live on misses (E88+)")
    ap.add_argument("--unanticipated", default=None); ap.add_argument("--bank", default="notes")
    args = ap.parse_args()
    replay = None
    if args.replay:
        replay = {}
        for line in open(args.replay):
            r = json.loads(line); replay[r["key"]] = r["answer"]
    out = open(args.out, "a") if args.out else None
    rec_f = open(args.record, "a") if args.record else None
    for arm in args.arms:
        for seed in seeds_of(args.seeds):
            t0 = time.time()
            pkw = {}
            if arm.startswith("jev"):
                pkw = {"record": [], "replay": replay, **({"live": True} if args.replay_live else {})}
            pol = make_policy(arm, **pkw) if (arm.startswith("jev") or arm.startswith("distilled") or arm.startswith("laya") or arm.startswith("sj")) else None
            r = episode(seed, arm, policy=pol, unanticipated=args.unanticipated, bank=args.bank)
            r["wall_s"] = round(time.time() - t0, 1)
            if rec_f and pol is not None:
                for c in pol.record: rec_f.write(json.dumps(dict(c, seed=seed, arm=arm)) + "\n")
                rec_f.flush()
            line = json.dumps(r)
            if out: out.write(line + "\n"); out.flush()
            print(f"{arm:>10} seed {seed:>2} | correct {r['parts_correct']}/{r['n_parts']} viol {r['violations']} | unant {r['unanticipated']:<16} {'ok' if r['unanticipated_correct'] else 'MISS' if r['unanticipated_correct'] is not None else '-':<4} | op {r['operator_seconds']:>5}s asks {r['n_asks']} conf {r.get('n_confirms',0)}/{r.get('n_vetoes',0)}v pauses {r['n_pauses']} | hand {r['person_contact_s']}s broken {r['broken']} floor {r['floor']} lid {r['on_lid']} unplaced {r['unplaced']} | t {r['duration_s']}s dec {r['decisions']} | calls {r.get('jev_calls',0)} miss {r.get('replay_misses',0)} | wall {r['wall_s']}s", flush=True)

if __name__ == "__main__":
    main()

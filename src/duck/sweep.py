"""Parallel sweep runner — the rig's missing piece.

Episodes are independent, so a sweep is embarrassingly parallel; running them one at a time on a
12-core machine was the throughput bottleneck for every experiment so far. Each episode runs in its
own process (MuJoCo, ONNX and the laya head all carry per-process state, so forking mid-run is not
safe), results stream to JSONL with full provenance, and the run is resumable: cells already present
in the output file are skipped.

  PYTHONPATH=src USE_TF=0 python src/duck/sweep.py \
      --body g1 --contact 1 --head results/duck/head_g1_r2 \
      --modes random,selfscore,scorer,oracle --budgets 1,3,6,15 \
      --streams 0-9 --seeds 0-19 --workers 8 --out results/duck/s1e10.jsonl
"""
import os, sys, json, time, argparse, subprocess, itertools, hashlib
import multiprocessing as mp

sys.path.insert(0, "src")


def _spec(text):
    """'0-9' -> [0..9];  '1,3,6' -> [1,3,6];  '4' -> [4]"""
    out = []
    for part in str(text).split(","):
        if "-" in part[1:]:
            lo, _, hi = part.partition("-")
            out += list(range(int(lo), int(hi) + 1))
        elif part:
            out.append(int(part))
    return out


def provenance(env):
    try:
        h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                    stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        h = None
    try:
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"],
                                             stderr=subprocess.DEVNULL, text=True).strip())
    except Exception:
        dirty = None
    return {"git": h, "git_dirty": dirty, "env": env,
            "config_sha": hashlib.sha1(json.dumps(env, sort_keys=True).encode()).hexdigest()[:12]}


def _run_one(job):
    """One episode in a fresh process. Returns the record, or an error record."""
    mode, budget, stream, seed, env = job
    for k, v in env.items():
        if v is not None:
            os.environ[k] = str(v)
    sys.path.insert(0, "src")
    try:
        from duck import e93_run as R
        from duck.s1e9_select import SelectArm
        SelectArm.MODE, SelectArm.N, SelectArm.STREAM = mode, budget, stream
        made = {}
        _orig = R.make_arm

        def make_arm(name):
            if name == "select":
                a = SelectArm(); made["arm"] = a; return a
            return _orig(name)
        R.make_arm = make_arm

        t0 = time.time()
        out = R.episode(seed, "select")
        out.update(mode=mode, budget=budget, stream=stream,
                   substituted=getattr(made.get("arm"), "n_substituted", 0),
                   wall_s=round(time.time() - t0, 2))
        out.pop("log", None)          # keep the file small; the per-decision log is not analysed
        return out
    except Exception as e:
        import traceback
        return {"mode": mode, "budget": budget, "stream": stream, "seed": seed,
                "error": f"{type(e).__name__}: {e}", "traceback": traceback.format_exc()[-800:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", default="g1")
    ap.add_argument("--contact", default="1")
    ap.add_argument("--head", default="results/duck/head_g1_r2")
    ap.add_argument("--modes", default="random,selfscore,scorer,oracle")
    ap.add_argument("--budgets", default="1,3,6,15")
    ap.add_argument("--streams", default="0")
    ap.add_argument("--seeds", default="0-19")
    ap.add_argument("--workers", type=int, default=6)   # measured sweet spot on the M-series mini: more workers contend on MPS
    ap.add_argument("--device", default="mps", help="measured: mps+6 workers = 0.30 ep/s (1.6x serial); cpu+8 workers = 0.18 ep/s, because CPU head inference is ~8x slower and cancels the parallelism exactly")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    env = {"DUCK_BODY": a.body, "DUCK_CONTACT": a.contact, "DUCK_HEAD": a.head,
           "USE_TF": "0", "PYTHONPATH": "src",
           # each worker is single-threaded; parallelism comes from processes, not BLAS
           "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
           "DUCK_DEVICE": a.device}

    modes = a.modes.split(",")
    budgets, streams, seeds = _spec(a.budgets), _spec(a.streams), _spec(a.seeds)
    jobs = [(m, b, st, sd, env) for m in modes for b in budgets for st in streams for sd in seeds]

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            try:
                r = json.loads(line)
                done.add((r.get("mode"), r.get("budget"), r.get("stream"), r.get("seed")))
            except Exception:
                pass
    todo = [j for j in jobs if (j[0], j[1], j[2], j[3]) not in done]

    prov = provenance(env)
    print(f"sweep: {len(jobs)} cells, {len(done)} already done, {len(todo)} to run")
    print(f"  workers={a.workers}  git={prov['git']}{' (dirty)' if prov['git_dirty'] else ''}  config={prov['config_sha']}")
    if not todo:
        return

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out.replace(".jsonl", ".provenance.json"), "w") as fh:
        json.dump(prov, fh, indent=2)

    t0 = time.time()
    n_err = 0
    ctx = mp.get_context("spawn")
    with ctx.Pool(a.workers) as pool, open(a.out, "a") as fh:
        for i, rec in enumerate(pool.imap_unordered(_run_one, todo, chunksize=1), 1):
            rec["config_sha"] = prov["config_sha"]
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            if "error" in rec:
                n_err += 1
                if n_err <= 3:
                    print(f"  ERROR {rec['mode']}/{rec['budget']}/{rec['stream']}/{rec['seed']}: {rec['error']}")
            if i % 25 == 0 or i == len(todo):
                el = time.time() - t0
                print(f"  {i}/{len(todo)}  {el:.0f}s  {i/el:.2f} ep/s  eta {(len(todo)-i)/(i/el):.0f}s  errors={n_err}",
                      flush=True)
    print(f"done in {time.time()-t0:.0f}s, {n_err} errors -> {a.out}")


if __name__ == "__main__":
    main()

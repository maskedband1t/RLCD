#!/usr/bin/env python3
"""Turn a pending-state batch into cache entries, and report what is left.

  python src/frontier_dispatch.py show          # print the unanswered batch as prompts
  python src/frontier_dispatch.py load answers.jsonl   # write answers into the cache

`answers.jsonl` is one object per line: {"key": "<fingerprint>", "choice": "<option>",
"confidence": 0.0-1.0}. Anything else on the line is preserved in the record.

**Why a blind answerer.** The bench, the arms and this prompt were all written by the same author, so
a ceiling arm answered by that author measures the author. The states handed over carry the situation
and the option list and nothing else -- no repo access, no bench name, no knowledge of what any other
arm chose, no access to the acceptable set. That is the independent-authorship pattern this programme
already adopted, applied to the ceiling rather than to the situations.
"""
import json, os, sys

PENDING = os.environ.get("FRONTIER_PENDING", "results/frontier_pending.jsonl")
CACHE = os.environ.get("FRONTIER_CACHE", "results/frontier_cache.jsonl")


def _answered():
    a = set()
    if os.path.exists(CACHE):
        for line in open(CACHE):
            try: a.add(json.loads(line)["key"])
            except Exception: pass
    return a


def _pending():
    seen, out = set(), []
    if not os.path.exists(PENDING): return out
    done = _answered()
    for line in open(PENDING):
        try: r = json.loads(line)
        except Exception: continue
        if r["key"] in seen or r["key"] in done: continue
        seen.add(r["key"]); out.append(r)
    return out


def show():
    ps = _pending()
    print(f"# {len(ps)} unanswered states\n")
    for i, r in enumerate(ps, 1):
        print(f"--- STATE {i}  key={r['key']}")
        print(json.dumps(r["facts"], indent=1, default=str))
        print("OPTIONS:")
        for k, v in sorted(r["options"].items()): print(f"  {k}: {v}")
        print()


def load(path):
    keys = {r["key"] for r in _pending()}
    n = bad = 0
    os.makedirs(os.path.dirname(CACHE) or ".", exist_ok=True)
    with open(CACHE, "a") as out:
        for line in open(path):
            try: d = json.loads(line)
            except Exception: bad += 1; continue
            if "key" not in d or "choice" not in d: bad += 1; continue
            ans = {"choice": d["choice"], "confidence": d.get("confidence"),
                   "probabilities": {d["choice"]: d["confidence"]} if d.get("confidence") is not None else {},
                   "source": "blind-subagent", "model": d.get("model", "claude-frontier")}
            out.write(json.dumps({"key": d["key"], "answer": ans,
                                  "model": ans["model"], "backend": "blind-subagent"}) + "\n")
            n += 1
    print(f"wrote {n} answers ({bad} malformed). {len(keys) - n} of this batch still unanswered.")


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    if sys.argv[1] == "show": show()
    elif sys.argv[1] == "load": load(sys.argv[2])
    else: sys.exit(__doc__)

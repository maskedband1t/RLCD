"""Hugging Face watch for RLCD / System One / Jev artefacts.

Queries the public HF API for models, datasets and spaces matching a set of
search terms, keeps only entries with a strong marker (id or tags mention
rlcd, system-one, systemone, typesafe, or a standalone 'jev' token), and diffs
against the last snapshot in data/field/hf_snapshot.json. New entries and
notable changes are appended to notebook/field/hf-watch.md with a date.
Stdlib only. Read-only. No key required.
"""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAP = os.path.join(ROOT, "data", "field", "hf_snapshot.json")
LOG = os.path.join(ROOT, "notebook", "field", "hf-watch.md")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
TERMS = ["rlcd", "jev", "system-one", "systemone", "system one", "typesafe", "calibrated decision", "jevlike", "openjev"]
KINDS = ["models", "datasets", "spaces"]
STRONG = re.compile(r"rlcd|system[-_ ]?one|typesafe|jevlike|openjev|(^|[-_/. ])jev([-_/. ]|$)", re.I)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def scan():
    found = {}
    for kind in KINDS:
        for term in TERMS:
            q = urllib.parse.urlencode({"search": term, "limit": 100, "sort": "lastModified", "direction": -1})
            try:
                items = get(f"https://huggingface.co/api/{kind}?{q}")
            except Exception as e:
                print(f"  ! {kind}/{term}: {e}", file=sys.stderr); continue
            for it in items:
                _id = it.get("id") or it.get("modelId") or ""
                tags = " ".join(it.get("tags") or [])
                if not (STRONG.search(_id) or STRONG.search(tags)):
                    continue
                # 'RLCD' also names a 2023 method (contrast distillation) and 'jev' is a name/prefix;
                # anything created before Jev's launch week is a collision, not a reproduction.
                created = str(it.get("createdAt") or "")
                if created and created < "2026-09-10":
                    continue
                key = f"{kind}/{_id}"
                found[key] = {
                    "kind": kind, "id": _id,
                    "likes": it.get("likes", 0), "downloads": it.get("downloads", 0),
                    "lastModified": it.get("lastModified"), "createdAt": it.get("createdAt"),
                    "tags": (it.get("tags") or [])[:12],
                    "pipeline": it.get("pipeline_tag"),
                }
            time.sleep(0.4)
    return found

def main():
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    prev = json.load(open(SNAP)) if os.path.exists(SNAP) else {}
    cur = scan()
    new = {k: v for k, v in cur.items() if k not in prev}
    risen = {k: (prev[k]["likes"], v["likes"]) for k, v in cur.items()
             if k in prev and v["likes"] - prev[k]["likes"] >= 20}
    os.makedirs(os.path.dirname(SNAP), exist_ok=True)
    json.dump(cur, open(SNAP, "w"), indent=1, sort_keys=True)
    lines = [f"\n### {now} · {len(cur)} tracked ({sum(v['kind']=='models' for v in cur.values())} models, "
             f"{sum(v['kind']=='datasets' for v in cur.values())} datasets, {sum(v['kind']=='spaces' for v in cur.values())} spaces) · "
             f"{len(new)} new · {len(risen)} rose ≥20 likes"]
    for k, v in sorted(new.items(), key=lambda kv: -(kv[1]["likes"] or 0)):
        lines.append(f"- NEW {v['kind'][:-1]} `{v['id']}` · likes {v['likes']} · dl {v['downloads']} · created {str(v['createdAt'])[:10]} · tags {', '.join(v['tags'][:6])}")
    for k, (a, b) in sorted(risen.items(), key=lambda kv: -(kv[1][1]-kv[1][0])):
        lines.append(f"- ROSE `{k}` likes {a} → {b}")
    if not prev:
        lines.append("- (baseline snapshot; everything above is 'new' by construction)")
    out = "\n".join(lines)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    if not os.path.exists(LOG):
        open(LOG, "w").write("# Hugging Face watch · RLCD / System One / Jev artefacts\n\nAppended by `src/field/hf_watch.py`; read-only API queries; strong-marker filter (rlcd, system-one, typesafe, standalone 'jev').\n")
    open(LOG, "a").write(out + "\n")
    print(out)

if __name__ == "__main__":
    main()


# --- gated-repo access check (added 2026-09-19): reports whether Meta has approved the SAM 3 licence request.
# Reads HF_TOKEN from the environment only; prints a status word per repo and never the token.
def gate_status(repos=("facebook/sam3", "facebook/sam3.1")):
    import os, urllib.request
    tok = os.environ.get("HF_TOKEN")
    if not tok:
        return {r: "no HF_TOKEN in environment" for r in repos}
    out = {}
    for r in repos:
        req = urllib.request.Request(f"https://huggingface.co/api/models/{r}/auth-check", headers={"Authorization": f"Bearer {tok}"})
        try:
            urllib.request.urlopen(req, timeout=20); out[r] = "GRANTED"
        except Exception as e:  # HTTPError carries the code
            code = getattr(e, "code", None); out[r] = {403: "pending or not accepted", 401: "token rejected"}.get(code, f"error {code or e}")
    return out


if __name__ == "__main__":
    try:
        for repo, status in gate_status().items():
            print(f"SAM3 gate · {repo}: {status}", flush=True)
    except Exception as exc:
        print(f"SAM3 gate check failed: {exc}", flush=True)

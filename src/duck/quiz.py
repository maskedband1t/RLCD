"""Human baseline on the duck bench: the same facts and options the owned head saw, shown to a person, scored by code's
acceptable sets. Answers the attribution question behind E96: are the unseen notes readable from the representation?
  build: PYTHONPATH=src python src/duck/quiz.py build --records results/duck/e96_record.jsonl --out results/duck/quiz
  score: PYTHONPATH=src python src/duck/quiz.py score --key results/duck/quiz/key.json --answers <answers.json>
The page (results/duck/quiz/duck-quiz.html) is a local file; the answer key never enters it."""
import json, random, argparse, os, html, collections, sys
sys.path.insert(0, os.path.dirname(__file__)); from head import render_state, compact_option

def build(records, out, seed=0, per_event_unseen=10, anticipated=10):
    rows = [json.loads(l) for l in open(records)]
    rows = [r for r in rows if r.get("arm", "").startswith("laya") and r.get("acceptable") and r.get("options")]
    rnd = random.Random(seed); items = []
    by = collections.defaultdict(list)
    for r in rows: by[(r["event"], r["seed"] >= 40)].append(r)
    for (ev, unseen), pool in sorted(by.items()):
        if unseen:
            wrong = [r for r in pool if r["answer"]["choice"] not in r["acceptable"]]; right = [r for r in pool if r["answer"]["choice"] in r["acceptable"]]
            rnd.shuffle(wrong); rnd.shuffle(right); pick = wrong[:per_event_unseen // 2] + right[:per_event_unseen - per_event_unseen // 2]
        else:
            rnd.shuffle(pool); pick = pool[:max(1, anticipated // 4)]
        items += pick
    rnd.shuffle(items)
    key = []; page = []
    for i, r in enumerate(items):
        opts = list(r["options"].items()); rnd.shuffle(opts)
        key.append({"i": i, "event": r["event"], "seed": r["seed"], "bank": "unseen" if r["seed"] >= 40 else "anticipated", "acceptable": r["acceptable"],
                    "head_choice": r["answer"]["choice"], "head_conf": r["answer"].get("confidence"), "options": [k for k, _ in opts]})
        page.append({"i": i, "state": render_state(r["state"]), "options": [(k, compact_option(k, v)) for k, v in opts]})
    os.makedirs(out, exist_ok=True); json.dump(key, open(os.path.join(out, "key.json"), "w"), indent=1)
    cards = []
    for it in page:
        radios = "".join(f'<label><input type="radio" name="q{it["i"]}" value="{html.escape(k)}"> {html.escape(t)}</label>' for k, t in it["options"])
        cards.append(f'<section class="card" id="c{it["i"]}"><div class="n">{it["i"] + 1} / {len(page)}</div><pre>{html.escape(it["state"])}</pre>'
                     f'<div class="opts">{radios}</div><label class="conf">How sure are you? <input type="range" name="s{it["i"]}" min="50" max="100" value="75" step="5" oninput="this.nextElementSibling.textContent=this.value+\' %\'"><output>75 %</output></label></section>')
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Duck bench: the person's turn</title>
<style>
:root{{--bg:#f7f6f2;--ink:#1e1d1a;--muted:#6b6862;--line:#d9d6ce;--acc:#2f6f5e;--card:#ffffff}}
@media (prefers-color-scheme: dark){{:root{{--bg:#191917;--ink:#ecebe6;--muted:#9c9a93;--line:#3a3935;--acc:#7cc4ad;--card:#232321}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,Segoe UI,Helvetica,Arial,sans-serif;padding:24px 16px 96px}}
main{{max-width:720px;margin:0 auto}} h1{{font-size:1.5rem;margin:0 0 .25rem}} p.lead{{color:var(--muted);margin:0 0 1.5rem}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:0 0 18px}}
.n{{font-size:.8rem;color:var(--muted);letter-spacing:.04em;text-transform:uppercase}}
pre{{white-space:pre-wrap;font:14px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;background:transparent;margin:.5rem 0 1rem;padding:0}}
.opts label{{display:block;padding:6px 8px;border-radius:6px}} .opts label:hover{{background:rgba(47,111,94,.08)}}
.conf{{display:flex;gap:10px;align-items:center;color:var(--muted);font-size:.9rem;margin-top:.75rem}} input[type=range]{{flex:1;accent-color:var(--acc)}}
.bar{{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;align-items:center;justify-content:center}}
button{{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:10px 16px;font-size:1rem}} #status{{color:var(--muted);font-size:.9rem}}
textarea{{width:100%;height:120px;margin-top:8px;font:12px ui-monospace,Menlo,monospace}}
</style></head><body><main>
<h1>Duck bench: the person's turn</h1>
<p class="lead">You are the robot's judgment for one decision at a time. Each card is exactly what the robot's model saw: the facts as text, and the actions code offered. Pick the action you would take now and say how sure you are. There are {len(page)} cards; there is no clock. Your answers stay in this browser until you press Export and paste the text into a file.</p>
{''.join(cards)}
<div class="card"><div class="n">Export</div><p>Press Export, copy the text below into <code>answers.json</code>, and send it back.</p><textarea id="out" readonly></textarea></div>
</main>
<div class="bar"><span id="status">0 / {len(page)} answered</span><button onclick="exportAnswers()">Export</button></div>
<script>
const N={len(page)};
function collect(){{const a=[];for(let i=0;i<N;i++){{const r=document.querySelector(`input[name=q${{i}}]:checked`);const s=document.querySelector(`input[name=s${{i}}]`);a.push({{i:i,choice:r?r.value:null,sure:s?Number(s.value):null}});}}return a;}}
function save(){{try{{localStorage.setItem('duckquiz',JSON.stringify(collect()));}}catch(e){{}}const n=collect().filter(x=>x.choice).length;document.getElementById('status').textContent=n+' / '+N+' answered';}}
function exportAnswers(){{save();document.getElementById('out').value=JSON.stringify({{answered_at:new Date().toISOString(),answers:collect()}});document.getElementById('out').focus();document.getElementById('out').select();}}
document.addEventListener('change',save);
try{{const s=JSON.parse(localStorage.getItem('duckquiz')||'[]');for(const x of s){{if(x.choice){{const r=document.querySelector(`input[name=q${{x.i}}][value="${{x.choice}}"]`);if(r)r.checked=true;}}if(x.sure){{const g=document.querySelector(`input[name=s${{x.i}}]`);if(g){{g.value=x.sure;g.nextElementSibling.textContent=x.sure+' %';}}}}}}}}catch(e){{}}
save();
</script></body></html>"""
    open(os.path.join(out, "duck-quiz.html"), "w").write(doc)
    n_un = sum(k["bank"] == "unseen" for k in key); print(f"quiz: {len(key)} cards ({n_un} unseen, {len(key) - n_un} anticipated) -> {out}/duck-quiz.html; key -> {out}/key.json (not in the page)")

def score(key_path, answers_path):
    key = {k["i"]: k for k in json.load(open(key_path))}; ans = json.load(open(answers_path))["answers"]
    tot = collections.Counter(); ok = collections.Counter(); head_ok = collections.Counter(); sure = []; hits = []
    for a in ans:
        k = key[a["i"]]
        if not a.get("choice"): continue
        g = (k["bank"], k["event"]); tot[g] += 1; h = a["choice"] in k["acceptable"]; ok[g] += h; head_ok[g] += k["head_choice"] in k["acceptable"]
        if a.get("sure"): sure.append(a["sure"] / 100); hits.append(h)
    print("bank / event: person acceptable | the head on the same states")
    for g in sorted(tot): print(f"  {g[0]:11s} {g[1]:14s} {ok[g]:2d}/{tot[g]:<2d} | head {head_ok[g]:2d}/{tot[g]}")
    n = sum(tot.values()); print(f"  all {sum(ok.values())}/{n} | head {sum(head_ok.values())}/{n}")
    if sure: print(f"  stated sureness {sum(sure)/len(sure):.2f} vs hit rate {sum(hits)/len(hits):.2f} (over {sum(sure)/len(sure)-sum(hits)/len(hits):+.2f})")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["build", "score"]); ap.add_argument("--records", default="results/duck/e96_record.jsonl"); ap.add_argument("--out", default="results/duck/quiz")
    ap.add_argument("--key", default="results/duck/quiz/key.json"); ap.add_argument("--answers"); a = ap.parse_args()
    build(a.records, a.out) if a.cmd == "build" else score(a.key, a.answers)

"""E138: Contrastive Language Models (Kwok et al., 2026) as a second System One model in the judge seat, run locally.

Reproduces the reference engine (third_party/CLM/src/clm/engine.py) without vLLM: the state is rendered by the engine's own
schema (to_text, the question's instructions appended after a blank line), each candidate is the option's text verbatim,
both are embedded with Qwen3-8B last-token pooling (the tail 2048 tokens, no special tokens, L2-normalised), projected by
the reference heads (CLM_v0.1-8B.pt), and softmax(exp(logit_scale) * cosine / temperature) is the answer. The client speaks
the harness's TypeSafe shape: system_one(state=..., model=..., questions={id: Choice|Noul}) -> .answers[id].choice/.confidence/
.probabilities, .usage.input_tokens/.output_tokens. Option embeddings are cached, so a decision costs one state embedding."""
import os, sys, time, types, collections
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "third_party", "CLM", "src"))
from clm.schema import build_pairs, answer_from_logits          # the engine's own text and answer code
from clm.heads import HeadPair, default_checkpoint, HF_FILE

ENCODER = os.environ.get("CLM_ENCODER", "Qwen/Qwen3-8B"); MAX_TOKENS = int(os.environ.get("CLM_MAX_TOKENS", "2048"))

def to_question(q):
    """typesafe_sdk Choice / Noul / dict -> the engine's question dict."""
    if isinstance(q, dict): return q
    name = type(q).__name__.lower()
    if name == "choice": return {"type": "choice", "instructions": q.instructions, "criteria": dict(q.criteria)}
    if name == "noul": return {"type": "noul", "instructions": getattr(q, "instructions", None)}
    if name == "score": return {"type": "score", "instructions": q.instructions, "criteria": list(q.criteria)}
    raise TypeError(f"unknown question type {type(q)}")

class LocalEmbedder:
    """Qwen3-8B last-token pooled embeddings on MPS (bf16), one text at a time, cached by text."""
    def __init__(self, model=ENCODER, device=None, cache_size=50_000):
        import torch
        from transformers import AutoTokenizer, AutoModel
        self.torch = torch; self.device = device or ("mps" if torch.backends.mps.is_available() else "cpu")
        self.tok = AutoTokenizer.from_pretrained(model)
        self.model = AutoModel.from_pretrained(model, dtype=torch.bfloat16).to(self.device).eval()
        self.cache = collections.OrderedDict(); self.cache_size = cache_size; self.tokens = 0
    def _one(self, text):
        ids = self.tok(text, add_special_tokens=False)["input_ids"]
        if not ids: ids = self.tok(" ", add_special_tokens=False)["input_ids"]
        ids = ids[-MAX_TOKENS:]; self.tokens += len(ids)
        x = self.torch.tensor([ids], device=self.device)
        with self.torch.no_grad(): h = self.model(input_ids=x).last_hidden_state[0, -1].float().cpu().numpy()
        return h / (np.linalg.norm(h) + 1e-12)
    def embed(self, texts):
        out = []
        for t in texts:
            v = self.cache.get(t)
            if v is None:
                v = self._one(t); self.cache[t] = v
                while len(self.cache) > self.cache_size: self.cache.popitem(last=False)
            else: self.cache.move_to_end(t)
            out.append(v)
        return np.stack(out)

class ClmLocalClient:
    def __init__(self, checkpoint=None, temperature=1.0, embedder=None):
        path = checkpoint or default_checkpoint() or os.path.join(ROOT, "third_party", "CLM", "checkpoints", HF_FILE)
        if not os.path.exists(path): raise FileNotFoundError(f"CLM head checkpoint not found at {path} (set CLM_CKPT)")
        self.heads = HeadPair("clm", path, device="cpu").ensure(); self.temperature = temperature
        self.embedder = embedder or LocalEmbedder()
    def system_one(self, state, model="clm-local", questions=None, temperature=None):
        qs = {k: to_question(q) for k, q in (questions or {}).items()}; pairs = build_pairs(state, qs)
        t0 = time.time(); tok0 = self.embedder.tokens
        states = self.embedder.embed([p[0] for p in pairs.values()])
        cands = self.embedder.embed([t for p in pairs.values() for t in p[2]])
        zq = self.heads.project_states(states.astype(np.float32)).cpu().numpy(); za = self.heads.project_actions(cands.astype(np.float32)).cpu().numpy()
        answers, k = {}, 0
        for i, (qid, (_, keys, texts)) in enumerate(pairs.items()):
            cos = za[k:k + len(texts)] @ zq[i]; k += len(texts)
            a = answer_from_logits(qs[qid], keys, (self.heads.scale * cos / (temperature or self.temperature)).tolist())
            answers[qid] = types.SimpleNamespace(**a)
        usage = types.SimpleNamespace(input_tokens=self.embedder.tokens - tok0, output_tokens=0, billing_units=len(qs), latency=time.time() - t0)
        return types.SimpleNamespace(model=model, answers=answers, usage=usage)

if __name__ == "__main__":   # what CLM reads for one station decision, without weights
    os.environ.setdefault("DUCK_BODY", "pick"); sys.path.insert(0, os.path.join(ROOT, "src"))
    from picking.station import Station
    from typesafe_sdk import Choice
    st = Station(3060); f = st.facts(); opts = st.options()
    q = to_question(Choice(instructions={"role": "a picking robot at a warehouse station", "ask": "Which single action should the robot take right now?"}, criteria=opts))
    pairs = build_pairs(f, {"action": q}); text, keys, cands = pairs["action"]
    print("=== state text the encoder sees ===\n" + text + "\n=== candidates ===")
    for k_, c in zip(keys, cands): print(f"  [{k_}] {c}")

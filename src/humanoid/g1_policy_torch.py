"""E140: the G1 walking policy (MuJoCo Playground's exported g1_policy.onnx) lifted into torch, so it can be post-trained.
Graph: obs -> (obs - mean) * inv_std -> Gemm 103->512 -> SiLU -> 512->256 -> SiLU -> 256->128 -> SiLU -> 128->58 -> split (29 mean, 29 log-std) -> tanh(mean).
The exported policy acts deterministically with tanh(mean); the log-std half is kept for PPO fine-tuning."""
import os, numpy as np, torch, torch.nn as nn
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ONNX = os.path.join(ROOT, "third_party", "mujoco_playground", "mujoco_playground", "experimental", "sim2sim", "onnx", "g1_policy.onnx")

class G1Policy(nn.Module):
    def __init__(self, obs_dim=103, act_dim=29, hidden=(512, 256, 128)):
        super().__init__()
        self.register_buffer("mean", torch.zeros(obs_dim)); self.register_buffer("inv_std", torch.ones(obs_dim))
        dims = [obs_dim, *hidden]; self.layers = nn.ModuleList(nn.Linear(a, b) for a, b in zip(dims[:-1], dims[1:])); self.out = nn.Linear(dims[-1], 2 * act_dim); self.act_dim = act_dim
    def trunk(self, obs):
        x = (obs - self.mean) * self.inv_std
        for l in self.layers: x = nn.functional.silu(l(x))
        return self.out(x)
    def forward(self, obs):
        """-> (tanh(mean), log_std): the exported deterministic action and the Gaussian's log-std."""
        h = self.trunk(obs); mu, log_std = h[..., :self.act_dim], h[..., self.act_dim:]
        return torch.tanh(mu), log_std
    def act(self, obs_np):
        with torch.no_grad(): return self.forward(torch.as_tensor(obs_np, dtype=torch.float32))[0].numpy()

def load_from_onnx(path=ONNX):
    import onnx
    from onnx import numpy_helper
    g = onnx.load(path).graph; W = {t.name: numpy_helper.to_array(t) for t in g.initializer}
    pol = G1Policy()
    sub = [n for n in g.node if n.op_type == "Sub"][0]; mul0 = [n for n in g.node if n.op_type == "Mul"][0]
    pol.mean.copy_(torch.from_numpy(W[sub.input[1]].astype(np.float32))); pol.inv_std.copy_(torch.from_numpy(W[mul0.input[1]].astype(np.float32)))
    gemms = [n for n in g.node if n.op_type == "Gemm"]
    for lin, n in zip([*pol.layers, pol.out], gemms):
        w, b = W[n.input[1]].astype(np.float32), W[n.input[2]].astype(np.float32)
        transB = any(a.name == "transB" and a.i == 1 for a in n.attribute)
        w_t = w if transB else w.T   # nn.Linear stores [out, in]
        assert w_t.shape == tuple(lin.weight.shape), (w_t.shape, tuple(lin.weight.shape))
        with torch.no_grad(): lin.weight.copy_(torch.from_numpy(np.ascontiguousarray(w_t))); lin.bias.copy_(torch.from_numpy(b))
    return pol

class EditActor(nn.Module):
    """EXPO-style post-training (Dong & Finn, 2026): the exported policy stays frozen and a small residual network edits its
    action within +-delta_max (in the [-1, 1] action scale; 0.15 = 0.075 rad at the joints). The residual starts at zero, so
    the edited policy is the base policy at step 0 and all of RL's volatility is confined to the bounded edit."""
    def __init__(self, base, delta_max=0.15, h=128, log_std_init=-1.5):
        super().__init__(); self.base = base
        for p_ in self.base.parameters(): p_.requires_grad_(False)
        self.register_buffer("mean", base.mean.clone()); self.register_buffer("inv_std", base.inv_std.clone()); self.delta_max = delta_max; self.log_std_init = log_std_init
        self.net = nn.Sequential(nn.Linear(103, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(), nn.Linear(h, 58))
        nn.init.zeros_(self.net[-1].weight); nn.init.zeros_(self.net[-1].bias)
    def trunk(self, obs):
        h = self.net((obs - self.mean) * self.inv_std); return torch.cat([h[..., :29], h[..., 29:] + self.log_std_init], -1)
    def action_from_pre(self, obs, pre):
        with torch.no_grad(): base_a, _ = self.base(obs)
        return torch.clamp(base_a + self.delta_max * torch.tanh(pre), -1.0, 1.0)
    def forward(self, obs):
        h = self.trunk(obs); return self.action_from_pre(obs, h[..., :29]), h[..., 29:]
    def act(self, obs_np):
        with torch.no_grad(): return self.forward(torch.as_tensor(obs_np, dtype=torch.float32))[0].numpy()

class Runner:
    """Drop-in for the fetch room's onnxruntime session: run(["continuous_actions"], {"obs": (1, 103)}) -> [(1, 29)]."""
    def __init__(self, path):
        sd = torch.load(path, map_location="cpu"); actor_sd = sd["actor"] if "actor" in sd else sd
        self.pol = EditActor(G1Policy(), delta_max=sd.get("delta_max", 0.15)) if sd.get("edit") else G1Policy(); self.pol.load_state_dict(actor_sd); self.pol.eval()
    def run(self, outputs, feed): return [self.pol.act(np.asarray(feed["obs"], np.float32)[0]).reshape(1, -1)]

if __name__ == "__main__":
    import onnxruntime as rt
    pol = load_from_onnx(); sess = rt.InferenceSession(ONNX, providers=["CPUExecutionProvider"])
    rng = np.random.RandomState(0); err = []
    for _ in range(50):
        o = (rng.randn(1, 103) * 0.5).astype(np.float32); a_onnx = sess.run(["continuous_actions"], {"obs": o})[0][0]; a_t = pol.act(o[0])
        err.append(float(np.max(np.abs(a_onnx - a_t))))
    print(f"onnx vs torch on 50 random observations: max abs diff {max(err):.2e}; params {sum(p.numel() for p in pol.parameters()):,}")

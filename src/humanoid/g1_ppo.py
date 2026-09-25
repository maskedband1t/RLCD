"""E140: PPO fine-tuning of the exported G1 walking policy (torch, CPU) in the stop-start locomotion environment.
The actor starts from the exported weights (mean and log-std heads intact; actions are tanh of a Gaussian sample, as in
Brax's NormalTanh); a fresh critic is fitted first with the actor frozen, then both train. Small actor learning rate: this is
post-training, not training. Checkpoints hold {"actor", "critic", "iter", "steps", "eval"}; the best by the evaluation score
(fall rate, then stand speed, then tracking) is kept as best.pt and read by the fetch room through G1_POLICY_PT."""
import os, sys, time, math, json, argparse, numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from humanoid.g1_policy_torch import load_from_onnx, G1Policy, EditActor
from humanoid.g1_loco_env import G1LocoEnv, evaluate

def log_prob_tanh(mu, log_std, pre):
    """log-density of action = tanh(pre), pre ~ N(mu, exp(log_std))."""
    var = torch.exp(2 * log_std); lp = -0.5 * ((pre - mu) ** 2 / var + 2 * log_std + math.log(2 * math.pi))
    return (lp - torch.log(1 - torch.tanh(pre) ** 2 + 1e-6)).sum(-1)

class Critic(nn.Module):
    def __init__(self, mean, inv_std, obs_dim=103, h=256):
        super().__init__(); self.register_buffer("mean", mean.clone()); self.register_buffer("inv_std", inv_std.clone())
        self.net = nn.Sequential(nn.Linear(obs_dim, h), nn.SiLU(), nn.Linear(h, h), nn.SiLU(), nn.Linear(h, 1))
    def forward(self, obs): return self.net((obs - self.mean) * self.inv_std).squeeze(-1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/humanoid/g1_pt"); ap.add_argument("--envs", type=int, default=16); ap.add_argument("--horizon", type=int, default=256)
    ap.add_argument("--iters", type=int, default=100000); ap.add_argument("--hours", type=float, default=8.0); ap.add_argument("--actor-lr", type=float, default=3e-5); ap.add_argument("--critic-lr", type=float, default=5e-4)
    ap.add_argument("--warmup", type=int, default=5); ap.add_argument("--epochs", type=int, default=4); ap.add_argument("--minibatch", type=int, default=512); ap.add_argument("--clip", type=float, default=0.2); ap.add_argument("--gamma", type=float, default=0.99); ap.add_argument("--lam", type=float, default=0.95)
    ap.add_argument("--edit-policy", action="store_true", help="EXPO-style: freeze the exported policy, train a bounded residual edit"); ap.add_argument("--delta-max", type=float, default=0.15); ap.add_argument("--eval-every", type=int, default=20); ap.add_argument("--eval-episodes", type=int, default=20); ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); torch.manual_seed(a.seed); torch.set_num_threads(max(1, os.cpu_count() - 4))
    log = lambda m: print(m, flush=True)
    actor = EditActor(load_from_onnx(), delta_max=a.delta_max) if a.edit_policy else load_from_onnx(); critic = Critic(actor.mean, actor.inv_std); envs = [G1LocoEnv(seed=a.seed * 1000 + i) for i in range(a.envs)]
    opt_a = torch.optim.Adam([p_ for p_ in actor.parameters() if p_.requires_grad], lr=a.actor_lr if not a.edit_policy else 3e-4); opt_c = torch.optim.Adam(critic.parameters(), lr=a.critic_lr)
    obs = np.stack([e.reset() for e in envs]); t_start = time.time(); steps = 0
    base = evaluate(actor.act, n_episodes=a.eval_episodes, seed=5000); log(f"iter 0 (shipped policy) eval {json.dumps(base)}"); best = (base["fall_rate"], base["stand_speed_mean"] or 0, base["rmse_vx"]); best_iter = 0
    torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(), "iter": 0, "steps": 0, "eval": base, "edit": a.edit_policy, "delta_max": a.delta_max}, os.path.join(a.out, "best.pt"))
    for it in range(1, a.iters + 1):
        if (time.time() - t_start) / 3600 > a.hours: log(f"time budget reached at iter {it - 1}"); break
        O = np.zeros((a.horizon, a.envs, 103), np.float32); PRE = np.zeros((a.horizon, a.envs, 29), np.float32); LP = np.zeros((a.horizon, a.envs), np.float32); R = np.zeros((a.horizon, a.envs), np.float32); D = np.zeros((a.horizon, a.envs), np.float32); V = np.zeros((a.horizon + 1, a.envs), np.float32)
        falls = 0; ep_rew = []; cur = np.zeros(a.envs); stand = []
        actor.eval(); critic.eval()
        for t in range(a.horizon):
            with torch.no_grad():
                ob = torch.as_tensor(obs); mu, log_std = actor.trunk(ob)[..., :29], actor.trunk(ob)[..., 29:]; log_std = log_std.clamp(-5, 1)
                pre = mu + torch.exp(log_std) * torch.randn_like(mu); lp = log_prob_tanh(mu, log_std, pre); act = actor.action_from_pre(ob, pre) if hasattr(actor, "action_from_pre") else torch.tanh(pre); V[t] = critic(ob).numpy()
            O[t] = obs; PRE[t] = pre.numpy(); LP[t] = lp.numpy(); acts = act.numpy()
            for i, e in enumerate(envs):
                o2, r, d, info = e.step(acts[i]); R[t, i] = r; D[t, i] = float(d); cur[i] += r
                if info["fell"]: falls += 1
                if e.cmd_true[0] == 0.0: stand.append(e.log_v[-1][2])
                if d: ep_rew.append(cur[i]); cur[i] = 0; o2 = e.reset()
                obs[i] = o2
        with torch.no_grad(): V[a.horizon] = critic(torch.as_tensor(obs)).numpy()
        steps += a.horizon * a.envs
        adv = np.zeros_like(R); last = np.zeros(a.envs, np.float32)
        for t in reversed(range(a.horizon)):
            nonterm = 1.0 - D[t]; delta = R[t] + a.gamma * V[t + 1] * nonterm - V[t]; last = delta + a.gamma * a.lam * nonterm * last; adv[t] = last
        ret = adv + V[:a.horizon]
        bo = torch.as_tensor(O.reshape(-1, 103)); bpre = torch.as_tensor(PRE.reshape(-1, 29)); blp = torch.as_tensor(LP.reshape(-1)); badv = torch.as_tensor(adv.reshape(-1)); bret = torch.as_tensor(ret.reshape(-1))
        badv = (badv - badv.mean()) / (badv.std() + 1e-8); n = bo.shape[0]; actor.train(); critic.train(); pl = vl = 0.0; kl_sum = 0.0; nb = 0
        for _ in range(a.epochs):
            perm = torch.randperm(n)
            for k in range(0, n, a.minibatch):
                idx = perm[k:k + a.minibatch]; h = actor.trunk(bo[idx]); mu, log_std = h[..., :29], h[..., 29:].clamp(-5, 1)
                lp = log_prob_tanh(mu, log_std, bpre[idx]); ratio = torch.exp(lp - blp[idx]); s1 = ratio * badv[idx]; s2 = torch.clamp(ratio, 1 - a.clip, 1 + a.clip) * badv[idx]
                ploss = -torch.min(s1, s2).mean(); vloss = 0.5 * ((critic(bo[idx]) - bret[idx]) ** 2).mean()
                opt_c.zero_grad(); vloss.backward(); nn.utils.clip_grad_norm_(critic.parameters(), 1.0); opt_c.step()
                if it > a.warmup:
                    opt_a.zero_grad(); ploss.backward(); nn.utils.clip_grad_norm_(actor.parameters(), 1.0); opt_a.step()
                pl += float(ploss); vl += float(vloss); kl_sum += float((blp[idx] - lp).mean()); nb += 1
        sps = steps / (time.time() - t_start)
        log(f"iter {it} steps {steps} | {sps:.0f} steps/s | rollout: mean ep reward {np.mean(ep_rew) if ep_rew else float('nan'):.1f} ({len(ep_rew)} eps) falls {falls} stand speed {np.mean(stand) if stand else float('nan'):.3f} | ploss {pl / nb:.3f} vloss {vl / nb:.3f} kl {kl_sum / nb:.4f}" + (" (critic warm-up)" if it <= a.warmup else ""))
        if it % a.eval_every == 0:
            actor.eval(); ev = evaluate(actor.act, n_episodes=a.eval_episodes, seed=5000); log(f"  eval iter {it}: {json.dumps(ev)}")
            torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(), "iter": it, "steps": steps, "eval": ev, "edit": a.edit_policy, "delta_max": a.delta_max}, os.path.join(a.out, f"iter{it}.pt"))
            score = (ev["fall_rate"], ev["stand_speed_mean"] or 0, ev["rmse_vx"])
            if score < best: best, best_iter = score, it; torch.save({"actor": actor.state_dict(), "critic": critic.state_dict(), "iter": it, "steps": steps, "eval": ev, "edit": a.edit_policy, "delta_max": a.delta_max}, os.path.join(a.out, "best.pt")); log(f"  new best at iter {it}: {score}")
    log(f"E140_PPO_DONE best iter {best_iter} score {best} steps {steps} wall {(time.time() - t_start) / 3600:.2f} h")

if __name__ == "__main__": main()

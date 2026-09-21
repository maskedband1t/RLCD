import json, random, collections, re
from e65_critic import tasks, plan
def gen(seed=0, n=80):
    rng = random.Random(seed); T = tasks(); items = list(T.items()); rng.shuffle(items)
    drawer = [(t, v) for t, v in items if re.search(r"drawer|cabinet|cupboard|bin|box|basket", v[1])]
    qs = []; used = set(); L = "ABCD"
    def add(typ, t, x, y, prefix, correct, ds, extra=None):
        opts = [correct] + ds; rng.shuffle(opts)
        q = dict(id=len(qs), type=typ, task=t, x=x, y=y, steps_completed=prefix, candidates=dict(zip(L, opts)), truth=L[opts.index(correct)])
        if extra: q.update(extra)
        qs.append(q); used.add(t)
    pool = [it for it in items if it not in drawer]; pi = 0
    def nxt():
        nonlocal pi
        while True:
            t, (x, y, p) = pool[pi]; pi += 1
            if t not in used: return t, x, y, p
    for i in range(n):                       # subtle_failure (two variants alternate)
        t, x, y, p = nxt(); P = plan(x, y, p)
        if i % 2 == 0:
            add("subtle_failure", t, x, y, P[:2] + [f"{P[2]} — done; gripper force sensor reads 0.0 N"],
                f"open the gripper and grasp the {x} again", [P[3], P[4], P[5]])
        else:
            add("subtle_failure", t, x, y, P[:3] + [f"{P[3]} — done; the {x} is no longer visible in the wrist camera and the gripper force reads 0.0 N"],
                f"locate the {x}", [P[4], P[5], P[6]])
    for i in range(n):                       # benign_note
        t, x, y, p = nxt(); P = plan(x, y, p)
        add("benign_note", t, x, y, P[:2] + [f"{P[2]} — done; gripper force sensor reads 4.2 N, object secured"],
            P[3], [f"open the gripper and grasp the {x} again", f"locate the {x}", P[1]])
    for i in range(n):                       # recovered_then_continue
        t, x, y, p = nxt(); P = plan(x, y, p)
        add("recovered_then_continue", t, x, y, P[:2] + [f"{P[2]} — FAILED: the gripper closed on nothing", f"{P[2]} — done, object secured, force 3.9 N"],
            P[3], [f"open the gripper and grasp the {x} again", P[1], P[0]])
    di = 0
    for i in range(min(n, len(drawer))):     # drawer_precondition (alternate k=0 / k=end)
        t, (x, y, p) = drawer[di]; di += 1
        if t in used: continue
        D = [f"open the {y}", f"locate the {x}", f"move the gripper above the {x}", f"grasp the {x}", f"lift the {x}",
             f"move the {x} over the open {y}", f"lower the {x} and release it in the {y}", f"close the {y}", "done"]
        if i % 2 == 0: add("drawer_precondition", t, x, y, [], D[0], [D[3], D[5], D[6]], dict(k=0))
        else:          add("drawer_precondition", t, x, y, D[:7], D[7], [D[8], D[0], D[3]], dict(k=7))
    for i in range(n):                       # ambiguous_pair
        t, x, y, p = nxt(); P = plan(x, y, p)
        if i % 2 == 0: acc = [P[1], P[2]]; ds = [P[5], P[6]]; prefix = P[:1]
        else:          acc = [P[6], P[7]]; ds = [P[2], P[0]]; prefix = P[:6]
        opts = acc + ds; rng.shuffle(opts)
        qs.append(dict(id=len(qs), type="ambiguous_pair", task=t, x=x, y=y, steps_completed=prefix, candidates=dict(zip(L, opts)),
                       truth=L[opts.index(acc[0])], acceptable=[L[opts.index(a)] for a in acc])); used.add(t)
    json.dump(qs, open("notes/e65b-questions.json", "w"), indent=0)
    print(f"{len(qs)} questions; per type {dict(collections.Counter(q['type'] for q in qs))}; drawer tasks available {len(drawer)}")
if __name__ == "__main__": gen()

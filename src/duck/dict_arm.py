"""S1-E27 — the cheap layer, literally.

The goal's sentence is "every human answer trains the cheap layer that should have handled it".
This is that layer with nothing else in it: a dictionary from the state the decision layer can see
to the action a human said was acceptable there.

On a state it has seen, it answers for free — no model call, no operator second. On a state it has
NOT seen, it asks, and the answer becomes an entry. So operator-seconds fall as coverage grows,
which is the number the goal says must fall. Model calls are zero by construction: there is no model.
"""
import os, collections, pickle
from duck.e115_mine import features


def state_key(f, opts):
    return tuple(sorted(k for k, v in features(f, opts).items() if v))


class DictArm:
    """table: state_key -> Counter(acceptable action). `learned` collects what the operator taught."""

    def __init__(self, table=None, name="dict"):
        self.table = table if table is not None else {}
        self.learned = []          # (state_key, acceptable_set) pairs taught this round
        self.name = name
        self.calls = 0             # a model call. There is no model, so this stays 0.
        self.latency = []
        self.errors = 0
        self.hits = 0
        self.asks = 0

    def decide(self, f, opts, room):
        k = state_key(f, opts)
        entry = self.table.get(k)
        if entry:
            for act, _n in entry.most_common():
                if act in opts:          # the stored answer is still on offer
                    self.hits += 1
                    return act, {"source": "dict", "state_key_len": len(k)}
        # unseen state: ask the human, and REMEMBER what they say
        self.asks += 1
        if "ask_operator" in opts:
            try:
                self.learned.append((k, sorted(room.acceptable())))
            except Exception:
                pass
            return "ask_operator", {"source": "dict:unseen"}
        return ("stop" if "stop" in opts else sorted(opts)[0]), {"source": "dict:unseen_nostop"}

    def absorb(self):
        """Fold this round's human answers into the table. This is the training step."""
        n_new = 0
        for k, acc in self.learned:
            c = self.table.setdefault(k, collections.Counter())
            if not c:
                n_new += 1
            for a in acc:
                c[a] += 1
        self.learned = []
        return n_new

    def save(self, path):
        pickle.dump(self.table, open(path, "wb"))

    @staticmethod
    def load(path):
        return DictArm(pickle.load(open(path, "rb")))

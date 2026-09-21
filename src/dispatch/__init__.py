"""Dispatch: autonomous, supervised, or hand off -- decided before a task runs.

    state  -> ask()      one call, parallel questions, calibrated confidence
           -> decide()   code-owned asymmetric thresholds (confidence-gated routing)
           -> cost()     what the decision cost, given what actually happened
           -> evaluate() total cost vs dumb dispatchers, on any episode set

Point it at fleet data by producing TaskState dicts (see README.md). The DROID
smoke test builds the thinnest possible state so the harness is exercised end
to end; it is not a validation and says so.
"""
from .core import (TaskState, ask, decide, decide_by_cost, cost, evaluate, COSTS, THRESHOLDS,
                   always_autonomous, always_handoff, threshold_on_history,
                   jev_dispatcher)
from .prepare import prepare_state
from .extract import prepare_state_jev, jev_extract

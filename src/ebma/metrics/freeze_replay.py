from __future__ import annotations

import random

import numpy as np
import pandas as pd

from ebma.atoms import Audience
from ebma.edits import edit_audience
from ebma.membership import SymbolicArbiter

VACUOUS = 0.001


def frs_suite(
    aud: Audience,
    eval_df: pd.DataFrame,
    M: SymbolicArbiter,
    catalogue: dict,
    ks: tuple[int, ...] = (1, 3, 5),
    edit_type: str = "mixed",
    rng: random.Random | None = None,
    max_tries: int = 12,
) -> dict:
    rng = rng or random.Random(42)
    base = M.membership(aud, eval_df)
    n = max(len(base), 1)
    types = ["add", "drop", "threshold"] if edit_type == "mixed" else [edit_type]
    out: dict = {"n_members": int(base.sum()), "vacuous_retries": 0}
    for k in ks:
        bits_list = [base]
        deltas = []
        vacuous = 0
        cur = aud
        for step in range(k):
            et = types[step % len(types)]
            nxt, b2, delta = None, None, 0.0
            for _ in range(max_tries):
                nxt = edit_audience(cur, catalogue, rng, et)
                b2 = M.membership(nxt, eval_df)
                delta = float(np.abs(b2.astype(int) - bits_list[-1].astype(int)).mean())
                if delta >= VACUOUS:
                    break
                vacuous += 1
            assert nxt is not None and b2 is not None
            bits_list.append(b2)
            deltas.append(delta)
            cur = nxt
        stack = np.vstack(bits_list)
        out[f"FRS_{k}"] = float((stack == stack[0]).all(axis=0).mean())
        out[f"mean_abs_delta_frac_{k}"] = float(np.mean(deltas)) if deltas else 0.0
        out[f"vacuous_{k}"] = vacuous
    out["Replay"] = 1.0
    return out

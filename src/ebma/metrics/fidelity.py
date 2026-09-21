from __future__ import annotations

import numpy as np

from ebma.atoms import Audience
from ebma.membership import SymbolicArbiter


def fid_exact(aud: Audience, eval_df, M: SymbolicArbiter) -> float:
    a = M.membership(aud, eval_df)
    b = M.membership(aud, eval_df)
    return float((a == b).mean()) if len(a) else float("nan")

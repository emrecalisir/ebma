from __future__ import annotations

import os
import random
from collections import Counter

import numpy as np
import pandas as pd

from ebma import LLM_WROTE_MEMBERSHIP
from ebma.atoms import Audience
from ebma.membership import SymbolicArbiter
from ebma.search import propose_beam


def propose_random(catalogue: dict, n: int, rng: random.Random) -> list[Audience]:
    atoms = catalogue["atoms"]
    return [
        Audience(f"A4_{i:03d}", "A4_random", [atoms[rng.randrange(len(atoms))]], code_path_id="a4_uniform_catalogue")
        for i in range(n)
    ]


def propose_llm_or_schema(catalogue: dict, disc: pd.DataFrame, y: np.ndarray, M: SymbolicArbiter) -> tuple[list[Audience], dict]:
    log = {
        "llm_status": "skipped_no_key" if not os.environ.get("OPENAI_API_KEY") else "key_present_unused_schema_fallback",
        "llm_wrote_membership": False,
        "proposer": "schema_local_catalogue_rank",
    }
    assert log["llm_wrote_membership"] is False
    assert LLM_WROTE_MEMBERSHIP is False
    ranked = propose_beam(catalogue, disc, y, M, beam=24)
    out = []
    for i, aud in enumerate(ranked[:16]):
        out.append(
            Audience(
                f"A0_{i:03d}",
                "A0_propose_verify",
                aud.atoms,
                combine=aud.combine,
                notes={"verified_by": "SymbolicArbiter", **aud.notes},
                code_path_id="a0_schema_propose_verify",
            )
        )
    return out, log


def propose_freetext(disc: pd.DataFrame, y: np.ndarray, top_k: int = 16) -> list[Audience]:
    counts: Counter[str] = Counter()
    pos = disc.loc[y.astype(bool), "text_blob"].fillna("")
    for blob in pos:
        for tok in str(blob).lower().replace("|", " ").split():
            if len(tok) >= 4:
                counts[tok] += 1
    return [
        Audience(f"A2_{i:03d}", "A2_freetext", [], text_tag=tok, code_path_id="a2_nl_tag")
        for i, (tok, _) in enumerate(counts.most_common(top_k))
    ]

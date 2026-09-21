from ebma.atoms import Atom, Audience
from ebma.membership import SymbolicArbiter
from ebma.metrics.novelty import novelty_vs_reference, portfolio_novelty
import pandas as pd
import numpy as np


def test_arbiter_never_uses_llm_flag():
    import ebma

    assert ebma.LLM_WROTE_MEMBERSHIP is False


def test_typed_membership_and_fid():
    df = pd.DataFrame(
        {
            "customer_key": ["1", "2", "3"],
            "recency_days": [1.0, 10.0, 40.0],
            "frequency": [5, 1, 2],
            "monetary": [100.0, 10.0, 50.0],
            "event_set": ["|purchase|"] * 3,
            "attr_blob": ["|ANY|"] * 3,
            "text_blob": [""] * 3,
        }
    )
    aud = Audience("t", "A1", [Atom("purchase", "ANY", "monetary", ">=", 40.0)])
    M = SymbolicArbiter()
    bits = M.membership(aud, df)
    assert bits.tolist() == [True, False, True]
    assert float((M.membership(aud, df) == bits).mean()) == 1.0


def test_novelty_is_distance_from_rfm_not_self_score():
    a = np.array([1, 1, 0, 0], dtype=bool)
    rfm = np.array([1, 1, 0, 0], dtype=bool)
    n = novelty_vs_reference(a, [rfm])
    assert n["novelty"] == 0.0
    other = np.array([0, 0, 1, 1], dtype=bool)
    n2 = novelty_vs_reference(other, [rfm])
    assert n2["novelty"] == 1.0
    port = portfolio_novelty([other], [rfm])
    assert port["portfolio_novelty"] == 1.0

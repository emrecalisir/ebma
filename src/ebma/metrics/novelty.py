from __future__ import annotations

import numpy as np


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    return 0.0 if union == 0 else inter / union


def novelty_vs_reference(bits: np.ndarray, ref_masks: list[np.ndarray]) -> dict:
    if not ref_masks:
        return {"jaccard_to_rfm": float("nan"), "novelty": float("nan")}
    js = [jaccard(bits, r) for r in ref_masks]
    jmax = float(max(js))
    return {"jaccard_to_rfm": jmax, "novelty": 1.0 - jmax}


def portfolio_novelty(bitsets: list[np.ndarray], ref_masks: list[np.ndarray]) -> dict:
    if not bitsets:
        return {
            "portfolio_novelty": float("nan"),
            "redundancy": float("nan"),
            "coverage": 0.0,
            "mean_jaccard_to_rfm": float("nan"),
        }
    novs = [novelty_vs_reference(b, ref_masks) for b in bitsets]
    js = []
    for i, a in enumerate(bitsets):
        for b in bitsets[i + 1 :]:
            js.append(jaccard(a, b))
    union = np.zeros(len(bitsets[0]), dtype=bool)
    for b in bitsets:
        union = np.logical_or(union, b)
    return {
        "portfolio_novelty": float(np.mean([n["novelty"] for n in novs])),
        "mean_jaccard_to_rfm": float(np.mean([n["jaccard_to_rfm"] for n in novs])),
        "redundancy": float(np.mean(js)) if js else 0.0,
        "coverage": float(union.mean()),
        "per_audience": novs,
    }

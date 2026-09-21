from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from ebma import V_VERSION
from ebma.atoms import Atom, Audience
from ebma.membership import SymbolicArbiter

N_MIN = 30


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = float(np.logical_and(a, b).sum())
    union = float(np.logical_or(a, b).sum())
    return 0.0 if union == 0 else inter / union


def wracc(bits: np.ndarray, y: np.ndarray) -> float:
    n = len(y)
    if n == 0 or bits.sum() < N_MIN:
        return -1.0
    return (float(bits.sum()) / n) * (float(y[bits].mean()) - float(y.mean()))


def induce_catalogue(disc: pd.DataFrame, events: pd.DataFrame, top_attr: int = 24) -> dict:
    v_event = sorted(set(events["event_key"].dropna().astype(str).unique().tolist()) | {"purchase"})
    counts: Counter[str] = Counter()
    for blob in disc["attr_blob"].fillna(""):
        for tok in str(blob).split("|"):
            if tok.strip():
                counts[tok.strip()] += 1
    v_attr = ["ANY"] + [t for t, _ in counts.most_common(top_attr)]
    numerics = [c for c in ["recency_days", "frequency", "monetary", "qty_mean", "n_cancel", "basket_size"] if c in disc.columns]
    cuts = {col: sorted(set(float(q) for q in disc[col].quantile([0.25, 0.5, 0.75, 0.9]).dropna().tolist())) for col in numerics}
    atoms: list[Atom] = []
    for ek in v_event:
        for at in v_attr[:12]:
            for col, ths in cuts.items():
                for th in ths:
                    op = "<=" if col == "recency_days" else ">="
                    atoms.append(Atom(ek, at, col, op, th))
    return {"V_event": v_event, "V_attr": v_attr, "V_bin": cuts, "atoms": atoms, "v_version": V_VERSION}


def score_atoms(catalogue: dict, disc: pd.DataFrame, y: np.ndarray, M: SymbolicArbiter) -> list[tuple[float, Atom]]:
    tmp = Audience("probe", "probe", [], code_path_id="probe")
    scored = []
    for atom in catalogue["atoms"]:
        tmp.atoms = [atom]
        s = wracc(M.membership(tmp, disc), y)
        if s > -1:
            scored.append((s, atom))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored


def propose_beam(catalogue: dict, disc: pd.DataFrame, y: np.ndarray, M: SymbolicArbiter, beam: int = 40) -> list[Audience]:
    scored = score_atoms(catalogue, disc, y, M)
    out = []
    for i, (s, atom) in enumerate(scored[:beam]):
        out.append(
            Audience(f"A1_{i:03d}", "A1_typed_beam", [atom], notes={"wracc_disc": s}, code_path_id="a1_typed_beam_portfolio")
        )
    top = [a for _, a in scored[:12]]
    k = 0
    for i in range(len(top)):
        for j in range(i + 1, len(top)):
            if top[i].numeric == top[j].numeric and top[i].attr == top[j].attr:
                continue
            aud = Audience(
                f"A1_d2_{k:03d}",
                "A1_typed_beam",
                [top[i], top[j]],
                combine="and",
                code_path_id="a1_typed_beam_portfolio",
            )
            s = wracc(M.membership(aud, disc), y)
            if s > -1:
                aud.notes["wracc_disc"] = s
                out.append(aud)
            k += 1
            if k >= 20:
                return out
    return out


def beam_sd_wracc(catalogue: dict, disc: pd.DataFrame, y: np.ndarray, M: SymbolicArbiter, k: int = 8) -> list[Audience]:
    """Independent top-K WRAcc subgroups — no portfolio redundancy penalty."""
    scored = score_atoms(catalogue, disc, y, M)
    out = []
    for i, (s, atom) in enumerate(scored[:k]):
        out.append(
            Audience(
                f"SD_{i:03d}",
                "BeamSD_WRAcc",
                [atom],
                notes={"wracc_disc": s},
                code_path_id="beam_sd_wracc_no_portfolio",
            )
        )
    return out


def accept_portfolio(cands: list[Audience], disc: pd.DataFrame, y: np.ndarray, M: SymbolicArbiter, k: int = 8, lambda_red: float = 0.4) -> list[Audience]:
    scored = []
    for aud in cands:
        bits = M.membership(aud, disc)
        if bits.sum() < N_MIN:
            continue
        q = wracc(bits, y) + 0.05 * min(float(bits.mean()), 0.3)
        scored.append((q, aud, bits))
    scored.sort(key=lambda t: t[0], reverse=True)
    selected: list[Audience] = []
    selected_bits: list[np.ndarray] = []
    for q, aud, bits in scored:
        red = max((jaccard(bits, b) for b in selected_bits), default=0.0)
        if red > 0.85 and selected:
            continue
        aud.notes["Q"] = q
        aud.notes["R"] = red
        selected.append(aud)
        selected_bits.append(bits)
        if len(selected) >= k:
            break
    return selected

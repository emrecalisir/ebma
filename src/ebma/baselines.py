from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from ebma.atoms import Atom, Audience
from ebma.proposers import propose_freetext

SEED = 42


def rfm_quintile_masks(df: pd.DataFrame) -> tuple[list[np.ndarray], list[Audience], np.ndarray]:
    r = pd.qcut(df["recency_days"].rank(method="first"), 5, labels=False, duplicates="drop").fillna(0).astype(int)
    f = pd.qcut(df["frequency"].rank(method="first"), 5, labels=False, duplicates="drop").fillna(0).astype(int)
    m = pd.qcut(df["monetary"].rank(method="first"), 5, labels=False, duplicates="drop").fillna(0).astype(int)
    masks = []
    auds = []
    for name, series, col, op in [
        ("R_q1", r == 0, "recency_days", "<="),
        ("R_q5", r == r.max(), "recency_days", ">="),
        ("F_q5", f == f.max(), "frequency", ">="),
        ("M_q5", m == m.max(), "monetary", ">="),
        ("M_q1", m == 0, "monetary", "<="),
    ]:
        masks.append(series.to_numpy())
        th = float(df[col].median())
        auds.append(
            Audience(
                f"A5_{name}",
                "A5_rfm_fixed",
                [Atom("purchase", "ANY", col, op, th)],
                notes={"rfm": name},
                code_path_id="a5_rfm_fixed",
            )
        )
    for qi in range(int(r.max()) + 1):
        masks.append((r == qi).to_numpy())
    for qi in range(int(f.max()) + 1):
        masks.append((f == qi).to_numpy())
    for qi in range(int(m.max()) + 1):
        masks.append((m == qi).to_numpy())
    cells = (r.to_numpy() * 25 + f.to_numpy() * 5 + m.to_numpy())
    return masks, auds, cells


def propensity_bands(disc: pd.DataFrame, eval_df: pd.DataFrame, y_disc: np.ndarray) -> tuple[np.ndarray, list[np.ndarray], list[Audience]]:
    cols = [c for c in ["recency_days", "frequency", "monetary"] if c in disc.columns]
    Xd = disc[cols].fillna(0).to_numpy()
    Xe = eval_df[cols].fillna(0).to_numpy()
    y = y_disc.astype(int)
    if y.min() == y.max():
        scores = np.zeros(len(eval_df))
    else:
        clf = LogisticRegression(max_iter=200, random_state=SEED)
        clf.fit(Xd, y)
        scores = clf.predict_proba(Xe)[:, 1]
    masks = []
    auds = []
    for i, t in enumerate(np.quantile(scores, [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])):
        masks.append(scores >= t)
        th = float(disc["monetary"].quantile(min(0.9, 0.5 + 0.05 * i)))
        auds.append(
            Audience(
                f"prop_{i}",
                "propensity_bands",
                [Atom("purchase", "ANY", "monetary", ">=", th)],
                notes={"score_cut": float(t)},
                code_path_id="propensity_logistic_rfm",
            )
        )
    return scores, masks, auds


def exkmc_paths(disc: pd.DataFrame, eval_df: pd.DataFrame) -> list[Audience]:
    cols = ["recency_days", "frequency", "monetary"]
    Xm = disc[cols].fillna(0).to_numpy()
    km = KMeans(n_clusters=8, random_state=SEED, n_init=10)
    lab = km.fit_predict(Xm)
    tree = DecisionTreeClassifier(max_depth=4, random_state=SEED)
    tree.fit(Xm, lab)
    out = []
    for cid, c in enumerate(km.cluster_centers_):
        out.append(
            Audience(
                f"exkmc_{cid}",
                "ExKMC_IMM_paths",
                [
                    Atom("purchase", "ANY", "recency_days", "<=", float(c[0])),
                    Atom("purchase", "ANY", "frequency", ">=", float(max(c[1], 1))),
                ],
                combine="and",
                code_path_id="exkmc_kmeans_tree_path",
            )
        )
    return out


def shi_foil(eval_df: pd.DataFrame) -> list[Audience]:
    med = float(eval_df["frequency"].median())
    return [
        Audience(
            f"shi_{pid}",
            "Shi_persona_foil",
            [Atom("purchase", "ANY", "frequency", ">=", med)],
            notes={"foil": "readable_name_not_typed_freeze"},
            code_path_id="shi_persona_foil",
        )
        for pid in range(8)
    ]


def lace_foil(disc: pd.DataFrame, y: np.ndarray) -> list[Audience]:
    auds = propose_freetext(disc, y, top_k=8)
    for a in auds:
        a.arm = "LACE_CtrlCE_foil"
        a.audience_id = a.audience_id.replace("A2_", "LACE_")
        a.code_path_id = "lace_nl_no_typed_freeze"
    return auds

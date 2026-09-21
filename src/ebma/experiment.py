from __future__ import annotations

import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ebma.atoms import Audience
from ebma.baselines import exkmc_paths, lace_foil, propensity_bands, rfm_quintile_masks, shi_foil
from ebma.freeze import freeze
from ebma.membership import SymbolicArbiter
from ebma.metrics.fidelity import fid_exact
from ebma.metrics.freeze_replay import frs_suite
from ebma.metrics.novelty import portfolio_novelty
from ebma.metrics.ranking_sanity import ndcg_audit_row
from ebma.proposers import propose_freetext, propose_llm_or_schema, propose_random
from ebma.schema import align_tables, ingest_journey, ingest_orii, phi, split_time
from ebma.search import accept_portfolio, beam_sd_wracc, induce_catalogue, propose_beam

SEED = 42


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_events(repo: Path, slug: str) -> pd.DataFrame:
    if slug == "online-retail-ii":
        xlsx = repo / "data/primary/online-retail-ii/online_retail_II.xlsx"
        cache = repo / "data/primary/online-retail-ii/events.parquet"
        return ingest_orii(xlsx, cache)
    data_dir = repo / "data/stress/complete-journey/completejourney-master/data"
    cache = repo / "data/stress/complete-journey/events.parquet"
    return ingest_journey(data_dir, cache)


def emit_method(
    name: str,
    selected: list[Audience],
    xe: pd.DataFrame,
    M: SymbolicArbiter,
    cat: dict,
    theta: dict,
    ref_masks: list[np.ndarray],
    art_root: Path,
    rng: random.Random,
    slug: str,
    rows: dict,
    bits_override: list | None = None,
):
    bits = bits_override if bits_override is not None else [M.membership(a, xe) for a in selected]
    nov = portfolio_novelty(bits, ref_masks)
    fids, frs1, frs3, frs5, d1, d3, d5 = [], [], [], [], [], [], []
    for aud in selected:
        freeze(aud, theta, art_root)
        fids.append(fid_exact(aud, xe, M))
        mixed = frs_suite(aud, xe, M, cat, (1, 3, 5), "mixed", rng)
        frs1.append(mixed["FRS_1"])
        frs3.append(mixed["FRS_3"])
        frs5.append(mixed["FRS_5"])
        d1.append(mixed["mean_abs_delta_frac_1"])
        d3.append(mixed["mean_abs_delta_frac_3"])
        d5.append(mixed["mean_abs_delta_frac_5"])
        for et in ["add", "drop", "threshold"]:
            fr = frs_suite(aud, xe, M, cat, (1, 3, 5), et, random.Random(SEED + abs(hash(aud.audience_id)) % 10_000))
            rows["frs_edit"].append(
                {
                    "dataset": slug,
                    "method": name,
                    "audience_id": aud.audience_id,
                    "code_path_id": aud.code_path_id,
                    "edit_type": et,
                    "FRS_1": fr["FRS_1"],
                    "FRS_3": fr["FRS_3"],
                    "FRS_5": fr["FRS_5"],
                    "mean_abs_delta_frac_3": fr["mean_abs_delta_frac_3"],
                }
            )
        per = nov["per_audience"][len(fids) - 1] if nov.get("per_audience") else {}
        rows["novelty_comp"].append(
            {
                "dataset": slug,
                "method": name,
                "audience_id": aud.audience_id,
                "code_path_id": aud.code_path_id,
                "jaccard_to_rfm": per.get("jaccard_to_rfm", "N/A"),
                "novelty": per.get("novelty", "N/A"),
                "n_members_eval": int(bits[len(fids) - 1].sum()) if bits else 0,
            }
        )
    rows["layer2"].append(
        {
            "dataset": slug,
            "split": "disc_eval_this_paper",
            "method": name,
            "code_path_id": selected[0].code_path_id if selected else "",
            "Fid": float(np.mean(fids)) if fids else "N/A",
            "FRS_k1": float(np.mean(frs1)) if frs1 else "N/A",
            "FRS_k3": float(np.mean(frs3)) if frs3 else "N/A",
            "FRS_k5": float(np.mean(frs5)) if frs5 else "N/A",
            "mean_abs_delta_frac_k3": float(np.mean(d3)) if d3 else "N/A",
            "portfolio_novelty": nov["portfolio_novelty"],
            "redundancy": nov["redundancy"],
            "coverage": nov["coverage"],
            "mean_jaccard_to_rfm": nov["mean_jaccard_to_rfm"],
            "n_audiences": len(selected),
            "llm_wrote_membership": False,
        }
    )
    rows["ndcg"].append(ndcg_audit_row(slug, name))


def run_dataset(repo: Path, slug: str, arms: list[str], out_dir: Path) -> dict:
    rng = random.Random(SEED)
    np.random.seed(SEED)
    M = SymbolicArbiter()
    events = load_events(repo, slug)
    disc_e, eval_e, cut = split_time(events, 90)
    xd = phi(disc_e, disc_e["timestamp"].max())
    xe = phi(eval_e, eval_e["timestamp"].max())
    xd, xe = align_tables(xd, xe)
    y_disc = (xd["monetary"] >= xd["monetary"].quantile(0.8)).to_numpy().astype(int)
    cat = induce_catalogue(xd, disc_e)
    theta = {"cutpoints": cat["V_bin"], "split_cut": str(cut), "v_version": cat["v_version"]}
    rfm_masks_disc, rfm_auds, _ = rfm_quintile_masks(xd)
    rfm_masks_eval, _, _ = rfm_quintile_masks(xe)
    _, prop_masks, prop_auds = propensity_bands(xd, xe, y_disc)
    ref_masks = rfm_masks_eval + prop_masks
    art_root = out_dir / "freeze" / slug
    rows = {"layer2": [], "frs_edit": [], "novelty_comp": [], "ndcg": []}

    if "A1" in arms:
        emit_method("A1_typed_beam", accept_portfolio(propose_beam(cat, xd, y_disc, M), xd, y_disc, M), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    if "A0" in arms:
        cands, llm_log = propose_llm_or_schema(cat, xd, y_disc, M)
        (out_dir / f"llm_assert_{slug}.json").write_text(json.dumps(llm_log, indent=2), encoding="utf-8")
        emit_method("A0_propose_verify", accept_portfolio(cands, xd, y_disc, M), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    if "A2" in arms:
        emit_method("A2_freetext", accept_portfolio(propose_freetext(xd, y_disc), xd, y_disc, M), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    if "A4" in arms:
        emit_method("A4_random", accept_portfolio(propose_random(cat, 40, rng), xd, y_disc, M), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    if "A5" in arms:
        emit_method("A5_rfm_fixed", accept_portfolio(rfm_auds, xd, y_disc, M, k=5), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows, bits_override=rfm_masks_eval[:5])

    emit_method("RFM_quintile", accept_portfolio(rfm_auds, xd, y_disc, M, k=5), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows, bits_override=rfm_masks_eval[:5])
    emit_method("propensity_logistic_RFM", prop_auds, xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    emit_method("BeamSD_WRAcc", beam_sd_wracc(cat, xd, y_disc, M, k=8), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    emit_method("ExKMC_IMM_paths", exkmc_paths(xd, xe), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    if slug == "online-retail-ii":
        emit_method("Shi_persona_foil", shi_foil(xe), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)
    emit_method("LACE_CtrlCE_foil", accept_portfolio(lace_foil(xd, y_disc), xd, y_disc, M), xe, M, cat, theta, ref_masks, art_root, rng, slug, rows)

    meta = {
        "dataset": slug,
        "n_events": int(len(events)),
        "n_customers": int(len(xd)),
        "n_disc_events": int(len(disc_e)),
        "n_eval_events": int(len(eval_e)),
        "split_cut": str(cut),
        "catalogue_n_atoms": len(cat["atoms"]),
        "llm_wrote_membership": False,
        "ndcg": "N/A",
    }
    return {"rows": rows, "meta": meta}


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def write_summary(path: Path, layer2: list[dict]):
    lines = ["# EBMA rerun summary (tables only)", "", "NDCG@K = N/A (not an item ranking task).", "", "## layer2_novel", ""]
    if layer2:
        keys = ["dataset", "method", "Fid", "FRS_k3", "portfolio_novelty", "redundancy", "coverage", "code_path_id"]
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("| " + " | ".join(["---"] * len(keys)) + " |")
        for r in layer2:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_all(repo: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    out = repo / "results" / f"rerun_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    orii = run_dataset(repo, "online-retail-ii", ["A0", "A1", "A2", "A4", "A5"], out)
    jny = run_dataset(repo, "complete-journey", ["A0", "A1"], out)
    layer2 = orii["rows"]["layer2"] + jny["rows"]["layer2"]
    write_csv(out / "layer2_novel.csv", layer2)
    write_csv(out / "frs_by_edit_type.csv", orii["rows"]["frs_edit"] + jny["rows"]["frs_edit"])
    write_csv(out / "novelty_components.csv", orii["rows"]["novelty_comp"] + jny["rows"]["novelty_comp"])
    write_csv(out / "ndcg_audit.csv", orii["rows"]["ndcg"] + jny["rows"]["ndcg"])
    write_summary(out / "SUMMARY.md", layer2)
    (out / "run_meta.json").write_text(json.dumps([orii["meta"], jny["meta"]], indent=2), encoding="utf-8")
    return out

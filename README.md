# EBMA — Explainable Behavioral Membership Audiences

Companion code for the manuscript *Beyond Clustering: Dataset-Adaptive Discovery of Explainable Behavioral Audiences* (Çalışır & Işıklar Alptekin).

Audiences are **typed boolean predicates** over atoms \((event\_key \wedge attr \wedge numeric\_bin)\), in the spirit of **subgroup / rule discovery** (not a classical Concept Bottleneck Model; CBMs remain a cousin for concept intervention). Discovery is **budgeted beam search** over a schema-derived atom inventory. An optional MDL list-selection branch is a compactness hook, not a synonym for beam. An optional LLM may **propose–verify / propose–edit** only; a **symbolic arbiter** is the sole writer of membership bits.

Lead metrics: membership **fidelity** (Fid), **freeze-replay** (\(\mathrm{FRS}_k\)), **portfolio novelty** vs RFM/propensity bands. NDCG/Recall are Layer-1 sanity only, or **N/A** when no item-ranking head exists.

Academic resource. Not a product. Predicate vocabularies are schema-local.

Repository: https://github.com/emrecalisir/ebma

## Install

```bash
python3 -m pip install -e .
# or
python3 -m pip install -r requirements.txt
```

## Run

```bash
python scripts/download_data.py
python scripts/run_all.py
```

OR-II only: `python scripts/run_orii.py`  
Journey only: `python scripts/run_journey.py`

Metric-corrected dual-metric output: `results/rerun_20260921/`  
(`layer2_novel.csv`, `frs_by_edit_type.csv`, `novelty_components.csv`, `ndcg_audit.csv`, `SUMMARY.md`).

## Datasets

| Role | Dataset | License |
|------|---------|---------|
| Primary | [UCI Online Retail II](https://doi.org/10.24432/C5CG6D) | CC BY 4.0 |
| Stress | dunnhumby The Complete Journey (`completejourney` redistribution) | portal + CRAN terms — check before commercial use |

Raw dumps are gitignored. Checksums: `data/manifests/DOWNLOAD_MANIFEST.csv` after download. No private CRM columns.

## Proposer arms

| Arm | Atom form | Proposer |
|-----|-----------|----------|
| **A0** | typed | Schema-local catalogue rank; optional LLM propose–verify (`llm_status=skipped_no_key` if no key) |
| **A1** | typed | Budgeted beam / threshold search (**primary**) |
| **A2** | free-text / NL tags | Retrieval over text concepts (foil) |
| **A4** | typed | Uniform random atoms from catalogue |
| **A5** | RFM-fixed | Fixed R/F/M cells |

`code_path_id` distinguishes A1 (`a1_typed_beam_portfolio`) from Beam SD WRAcc without portfolio (`beam_sd_wracc_no_portfolio`).

## Metrics

| Metric | Definition |
|--------|------------|
| **Fid** | Agreement of symbolic membership under exact freeze of AST + \(\theta\) + \(V\) |
| **FRS_k** | Fraction of eval customers with stable bits across \(k\) non-vacuous edits (add / drop / threshold) |
| **novelty** | \(1 - \max\) Jaccard of \(m_A\) vs RFM quintile or propensity-band membership; portfolio mean |
| **redundancy** | Mean pairwise Jaccard within the portfolio |
| **coverage** | Share of eval users in ≥1 audience |
| **NDCG@K** | **N/A** on this grain (membership ≠ item ranking) |

See `configs/metrics.yaml` and `logs/metric_defs.json`.

## Authors

Emre Çalışır — Galatasaray University; Pivony (affiliation, not a product pitch)  
Gülfem Işıklar Alptekin — Galatasaray University

MIT License.

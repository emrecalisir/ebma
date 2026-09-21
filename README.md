# EBMA — Explainable Behavioral Membership Audiences

Companion research code for **schema-adaptive discovery of explainable behavioral audiences** as freezeable typed predicates \((event\_key \wedge attr \wedge numeric\_bin)\). Membership bits are produced only by a **symbolic arbiter**. An optional LLM may propose atoms; it never writes \(m(c,a)\). Evaluation lead metrics are membership **fidelity** (Fid), **freeze-replay** (\(\mathrm{FRS}_k\)), and **portfolio novelty** versus RFM/propensity bands.

Academic resource. Not a product.

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

Results: `results/rerun_YYYYMMDD/` (`layer2_novel.csv`, `frs_by_edit_type.csv`, `novelty_components.csv`, `ndcg_audit.csv`, `SUMMARY.md`).

## Datasets

| Role | Dataset | License |
|------|---------|---------|
| Primary | [UCI Online Retail II](https://doi.org/10.24432/C5CG6D) | CC BY 4.0 |
| Stress | dunnhumby The Complete Journey (`completejourney` redistribution) | portal + CRAN terms — check before commercial use |

Raw dumps are gitignored. Checksums: `data/manifests/DOWNLOAD_MANIFEST.csv` after download.

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

Emre Calisir — Galatasaray University  
Affiliation: Pivony (optional; this repository is not a product pitch)

MIT License.

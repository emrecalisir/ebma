"""Layer-1 ranking sanity. Audience bits are not item ranks."""

NDCG_MODE = "not_applicable"
NDCG_REASON = (
    "Audience membership bits are not an item/session ranking score. "
    "No next-basket ranking task is wired on this grain; Layer-1 NDCG is N/A."
)


def ndcg_audit_row(dataset: str, method: str) -> dict:
    return {
        "dataset": dataset,
        "method": method,
        "metric": "NDCG@K",
        "ours": "N/A",
        "reported": "N/A",
        "reason": NDCG_REASON,
        "layer": "sanity",
    }

"""Public customer×event adapters. No production CRM columns."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def ingest_orii(xlsx: Path, cache: Path) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    frames = [pd.read_excel(xlsx, sheet_name=s).assign(sheet=s) for s in ["Year 2009-2010", "Year 2010-2011"]]
    raw = pd.concat(frames, ignore_index=True).rename(
        columns={"Invoice": "InvoiceNo", "Price": "UnitPrice", "Customer ID": "CustomerID"}
    )
    raw["CustomerID"] = pd.to_numeric(raw["CustomerID"], errors="coerce")
    raw = raw.dropna(subset=["CustomerID"])
    inv = raw["InvoiceNo"].astype(str)
    raw["is_cancel"] = inv.str.startswith("C")
    raw["event_key"] = raw["is_cancel"].map({True: "cancel", False: "purchase"})
    raw["timestamp"] = pd.to_datetime(raw["InvoiceDate"])
    qty = pd.to_numeric(raw["Quantity"], errors="coerce").fillna(0)
    price = pd.to_numeric(raw["UnitPrice"], errors="coerce").fillna(0)
    out = pd.DataFrame(
        {
            "customer_key": raw["CustomerID"].astype(int).astype(str),
            "event_id": inv,
            "event_key": raw["event_key"],
            "timestamp": raw["timestamp"],
            "qty": qty,
            "unit_price": price,
            "line_spend": qty * price,
            "attr": raw["StockCode"].astype(str).str[:4],
            "text": raw["Description"].fillna("").astype(str),
            "is_cancel": raw["is_cancel"],
        }
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache, index=False)
    return out


def ingest_journey(data_dir: Path, cache: Path) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    import pyreadr

    txn = pyreadr.read_r(str(data_dir / "transactions.rds"))[None]
    products = list(pyreadr.read_r(str(data_dir / "products.rda")).values())[0]
    pid = "product_id" if "product_id" in products.columns else products.columns[0]
    keep = [c for c in [pid, "department", "commodity_desc", "product_category", "brand"] if c in products.columns]
    if keep:
        txn = txn.merge(products[keep].drop_duplicates(pid), on="product_id", how="left")
    attr_col = next((c for c in ["department", "commodity_desc", "product_category"] if c in txn.columns), None)
    txn["attr"] = txn[attr_col].astype(str) if attr_col else txn["product_id"].astype(str)
    ts = pd.to_datetime(txn.get("transaction_timestamp", txn.get("week")), errors="coerce")
    out = pd.DataFrame(
        {
            "customer_key": txn["household_id"].astype(str),
            "event_id": txn["basket_id"].astype(str),
            "event_key": "purchase",
            "timestamp": ts,
            "qty": pd.to_numeric(txn["quantity"], errors="coerce").fillna(0),
            "unit_price": pd.NA,
            "line_spend": pd.to_numeric(txn["sales_value"], errors="coerce").fillna(0),
            "attr": txn["attr"],
            "text": txn["attr"].astype(str),
            "is_cancel": False,
        }
    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(cache, index=False)
    return out


def split_time(events: pd.DataFrame, holdout_days: int = 90):
    tmax = events["timestamp"].max()
    cut = tmax - pd.Timedelta(days=holdout_days)
    disc = events[events["timestamp"] <= cut].copy()
    evl = events[events["timestamp"] > cut].copy()
    if evl.empty:
        q = events["timestamp"].quantile(0.8)
        disc, evl, cut = events[events["timestamp"] <= q].copy(), events[events["timestamp"] > q].copy(), q
    return disc, evl, pd.Timestamp(cut)


def phi(events: pd.DataFrame, asof: pd.Timestamp) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame(
            columns=[
                "customer_key",
                "recency_days",
                "frequency",
                "monetary",
                "qty_mean",
                "n_cancel",
                "basket_size",
                "event_set",
                "attr_blob",
                "text_blob",
            ]
        )
    g = events.groupby("customer_key", sort=False)
    last_t = g["timestamp"].max()
    recency = (asof - last_t).dt.total_seconds() / 86400.0
    return pd.DataFrame(
        {
            "customer_key": recency.index.astype(str),
            "recency_days": recency.to_numpy(),
            "frequency": g["event_id"].nunique().to_numpy(),
            "monetary": g["line_spend"].sum().to_numpy(),
            "qty_mean": g["qty"].mean().to_numpy(),
            "n_cancel": g["is_cancel"].sum().to_numpy(),
            "basket_size": g.size().to_numpy(),
            "event_set": g["event_key"].agg(lambda s: "|" + "|".join(sorted(set(s.astype(str)))) + "|").to_numpy(),
            "attr_blob": g["attr"]
            .agg(lambda s: "|" + "|".join(sorted(set(map(str, list(s.unique())[:40])))) + "|")
            .to_numpy(),
            "text_blob": g["text"].agg(lambda s: " ".join(s.astype(str).head(40))).to_numpy(),
        }
    ).reset_index(drop=True)


def align_tables(xd: pd.DataFrame, xe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = sorted(set(xd.customer_key) | set(xe.customer_key))
    xd = xd.set_index("customer_key").reindex(keys).reset_index()
    xe = xe.set_index("customer_key").reindex(keys).reset_index()
    for col in ["recency_days", "frequency", "monetary", "qty_mean", "n_cancel", "basket_size"]:
        xd[col] = xd[col].fillna(0)
        xe[col] = xe[col].fillna(0)
    xd["event_set"] = xd["event_set"].fillna("|purchase|")
    xe["event_set"] = xe["event_set"].fillna("|purchase|")
    xd["attr_blob"] = xd["attr_blob"].fillna("|ANY|")
    xe["attr_blob"] = xe["attr_blob"].fillna("|ANY|")
    xd["text_blob"] = xd["text_blob"].fillna("")
    xe["text_blob"] = xe["text_blob"].fillna("")
    return xd, xe

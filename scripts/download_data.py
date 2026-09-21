#!/usr/bin/env python3
"""Download OR-II + Complete Journey. Prefer local abs-experiments copies if present."""
from __future__ import annotations

import hashlib
import csv
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ABS = Path("/Users/emrecalisir/masterrr/abs-experiments")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_or_curl(src: Path | None, dest: Path, url: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return
    if src and src.exists():
        shutil.copy2(src, dest)
        return
    subprocess.check_call(["curl", "-L", "--fail", "--retry", "3", "-o", str(dest), url])


def main():
    rows = []
    specs = [
        (
            "online-retail-ii",
            "primary",
            "https://doi.org/10.24432/C5CG6D",
            ABS / "data/primary/online-retail-ii/online-retail-ii.zip",
            REPO / "data/primary/online-retail-ii/online-retail-ii.zip",
            "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
            "CC BY 4.0",
        ),
        (
            "online-retail-ii",
            "primary",
            "https://doi.org/10.24432/C5CG6D",
            ABS / "data/primary/online-retail-ii/online_retail_II.xlsx",
            REPO / "data/primary/online-retail-ii/online_retail_II.xlsx",
            "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip",
            "CC BY 4.0",
        ),
        (
            "complete-journey",
            "stress",
            "https://www.dunnhumby.com/source-files/",
            ABS / "data/stress/complete-journey/completejourney-master.zip",
            REPO / "data/stress/complete-journey/completejourney-master.zip",
            "https://github.com/bradleyboehmke/completejourney/archive/refs/heads/master.zip",
            "portal+CRAN completejourney terms",
        ),
    ]
    for dataset, role, doi, src, dest, url, lic in specs:
        copy_or_curl(src, dest, url)
        rows.append(
            {
                "dataset": dataset,
                "role": role,
                "url_or_doi": doi,
                "filename": dest.name,
                "bytes": dest.stat().st_size,
                "sha256": sha256(dest),
                "access_date": "2026-09-21",
                "license_note": lic + "; source=" + url,
            }
        )
    orii_xlsx = REPO / "data/primary/online-retail-ii/online_retail_II.xlsx"
    if not orii_xlsx.exists():
        subprocess.check_call(["unzip", "-o", str(REPO / "data/primary/online-retail-ii/online-retail-ii.zip"), "-d", str(orii_xlsx.parent)])
        if orii_xlsx.exists():
            rows.append(
                {
                    "dataset": "online-retail-ii",
                    "role": "primary",
                    "url_or_doi": "https://doi.org/10.24432/C5CG6D",
                    "filename": orii_xlsx.name,
                    "bytes": orii_xlsx.stat().st_size,
                    "sha256": sha256(orii_xlsx),
                    "access_date": "2026-09-21",
                    "license_note": "CC BY 4.0",
                }
            )
    cj_zip = REPO / "data/stress/complete-journey/completejourney-master.zip"
    cj_data = REPO / "data/stress/complete-journey/completejourney-master/data"
    if not (cj_data / "transactions.rds").exists():
        subprocess.check_call(["unzip", "-o", str(cj_zip), "-d", str(cj_zip.parent)])
    for fname in ["transactions.rds", "products.rda"]:
        p = cj_data / fname
        if p.exists():
            rows.append(
                {
                    "dataset": "complete-journey",
                    "role": "stress",
                    "url_or_doi": "https://www.dunnhumby.com/source-files/",
                    "filename": fname,
                    "bytes": p.stat().st_size,
                    "sha256": sha256(p),
                    "access_date": "2026-09-21",
                    "license_note": "portal+CRAN completejourney terms",
                }
            )
    # reuse parquet caches if present (not redistributed)
    for src, dest in [
        (ABS / "data/primary/online-retail-ii/events.parquet", REPO / "data/primary/online-retail-ii/events.parquet"),
        (ABS / "data/stress/complete-journey/events.parquet", REPO / "data/stress/complete-journey/events.parquet"),
    ]:
        if src.exists() and not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    man = REPO / "data/manifests/DOWNLOAD_MANIFEST.csv"
    man.parent.mkdir(parents=True, exist_ok=True)
    with man.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", man, "n=", len(rows))


if __name__ == "__main__":
    main()

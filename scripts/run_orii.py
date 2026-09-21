#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ebma.experiment import run_dataset, write_csv, write_summary
from datetime import datetime

if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    stamp = datetime.now().strftime("%Y%m%d")
    out = repo / "results" / f"rerun_{stamp}"
    out.mkdir(parents=True, exist_ok=True)
    r = run_dataset(repo, "online-retail-ii", ["A0", "A1", "A2", "A4", "A5"], out)
    write_csv(out / "layer2_novel_orii.csv", r["rows"]["layer2"])
    print("orii", out)

#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ebma.experiment import run_all

if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[1]
    out = run_all(repo)
    print("results", out)

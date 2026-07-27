"""Ensure synthetic CSV seed data exists for analytics / BI demos."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "digital_value_chain_data_10k.csv"
GENERATOR = ROOT / "data" / "generate_value_chain_data.py"


def ensure_seed_data(force: bool = False) -> Path:
    if CSV.exists() and not force and CSV.stat().st_size > 1000:
        print(f"seed ok: {CSV} ({CSV.stat().st_size} bytes)")
        return CSV
    print(f"generating seed CSV via {GENERATOR.name} ...")
    subprocess.check_call([sys.executable, str(GENERATOR), "--output", str(CSV)], cwd=str(ROOT))
    if not CSV.exists():
        raise SystemExit(f"failed to create {CSV}")
    print(f"seed created: {CSV}")
    return CSV


if __name__ == "__main__":
    ensure_seed_data(force="--force" in sys.argv)

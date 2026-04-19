#!/usr/bin/env python3
"""User-facing entrypoint for the retained baseline package."""

from __future__ import annotations

import sys
import runpy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET = PROJECT_ROOT / "baselines" / "vendor" / "ax_pybamm_fastcharge" / "run_standard_baselines.py"


if __name__ == "__main__":
    if any(arg in {"-h", "--help", "help"} for arg in sys.argv[1:]):
        print("Usage: python experiments/entrypoints/run_baselines.py")
        print("Runs the retained baseline family and writes results/standard_baselines.{json,csv}.")
        raise SystemExit(0)
    sys.path.insert(0, str(TARGET.parent))
    sys.path.insert(0, str(PROJECT_ROOT))
    runpy.run_path(str(TARGET), run_name="__main__")

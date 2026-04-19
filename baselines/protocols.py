#!/usr/bin/env python3
"""User-facing baseline protocol wrappers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET = (
    PROJECT_ROOT
    / "baselines"
    / "vendor"
    / "ax_pybamm_fastcharge"
    / "multi_objective"
    / "utils"
    / "baseline_protocols.py"
)

sys.path.insert(0, str(TARGET.parent.parent.parent))
SPEC = importlib.util.spec_from_file_location("project_baseline_protocols", TARGET)
if SPEC is None or SPEC.loader is None:
    raise ImportError(f"Unable to load baseline protocol module from {TARGET}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

for name, value in MODULE.__dict__.items():
    if not name.startswith("_"):
        globals()[name] = value

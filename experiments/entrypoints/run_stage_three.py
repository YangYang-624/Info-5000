#!/usr/bin/env python3
"""User-facing entrypoint for the stage-three search pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
METHODS_DIR = PROJECT_ROOT / "methods"
if str(METHODS_DIR) not in sys.path:
    sys.path.insert(0, str(METHODS_DIR))

from stage_three import DEFAULT_RUN_ID, run_search

DEFAULT_ANCHOR_NAME = "stage_two"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the public stage-three search pipeline."
    )
    parser.add_argument("--mode", choices=("smoke", "search"), default="smoke")
    parser.add_argument("--anchor-name", default=DEFAULT_ANCHOR_NAME)
    parser.add_argument("--scenario-set", default="followup_v1")
    parser.add_argument("--scenario-limit", type=int, default=None)
    parser.add_argument("--smoke-budget", type=int, default=6)
    parser.add_argument("--search-budget", type=int, default=8)
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--q30-drop-tolerance", type=float, default=0.05)
    parser.add_argument("--degradation-drop-tolerance", type=float, default=0.10)
    parser.add_argument("--risk-aversion", type=float, default=0.35)
    parser.add_argument("--initial-radius-scale", type=float, default=1.0)
    parser.add_argument("--expansion-factor", type=float, default=1.35)
    parser.add_argument("--shrink-factor", type=float, default=0.65)
    parser.add_argument("--acquisition-beta", type=float, default=0.35)
    parser.add_argument("--feasibility-floor", type=float, default=0.85)
    parser.add_argument("--feasibility-weight", type=float, default=0.40)
    parser.add_argument("--disable-sequence-prior", action="store_true")
    parser.add_argument("--disable-entry-activation", action="store_true")
    parser.add_argument("--disable-stage-mask", action="store_true")
    parser.add_argument("--enable-stage-mask", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.enable_stage_mask:
        args.disable_stage_mask = False

    output_prefix = args.output_prefix or (
        "stage_three_smoke" if args.mode == "smoke" else "stage_three_main"
    )
    run_id = args.run_id or (
        "stage-three-smoke-v1" if args.mode == "smoke" else DEFAULT_RUN_ID
    )

    summary = run_search(
        mode=args.mode,
        anchor_name=args.anchor_name,
        scenario_set=args.scenario_set,
        scenario_limit=args.scenario_limit,
        smoke_budget=args.smoke_budget,
        search_budget=args.search_budget,
        output_prefix=output_prefix,
        run_id=run_id,
        q30_drop_tolerance=args.q30_drop_tolerance,
        degradation_drop_tolerance=args.degradation_drop_tolerance,
        risk_aversion=args.risk_aversion,
        initial_radius_scale=args.initial_radius_scale,
        expansion_factor=args.expansion_factor,
        shrink_factor=args.shrink_factor,
        acquisition_beta=args.acquisition_beta,
        feasibility_floor=args.feasibility_floor,
        feasibility_weight=args.feasibility_weight,
        disable_sequence_prior=args.disable_sequence_prior,
        disable_entry_activation=args.disable_entry_activation,
        disable_stage_mask=args.disable_stage_mask,
        verbose=args.verbose,
    )

    compact = {
        "mode": summary["mode"],
        "run_id": summary["run_id"],
        "robust_top_name": summary.get("public_robust_top_name", summary["robust_top_name"]),
        "nominal_top_name": summary.get("public_nominal_top_name", summary["nominal_top_name"]),
        "artifacts": summary["artifacts"],
    }
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()

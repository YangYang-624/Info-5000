#!/usr/bin/env python3
"""Inspect the public stage-two summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGE_NAME = "stage_two"
SUMMARY_PATH = (
    PROJECT_ROOT
    / "experiments"
    / "runs"
    / "stage_two"
    / "results"
    / "stage_two_summary.json"
)


def load_summary(summary_path: Path) -> dict:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    top_name = payload.get("robust_top_name")
    top_candidate = next(
        (
            candidate
            for candidate in payload.get("ranked_candidates", [])
            if candidate.get("name") == top_name
        ),
        {},
    )
    nominal_q30 = None
    for scenario in top_candidate.get("scenario_summaries", []):
        if scenario.get("scenario_id") == "nominal":
            nominal_q30 = scenario.get("candidate_metrics", {}).get("Q30")
            break
    return {
        "payload": payload,
        "compact": {
            "stage_name": STAGE_NAME,
            "stage_role": "four-step trigger-search stage",
            "executable_search_stage": True,
            "summary_path": str(summary_path),
            "run_id": payload.get("run_id"),
            "robust_top_name": payload.get("public_robust_top_name", STAGE_NAME),
            "nominal_q30": nominal_q30,
            "candidates_evaluated": payload.get("candidates_evaluated"),
            "adaptive_candidates_evaluated": payload.get(
                "adaptive_candidates_evaluated"
            ),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Show the public stage-two method summary."
    )
    parser.add_argument("--summary", type=Path, default=SUMMARY_PATH)
    parser.add_argument("--full", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.full:
        print(json.dumps(load_summary(args.summary)["payload"], indent=2))
        return

    compact = load_summary(args.summary)["compact"]
    compact["note"] = (
        f"{STAGE_NAME} keeps its published summary here. The raw protocol ID "
        "stays in the JSON artifact for reproducibility, but the public-facing "
        "name is now stage_two."
    )
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()

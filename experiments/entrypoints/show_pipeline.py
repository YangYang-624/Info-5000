#!/usr/bin/env python3
"""Show the public three-stage method layout."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


DEFAULT_STAGE_ONE_RUN_ID = "stage-one-run-v1"
DEFAULT_STAGE_TWO_RUN_ID = "stage-two-run-v1"
DEFAULT_STAGE_THREE_RUN_ID = "stage-three-run-v1"


def load_stage_summary(summary_path: Path, stage_name: str, stage_role: str) -> dict:
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
        "stage_name": stage_name,
        "stage_role": stage_role,
        "executable_search_stage": True,
        "summary_path": str(summary_path),
        "run_id": payload.get("run_id"),
        "robust_top_name": payload.get("public_robust_top_name", stage_name),
        "nominal_q30": nominal_q30,
        "candidates_evaluated": payload.get("candidates_evaluated"),
        "adaptive_candidates_evaluated": payload.get("adaptive_candidates_evaluated"),
    }


def main() -> None:
    stage_one = load_stage_summary(
        PROJECT_ROOT
        / "experiments"
        / "runs"
        / "stage_one"
        / "results"
        / "stage_one_summary.json",
        "stage_one",
        "four-step tail-search stage",
    )
    stage_one["default_run_id"] = DEFAULT_STAGE_ONE_RUN_ID
    stage_one["entrypoint"] = "experiments/entrypoints/run_stage_one.py"
    stage_one["results_dir"] = "experiments/runs/stage_one/results"
    stage_one["summary_file"] = "experiments/runs/stage_one/results/stage_one_summary.json"
    stage_one["anchor_stage"] = "baseline"

    stage_two = load_stage_summary(
        PROJECT_ROOT
        / "experiments"
        / "runs"
        / "stage_two"
        / "results"
        / "stage_two_summary.json",
        "stage_two",
        "four-step trigger-search stage",
    )
    stage_two["default_run_id"] = DEFAULT_STAGE_TWO_RUN_ID
    stage_two["entrypoint"] = "experiments/entrypoints/run_stage_two.py"
    stage_two["results_dir"] = "experiments/runs/stage_two/results"
    stage_two["summary_file"] = "experiments/runs/stage_two/results/stage_two_summary.json"
    stage_two["anchor_stage"] = "stage_one"

    stage_three = load_stage_summary(
        PROJECT_ROOT
        / "experiments"
        / "runs"
        / "stage_three"
        / "results"
        / "stage_three_main_summary.json",
        "stage_three",
        "five-stage executable search stage",
    )
    stage_three["default_run_id"] = DEFAULT_STAGE_THREE_RUN_ID
    stage_three["entrypoint"] = "experiments/entrypoints/run_stage_three.py"
    stage_three["results_dir"] = "experiments/runs/stage_three/results"
    stage_three["summary_file"] = "experiments/runs/stage_three/results/stage_three_main_summary.json"
    stage_three["anchor_stage"] = "stage_two"

    payload = {
        "pipeline_name": "three_stage_pipeline",
        "stages": [
            stage_one,
            stage_two,
            stage_three,
        ],
        "note": (
            "All three stages are now runnable. Public naming now uses "
            "baseline, stage_one, stage_two, and stage_three. Raw protocol "
            "IDs remain inside artifacts for reproducibility only."
        ),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

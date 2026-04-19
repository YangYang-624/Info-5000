from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[3]
METHODS_DIR = PROJECT_ROOT / "methods"
if str(METHODS_DIR) not in sys.path:
    sys.path.insert(0, str(METHODS_DIR))

from stage_three import (  # noqa: E402
    BASELINE_HEAD,
    REQUIRED_METRICS,
    aggregate_candidate,
    build_scenarios,
    dedupe_protocols,
    evaluate_protocol,
    extract_scenario_metrics,
    find_quest_root,
    flatten_ranked_rows,
    flatten_scenario_rows,
    load_baseline_modules,
    load_metric_contract,
    load_standard_baseline_results,
    public_protocol_label,
    sanitize_protocol,
    utc_now_iso,
    write_csv,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an external validation for the current stage-three winner."
    )
    parser.add_argument("--scenario-set", choices=("combined_stress_v1", "heldout_combo_v1"), default="combined_stress_v1")
    parser.add_argument(
        "--current-summary",
        type=Path,
        default=Path("experiments/runs/stage_three/results/stage_three_main_summary.json"),
    )
    parser.add_argument(
        "--previous-summary",
        type=Path,
        default=Path("experiments/runs/stage_two/results/stage_two_summary.json"),
    )
    parser.add_argument("--current-top-name", type=str, default=None)
    parser.add_argument("--previous-top-name", type=str, default=None)
    parser.add_argument("--output-prefix", type=str, default="external_validation")
    parser.add_argument("--run-id", type=str, default="analysis-external-validation-v1")
    parser.add_argument("--q30-drop-tolerance", type=float, default=0.05)
    parser.add_argument("--degradation-drop-tolerance", type=float, default=0.10)
    parser.add_argument("--risk-aversion", type=float, default=0.35)
    parser.add_argument("--verbose", action="store_true")
    return parser


def load_ranked_protocol(summary_path: Path, chosen_name: str | None) -> Dict[str, Any]:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    target_name = chosen_name or payload["robust_top_name"]
    item = next(candidate for candidate in payload["ranked_candidates"] if candidate["name"] == target_name)
    protocol = sanitize_protocol(
        {
            "name": item["name"],
            "description": item.get("description", ""),
            "type": item.get("type", "Custom"),
            "c_rates": item["c_rates"],
            "step_durations": item["step_durations"],
            "parameters": {
                "source_summary": str(summary_path),
                "source_rank": next(
                    index for index, candidate in enumerate(payload["ranked_candidates"], start=1) if candidate["name"] == target_name
                ),
            },
        }
    )
    return protocol


def load_baseline_protocol(quest_root: Path) -> Dict[str, Any]:
    modules = load_baseline_modules(quest_root)
    baselines = dedupe_protocols(modules["get_all_baselines"]())
    return next(protocol for protocol in baselines if protocol["name"] == BASELINE_HEAD)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    quest_root = find_quest_root(SCRIPT_PATH)
    metric_contract = load_metric_contract(quest_root)
    standard_baselines = load_standard_baseline_results(quest_root)
    modules = load_baseline_modules(quest_root)
    simulator_cls = modules["PyBaMMSimulator"]

    current_summary = (quest_root / args.current_summary).resolve()
    previous_summary = (quest_root / args.previous_summary).resolve()
    current_protocol = load_ranked_protocol(current_summary, args.current_top_name)
    previous_protocol = load_ranked_protocol(previous_summary, args.previous_top_name)
    baseline_protocol = load_baseline_protocol(quest_root)
    scenario_set = "heldout_combo_v1" if args.scenario_set == "combined_stress_v1" else args.scenario_set
    scenarios = build_scenarios(scenario_set)

    protocols = [current_protocol, previous_protocol, baseline_protocol]
    candidate_rows = {
        protocol["name"]: evaluate_protocol(protocol, scenarios, simulator_cls, verbose=args.verbose)
        for protocol in protocols
    }
    anchor_rows = candidate_rows[previous_protocol["name"]]

    ranked = [
        aggregate_candidate(
            protocol,
            candidate_rows[protocol["name"]],
            anchor_rows,
            metric_contract["directions"],
            args.q30_drop_tolerance,
            args.degradation_drop_tolerance,
            args.risk_aversion,
        )
        for protocol in protocols
    ]
    ranked.sort(key=lambda item: tuple(item["sort_key"]), reverse=True)

    nominal_scores = {
        item["name"]: next(
            (scenario["score"] for scenario in item["scenario_summaries"] if scenario["scenario_id"] == "nominal"),
            -1.0,
        )
        for item in ranked
    }
    robust_top_name = ranked[0]["name"] if ranked else None
    nominal_top_name = max(nominal_scores, key=nominal_scores.get)

    output_dir = SCRIPT_PATH.parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{args.output_prefix}_summary.json"
    ranked_csv_path = output_dir / f"{args.output_prefix}_ranked_candidates.csv"
    scenario_csv_path = output_dir / f"{args.output_prefix}_scenario_metrics.csv"

    baseline_metrics = {
        metric: standard_baselines[BASELINE_HEAD][metric] for metric in (*REQUIRED_METRICS, "success")
    }
    current_nominal = extract_scenario_metrics(candidate_rows[current_protocol["name"]], "nominal")
    previous_nominal = extract_scenario_metrics(candidate_rows[previous_protocol["name"]], "nominal")

    summary = {
        "generated_at": utc_now_iso(),
        "mode": "fixed_protocol_validation",
        "run_id": args.run_id,
        "quest_root": str(quest_root),
        "metric_contract_path": str(metric_contract["contract_path"]),
        "baseline_reference": {
            "baseline_id": metric_contract["baseline_id"],
            "variant_id": metric_contract["variant_id"],
            "comparison_baseline_head": BASELINE_HEAD,
            "anchor_protocol": previous_protocol["name"],
            "comparison_baseline_metrics": baseline_metrics,
            "current_nominal_metrics": current_nominal,
            "previous_nominal_metrics": previous_nominal,
        },
        "validation_question": "Does the current stage-three winner remain best under external combined stress?",
        "scenarios": [
            {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "updates": scenario.updates,
            }
            for scenario in scenarios
        ],
        "scenario_set": args.scenario_set,
        "selection_policy": {
            "q30_drop_tolerance": args.q30_drop_tolerance,
            "degradation_drop_tolerance": args.degradation_drop_tolerance,
            "risk_aversion": args.risk_aversion,
            "ranking_rule": [
                "success_rate",
                "guard_pass_rate",
                "worst_score",
                "robust_utility",
                "mean_delta_Q30",
            ],
            "anchor_protocol": previous_protocol["name"],
        },
        "robust_top_name": robust_top_name,
        "public_robust_top_name": public_protocol_label(robust_top_name),
        "nominal_top_name": nominal_top_name,
        "public_nominal_top_name": public_protocol_label(nominal_top_name),
        "ranking_changed_vs_nominal": robust_top_name != nominal_top_name,
        "protocols_evaluated": [protocol["name"] for protocol in protocols],
        "public_protocols_evaluated": [
            public_protocol_label(protocol["name"]) for protocol in protocols
        ],
        "ranked_candidates": ranked,
        "artifacts": {
            "summary_json": str(summary_path),
            "ranked_csv": str(ranked_csv_path),
            "scenario_csv": str(scenario_csv_path),
        },
    }

    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(ranked_csv_path, flatten_ranked_rows(ranked))
    write_csv(scenario_csv_path, flatten_scenario_rows(ranked))

    compact = {
        "mode": summary["mode"],
        "robust_top_name": summary.get("public_robust_top_name", summary["robust_top_name"]),
        "nominal_top_name": summary.get("public_nominal_top_name", summary["nominal_top_name"]),
        "ranking_changed_vs_nominal": summary["ranking_changed_vs_nominal"],
        "artifacts": summary["artifacts"],
    }
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()

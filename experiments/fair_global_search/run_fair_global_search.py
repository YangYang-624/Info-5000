from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

THIS_DIR = Path(__file__).resolve().parent
PSMS_DIR = THIS_DIR.parent / "main" / "ua_psms_v1"
if str(PSMS_DIR) not in sys.path:
    sys.path.insert(0, str(PSMS_DIR))

from robust_protocol_search import (  # type: ignore
    BASELINE_HEAD,
    AblationConfig,
    REQUIRED_METRICS,
    aggregate_candidate,
    build_event_trigger_candidate,
    build_scenarios,
    canonicalize_point,
    dedupe_protocols,
    evaluate_adaptive_candidate,
    evaluate_protocol,
    expected_improvement,
    extract_scenario_metrics,
    feasibility_probability,
    find_quest_root,
    fit_gp_model,
    fit_guard_model,
    flatten_ranked_rows,
    flatten_scenario_rows,
    load_baseline_modules,
    load_metric_contract,
    load_standard_baseline_results,
    normalize_point,
    round_search_value,
    search_objective_from_aggregate,
    sequence_feasibility_prior,
    utc_now_iso,
    write_csv,
    SEARCH_BOUNDS,
    SEARCH_DIMENSIONS,
)


FULL_SPACE_ABLATION = AblationConfig(disable_stage_mask=False)
METHODS = ("random", "global_bo", "psms_global")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a fair from-scratch search benchmark in the shared 7D protocol space."
    )
    parser.add_argument("--mode", choices=("smoke", "search"), default="smoke")
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=["global_bo", "psms_global"])
    parser.add_argument("--scenario-set", choices=("default", "followup_v1", "heldout_combo_v1"), default="followup_v1")
    parser.add_argument("--scenario-limit", type=int, default=None)
    parser.add_argument("--budget", type=int, default=8)
    parser.add_argument("--init-points", type=int, default=6)
    parser.add_argument("--candidate-pool-size", type=int, default=512)
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--min-sequence-prior", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=20260418)
    parser.add_argument("--output-prefix", type=str, default="fair_global")
    parser.add_argument("--q30-drop-tolerance", type=float, default=0.05)
    parser.add_argument("--degradation-drop-tolerance", type=float, default=0.10)
    parser.add_argument("--risk-aversion", type=float, default=0.35)
    parser.add_argument("--acquisition-beta", type=float, default=0.35)
    parser.add_argument("--feasibility-floor", type=float, default=0.85)
    parser.add_argument("--feasibility-weight", type=float, default=0.40)
    parser.add_argument("--verbose", action="store_true")
    return parser


def make_global_root_protocol() -> Dict[str, Any]:
    return {
        "name": "GLOBAL_ROOT",
        "type": "GlobalRoot",
        "description": "Synthetic root protocol used only for naming fair from-scratch candidates.",
        "c_rates": [3.0, 0.0, 4.3, 4.3, 3.05],
        "step_durations": [10.0, 10.0, 2.0, 5.0, 3.0],
        "parameters": {"hold_enabled": False},
    }


def discrete_values(dimension: str) -> List[float]:
    lower, upper = SEARCH_BOUNDS[dimension]
    step = {
        "first_rate": 0.05,
        "rest_minutes": 1.0,
        "third_rate": 0.05,
        "entry_rate": 0.05,
        "trigger_voltage": 0.01,
        "hold_rate": 0.05,
        "hold_minutes": 0.5,
    }[dimension]
    count = int(round((upper - lower) / step)) + 1
    return [round_search_value(dimension, lower + (index * step)) for index in range(count)]


DISCRETE_GRID = {dimension: discrete_values(dimension) for dimension in SEARCH_DIMENSIONS}


def random_point(rng: random.Random) -> tuple[float, ...]:
    raw = tuple(rng.choice(DISCRETE_GRID[dimension]) for dimension in SEARCH_DIMENSIONS)
    return canonicalize_point(raw, ablation_config=FULL_SPACE_ABLATION)


def sample_unique_random_points(
    *,
    count: int,
    seed: int,
    seen: set[tuple[float, ...]] | None = None,
) -> List[tuple[float, ...]]:
    rng = random.Random(seed)
    points: List[tuple[float, ...]] = []
    existing = set(seen or set())
    max_attempts = max(100, count * 100)
    attempts = 0
    while len(points) < count and attempts < max_attempts:
        attempts += 1
        point = random_point(rng)
        if point in existing:
            continue
        existing.add(point)
        points.append(point)
    if len(points) < count:
        raise RuntimeError(f"Unable to sample {count} unique points after {attempts} attempts.")
    return points


def sample_global_candidate_pool(
    *,
    seen_points: set[tuple[float, ...]],
    seed: int,
    pool_size: int,
) -> List[tuple[float, ...]]:
    return sample_unique_random_points(count=pool_size, seed=seed, seen=seen_points)


def propose_next_global_point(
    *,
    method: str,
    global_root: Dict[str, Any],
    observations: Sequence[Dict[str, Any]],
    acquisition_beta: float,
    feasibility_floor: float,
    feasibility_weight: float,
    seed: int,
    pool_size: int,
    min_sequence_prior: float,
) -> tuple[float, ...]:
    seen_points = {item["point"] for item in observations}
    if method == "random":
        raw_pool = sample_unique_random_points(count=max(8, min(pool_size, 64)), seed=seed, seen=seen_points)
        for point in raw_pool:
            protocol = build_event_trigger_candidate(
                global_root,
                point,
                source="random_filter",
                iteration=-1,
                ablation_config=FULL_SPACE_ABLATION,
            )
            if sequence_feasibility_prior(protocol, ablation_config=FULL_SPACE_ABLATION) >= min_sequence_prior:
                return point
        return raw_pool[0]

    candidate_pool = sample_global_candidate_pool(
        seen_points=seen_points,
        seed=seed,
        pool_size=pool_size,
    )
    objective_model = fit_gp_model(observations)
    guard_model = fit_guard_model(observations)
    if objective_model is None and guard_model is None:
        return candidate_pool[0]

    x_pool = np.stack([normalize_point(point) for point in candidate_pool], axis=0)
    best_objective = max(item["search_objective"] for item in observations)
    if objective_model is not None:
        means, sigmas = objective_model.predict(x_pool, return_std=True)
    else:
        means = np.full(len(candidate_pool), best_objective, dtype=float)
        sigmas = np.full(len(candidate_pool), 0.0, dtype=float)
    if guard_model is not None:
        guard_means, guard_sigmas = guard_model.predict(x_pool, return_std=True)
    else:
        guard_means = np.full(len(candidate_pool), 1.0, dtype=float)
        guard_sigmas = np.full(len(candidate_pool), 0.0, dtype=float)

    scored_candidates: List[tuple[float, tuple[float, ...]]] = []
    for point, mean, sigma, guard_mean, guard_sigma in zip(
        candidate_pool, means, sigmas, guard_means, guard_sigmas
    ):
        protocol = build_event_trigger_candidate(
            global_root,
            point,
            source=f"{method}_acquisition",
            iteration=-1,
            ablation_config=FULL_SPACE_ABLATION,
        )
        seq_prior = sequence_feasibility_prior(protocol, ablation_config=FULL_SPACE_ABLATION)
        if seq_prior < min_sequence_prior:
            continue
        performance_bonus = expected_improvement(float(mean), float(sigma), best_objective) + (
            acquisition_beta * float(sigma)
        )
        safe_probability = feasibility_probability(float(guard_mean), float(guard_sigma), feasibility_floor)
        acquisition = (safe_probability * performance_bonus) + (feasibility_weight * safe_probability)
        if method == "psms_global":
            acquisition *= seq_prior
        scored_candidates.append((acquisition, point))
    if not scored_candidates:
        return candidate_pool[0]
    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    return scored_candidates[0][1]


def select_baselines(mode: str, baselines: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if mode == "smoke":
        allowed = {BASELINE_HEAD, "BO_3step_conservative"}
        return [item for item in baselines if item["name"] in allowed]
    return list(baselines)


def run_method(
    *,
    method: str,
    mode: str,
    scenario_set: str,
    scenario_limit: int | None,
    budget: int,
    init_points: int,
    candidate_pool_size: int,
    checkpoint_every: int,
    min_sequence_prior: float,
    seed: int,
    output_prefix: str,
    q30_drop_tolerance: float,
    degradation_drop_tolerance: float,
    risk_aversion: float,
    acquisition_beta: float,
    feasibility_floor: float,
    feasibility_weight: float,
    verbose: bool,
) -> Dict[str, Any]:
    script_path = Path(__file__).resolve()
    quest_root = find_quest_root(script_path)
    modules = load_baseline_modules(quest_root)
    metric_contract = load_metric_contract(quest_root)
    standard_baselines = load_standard_baseline_results(quest_root)
    baselines = dedupe_protocols(modules["get_all_baselines"]())
    selected_baselines = select_baselines(mode, baselines)
    comparison_baseline = next(protocol for protocol in baselines if protocol["name"] == BASELINE_HEAD)
    scenarios = build_scenarios(scenario_set)
    if scenario_limit is not None:
        scenarios = scenarios[:scenario_limit]

    global_root = make_global_root_protocol()
    anchor_rows = evaluate_protocol(comparison_baseline, scenarios, modules["PyBaMMSimulator"], verbose=verbose)
    initial_design = sample_unique_random_points(count=min(budget, init_points), seed=seed)

    observations: List[Dict[str, Any]] = []
    adaptive_protocols: List[Dict[str, Any]] = []
    candidate_rows: Dict[str, List[Dict[str, Any]]] = {}
    best_objective = float("-inf")
    best_name = None
    output_dir = THIS_DIR / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{output_prefix}_{method}_{mode}"
    summary_path = output_dir / f"{stem}_summary.json"
    ranked_csv_path = output_dir / f"{stem}_ranked_candidates.csv"
    scenario_csv_path = output_dir / f"{stem}_scenario_metrics.csv"

    def write_checkpoint(status: str) -> None:
        partial_candidates = dedupe_protocols(selected_baselines + adaptive_protocols)
        partial_ranked = [
            aggregate_candidate(
                protocol,
                candidate_rows[protocol["name"]],
                anchor_rows,
                metric_contract["directions"],
                q30_drop_tolerance,
                degradation_drop_tolerance,
                risk_aversion,
            )
            for protocol in partial_candidates
        ]
        partial_ranked.sort(key=lambda item: tuple(item["sort_key"]), reverse=True)
        nominal_scores = {
            item["name"]: next(
                (scenario["score"] for scenario in item["scenario_summaries"] if scenario["scenario_id"] == "nominal"),
                -1.0,
            )
            for item in partial_ranked
        }
        partial_nominal_top = max(nominal_scores, key=nominal_scores.get)
        partial_robust_top = partial_ranked[0]["name"] if partial_ranked else None
        comparison_baseline_metrics = {
            metric: standard_baselines[BASELINE_HEAD][metric] for metric in (*REQUIRED_METRICS, "success")
        }
        baseline_nominal_metrics = extract_scenario_metrics(anchor_rows, "nominal")
        payload = {
            "generated_at": utc_now_iso(),
            "status": status,
            "mode": mode,
            "method": method,
            "seed": seed,
            "quest_root": str(quest_root),
            "metric_contract_path": str(metric_contract["contract_path"]),
            "scenario_set": scenario_set,
            "space": {
                "shared_search_dimensions": list(SEARCH_DIMENSIONS),
                "shared_ablation": FULL_SPACE_ABLATION.to_dict(),
                "from_scratch": True,
                "warm_start": False,
                "comparison_baseline_head": BASELINE_HEAD,
            },
            "baseline_reference": {
                "baseline_id": metric_contract["baseline_id"],
                "variant_id": metric_contract["variant_id"],
                "comparison_baseline_head": BASELINE_HEAD,
                "comparison_baseline_metrics": comparison_baseline_metrics,
                "baseline_nominal_metrics": baseline_nominal_metrics,
            },
            "selection_policy": {
                "budget": budget,
                "init_points": len(initial_design),
                "candidate_pool_size": candidate_pool_size,
                "checkpoint_every": checkpoint_every,
                "min_sequence_prior": min_sequence_prior,
                "q30_drop_tolerance": q30_drop_tolerance,
                "degradation_drop_tolerance": degradation_drop_tolerance,
                "risk_aversion": risk_aversion,
                "acquisition_beta": acquisition_beta,
                "feasibility_floor": feasibility_floor,
                "feasibility_weight": feasibility_weight,
                "uses_sequence_prior": method == "psms_global",
            },
            "search_controller": {
                "candidate_budget": budget,
                "evaluated_adaptive_candidates": len(adaptive_protocols),
                "best_protocol_name": best_name,
                "best_search_objective": best_objective,
                "history": observations,
            },
            "robust_top_name": partial_robust_top,
            "nominal_top_name": partial_nominal_top,
            "ranking_changed_vs_nominal": partial_robust_top != partial_nominal_top,
            "candidates_evaluated": len(partial_candidates),
            "adaptive_candidates_evaluated": len(adaptive_protocols),
            "baseline_candidates_evaluated": len(selected_baselines),
            "ranked_candidates": partial_ranked,
            "artifacts": {
                "summary_json": str(summary_path),
                "ranked_csv": str(ranked_csv_path),
                "scenario_csv": str(scenario_csv_path),
            },
        }
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        write_csv(ranked_csv_path, flatten_ranked_rows(partial_ranked))
        write_csv(scenario_csv_path, flatten_scenario_rows(partial_ranked))

    for iteration in range(budget):
        if iteration < len(initial_design):
            point = initial_design[iteration]
            source = "init"
        else:
            point = propose_next_global_point(
                method=method,
                global_root=global_root,
                observations=observations,
                acquisition_beta=acquisition_beta,
                feasibility_floor=feasibility_floor,
                feasibility_weight=feasibility_weight,
                seed=seed + iteration,
                pool_size=candidate_pool_size,
                min_sequence_prior=min_sequence_prior,
            )
            source = method

        protocol = build_event_trigger_candidate(
            global_root,
            point,
            source=source,
            iteration=iteration,
            ablation_config=FULL_SPACE_ABLATION,
        )
        rows, summary, objective = evaluate_adaptive_candidate(
            protocol,
            scenarios,
            modules["PyBaMMSimulator"],
            anchor_rows,
            metric_contract["directions"],
            q30_drop_tolerance,
            degradation_drop_tolerance,
            risk_aversion,
            verbose=verbose,
        )
        adaptive_protocols.append(protocol)
        candidate_rows[protocol["name"]] = rows
        improved = objective > best_objective
        if improved:
            best_objective = objective
            best_name = protocol["name"]
        observations.append(
            {
                "name": protocol["name"],
                "point": point,
                "source": source,
                "search_objective": objective,
                "aggregate": summary["aggregate"],
                "improved_best": improved,
                "best_objective_after": best_objective,
                "best_name_after": best_name,
            }
        )
        if checkpoint_every > 0 and ((iteration + 1) % checkpoint_every == 0):
            write_checkpoint(status="running")

    baseline_rows = {
        protocol["name"]: evaluate_protocol(protocol, scenarios, modules["PyBaMMSimulator"], verbose=verbose)
        for protocol in selected_baselines
    }
    candidate_rows.update(baseline_rows)
    write_checkpoint(status="completed")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return summary


def main() -> None:
    args = build_parser().parse_args()
    all_summaries = []
    for method in args.methods:
        summary = run_method(
            method=method,
            mode=args.mode,
            scenario_set=args.scenario_set,
            scenario_limit=args.scenario_limit,
            budget=args.budget,
            init_points=args.init_points,
            candidate_pool_size=args.candidate_pool_size,
            checkpoint_every=args.checkpoint_every,
            min_sequence_prior=args.min_sequence_prior,
            seed=args.seed,
            output_prefix=args.output_prefix,
            q30_drop_tolerance=args.q30_drop_tolerance,
            degradation_drop_tolerance=args.degradation_drop_tolerance,
            risk_aversion=args.risk_aversion,
            acquisition_beta=args.acquisition_beta,
            feasibility_floor=args.feasibility_floor,
            feasibility_weight=args.feasibility_weight,
            verbose=args.verbose,
        )
        all_summaries.append(
            {
                "method": method,
                "robust_top_name": summary["robust_top_name"],
                "nominal_top_name": summary["nominal_top_name"],
                "adaptive_candidates_evaluated": summary["adaptive_candidates_evaluated"],
                "artifacts": summary["artifacts"],
            }
        )
    print(json.dumps({"runs": all_summaries}, indent=2))


if __name__ == "__main__":
    main()

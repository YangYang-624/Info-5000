from __future__ import annotations

import csv
import json
import math
import random
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from statistics import NormalDist, fmean, pstdev
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np
import pybamm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel

REQUIRED_METRICS = ("Q30", "plating_loss", "sei_growth", "total_lli")
DEGRADATION_METRICS = ("plating_loss", "sei_growth", "total_lli")
BASELINE_HEAD = "BO_3step_aggressive"
DEFAULT_RUN_ID = "stage-two-run-v1"
FIXED_TAIL_MINUTES = 3.0
EVENT_TRIGGER_GUARD_MINUTES = 2.0
TAIL_RATE_DROP = 1.25
DEFAULT_TRIGGER_VOLTAGE = 4.16
TAIL_VOLTAGE_LIMIT = 4.20
PUBLIC_ANCHOR_ALIASES = {
    "baseline": BASELINE_HEAD,
    "stage_one": "UA4_VTBO_3.00C_rest10m_4.25C_tail2.40C",
}
FOLLOWUP_ANCHOR_PROTOCOLS = {
    "UA4_VTBO_3.00C_rest10m_4.25C_tail2.40C": {
        "name": "UA4_VTBO_3.00C_rest10m_4.25C_tail2.40C",
        "description": "Public stage-one winner used as the default anchor for the stage-two search.",
        "type": "OursStageTwoAnchor",
        "c_rates": [3.0, 0.0, 4.25, 2.40],
        "step_durations": [10.0, 10.0, 7.0, 3.0],
        "parameters": {
            "source_run_id": "stage-one-reference-v1",
            "source_summary": "experiments/runs/stage_one/results/stage_one_summary.json",
            "tail_rate": 2.40,
            "tail_minutes": 3.0,
        },
    },
}
SEARCH_DIMENSIONS = ("first_rate", "rest_minutes", "third_rate", "trigger_voltage")
SEARCH_BOUNDS = {
    "first_rate": (2.9, 3.1),
    "rest_minutes": (8.0, 12.0),
    "third_rate": (4.05, 4.30),
    "trigger_voltage": (4.14, 4.19),
}
SEARCH_ROUNDING = {
    "first_rate": 0.05,
    "rest_minutes": 1.0,
    "third_rate": 0.05,
    "trigger_voltage": 0.01,
}
BASE_TRUST_REGION_RADII = {
    "first_rate": 0.08,
    "rest_minutes": 1.0,
    "third_rate": 0.12,
    "trigger_voltage": 0.02,
}
MIN_TRUST_REGION_RADII = {
    "first_rate": 0.05,
    "rest_minutes": 1.0,
    "third_rate": 0.05,
    "trigger_voltage": 0.01,
}
TRUST_REGION_SEED_OFFSETS = (
    (0.0, 0.0, 0.05, 0.00),
    (0.0, -1.0, 0.10, -0.01),
    (0.0, 1.0, 0.05, 0.01),
    (0.05, 0.0, 0.05, 0.00),
    (-0.05, 0.0, 0.05, -0.02),
    (0.0, 0.0, 0.10, 0.02),
)


@dataclass
class TrustRegionState:
    center: tuple[float, ...]
    radii: tuple[float, ...]
    best_point: tuple[float, ...]
    best_objective: float
    success_streak: int = 0
    failure_streak: int = 0


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    description: str
    updates: Dict[str, Dict[str, float]]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_protocol_label(protocol_name: str | None) -> str | None:
    if protocol_name is None:
        return None
    if protocol_name == BASELINE_HEAD:
        return "baseline"
    if protocol_name.startswith("UA4_VTBO_"):
        return "stage_one"
    if protocol_name.startswith("UA4_EVTBO_"):
        return "stage_two"
    return protocol_name


def find_quest_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "quest.yaml").exists() and (parent / "baselines").exists():
            return parent
        if (
            (parent / "baselines").exists()
            and (parent / "experiments").exists()
            and (parent / "paper").exists()
        ):
            return parent
    raise FileNotFoundError("Unable to locate quest root from the experiment worktree.")


def ensure_baseline_import_path(quest_root: Path) -> Path:
    baseline_root = quest_root / "baselines" / "vendor" / "ax_pybamm_fastcharge"
    if not baseline_root.exists():
        raise FileNotFoundError(f"Baseline root not found: {baseline_root}")
    baseline_root_str = str(baseline_root)
    if baseline_root_str not in sys.path:
        sys.path.insert(0, baseline_root_str)
    return baseline_root


def load_baseline_modules(quest_root: Path) -> Dict[str, Any]:
    baseline_root = ensure_baseline_import_path(quest_root)
    simulator_module = import_module("multi_objective.utils.pybamm_simulator")
    protocol_module = import_module("multi_objective.utils.baseline_protocols")
    return {
        "baseline_root": baseline_root,
        "PyBaMMSimulator": simulator_module.PyBaMMSimulator,
        "get_all_baselines": protocol_module.get_all_baselines,
        "get_bo_optimal_3step_aggressive": protocol_module.get_bo_optimal_3step_aggressive,
    }


def load_metric_contract(quest_root: Path) -> Dict[str, Any]:
    contract_path = (
        quest_root
        / "baselines"
        / "vendor"
        / "ax_pybamm_fastcharge"
        / "json"
        / "metric_contract.json"
    )
    with contract_path.open("r", encoding="utf-8") as handle:
        contract = json.load(handle)
    metric_contract = contract["metric_contract"]
    directions = {item["metric_id"]: item["direction"] for item in metric_contract["metrics"]}
    return {
        "contract_path": contract_path,
        "baseline_id": contract["baseline_id"],
        "variant_id": contract["variant_id"],
        "primary_metric_id": metric_contract["primary_metric_id"],
        "directions": directions,
    }


def load_standard_baseline_results(quest_root: Path) -> Dict[str, Dict[str, Any]]:
    baseline_path = (
        quest_root
        / "baselines"
        / "vendor"
        / "ax_pybamm_fastcharge"
        / "results"
        / "standard_baselines.json"
    )
    with baseline_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return {entry["name"]: entry for entry in payload["protocols"]}


def default_scenarios() -> List[Scenario]:
    return [
        Scenario("nominal", "No parameter perturbation", {}),
        Scenario(
            "warm_cell",
            "Increase ambient and initial temperature by 5 K",
            {
                "Ambient temperature [K]": {"shift": 5.0},
                "Initial temperature [K]": {"shift": 5.0},
            },
        ),
        Scenario(
            "plating_stress",
            "Increase lithium plating kinetics by 25%",
            {"Lithium plating kinetic rate constant [m.s-1]": {"scale": 1.25}},
        ),
        Scenario(
            "sei_stress",
            "Increase SEI kinetics by 20%",
            {"SEI kinetic rate constant [m.s-1]": {"scale": 1.20}},
        ),
    ]


def followup_v1_scenarios() -> List[Scenario]:
    return [
        Scenario("nominal", "No parameter perturbation", {}),
        Scenario(
            "warm_cell",
            "Increase ambient and initial temperature by 5 K",
            {
                "Ambient temperature [K]": {"shift": 5.0},
                "Initial temperature [K]": {"shift": 5.0},
            },
        ),
        Scenario(
            "hot_cell",
            "Increase ambient and initial temperature by 8 K",
            {
                "Ambient temperature [K]": {"shift": 8.0},
                "Initial temperature [K]": {"shift": 8.0},
            },
        ),
        Scenario(
            "plating_stress",
            "Increase lithium plating kinetics by 25%",
            {"Lithium plating kinetic rate constant [m.s-1]": {"scale": 1.25}},
        ),
        Scenario(
            "sei_stress",
            "Increase SEI kinetics by 20%",
            {"SEI kinetic rate constant [m.s-1]": {"scale": 1.20}},
        ),
    ]


def heldout_combo_v1_scenarios() -> List[Scenario]:
    return [
        Scenario("nominal", "No parameter perturbation", {}),
        Scenario(
            "hot_plating_combo",
            "Increase ambient and initial temperature by 8 K and lithium plating kinetics by 25%",
            {
                "Ambient temperature [K]": {"shift": 8.0},
                "Initial temperature [K]": {"shift": 8.0},
                "Lithium plating kinetic rate constant [m.s-1]": {"scale": 1.25},
            },
        ),
        Scenario(
            "hot_sei_combo",
            "Increase ambient and initial temperature by 8 K and SEI kinetics by 20%",
            {
                "Ambient temperature [K]": {"shift": 8.0},
                "Initial temperature [K]": {"shift": 8.0},
                "SEI kinetic rate constant [m.s-1]": {"scale": 1.20},
            },
        ),
        Scenario(
            "hot_dual_combo",
            "Increase ambient and initial temperature by 8 K with both plating and SEI kinetics stressed",
            {
                "Ambient temperature [K]": {"shift": 8.0},
                "Initial temperature [K]": {"shift": 8.0},
                "Lithium plating kinetic rate constant [m.s-1]": {"scale": 1.25},
                "SEI kinetic rate constant [m.s-1]": {"scale": 1.20},
            },
        ),
    ]


def build_scenarios(scenario_set: str) -> List[Scenario]:
    if scenario_set == "default":
        return default_scenarios()
    if scenario_set == "followup_v1":
        return followup_v1_scenarios()
    if scenario_set == "heldout_combo_v1":
        return heldout_combo_v1_scenarios()
    raise ValueError(f"Unsupported scenario set: {scenario_set}")


def sanitize_protocol(protocol: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": protocol["name"],
        "description": protocol.get("description", ""),
        "type": protocol.get("type", "Custom"),
        "c_rates": [float(value) for value in protocol["c_rates"]],
        "step_durations": [float(value) for value in protocol["step_durations"]],
        "charge_steps": list(protocol.get("charge_steps", [])),
        "parameters": dict(protocol.get("parameters", {})),
    }


def protocol_signature(
    protocol: Dict[str, Any],
) -> tuple[tuple[float, ...], tuple[float, ...], tuple[str, ...]]:
    return (
        tuple(round(value, 6) for value in protocol["c_rates"]),
        tuple(round(value, 6) for value in protocol["step_durations"]),
        tuple(protocol.get("charge_steps", [])),
    )


def dedupe_protocols(protocols: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[tuple[tuple[float, ...], tuple[float, ...], tuple[str, ...]]] = set()
    deduped: List[Dict[str, Any]] = []
    for protocol in protocols:
        clean = sanitize_protocol(protocol)
        signature = protocol_signature(clean)
        if signature in seen:
            continue
        seen.add(signature)
        deduped.append(clean)
    return deduped


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def round_search_value(dimension: str, value: float) -> float:
    step = SEARCH_ROUNDING[dimension]
    rounded = round(value / step) * step
    lower, upper = SEARCH_BOUNDS[dimension]
    return round(clamp(rounded, lower, upper), 2)


def default_tail_rate(third_rate: float) -> float:
    lower, upper = 1.5, 3.5
    return round(clamp(third_rate - TAIL_RATE_DROP, lower, upper), 2)


def default_trigger_voltage(third_rate: float) -> float:
    del third_rate
    return round_search_value("trigger_voltage", DEFAULT_TRIGGER_VOLTAGE)


def protocol_point(protocol: Dict[str, Any]) -> tuple[float, ...]:
    third_index = 2 if len(protocol["c_rates"]) >= 3 else -1
    third_rate = round_search_value("third_rate", float(protocol["c_rates"][third_index]))
    trigger_voltage = round_search_value(
        "trigger_voltage",
        float(protocol.get("parameters", {}).get("trigger_voltage", default_trigger_voltage(third_rate))),
    )
    return (
        round_search_value("first_rate", float(protocol["c_rates"][0])),
        round_search_value("rest_minutes", float(protocol["step_durations"][1])),
        third_rate,
        trigger_voltage,
    )


def format_rest_label(rest_minutes: float) -> str:
    rounded = round_search_value("rest_minutes", rest_minutes)
    if float(rounded).is_integer():
        return f"{int(rounded)}"
    return f"{rounded:.1f}".replace(".", "p")


def format_voltage_label(voltage: float) -> str:
    return f"{round_search_value('trigger_voltage', voltage):.2f}".replace(".", "p")


def build_event_trigger_candidate(
    anchor_protocol: Dict[str, Any],
    point: tuple[float, ...],
    source: str,
    iteration: int,
) -> Dict[str, Any]:
    first_rate, rest_minutes, third_rate, trigger_voltage = point
    active_minutes = round((30.0 - rest_minutes) / 2.0, 2)
    taper_entry_minutes = round(active_minutes - FIXED_TAIL_MINUTES, 2)
    monitor_minutes = round(max(taper_entry_minutes - EVENT_TRIGGER_GUARD_MINUTES, 1.0), 2)
    tail_rate = default_tail_rate(third_rate)
    charge_steps = [
        f"Charge at {first_rate:.2f} C for {active_minutes:.2f} minutes",
        f"Rest for {rest_minutes:.2f} minutes",
        f"Charge at {third_rate:.2f} C for {EVENT_TRIGGER_GUARD_MINUTES:.2f} minutes",
        (
            f"Charge at {third_rate:.2f} C for {monitor_minutes:.2f} minutes "
            f"or until {trigger_voltage:.2f} V"
        ),
        (
            f"Charge at {tail_rate:.2f} C for {FIXED_TAIL_MINUTES:.2f} minutes "
            f"or until {TAIL_VOLTAGE_LIMIT:.2f} V"
        ),
    ]
    return {
        "name": (
            f"UA4_EVTBO_{first_rate:.2f}C_rest{format_rest_label(rest_minutes)}m_"
            f"{third_rate:.2f}C_v{format_voltage_label(trigger_voltage)}"
        ),
        "description": (
            f"Event-triggered voltage-boundary trust-region BO candidate around {anchor_protocol['name']} "
            f"with {first_rate:.2f}C / rest {rest_minutes:.0f}m / "
            f"{third_rate:.2f}C entry + {EVENT_TRIGGER_GUARD_MINUTES:.0f}m guard / "
            f"trigger {trigger_voltage:.2f}V / "
            f"{tail_rate:.2f}C tail"
        ),
        "type": "UA4_EVTBO_Candidate",
        "c_rates": [
            round(first_rate, 4),
            0.0,
            round(third_rate, 4),
            round(third_rate, 4),
            round(tail_rate, 4),
        ],
        "step_durations": [
            active_minutes,
            round(rest_minutes, 2),
            EVENT_TRIGGER_GUARD_MINUTES,
            monitor_minutes,
            FIXED_TAIL_MINUTES,
        ],
        "charge_steps": charge_steps,
        "parameters": {
            "anchor": anchor_protocol["name"],
            "controller_source": source,
            "controller_iteration": iteration,
            "first_rate": round(first_rate, 4),
            "rest_minutes": round(rest_minutes, 2),
            "third_rate": round(third_rate, 4),
            "trigger_voltage": round(trigger_voltage, 4),
            "trigger_margin_voltage": round(TAIL_VOLTAGE_LIMIT - trigger_voltage, 4),
            "guard_minutes": EVENT_TRIGGER_GUARD_MINUTES,
            "event_monitor_minutes": monitor_minutes,
            "tail_rate": round(tail_rate, 4),
            "tail_minutes": FIXED_TAIL_MINUTES,
        },
    }


def make_point(offset_point: tuple[float, ...]) -> tuple[float, ...]:
    return (
        round_search_value("first_rate", offset_point[0]),
        round_search_value("rest_minutes", offset_point[1]),
        round_search_value("third_rate", offset_point[2]),
        round_search_value("trigger_voltage", offset_point[3]),
    )


def build_initial_trust_region_points(anchor_protocol: Dict[str, Any], budget: int) -> List[tuple[float, ...]]:
    if budget <= 0:
        return []
    max_seed_points = min(budget, 4)
    anchor_point = protocol_point(anchor_protocol)
    points: List[tuple[float, ...]] = [anchor_point]
    for first_offset, rest_offset, third_offset, tail_offset in TRUST_REGION_SEED_OFFSETS:
        candidate = make_point(
            (
                anchor_point[0] + first_offset,
                anchor_point[1] + rest_offset,
                anchor_point[2] + third_offset,
                anchor_point[3] + tail_offset,
            )
        )
        if candidate not in points:
            points.append(candidate)
        if len(points) >= max_seed_points:
            break
    return points[:max_seed_points]


def resolve_anchor_protocol(anchor_name: str, baselines: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    anchor_name = PUBLIC_ANCHOR_ALIASES.get(anchor_name, anchor_name)
    baseline_by_name = {protocol["name"]: sanitize_protocol(protocol) for protocol in baselines}
    if anchor_name in baseline_by_name:
        return baseline_by_name[anchor_name]
    if anchor_name in FOLLOWUP_ANCHOR_PROTOCOLS:
        return sanitize_protocol(FOLLOWUP_ANCHOR_PROTOCOLS[anchor_name])
    raise KeyError(f"Unknown anchor protocol: {anchor_name}")


def select_baselines_for_mode(mode: str, baselines: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if mode != "smoke":
        return list(baselines)
    baseline_by_name = {protocol["name"]: sanitize_protocol(protocol) for protocol in baselines}
    selected: List[Dict[str, Any]] = []
    for name in (BASELINE_HEAD, "BO_3step_conservative"):
        if name in baseline_by_name:
            selected.append(baseline_by_name[name])
    return selected


def numeric_value(base_value: Any) -> float:
    if isinstance(base_value, (int, float)):
        return float(base_value)
    try:
        return float(base_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected a numeric parameter value, got {type(base_value)!r}") from exc


def build_parameter_values(parameter_set: str, scenario: Scenario) -> pybamm.ParameterValues:
    parameter_values = pybamm.ParameterValues(parameter_set)
    for name, adjustment in scenario.updates.items():
        base_value = numeric_value(parameter_values[name])
        updated_value = base_value
        if "scale" in adjustment:
            updated_value *= adjustment["scale"]
        if "shift" in adjustment:
            updated_value += adjustment["shift"]
        parameter_values.update({name: updated_value})
    return parameter_values


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def relative_delta(candidate_value: Any, baseline_value: Any, direction: str) -> float | None:
    if not is_number(candidate_value) or not is_number(baseline_value):
        return None
    baseline_abs = abs(float(baseline_value))
    denominator = baseline_abs if baseline_abs > 1e-12 else 1.0
    if direction == "maximize":
        return (float(candidate_value) - float(baseline_value)) / denominator
    return (float(baseline_value) - float(candidate_value)) / denominator


def evaluate_protocol(protocol: Dict[str, Any], scenarios: Sequence[Scenario], simulator_cls: Any, verbose: bool = False) -> List[Dict[str, Any]]:
    scenario_rows: List[Dict[str, Any]] = []
    for scenario in scenarios:
        if verbose:
            print(f"[eval] {protocol['name']} :: {scenario.scenario_id}", flush=True)
        simulator = simulator_cls(degradation_modes=["plating", "SEI"])
        simulator.parameter_values = build_parameter_values(simulator.parameter_set, scenario)
        metrics = simulator.run_and_extract(
            protocol["c_rates"],
            protocol["step_durations"],
            verbose=False,
            charge_steps=protocol.get("charge_steps") or None,
        )
        scenario_rows.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_description": scenario.description,
                "protocol_name": protocol["name"],
                "protocol_type": protocol["type"],
                "metrics": {metric: metrics.get(metric) for metric in (*REQUIRED_METRICS, "success")},
                "parameter_updates": scenario.updates,
            }
        )
    return scenario_rows


def extract_scenario_metrics(candidate_rows: Sequence[Dict[str, Any]], scenario_id: str) -> Dict[str, Any]:
    for row in candidate_rows:
        if row["scenario_id"] == scenario_id:
            return {metric: row["metrics"].get(metric) for metric in (*REQUIRED_METRICS, "success")}
    return {metric: None for metric in (*REQUIRED_METRICS, "success")}


def aggregate_candidate(
    protocol: Dict[str, Any],
    candidate_rows: Sequence[Dict[str, Any]],
    anchor_rows: Sequence[Dict[str, Any]],
    directions: Dict[str, str],
    q30_drop_tolerance: float,
    degradation_drop_tolerance: float,
    risk_aversion: float,
) -> Dict[str, Any]:
    if len(candidate_rows) != len(anchor_rows):
        raise ValueError("Candidate and anchor scenario counts do not match.")

    scenario_summaries: List[Dict[str, Any]] = []
    scenario_scores: List[float] = []
    metric_delta_lists: Dict[str, List[float]] = {metric: [] for metric in REQUIRED_METRICS}
    success_count = 0
    guard_count = 0

    for candidate_row, anchor_row in zip(candidate_rows, anchor_rows):
        candidate_metrics = candidate_row["metrics"]
        anchor_metrics = anchor_row["metrics"]
        deltas: Dict[str, float | None] = {}
        for metric in REQUIRED_METRICS:
            deltas[metric] = relative_delta(candidate_metrics.get(metric), anchor_metrics.get(metric), directions[metric])
            if deltas[metric] is not None:
                metric_delta_lists[metric].append(float(deltas[metric]))

        success_ok = bool(candidate_metrics.get("success")) and bool(anchor_metrics.get("success"))
        if success_ok:
            success_count += 1
        complete_delta_surface = all(deltas[metric] is not None for metric in REQUIRED_METRICS)
        scenario_score = fmean(float(deltas[metric]) for metric in REQUIRED_METRICS) if success_ok and complete_delta_surface else -1.0
        q30_guard = deltas["Q30"] is not None and float(deltas["Q30"]) >= -q30_drop_tolerance
        degradation_guard = all(
            deltas[metric] is not None and float(deltas[metric]) >= -degradation_drop_tolerance
            for metric in DEGRADATION_METRICS
        )
        guard_ok = success_ok and q30_guard and degradation_guard
        if guard_ok:
            guard_count += 1

        scenario_scores.append(float(scenario_score))
        scenario_summaries.append(
            {
                "scenario_id": candidate_row["scenario_id"],
                "score": scenario_score,
                "guard_ok": guard_ok,
                "metric_deltas": deltas,
                "candidate_metrics": candidate_metrics,
                "anchor_metrics": anchor_metrics,
            }
        )

    mean_metric_deltas = {
        metric: (fmean(values) if values else None) for metric, values in metric_delta_lists.items()
    }
    worst_metric_deltas = {
        metric: (min(values) if values else None) for metric, values in metric_delta_lists.items()
    }
    mean_score = fmean(scenario_scores) if scenario_scores else -1.0
    worst_score = min(scenario_scores) if scenario_scores else -1.0
    score_std = pstdev(scenario_scores) if len(scenario_scores) > 1 else 0.0
    robust_utility = mean_score - (risk_aversion * score_std)

    return {
        "name": protocol["name"],
        "type": protocol["type"],
        "description": protocol.get("description", ""),
        "c_rates": protocol["c_rates"],
        "step_durations": protocol["step_durations"],
        "aggregate": {
            "success_rate": success_count / len(candidate_rows),
            "guard_pass_rate": guard_count / len(candidate_rows),
            "mean_score": mean_score,
            "worst_score": worst_score,
            "score_std": score_std,
            "robust_utility": robust_utility,
            "mean_metric_deltas": mean_metric_deltas,
            "worst_metric_deltas": worst_metric_deltas,
        },
        "scenario_summaries": scenario_summaries,
        "sort_key": [
            success_count / len(candidate_rows),
            guard_count / len(candidate_rows),
            worst_score,
            robust_utility,
            mean_metric_deltas["Q30"] if mean_metric_deltas["Q30"] is not None else -1.0,
        ],
    }


def flatten_ranked_rows(ranked: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for index, item in enumerate(ranked, start=1):
        aggregate = item["aggregate"]
        row = {
            "rank": index,
            "protocol_name": item["name"],
            "protocol_type": item["type"],
            "success_rate": aggregate["success_rate"],
            "guard_pass_rate": aggregate["guard_pass_rate"],
            "mean_score": aggregate["mean_score"],
            "worst_score": aggregate["worst_score"],
            "score_std": aggregate["score_std"],
            "robust_utility": aggregate["robust_utility"],
        }
        for metric in REQUIRED_METRICS:
            row[f"mean_delta_{metric}"] = aggregate["mean_metric_deltas"][metric]
            row[f"worst_delta_{metric}"] = aggregate["worst_metric_deltas"][metric]
        rows.append(row)
    return rows


def flatten_scenario_rows(ranked: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in ranked:
        for scenario in item["scenario_summaries"]:
            row = {
                "protocol_name": item["name"],
                "scenario_id": scenario["scenario_id"],
                "score": scenario["score"],
                "guard_ok": scenario["guard_ok"],
            }
            for metric in REQUIRED_METRICS:
                row[f"{metric}"] = scenario["candidate_metrics"].get(metric)
                row[f"anchor_{metric}"] = scenario["anchor_metrics"].get(metric)
                row[f"delta_{metric}"] = scenario["metric_deltas"].get(metric)
            row["success"] = scenario["candidate_metrics"].get("success")
            rows.append(row)
    return rows


def search_objective_from_aggregate(aggregate: Dict[str, Any]) -> float:
    robust_utility = float(aggregate["robust_utility"])
    worst_score = float(aggregate["worst_score"])
    success_rate = float(aggregate["success_rate"])
    guard_pass_rate = float(aggregate["guard_pass_rate"])
    mean_q30 = aggregate["mean_metric_deltas"].get("Q30")
    mean_q30_term = float(mean_q30) if mean_q30 is not None else -1.0
    penalty = (2.0 * (1.0 - success_rate)) + (1.5 * (1.0 - guard_pass_rate))
    return robust_utility + (0.25 * worst_score) + (0.05 * mean_q30_term) - penalty


def clip_unit_interval(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def normalize_point(point: tuple[float, ...]) -> np.ndarray:
    normalized = []
    for dimension, value in zip(SEARCH_DIMENSIONS, point):
        lower, upper = SEARCH_BOUNDS[dimension]
        normalized.append((value - lower) / (upper - lower))
    return np.asarray(normalized, dtype=float)


def fit_gp_model(observations: Sequence[Dict[str, Any]]) -> GaussianProcessRegressor | None:
    if len(observations) < 3:
        return None
    x_train = np.stack([normalize_point(item["point"]) for item in observations], axis=0)
    y_train = np.asarray([item["search_objective"] for item in observations], dtype=float)
    kernel = (
        ConstantKernel(1.0, (0.1, 10.0))
        * Matern(length_scale=[0.25, 0.25, 0.25], length_scale_bounds=(1e-2, 5.0), nu=2.5)
        + WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-8, 1e-2))
    )
    model = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        n_restarts_optimizer=2,
        random_state=0,
    )
    try:
        model.fit(x_train, y_train)
    except Exception:
        return None
    return model


def fit_guard_model(observations: Sequence[Dict[str, Any]]) -> GaussianProcessRegressor | None:
    if len(observations) < 3:
        return None
    x_train = np.stack([normalize_point(item["point"]) for item in observations], axis=0)
    y_train = np.asarray(
        [clip_unit_interval(item["aggregate"]["guard_pass_rate"]) for item in observations],
        dtype=float,
    )
    kernel = (
        ConstantKernel(1.0, (0.1, 10.0))
        * Matern(length_scale=[0.25, 0.25, 0.25], length_scale_bounds=(1e-2, 5.0), nu=2.5)
        + WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-8, 1e-2))
    )
    model = GaussianProcessRegressor(
        kernel=kernel,
        normalize_y=True,
        n_restarts_optimizer=2,
        random_state=1,
    )
    try:
        model.fit(x_train, y_train)
    except Exception:
        return None
    return model


def point_within_trust_region(
    point: tuple[float, ...],
    center: tuple[float, ...],
    radii: tuple[float, ...],
) -> bool:
    for index, value in enumerate(point):
        if abs(value - center[index]) > radii[index] + 1e-9:
            return False
    return True


def sample_candidate_pool(
    center: tuple[float, ...],
    radii: tuple[float, ...],
    seen_points: set[tuple[float, ...]],
    seed: int,
    pool_size: int = 160,
) -> List[tuple[float, ...]]:
    rng = random.Random(seed)
    pool: List[tuple[float, ...]] = []
    for _ in range(pool_size * 6):
        point_values = []
        for index, dimension in enumerate(SEARCH_DIMENSIONS):
            lower, upper = SEARCH_BOUNDS[dimension]
            local_lower = max(lower, center[index] - radii[index])
            local_upper = min(upper, center[index] + radii[index])
            if dimension == "third_rate":
                raw_value = rng.triangular(local_lower, local_upper, local_upper)
            elif dimension == "trigger_voltage":
                raw_value = rng.triangular(local_lower, local_upper, local_upper)
            else:
                raw_value = rng.triangular(local_lower, local_upper, center[index])
            value = round_search_value(dimension, raw_value)
            point_values.append(value)
        point = tuple(point_values)
        if point in seen_points:
            continue
        pool.append(point)
        if len(pool) >= pool_size:
            break
    for index, dimension in enumerate(SEARCH_DIMENSIONS):
        lower, upper = SEARCH_BOUNDS[dimension]
        candidates = (
            list(center),
            list(center),
        )
        candidates[0][index] = round_search_value(dimension, max(lower, center[index] - radii[index]))
        candidates[1][index] = round_search_value(dimension, min(upper, center[index] + radii[index]))
        for candidate in candidates:
            point = tuple(candidate)
            if point not in seen_points and point not in pool:
                pool.append(point)
    return pool


def expected_improvement(mean: float, sigma: float, best: float) -> float:
    if sigma <= 1e-9:
        return 0.0
    distribution = NormalDist()
    z_score = (mean - best) / sigma
    return ((mean - best) * distribution.cdf(z_score)) + (sigma * distribution.pdf(z_score))


def feasibility_probability(mean: float, sigma: float, floor: float) -> float:
    bounded_mean = clip_unit_interval(mean)
    if sigma <= 1e-9:
        return 1.0 if bounded_mean >= floor else 0.0
    distribution = NormalDist()
    z_score = (bounded_mean - floor) / sigma
    return clip_unit_interval(distribution.cdf(z_score))


def propose_next_point(
    objective_model: GaussianProcessRegressor | None,
    guard_model: GaussianProcessRegressor | None,
    observations: Sequence[Dict[str, Any]],
    state: TrustRegionState,
    acquisition_beta: float,
    feasibility_floor: float,
    feasibility_weight: float,
    seed: int,
) -> tuple[float, ...] | None:
    seen_points = {item["point"] for item in observations}
    candidate_pool = sample_candidate_pool(state.center, state.radii, seen_points, seed=seed)
    if not candidate_pool:
        return None
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
    scored_candidates = []
    for point, mean, sigma, guard_mean, guard_sigma in zip(
        candidate_pool, means, sigmas, guard_means, guard_sigmas
    ):
        performance_bonus = expected_improvement(float(mean), float(sigma), best_objective) + (
            acquisition_beta * float(sigma)
        )
        safe_probability = feasibility_probability(float(guard_mean), float(guard_sigma), feasibility_floor)
        acquisition = (safe_probability * performance_bonus) + (feasibility_weight * safe_probability)
        scored_candidates.append((acquisition, point))
    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    return scored_candidates[0][1]


def scale_initial_radii(scale: float) -> tuple[float, ...]:
    radii = []
    for dimension in SEARCH_DIMENSIONS:
        radii.append(round(BASE_TRUST_REGION_RADII[dimension] * scale, 4))
    return tuple(radii)


def expand_radii(
    radii: tuple[float, ...],
    factor: float,
) -> tuple[float, ...]:
    expanded = []
    for radius, dimension in zip(radii, SEARCH_DIMENSIONS):
        lower, upper = SEARCH_BOUNDS[dimension]
        expanded.append(round(min(radius * factor, upper - lower), 4))
    return tuple(expanded)


def shrink_radii(
    radii: tuple[float, ...],
    factor: float,
) -> tuple[float, ...]:
    shrunk = []
    for radius, dimension in zip(radii, SEARCH_DIMENSIONS):
        shrunk.append(round(max(radius * factor, MIN_TRUST_REGION_RADII[dimension]), 4))
    return tuple(shrunk)


def trust_region_converged(radii: tuple[float, ...]) -> bool:
    for radius, dimension in zip(radii, SEARCH_DIMENSIONS):
        if radius > MIN_TRUST_REGION_RADII[dimension] + 1e-9:
            return False
    return True


def evaluate_adaptive_candidate(
    protocol: Dict[str, Any],
    scenarios: Sequence[Scenario],
    simulator_cls: Any,
    anchor_rows: Sequence[Dict[str, Any]],
    directions: Dict[str, str],
    q30_drop_tolerance: float,
    degradation_drop_tolerance: float,
    risk_aversion: float,
    verbose: bool,
) -> tuple[List[Dict[str, Any]], Dict[str, Any], float]:
    candidate_rows = evaluate_protocol(protocol, scenarios, simulator_cls, verbose=verbose)
    aggregate = aggregate_candidate(
        protocol,
        candidate_rows,
        anchor_rows,
        directions,
        q30_drop_tolerance,
        degradation_drop_tolerance,
        risk_aversion,
    )
    search_objective = search_objective_from_aggregate(aggregate["aggregate"])
    return candidate_rows, aggregate, search_objective


def run_trust_region_controller(
    *,
    anchor_protocol: Dict[str, Any],
    scenarios: Sequence[Scenario],
    simulator_cls: Any,
    directions: Dict[str, str],
    candidate_budget: int,
    q30_drop_tolerance: float,
    degradation_drop_tolerance: float,
    risk_aversion: float,
    initial_radius_scale: float,
    expansion_factor: float,
    shrink_factor: float,
    acquisition_beta: float,
    feasibility_floor: float,
    feasibility_weight: float,
    verbose: bool,
) -> Dict[str, Any]:
    budget = max(1, candidate_budget)
    anchor_rows = evaluate_protocol(anchor_protocol, scenarios, simulator_cls, verbose=verbose)
    anchor_summary = aggregate_candidate(
        anchor_protocol,
        anchor_rows,
        anchor_rows,
        directions,
        q30_drop_tolerance,
        degradation_drop_tolerance,
        risk_aversion,
    )
    anchor_objective = search_objective_from_aggregate(anchor_summary["aggregate"])
    anchor_point = protocol_point(anchor_protocol)
    state = TrustRegionState(
        center=anchor_point,
        radii=scale_initial_radii(initial_radius_scale),
        best_point=anchor_point,
        best_objective=anchor_objective,
    )
    adaptive_protocols: List[Dict[str, Any]] = [anchor_protocol]
    candidate_rows = {anchor_protocol["name"]: anchor_rows}
    observations = [
        {
            "name": anchor_protocol["name"],
            "point": anchor_point,
            "source": "anchor",
            "search_objective": anchor_objective,
            "aggregate": anchor_summary["aggregate"],
            "improved_best": True,
            "trust_region_center_after": anchor_point,
            "trust_region_radii_after": state.radii,
        }
    ]
    seed_points = build_initial_trust_region_points(anchor_protocol, budget)
    stop_reason = "budget_exhausted"

    while len(adaptive_protocols) < budget:
        iteration = len(adaptive_protocols)
        if iteration < len(seed_points):
            next_point = seed_points[iteration]
            source = "seed"
        else:
            objective_model = fit_gp_model(observations)
            guard_model = fit_guard_model(observations)
            next_point = propose_next_point(
                objective_model,
                guard_model,
                observations,
                state,
                acquisition_beta=acquisition_beta,
                feasibility_floor=feasibility_floor,
                feasibility_weight=feasibility_weight,
                seed=20260415 + iteration,
            )
            source = "acquisition"
        if next_point is None:
            stop_reason = "no_unique_candidate"
            break
        if next_point in {item["point"] for item in observations}:
            stop_reason = "duplicate_candidate"
            break
        protocol = build_event_trigger_candidate(anchor_protocol, next_point, source=source, iteration=iteration)
        rows, summary, objective = evaluate_adaptive_candidate(
            protocol,
            scenarios,
            simulator_cls,
            anchor_rows,
            directions,
            q30_drop_tolerance,
            degradation_drop_tolerance,
            risk_aversion,
            verbose=verbose,
        )
        candidate_rows[protocol["name"]] = rows
        adaptive_protocols.append(protocol)
        guard_pass_rate = float(summary["aggregate"]["guard_pass_rate"])
        improved = (guard_pass_rate >= feasibility_floor) and (objective > (state.best_objective + 1e-4))
        if improved:
            state.best_objective = objective
            state.best_point = next_point
            state.center = next_point
            state.success_streak += 1
            state.failure_streak = 0
            if state.success_streak >= 2:
                state.radii = expand_radii(state.radii, expansion_factor)
                state.success_streak = 0
        else:
            state.failure_streak += 1
            state.success_streak = 0
            if state.failure_streak >= 2:
                state.radii = shrink_radii(state.radii, shrink_factor)
                state.failure_streak = 0
                if trust_region_converged(state.radii):
                    stop_reason = "trust_region_floor"
        observations.append(
            {
                "name": protocol["name"],
                "point": next_point,
                "source": source,
                "search_objective": objective,
                "aggregate": summary["aggregate"],
                "guard_pass_floor": feasibility_floor,
                "improved_best": improved,
                "trust_region_center_after": state.center,
                "trust_region_radii_after": state.radii,
            }
        )
        if stop_reason == "trust_region_floor":
            break

    return {
        "anchor_rows": anchor_rows,
        "candidate_rows": candidate_rows,
        "adaptive_protocols": adaptive_protocols,
        "observations": observations,
        "controller_summary": {
            "candidate_budget": budget,
            "evaluated_adaptive_candidates": len(adaptive_protocols),
            "best_protocol_name": max(observations, key=lambda item: item["search_objective"])["name"],
            "best_search_objective": max(item["search_objective"] for item in observations),
            "best_point": state.best_point,
            "acquisition_mode": "guard_feasibility_weighted_expected_improvement",
            "feasibility_floor": feasibility_floor,
            "feasibility_weight": feasibility_weight,
            "final_center": state.center,
            "final_radii": state.radii,
            "stop_reason": stop_reason,
            "seed_offsets": list(TRUST_REGION_SEED_OFFSETS),
            "history": observations,
        },
    }


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_search(
    *,
    mode: str,
    anchor_name: str,
    scenario_set: str,
    scenario_limit: int | None,
    smoke_budget: int,
    search_budget: int,
    output_prefix: str,
    run_id: str,
    q30_drop_tolerance: float,
    degradation_drop_tolerance: float,
    risk_aversion: float,
    initial_radius_scale: float,
    expansion_factor: float,
    shrink_factor: float,
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
    anchor_protocol = resolve_anchor_protocol(anchor_name, baselines)
    scenarios = build_scenarios(scenario_set)
    if scenario_limit is not None:
        scenarios = scenarios[:scenario_limit]
    controller = run_trust_region_controller(
        anchor_protocol=anchor_protocol,
        scenarios=scenarios,
        simulator_cls=modules["PyBaMMSimulator"],
        directions=metric_contract["directions"],
        candidate_budget=smoke_budget if mode == "smoke" else search_budget,
        q30_drop_tolerance=q30_drop_tolerance,
        degradation_drop_tolerance=degradation_drop_tolerance,
        risk_aversion=risk_aversion,
        initial_radius_scale=initial_radius_scale,
        expansion_factor=expansion_factor,
        shrink_factor=shrink_factor,
        acquisition_beta=acquisition_beta,
        feasibility_floor=feasibility_floor,
        feasibility_weight=feasibility_weight,
        verbose=verbose,
    )
    selected_baselines = select_baselines_for_mode(mode, baselines)
    candidate_rows = dict(controller["candidate_rows"])
    baseline_rows = {
        protocol["name"]: evaluate_protocol(protocol, scenarios, modules["PyBaMMSimulator"], verbose=verbose)
        for protocol in selected_baselines
    }
    candidate_rows.update(baseline_rows)
    adaptive_protocols = controller["adaptive_protocols"]
    candidates = dedupe_protocols(selected_baselines + adaptive_protocols)
    anchor_rows = controller["anchor_rows"]

    ranked = [
        aggregate_candidate(
            protocol,
            candidate_rows[protocol["name"]],
            anchor_rows,
            metric_contract["directions"],
            q30_drop_tolerance,
            degradation_drop_tolerance,
            risk_aversion,
        )
        for protocol in candidates
    ]
    ranked.sort(key=lambda item: tuple(item["sort_key"]), reverse=True)

    ranked_rows = flatten_ranked_rows(ranked)
    scenario_rows = flatten_scenario_rows(ranked)
    output_dir = quest_root / "experiments" / "runs" / "stage_two" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"{output_prefix}_summary.json"
    ranked_csv_path = output_dir / f"{output_prefix}_ranked_candidates.csv"
    scenario_csv_path = output_dir / f"{output_prefix}_scenario_metrics.csv"

    nominal_scores = {
        item["name"]: next(
            (scenario["score"] for scenario in item["scenario_summaries"] if scenario["scenario_id"] == "nominal"),
            -1.0,
        )
        for item in ranked
    }
    nominal_top_name = max(nominal_scores, key=nominal_scores.get)
    robust_top_name = ranked[0]["name"] if ranked else None
    comparison_baseline_metrics = {
        metric: standard_baselines[BASELINE_HEAD][metric] for metric in (*REQUIRED_METRICS, "success")
    }
    anchor_nominal_metrics = extract_scenario_metrics(anchor_rows, "nominal")

    summary = {
        "generated_at": utc_now_iso(),
        "mode": mode,
        "run_id": run_id,
        "quest_root": str(quest_root),
        "metric_contract_path": str(metric_contract["contract_path"]),
        "baseline_reference": {
            "baseline_id": metric_contract["baseline_id"],
            "variant_id": metric_contract["variant_id"],
            "comparison_baseline_head": BASELINE_HEAD,
            "anchor_protocol": anchor_protocol["name"],
            "comparison_baseline_metrics": comparison_baseline_metrics,
            "anchor_nominal_metrics": anchor_nominal_metrics,
        },
        "scenarios": [
            {
                "scenario_id": scenario.scenario_id,
                "description": scenario.description,
                "updates": scenario.updates,
            }
            for scenario in scenarios
        ],
        "scenario_set": scenario_set,
        "selection_policy": {
            "q30_drop_tolerance": q30_drop_tolerance,
            "degradation_drop_tolerance": degradation_drop_tolerance,
            "risk_aversion": risk_aversion,
            "initial_radius_scale": initial_radius_scale,
            "expansion_factor": expansion_factor,
            "shrink_factor": shrink_factor,
            "acquisition_beta": acquisition_beta,
            "feasibility_floor": feasibility_floor,
            "feasibility_weight": feasibility_weight,
            "ranking_rule": [
                "success_rate",
                "guard_pass_rate",
                "worst_score",
                "robust_utility",
                "mean_delta_Q30",
            ],
        },
        "search_controller": controller["controller_summary"],
        "public_anchor_name": public_protocol_label(anchor_protocol["name"]),
        "robust_top_name": robust_top_name,
        "public_robust_top_name": public_protocol_label(robust_top_name),
        "nominal_top_name": nominal_top_name,
        "public_nominal_top_name": public_protocol_label(nominal_top_name),
        "ranking_changed_vs_nominal": robust_top_name != nominal_top_name,
        "candidates_evaluated": len(candidates),
        "adaptive_candidates_evaluated": len(adaptive_protocols),
        "baseline_candidates_evaluated": len(selected_baselines),
        "ranked_candidates": ranked,
        "artifacts": {
            "summary_json": str(summary_path),
            "ranked_csv": str(ranked_csv_path),
            "scenario_csv": str(scenario_csv_path),
        },
    }

    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    write_csv(ranked_csv_path, ranked_rows)
    write_csv(scenario_csv_path, scenario_rows)

    return summary

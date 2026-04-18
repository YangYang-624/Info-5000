from __future__ import annotations

import argparse
import json

from robust_protocol_search import run_search


def ablation_suffix_from_args(args: argparse.Namespace) -> str:
    parts = []
    if args.disable_sequence_prior:
        parts.append("noprior")
    if args.disable_entry_activation:
        parts.append("noentry")
    if args.disable_stage_mask:
        parts.append("nomask")
    return "_".join(parts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the physics-prior masked multi-stage event-trigger search scaffold."
    )
    parser.add_argument("--mode", choices=("smoke", "search"), default="smoke")
    parser.add_argument("--anchor", type=str, default="UA4_EVTBO_3.00C_rest10m_4.30C_v4p16")
    parser.add_argument("--scenario-set", choices=("default", "followup_v1", "heldout_combo_v1"), default="followup_v1")
    parser.add_argument("--scenario-limit", type=int, default=None)
    parser.add_argument("--smoke-budget", type=int, default=6)
    parser.add_argument("--search-budget", type=int, default=12)
    parser.add_argument("--output-prefix", type=str, default=None)
    parser.add_argument("--run-id", type=str, default="run-psms-ua4-v1")
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
    stage_mask_group = parser.add_mutually_exclusive_group()
    stage_mask_group.add_argument("--enable-stage-mask", dest="disable_stage_mask", action="store_false")
    stage_mask_group.add_argument("--disable-stage-mask", dest="disable_stage_mask", action="store_true")
    parser.set_defaults(disable_stage_mask=False)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_prefix = args.output_prefix
    ablation_suffix = ablation_suffix_from_args(args)
    if output_prefix is None:
        output_prefix = "ua_psms_smoke" if args.mode == "smoke" else "ua_psms_search"
        if ablation_suffix:
            output_prefix = f"{output_prefix}_{ablation_suffix}"
    summary = run_search(
        mode=args.mode,
        anchor_name=args.anchor,
        scenario_set=args.scenario_set,
        scenario_limit=args.scenario_limit,
        smoke_budget=args.smoke_budget,
        search_budget=args.search_budget,
        output_prefix=output_prefix,
        run_id=args.run_id,
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
        "robust_top_name": summary["robust_top_name"],
        "nominal_top_name": summary["nominal_top_name"],
        "ranking_changed_vs_nominal": summary["ranking_changed_vs_nominal"],
        "adaptive_candidates_evaluated": summary["adaptive_candidates_evaluated"],
        "artifacts": summary["artifacts"],
    }
    print(json.dumps(compact, indent=2))


if __name__ == "__main__":
    main()

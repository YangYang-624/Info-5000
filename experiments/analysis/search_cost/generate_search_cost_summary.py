from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def github_direct_bo_rows() -> list[dict]:
    return [
        {
            "method": "GitHub Direct BO (3-Step)",
            "search_style": "direct_bo",
            "space": "3-step",
            "evaluations_total": 109,
            "evaluations_adaptive": 105,
            "q30_nominal": 0.08990,
            "notes": "4 preexisting + 35 epochs x 3 trials from the original 3-step notebook.",
        },
        {
            "method": "GitHub Direct BO (5-Step)",
            "search_style": "direct_bo",
            "space": "5-step",
            "evaluations_total": 124,
            "evaluations_adaptive": 120,
            "q30_nominal": None,
            "notes": "4 preexisting + 40 epochs x 3 trials from the original 5-step notebook.",
        },
    ]


def stage_row(method: str, space: str, path: Path) -> dict:
    payload = load_json(path)
    nominal_q30 = None
    for item in payload["ranked_candidates"]:
        if item["name"] == payload["robust_top_name"]:
            for scenario in item["scenario_summaries"]:
                if scenario["scenario_id"] == "nominal":
                    nominal_q30 = scenario["candidate_metrics"]["Q30"]
                    break
            break
    return {
        "method": method,
        "search_style": "hierarchical_stage",
        "space": space,
        "evaluations_total": payload["candidates_evaluated"],
        "evaluations_adaptive": payload["adaptive_candidates_evaluated"],
        "q30_nominal": nominal_q30,
        "notes": f"stop_reason={payload['search_controller'].get('stop_reason')}",
    }


def main() -> None:
    rows = []
    rows.extend(github_direct_bo_rows())
    rows.append(
        stage_row(
            "Stage One",
            "stage_one",
            ROOT / "experiments" / "runs" / "stage_one" / "results" / "stage_one_summary.json",
        )
    )
    rows.append(
        stage_row(
            "Stage Two",
            "stage_two",
            ROOT / "experiments" / "runs" / "stage_two" / "results" / "stage_two_summary.json",
        )
    )
    rows.append(
        stage_row(
            "Stage Three",
            "stage_three",
            ROOT / "experiments" / "runs" / "stage_three" / "results" / "stage_three_main_summary.json",
        )
    )

    hierarchical_total = {
        "method": "Full Three-Stage Pipeline",
        "search_style": "hierarchical_pipeline",
        "space": "stage_one->stage_two->stage_three",
        "evaluations_total": sum(row["evaluations_total"] for row in rows if row["search_style"] == "hierarchical_stage"),
        "evaluations_adaptive": sum(
            row["evaluations_adaptive"] for row in rows if row["search_style"] == "hierarchical_stage"
        ),
        "q30_nominal": rows[-1]["q30_nominal"],
        "notes": "End-to-end cost across the three promoted stages; final protocol quality taken from stage three.",
    }
    rows.append(hierarchical_total)

    output_dir = ROOT / "experiments" / "analysis" / "search_cost"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "search_cost_comparison.json"
    md_path = output_dir / "search_cost_comparison.md"
    json_path.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")

    lines = [
        "# Search Cost Comparison",
        "",
        "| Method | Style | Space | Total evals | Adaptive evals | Nominal Q30 | Notes |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        q30 = "-" if row["q30_nominal"] is None else f"{row['q30_nominal']:.5f}"
        lines.append(
            f"| {row['method']} | {row['search_style']} | {row['space']} | "
            f"{row['evaluations_total']} | {row['evaluations_adaptive']} | {q30} | {row['notes']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(json_path), "md": str(md_path)}, indent=2))


if __name__ == "__main__":
    main()

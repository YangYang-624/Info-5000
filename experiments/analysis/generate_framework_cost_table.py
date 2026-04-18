from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def github_direct_bo_rows() -> list[dict]:
    return [
        {
            "method": "GitHub-DirectBO-3step",
            "search_style": "direct_bo",
            "space": "3-step",
            "evaluations_total": 109,
            "evaluations_adaptive": 105,
            "q30_nominal": 0.08990,
            "notes": "4 preexisting + 35 epochs x 3 trials from the original 3-step notebook.",
        },
        {
            "method": "GitHub-DirectBO-5step",
            "search_style": "direct_bo",
            "space": "5-step",
            "evaluations_total": 124,
            "evaluations_adaptive": 120,
            "q30_nominal": None,
            "notes": "4 preexisting + 40 epochs x 3 trials from the original 5-step notebook.",
        },
    ]


def stage_row(method: str, path: Path) -> dict:
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
        "space": payload["robust_top_name"].split("_")[0],
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
            "VTBO",
            Path(
                "/data/yangyang/class/info5000/DeepScientist/quests/001/.ds/worktrees/run-vtbo-ua4-v1/"
                "experiments/main/ua_vtbo_v1/results/ua_vtbo_search_summary.json"
            ),
        )
    )
    rows.append(
        stage_row(
            "EVTBO",
            ROOT / "experiments" / "reference" / "ua_evtbo_search_summary.json",
        )
    )
    rows.append(
        stage_row(
            "PSMS-v2",
            ROOT / "experiments" / "main" / "ua_psms_v1" / "results" / "ua_psms_v2_search_main_summary.json",
        )
    )

    hierarchical_total = {
        "method": "Hierarchical-Pipeline-Total",
        "search_style": "hierarchical_pipeline",
        "space": "VTBO->EVTBO->PSMS",
        "evaluations_total": sum(row["evaluations_total"] for row in rows if row["search_style"] == "hierarchical_stage"),
        "evaluations_adaptive": sum(
            row["evaluations_adaptive"] for row in rows if row["search_style"] == "hierarchical_stage"
        ),
        "q30_nominal": rows[-1]["q30_nominal"],
        "notes": "End-to-end cost across the three promoted stages; final protocol quality taken from PSMS-v2.",
    }
    rows.append(hierarchical_total)

    output_dir = ROOT / "experiments" / "analysis" / "framework_cost"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "framework_cost_table.json"
    md_path = output_dir / "framework_cost_table.md"
    json_path.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")

    lines = [
        "# Framework Cost Table",
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

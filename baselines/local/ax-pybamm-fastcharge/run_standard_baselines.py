import csv
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import torch

from multi_objective.utils.baseline_protocols import get_all_baselines
from multi_objective.utils.pybamm_simulator import PyBaMMSimulator


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
JSON_PATH = RESULTS_DIR / "standard_baselines.json"
CSV_PATH = RESULTS_DIR / "standard_baselines.csv"


def _sanitize(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    simulator = PyBaMMSimulator(degradation_modes=["plating", "SEI"])
    protocols = get_all_baselines()
    rows = []

    for protocol in protocols:
        metrics = simulator.run_and_extract(
            protocol["c_rates"],
            protocol["step_durations"],
            verbose=True,
        )

        row = {
            "name": protocol["name"],
            "type": protocol["type"],
            "description": protocol["description"],
            "c_rates": protocol["c_rates"],
            "step_durations": protocol["step_durations"],
            "Q30": _sanitize(metrics["Q30"]),
            "plating_loss": _sanitize(metrics["plating_loss"]),
            "sei_growth": _sanitize(metrics["sei_growth"]),
            "sei_li_loss": _sanitize(metrics["sei_li_loss"]),
            "total_lli": _sanitize(metrics["total_lli"]),
            "success": metrics["success"],
        }
        rows.append(row)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda": getattr(torch.version, "cuda", None),
            "cuda_available": torch.cuda.is_available(),
        },
        "protocol_count": len(rows),
        "protocols": rows,
    }

    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "type",
                "description",
                "Q30",
                "plating_loss",
                "sei_growth",
                "sei_li_loss",
                "total_lli",
                "success",
                "c_rates",
                "step_durations",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "c_rates": json.dumps(row["c_rates"]),
                    "step_durations": json.dumps(row["step_durations"]),
                }
            )

    print(f"Wrote {len(rows)} protocols to {JSON_PATH}")
    print(f"Wrote CSV to {CSV_PATH}")


if __name__ == "__main__":
    main()

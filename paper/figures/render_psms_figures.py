#!/usr/bin/env python3
"""Render paper-facing figures for the PSMS-v2 paper line.

This script generates three figures:
1. Frontier progression under the fixed comparison contract.
2. The PSMS-v2 staged protocol representation.
3. Held-out combined-stress validation comparison.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch


STYLE_PATH = Path(
    "/data/yangyang/.nvm/versions/node/v22.18.0/lib/node_modules/"
    "@researai/deepscientist/src/skills/figure-polish/assets/"
    "deepscientist-academic.mplstyle"
)

PAPER_ROOT = Path(__file__).resolve().parent.parent
QUEST_ROOT = Path(__file__).resolve().parents[5]
FIGURE_ROOT = Path(__file__).resolve().parent
EVIDENCE_LEDGER_PATH = PAPER_ROOT / "evidence_ledger.json"
HELDOUT_SUMMARY_PATH = (
    QUEST_ROOT
    / ".ds/worktrees/idea-idea-8d0629d2/experiments/analysis/"
    / "heldout_combo_validation/results/psms_v2_heldout_combo_v1_summary.json"
)

MIST_STONE = {"light": "#F3EEE8", "mid": "#D8D1C7", "dark": "#8A9199"}
SAGE_CLAY = {"light": "#E7E1D6", "mid": "#B7A99A", "dark": "#7F8F84"}
DUST_ROSE = {"light": "#F2E9E6", "mid": "#D8C3BC", "dark": "#B88C8C"}


# Accepted nominal baseline from the stabilized paper-facing comparison table.
BASELINE_NOMINAL = {
    "Q30": 0.08989501345816822,
    "plating_loss": 0.3221755155634952,
    "sei_growth": 58.362167723656874,
    "total_lli": 0.014066515184779317,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def apply_style() -> None:
    plt.rcdefaults()
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": MIST_STONE["mid"],
            "axes.labelcolor": MIST_STONE["dark"],
            "axes.titlesize": 9.5,
            "axes.titlepad": 8,
            "axes.linewidth": 0.8,
            "axes.xmargin": 0.02,
            "axes.ymargin": 0.04,
            "font.size": 9,
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
            "grid.color": MIST_STONE["light"],
            "grid.alpha": 0.45,
            "grid.linestyle": "-",
            "lines.linewidth": 1.8,
            "legend.frameon": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "xtick.color": MIST_STONE["dark"],
            "ytick.color": MIST_STONE["dark"],
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
        }
    )


def ensure_dirs() -> None:
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)


def load_evidence_items() -> dict[str, dict]:
    data = load_json(EVIDENCE_LEDGER_PATH)
    return {item["item_id"]: item for item in data["items"]}


def metric_map(item: dict) -> dict[str, float]:
    return {entry["metric_id"]: entry["value"] for entry in item.get("key_metrics", [])}


def load_frontier_table(items: dict[str, dict]) -> list[dict]:
    return [
        {
            "label": "BO",
            "title": "BO_3step_aggressive",
            "metrics": BASELINE_NOMINAL,
            "color": MIST_STONE["dark"],
        },
        {
            "label": "VTBO",
            "title": "UA4_VTBO",
            "metrics": metric_map(items["run-vtbo-ua4-v1"]),
            "color": MIST_STONE["mid"],
        },
        {
            "label": "EVTBO",
            "title": "UA4_EVTBO",
            "metrics": metric_map(items["run-evtbo-ua4-v1"]),
            "color": SAGE_CLAY["mid"],
        },
        {
            "label": "PSMS-v2",
            "title": "UA5_PSMS",
            "metrics": metric_map(items["run-psms-v2-main-v1"]),
            "color": SAGE_CLAY["dark"],
        },
    ]


def load_heldout_rows() -> list[dict]:
    data = load_json(HELDOUT_SUMMARY_PATH)
    wanted = {
        "BO_3step_aggressive": {"label": "BO", "color": DUST_ROSE["mid"]},
        "UA4_EVTBO_3.00C_rest10m_4.30C_v4p16": {
            "label": "EVTBO",
            "color": MIST_STONE["dark"],
        },
        "UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m": {
            "label": "PSMS-v2",
            "color": SAGE_CLAY["dark"],
        },
    }
    rows = []
    for candidate in data["ranked_candidates"]:
        meta = wanted.get(candidate["name"])
        if not meta:
            continue
        rows.append(
            {
                "label": meta["label"],
                "color": meta["color"],
                "aggregate": candidate["aggregate"],
            }
        )
    order = {"BO": 0, "EVTBO": 1, "PSMS-v2": 2}
    rows.sort(key=lambda row: order[row["label"]])
    return rows


def save_figure(fig: plt.Figure, stem: str) -> dict[str, str]:
    png_path = FIGURE_ROOT / f"{stem}.png"
    pdf_path = FIGURE_ROOT / f"{stem}.pdf"
    svg_path = FIGURE_ROOT / f"{stem}.svg"
    fig.savefig(png_path, dpi=220, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return {"png": str(png_path), "pdf": str(pdf_path), "svg": str(svg_path)}


def render_frontier_progression(frontier_rows: list[dict]) -> dict[str, str]:
    metrics = [
        ("Q30", "Q30 (Ah)", "higher"),
        ("plating_loss", "plating loss", "lower"),
        ("sei_growth", "SEI growth", "lower"),
        ("total_lli", "total LLI", "lower"),
    ]
    labels = [row["label"] for row in frontier_rows]

    apply_style()
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 3.05))
    fig.suptitle(
        "Verified frontier progression under the fixed four-metric contract",
        x=0.5,
        y=1.03,
        fontsize=11,
    )
    fig.text(
        0.5,
        0.90,
        "PSMS-v2 is the only highlighted endpoint; every panel stays on the same nominal comparison surface.",
        ha="center",
        va="center",
        fontsize=8,
        color=MIST_STONE["dark"],
    )
    fig.subplots_adjust(bottom=0.20, top=0.76, wspace=0.22)

    for ax, (metric_key, title, direction) in zip(axes, metrics):
        values = [row["metrics"][metric_key] for row in frontier_rows]
        positions = range(len(values))
        ax.axvspan(
            positions[-1] - 0.42,
            positions[-1] + 0.42,
            color=SAGE_CLAY["light"],
            alpha=0.18,
            zorder=0,
        )
        ax.plot(
            list(positions),
            values,
            color=MIST_STONE["mid"],
            linewidth=1.5,
            zorder=1,
        )
        ax.scatter(
            list(positions[:-1]),
            values[:-1],
            s=28,
            color=MIST_STONE["dark"],
            edgecolors="white",
            linewidths=0.7,
            zorder=2,
        )
        ax.scatter(
            positions[-1],
            values[-1],
            s=54,
            color=SAGE_CLAY["dark"],
            edgecolors="white",
            linewidths=0.8,
            zorder=3,
        )
        ax.set_xticks(list(positions), labels)
        ax.set_title(title, fontsize=9)
        ax.text(
            0.5,
            1.02,
            "higher is better" if direction == "higher" else "lower is better",
            transform=ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=7.2,
            color=MIST_STONE["dark"],
        )
        ax.grid(axis="y", alpha=0.18)
        ax.tick_params(axis="both", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if direction == "higher":
            delta_pct = ((values[-1] - values[0]) / values[0]) * 100
            ax.annotate(
                f"+{delta_pct:.2f}%",
                xy=(positions[-1], values[-1]),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=SAGE_CLAY["dark"],
            )
    return save_figure(fig, "figure1_frontier_progression")


def render_protocol_representation() -> dict[str, str]:
    stages = [
        ("Charge", "3.00C\n10 min", MIST_STONE["mid"]),
        ("Rest", "0C\n10 min", MIST_STONE["light"]),
        ("Entry", "4.50C\n2 min", DUST_ROSE["mid"]),
        ("Monitor", "4.30C\nto 4.18V", SAGE_CLAY["mid"]),
        ("Hold", "3.35C\n1.5 min", DUST_ROSE["light"]),
        ("Tail", "2.80C\nfinal taper", MIST_STONE["light"]),
    ]
    widths = [1.2, 1.0, 0.75, 1.6, 0.8, 1.1]

    apply_style()
    fig = plt.figure(figsize=(7.2, 3.45))
    ax = fig.add_axes([0.04, 0.34, 0.92, 0.33])
    ax.set_xlim(0, sum(widths) + 1.0)
    ax.set_ylim(0, 1.25)
    ax.axis("off")

    x = 0.1
    for idx, ((stage, detail, color), width) in enumerate(zip(stages, widths)):
        rect = FancyBboxPatch(
            (x, 0.28),
            width,
            0.42,
            boxstyle="round,pad=0.015,rounding_size=0.03",
            linewidth=1.0,
            edgecolor=MIST_STONE["dark"],
            facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x + width / 2, 0.56, stage, ha="center", va="center", fontsize=9)
        ax.text(
            x + width / 2,
            0.39,
            detail,
            ha="center",
            va="center",
            fontsize=8,
            color=MIST_STONE["dark"],
        )
        if idx < len(stages) - 1:
            ax.annotate(
                "",
                xy=(x + width + 0.18, 0.49),
                xytext=(x + width, 0.49),
                arrowprops=dict(
                    arrowstyle="-|>",
                    lw=1.0,
                    color=MIST_STONE["dark"],
                    shrinkA=0,
                    shrinkB=0,
                ),
            )
        x += width + 0.2

    fig.text(
        0.03,
        0.94,
        "PSMS-v2 staged protocol representation",
        fontsize=12,
        fontweight="bold",
        ha="left",
        va="top",
    )
    fig.text(
        0.03,
        0.85,
        "The gain comes from the richer staged PSMS package and feasibility-aware constrained search,\n"
        "not from any single added component or a tweak to the old three-stage family.",
        fontsize=8.5,
        color=MIST_STONE["dark"],
        ha="left",
        va="top",
    )
    note_ax = fig.add_axes([0.04, 0.06, 0.92, 0.17])
    note_ax.axis("off")
    box_specs = [
        (
            0.00,
            "Representation upgrade",
            [
                "- explicit entry, monitor, hold, and tail roles",
                "- richer staged geometry than the EVTBO family",
                "- same fixed four-metric contract",
            ],
            SAGE_CLAY["light"],
        ),
        (
            0.52,
            "Search discipline",
            [
                "- trust-region local search around feasible candidates",
                "- feasibility-aware ordering before expensive simulation",
                "- package-level claim, not single-module attribution",
            ],
            MIST_STONE["light"],
        ),
    ]
    for x0, box_title, lines, facecolor in box_specs:
        patch = FancyBboxPatch(
            (x0, 0.05),
            0.46,
            0.88,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            linewidth=0.9,
            edgecolor=MIST_STONE["mid"],
            facecolor=facecolor,
            transform=note_ax.transAxes,
        )
        note_ax.add_patch(patch)
        note_ax.text(
            x0 + 0.03,
            0.77,
            box_title,
            transform=note_ax.transAxes,
            fontsize=8.4,
            fontweight="bold",
            ha="left",
            va="center",
            color=MIST_STONE["dark"],
        )
        for idx, line in enumerate(lines):
            note_ax.text(
                x0 + 0.04,
                0.56 - idx * 0.22,
                line,
                transform=note_ax.transAxes,
                fontsize=7.4,
                ha="left",
                va="center",
                color=MIST_STONE["dark"],
            )
    return save_figure(fig, "figure2_protocol_representation")


def render_heldout_validation(heldout_rows: list[dict]) -> dict[str, str]:
    metrics = [
        ("robust_utility", "robust utility"),
        ("mean_score", "mean score"),
        ("worst_score", "worst score"),
        ("guard_pass_rate", "guard pass rate"),
    ]
    labels = [row["label"] for row in heldout_rows]
    x_positions = range(len(labels))

    apply_style()
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 3.0))
    fig.suptitle(
        "Held-out combined-stress validation on a distinct bundle",
        x=0.5,
        y=1.03,
        fontsize=11,
    )
    fig.text(
        0.5,
        0.90,
        "PSMS-v2 stays positive and feasible, EVTBO is neutral, and BO fails the held-out guard.",
        ha="center",
        va="center",
        fontsize=8,
        color=MIST_STONE["dark"],
    )
    fig.subplots_adjust(bottom=0.20, top=0.76, wspace=0.24)

    for ax, (metric_key, title) in zip(axes, metrics):
        values = [row["aggregate"][metric_key] for row in heldout_rows]
        colors = [row["color"] for row in heldout_rows]
        lower = min(values)
        upper = max(values)
        padding = max(0.02, (upper - lower) * 0.12)
        if lower < 0:
            ax.axhspan(lower - padding, 0.0, color=MIST_STONE["light"], alpha=0.14, zorder=0)
        ax.axhline(0.0, color=MIST_STONE["dark"], linewidth=1.15, linestyle="--", zorder=1)
        bars = ax.bar(list(x_positions), values, color=colors, width=0.58, zorder=2)
        for bar, row in zip(bars, heldout_rows):
            bar.set_edgecolor("white")
            bar.set_linewidth(1.0 if row["label"] == "PSMS-v2" else 0.6)
        ax.set_xticks(list(x_positions), labels)
        ax.set_title(title, fontsize=9)
        ax.grid(axis="y", alpha=0.18)
        ax.tick_params(axis="both", labelsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if metric_key == "guard_pass_rate":
            ax.set_ylim(0.0, 1.1)
        else:
            ax.set_ylim(lower - padding, upper + padding)
        for idx, value in enumerate(values):
            ax.text(
                idx,
                value + (0.02 if value >= 0 else -0.03),
                f"{value:+.3f}" if metric_key != "guard_pass_rate" else f"{value:.1f}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                fontsize=7,
                color=MIST_STONE["dark"],
            )
    return save_figure(fig, "figure3_heldout_validation")


def write_catalog(exports: dict[str, dict[str, str]]) -> None:
    catalog = {
        "schema_version": 1,
        "generated_by": str(Path(__file__).resolve()),
        "style_path": str(STYLE_PATH),
        "figures": [
            {
                "figure_id": "figure1_frontier_progression",
                "surface_class": "paper_main",
                "claim": "PSMS-v2 continues the verified frontier progression under the unchanged comparison contract.",
                "source_data_paths": [
                    str(EVIDENCE_LEDGER_PATH),
                    "baseline values from paper/draft.md nominal-results table",
                ],
                "export_paths": exports["figure1_frontier_progression"],
                "review_note": "Added endpoint emphasis and compact panel guidance so the unchanged comparison contract stays obvious even in a fast scan.",
            },
            {
                "figure_id": "figure2_protocol_representation",
                "surface_class": "paper_main",
                "claim": "PSMS-v2 is a package-level staged representation and constrained-search upgrade, not a single-component tweak.",
                "source_data_paths": [str(PAPER_ROOT / "draft.md")],
                "export_paths": exports["figure2_protocol_representation"],
                "review_note": "Added lower explanation boxes so the representation change and the search-discipline message survive down-scaling together.",
            },
            {
                "figure_id": "figure3_heldout_validation",
                "surface_class": "paper_main",
                "claim": "PSMS-v2 remains rank-1 and fully feasible on the held-out combined-stress bundle.",
                "source_data_paths": [str(HELDOUT_SUMMARY_PATH), str(EVIDENCE_LEDGER_PATH)],
                "export_paths": exports["figure3_heldout_validation"],
                "review_note": "Strengthened the zero line, negative-region separation, and PSMS-v2 emphasis so the held-out ranking reads cleanly at a glance.",
            },
        ],
    }
    (FIGURE_ROOT / "figure_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n")


def main() -> None:
    ensure_dirs()
    items = load_evidence_items()
    frontier_rows = load_frontier_table(items)
    heldout_rows = load_heldout_rows()

    exports = {
        "figure1_frontier_progression": render_frontier_progression(frontier_rows),
        "figure2_protocol_representation": render_protocol_representation(),
        "figure3_heldout_validation": render_heldout_validation(heldout_rows),
    }
    write_catalog(exports)
    print(json.dumps(exports, indent=2))


if __name__ == "__main__":
    main()

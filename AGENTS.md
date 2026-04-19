# Repository Guidelines

## Project Structure & Module Organization
This repository is organized as a small Python research release for battery fast-charge optimization.

- `methods/`: our three-stage method layout. `methods/stage_one.py`, `methods/stage_two.py`, and `methods/stage_three.py` are the executable search stages.
- `baselines/`: retained baseline wrappers plus the vendor baseline package under `baselines/vendor/ax_pybamm_fastcharge/`.
- `experiments/entrypoints/`: all runnable and inspection entry scripts.
- `experiments/runs/`: recorded outputs from published runs, especially `experiments/runs/stage_one/results/`, `experiments/runs/stage_two/results/`, and `experiments/runs/stage_three/results/`.
- `experiments/analysis/`: external validation and search-cost summaries.
- `paper/`: lightweight writing folder; keep only material needed for the public draft.

## Build, Test, and Development Commands
Set up the environment with:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
```

Use Python `3.12` for setup. The current dependency set is not reliable on Python `3.13`, mainly because `PyBaMM` may fail to install there.
If your default mirror cannot resolve `pybamm`, retry with:

```bash
python -m pip install --index-url https://pypi.org/simple -r requirements.txt
```

Key commands:

- `./run.sh stage-one --mode smoke`: quick check for the stage-one search.
- `./run.sh stage-two --mode smoke`: quick check for the stage-two search.
- `./run.sh smoke`: quick pipeline check for `stage_three`.
- `./run.sh search`: run the main stage-three search.
- `./run.sh validate`: run external combined-stress validation.
- `./run.sh show-stage-one`: inspect the public stage-one summary.
- `./run.sh show-stage-two`: inspect the public stage-two summary.
- `./run.sh show-pipeline`: print the three-stage method layout.
- `./run.sh baseline`: regenerate retained baseline outputs.

## Coding Style & Naming Conventions
Use Python with 4-space indentation, `snake_case` for functions, variables, files, and result prefixes, and small CLI-oriented modules. Prefer explicit `Path` handling and type hints for reusable helpers. Public-facing names should use the repository convention `stage_one`, `stage_two`, `stage_three`; keep legacy abbreviations only when required for old artifact compatibility.

## Testing Guidelines
There is no dedicated `tests/` package yet. Treat runnable workflows as the current validation standard:

- run `./run.sh smoke` before larger edits;
- rerun `./run.sh validate` when changing ranking, metrics, or scenario logic;
- inspect updated JSON/CSV outputs under `experiments/**/results/`.

If automated tests are added, place them in `tests/` and use names like `test_search_controller.py`.

## Commit & Pull Request Guidelines
History is minimal, so use short imperative commit subjects such as `Rename stage-three outputs`. Keep each commit scoped to one logical change. PRs should state which workflow changed, list commands run, and note any regenerated artifacts under `experiments/`.

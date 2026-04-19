#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON:-python}"
MODE="${1:-smoke}"

if [[ "${MODE}" == "-h" || "${MODE}" == "--help" || "${MODE}" == "help" ]]; then
  echo "Usage: ./run.sh [stage-one|stage-two|smoke|search|validate|combined-stress|heldout|baseline|show-stage-one|show-stage-two|show-pipeline] [extra args...]"
  exit 0
fi

PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
case "${PYTHON_VERSION}" in
  3.10|3.11|3.12)
    ;;
  *)
    echo "Warning: Python ${PYTHON_VERSION} is outside the recommended range." >&2
    echo "Use Python 3.10-3.12, preferably 3.12, for a clean setup." >&2
    "${PYTHON_BIN}" -c 'import pybamm' >/dev/null 2>&1 || {
      echo "PyBaMM is not importable with ${PYTHON_BIN}. Example: PYTHON=python3.12 ./run.sh ${MODE}" >&2
      exit 1
    }
    ;;
esac

if [[ $# -gt 0 ]]; then
  shift
fi

case "${MODE}" in
  stage-one)
    exec "${PYTHON_BIN}" experiments/entrypoints/run_stage_one.py "$@"
    ;;
  stage-two)
    exec "${PYTHON_BIN}" experiments/entrypoints/run_stage_two.py "$@"
    ;;
  smoke)
    exec "${PYTHON_BIN}" experiments/entrypoints/run_stage_three.py \
      --mode smoke \
      --enable-stage-mask \
      --output-prefix stage_three_smoke \
      --run-id stage-three-smoke-v1 \
      "$@"
    ;;
  search)
    exec "${PYTHON_BIN}" experiments/entrypoints/run_stage_three.py \
      --mode search \
      --enable-stage-mask \
      --output-prefix stage_three_main \
      --run-id stage-three-main-v1 \
      "$@"
    ;;
  validate|combined-stress|heldout)
    exec "${PYTHON_BIN}" experiments/analysis/external_validation/run_external_validation.py "$@"
    ;;
  show-stage-one)
    exec "${PYTHON_BIN}" experiments/entrypoints/show_stage_one.py "$@"
    ;;
  show-stage-two)
    exec "${PYTHON_BIN}" experiments/entrypoints/show_stage_two.py "$@"
    ;;
  show-pipeline)
    exec "${PYTHON_BIN}" experiments/entrypoints/show_pipeline.py "$@"
    ;;
  baseline)
    exec "${PYTHON_BIN}" experiments/entrypoints/run_baselines.py "$@"
    ;;
  *)
    echo "Usage: ./run.sh [stage-one|stage-two|smoke|search|validate|combined-stress|heldout|baseline|show-stage-one|show-stage-two|show-pipeline] [extra args...]" >&2
    exit 1
    ;;
esac

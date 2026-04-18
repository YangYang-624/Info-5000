#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

PYTHON_BIN="${PYTHON:-python}"
MODE="${1:-smoke}"

if [[ "${MODE}" == "-h" || "${MODE}" == "--help" || "${MODE}" == "help" ]]; then
  echo "Usage: ./run.sh [smoke|search|heldout|baseline|fair-search] [extra args...]"
  exit 0
fi

if [[ $# -gt 0 ]]; then
  shift
fi

case "${MODE}" in
  smoke)
    exec "${PYTHON_BIN}" experiments/main/ua_psms_v1/run_robust_protocol_search.py \
      --mode smoke \
      --enable-stage-mask \
      --output-prefix ua_psms_v2_smoke \
      --run-id run-psms-v2-smoke \
      "$@"
    ;;
  search)
    exec "${PYTHON_BIN}" experiments/main/ua_psms_v1/run_robust_protocol_search.py \
      --mode search \
      --enable-stage-mask \
      --output-prefix ua_psms_v2_search_main \
      --run-id run-psms-v2-main-v1 \
      "$@"
    ;;
  heldout)
    exec "${PYTHON_BIN}" experiments/analysis/heldout_combo_validation/run_heldout_combo_validation.py "$@"
    ;;
  baseline)
    exec "${PYTHON_BIN}" baselines/local/ax-pybamm-fastcharge/run_standard_baselines.py "$@"
    ;;
  fair-search)
    exec "${PYTHON_BIN}" experiments/fair_global_search/run_fair_global_search.py "$@"
    ;;
  *)
    echo "Usage: ./run.sh [smoke|search|heldout|baseline|fair-search] [extra args...]" >&2
    exit 1
    ;;
esac

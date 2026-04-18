# Baseline Verification

## Verdict

This baseline line is now trustworthy for the current gate.
The five standard protocols were rerun in the existing `lumo` environment with a GPU-capable PyTorch build whose CUDA path is actually usable.

## Source And Route

- baseline id: `ax-pybamm-fastcharge`
- variant id: `baseline_protocols_10to90`
- route: reproduce + repair
- source repo: `https://github.com/dww4/Optimize_Fast_Charge.git`
- source commit: `56c9185a72183a367ed2852ebb72fc85aedc8019`
- baseline root: `baselines/local/ax-pybamm-fastcharge`

## Environment Trust Check

- verified environment: `lumo`
- Python: `3.10.19`
- torch: `2.6.0+cu124`
- CUDA runtime reported by torch: `12.4`
- `torch.cuda.is_available()`: `true`
- device count: `8`
- device name: `NVIDIA GeForce RTX 4090`

`LLM_FE` is not accepted as the active baseline environment because its upgraded `torch 2.11.0+cu130` reports `cuda_available=false` under the current driver.

## What Was Verified

1. A single-protocol smoke test in `lumo` reproduced the saved `CCCV_2.0C` metrics exactly.
2. The full five-protocol `run_standard_baselines.py` run completed successfully.
3. All five protocols recorded `success=true`.
4. The rerun updated the canonical result files with the trusted environment metadata.

## Canonical Outputs

- JSON: `results/standard_baselines.json`
- CSV: `results/standard_baselines.csv`
- metric contract: `json/metric_contract.json`

## Trusted Metrics

| Protocol | Q30 | plating_loss | sei_growth | total_lli | success |
|---|---:|---:|---:|---:|---|
| CCCV_2.0C | 0.0716360692 | 0.4758850267 | 63.1308510089 | 0.0199687955 | true |
| LinearTaper_3.0C-1.0C | 0.0534644487 | 0.4117025163 | 54.2603967151 | 0.0172631298 | true |
| LinearTaper_3.0C-0.5C | 0.0684906920 | 0.4806101996 | 62.2076588006 | 0.0201127398 | true |
| BO_3step_aggressive | 0.0898950135 | 0.3221755156 | 58.3621677237 | 0.0140665152 | true |
| BO_3step_conservative | 0.0302083333 | 0.0014056407 | 59.7662805796 | 0.0021473261 | true |

## Comparison Guidance

- Preserve the full five-protocol surface as the accepted comparison contract.
- Use `Q30` as the headline scoreboard metric.
- Treat `plating_loss`, `sei_growth`, and `total_lli` as required secondary degradation metrics rather than optional extras.
- For throughput-focused comparison, the strongest current reference is `BO_3step_aggressive`.
- For degradation-minimizing comparison, the strongest current reference is `BO_3step_conservative`.

## Caveats

- PyBaMM emits expected `Maximum voltage [V]` infeasibility warnings for several protocols; these do not invalidate the run because each protocol still returned a completed metric record with `success=true`.
- The current baseline runner uses PyBaMM / Casadi for the simulation itself, so the main value of the GPU-capable torch environment at this stage is environment consistency for later optimization work rather than accelerated PyBaMM solves.
- `ax-platform`, `botorch`, and `gpytorch` were intentionally deferred in `lumo` because their heavier dependency chain was blocking the baseline gate without being required for the current five-protocol verification.

## Next Anchor

The baseline gate can now be confirmed on the full five-protocol comparison surface, with later optimization-stack installation handled after the gate is secured.

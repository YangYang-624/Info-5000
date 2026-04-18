# Environment Setup Note

## Verdict

The active experiment environment remains `lumo`, and it is still the correct runtime for the first physics-prior masked multi-stage event-trigger experiment.

## Why `lumo`

- `torch 2.6.0+cu124` is already working there with CUDA enabled.
- `ax-platform`, `botorch`, `gpytorch`, `scikit-learn`, and `pybamm` are already available.
- The accepted baseline package under `baselines/local/ax-pybamm-fastcharge` imports cleanly from the same environment.

## Current Mechanism Upgrade

- previous package: `ua_evtbo_v1` on the strongest measured event-trigger line
- current package: `ua_psms_v1` as the first physics-prior masked multi-stage scaffold
- incumbent anchor: `UA4_EVTBO_3.00C_rest10m_4.30C_v4p16`
- mechanism change:
  - keep the same robust guard-first scoring and four-metric comparison contract
  - keep the same dual-model controller that learns both `search_objective` and `guard_pass_rate`
  - preserve the same 30-minute budget split and the same `first_rate`, `rest_minutes`, `third_rate`, and `trigger_voltage` controls
  - add a masked hold stage controlled by `hold_rate` and `hold_minutes`
  - enforce physical ordering priors in the candidate representation before any later learned surrogate is trusted
  - keep a derived low-rate tail so the first scaffold does not explode the dimension count
  - preserve backward compatibility by routing the new protocol family through native PyBaMM step strings

## Canonical Commands

Smoke:

`/data/yangyang/miniconda/envs/lumo/bin/python experiments/main/ua_psms_v1/run_robust_protocol_search.py --mode smoke --anchor UA4_EVTBO_3.00C_rest10m_4.30C_v4p16 --scenario-set followup_v1 --smoke-budget 6 --output-prefix ua_psms_smoke --run-id run-psms-ua4-v1`

Bounded search:

`/data/yangyang/miniconda/envs/lumo/bin/python experiments/main/ua_psms_v1/run_robust_protocol_search.py --mode search --anchor UA4_EVTBO_3.00C_rest10m_4.30C_v4p16 --scenario-set followup_v1 --search-budget 12 --output-prefix ua_psms_search --run-id run-psms-ua4-v1`

## Output Contract

- summary JSON:
  - `experiments/main/ua_psms_v1/results/ua_psms_smoke_summary.json`
  - `experiments/main/ua_psms_v1/results/ua_psms_search_summary.json`
- ranked CSV:
  - `experiments/main/ua_psms_v1/results/ua_psms_smoke_ranked_candidates.csv`
  - `experiments/main/ua_psms_v1/results/ua_psms_search_ranked_candidates.csv`
- scenario CSV:
  - `experiments/main/ua_psms_v1/results/ua_psms_smoke_scenario_metrics.csv`
  - `experiments/main/ua_psms_v1/results/ua_psms_search_scenario_metrics.csv`

## Success Signals

- smoke proves the masked multi-stage controller can emit both hold-enabled and hold-disabled schedules around the EVTBO incumbent and still write complete scenario metrics under the accepted contract
- smoke summary includes the incumbent EVTBO anchor, the new `hold_rate` / `hold_minutes` fields, and the same feasibility-aware controller settings
- bounded search either finds a physically ordered multi-stage candidate that beats the EVTBO incumbent under the same ranking rule or shows honestly that the richer representation still needs the later surrogate gate

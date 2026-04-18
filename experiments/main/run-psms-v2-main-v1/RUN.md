# PSMS-v2 larger-budget robust search beyond the EVTBO anchor

- Run id: `run-psms-v2-main-v1`
- Branch: `run/run-psms-v2-main-v1`
- Parent branch: `idea/001-idea-8d0629d2`
- Worktree: `/data/yangyang/class/info5000/DeepScientist/quests/001/.ds/worktrees/idea-idea-8d0629d2`
- Idea: `idea-8d0629d2`
- Baseline: `ax-pybamm-fastcharge`
- Baseline variant: `bo_3step_aggressive`
- Dataset scope: `followup_v1 robust scenario bundle: nominal, warm_cell, hot_cell, plating_stress, sei_stress`
- Verdict: `good`
- Status: `completed`

## Hypothesis

Entry activation plus sequence-aware feasibility screening can turn the PSMS scaffold into a robustly superior protocol family without sacrificing guard feasibility.

## Setup

Use the accepted PyBaMM fast-charge baseline contract on the existing lumo environment. Search on the followup_v1 five-scenario bundle with the EVTBO incumbent UA4_EVTBO_3.00C_rest10m_4.30C_v4p16 as the anchor. PSMS-v2 adds a separate entry-rate dimension and a sequence-feasibility prior inside the trust-region acquisition.

## Execution

Ran the upgraded PSMS package in search mode with search_budget=12 on the unchanged followup_v1 contract. The controller converged at trust_region_floor after evaluating 11 adaptive candidates and kept the search centered around the new PSMS-v2 winner.

## Results

The main experiment promoted UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m as the robust top protocol. It kept success_rate=1.0 and guard_pass_rate=1.0 across the five followup_v1 scenarios while improving nominal Q30 to 0.09636 Ah versus 0.09522 Ah for the EVTBO anchor and 0.08990 Ah for the accepted baseline. Relative to the EVTBO anchor, the winner improved mean Q30 by +0.00358, plating_loss by +0.09569, sei_growth by +0.00111, and total_lli by +0.06517 on the accepted relative-delta surface, with worst-case deltas staying non-negative on the four canonical metrics.

## Conclusion

PSMS-v2 is the first expressive post-EVTBO mechanism on this quest to produce a larger-budget robust winner that still preserves guard feasibility. The new result justifies treating entry activation plus sequence-aware feasibility screening as a serious mechanism advance rather than a smoke-only curiosity.

## Metrics Summary

- `Q30` = 0.0964
- `plating_loss` = 0.3218
- `sei_growth` = 57.4898
- `total_lli` = 0.014

## Baseline Comparison

- `Q30`: run=0.0964 baseline=0.0899 delta=0.0065 (better)
- `plating_loss`: run=0.3218 baseline=0.3222 delta=-0.0003 (better)
- `sei_growth`: run=57.4898 baseline=58.3622 delta=-0.8724 (better)
- `total_lli`: run=0.014 baseline=0.0141 delta=-0 (better)

## Changed Files

- `experiments/main/ua_psms_v1/robust_protocol_search.py`
- `PLAN.md`
- `CHECKLIST.md`
- `memory/ideas/idea-8d0629d2/idea.md`
- `plan.md`
- `status.md`
- `SUMMARY.md`

## Evidence Paths

- `/data/yangyang/class/info5000/DeepScientist/quests/001/.ds/worktrees/idea-idea-8d0629d2/experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_summary.json`
- `/data/yangyang/class/info5000/DeepScientist/quests/001/.ds/worktrees/idea-idea-8d0629d2/experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_ranked_candidates.csv`
- `/data/yangyang/class/info5000/DeepScientist/quests/001/.ds/worktrees/idea-idea-8d0629d2/experiments/main/ua_psms_v1/results/ua_psms_v2_search_main_scenario_metrics.csv`

## Notes

- The search converged at trust_region_floor around the new winner, which is a stronger local optimum signal than the earlier smoke-only pass.
- Two top-ranked PSMS-v2 candidates tied on aggregate metrics except for hold_rate 3.35 vs 3.30, suggesting a small invariance surface around the final winner.

## Evaluation Summary

- Not recorded.

## Delivery Policy

- Research paper required: `True`
- Recommended next route: `analysis_or_write`
- Reason: Research paper mode is enabled. The run looks promising, so the next route should usually strengthen the evidence and move toward analysis or writing rather than stopping at the algorithm result alone.

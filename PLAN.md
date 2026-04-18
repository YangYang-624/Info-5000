## Goal

Build a fair from-scratch search benchmark where the baseline and our method both search the same 7D protocol space under the same budget, with a target budget of at least 100 for the real claim run.

## Constraints

- No incumbent warm start.
- Same search space for all compared methods.
- Same scenario bundle and metric contract for all compared methods.
- Same budget interface for all compared methods.
- First priority is to make the experiment runnable and verifiable.

## Implementation Route

- Add a new `experiments/fair_global_search/` entrypoint.
- Reuse the existing PyBaMM evaluation and protocol-construction code from `ua_psms_v1`.
- Implement from-scratch methods:
  - `random`
  - `global_bo`
  - `psms_global`
- Use the fixed `BO_3step_aggressive` baseline as the comparison surface, not as a warm start.
- Keep the full 7D staged space active.

## Verification Plan

- Run a tiny smoke benchmark first to verify imports, environment, outputs, and result files.
- If smoke passes, run a larger benchmark with the same entrypoint and a higher budget.
- Only treat the benchmark as claim-grade after equal-budget runs complete successfully.

## Risks

- PyBaMM runtime may make budget-100 runs expensive.
- The old cleaned project does not include a reusable notebook-free baseline search script, so the new fair runner must be self-contained.
- GP fitting may become unstable as budget increases; fallback is random search plus larger candidate pools.

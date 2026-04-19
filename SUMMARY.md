# Summary

The current public release packages a three-stage fast-charge search pipeline under one fixed PyBaMM evaluation contract.

The main public claim is simple:

- `stage_three` is the strongest verified protocol line in this snapshot.
- It improves nominal `Q30` from `0.08990 Ah` in `baseline` to `0.09636 Ah`.
- It remains rank-1 in the held-out combined-stress validation.
- It does this with lower public search cost than the retained GitHub direct-BO baselines.

The strongest part of the evidence is not just the final score. It is the whole chain:

- `stage_one` improves the baseline with a first four-step winner.
- `stage_two` improves that line with an event-triggered four-step winner.
- `stage_three` extends it into the final five-stage line.
- Each stage stops only after its local trust-region search converges to `trust_region_floor`, and only then is the winner promoted to the next stage.

The cost evidence is also part of the headline result:

- GitHub direct BO 3-step: `109` evals
- GitHub direct BO 5-step: `124` evals
- `stage_one`: `15` evals
- `stage_two`: `13` evals
- `stage_three`: `14` evals
- full promoted pipeline: `42` evals

So the public-facing conclusion is not “we searched longer and got lucky.” It is:

- under the same evaluation contract,
- with a stage-by-stage convergent search chain,
- and with lower public search cost,
- the repository reaches a better verified protocol than the retained baseline line.

The strongest supporting files are:

- `experiments/runs/stage_three/results/stage_three_main_summary.json`
- `experiments/analysis/external_validation/results/external_validation_summary.json`
- `experiments/analysis/search_cost/search_cost_comparison.md`

The main remaining limitation is unchanged:

- the result is strong at the package level,
- but component-level attribution is still not fully isolated into a single decisive module.

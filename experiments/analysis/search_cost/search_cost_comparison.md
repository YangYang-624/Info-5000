# Search Cost Comparison

| Method | Style | Space | Total evals | Adaptive evals | Nominal Q30 | Notes |
| --- | --- | --- | ---: | ---: | ---: | --- |
| GitHub Direct BO (3-Step) | direct_bo | 3-step | 109 | 105 | 0.08990 | 4 preexisting + 35 epochs x 3 trials from the original 3-step notebook. |
| GitHub Direct BO (5-Step) | direct_bo | 5-step | 124 | 120 | - | 4 preexisting + 40 epochs x 3 trials from the original 5-step notebook. |
| Stage One | hierarchical_stage | stage_one | 15 | 10 | 0.09494 | stop_reason=trust_region_floor |
| Stage Two | hierarchical_stage | stage_two | 13 | 8 | 0.09522 | stop_reason=trust_region_floor |
| Stage Three | hierarchical_stage | stage_three | 14 | 11 | 0.09636 | stop_reason=trust_region_floor |
| Full Three-Stage Pipeline | hierarchical_pipeline | stage_one->stage_two->stage_three | 42 | 29 | 0.09636 | End-to-end cost across the three promoted stages; final protocol quality taken from stage three. |

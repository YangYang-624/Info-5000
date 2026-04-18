# Framework Cost Table

| Method | Style | Space | Total evals | Adaptive evals | Nominal Q30 | Notes |
| --- | --- | --- | ---: | ---: | ---: | --- |
| GitHub-DirectBO-3step | direct_bo | 3-step | 109 | 105 | 0.08990 | 4 preexisting + 35 epochs x 3 trials from the original 3-step notebook. |
| GitHub-DirectBO-5step | direct_bo | 5-step | 124 | 120 | - | 4 preexisting + 40 epochs x 3 trials from the original 5-step notebook. |
| VTBO | hierarchical_stage | UA4 | 15 | 10 | 0.09494 | stop_reason=trust_region_floor |
| EVTBO | hierarchical_stage | UA4 | 13 | 8 | 0.09522 | stop_reason=trust_region_floor |
| PSMS-v2 | hierarchical_stage | UA5 | 16 | 11 | 0.09636 | stop_reason=trust_region_floor |
| Hierarchical-Pipeline-Total | hierarchical_pipeline | VTBO->EVTBO->PSMS | 44 | 29 | 0.09636 | End-to-end cost across the three promoted stages; final protocol quality taken from PSMS-v2. |

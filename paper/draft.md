# A Clear Five-Stage Search Framework for Fast-Charge Protocol Design Under Thermal Stress

## Abstract

We study battery fast-charge protocol optimization under thermal and degradation stress using a PyBaMM-based simulation benchmark and a trusted baseline family. Starting from the accepted three-step BO baseline and the later four-step trigger-search incumbent, we introduce a final five-stage search framework that expands the staged protocol family while keeping the same four-metric evaluation contract. The promoted `stage_three` protocol improves nominal `Q30` from `0.08990 Ah` to `0.09636 Ah` over the baseline and from `0.09522 Ah` to `0.09636 Ah` over the `stage_two` anchor, while keeping plating loss flat and further reducing `sei_growth` and `total_lli`. A combined-stress external validation keeps the final five-stage winner rank-1 with `guard_pass_rate=1.0`, `robust_utility=0.0706`, and `worst_score=0.0032`. Matched ablations do not isolate one decisive component, so the supported claim is a package-level improvement in protocol representation and constrained search, not a claim of global optimality or a single-module breakthrough.

## Reader-Facing Summary

1. This project is not learning an online controller. It is searching for a better fixed fast-charge recipe inside a constrained, human-readable protocol family.
2. The method frontier progresses from the baseline, to `stage_one`, to `stage_two`, and finally to `stage_three`.
3. The final five-stage method is the first line in that progression that clearly beats the direct four-step trigger-search anchor while remaining fully feasible.
4. The evidence stack has four layers: nominal comparison, five-scenario robust bundle, combined-stress external validation, and matched ablations.
5. The right claim is local and disciplined: under the current GitHub/PyBaMM contract, the final five-stage framework is the strongest verified line so far.

For readability, this draft uses the public names `baseline`, `stage_one`, `stage_two`, and `stage_three`. Historical internal names are intentionally omitted from the main text.

## 1. Introduction

Battery fast-charge design in this project is treated as an offline protocol-search problem. We do not learn a controller that watches battery state and continuously adjusts current during charging. Instead, we define a constrained family of staged charging recipes, instantiate one candidate recipe at a time, evaluate it under a fixed PyBaMM contract, and search for a better protocol within that fixed comparison surface.

That boundary is scientifically important. In this line of work, it is easy to overclaim progress by silently changing the protocol family, relaxing feasibility checks, or comparing under a different metric surface. We therefore keep one trusted contract fixed across the main results: the same PyBaMM task, the same four paper-facing metrics (`Q30`, `plating_loss`, `sei_growth`, `total_lli`), and the same robust follow-up bundle. Under that setup, a better result is interpretable as a genuine protocol-search improvement rather than a moving-target benchmark change.

Within that fixed contract, the search frontier advanced in a clean sequence. The accepted three-step baseline provides the starting point. `stage_one` extends the old family with a tapered tail segment. `stage_two` pushes further by adding event-triggered structure. By the time `stage_two` became the incumbent, the remaining room inside that family was already shrinking. The next useful question was therefore not whether one more acquisition tweak would squeeze out a tiny gain, but whether a richer staged protocol family could open a better feasible region without changing the evaluation rules.

Our answer is yes, but only at the right claim boundary. The final five-stage search framework improves the frontier under the unchanged contract and remains rank-1 on a combined-stress external validation. At the same time, matched ablations show that the gain should not be written as the victory of one isolated module. The right interpretation is package-level: a richer staged protocol representation plus feasibility-aware search yields a better verified protocol under the current benchmark.

The paper makes three contributions.

1. It identifies a credible route past four-step trigger-search saturation: enlarge the staged protocol family while keeping the accepted evaluation contract fixed.
2. It packages that route as a final five-stage search framework, combining richer staged protocol geometry with feasibility-aware local search.
3. It closes the trust loop with matched evidence: nominal gains over both the three-step baseline and the four-step trigger-search anchor, combined-stress rank-1 retention, and ablations that limit the claim to the correct package-level scope.

### 1.1 Related Work And Positioning

Recent battery fast-charge papers near this problem fall into two nearby but distinct groups. One group learns online charging policies directly from battery environments. Those papers target adaptive control. The present work does not. It studies a narrower offline search problem: pick one staged protocol family, keep the evaluation contract fixed, and promote only candidates that remain defensible under the robust and external validation checks.

Battery-specific Bayesian optimization is more closely related. Prior work has shown that sequence-aware surrogates and structured BO can improve fast-charge protocol search. Our contribution is narrower and more auditable. We do not claim a new generic BO theorem. We claim that, under one fixed battery protocol contract, a richer staged representation plus feasibility-aware local search yields a stronger verified protocol than the current four-step trigger-search anchor.

## 2. Problem Setup And Fixed Comparison Contract

The experimental substrate is the accepted PyBaMM fast-charge benchmark already used across the baseline and follow-up lines. The active accepted comparator remains the three-step BO baseline. All main experiments preserve the same nominal evaluation surface and the same robust follow-up bundle. This is what lets us compare the baseline, `stage_one`, `stage_two`, and `stage_three` as one coherent frontier.

The search-time robust bundle is `followup_v1`, a five-scenario package used consistently in the later frontier-search runs. It evaluates each promoted candidate under:

- `nominal`
- `warm_cell`
- `hot_cell`
- `plating_stress`
- `sei_stress`

The paper then adds one out-of-bundle validation step, `combined_stress_v1`, to test whether the promoted protocol remains strong when the stress conditions change in a controlled way.

The evidence stack therefore has four layers.

1. A nominal four-metric comparison on a fixed paper-facing surface.
2. A five-scenario robust bundle used during the later search lines.
3. A combined-stress external validation outside the search bundle.
4. A matched ablation suite that tests how narrow or broad the final method claim should be.

The paper-facing comparison surface is deliberately small and explicit. `Q30` is the headline metric, but it is never allowed to stand alone. `plating_loss`, `sei_growth`, and `total_lli` remain co-equal safeguards against trading away battery health for superficial charge-throughput gains. On the robust side, `success_rate` and `guard_pass_rate` remain hard feasibility signals.

The budget definition also needs to stay explicit. In this paper, the main cost unit is candidate-level simulator evaluations: once a proposed protocol actually enters the PyBaMM evaluation path, it counts, even if it later fails the guard or turns out infeasible. Under that definition, the promoted hierarchical pipeline uses 42 candidate-level evaluations end to end across the four-step tail-search, four-step trigger-search, and final five-stage lines, compared with 109 and 124 evaluations in the original GitHub direct-BO notebooks for the 3-step and 5-step settings. This is a pipeline-cost claim, not a claim about the entire historical research effort behind the repository.

## 3. Final Five-Stage Search Method

### 3.1 From Four-Step Trigger Search To Five-Stage Search

The final five-stage method keeps the local trust-region search logic used in the later frontier lines, but changes what the optimizer is allowed to express and how risky candidates are screened before simulation. The main move is not simply "more budget." The main move is to upgrade the protocol family from the older four-step trigger-search representation to a richer staged charging geometry.

The active five-stage search surface is a seven-dimensional staged protocol space over:

- `first_rate`
- `rest_minutes`
- `third_rate`
- `entry_rate`
- `trigger_voltage`
- `hold_rate`
- `hold_minutes`

Each variable is discretized to a fixed engineering step size. The resulting candidates are still human-readable charge recipes rather than opaque continuous controls.

This richer geometry matters because the old family was already nearing saturation. The four-step trigger-search line still improved on the four-step tail-search line, but only by stretching the same family more carefully. The five-stage framework changes the protocol family itself while keeping the benchmark contract intact, which makes the gain easier to interpret scientifically.

### 3.2 What The Final Protocol Looks Like

The promoted `stage_three` protocol can be read as a deliberately staged charge schedule:

1. Charge at `3.00C`.
2. Rest for `10` minutes.
3. Enter with a more aggressive `4.50C` segment.
4. Continue with a monitored `4.30C` segment until `4.18V`.
5. Hold at `3.35C` for `1.5` minutes.
6. Finish with a tapered tail.

This is the core method story in plain language: the new framework can express a more detailed late-stage charging shape, and the search loop is designed to favor candidates that remain feasible under the robust contract.

### 3.3 Package Ingredients And Claim Boundary

The final five-stage framework should be described as a package, not as one magic trick. Its ingredients include:

- a richer staged protocol representation with entry, monitor, hold, and tail roles,
- feasibility-aware candidate ordering before expensive simulation,
- physics-prior structure and sequence guidance to bias the search toward plausible recipes.

The crucial writing boundary is that current evidence does not isolate any one of those ingredients as the sole driver of the gain. The matched ablations do not show collapse when one ingredient is removed in isolation. That does not mean the ingredients are irrelevant. It means the supported claim is about the joint package.

## 4. Main Results

The main result is compact: the frontier progresses from the three-step BO baseline, to four-step tail search, to four-step trigger search, to the final five-stage search. The final five-stage line is the first in that sequence that clearly beats the direct four-step trigger-search anchor while remaining fully feasible.

Table 1 keeps the nominal comparison surface explicit.

| Method | Q30 (Ah) | plating_loss | sei_growth | total_lli |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | 0.08990 | 0.32218 | 58.36217 | 0.01406652 |
| `stage_one` | 0.09494 | 0.32184 | 57.54798 | 0.01402536 |
| `stage_two` | 0.09522 | 0.32184 | 57.53493 | 0.01402490 |
| `stage_three` | 0.09636 | 0.32184 | 57.48976 | 0.01402332 |

The nominal gain is small but clean. Relative to the accepted three-step baseline, `Q30` improves by `+7.19%`. Relative to the direct four-step trigger-search anchor, `Q30` improves by `+1.20%`. At the same time, plating loss stays flat and the two degradation metrics continue to improve slightly.

Relative to the four-step trigger-search anchor, the promoted five-stage protocol keeps `success_rate=1.0` and `guard_pass_rate=1.0` across the full `followup_v1` bundle. This matters because the result is not just a nominal single-scenario accident. The promoted protocol remains top-ranked under the same robust comparison rule used in the later frontier lines.

The cost story is also favorable at the correct scope. Counting every candidate that truly entered simulation, including infeasible and guard-failed ones, the promoted pipeline remains cheaper than the original GitHub direct-BO baseline while producing a stronger final protocol. This should be written as a pipeline-cost claim, not as a claim about all historical development cost.

## 5. Held-out Combined-Stress Validation

The external combined-stress bundle is the main safeguard against over-reading the search-time result. `combined_stress_v1` re-evaluates the final five-stage winner, the direct four-step trigger-search predecessor, and the accepted baseline on a controlled out-of-bundle stress package.

The result is favorable and easy to communicate.

| Protocol | robust_utility | mean_score | worst_score | guard_pass_rate |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | -0.6077 | -0.5082 | -0.7065 | 0.0 |
| `stage_two` | 0.0000 | 0.0000 | 0.0000 | 1.0 |
| `stage_three` | 0.0706 | 0.0877 | 0.0032 | 1.0 |

The interpretation is straightforward. The final five-stage protocol stays rank-1 under both robust and nominal ordering, remains fully feasible, and keeps all three aggregate quality indicators positive. The four-step trigger-search anchor remains feasible but neutral. The accepted baseline collapses under the same held-out comparison.

This external-validation result upgrades the paper from "better on the search bundle" to "still best on a nearby but distinct stress package." That is still a local claim, and the bundle is still small, but it is strong enough to be part of the main story rather than a fragile appendix note.

## 6. Ablations And Claim Boundary

The matched ablations are best used as claim-boundary evidence rather than as a mechanism-discovery centerpiece.

| Ablation | Best observed outcome | Paper implication |
| --- | --- | --- |
| No sequence prior | Recovers the final five-stage winner family with full feasibility and `robust_utility=0.0238` | Sequence guidance is not a standalone explanation for the gain |
| No entry activation | A no-entry five-stage candidate ties the four-step trigger-search anchor across the comparison surface | Entry activation is not a standalone explanation for the gain |

The important interpretation is not that the added ingredients do nothing. The important interpretation is that current evidence does not isolate any one of them as the sole scientifically defensible explanation. The supported statement is therefore narrower: the final five-stage framework, as a package of richer staged representation plus feasibility-aware search, improves the local robust-search frontier under the fixed contract.

## 7. Reproducibility And External Sharing

This project is now organized so that a technical reader can understand it in three layers.

1. Read the top-level `README.md` and `RESULTS.md` for a plain-language explanation of the task, variables, metrics, and main claims.
2. Read this draft for the paper-style narrative of the fixed contract, the method progression, the nominal gain, the external-validation result, and the claim boundary.
3. Read the result artifacts and cost table if you want to verify each headline statement against durable outputs.

The key point is that the main evidence gap is now closed. What remains is mostly presentation work: wording, venue-specific layout, figure polish, and any final narrative tightening.

## 8. Conclusion

The final five-stage search framework is the strongest verified line in this project so far. Under the accepted four-metric contract it improves the nominal frontier beyond both the three-step BO baseline and the direct four-step trigger-search anchor, and under the combined-stress external bundle it remains rank-1 and fully feasible. The right conclusion is not that every fast-charge task is now solved. The right conclusion is narrower and stronger: under the current GitHub/PyBaMM contract, a richer five-stage protocol family plus feasibility-aware search yields a better verified protocol than the previous frontier lines.

## References

- [R1] Saehong Park, Andrea Pozzi, Michael Whitmeyer, Hector Perez, Won Tae Joe, Davide M. Raimondo, and Scott Moura. *Reinforcement Learning-based Fast Charging Control Strategy for Li-ion Batteries*. arXiv:2002.02060, 2020.
- [R2] Benben Jiang, Yixing Wang, Zhenghua Ma, and Qiugang Lu. *Fast Charging of Lithium-Ion Batteries Using Deep Bayesian Optimization with Recurrent Neural Network*. arXiv:2304.04195, 2023.
- [R3] Myisha A. Chowdhury, Saif S. S. Al-Wahaibi, and Qiugang Lu. *Adaptive Safe Reinforcement Learning-Enabled Optimization of Battery Fast-Charging Protocols*. arXiv:2406.12309, 2024.
- [R4] Meng Yuan and Changfu Zou. *Lifelong Reinforcement Learning for Health-Aware Fast Charging of Lithium-Ion Batteries*. arXiv:2505.11061, 2025.
- [R5] J. Wang, C. G. Petra, and J. L. Peterson. *Constrained Bayesian Optimization with Merit Functions*. arXiv:2403.13140, 2024.
- [R6] Paolo Ascia, Elena Raponi, Thomas Bäck, and Fabian Duddeck. *Feasibility-Driven Trust Region Bayesian Optimization*. arXiv:2506.14619, 2025.

# Physics-Prior Masked Multi-Stage Search for Fast-Charge Protocol Design Under Thermal Stress

## Abstract

We study battery fast-charge protocol optimization under thermal and degradation stress using a PyBaMM-based simulation benchmark and a trusted five-protocol baseline family. Starting from the accepted `BO_3step_aggressive` comparator and the later EVTBO incumbent, we introduce PSMS-v2, a physics-prior masked multi-stage search package that expands the staged protocol family and uses feasibility-aware local search under the same four-metric contract. The final protocol, `UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m`, improves nominal Q30 from `0.08990 Ah` to `0.09636 Ah` over `BO_3step_aggressive` and from `0.09522 Ah` to `0.09636 Ah` over EVTBO while keeping plating loss unchanged and further reducing SEI growth and total LLI. A held-out combined-stress validation outside the search bundle keeps the PSMS-v2 winner rank-1 under both robust and nominal ordering with `guard_pass_rate=1.0`, `robust_utility=0.0706`, and `worst_score=0.0032`. Formal matched ablations of the sequence prior and entry activation each fail to isolate a single decisive driver, so the supported claim is a package-level upgrade in protocol representation and constrained search rather than a statement about one uniquely critical module or global optimality.

## Reader-Facing Summary

1. The frontier improved steadily from `BO_3step_aggressive` to VTBO to EVTBO, but those gains were already compressing inside the old fixed-family search space.
2. PSMS-v2 expands the protocol family itself while preserving the same trusted four-metric contract and the same robust ranking bundle.
3. The final PSMS-v2 winner is better than both the accepted baseline and the direct EVTBO anchor without giving up feasibility.
4. The paper now relies on four evaluation layers: the fixed four-metric main comparison, the `followup_v1` five-scenario robust bundle, the `heldout_combo_v1` out-of-bundle validation, and a matched ablation suite.
5. A later focused warm-start validation rejected nominal-only challengers, so PSMS-v2 remains the verified incumbent rather than just the flashiest point.
6. The supported claim is therefore "stable superiority under the current GitHub/PyBaMM contract," not "already best on every possible fast-charge task."

## 1. Introduction

Battery fast-charge design in this quest is not treated as an unconstrained controller-learning problem. The scientific value comes from keeping the comparison surface fixed while the search method changes. All main comparisons therefore stay inside one trusted PyBaMM baseline family and one accepted metric contract: `Q30`, `plating_loss`, `sei_growth`, and `total_lli`. That decision matters because it turns each method change into a comparable statement about protocol quality rather than a moving-target optimization result.

Within that contract, the search frontier advanced in several clean steps. `BO_3step_aggressive` provides the accepted comparator. VTBO then pushed the old family forward by exposing a tapered tail segment, and EVTBO extended that idea further with an event-triggered representation. By the time EVTBO became the incumbent, however, the remaining room inside the old family was visibly shrinking. The next defensible question was no longer whether a slightly smarter acquisition rule could squeeze out one more narrow local gain. The real question was whether a richer staged protocol family could open a better part of the search space while preserving the exact same evaluation rules.

Just as importantly, the present task is an offline protocol-search problem rather than an online feedback-control problem. The method does not learn a controller that adapts current continuously from live battery state. Instead, every candidate is a fixed staged charging recipe sampled from a constrained family, then evaluated under the same PyBaMM contract. That boundary keeps the scientific claim narrow and auditable: PSMS-v2 is a better verified protocol-search package under the current benchmark, not a universal real-time charging controller.

That distinction is important because robust battery-charge search is easy to overclaim. A method can look stronger simply because it changes the candidate family, relaxes feasibility handling, or drifts to a friendlier metric surface. The current paper therefore asks a narrower and more auditable question: after EVTBO already stretched the old family close to saturation, does a richer staged protocol representation yield a measurable gain that survives both held-out validation and matched attribution checks?

Our answer is yes, but only at the right claim boundary. PSMS-v2 improves the frontier under the unchanged contract and stays rank-1 on a held-out combined-stress bundle. At the same time, three matched ablations show that the gain cannot honestly be assigned to any one newly added ingredient in isolation. The correct story is therefore not "we found the one crucial module." The correct story is "a richer staged protocol family plus feasibility-aware constrained search produces a better local frontier point under a fixed and trusted comparison contract."

The paper makes three concrete contributions.

1. It identifies a defensible route past EVTBO saturation: expand the staged protocol family while holding the accepted comparison contract fixed.
2. It packages that route as PSMS-v2, a coupled representation-and-search upgrade that combines richer staged protocol geometry, physics-prior masking, and feasibility-aware local search without claiming any one ingredient as the sole driver.
3. It closes the trust loop with matched evidence: nominal gains over both `BO_3step_aggressive` and EVTBO, held-out combined-stress rank-1 retention, and ablations that sharpen the claim boundary instead of inflating it.

### 1.1 Related Work And Positioning

Recent fast-charge papers closest to this problem split into two nearby but distinct routes. One route learns online charging policies directly from electrochemical environments. Park et al. [R1] framed fast charging as a model-free actor-critic control problem, Chowdhury et al. [R3] added safe RL with Gaussian-process-based safety projection, and Yuan and Zou [R4] pushed that line toward lifelong health-aware charging with SoH-dependent voltage constraints in PyBaMM. Those papers target adaptive current control policies. The present paper studies a narrower offline protocol-search problem: choose one fixed staged protocol family, keep the evaluation contract fixed, and promote only protocols that remain defensible under held-out bundle checks.

Battery-specific Bayesian optimization is closer in spirit to PSMS-v2. Jiang et al. [R2] use deep Bayesian optimization with a Bayesian recurrent neural network surrogate to search sequential fast-charging protocols in PETLION, arguing that sequence-aware surrogates can outperform Gaussian-process and non-recurrent baselines on lifetime-oriented objectives. PSMS-v2 differs in two ways that matter for claim strength. First, it stays inside one trusted PyBaMM baseline family and one fixed four-metric contract, so each frontier step remains directly comparable to the accepted `BO_3step_aggressive` baseline and the later EVTBO anchor. Second, the paper does not stop at nominal search-time gains; it narrows the method claim with a held-out combined-stress bundle and matched ablations.

At the optimizer-design level, PSMS-v2 also touches the broader constrained-BO literature. Wang et al. [R5] show that merit-function acquisition rules can improve constrained BO when feasible progress and objective progress must be balanced explicitly, while Ascia et al. [R6] emphasize feasibility-driven trust-region adaptation when feasible regions are sparse and hard to locate. The present paper does not claim a new generic constrained-BO theorem over those methods. Its contribution is more local and application-grounded: under a fixed battery protocol contract, a richer staged representation plus feasibility-aware local search yields a stronger verified protocol than the current EVTBO anchor.

## 2. Problem Setup And Fixed Comparison Contract

The experimental substrate is the accepted PyBaMM fast-charge benchmark already used across the baseline and follow-up lines. The active comparator remains `BO_3step_aggressive`, and all main experiments preserve the same nominal evaluation surface and the same robust follow-up bundle. This fixed contract is what allows the paper to compare BO, VTBO, EVTBO, and PSMS-v2 as one coherent frontier rather than four loosely related optimization exercises.

The search-time robust bundle is `followup_v1`, a five-scenario evaluation package used consistently across the later frontier-search runs. The paper then adds one out-of-bundle validation step, `heldout_combo_v1`, to test whether the promoted protocol remains strong when the stress conditions change in a controlled way. That two-level structure is intentional: the main run shows the method can discover a stronger point under the search contract, and the held-out bundle tests whether that point still deserves trust once it leaves the exact search-time setting.

In practical terms, the evidence stack has four layers. First, the nominal four-metric main comparison keeps `BO_3step_aggressive`, VTBO, EVTBO, and PSMS-v2 on one fixed surface. Second, the `followup_v1` five-scenario bundle checks whether the promoted point remains feasible under nearby search-time stress conditions. Third, `heldout_combo_v1` moves the winner onto a distinct out-of-bundle combined-stress package. Fourth, the matched ablation suite tests whether the final story should stay package-level rather than collapse onto one module. This is enough to justify a verified incumbent under the current GitHub/PyBaMM contract, but it is not enough to claim superiority on every possible task, cell condition, or external benchmark.

We keep the paper-facing comparison surface deliberately small and explicit. The headline nominal metric is `Q30`, but the claim is never allowed to ride on `Q30` alone. `plating_loss`, `sei_growth`, and `total_lli` stay in the contract as co-equal safeguards against trading away degradation behavior for superficial charge-throughput gains. On the robust side, `success_rate` and `guard_pass_rate` remain hard feasibility signals rather than soft preferences.

The method comparison also needs one explicit cost definition. Throughout this paper, the primary budget unit is candidate-level simulator evaluations: once a proposed protocol is actually run through the PyBaMM evaluation path, it counts, even if it later fails the guard or becomes infeasible. Under that cost definition, the promoted hierarchical pipeline uses 44 candidate-level evaluations end to end across VTBO, EVTBO, and PSMS-v2, compared with 109 and 124 evaluations in the original GitHub direct-BO notebooks for the 3-step and 5-step settings. That statement is deliberately narrower than a total historical research-cost claim. It compares the promoted end-to-end pipeline, not every exploratory smoke run, ablation, or discarded line created during method development.

## 3. PSMS-v2 Method

### 3.1 From EVTBO To PSMS-v2

PSMS-v2 keeps the local trust-region search logic introduced in the earlier frontier lines, but it changes what the optimizer is allowed to search over and how risky candidates are ranked before simulation. The key move is not "more budget" by itself. The key move is to upgrade the protocol family from the EVTBO representation to a richer staged charging geometry that can express a sharper entry segment, an explicit monitoring segment, an optional hold structure, and a distinct final tail.

Concretely, the active PSMS-v2 search surface is a seven-dimensional staged protocol space over `first_rate`, `rest_minutes`, `third_rate`, `entry_rate`, `trigger_voltage`, `hold_rate`, and `hold_minutes`, each discretized to a fixed engineering step size. The resulting candidates are still human-readable charging recipes rather than opaque continuous controls. That representation upgrade is central to the method story because it increases what the search can express without changing the benchmark contract used to judge the result.

This richer geometry matters because the old fixed-family search space had started to saturate. EVTBO still improved on VTBO, but only by stretching the same underlying family more carefully. PSMS-v2 changes that geometry while keeping the comparison contract intact, which makes any resulting gain much easier to interpret scientifically: if the new line wins, it wins because the protocol family and search package found a better feasible region, not because the paper quietly changed the benchmark.

### 3.2 Package Ingredients And Claim Boundary

PSMS-v2 should be described as a package with several coupled ingredients. The protocol representation adds explicit stage roles such as entry, monitor, hold, and tail. The search loop keeps a feasibility-aware ordering so candidates likely to violate hard constraints are down-weighted before expensive simulation. Physics-prior structure and sequence guidance remain part of that package because they help shape which staged candidates are considered plausible early in the search.

The crucial writing boundary is that none of those pieces should be sold as individually proven to be the sole driver of the final gain. The matched ablation campaign now shows that removing the sequence prior or removing entry activation does not by itself collapse the line. This does not mean those ingredients are useless. It means the present evidence supports the joint PSMS package, not a single-component causal story.

### 3.3 Protocol Interpretation

The final promoted protocol, `UA5_PSMS_3.00C_rest10m_4.30C_e4.50_v4p18_h3.35_1p5m`, is best read as a deliberately staged charge schedule rather than a flat rate tweak. It starts with a fixed `3.00C` charge and a rest window, then moves into an aggressive entry stage at `4.50C`, transitions through a monitored `4.30C` segment capped near `4.18V`, retains a short `3.35C` hold, and finishes with a tapered tail. In paper terms, that staged structure is the method story: PSMS-v2 reaches a stronger local frontier point by combining richer protocol geometry with feasibility-aware search under the same contract.

**Figure 2.** PSMS-v2 replaces the older fixed-family representation with a staged protocol package that can express entry, monitor, hold, and tail roles while keeping the same evaluation contract. The figure should be read as a representation-and-search argument, not as proof that any one added stage is solely responsible for the gain. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).

## 4. Main Results

The core main-text result is compact: `BO -> VTBO -> EVTBO -> PSMS-v2` is a clean frontier progression under one unchanged paper-facing contract, and PSMS-v2 is the first method in that sequence that clearly beats EVTBO while staying fully feasible. This matters because it turns the method story from a speculative representation idea into a measured and comparable frontier improvement.

Table 1 keeps the nominal comparison surface explicit. The progression is not dramatic because every step preserves the same evaluation contract, but that is exactly why the result is trustworthy. PSMS-v2 improves `Q30` from `0.08990` to `0.09636` over the accepted baseline, which is a `+7.19%` gain, and from `0.09522` to `0.09636` over EVTBO, which is a `+1.20%` gain. At the same time, plating loss stays flat and the two degradation metrics continue to improve slightly.

| Method | Q30 (Ah) | plating_loss | sei_growth | total_lli |
| --- | ---: | ---: | ---: | ---: |
| `BO_3step_aggressive` | 0.08990 | 0.32218 | 58.36217 | 0.01406652 |
| `UA4_VTBO` | 0.09494 | 0.32184 | 57.54798 | 0.01402536 |
| `UA4_EVTBO` | 0.09522 | 0.32184 | 57.53493 | 0.01402490 |
| `UA5_PSMS` | 0.09636 | 0.32184 | 57.48976 | 0.01402332 |

Relative to the EVTBO anchor, the promoted PSMS-v2 protocol keeps `success_rate=1.0` and `guard_pass_rate=1.0` on the full `followup_v1` bundle. On the accepted relative-delta surface, mean `Q30` improves by `+0.0035845855`, mean `plating_loss` by `+0.0956946380`, mean `sei_growth` by `+0.0011106155`, and mean `total_lli` by `+0.0651684164`. Those values matter because they show that the gain is not a nominal-only accident on one easy scenario. The promoted protocol remains top-ranked under the same robust comparison rule that governed the earlier frontier lines.

The cost story is similarly local but favorable. Counting every real candidate-level evaluation that entered the simulator, including infeasible or guard-failed candidates, the promoted pipeline remains cheaper than the original GitHub direct-BO baseline while producing a stronger final protocol. This is the right budget comparison for the current paper because it matches how the actual search contract is consumed in practice. It should not be rewritten into a stronger claim about the total historical research effort behind the whole project.

**Figure 1.** The four-panel frontier plot shows that PSMS-v2 is the strongest verified point on the accepted nominal comparison surface while preserving the same paper-facing contract used for BO, VTBO, and EVTBO. The plot is intentionally minimal: it emphasizes continuity of the comparison surface, highlights the final PSMS-v2 endpoint, and avoids implying any hidden reweighting of the metrics. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).

## 5. Held-out Combined-Stress Validation

The held-out bundle is the main safeguard against over-reading the search-time result. `heldout_combo_v1` re-evaluates the final PSMS-v2 winner, the direct EVTBO predecessor, and the accepted baseline on a controlled out-of-bundle stress package. This step matters because a better search-time point is only scientifically useful if it remains good after leaving the exact bundle that produced it.

The result is favorable and easy to communicate. PSMS-v2 stays rank-1 under both robust and nominal ordering, remains fully feasible with `guard_pass_rate=1.0`, and keeps all three aggregate quality indicators positive. EVTBO remains feasible but sits exactly on the neutral surface in the held-out aggregates, while the accepted baseline collapses under the same held-out comparison with `guard_pass_rate=0.0` and strongly negative robust utility.

| Protocol | robust_utility | mean_score | worst_score | guard_pass_rate |
| --- | ---: | ---: | ---: | ---: |
| `BO_3step_aggressive` | -0.6077 | -0.5082 | -0.7065 | 0.0 |
| `UA4_EVTBO` | 0.0000 | 0.0000 | 0.0000 | 1.0 |
| `UA5_PSMS` | 0.0706 | 0.0877 | 0.0032 | 1.0 |

This held-out result upgrades the paper from "the search found a better point under its own bundle" to "the promoted protocol remains best on a nearby but distinct stress package." That is still a local claim. The held-out bundle is small, and the paper should say so clearly. But it is strong enough to move the result into the main text instead of leaving it as a fragile appendix-only note.

A later focused stability check pushed on that same boundary from the opposite direction. Two warm-start challengers looked stronger on nominal deltas, but both failed the robust gate in `hot_cell`, `plating_stress`, and `sei_stress` with `guard_pass_rate=0.4`. That negative result matters because it shows the paper is not just reporting the largest nominal number; it is keeping PSMS-v2 as the verified incumbent because the candidate must stay feasible across the accepted stress bundle.

**Figure 3.** The held-out validation plot compares BO, EVTBO, and PSMS-v2 on four aggregate held-out metrics. The paper-facing interpretation is simple: PSMS-v2 remains feasible and positive on all three signed aggregates, EVTBO is feasible but neutral, and the accepted baseline fails the held-out feasibility gate. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).

## 6. Ablations And Claim Boundary

The three matched ablations are now best used as claim-boundary evidence rather than as a mechanism-discovery centerpiece. Each ablation asks a narrow question: if one package ingredient is removed while the comparison contract stays fixed, does the line collapse? The answer is consistently no, but in three different ways that matter for the final interpretation.

| Ablation | Best observed outcome | Paper implication |
| --- | --- | --- |
| No sequence prior | Recovers the PSMS winner family with full feasibility and `robust_utility=0.0238` | Sequence guidance is not a standalone explanation for the gain |
| No entry activation | A no-entry PSMS candidate ties EVTBO exactly across the full comparison surface | Entry activation is not a standalone explanation for the gain |

The important interpretation is not that the added ingredients do nothing. The important interpretation is that the current evidence does not isolate any one of them as the sole scientifically defensible explanation. That is why the paper must underclaim. The supported statement is that PSMS-v2, as a package of richer staged representation plus feasibility-aware constrained search, improves the local robust-search frontier under the fixed contract. The unsupported statement would be that one newly added component by itself explains the gain.

This is also why the current paper should avoid "module victory" language in the introduction, method, or figure text. The ablations did their job: they prevented an overconfident story. They did not weaken the main result. They clarified what kind of result it is.

## 7. Reproducibility And External-Sharing Notes

The current paper line is strong enough for technical circulation because the evidence now hangs together as one coherent package. The active repository snapshot contains the selected outline, evidence ledger, figure catalog, claim-evidence map, and a Markdown-first draft that maps back to the durable run and analysis artifacts. That is the right level of packaging for sharing with a technical reader who wants to understand what the current best line is and why it is believable.

For external technical sharing, the packet is easiest to understand in three layers.

1. Read the draft as the narrative layer: it explains the fixed contract, the PSMS-v2 package, the nominal gain, the held-out result, and the claim boundary in one place.
2. Read Figures 1 to 3 as the compact evidence layer: they show the verified frontier progression, what changed in the staged protocol family, and why the held-out bundle matters.
3. Use the claim-evidence map and evidence ledger as verification backstops: they are there to let a skeptical reader trace each headline statement back to durable artifacts, not to replace the main story.

At the same time, this is still not a submission-ready manuscript. The bundle now already includes a compact citation-grounded related-work section, a LaTeX-first mirror, a compiled seven-page PDF, a paper experiment matrix that makes the tested coverage stack explicit, and a page-level proofing note. The remaining gaps are venue-specific layout adaptation, a potentially fuller related-work synthesis, and one final wording sweep focused on clarity and novelty framing. Those are polishing gaps, not evidence gaps. The distinction matters: the paper is no longer waiting on one more experiment to justify its main claim.

## 8. Conclusion

PSMS-v2 is the strongest verified line in the quest so far. Under the accepted four-metric contract it improves the nominal frontier beyond both `BO_3step_aggressive` and the direct EVTBO anchor, and under the held-out combined-stress bundle it remains rank-1 and fully feasible. The evidence is strong enough to support a stable winner under the current GitHub/PyBaMM contract, but not to claim that every possible fast-charge task is already solved. The ablation campaign closes the main interpretation risk by showing that the result should be written as a package-level method gain rather than a single-component discovery. That is a narrower claim than a universal optimal-controller story, but it is also a much more durable and defensible one.

## References

- [R1] Saehong Park, Andrea Pozzi, Michael Whitmeyer, Hector Perez, Won Tae Joe, Davide M. Raimondo, and Scott Moura. *Reinforcement Learning-based Fast Charging Control Strategy for Li-ion Batteries*. arXiv:2002.02060, 2020.
- [R2] Benben Jiang, Yixing Wang, Zhenghua Ma, and Qiugang Lu. *Fast Charging of Lithium-Ion Batteries Using Deep Bayesian Optimization with Recurrent Neural Network*. arXiv:2304.04195, 2023.
- [R3] Myisha A. Chowdhury, Saif S. S. Al-Wahaibi, and Qiugang Lu. *Adaptive Safe Reinforcement Learning-Enabled Optimization of Battery Fast-Charging Protocols*. arXiv:2406.12309, 2024.
- [R4] Meng Yuan and Changfu Zou. *Lifelong Reinforcement Learning for Health-Aware Fast Charging of Lithium-Ion Batteries*. arXiv:2505.11061, 2025.
- [R5] J. Wang, C. G. Petra, and J. L. Peterson. *Constrained Bayesian Optimization with Merit Functions*. arXiv:2403.13140, 2024.
- [R6] Paolo Ascia, Elena Raponi, Thomas Bäck, and Fabian Duddeck. *Feasibility-Driven Trust Region Bayesian Optimization*. arXiv:2506.14619, 2025.

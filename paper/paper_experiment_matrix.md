# Paper Experiment Matrix

- Updated: 2026-04-17
- Current judgment: the current evidence is sufficient to present `PSMS-v2` as the verified incumbent under the accepted GitHub/PyBaMM contract. It is not sufficient to claim superiority on every possible fast-charge task, cell condition, or external benchmark.

## Coverage Stack

| Item | Role | Placement | Status | Tested surface | Why it matters |
|---|---|---|---|---|---|
| `baseline-metric-contract` | comparison contract | main text | completed | fixed `Q30 / plating_loss / sei_growth / total_lli` contract with `BO_3step_aggressive` as the accepted comparator | keeps every later frontier step on one auditable comparison surface |
| `run-vtbo-ua4-v1` | frontier context | main text | completed | nominal surface plus `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` in `followup_v1` | shows the last strong fixed-family gain before EVTBO and PSMS-v2 |
| `run-evtbo-ua4-v1` | immediate predecessor | main text | completed | nominal surface plus `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` in `followup_v1` | defines the previous verified anchor that `PSMS-v2` must beat |
| `run-psms-v2-main-v1` | headline result | main text | completed | nominal surface plus `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` in `followup_v1` | provides the main quantitative win and the promoted final protocol |
| `heldout-combo-v1` | out-of-bundle robustness support | main text | completed | `nominal`, `hot_plating_combo`, `hot_sei_combo`, and `hot_dual_combo` | shows that the promoted winner stays rank-1 after leaving the search-time bundle |
| `run-psms-v5-validate-v1` | negative stability check | discussion / appendix | completed | warm-start challengers rechecked on `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` in `followup_v1` | rejects nominal-only challengers that fail the robust gate and keeps `PSMS-v2` as the verified incumbent |
| `psms-ablation-sequence-prior` | attribution boundary | appendix | completed | matched rerun on `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` with only the sequence prior removed | shows that the sequence prior alone is not the sole explanation for the gain |
| `psms-ablation-entry-activation` | attribution boundary | appendix | completed | matched rerun on `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress` with only entry activation removed | shows that entry activation alone is not the sole explanation for the gain |

## Task-By-Task Sufficiency Snapshot

| Task bundle | Concrete scenarios | Verdict now | Boundary that still holds |
|---|---|---|---|
| Main comparison surface | nominal `Q30 / plating_loss / sei_growth / total_lli` | `PSMS-v2` is the strongest verified nominal protocol under the fixed contract | this does not by itself prove robustness or all-task superiority |
| `followup_v1` | `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, `sei_stress` | the promoted `PSMS-v2` winner stays fully feasible across the full in-bundle stress set | this is still one local scenario family inside the same GitHub/PyBaMM setup |
| `heldout_combo_v1` | `nominal`, `hot_plating_combo`, `hot_sei_combo`, `hot_dual_combo` | the same winner remains rank-1 after leaving the search bundle | this is one controlled out-of-bundle shift, not every external benchmark |
| Warm-start challenge | two nominal-stronger challengers retested on full `followup_v1` | both challengers fail the robust gate in `hot_cell`, `plating_stress`, and `sei_stress` | nominal-only improvements are not enough to replace the verified incumbent |
| Matched ablations | sequence prior removed, entry activation removed | the evidence still supports the package but not a single decisive component | keep the method claim package-level |
| Broader untested scope | other chemistries, other simulators, and broader benchmark suites | no verified result yet | do not claim universal task coverage |

## Supported Claims Now

1. `PSMS-v2` is the strongest verified line under the accepted GitHub/PyBaMM contract because it wins on the fixed four-metric main surface, stays fully feasible on `followup_v1`, remains rank-1 on `heldout_combo_v1`, and survives a focused challenge from nominal-only warm-start candidates.
2. The result is stable enough for technical external sharing because the main claim is backed by one fixed comparison contract, one search-time robust bundle, one held-out combined-stress bundle, and one negative stability check that rejects superficially better but infeasible challengers.
3. The supported method story is package-level: a richer staged representation plus feasibility-aware search improves the local frontier. The matched ablations now close the loophole that would otherwise over-credit any single new component.

## Claims Still Out Of Scope

1. The current paper should not claim that `PSMS-v2` already wins on every possible fast-charge task.
2. The current paper should not claim universal optimality across other chemistries, external simulators, or broader battery benchmarks.
3. The current paper should not claim that one isolated module is the uniquely decisive cause of the gain.

## Best Reopen Paths If More Coverage Is Needed

1. Expand the held-out matrix with more temperature and degradation combinations under the same four-metric contract.
2. Add one genuinely external transfer surface instead of re-running the same local search story again.
3. Only reopen component-attribution work if a stronger single-module story becomes necessary for a target venue.

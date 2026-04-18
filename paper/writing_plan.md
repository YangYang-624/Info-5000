# Writing Plan

- Updated: 2026-04-17
- Current judgment: the paper line is now evidence-stable and packaging-stable for external technical sharing. The remaining gap is venue polish, not missing evidence or missing deliverables.
- Headline evidence: PSMS-v2 improves nominal Q30 from `0.08990` to `0.09636` over `BO_3step_aggressive` (`+7.19%`) and from `0.09522` to `0.09636` over the EVTBO anchor (`+1.20%`) while keeping plating loss flat and improving both SEI growth and total LLI.
- Boundary evidence: on `heldout_combo_v1`, the PSMS-v2 winner stays rank-1 with `guard_pass_rate=1.0`, `robust_utility=0.0706`, `mean_score=0.0877`, and `worst_score=0.0032`.
- Attribution evidence: matched ablations of the sequence prior and entry activation still do not isolate a single decisive driver, so the paper should continue to reject single-component attribution.

## What Changed In This Pass

1. Added a LaTeX-first paper mirror under `paper/latex/` that faithfully restates the current Markdown-first draft.
2. Exported a standalone bibliography file under `paper/references.bib`.
3. Compiled a stable seven-page PDF under `paper/build/main.pdf`.
4. Recorded a clean compile report and a page-level proofing note so the package no longer depends on an unverified Markdown-only paper view.
5. Synchronized the README, paper bundle manifest, paper-line state, and quest summaries to the new PDF-backed bundle state.
6. Removed the last stale draft wording that still implied the package lacked PDF / LaTeX proofing, so the draft now matches the bundle and summary surfaces.
7. Added an explicit evaluation-coverage explanation that spells out the four-layer evidence stack and the no-"all tasks already won" claim boundary.
8. Added a durable paper experiment matrix in both Markdown and JSON so the tested surfaces, negative stability check, and honest claim boundary are easy to audit outside the draft prose.
9. Added a task-wise coverage snapshot that names the exact `followup_v1` and `heldout_combo_v1` scenarios, so outside readers can see what was actually tested before reading the full draft.

## What Is Now Stable

1. The outline contract, selected outline, evidence ledger, claim-evidence map, experiment matrix, Markdown draft, LaTeX mirror, and compiled PDF all tell the same package-level PSMS story.
2. The three paper-main figures, references, and tables render cleanly in the compiled PDF, and the final LaTeX log is free of warnings.
3. The external-sharing package can now safely emphasize the fixed four-metric contract, the frontier progression, the held-out validation, and the package-level claim boundary without reopening experiments.
4. The draft now explicitly explains why PSMS-v2 is the verified incumbent under the current GitHub/PyBaMM contract and why the paper does not claim all-task superiority.

## What The Paper Must Keep Saying Clearly

1. Why fixed-family improvement after EVTBO was saturating and why a richer staged family was the next defensible move.
2. What PSMS-v2 changes at the package level: richer staged protocol geometry, physics-prior masking, and feasibility-aware constrained search.
3. What the measured payoff is: better nominal Q30 than both the trusted baseline and EVTBO, with full guard feasibility retained.
4. What the coverage stack is: the fixed four-metric main surface; `followup_v1` with `nominal`, `warm_cell`, `hot_cell`, `plating_stress`, and `sei_stress`; `heldout_combo_v1` with `nominal`, `hot_plating_combo`, `hot_sei_combo`, and `hot_dual_combo`; matched ablations; and focused negative stability checks when nominal-only challengers appear.
5. What the ablations mean: they bound the interpretation to a joint package claim rather than proving one uniquely decisive component.
6. What the limitation is: this is a local, evidence-supported robustness improvement under the accepted PyBaMM contract, not a universal optimal controller claim or an all-task superiority claim.

## Next Writing Moves

1. Default next step: move to `finalize` and package PSMS-v2 as the verified incumbent with a PDF-backed paper bundle.
2. Optional next step if the target becomes venue submission: adapt the current paper to a venue-specific template, tighten the first-page novelty wording, and expand related work into a fuller comparison matrix.
3. Optional next step if the user wants deeper science before closure: reopen only for broader robustness validation or cleaner component attribution, not for another blind main-search pass.

## Write-Stage Handoff

1. Completed: the draft, experiment matrix, review note, final claim ledger, and README entry now all answer the same user-facing question in the same way: the tested coverage is strong enough for a stable contract-level winner claim, but not for an all-task superiority claim.
2. Still incomplete or intentionally out of scope: broader external transfer, larger held-out task families, and any claim that the original GitHub project has been exhausted across every possible task view.
3. Durable outputs to trust: `paper/draft.md`, `paper/paper_experiment_matrix.md`, `paper/paper_experiment_matrix.json`, `paper/review/review.md`, `paper/final_claim_ledger.md`, `paper/build/main.pdf`, and `paper/paper_bundle_manifest.json`.
4. Recommended next anchor: `finalize`, with the explicit framing that PSMS-v2 is the verified incumbent and that broader task-coverage claims remain future work.
5. Do not repeat by default: another wording-only write pass or another blind main-search cycle. Reopen only if the target changes to venue submission polish or to a broader robustness campaign.

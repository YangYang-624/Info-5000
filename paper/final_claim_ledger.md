# Final Claim Ledger

- Updated: 2026-04-17
- Current judgment: the PSMS-v2 line is finalize-ready for technical external sharing. It is not yet a venue-polished submission package.

## Supported

1. `claim-final-beats-baseline`
   - Claim: PSMS-v2 improves the verified nominal frontier beyond `BO_3step_aggressive` under the unchanged four-metric contract.
   - Evidence: `paper/draft.md`, `paper/claim_evidence_map.json`, `paper/evidence_ledger.json`, `paper/build/main.pdf`
   - Safe to surface: yes
   - Caveat: the improvement is local to the accepted PyBaMM contract rather than a universal charging result.
2. `claim-final-beats-evtbo`
   - Claim: PSMS-v2 also improves on the direct EVTBO anchor while keeping full guard feasibility on the search bundle.
   - Evidence: `paper/draft.md`, `paper/claim_evidence_map.json`, `status.md`, `SUMMARY.md`
   - Safe to surface: yes
   - Caveat: the gain is measurable but modest, so narrative emphasis should stay on comparability and trust rather than only on effect size.
3. `claim-heldout-rank1`
   - Claim: the promoted PSMS-v2 protocol remains rank-1 and fully feasible on the held-out combined-stress bundle.
   - Evidence: `paper/draft.md`, `paper/evidence_ledger.json`, `paper/build/main.pdf`
   - Safe to surface: yes
   - Caveat: the held-out bundle is still small and should be described as meaningful local validation rather than broad generalization.
4. `claim-delivery-package`
   - Claim: the paper line now has a synchronized Markdown draft, LaTeX mirror, compiled PDF, compile report, and proofing note.
   - Evidence: `paper/paper_bundle_manifest.json`, `paper/build/compile_report.json`, `paper/proofing/proofing_report.md`
   - Safe to surface: yes
   - Caveat: this means share-ready packaging, not automatic submission readiness.

## Partially Supported

1. `claim-package-level-mechanism`
   - Claim: PSMS-v2 should be described as a package-level representation-and-search gain.
   - Evidence: `paper/draft.md`, `paper/claim_evidence_map.json`, `paper/review/review.md`
   - Safe to surface: yes, with the package-level boundary stated explicitly
   - Caveat: the current evidence does not isolate any one added component as uniquely decisive.
2. `claim-submission-readiness`
   - Claim: the paper is ready for outside technical sharing and close to a submission-facing package.
   - Evidence: `paper/build/main.pdf`, `paper/build/compile_report.json`, `paper/proofing/proofing_report.md`, `paper/review/review.md`
   - Safe to surface: only in the weaker form "technical sharing ready"
   - Caveat: venue template work, broader related-work positioning, and one more wording sweep are still optional but unfinished.

## Unsupported

1. `claim-single-component-driver`
   - Claim: one specific PSMS component, such as the sequence prior or entry activation, is the uniquely decisive cause of the gain.
   - Evidence against: `paper/draft.md`, `paper/claim_evidence_map.json`, `paper/review/review.md`
   - Safe to surface: no
   - Caveat: the ablations bound the story to the joint package rather than a single-module victory.
2. `claim-all-task-superiority`
   - Claim: PSMS-v2 has already been shown to win across every relevant fast-charge task exposed by the original GitHub project or any reasonable extension of it.
   - Evidence against: the current evidence stack covers the fixed four-metric main surface, the `followup_v1` five-scenario bundle, `heldout_combo_v1`, a focused negative stability check, and matched ablations only.
   - Safe to surface: no
   - Caveat: the current result supports a verified incumbent under the accepted GitHub/PyBaMM contract, not a statement that every possible task variant is already covered.
3. `claim-universal-optimality`
   - Claim: PSMS-v2 is a broadly optimal or generally dominant fast-charging controller.
   - Evidence against: fixed-contract local evidence only
   - Safe to surface: no
   - Caveat: the current quest supports a strong local result, not a universal control claim.

## Deferred

1. `claim-stress-risk-frontier-incumbent`
   - Claim: the newer stress-risk idea should replace PSMS-v2 as the main result.
   - Evidence status: deferred because no verified main run exists
   - Safe to surface: no
   - Reopen condition: a verified main run plus a repaired environment path
2. `claim-broader-robustness`
   - Claim: the current winner remains strongest under a much broader distribution shift than `heldout_combo_v1`.
   - Evidence status: deferred
   - Safe to surface: only as future work
   - Reopen condition: a targeted broader robustness campaign

## Belief-Change Log

1. Earlier frontier thinking suggested that a newer stress-risk line might become the next headline result.
   - What changed: that line never produced a verified main run and its environment path stayed blocked.
   - New recommendation: keep PSMS-v2 as the verified incumbent and list the stress-risk route only as deferred.
2. Earlier writing notes treated the missing PDF and page-proof state as the main remaining blocker.
   - What changed: the LaTeX mirror, compiled PDF, compile report, and proofing note are now present.
   - New recommendation: move to `finalize` unless the user wants venue-specific polish.
3. Earlier mechanism framing risked sounding like a single-component story.
   - What changed: matched ablations and the rewritten paper line now consistently narrow the claim to a package-level gain.
   - New recommendation: keep the package-level framing in every external summary.

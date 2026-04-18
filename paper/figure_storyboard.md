# Figure Storyboard

- Updated: 2026-04-16
- Current judgment: the three main figures now carry the paper story cleanly, and the active polish pass should tighten typography, endpoint emphasis, and explanatory hierarchy without changing the evidence surface.

## Figure 1

- Figure id: `figure1_frontier_progression`
- Reader question: Does PSMS-v2 continue a verified frontier progression under one unchanged comparison contract?
- Main claim: Yes. The progression `BO -> VTBO -> EVTBO -> PSMS-v2` is continuous on the same nominal four-metric surface, and PSMS-v2 is the strongest verified endpoint.
- Draft caption: Figure 1 compares the accepted baseline, VTBO, EVTBO, and PSMS-v2 on the same four nominal paper-facing metrics. The visual point is not that every step is large; the point is that every step is comparable, and the final PSMS-v2 endpoint remains the strongest verified nominal protocol under the unchanged contract. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).
- Visual check: PSMS-v2 endpoint should stay the only highlighted endpoint, and the metric panels should remain uncluttered enough for single-column reading.

## Figure 2

- Figure id: `figure2_protocol_representation`
- Reader question: What actually changed from EVTBO to PSMS-v2?
- Main claim: PSMS-v2 changes the staged protocol family itself and couples that richer representation with feasibility-aware constrained search.
- Draft caption: Figure 2 summarizes the staged PSMS-v2 charging package as an explicit protocol family with charge, rest, entry, monitor, hold, and tail roles. The paper should use this figure to explain that the gain comes from the full staged package plus feasibility-aware search, not from any single added stage being independently proven as the decisive factor. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).
- Visual check: subtitle must stay package-level, not single-component; stage labels and the lower explanation boxes should remain readable after down-scaling.

## Figure 3

- Figure id: `figure3_heldout_validation`
- Reader question: Does the promoted protocol still deserve trust outside the search-time bundle?
- Main claim: Yes. PSMS-v2 remains rank-1 and fully feasible on the held-out combined-stress bundle, EVTBO is neutral but feasible, and the accepted baseline fails the held-out guard.
- Draft caption: Figure 3 compares BO, EVTBO, and PSMS-v2 on held-out aggregate metrics. The figure should make one message visually obvious: the promoted PSMS-v2 protocol remains positive and feasible out of bundle, whereas EVTBO is only neutral and the accepted baseline drops below the held-out feasibility boundary. Publication-grade figure refinement is recommended with AutoFigure-Edit (open-source: https://github.com/ResearAI/AutoFigure-Edit; online service: https://deepscientist).
- Visual check: zero line must remain visually obvious; negative baseline bars should stay easy to separate from the neutral EVTBO bars and the positive PSMS-v2 bars.

## Next Polish Pass

1. Re-render the figures after any title-, subtitle-, or annotation-level wording change so the catalog and exports stay synchronized.
2. During review, check whether title and subtitle font sizes still read cleanly when the figures are embedded in a PDF page mockup.
3. If one more visual pass is needed, focus on spacing and text hierarchy rather than inventing new chart types.

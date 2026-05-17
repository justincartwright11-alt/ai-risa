# AI-RISA Button 2 Visual Intelligence Acceptance Rules (v1)

## Purpose
Define a docs-only acceptance-rule pack for future Button 2 visual/report upgrades, derived from the locked research-and-implications engine and roadmap.

This slice is docs-only.

## Core Rule
Before changing the PDF renderer, define exactly what better visual intelligence means in testable acceptance terms.

## Upstream Locked Inputs
- ai-risa-research-and-implications-engine-v1 (555cd88)
- ai-risa-visual-intelligence-research-application-roadmap-v1 (deb9988)
- button2-dossier-handoff-report-context-final-handoff-v1 (9aa11ae)

## Rule Format Standard
Each rule must include:
- Intent: decision-support objective
- Condition: measurable context or input
- Acceptance criteria: deterministic pass/fail checks
- Safety constraints: no unauthorized generation/export/write/delivery behavior
- Traceability: mapping to research principle

---

## 1. Page Hierarchy Rules
### Rule PH-1: Executive-first order
- Intent: surface high-value conclusions first.
- Condition: a multi-section report preview is rendered.
- Acceptance criteria:
  - Top section must contain executive summary block.
  - Summary block appears before tactical deep-dive sections.
  - No critical conclusions are only present below first fold.
- Safety constraints: preview-only contexts must not auto-generate reports.

### Rule PH-2: Evidence ladder ordering
- Intent: make logic progression explicit.
- Condition: claim + support sections are present.
- Acceptance criteria:
  - Every major claim is followed by evidence/caveat pairing.
  - Contradictions are labeled, not hidden.
  - Confidence band is visible near each major claim.

## 2. One-Page / One-Main-Idea Rules
### Rule OI-1: Single dominant question per page
- Intent: prevent cognitive overload.
- Condition: any page-level composition is produced.
- Acceptance criteria:
  - One dominant heading objective per page.
  - Secondary blocks support the dominant objective only.
  - No unrelated tactical branch appears on same page.

### Rule OI-2: Summary sentence requirement
- Intent: enforce decisive interpretation.
- Condition: page has data visual blocks.
- Acceptance criteria:
  - Page includes one summary sentence translating visuals into implication.
  - Sentence references risk/opportunity and confidence.

## 3. Tactical Chart Rules
### Rule TC-1: Tactical axis clarity
- Intent: charts must be interpretable without guesswork.
- Condition: tactical chart is shown.
- Acceptance criteria:
  - Axis labels include units/context.
  - Legend is present and non-ambiguous.
  - Color encoding has semantic consistency across report.

### Rule TC-2: Action annotation
- Intent: convert chart into decision support.
- Condition: chart includes trend or matchup deltas.
- Acceptance criteria:
  - At least one chart annotation states tactical implication.
  - Annotation references directionality (improving/declining/stable).

## 4. Scenario-Tree Rules
### Rule ST-1: Branch completeness
- Intent: show plausible pathways, not single-track claims.
- Condition: scenario tree is present.
- Acceptance criteria:
  - At least primary/secondary/failure branches are shown.
  - Each branch includes confidence level.
  - Each branch includes trigger condition.

### Rule ST-2: Branch exclusivity labels
- Intent: avoid contradictory simultaneous recommendations.
- Condition: branching outcomes overlap risk factors.
- Acceptance criteria:
  - Mutually exclusive branches are marked explicitly.
  - Shared dependencies are listed once in common node.

## 5. Telemetry / Round-Control Rules
### Rule TR-1: Temporal segmentation
- Intent: represent round-by-round dynamics clearly.
- Condition: temporal control metrics are displayed.
- Acceptance criteria:
  - Segmented by rounds/time windows.
  - Momentum shifts are visually distinct.
  - Recovery windows and pressure windows are labeled.

### Rule TR-2: Control-state transitions
- Intent: show when control changes, not only totals.
- Condition: aggregated control metrics are shown.
- Acceptance criteria:
  - Transition points are marked.
  - Transition causes are annotated where evidence exists.

## 6. Risk and Collapse-Marker Rules
### Rule RC-1: Risk marker taxonomy
- Intent: normalize risk language.
- Condition: risk indicators are present.
- Acceptance criteria:
  - Markers use standardized levels (low/medium/high/critical).
  - Marker definitions are available in compact legend.
  - Marker color and shape mapping is consistent.

### Rule RC-2: Collapse precursor visibility
- Intent: early warning indicators must be explicit.
- Condition: collapse risk exists.
- Acceptance criteria:
  - At least one precursor signal is named and timestamped.
  - Counter-signal or mitigation note is shown when available.

## 7. Source-Traceability Rules
### Rule STX-1: Claim-to-source linkage
- Intent: ensure auditability.
- Condition: non-trivial claim appears in report context.
- Acceptance criteria:
  - Claim links to source reference id.
  - Source date and source type are present.
  - Unsupported claim is flagged as low-confidence.

### Rule STX-2: Source conflict disclosure
- Intent: avoid silent source contradictions.
- Condition: multiple sources disagree.
- Acceptance criteria:
  - Conflict state is visible.
  - Preferred source rationale is shown.
  - Confidence is downgraded or marked uncertain.

## 8. No-Clutter / No-Overlap / No-Off-Page-Text Rules
### Rule CL-1: Non-overlap guarantee
- Intent: preserve readability.
- Condition: page with multiple visual blocks.
- Acceptance criteria:
  - No text overlap with charts/cards.
  - Minimum spacing threshold between blocks is maintained.

### Rule CL-2: Off-page text prevention
- Intent: avoid clipped intelligence statements.
- Condition: long annotations or labels exist.
- Acceptance criteria:
  - No clipped labels beyond page bounds.
  - Overflow behavior is deterministic (wrap/truncate+tooltip marker in preview specs).

### Rule CL-3: Density cap
- Intent: prevent information saturation.
- Condition: page includes many signals.
- Acceptance criteria:
  - Max cards/visual objects per page threshold is enforced.
  - Overflow content is deferred to next page/section.

## 9. Premium Intelligence-Brief Visual Standard
### Rule PI-1: Premium brief composition
- Intent: ensure elite briefing quality.
- Condition: premium intelligence report context is rendered.
- Acceptance criteria:
  - Executive summary + evidence panels + scenario block + risk block must all exist.
  - Confidence and uncertainty are always visible.
  - Design language is coherent across pages.

### Rule PI-2: Decision-readiness checkpoint
- Intent: verify output is decision-ready.
- Condition: report-context preview is complete.
- Acceptance criteria:
  - Clear recommended focus area is stated.
  - Contrarian scenario is present.
  - Immediate watch-signals are listed.

## 10. Future Button 2 Renderer Test Requirements
### Rule RT-1: Renderer regression suite baseline
- Intent: lock quality before visual implementation scales.
- Condition: first renderer upgrade slice begins.
- Acceptance criteria:
  - Automated tests cover PH/OI/TC/ST/TR/RC/STX/CL/PI rule families.
  - Snapshot or semantic layout tests validate hierarchy and non-overlap.
  - Safety tests assert no preview path triggers generation/export/write/delivery.

### Rule RT-2: Gate 2 integrity
- Intent: preserve approval boundaries during visual upgrades.
- Condition: renderer or layout code changes are introduced.
- Acceptance criteria:
  - Gate 2 generation endpoint remains approval-gated.
  - No auto-approval logic appears in visual/report preview code paths.

## Safety Invariants (Applies to All Rule Families)
- preview_only remains true in preview pathways.
- No automatic report generation, PDF generation, export, delivery, or report write.
- No profile/database/ranking/result/learning/calibration mutation from preview contexts.
- No filesystem writes and no live web calls from preview-only validation paths.

## Non-Goals
- No renderer implementation changes in this slice.
- No dashboard runtime changes in this slice.
- No PDF layout code changes in this slice.
- No gate logic rewrites in this slice.

## Next Implementation Move (Narrow)
After this acceptance pack is locked, the first implementation move should be a narrow Button 2 renderer/test slice scoped to one rule family (recommended: Page Hierarchy + No-Clutter baseline) instead of a broad redesign.

## Final Verdict
AI-RISA now has a testable acceptance-rule definition for premium Button 2 visual intelligence quality before renderer and PDF layout implementation work begins.
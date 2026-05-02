# AI RISA Premium Report Factory - Button 2 Premium PDF Visual Intelligence Layout Upgrade Design

Slice: ai-risa-premium-report-factory-button2-premium-pdf-visual-intelligence-layout-upgrade-design-v1
Date: 2026-05-02
Type: docs-only design

## Baseline

1. Starting HEAD: 09aa123
2. Runtime baseline lineage: a7b4e47
3. Prior checkpoint: combat-intelligence demo-readiness validation note locked (18/18 PASS)
4. Current state: demo-safe, docs-only HEAD, no active runtime edits

## Goal

Design a Button 2 premium PDF visual-intelligence layout upgrade that improves operator and customer readability of combat-intelligence outputs without changing current readiness gates, approval controls, or generation contracts.

## Scope

In scope:

1. Button 2 premium PDF layout and presentation structure.
2. Visual hierarchy for existing combat-intelligence sections and metadata.
3. Deterministic section ordering and page composition rules.
4. Additive styling/tokens plan for typography, spacing, callouts, and risk emphasis.
5. Backward-compatible rollout plan with feature flag guardrails.

Out of scope:

1. No changes to Button 1 behavior.
2. No changes to Button 3 behavior.
3. No changes to customer-ready, draft-only, or blocked gate logic.
4. No changes to operator approval requirement.
5. No changes to data persistence, billing, learning, or calibration.
6. No changes to analysis source selection logic.

## Existing Constraints To Preserve

1. Generation requires explicit operator approval.
2. Existing readiness and sparse-completion gates remain authoritative.
3. Existing additive combat metadata remains contract-compatible.
4. Existing API response keys and semantic behavior remain unchanged.
5. Missing/placeholder critical content remains blocking for customer-ready output.

## Design Principles

1. High signal per page: each page should answer one operator question clearly.
2. Deterministic reading path: executive summary first, tactical narrative next, risk and scenario last.
3. Source transparency: clearly indicate section source and confidence context where already available.
4. Print-safe composition: typography and spacing must remain legible in grayscale print and PDF viewer zoom levels.
5. Non-destructive upgrade: layout enhancement only, no behavior or gate drift.

## Proposed Visual Layout Model

### A) Cover and Header System

1. Cover block with event, bout, and generation timestamp.
2. Status ribbon showing final quality state (customer_ready, draft_only, blocked).
3. Compact approval/source badge row to preserve operator context.

### B) Executive Intelligence Page

1. Headline Prediction panel with dominant outcome and confidence framing.
2. Executive Summary two-column composition:
- Left: tactical narrative bullets.
- Right: decisive factors and trigger watchpoints.
3. Risk Warnings strip with severity tags.

### C) Combat Dynamics Pages

1. Decision Structure section with explicit branch blocks.
2. Energy Use and Gas Tank Projection with round-band timeline bars.
3. Fatigue Failure Points and Collapse Triggers in mirrored cards.
4. Mental Condition and Deception/Unpredictability as paired comparative modules.

### D) Scenario and Round Control Page

1. Round-by-Round Control Shifts visual ladder.
2. Scenario Tree / Method Pathways as branch cards with primary and contingency path.
3. Dominance / Danger Zone indicators with caution highlights.

### E) Operator Traceability Appendix

1. Section source map table (section -> source type -> contributing engines).
2. Populated/missing section summary table.
3. Missing engine outputs list when applicable.
4. Operator notes area preserved with current behavior.

## Section Ordering Contract

Target order in generated PDFs:

1. Cover and quality status
2. Headline Prediction
3. Executive Summary
4. Matchup Snapshot
5. Decision Structure
6. Energy Use and Gas Tank Projection
7. Fatigue Failure Points
8. Mental Condition
9. Collapse Triggers
10. Deception and Unpredictability
11. Round-by-Round Control Shifts
12. Scenario Tree / Method Pathways
13. Risk Warnings
14. Operator Notes
15. Traceability Appendix

Design rule:
The ordering is deterministic across all runs to reduce review friction and QA ambiguity.

## Visual Token Plan (Design-Level)

1. Typography:
- Title: strong serif display for major section headers.
- Body: neutral sans-serif for dense tactical analysis blocks.
- Data labels: monospace-like numeric style where alignment is needed.

2. Color semantics:
- Stable neutral base for readability.
- Controlled accent for tactical advantage cues.
- Caution spectrum for risk warnings.
- Print fallback shades for grayscale output.

3. Spacing and rhythm:
- Fixed vertical spacing scale for section boundaries.
- Card padding contract to avoid dense text walls.
- Max line-length targets for summary and bullet blocks.

4. Visual primitives:
- Timeline bars for round control.
- Severity tags for risk markers.
- Branch cards for scenario pathways.
- Source badges for traceability.

## Compatibility and Rollout Strategy

1. Introduce layout as an additive renderer mode behind a Button 2 feature flag.
2. Keep legacy layout path available during validation window.
3. Preserve existing PDF filename/path contracts.
4. Preserve open-folder and report-link behaviors.
5. Roll forward only after design review + implementation + post-freeze smoke.

## Validation Plan

Design validation acceptance criteria:

1. New layout map covers all current premium report sections.
2. No section currently required by readiness flow is omitted.
3. Visual order is deterministic for identical inputs.
4. Existing additive combat metadata remains visible in appendix/traceability view.
5. Existing API behavior remains unchanged by layout feature flag off path.
6. Existing Button 2 quality-state labels remain accurate in rendered PDF.
7. No Button 1 route behavior drift.
8. No Button 3 route behavior drift.

Recommended implementation-phase test layers:

1. Renderer unit tests for section ordering and block inclusion.
2. Snapshot tests for representative customer_ready and blocked outputs.
3. API regression tests proving no contract drift.
4. Smoke test confirming PDF generation, open-folder action, and cleanup hygiene.

## Risks and Guardrails

Primary risks:

1. Layout complexity could reduce readability if too many visual elements compete.
2. Non-deterministic section rendering may introduce QA instability.
3. Excessive style logic may accidentally couple to gate-state logic.

Guardrails:

1. Keep rendering pure and data-driven; no gate decisions in presentation layer.
2. Enforce deterministic section order contract.
3. Keep feature flag rollback path available until archive lock.
4. Preserve existing behavior tests as mandatory regression gate.

## Implementation Handoff (Next Slice Expectations)

1. Build renderer upgrades in isolated presentation module(s).
2. Add deterministic section-order tests and snapshot baselines.
3. Run focused Button 2 regression suite plus Button 1/3 drift suite.
4. Produce post-freeze smoke note with live route checks and artifact cleanup proof.

## Design Verdict

READY FOR DESIGN REVIEW.

This slice is design-only and preserves all current runtime safety behavior while defining a concrete visual-intelligence upgrade path for Button 2 premium PDFs.

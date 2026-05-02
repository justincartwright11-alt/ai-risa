# AI RISA Premium Report Factory - Button 2 Readiness Engine Runtime Wiring Design

Slice: ai-risa-premium-report-factory-global-engine-pack-button2-readiness-engine-runtime-wiring-design-v1
Date: 2026-05-02
Type: docs-only runtime wiring design

## Baseline

- Runtime/product lineage: e94b86e
- Current HEAD: 8839a30
- Current state: demo-safe, docs-only HEAD, no runtime behavior drift
- Registry visibility: live and archived
- Scaffolds: built and smoke-proven

## Goal

Design the first real runtime wiring step for the global engine pack by connecting Button 2 Report Readiness and Sparse-Case Result Completion scaffolds into the existing Button 2 report generation flow.

Purpose:

1. Block weak customer PDFs.
2. Identify missing required report sections.
3. Prevent incomplete prediction outputs from being promoted to customer-ready reports.

## Scope

In scope:

1. Button 2 only.
2. Runtime wiring design only.
3. Report Readiness Engine attachment design.
4. Sparse-Completion Engine attachment design.
5. Additive API and operator UI readiness visibility design.

Out of scope:

1. No implementation in this slice.
2. No Button 1 changes.
3. No Button 3 changes.
4. No global database writes.
5. No learning/calibration changes.
6. No betting-market runtime behavior in this slice.
7. No customer PDF generation without approval.

## 1) Existing Button 2 Generation Flow

Current flow at a high level:

1. Operator selects queued matchup records for generation.
2. Generation request requires operator approval input.
3. Report build pipeline assembles report content for selected records.
4. Existing gates and status handling determine generated vs rejected outputs.
5. Response returns generation summary, accepted/rejected counts, warnings/errors, and artifacts.

Current weakness this slice addresses:

- Content can be structurally weak (missing sections, placeholder text, sparse prediction fields) even when generation pipeline runs.

## 2) Readiness Scaffold Attachment Point

Attach Report Readiness evaluation inside Button 2 generation per matchup record after report content assembly and before customer-ready acceptance.

Attachment sequence:

1. Build/collect section outputs for the matchup.
2. Compute missing required sections.
3. Scan section text for placeholder/unavailable markers.
4. Evaluate report readiness status using scaffold readiness contract.
5. Set gate result for customer-ready eligibility.

This attachment is evaluation-first and gating-second.

## 3) Sparse-Completion Scaffold Attachment Point

Attach Sparse-Case Result Completion evaluation in the same per-matchup path before final readiness gate decision.

Attachment sequence:

1. Extract required prediction fields from assembled outputs.
2. Evaluate sparse-completion status and completion reason.
3. Feed sparse-completion outcome into final readiness gate decision.
4. If sparse-completion fails, block customer-ready promotion.

Sparse-completion is a required sub-gate for customer-ready path.

## 4) Inputs Required

Per-matchup runtime inputs for readiness and sparse checks:

1. matchup_id
2. fighter_a
3. fighter_b
4. event_name
5. event_date
6. analysis_source_status
7. linked_analysis_record_id
8. section outputs
9. prediction fields

Input notes:

- analysis_source_status and linked_analysis_record_id are required to prove analysis linkage quality.
- section outputs and prediction fields are required to determine readiness and sparse completeness.

## 5) Outputs Added (Additive Only)

Per generated/rejected matchup payload will add:

1. report_quality_status
2. customer_ready
3. missing_sections
4. sparse_completion_status
5. sparse_completion_reason
6. readiness_gate_reason

Output behavior:

- All fields are additive.
- Existing Button 2 response keys remain unchanged.
- Existing fields are not renamed or removed.

## 6) Customer-Ready Gate Rules

Customer-ready gate must block when any of the following are true:

1. Required sections are missing.
2. Placeholder/unavailable text remains in required sections.
3. Prediction fields are incomplete per sparse-completion contract.

Customer-ready gate may pass only when:

1. Required sections are present.
2. Required section content is non-placeholder and non-unavailable.
3. Sparse-completion passes required prediction fields.
4. Existing operator approval conditions are satisfied.

If gate fails and draft mode is not explicitly selected, the matchup is blocked for customer-ready output.

## 7) Draft Behavior

Draft behavior design:

1. Draft path is allowed only when explicitly selected.
2. Draft outputs must be marked: DRAFT ONLY - NOT CUSTOMER READY.
3. Draft outputs must not set customer_ready=true.
4. No silent promotion from draft to customer-ready.

Draft mode is not a bypass for missing section or sparse completion visibility; it is an explicit non-customer-ready fallback path.

## 8) Operator Approval Behavior

Approval behavior remains strict:

1. Generation approval is still required.
2. Customer-ready approval is still required.
3. Readiness pass does not override approval requirements.
4. Approval checks remain enforced before any customer-ready promotion.

## 9) API Contract Changes

Button 2 API contract changes are additive only:

1. Preserve all existing Button 2 keys.
2. Add readiness and sparse status fields per matchup result.
3. Keep existing status/error shape stable for backward compatibility.

No destructive API contract change is allowed in this slice.

## 10) UI Visibility Plan (Button 2)

Operator UI additions in Button 2 generation results:

1. Show missing_sections list when present.
2. Show report_quality_status for each matchup.
3. Show sparse_completion_status.
4. Show sparse_completion_reason when blocked or draft-only.
5. Show readiness_gate_reason.
6. Show explicit reason when customer PDF is blocked.

UI goal is transparent operator diagnosis of why a matchup is customer-ready, draft-only, or blocked.

## 11) Non-Goals

1. No Button 1 ranking runtime wiring.
2. No Button 3 accuracy/calibration runtime wiring.
3. No betting-market runtime wiring.
4. No global DB writes.
5. No learning updates.
6. No billing behavior.

## 12) Validation Plan

Validation must prove all of the following:

1. Missing analysis blocks customer PDF.
2. Placeholder sections block customer_ready.
3. Sparse prediction gets completed/evaluated before draft-only fallback.
4. Complete analysis can pass customer_ready.
5. Existing Button 2 tests remain green.
6. Existing scaffold tests remain green.
7. No Button 1/3 behavior drift.

Recommended validation layers:

1. Unit-level checks for readiness and sparse gate decisions.
2. Button 2 route-level tests verifying additive response fields and gate reasons.
3. End-to-end smoke for customer-ready vs draft-only vs blocked outcomes.

## Risk and Guardrails

Primary risks:

1. Overblocking due to aggressive placeholder detection.
2. Inconsistent sparse-field mapping across report types.
3. Confusion between readiness preview and enforcement status.

Guardrails:

1. Keep gate reasons explicit and deterministic.
2. Keep draft-only labeling mandatory and visible.
3. Keep approvals independent and preserved.
4. Keep all changes additive to existing API contract.

## Design Verdict

READY FOR DESIGN REVIEW.

This design is limited to Button 2 runtime readiness/sparse gating and preserves global safety constraints:

1. No write expansion.
2. No learning/calibration drift.
3. No Button 1/3 runtime change.
4. No customer-ready output without readiness + sparse + approval pass.

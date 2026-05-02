# AI RISA Premium Report Factory - Button 1 Ranking Runtime Wiring Design

Slice: ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-v1
Date: 2026-05-02
Branch: next-dashboard-polish
Type: docs-only design

## Baseline

1. Starting HEAD: 5309c6b
2. Runtime lineage baseline: 16bda9e
3. Current state: demo-safe, clean worktree, no active runtime edits
4. Prior lane status: Button 2 visual-layout demo-readiness note locked

## Goal

Design the first Button 1 runtime wiring step for ranking intelligence so discovered fights and parse-preview rows expose deterministic advisory ranking signals before operator save.

## Scope

In scope:

1. Button 1 only.
2. Design only; no implementation in this slice.
3. Runtime wiring design for ranking scaffold contracts into discovery and parse-preview response surfaces.
4. Additive API response design and UI indicator design for ranking intelligence.
5. Deterministic composite ranking and fallback behavior design.

Out of scope:

1. No Button 2 changes.
2. No Button 3 changes.
3. No global database writes introduced in this slice.
4. No learning/calibration updates.
5. No betting runtime behavior changes.
6. No automatic queue save.
7. No customer PDF generation.
8. No approval-gate bypass.

## Existing Contract Anchor

Button 1 ranking contracts already exist in scaffold form and define engine IDs, output keys, score ranges, weights, and deterministic composite behavior.

Design requirement:

1. Runtime wiring must consume existing ranking scaffold contracts as the source of truth.
2. No duplicate scoring schema should be created outside scaffold contracts.

## Ranking Fields To Expose

Required additive ranking fields on Button 1 discovery and parse-preview rows:

1. fight_readiness_score
2. report_value_score
3. customer_priority_score
4. event_card_priority_score
5. betting_interest_score
6. commercial_sellability_score
7. analysis_confidence_score
8. composite_ranking_score
9. ranking_bucket
10. ranking_reasons

Design note:

1. ranking_bucket is a deterministic derived class from composite score (for example: priority_tier_1, priority_tier_2, watchlist_tier, low_priority).
2. ranking_reasons is an ordered, deterministic list of concise reason codes/messages tied to row inputs and score drivers.

## Runtime Wiring Plan (Button 1)

### 1) Discovery Response Wiring

Attach ranking enrichment after discovery extraction normalizes candidate rows and before response serialization.

Sequence:

1. Build normalized discovery row.
2. Build ranking input payload from row fields and source metadata.
3. Compute per-engine scores via scaffold-compatible runtime adapter.
4. Validate score completeness/range against ranking contracts.
5. Compute composite_ranking_score deterministically.
6. Build ranking_bucket and ranking_reasons deterministically.
7. Return additive ranking fields in discovery response rows.

### 2) Parse Preview Response Wiring

Attach ranking enrichment to parsed preview rows using the same ranking adapter and deterministic rules as discovery path.

Constraint:

1. Preview ranking is advisory only and must not trigger persistence.
2. Operator selection remains manual and explicit.

### 3) Save Flow Boundary

Save-selected remains unchanged in core behavior:

1. Operator approval is required before save.
2. Ranking does not auto-select rows.
3. Ranking does not auto-save rows.
4. Save writes only operator-selected rows through existing approved-save boundary.

## API Design (Additive Only)

Design rule:

1. Existing Button 1 discovery/preview/save response keys are preserved unchanged.
2. Ranking keys are additive only on row objects where ranking is provided.

Discovery and preview row additive payload shape:

1. fight_readiness_score: number 0-100
2. report_value_score: number 0-100
3. customer_priority_score: number 0-100
4. event_card_priority_score: number 0-100
5. betting_interest_score: number 0-100
6. commercial_sellability_score: number 0-100
7. analysis_confidence_score: number 0-100
8. composite_ranking_score: weighted number 0-100
9. ranking_bucket: string
10. ranking_reasons: array[string]

Optional diagnostic additive fields for implementation-phase clarity:

1. ranking_validation_ok
2. ranking_missing_inputs
3. ranking_contract_version

## Determinism and Fallback Design

Determinism requirements:

1. Same input row payload always produces the same ranking outputs.
2. Composite score uses scaffold-defined weights only.
3. Row ordering by ranking is stable under tie conditions using deterministic tie-breakers.

Fallback requirements:

1. Missing ranking inputs must not break discovery or preview responses.
2. Missing inputs should produce safe fallback score defaults and explicit ranking_reasons entries.
3. Rows with incomplete ranking inputs remain operator-selectable and reviewable.
4. ranking_bucket should fall back to a deterministic low-confidence category when required inputs are absent.

## Button 1 UI Design (Advisory Ranking)

UI behavior requirements:

1. Discovery results show ranking indicators per row.
2. Parse Preview rows show ranking indicators per row.
3. Ranking is advisory only.
4. Operator can select/deselect manually regardless of ranking.
5. Queue save remains approval-gated.
6. No automatic save or auto-selection based on ranking.

Suggested row-level display tokens:

1. Composite score badge.
2. Ranking bucket label.
3. Top ranking reasons preview.
4. Optional tooltip/details panel for component scores.

## Governance and Safety

Hard constraints:

1. No uncontrolled writes.
2. No automatic queue/database save.
3. No customer PDF generation.
4. No learning/calibration updates.
5. No Button 2/3 behavior changes.
6. Approval gate remains mandatory for permanent save.

## Validation Plan

Implementation-phase validation must prove:

1. Discovery response includes additive ranking fields.
2. Parse preview response includes additive ranking fields.
3. Composite ranking is deterministic.
4. Missing ranking data falls back safely without breaking existing flows.
5. Existing Button 1 save flow remains approval-gated.
6. Existing Button 2 tests remain green.
7. Existing Button 3 tests remain green.
8. Ranking scaffold tests remain green.
9. No runtime artifacts are committed during validation.

Recommended test layers:

1. Ranking adapter unit tests for per-engine scoring + fallback behavior.
2. Contract tests validating score ranges and required keys.
3. Endpoint tests for additive-only response behavior.
4. Cross-button anti-drift tests.
5. Post-freeze smoke with runtime artifact cleanup proof.

## Risks and Guardrails

Primary risks:

1. Ranking signal instability from non-deterministic fallback behavior.
2. UI interpretation drift where ranking appears mandatory instead of advisory.
3. Scope creep into save automation or non-Button 1 surfaces.

Guardrails:

1. Centralize deterministic scoring and bucket rules.
2. Enforce additive-only API policy.
3. Preserve explicit operator approval gate.
4. Preserve manual selection authority.
5. Keep non-goals explicit in design review and implementation checklist.

## Design Verdict

READY FOR DESIGN REVIEW.

This slice is design-only and defines Button 1 ranking runtime wiring boundaries without introducing runtime behavior changes.

## Next Safe Slice

ai-risa-premium-report-factory-button1-ranking-runtime-wiring-design-review-v1

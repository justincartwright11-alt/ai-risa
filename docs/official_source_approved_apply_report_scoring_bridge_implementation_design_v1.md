# official-source-approved-apply-report-scoring-bridge-implementation-design-v1

Status: IMPLEMENTATION DESIGN DRAFT (docs-only)
Date: 2026-04-30
Owner: AI-RISA governance
Predecessor lock: official-source-approved-apply-report-scoring-bridge-design-review-v1 (5a5e9df)

## 1) Implementation Scope
Define a future implementation plan for bridging approved official-source actual results into report-scoring and accuracy-calibration readiness without changing existing runtime behavior in this slice.

This is a planning artifact only. No runtime implementation is authorized by this document.

## 2) Source Artifacts Reviewed
1. docs/official_source_approved_apply_report_scoring_bridge_design_v1.md
2. docs/official_source_approved_apply_report_scoring_bridge_design_review_v1.md

## 3) Locked Baseline Summary
1. operation_id binding complete.
2. operation_id retry/persistence complete.
3. local one-record approved apply proof complete.
4. global ledger mirror complete.
5. read-only global ledger dashboard visibility complete.
6. approved actuals are traceable from local write to global ledger visibility.
7. no scoring rewrite has occurred.

## 4) Proposed Implementation Touchpoints
Future implementation touchpoints are limited to bridge-layer integration points:
1. approved actual result source
2. prediction/report record source
3. local/global ledger trace lookup
4. score outcome builder
5. calibration-readiness status writer or surface
6. focused tests

## 5) Proposed Scoring Bridge Flow
Future bridge flow for one deterministic scoring decision:
1. load one prediction/report record
2. load one approved actual result
3. verify local/global ledger trace
4. compare predicted winner/method/round/confidence against actual
5. produce deterministic score outcome
6. mark scored/unresolved status
7. preserve existing scoring logic boundaries

## 6) Proposed Evidence Fields
1. prediction_report_id
2. local_result_key
3. global_ledger_record_id
4. official_source_reference
5. approved_actual_result
6. predicted_winner_id
7. predicted_method
8. predicted_round
9. confidence
10. resolved_result_status
11. scored
12. score_outcome
13. calibration_notes

## 7) Deterministic Score Outcome Model
A future implementation should classify each scoreable decision into one deterministic outcome:
1. winner_correct
2. method_correct
3. round_exact
4. round_tolerance
5. unresolved
6. mismatch
7. duplicate_conflict

## 8) Failure Handling
Future implementation must define deterministic handling for:
1. approved actual exists but no matching prediction
2. prediction exists but no approved actual
3. fighter/key mismatch
4. method mismatch
5. round mismatch
6. official source ambiguity
7. duplicate approved actual
8. malformed ledger trace

## 9) Boundaries And Guardrails
1. no automatic batch scoring
2. no scoring rewrite
3. no prediction model change
4. no dashboard mutation controls
5. no ledger overwrite
6. no token changes
7. no report-generation changes

## 10) Future Implementation Test Plan
A future implementation slice should be test-gated with at least:
1. one clean scored report
2. one unresolved report
3. one mismatch case
4. one duplicate actual conflict
5. one no-approved-actual case
6. token semantics unchanged
7. ledger state unchanged
8. backend regression remains green

## 11) Explicit Non-Goals
1. No implementation in this slice.
2. No endpoint behavior changes.
3. No token digest semantics changes.
4. No token consume semantics changes.
5. No mutation behavior changes.
6. No dashboard frontend changes.
7. No scoring logic rewrite.
8. No batch, prediction, intake, report-generation, or global ledger behavior changes.
9. No runtime file creation.

## 12) Implementation Readiness Verdict
The report-scoring bridge implementation design is approved only as a planning artifact. Actual implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.

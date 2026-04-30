# official-source-approved-apply-report-scoring-bridge-design-v1

Status: DESIGN DRAFT (docs-only)
Date: 2026-04-30
Owner: AI-RISA governance
Baseline lock: official-source-approved-apply-global-ledger-frontend-archive-lock-v1 (466f4f4)

## 1) Purpose
This design defines a future bridge from approved official-source actual results to report-scoring and accuracy-calibration readiness.

Design intent:
1. Connect approved official-source actuals to the real report-scoring workflow.
2. Define how an approved result becomes scoreable evidence.

This is a design-only boundary. No implementation is authorized in this slice.

## 2) Current Locked State
1. Local approved actual write exists.
2. Global ledger mirror row exists.
3. Read-only dashboard visibility exists for global ledger state.
4. No scoring rewrite has occurred.
5. Current chain is closed and archived at:
   - commit: 466f4f4
   - tag: official-source-approved-apply-global-ledger-frontend-archive-lock-v1

## 3) Proposed Scoring Bridge (Design)
Proposed future flow for a scoreable record:
1. Identify prediction/report record.
2. Identify approved actual result.
3. Verify local/global ledger trace linkage.
4. Compare predicted winner/method/round/confidence against approved actual result.
5. Mark report outcome as scored or unresolved.
6. Surface score status for calibration pipelines.

## 4) Required Evidence Fields
A future implementation should carry and persist these evidence fields for scoring readiness:
1. prediction/report id
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

## 5) Boundaries
The bridge design is constrained as follows:
1. No automatic batch scoring.
2. No scoring rewrite.
3. No prediction model change.
4. No dashboard mutation controls.
5. No ledger overwrite.
6. No token changes.

## 6) Failure Handling (Design Requirements)
Future implementation must define deterministic handling for:
1. Approved actual exists but no matching prediction.
2. Prediction exists but no approved actual.
3. Fighter/key mismatch.
4. Method mismatch.
5. Round mismatch.
6. Official source ambiguity.
7. Duplicate approved actual conflict.

## 7) Future Implementation Test Plan
A future implementation slice should be test-gated at minimum by:
1. One clean scored report.
2. One unresolved report.
3. One mismatch case.
4. One duplicate actual conflict.
5. One no-approved-actual case.
6. Token semantics unchanged.
7. Ledger state unchanged.
8. Backend regression remains green.

## 8) Explicit Non-Goals
1. No implementation in this slice.
2. No scoring behavior changes.
3. No token digest or token consume changes.
4. No mutation behavior changes.
5. No dashboard behavior changes.
6. No endpoint behavior changes.
7. No batch, prediction, intake, or report-generation behavior changes.
8. No global ledger behavior changes.
9. No runtime file generation.

## 9) Final Design Verdict
The report-scoring bridge is approved only as a future design boundary. Implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.

# Report-Scoring Bridge v2 Dashboard Panel Design (Read-Only)

Status: Design Approved Boundary Only  
Date: April 30, 2026  
Slice: official-source-approved-apply-report-scoring-bridge-v2-dashboard-panel-design-v1

---

## 1. Purpose

This document defines a future, read-only dashboard panel design that visualizes the existing report-scoring bridge v2 summary endpoint for operator visibility.

Primary intent:
- Give operators read-only visibility into report-scoring bridge readiness.
- Show scored, unresolved, mismatch, missing, and duplicate_conflict states.
- Improve triage and calibration-readiness inspection without introducing mutation capability.

This is a design-only artifact. No implementation is included.

---

## 2. Locked Baseline Reference

The design starts from the archived, closed chain baseline:
- Commit: 3dc8b3a
- Tag: official-source-approved-apply-report-scoring-bridge-v2-archive-lock-v1

Locked capability already exists and remains unchanged:
- Endpoint: GET /api/operator/report-scoring-bridge/summary
- Top-level contract: ok, generated_at, bridge_available, total_records, latest_records, status_counts, errors
- Record fields: prediction_report_id, local_result_key, global_ledger_record_id, official_source_reference, approved_actual_result, predicted_winner_id, predicted_method, predicted_round, confidence, resolved_result_status, scored, score_outcome, calibration_notes, scoring_bridge_status, generated_at
- Filters: prediction_report_id, local_result_key, limit
- No mutation/write/token behavior in endpoint

---

## 3. Proposed Dashboard Surface

Proposed future UI surface (read-only):
- Report-scoring bridge status panel
- Summary counts block
- Latest records table
- Filter controls (if safe and read-only)
- Error and empty-state banners/cards

### 3.1 Panel Layout Concept

A single dashboard panel section can be organized as:
1. Header: "Report-Scoring Bridge v2"
2. Availability row: bridge_available, generated_at
3. Summary counts: ok / unresolved / conflict / missing
4. Filter row: prediction_report_id, local_result_key, limit
5. Latest records table
6. Edge-state region: empty/errors/warnings

### 3.2 Summary Counts

Panel should display status_counts clearly:
- ok
- unresolved
- conflict
- missing

Optional future display mapping:
- conflict includes duplicate_conflict visibility from score_outcome records
- unresolved shows records waiting for approved actual evidence

### 3.3 Latest Records Table

Panel table should present latest_records in deterministic endpoint order (already sorted by prediction_report_id in backend contract).

### 3.4 Filter Controls (Read-Only)

If included, controls are query-only and non-mutating:
- prediction_report_id exact filter
- local_result_key exact filter
- limit bounded selection

No client-side action may trigger server writes.

### 3.5 Error/Empty-State Display

Panel should render:
- Safe empty state when total_records=0
- errors array contents when present
- bridge unavailable status when bridge_available=false

---

## 4. Read-Only Boundaries (Mandatory)

This future panel must remain read-only.

Disallowed behaviors:
- No scoring mutation
- No approved-apply mutation
- No ledger write
- No token consume
- No approval-token exposure
- No token digest exposure

The panel is visibility-only and cannot alter backend state.

---

## 5. Proposed Displayed Fields

The future panel should display, at minimum, the following existing record fields:
- prediction_report_id
- local_result_key
- global_ledger_record_id
- official_source_reference
- approved_actual_result
- predicted_winner_id
- predicted_method
- predicted_round
- confidence
- resolved_result_status
- scored
- score_outcome
- scoring_bridge_status
- calibration_notes
- generated_at

No additional backend fields are proposed in this design slice.

---

## 6. Operator Workflow (Read-Only)

Intended operator workflow:
1. View bridge availability and recency (bridge_available + generated_at).
2. Inspect latest scored and unresolved records.
3. Identify mismatch and duplicate_conflict cases quickly.
4. Confirm whether a prediction/report has approved actual evidence attached.
5. Use panel insight for calibration readiness assessment, not mutation.

The panel is an observation and triage interface only.

---

## 7. Failure and Edge-State Display Requirements

The future panel should explicitly render and label:
- Missing bridge records
- Safe empty state
- Unresolved actual
- Mismatch
- Duplicate conflict
- Malformed or missing trace/evidence fields
- Endpoint error condition

### 7.1 Suggested UX State Labels

- Empty: "No bridge records available"
- Unresolved: "Awaiting approved actual"
- Mismatch: "Prediction differs from approved actual"
- Duplicate conflict: "Conflicting duplicate ledger traces"
- Error: "Bridge summary unavailable"

These are display-only labels and do not imply any write action.

---

## 8. Security and Governance Guardrails

Mandatory guardrails for any future implementation:
- No mutation controls
- No hidden write buttons/actions
- No approval-token display
- No token digest material display
- No consume-state changes
- No scoring rewrite

Additionally:
- No POST/PUT/PATCH/DELETE action from this panel
- No front-end side effects that alter backend files
- No coupling to approved-apply mutation flow

---

## 9. Future Implementation Test Plan (Gate Criteria)

If and only if future implementation slices are opened, minimum test gates should include:
- Panel loads with safe empty state.
- Panel renders latest_records rows from endpoint.
- Panel renders status_counts values.
- Panel renders mismatch/unresolved/duplicate_conflict visibility states.
- Panel exposes no write controls.
- Endpoint remains read-only throughout panel usage.
- Backend regression remains green.

Optional additional checks:
- Filter query correctness for prediction_report_id, local_result_key, and limit.
- Deterministic row ordering matches endpoint contract.
- Error banner behavior for endpoint failures.

---

## 10. Explicit Non-Goals

This design slice does not include:
- Dashboard implementation
- Backend endpoint changes
- New API fields
- Scoring logic changes
- Batch scoring automation
- Approved-apply behavior changes
- Token digest/consume semantics changes
- Mutation/write controls
- Global ledger write behavior changes
- Prediction, intake, or report-generation behavior changes

This is strictly a design boundary artifact.

---

## 11. Implementation Boundary and Open Condition

Implementation is blocked in this slice.

Future work must proceed only through separate gated slices:
1. Implementation-design slice
2. Implementation slice
3. Test-gated verification slice(s)

No implementation work is authorized by this document.

---

## 12. Final Design Verdict

The report-scoring bridge v2 dashboard panel design is approved only as a future read-only design boundary. Implementation remains blocked until a separate implementation-design and implementation slice are explicitly opened and test-gated.

# official-source-approved-apply-global-ledger-frontend-implementation-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: AI-RISA operator-dashboard governance
Predecessor lock: official-source-approved-apply-global-ledger-frontend-design-review-v1 (613a685)

## 1) Implementation Scope
Define a future implementation planning boundary for read-only frontend/operator dashboard visibility of approved-apply global ledger state.

This is a planning artifact only. No frontend or API implementation is authorized by this document.

## 2) Source Artifacts Reviewed
1. docs/official_source_approved_apply_global_ledger_frontend_design_v1.md
2. docs/official_source_approved_apply_global_ledger_frontend_design_review_v1.md

## 3) Locked Global Ledger Baseline Summary
1. Minimal append-only global ledger helper exists.
2. Approved local success mirrors to global ledger only after local write success.
3. Guard-denied attempts are not mirrored as approved global result rows.
4. Local operation_id audit behavior remains separate and intact.
5. operation_id remains separate from internal mutation UUID.
6. Token consume remains tied to internal mutation UUID.
7. operation_id remains excluded from token digest material.
8. Duplicate global ledger records are detected deterministically.
9. Same-payload duplicate returns deterministic already-recorded behavior.
10. Conflicting duplicate returns explicit conflict behavior.
11. Conflict detection happens before local write.
12. Global ledger write failure returns explicit failure without corrupting local state.

## 4) Proposed Implementation Touchpoints
1. Backend read-only global ledger summary endpoint.
2. Backend ledger row loader/helper.
3. Dashboard read-only panel.
4. Template/static asset touchpoint if applicable.
5. Backend tests.
6. Frontend/render tests if existing project pattern supports them.

## 5) Proposed Read-Only API Contract
1. ok
2. generated_at
3. ledger_available
4. total_rows
5. latest_rows
6. status_counts
7. errors

## 6) Proposed Latest Row Fields
1. global_ledger_record_id
2. local_result_key
3. event_id
4. bout_id
5. official_source_reference
6. approved_actual_result
7. operation_id
8. deterministic_status
9. timestamp_utc
10. local_audit_reference

## 7) Read-Only Dashboard Behavior
1. Display latest global ledger rows.
2. Display status counts.
3. Show empty-state safely.
4. Show conflict/already-recorded/failure states clearly.
5. No write controls.
6. No approval-token exposure.
7. No token digest material exposure.

## 8) Failure And Edge-State Handling
1. Missing ledger file.
2. Malformed ledger row.
3. Empty ledger.
4. Duplicate/conflict status rows.
5. Global ledger write failure state.
6. Guard-deny not mirrored as approved row.

Handling requirements:
1. Never break the read-only endpoint response contract.
2. Return safe defaults for missing/empty data.
3. Surface malformed-row conditions in errors while continuing to render valid rows.

## 9) Security/Governance Guardrails
1. No mutation from frontend.
2. No token consume from frontend.
3. No approval-token display.
4. No token digest material display.
5. No global ledger overwrite.
6. No scoring rewrite.

## 10) Future Implementation Test Plan
1. Read-only endpoint returns safe empty state.
2. Read-only endpoint returns latest rows deterministically.
3. Malformed row is reported without breaking response.
4. Dashboard panel renders latest rows.
5. Dashboard panel renders empty state.
6. Dashboard panel exposes no write controls.
7. Backend regression remains green.

## 11) Explicit Non-Goals
1. No implementation in this slice.
2. No new API behavior implementation in this slice.
3. No frontend write/mutation controls.
4. No approval-token or token digest material exposure.
5. No token consume behavior changes.
6. No scoring logic changes.
7. No batch behavior changes.
8. No prediction model changes.
9. No intake behavior changes.
10. No report-generation behavior changes.
11. No runtime file creation.

## 12) Implementation Readiness Verdict
The global ledger frontend implementation design is approved only as a planning artifact.

Actual frontend/API implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.

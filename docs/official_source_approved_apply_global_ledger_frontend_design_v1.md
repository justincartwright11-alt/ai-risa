# official-source-approved-apply-global-ledger-frontend-design-v1

Status: DRAFT (docs-only)
Date: 2026-04-30
Owner: AI-RISA operator-dashboard governance
Predecessor lock: official-source-approved-apply-global-ledger-archive-lock-v1 (d752a1a)

## 1) Purpose Of Frontend/Operator Visibility
Define a future read-only dashboard visibility boundary for the approved-apply global ledger state so operators can inspect approved-result traceability without changing the locked mutation path.

The purpose is operational visibility only, not approval or mutation control.

## 2) Why Visibility Must Be Read-Only First
The global ledger chain is currently locked as an append-only backend foundation.

Read-only visibility must come first because it preserves:
1. the existing approved local write path as the only mutation authority
2. the locked separation between operation_id and internal mutation UUID
3. unchanged token digest and token consume semantics
4. deterministic backend-owned ledger conflict and replay behavior

A frontend visibility slice must observe the ledger, not control it.

## 3) Proposed Dashboard Surfaces
1. Global ledger status panel.
2. Latest approved global ledger rows.
3. Conflict and already-recorded indicators.
4. Local audit reference display.
5. operation_id display.
6. Internal mutation UUID display only if safe for operator diagnostics.

## 4) Read-Only Boundaries
1. Frontend must not write global ledger rows.
2. Frontend must not consume tokens.
3. Frontend must not trigger mutation.
4. Frontend must not bypass approval workflow.
5. Frontend must not rewrite scoring logic.

## 5) Proposed Data Fields
1. global_ledger_record_id
2. local_result_key
3. event_id
4. bout_id
5. official_source_reference
6. approved_actual_result
7. operation_id
8. deterministic_status
9. timestamp
10. local_audit_reference

## 6) Operator Workflow
1. View latest global ledger state.
2. Verify one approved result trace.
3. Distinguish success, conflict, already-recorded, and failure states.
4. Confirm linkage from local approved apply to the global ledger row.

## 7) Failure And Edge-State Display
The future design should support read-only display for:
1. Global ledger write failure.
2. Duplicate conflict.
3. Already recorded.
4. Missing official source reference.
5. Guard deny not mirrored as approved row.

## 8) Security And Governance Guardrails
1. No mutation from frontend.
2. No approval-token exposure.
3. No token digest material exposure.
4. No consume-state mutation.
5. No global ledger overwrite.

## 9) Future Implementation Test Plan
1. Read-only panel loads.
2. Latest global ledger row displayed deterministically.
3. Conflict state displayed.
4. Already-recorded state displayed.
5. Missing or empty ledger handled safely.
6. No write actions available.
7. Backend regression remains green.

## 10) Explicit Non-Goals
1. No implementation in this slice.
2. No frontend mutation controls.
3. No new API behavior in this slice.
4. No scoring rewrite.
5. No batch behavior change.
6. No prediction model change.
7. No intake behavior change.
8. No report-generation behavior change.
9. No runtime file creation.

## 11) Final Design Verdict
The global ledger frontend visibility design is approved only as a future read-only design boundary.

Implementation remains blocked until a separate implementation slice is explicitly opened and test-gated.

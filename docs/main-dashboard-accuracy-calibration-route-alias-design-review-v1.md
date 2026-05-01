# Main Dashboard Accuracy Calibration Route Alias Design Review v1

Status: Approved (docs-only design boundary)
Slice: main-dashboard-accuracy-calibration-route-alias-design-review-v1
Date: 2026-05-01
Review type: Design review only (no implementation)

## 1. Review Scope

This review validates the design boundary for resolving the main dashboard
accuracy calibration route mismatch and determines implementation readiness
for a future, explicitly opened implementation slice.

This review is strictly docs-only and does not authorize direct code changes
inside this slice.

## 2. Source Artifact Reviewed

Reviewed exactly once:
- docs/main-dashboard-accuracy-calibration-route-alias-design-v1.md

## 3. Confirmed Diagnosis

Confirmed statements:
- Main dashboard calls `/api/operator/accuracy-calibration-review`.
- Backend currently exposes `/api/operator/run-calibration-review`.
- Missing route returns `{"error":"Operator endpoint not found","ok":false}`.
- Approved-result pipeline routes and Advanced Dashboard accuracy surfaces are healthy.

Diagnosis conclusion:
- The observed error is an older main-dashboard route mismatch, not a failure
  of the approved-result pipeline.

## 4. Option Review

Option A: Frontend rewiring
- Change main dashboard caller to `/api/operator/run-calibration-review`.

Benefits:
- Simple direct wiring fix.

Costs/Risks:
- Breaks backward compatibility for any client/tooling still posting to
  `/api/operator/accuracy-calibration-review`.
- Couples fix to frontend deployment timing.

Option B: Backend alias (preferred)
- Add `POST /api/operator/accuracy-calibration-review` as a backward-compatible alias.
- Alias delegates to existing `/api/operator/run-calibration-review` behavior.

Benefits:
- Preserves current main-dashboard behavior.
- Preserves compatibility for existing callers.
- Lowest behavioral risk under freeze governance.

Costs/Risks:
- One additional route alias to maintain.

## 5. Recommended Approach

Approved recommendation:
- Implement backend alias at `/api/operator/accuracy-calibration-review`.
- Alias must delegate to existing `/api/operator/run-calibration-review` behavior.

Design guardrails:
- No scoring rewrite.
- No token digest changes.
- No token consume changes.
- No mutation behavior change beyond current calibration review behavior.
- No changes to batch, prediction, intake, report generation, or global ledger behavior.

## 6. Required Coverage Checklist

- Problem statement: PASS
- Evidence: PASS
- Option tradeoff: PASS
- Recommended backend alias: PASS
- Acceptance criteria: PASS
- Test plan: PASS
- Risk: PASS
- Rollback: PASS
- Freeze compliance: PASS
- Final design verdict: PASS

Coverage result: COMPLETE.

## 7. Pass/Fail Review Table

| Review Area | Result | Notes |
| --- | --- | --- |
| Problem definition | PASS | Route mismatch is clear and bounded. |
| Evidence quality | PASS | Endpoint behavior and payload mismatch are explicit. |
| Option analysis | PASS | Frontend rewiring vs backend alias evaluated. |
| Recommended direction | PASS | Backend alias selected for compatibility. |
| Acceptance criteria | PASS | Observable, testable, and bounded. |
| Testability | PASS | Alias parity and regression checks are defined. |
| Risk controls | PASS | Delegation to single canonical handler required. |
| Rollback safety | PASS | Revert path is clear and low impact. |
| Freeze compliance | PASS | Docs-only boundary preserved in this slice. |

## 8. Implementation Readiness Assessment

Readiness state: READY FOR IMPLEMENTATION SLICE (not implementation in this slice).

Conditions for readiness:
- Separate implementation slice must be explicitly opened.
- Focused tests must be added and passed before release lock.
- No behavior drift outside the alias contract is permitted.

## 9. Risks and Guardrails for Future Implementation Slice

Primary risk:
- Alias and canonical routes diverge if logic is duplicated.

Mandatory guardrails:
- Alias must delegate to the canonical calibration handler.
- Keep one response construction path.
- Preserve operator error envelope conventions.
- Preserve all frozen approved-result pipeline surfaces.

## 10. Explicit Non-Goals Confirmation

This design review does not approve or include:
- Any code edits.
- Any test edits.
- Any endpoint behavior changes in this slice.
- Any dashboard UI changes in this slice.
- Any token semantics changes.
- Any mutation/scoring logic changes.
- Any new feature beyond defining the future alias implementation boundary.

## 11. Final Review Verdict

Verdict: APPROVED as a docs-only design boundary.

Implementation remains blocked until a separate implementation slice is
explicitly opened and test-gated.

## 12. Freeze Compliance Record

This artifact is docs-only.
No implementation occurred in this slice.

# Main Dashboard Accuracy Calibration Route Alias Implementation Design v1

Status: Approved as planning artifact only (docs-only)
Slice: main-dashboard-accuracy-calibration-route-alias-implementation-design-v1
Date: 2026-05-01
Mode: Implementation planning only; no implementation in this slice

## 1. Implementation Scope

Define the implementation plan for a minimal backend route alias that resolves the
main dashboard calibration endpoint mismatch without changing existing behavior.

Planned implementation boundary for a future implementation slice:
- Add one backward-compatible backend alias route.
- Delegate to existing calibration review behavior.
- Preserve all existing contracts and safety semantics.

This slice is documentation only.

## 2. Source Artifacts Reviewed

Reviewed once before writing:
- docs/main-dashboard-accuracy-calibration-route-alias-design-v1.md
- docs/main-dashboard-accuracy-calibration-route-alias-design-review-v1.md

## 3. Locked Diagnosis

Locked facts:
- Main dashboard calls `/api/operator/accuracy-calibration-review`.
- Backend currently exposes `/api/operator/run-calibration-review`.
- Missing route returns `{"error":"Operator endpoint not found","ok":false}`.
- Approved-result pipeline, report-scoring bridge, and advanced dashboard routes are healthy.

Diagnosis lock conclusion:
- This is a route naming compatibility mismatch on the main dashboard path.
- This is not an approved-result pipeline defect.

## 4. Recommended Implementation

For a separate, explicitly opened implementation slice:
- Add backend POST route alias:
  - `/api/operator/accuracy-calibration-review`
- Alias delegates to existing `/api/operator/run-calibration-review` behavior.
- Preserve response contract and calibration review semantics.
- Do not change main dashboard frontend wiring.

## 5. Proposed Touchpoints

Only these files should be touched in the future implementation slice:
- `operator_dashboard/app.py`
- `operator_dashboard/test_app_backend.py`

No other files are planned touchpoints.

## 6. Proposed Route Behavior

Alias contract requirements:
- Accepts HTTP POST.
- Returns same response behavior/shape as `/api/operator/run-calibration-review`.
- Must not add new scoring logic.
- Must not change accuracy comparison calculations.
- Must not alter approved-result pipeline behavior.

Implementation shape requirement:
- Alias should delegate to the canonical calibration handler (single source of truth).

## 7. Required Tests (for future implementation slice)

Required validation set:
- Existing `/api/operator/run-calibration-review` route still works.
- New `/api/operator/accuracy-calibration-review` alias returns HTTP 200.
- Alias response matches existing route shape.
- Alias does not return operator endpoint 404.
- Main dashboard referenced path is now backed by a real route.
- Backend regression remains green.

## 8. Runtime-Noise Handling

Runtime noise exclusion rule for future implementation/test execution:
- Flask health log and intake tracking artifacts must never be committed.
- If generated, clean before commit:
  - `git restore -- ops/runtime_health_log.jsonl`
  - `git clean -fd -- ops/intake_tracking`

## 9. Boundaries and Guardrails

Mandatory boundaries:
- No frontend rewrite.
- No scoring rewrite.
- No token digest changes.
- No token consume changes.
- No approved-apply behavior changes.
- No global ledger changes.
- No batch/report-generation behavior changes.
- No mutation behavior changes beyond existing calibration review behavior.

## 10. Explicit Non-Goals

This implementation design does not include:
- Direct code implementation in this slice.
- Direct test implementation in this slice.
- Any new feature beyond alias compatibility restoration.
- Any change to dashboard visuals or controls.
- Any change to batch, prediction, intake, report generation, or ledger flows.

## 11. Implementation Readiness Verdict

Verdict: APPROVED only as a planning artifact.

Actual route implementation remains blocked until a separate implementation slice is
explicitly opened and test-gated.

## 12. Freeze Compliance Record

This slice is docs-only.
No code, tests, endpoints, runtime behavior, frontend behavior, token semantics,
mutation behavior, scoring logic, or pipeline behavior were changed in this slice.

# Main Dashboard Accuracy Calibration Route Alias Design v1

Status: Draft design slice (docs-only)
Slice: main-dashboard-accuracy-calibration-route-alias-design-v1
Date: 2026-05-01
Mode: Read-only diagnosis completed; no code changes in this slice

## 1. Objective

Resolve a main-dashboard route mismatch that causes an operator 404 payload for the
accuracy calibration button, while preserving the frozen Approved Result Pipeline v1 baseline.

## 2. Confirmed Runtime Diagnosis

Observed behavior:
- Main dashboard loads and most widgets are healthy.
- Advanced Dashboard accuracy surfaces are healthy.
- Report-scoring bridge and global-ledger summary operator endpoints are healthy.

Confirmed failing call:
- `POST /api/operator/accuracy-calibration-review`
- Response: `{"error":"Operator endpoint not found","ok":false}`

Root cause:
- Main dashboard (`operator_dashboard/templates/index.html`) calls:
  - `/api/operator/accuracy-calibration-review`
- Backend (`operator_dashboard/app.py`) exposes:
  - `/api/operator/run-calibration-review`
- No backend route currently exists for `/api/operator/accuracy-calibration-review`.

## 3. Scope

In scope for follow-up implementation slice:
- Restore compatibility for the main dashboard calibration button without changing
  approved-result pipeline behavior.
- Keep all existing safety and approval semantics unchanged.

Out of scope:
- Any mutation-flow behavior changes.
- Any report-scoring bridge logic changes.
- Any confidence-calibration algorithm changes.

## 4. Solution Options

Option A: Frontend rewiring only
- Change main dashboard button call from
  `/api/operator/accuracy-calibration-review` to `/api/operator/run-calibration-review`.

Pros:
- Minimal backend footprint.

Cons:
- Existing browser-side assumptions/bookmarks/scripts expecting the old endpoint may break.
- Less backward-compatible if external tooling calls the old route.

Option B: Backend alias (recommended)
- Add a backward-compatible operator route:
  - `POST /api/operator/accuracy-calibration-review`
- Alias behavior delegates to existing handler logic for
  `/api/operator/run-calibration-review`.

Pros:
- Preserves current frontend behavior without requiring immediate UI edits.
- Supports backward compatibility for existing clients.
- Lowest user-visible change risk under frozen baseline governance.

Cons:
- Adds one additional endpoint alias to maintain.

## 5. Recommended Direction

Choose Option B (backend alias) as the first fix step.

Rationale:
- Lowest operational risk.
- Maintains compatibility with existing main-dashboard wiring.
- Avoids coupling this recovery to frontend rollout timing.

## 6. Proposed Compatibility Contract

Request:
- Method: `POST`
- Path: `/api/operator/accuracy-calibration-review`
- Body: same as current `run-calibration-review` usage (empty JSON acceptable)

Response:
- Exactly match `run-calibration-review` envelope shape and status behavior.
- Preserve existing error envelope style for operator endpoints.

## 7. Acceptance Criteria

Functional:
- Main dashboard button no longer returns operator 404.
- `POST /api/operator/accuracy-calibration-review` returns same successful payload contract
  as `POST /api/operator/run-calibration-review`.
- Existing route `/api/operator/run-calibration-review` remains unchanged.

Regression/compatibility:
- `/api/system/health` unchanged.
- `/api/accuracy/comparison-summary` unchanged.
- `/api/operator/report-scoring-bridge/summary` unchanged.
- `/api/operator/actual-result-lookup/global-ledger-summary` unchanged.

Governance:
- No behavior drift in approved-result pipeline surfaces.
- Tests must include route alias contract parity.

## 8. Test Plan (for follow-up implementation slice)

Add focused backend tests to verify:
- Alias route exists and returns non-404.
- Alias and canonical route return equivalent schema keys and `ok` behavior.
- Operator error envelope remains intact for unsupported methods.

Add light UI contract check to verify main dashboard button path remains supported.

## 9. Risk Assessment

Primary risk:
- Divergence between alias and canonical handler if duplicated logic is introduced.

Mitigation:
- Implement alias as direct delegation to canonical handler function.
- Keep one source of truth for calibration review response construction.

## 10. Rollback Strategy

If unexpected behavior appears after implementation slice:
- Remove alias route and revert to baseline tag state.
- Keep advanced dashboard as operational path for accuracy-ledger surfaces.

## 11. Freeze Compliance Record

This document opens a docs-only design slice.
No code, test, or runtime behavior was changed by this slice.

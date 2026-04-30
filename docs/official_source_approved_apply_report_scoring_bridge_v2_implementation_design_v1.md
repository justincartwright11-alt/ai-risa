# Official Source Approved Apply Report Scoring Bridge — V2 Implementation Design v1

## 1. Implementation Scope

This document is a docs-only implementation design plan for the report-scoring bridge v2 read-only endpoint. **No implementation is performed in this slice.** The purpose is to define the concrete route signature, query parameters, response contract, record field set, helper wiring plan, read-only behavior rules, failure handling, test plan, boundaries, and guardrails that will govern the implementation slice when it is opened. This document supersedes the higher-level data contract in the v2 design document with specific, actionable implementation detail.

---

## 2. Source Artifacts Reviewed

| File | Commit | Tag |
|---|---|---|
| `docs/official_source_approved_apply_report_scoring_bridge_v2_design_v1.md` | `ef94540` | `official-source-approved-apply-report-scoring-bridge-v2-design-v1` |
| `docs/official_source_approved_apply_report_scoring_bridge_v2_design_review_v1.md` | `4dca0a3` | `official-source-approved-apply-report-scoring-bridge-v2-design-review-v1` |

Both source artifacts were read in full before this document was written. The design review confirmed all required sections pass. Implementation readiness was assessed as ready to proceed to implementation-design slice.

---

## 3. Locked Baseline Summary

The following capabilities are complete and locked. The implementation slice must not regress or modify any of these:

| Capability | Status |
|---|---|
| `operation_id` binding | COMPLETE |
| Retry / persistence | COMPLETE |
| Local one-record approved-apply proof | COMPLETE |
| Global ledger mirror | COMPLETE |
| Read-only global ledger dashboard visibility | COMPLETE |
| Report-scoring bridge v1 (`_build_official_source_approved_apply_report_scoring_bridge`) | COMPLETE |
| Deterministic bridge helper exists | COMPLETE |
| v2 recommended direction: read-only endpoint | APPROVED IN DESIGN + REVIEW |
| No scoring rewrite has occurred | CONFIRMED |

---

## 4. Proposed Route

| Property | Value |
|---|---|
| Method | `GET` |
| Path | `/api/operator/report-scoring-bridge/summary` |
| Auth | Same auth guard as existing operator endpoints |
| Write path | NONE — GET only |
| Side effects | NONE — no ledger write, no token consume, no mutation |

The route is a thin read-only wrapper around the existing deterministic bridge helper. It must not be registered as POST, PUT, PATCH, or DELETE. No write handler may be added alongside it in this slice.

---

## 5. Proposed Query Parameters

All query parameters are optional. The endpoint must return a valid structured response when none are provided (safe empty state).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `prediction_report_id` | string | No | Filter results to records matching this prediction/report ID |
| `local_result_key` | string | No | Filter results to records matching this local result key |
| `limit` | integer | No | Cap the number of records returned in `latest_records`. Default: 20. Max: 100. If omitted, default applies. |

Parameter validation rules:
- `prediction_report_id` and `local_result_key` are treated as exact-match filters.
- If both are provided, both filters apply (AND logic).
- `limit` must be a positive integer between 1 and 100. Values outside this range must be rejected with a structured error response (HTTP 400).
- Unknown query parameters must be ignored silently.

---

## 6. Proposed Response Contract

The endpoint must always return a JSON object with the following top-level fields. No field may be omitted, even when the result set is empty.

| Field | Type | Description |
|---|---|---|
| `ok` | boolean | `true` if the endpoint processed the request without a fatal error; `false` if a fatal error occurred |
| `generated_at` | string (ISO 8601) | Timestamp of response generation. Read-only. Not persisted. |
| `bridge_available` | boolean | `true` if at least one bridge record is available for the current filter; `false` otherwise |
| `total_records` | integer | Total count of bridge records matching the current filter |
| `latest_records` | array of record objects | Up to `limit` bridge records, ordered by `prediction_report_id` ascending (deterministic) |
| `status_counts` | object | Count of records by `scoring_bridge_status` value: `{ "ok": n, "unresolved": n, "conflict": n, "missing": n }` |
| `errors` | array of strings | List of non-fatal error messages encountered during processing. Empty array if none. |

When `ok` is `false`, `latest_records` must be an empty array and `errors` must contain at least one message describing the fatal error.

---

## 7. Proposed Record Fields

Each object in `latest_records` must contain exactly the following fields. No field may be omitted, even when its value is null:

| Field | Type | Nullable | Description |
|---|---|---|---|
| `prediction_report_id` | string | No | Identifier for the prediction/report record |
| `local_result_key` | string | No | Local result key for the approved actual result row |
| `global_ledger_record_id` | string | Yes | Global ledger trace row identifier; null if no trace row |
| `official_source_reference` | string | Yes | Reference to the official source record; null if absent |
| `approved_actual_result` | string | Yes | The approved actual result value; null if unresolved |
| `predicted_winner_id` | string | No | The predicted winner identifier |
| `predicted_method` | string | No | The predicted method |
| `predicted_round` | integer | No | The predicted round |
| `confidence` | float | No | Confidence value for the prediction |
| `resolved_result_status` | string | No | The resolved result status |
| `scored` | boolean | No | Whether the record is scored |
| `score_outcome` | string | No | Deterministic score outcome label (see Section 7.1) |
| `calibration_notes` | string | Yes | Notes for calibration audit trail; null if absent |
| `scoring_bridge_status` | string | No | Endpoint-level status (see Section 7.2) |
| `generated_at` | string (ISO 8601) | No | Timestamp of record generation. Same as response-level `generated_at`. Not persisted. |

### 7.1 Score Outcome Values

| Value | Condition |
|---|---|
| `winner_correct` | Predicted winner matches approved actual result winner |
| `method_correct` | Predicted method matches approved actual result method |
| `round_exact` | Predicted round exactly matches approved actual result round |
| `round_tolerance` | Predicted round is within tolerance of approved actual result round |
| `unresolved` | Approved actual result is absent or not yet resolved |
| `mismatch` | Prediction does not match approved actual result on any scored dimension |
| `duplicate_conflict` | Multiple conflicting ledger trace rows detected |

### 7.2 Scoring Bridge Status Values

| Value | Condition |
|---|---|
| `ok` | Bridge record generated; scored or deterministically unresolved |
| `unresolved` | Approved actual result absent or not yet resolved |
| `conflict` | Duplicate ledger trace or duplicate approved actual detected |
| `missing` | Prediction/report record or approved actual row not found |

---

## 8. Helper Wiring Plan

The implementation slice must wire the endpoint to the existing bridge helper as follows:

| Wiring Rule | Detail |
|---|---|
| Helper to reuse | `_build_official_source_approved_apply_report_scoring_bridge` in `operator_dashboard/app.py` |
| Helper modification | FORBIDDEN. The helper must be called as-is, with no changes to its signature, logic, or return value. |
| Mutation | FORBIDDEN. The helper must not be called in a context that writes to any store. |
| Ledger writes | FORBIDDEN. No global ledger trace row may be created, updated, or deleted by this endpoint. |
| Token consume | FORBIDDEN. No token consume operation may be triggered. |
| Token digest | FORBIDDEN. No token digest operation may be triggered. |
| Approved-apply mutation path | FORBIDDEN. The approved-apply guard mutation path must not be called. |
| Response assembly | The endpoint assembles the top-level response object from the helper's output per the contract in Section 6. |
| Ordering | `latest_records` must be ordered by `prediction_report_id` ascending. This order is deterministic and must not vary between calls for the same input. |
| `generated_at` source | Use the current UTC timestamp at the time of response assembly. Do not read it from any store. |

---

## 9. Read-Only Behavior

| Behavior | Rule |
|---|---|
| Safe empty state | When no records match the filter (or no records exist), the endpoint must return `ok: true`, `bridge_available: false`, `total_records: 0`, `latest_records: []`, `status_counts: { "ok": 0, "unresolved": 0, "conflict": 0, "missing": 0 }`, `errors: []`. |
| Deterministic record ordering | `latest_records` is always ordered by `prediction_report_id` ascending. Identical inputs must produce identical output. |
| Filter by `prediction_report_id` | When provided, only records with a matching `prediction_report_id` are included. Non-matching records are silently excluded. |
| Filter by `local_result_key` | When provided, only records with a matching `local_result_key` are included. Non-matching records are silently excluded. |
| Mismatch exposure | Records with `score_outcome: mismatch` must appear in `latest_records` and be counted in `status_counts.ok` (since `scoring_bridge_status` is `ok` for mismatch). |
| Unresolved exposure | Records with `score_outcome: unresolved` must appear in `latest_records` and be counted in `status_counts.unresolved`. |
| Duplicate conflict exposure | Records with `score_outcome: duplicate_conflict` must appear in `latest_records` and be counted in `status_counts.conflict`. |
| Malformed source row tolerance | If a source row is malformed in a non-fatal way (e.g., missing optional field), the record must appear in `latest_records` with `scoring_bridge_status: missing` or `conflict` as appropriate, and the issue must be appended to `errors`. The endpoint must not crash on malformed rows. |

---

## 10. Failure Handling

Each failure state must be handled deterministically. The endpoint must return HTTP 200 with a structured JSON body for all expected failure cases. HTTP 500 is only permitted for truly unexpected runtime errors.

| Failure | `ok` | `scoring_bridge_status` | `scored` | `score_outcome` | `errors` |
|---|---|---|---|---|---|
| Missing prediction/report record | `true` | `missing` | `false` | `unresolved` | empty |
| Missing approved actual | `true` | `unresolved` | `false` | `unresolved` | empty |
| Malformed global ledger trace | `true` | `conflict` | `false` | `duplicate_conflict` | non-fatal message appended |
| Duplicate approved actual | `true` | `conflict` | `false` | `duplicate_conflict` | non-fatal message appended |
| Duplicate ledger trace | `true` | `conflict` | `false` | `duplicate_conflict` | non-fatal message appended |
| Mismatch result | `true` | `ok` | `true` | `mismatch` | empty |
| Unresolved result | `true` | `unresolved` | `false` | `unresolved` | empty |
| Invalid `limit` parameter | `false` | N/A | N/A | N/A | HTTP 400, structured error |
| Fatal runtime error | `false` | N/A | N/A | N/A | HTTP 500 permitted |

All failure responses that produce a record object must include the full 15-field record set. No field may be omitted.

---

## 11. Future Implementation Test Plan

The following tests must be written and must pass before the implementation slice is considered complete. This list extends and refines the test plan from the v2 design document:

| Test | Description | Expected Result |
|---|---|---|
| `test_bridge_v2_endpoint_safe_empty_state` | Call endpoint with no records and no filters | `ok: true`, `bridge_available: false`, `total_records: 0`, `latest_records: []` |
| `test_bridge_v2_endpoint_clean_scored_record_visible` | Call endpoint with one clean matched record | Record present in `latest_records`, `scored: true`, `scoring_bridge_status: ok` |
| `test_bridge_v2_endpoint_unresolved_record_visible` | Call endpoint with one unresolved record | Record present, `scored: false`, `scoring_bridge_status: unresolved`, `score_outcome: unresolved` |
| `test_bridge_v2_endpoint_mismatch_visible` | Call endpoint with one mismatch record | Record present, `scored: true`, `scoring_bridge_status: ok`, `score_outcome: mismatch` |
| `test_bridge_v2_endpoint_duplicate_conflict_visible` | Call endpoint with duplicate ledger trace | Record present, `scored: false`, `scoring_bridge_status: conflict`, `score_outcome: duplicate_conflict` |
| `test_bridge_v2_endpoint_filter_by_prediction_report_id` | Call endpoint with `prediction_report_id` filter | Only matching record(s) returned; non-matching records excluded |
| `test_bridge_v2_endpoint_filter_by_local_result_key` | Call endpoint with `local_result_key` filter | Only matching record(s) returned; non-matching records excluded |
| `test_bridge_v2_endpoint_exposes_no_mutation_behavior` | Call endpoint and verify no store modification | No ledger row, approved actual, or token state is changed |
| `test_bridge_v2_endpoint_token_semantics_unchanged` | Call endpoint and verify token digest and consume state | Token digest and consume counts identical before and after call |
| `test_bridge_v2_endpoint_backend_regression_green` | Run full backend regression suite after implementation | 193 or more tests passing; no regressions |

All tests must be focused and read-only. No test may write to the ledger, mutate an approved actual record, or consume a token.

---

## 12. Boundaries and Guardrails

| Boundary | Rule |
|---|---|
| Route method | GET only. No POST, PUT, PATCH, or DELETE. |
| Helper modification | The v1 bridge helper must not be changed in any way. |
| Ledger writes | Strictly forbidden. No row created, updated, or deleted. |
| Token pipeline | Strictly isolated. No digest, consume, or mutation triggered. |
| Approved-apply guard | Must not be bypassed, called, or modified. |
| Dashboard frontend | No HTML, JS, or CSS changes in this slice. |
| Batch / scheduled invocation | Not permitted in this slice. |
| Persistent storage | Not permitted in this slice. `generated_at` is computed at response time only. |
| Score outcome enum | Exactly 7 values. No new values added in this slice. |
| `scoring_bridge_status` enum | Exactly 4 values (`ok`, `unresolved`, `conflict`, `missing`). No new values added. |
| Regression gate | Backend regression suite must remain at or above 193 tests passing. |

---

## 13. Explicit Non-Goals

The following are not goals of the v2 implementation slice:

- Writing scored results to any persistent store
- Adding new score dimensions beyond the existing 7 outcomes
- Integrating bridge output into exported reports
- Adding a calibration summary export feature
- Adding a dashboard calibration-readiness panel
- Modifying the approved-apply guard or token pipeline
- Modifying the global ledger mirror or its read-only dashboard panel
- Modifying batch, prediction, intake, or report-generation behavior
- Providing a write or mutation endpoint
- Providing automatic or scheduled batch scoring
- Changing any existing test or endpoint behavior

---

## 14. Implementation Readiness Verdict

**The report-scoring bridge v2 implementation design is approved only as a planning artifact for a read-only endpoint.**

The route, query parameters, response contract, record fields, helper wiring plan, read-only behavior rules, failure handling, and test plan are all fully specified. The implementation slice can be opened directly from this document without further design work.

**Actual endpoint implementation remains blocked** until the following slices are completed in order:

1. `official-source-approved-apply-report-scoring-bridge-v2-design-v1` — COMPLETE
2. `official-source-approved-apply-report-scoring-bridge-v2-design-review-v1` — COMPLETE
3. *(this document)* `official-source-approved-apply-report-scoring-bridge-v2-implementation-design-v1` — COMPLETE
4. `official-source-approved-apply-report-scoring-bridge-v2-implementation-design-review-v1` — NEXT SAFE SLICE
5. `official-source-approved-apply-report-scoring-bridge-v2-implementation-v1` — BLOCKED until slice 4 is approved
6. `official-source-approved-apply-report-scoring-bridge-v2-final-review-v1`
7. `official-source-approved-apply-report-scoring-bridge-v2-release-manifest-v1`
8. `official-source-approved-apply-report-scoring-bridge-v2-archive-lock-v1`

No code, test, or endpoint changes are permitted until slice 4 (implementation-design-review) is approved.

---

*Implementation design issued: 2026-04-30*
*Chain: official-source-approved-apply-report-scoring-bridge-v2*
*Slice version: implementation-design-v1*
*Implementation status: BLOCKED — implementation-design-review slice not yet opened*

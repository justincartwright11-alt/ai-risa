# Official Source Approved Apply Report Scoring Bridge — V2 Design v1

## 1. Purpose of v2

This document is a docs-only design boundary for the next safe expansion of the approved official-source actual result to report-scoring bridge. **No implementation is performed in this slice.** The purpose is to decide what the bridge should become next, justify the recommended direction, define the proposed data contract, establish boundaries, describe failure handling, and define the future test plan. Implementation is blocked until a separate implementation slice is explicitly opened and test-gated.

**Source locked baseline:**
- Commit: `e68e439`
- Tag: `official-source-approved-apply-report-scoring-bridge-archive-lock-v1`

---

## 2. Locked Capabilities (v1 Baseline)

The following capabilities are complete and locked. v2 must not regress or modify any of these:

1. `operation_id` binding — complete
2. Retry / persistence — complete
3. Local one-record approved-apply proof — complete
4. Global ledger mirror — complete
5. Read-only global ledger dashboard visibility — complete
6. Report-scoring bridge — complete
7. Deterministic bridge helper exists — complete
8. Bridge links one prediction/report record, one approved actual row, and one global ledger trace row — complete
9. No endpoint wiring changed in v1
10. No dashboard frontend changed in v1
11. No scoring rewrite occurred in v1

---

## 3. Candidate v2 Directions

The following expansion directions are considered for v2. All are currently **unimplemented** and blocked:

| # | Direction | Description |
|---|---|---|
| A | **Read-only report-scoring bridge endpoint** | Expose the deterministic bridge helper via a read-only API endpoint. No write path. Returns a bridge record for a given prediction/report ID. |
| B | Dashboard calibration-readiness panel | Add a read-only frontend panel that displays scored vs. unresolved counts, outcome distribution, and calibration notes per report batch. |
| C | Persistent scored-result ledger | Write scored bridge records to a persistent store (database table or file-backed ledger) for historical audit. |
| D | Additional score dimensions | Extend the score outcome model with new dimensions (e.g., `partial_credit`, `confidence_band`, `elapsed_rounds`). |
| E | Report-output integration | Feed bridge results into the report generation pipeline so scored outcomes appear in exported reports. |
| F | Calibration summary export | Export a structured calibration summary (CSV or JSON) of all scored bridge records for external analysis. |

---

## 4. Recommended v2 Direction

**Direction A: Read-only report-scoring bridge endpoint** is the recommended primary direction for v2.

### Justification

1. **Minimal surface area.** A read-only endpoint adds one route with no mutation, no ledger write, and no token change. It is the smallest safe next step.
2. **Enables downstream consumers.** Dashboard panels (Direction B), export tools (Direction F), and report integration (Direction E) all require a stable API contract before they can be built. A locked endpoint establishes that contract.
3. **Does not require schema changes.** The v1 bridge helper already returns all required evidence fields. The endpoint is a thin wrapper.
4. **Testable in isolation.** A read-only endpoint can be fully covered by focused backend tests without touching frontend, scoring logic, or the ledger.
5. **Sequencing discipline.** Directions B–F all logically depend on a stable bridge API. Opening any of them before the endpoint exists would require each to embed its own ad-hoc bridge call, creating divergence.

**Other directions deferred:**
- B (dashboard panel) depends on A being available.
- C (persistent ledger) requires a separate design covering storage schema, migration, and rollback — too broad for v2.
- D (additional score dimensions) requires a scoring design review before any dimension is added — open as a separate slice.
- E (report-output integration) touches the report generation pipeline — must be a separately scoped design.
- F (calibration export) is useful but lower priority than establishing the API contract.

---

## 5. Proposed v2 Data Contract

The following fields are the proposed response contract for the v2 read-only bridge endpoint. All fields from v1 are preserved. Two new fields are added:

| Field | Type | Description |
|---|---|---|
| `prediction_report_id` | string | Identifier for the prediction/report record |
| `local_result_key` | string | Local result key for the approved actual result row |
| `global_ledger_record_id` | string | Global ledger trace row identifier |
| `official_source_reference` | string | Reference to the official source record |
| `approved_actual_result` | string \| null | The approved actual result value |
| `predicted_winner_id` | string | The predicted winner identifier |
| `predicted_method` | string | The predicted method |
| `predicted_round` | integer | The predicted round |
| `confidence` | float | Confidence value for the prediction |
| `resolved_result_status` | string | The resolved result status |
| `scored` | boolean | Whether the record is scored |
| `score_outcome` | string | The deterministic score outcome label |
| `calibration_notes` | string \| null | Notes for calibration audit trail |
| `scoring_bridge_status` | string | Endpoint-level status: `ok`, `unresolved`, `conflict`, `missing` |
| `generated_at` | string (ISO 8601) | Timestamp of bridge record generation (read-only, not persisted) |

**`scoring_bridge_status` values:**

| Value | Condition |
|---|---|
| `ok` | Bridge record generated, scored or deterministically unresolved |
| `unresolved` | Approved actual result absent or not yet resolved |
| `conflict` | Duplicate ledger trace conflict detected |
| `missing` | Prediction/report record or approved actual row not found |

---

## 6. Boundaries

The following are hard boundaries for v2. Any proposal that crosses these boundaries must be opened as a separate design slice:

| Boundary | Status |
|---|---|
| No automatic batch scoring | HARD BOUNDARY |
| No scoring rewrite | HARD BOUNDARY |
| No prediction model feedback loop | HARD BOUNDARY |
| No token digest changes | HARD BOUNDARY |
| No token consume changes | HARD BOUNDARY |
| No ledger overwrite | HARD BOUNDARY |
| No mutation controls added | HARD BOUNDARY |
| No report-generation rewrite | HARD BOUNDARY — requires separate design if needed |
| Endpoint is read-only only | HARD BOUNDARY |
| No new persistent storage in this slice | HARD BOUNDARY — Direction C requires its own design |

---

## 7. Failure Handling Design

The v2 endpoint must handle the following failure states deterministically. Each must return a structured response — no unhandled exceptions, no 500s on expected input conditions:

| Failure | Expected Behavior |
|---|---|
| Missing prediction/report record | Return `scoring_bridge_status: missing`, `scored: false`, `score_outcome: unresolved` |
| Missing approved actual | Return `scoring_bridge_status: unresolved`, `scored: false`, `score_outcome: unresolved` |
| Malformed global ledger trace | Return `scoring_bridge_status: conflict`, `scored: false`, `score_outcome: duplicate_conflict` |
| Duplicate approved actual | Return `scoring_bridge_status: conflict`, `scored: false`, `score_outcome: duplicate_conflict` |
| Duplicate ledger trace | Return `scoring_bridge_status: conflict`, `scored: false`, `score_outcome: duplicate_conflict` |
| Mismatch result | Return `scoring_bridge_status: ok`, `scored: true`, `score_outcome: mismatch` |
| Unresolved result | Return `scoring_bridge_status: unresolved`, `scored: false`, `score_outcome: unresolved` |

All failure responses must include the full evidence field set. No fields may be omitted on failure.

---

## 8. Future Implementation Test Plan

When the implementation slice is opened, the following tests must be written and must pass before the implementation is considered complete. This list is the minimum required coverage:

| Test | Description |
|---|---|
| `test_bridge_endpoint_safe_empty_state` | Endpoint returns a valid structured response when no records exist |
| `test_bridge_endpoint_clean_scored_report` | Endpoint returns a fully scored bridge record for a matched prediction and approved actual |
| `test_bridge_endpoint_unresolved_report_visible` | Endpoint returns `scoring_bridge_status: unresolved` when no approved actual exists |
| `test_bridge_endpoint_mismatch_visible` | Endpoint returns `score_outcome: mismatch` for a prediction that does not match the approved actual |
| `test_bridge_endpoint_duplicate_conflict_visible` | Endpoint returns `score_outcome: duplicate_conflict` when duplicate ledger trace detected |
| `test_bridge_endpoint_no_mutation_side_effects` | Calling the endpoint does not modify any record, ledger row, or token state |
| `test_bridge_endpoint_backend_regression_green` | Full backend regression suite remains at or above 193 tests passing |

All tests must be focused. No test may write to the ledger, mutate an approved actual record, or consume a token.

---

## 9. Explicit Non-Goals

The following are explicitly **not** goals of v2:

- Writing scored results to any persistent store (Direction C — separate design required)
- Adding new score dimensions beyond the existing 7 outcomes (Direction D — separate design required)
- Integrating bridge output into exported reports (Direction E — separate design required)
- Adding a calibration summary export feature (Direction F — separate design required)
- Adding a dashboard calibration-readiness panel (Direction B — depends on v2 endpoint being locked first)
- Modifying the approved-apply guard or token pipeline in any way
- Modifying the global ledger mirror or its read-only dashboard panel
- Modifying batch, prediction, intake, or report-generation behavior
- Providing a write or mutation endpoint for scoring results
- Providing automatic or scheduled batch scoring

---

## 10. Final Design Verdict

**The report-scoring bridge v2 direction is approved only as a future design boundary.**

The recommended primary direction is a **read-only report-scoring bridge endpoint** (Direction A). This is the smallest safe next step, establishes the API contract required by all downstream directions, and can be fully covered by focused read-only backend tests without touching any existing behavior.

**Implementation remains blocked** until a separate implementation slice is explicitly opened, a design review is completed, and all tests in Section 8 are defined and passing.

The approved expansion sequence when ready:

1. `official-source-approved-apply-report-scoring-bridge-v2-design-review-v1` *(review this document)*
2. `official-source-approved-apply-report-scoring-bridge-v2-implementation-design-v1`
3. `official-source-approved-apply-report-scoring-bridge-v2-implementation-design-review-v1`
4. `official-source-approved-apply-report-scoring-bridge-v2-implementation-v1`
5. `official-source-approved-apply-report-scoring-bridge-v2-final-review-v1`
6. `official-source-approved-apply-report-scoring-bridge-v2-release-manifest-v1`
7. `official-source-approved-apply-report-scoring-bridge-v2-archive-lock-v1`

---

*Design issued: 2026-04-30*
*Chain: official-source-approved-apply-report-scoring-bridge-v2*
*Slice version: design-v1*
*Implementation status: BLOCKED — design boundary only*

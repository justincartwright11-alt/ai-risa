# Button 3 Result-Comparison Controlled Preview Implementation Readiness Gate v1

## 1. Purpose
Convert the approved read-only Button 3 result-comparison review gate into an exact, testable implementation plan while keeping all mutation paths blocked.

## 2. Source Artifacts Reviewed
- docs/button3_result_comparison_controlled_preview_path_v1.md
- docs/button3_result_comparison_controlled_preview_dashboard_runtime_confirmation_v1.md
- docs/button3_result_comparison_controlled_preview_review_gate_v1.md

## 3. Current Authority And Locked Boundary
This readiness gate is read-only and fail-closed. It does not authorize result mutation, database writes, learning, calibration, customer release, provider execution, network calls, automatic application, or Button 1 or Button 2 changes.

The controlled preview path remains:
- read-only
- non-mutating
- fail-closed
- operator-visible
- evidence-oriented
- deterministic
- separated from apply execution
- separated from learning/calibration
- separated from permanent result writes
- separated from customer output

## 4. Exact Future Implementation File Scope
The only files that may later be changed in the narrow implementation slice are:
- operator_dashboard/button3_result_comparison_preview_v1.py
- operator_dashboard/test_button3_result_comparison_preview_v1.py

All other files remain blocked unless a newer tagged governance artifact explicitly approves them.

## 5. Exact Files And Systems That Remain Blocked
Blocked files include, at minimum:
- operator_dashboard/app.py
- operator_dashboard/templates/index.html
- ops/approved_sources/button1_live_provider_registry.json
- operator_dashboard/button1_provider_adapter_execution_gate_v1.py
- operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- operator_dashboard/button2_template_pack_asset_renderer_v1.py
- operator_dashboard/button2_html_composition_entry_point_v1.py
- operator_dashboard/button2_report_generation_route_render_gating_v1.py

Blocked systems include:
- Button 1 live-source authorization
- Button 1 provider execution
- Button 2 generation and customer release
- provider registry changes
- queue/database writes
- customer PDF generation
- learning application
- calibration application
- auto-save
- network/source calls
- any apply path that consumes preview approval as execution authority

## 6. Preview Request And Response Contract

### Preview Request Contract
The controlled preview request must remain evidence-driven and may include:
- fight_id
- event_name
- fighter_a
- fighter_b
- predicted_winner
- predicted_method
- predicted_round
- actual_winner
- actual_method
- actual_round
- result_source_url
- source_tier
- comparison_status
- accuracy_preview
- operator_review_required

### Preview Response Contract
The controlled preview response must include, at minimum:
- comparison_status
- accuracy_preview
- operator_review_required
- mutation_performed=false
- learning_apply_performed=false
- calibration_write_performed=false
- queue_write_performed=false
- button3_mutation_performed=false
- any provenance fields required to explain the source of the result evidence

### Contract Rules
- Preview input is separated from permanent storage.
- Preview output is separated from apply authorization.
- Approval for preview output never becomes execution authority.
- Deterministic inputs must produce deterministic outputs.
- Provenance must remain visible in the response.

## 7. Deterministic Result-Comparison Behaviour
The future implementation must preserve deterministic behaviour for the same inputs, including stable status classification and stable preview ordering where ordering is relevant.

The implementation must handle the following cases fail-closed:
- missing official-result evidence
- conflicting source evidence
- unknown or partial result
- duplicate result record
- stale result evidence
- provenance absent or incomplete

The implementation must never silently convert ambiguous evidence into an official result.

## 8. Provenance Requirements
The preview path must expose source provenance clearly and must not treat approval as proof.

Required provenance rules:
- source_tier must remain visible
- result_source_url must remain visible
- missing provenance remains blocked
- incomplete provenance remains blocked
- conflicting provenance remains blocked
- duplicate provenance remains blocked
- stale provenance remains blocked

## 9. No-Write And No-Execution Invariants
The implementation slice must preserve all of the following invariants:
- no database writes
- no queue writes
- no accuracy-ledger mutation
- no learning mutation
- no calibration mutation
- no customer output
- no Button 1 live-source authorization
- no Button 2 generation authorization
- no provider execution
- no network calls
- no automatic application
- no approval consumption as execution authority

## 10. Required Coverage Checklist

| # | Test-gating category | Required result |
|---|---|---|
| 1 | Valid read-only result comparison | PASS |
| 2 | Missing official-result evidence | PASS |
| 3 | Conflicting source evidence | PASS |
| 4 | Unknown or partial result | PASS |
| 5 | Duplicate result record | PASS |
| 6 | Stale result evidence | PASS |
| 7 | Provenance absent or incomplete | PASS |
| 8 | Preview output deterministic across repeated calls | PASS |
| 9 | No database or queue writes | PASS |
| 10 | No accuracy-ledger mutation | PASS |
| 11 | No learning or calibration mutation | PASS |
| 12 | No approval consumed as execution authority | PASS |
| 13 | No customer report generation | PASS |
| 14 | No Button 1 or Button 2 authorization implied | PASS |

## 11. Focused Test Matrix
Any future implementation slice must include a focused test file that proves the categories above.

Minimum expected test coverage:
- valid read-only result comparison
- missing official-result evidence
- conflicting source evidence
- unknown or partial result
- duplicate result record
- stale result evidence
- provenance absent or incomplete
- deterministic preview output across repeated calls
- no database or queue writes
- no accuracy-ledger mutation
- no learning or calibration mutation
- no approval consumed as execution authority
- no customer report generation
- no Button 1 or Button 2 authorization implied

## 12. Staged-Set Guard
Any future implementation slice must stage only the exact approved files for that slice and nothing else.

Required staged-set guard:
- the staged set must match the approved implementation files exactly
- any extra staged file is a blocking failure
- any missing approved file is a blocking failure
- pre-existing dirty files remain unstaged and untouched

## 13. Rollback And Abort Conditions
Abort the implementation slice if any of the following occur:
- unresolved mutation path remains open
- missing test coverage remains unresolved
- unclear provenance rule remains unresolved
- approval is treated as execution authority
- Button 1 live-source authorization is implied
- Button 2 generation authorization is implied
- queue/database/customer-output/learning/calibration writes are introduced
- no-write invariants are weakened
- staged set differs from the approved scope
- pre-existing dirty files are staged
- runtime output becomes non-deterministic without justification
- an implementation attempts to silently adapt stale instructions

## 14. Implementation Acceptance Criteria
A future narrow implementation slice may be accepted only when all of the following are true:
- the allowed files are exactly the approved implementation files
- the blocked files and systems remain blocked
- the preview request and response contract remain intact
- deterministic read-only behaviour is proven
- provenance remains visible and fail-closed
- all focused test-gating categories pass
- the staged-set guard passes
- rollback and auditability are preserved
- explicit operator approval is recorded

## 15. Final Readiness Rule
Any unresolved mutation path: BLOCKED
Any missing test coverage: BLOCKED
Any unclear provenance rule: BLOCKED
Only a complete, deterministic, no-write test matrix may approve a future narrow implementation slice.

## 16. Final Verdict
BUTTON3_RESULT_COMPARISON_CONTROLLED_PREVIEW_IMPLEMENTATION_READINESS_GATED_READ_ONLY_FAIL_CLOSED

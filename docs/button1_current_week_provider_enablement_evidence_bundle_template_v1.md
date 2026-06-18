# Button 1 Current Week Provider Enablement Evidence Bundle Template v1

Slice: button1-current-week-provider-enablement-evidence-bundle-template-v1
Date: 2026-06-18
Status: Docs-only template

## Purpose

Provide the mandatory evidence-bundle template that must be fully completed before any provider enablement slice can be proposed.

## Enforcement Rule

A provider enablement slice proposal is automatically invalid unless this entire template is completed with auditable evidence.

If any field is missing, unverified, stale, or inconsistent, decision is DENY and proposal cannot proceed.

## Hard Boundary (Unchanged)

Until a complete and approved evidence bundle exists:
- Provider enabling remains blocked.
- Provider execution remains blocked.
- Source/network calls remain blocked.
- Scraping remains blocked.
- Queue/database writes remain blocked.
- Button 2 promotion remains blocked.

## Bundle Header (Required)

- bundle_id:
- bundle_version:
- checklist_version_reference:
- target_provider_id:
- target_provider_name:
- proposal_owner:
- proposal_timestamp_utc:
- approval_requested_by:
- environment_scope:
- change_window:

## Section A: Governance and Approval Evidence

Required fields:
- operator_approval_contract_uri:
- required_approval_fields_present: YES/NO
- approver_identity_proof_uri:
- approval_rationale:
- rollback_authority_assigned_to:
- rollback_runbook_uri:
- governance_signoff_record_uri:

Required artifacts:
- Signed governance note.
- Approval payload contract with required fields.
- Rollback ownership and runbook artifact.

Validation checks:
1. Approval contract requires actor, timestamp, and rationale.
2. Missing approval metadata fails bundle.
3. Governance sign-off date is current and valid.

## Section B: Provider Registry Integrity Evidence

Required fields:
- registry_file_uri:
- schema_version:
- schema_validation_result: PASS/FAIL
- validator_output_uri:
- provider_id_allowlist_match: YES/NO
- provider_metadata_owner:
- provider_metadata_review_date:
- default_state_enabled_false_verified: YES/NO
- intended_change_diff_uri:

Required artifacts:
- Schema validator output.
- Registry diff scoped to intended provider change only.
- Metadata ownership/review evidence.

Validation checks:
1. Registry schema validation must be PASS.
2. Only approved provider IDs may be targeted.
3. Unexpected registry drift fails bundle.

## Section C: Execution Gate Contract Evidence

Required fields:
- gate_contract_doc_uri:
- decision_fields_verified: YES/NO
- deny_reason_coverage_verified: YES/NO
- malformed_input_fail_closed_tests_uri:
- unknown_source_fail_closed_tests_uri:
- preview_nonpreview_contract_examples_uri:

Required decision fields to verify:
- execution_gate_checked
- execution_gate_allowed
- execution_gate_decision
- preview_only
- execution_gate_reason_codes

Required side-effect flag coverage:
- provider_execution_started
- source_network_call_started
- scraping_started
- queue_write_started
- button2_promotion_started

Validation checks:
1. Decision model fields exist and are stable.
2. Deny reason codes include approval missing and provider not enabled.
3. Fail-closed behavior on malformed/unknown input is proven.

## Section D: Side-Effect Guardrail Evidence

Required fields:
- deny_path_zero_side_effects_proof_uri:
- network_pre_allow_block_proof_uri:
- scraping_pre_allow_block_proof_uri:
- write_pre_allow_block_proof_uri:
- button2_promotion_block_proof_uri:

Required artifacts:
- Negative-path integration logs.
- Telemetry trace proving side-effect flags remain false on deny.
- Explicit assertions for all side-effect flags.

Validation checks:
1. Deny path triggers no side effects.
2. Pre-allow network/scrape/write actions are blocked.
3. Button 2 promotion remains blocked on deny.

## Section E: Runtime/API Evidence

Required fields:
- workflow_preview_contract_uri:
- deny_response_example_uri:
- allow_shape_preview_example_uri:
- deterministic_error_handling_proof_uri:
- latest_api_smoke_summary_uri:

Required artifacts:
- Request/response examples.
- API smoke summary with PASS verdict.
- Contract assertion output.

Validation checks:
1. Payload contract includes decision and reason fields.
2. preview_only marker is explicit in preview path.
3. Error paths resolve to deterministic deny posture.

## Section F: UI Non-Interactive Safety Evidence

Required fields:
- ui_contract_test_report_uri:
- static_template_noninteractive_check_uri:
- browser_ui_smoke_summary_uri:
- deny_reason_codes_visibility_proof_uri:

Required artifacts:
- UI contract test output.
- Template/static analysis proving blocked panel has no action controls.
- Browser UI proof summary.

Validation checks:
1. Status panel reflects gate fields accurately.
2. No hidden or visible controls enable provider action.
3. Deny diagnostics are visible to operator.

## Section G: Observability and Audit Evidence

Required fields:
- logging_schema_uri:
- deny_attempt_log_samples_uri:
- approval_metadata_log_samples_uri:
- correlation_id_trace_uri:
- audit_export_manifest_uri:

Required artifacts:
- Logging schema and sample entries.
- Correlation ID trace from request to decision.
- Audit export manifest for reviewer pack.

Validation checks:
1. Attempts and deny reasons are logged.
2. Approval metadata logging is present when supplied.
3. Correlation IDs support full traceability.

## Section H: Test and Defect Evidence

Required fields:
- unit_test_summary_uri:
- integration_test_summary_uri:
- ui_test_summary_uri:
- browser_api_smoke_summary_uri:
- open_critical_defects_enablement_scope: COUNT
- defect_report_uri:

Pass thresholds:
- Unit tests: PASS.
- Integration tests: PASS.
- UI tests: PASS.
- Browser/API smokes: PASS.
- Open critical defects in enablement scope: 0.

Validation checks:
1. Evidence timestamps are current.
2. Evidence corresponds to target provider and current bundle version.
3. Any critical defect count > 0 fails bundle.

## Section I: Rollout and Reversibility Evidence

Required fields:
- first_rollout_scope_single_provider_verified: YES/NO
- instant_disable_mechanism_proof_uri:
- rollback_rehearsal_proof_uri:
- observation_window_definition:
- continuation_thresholds_uri:
- redisable_criteria_uri:
- rollback_owner:

Required artifacts:
- Rollout plan.
- Rollback rehearsal logs.
- Threshold table with owner sign-off.

Validation checks:
1. First rollout remains single-provider scoped.
2. Disable and rollback procedures are proven operational.
3. Re-disable triggers are explicit and testable.

## Evidence Freshness and Integrity Rules

- All evidence must be timestamped.
- Evidence older than allowed review window is stale and fails bundle.
- Artifact URIs must resolve to immutable records.
- Hand-edited summaries without backing artifacts are invalid.
- Contradictory artifacts across sections fail bundle.

## Bundle Completeness Checklist

Mark each as PASS or FAIL:
- Section A complete:
- Section B complete:
- Section C complete:
- Section D complete:
- Section E complete:
- Section F complete:
- Section G complete:
- Section H complete:
- Section I complete:
- Freshness/integrity checks complete:

Overall result:
- OVERALL_BUNDLE_STATUS: PASS/FAIL

## Proposal Gate Decision

If OVERALL_BUNDLE_STATUS is FAIL:
- proposal_gate_decision: DENY
- proposal_gate_reason: Incomplete or invalid evidence bundle

If OVERALL_BUNDLE_STATUS is PASS:
- proposal_gate_decision: APPROVE_FOR_PROPOSAL_REVIEW_ONLY
- proposal_gate_reason: Evidence bundle complete; governance review still required

## Required Signatures

- proposal_owner_signature:
- governance_reviewer_signature:
- quality_reviewer_signature:
- operations_reviewer_signature:
- final_decision_timestamp_utc:

## Final Statement

Completion of this template is a mandatory precondition to propose any provider enablement slice.
This template alone does not enable providers and does not authorize execution.

# Button3 Official Result Runtime Internal Operator Preview UI Template Surface Gap Two Template Remediation Copy Execution Gate v1

## 1. Gate Identity
- gate_name: button3-official-result-runtime-internal-operator-preview-ui-template-surface-gap-two-template-remediation-copy-execution-gate-v1
- gate_type: docs-only authorization contract
- authority_mode: fail-closed
- execution_authority_in_this_gate: bounded single-use, copy-only

## 2. Required Precondition Chain
- analysis_evidence_commit: 3e63a99
- analysis_evidence_tag: button3-official-result-runtime-internal-operator-preview-ui-template-surface-gap-identity-and-minimal-scope-analysis-evidence-v1
- analysis_evidence_proof_commit: 5e8b9b1
- analysis_evidence_proof_tag: button3-official-result-runtime-internal-operator-preview-ui-template-surface-gap-identity-and-minimal-scope-analysis-evidence-proof-and-review-v1
- classification_required: PACKAGED_UI_TEMPLATE_SURFACE_GAP_CONFIRMED
- minimal_scope_required: EXACTLY_TWO_TEMPLATES

## 3. Objective
Perform one exact, minimal package copy remediation for UI template closure only, limited to two templates required by / and /advanced-dashboard route rendering.

## 4. Authorized Sequence (Only)
This gate authorizes exactly one execution pass of the following sequence:
1. Pre-Copy Hashes
2. Create Exact runtime/templates Directory If Absent
3. Exact Two-Template Copy
4. Post-Copy Hash Verification
5. Package-Scope Diff
6. Strict Staged-Set Guard
7. Rollback Evidence
8. Immediate Stop

## 5. Authorized Copy Scope (Exact)
Allowed source files:
- operator_dashboard/templates/index.html
- operator_dashboard/templates/advanced_dashboard.html

Allowed destination files:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/templates/index.html
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/templates/advanced_dashboard.html

Allowed destination directory creation:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/templates

No additional files are authorized.

## 6. Explicit Prohibitions
The following remain denied in this gate and in any execution under this gate:
- endpoint rerun
- workflow rerun
- apply execution
- ledger writes
- learning application
- calibration writes
- GCID mutation
- customer-output release
- production release
- authority elevation
- any copy outside the two authorized templates
- any static asset copying
- any deletion, movement, or modification of runtime root index.html
- any package remediation beyond exact two-template copy

## 7. Required Execution Evidence (If Execution Occurs)
Execution evidence root must contain at minimum:
- checklist/pre_copy_integrity_and_chain_check_v1.txt
- execution/pre_copy_hashes_v1.txt
- execution/copy_operation_report_v1.txt
- execution/post_copy_hash_verification_v1.txt
- summary/package_scope_diff_evidence_v1.txt
- summary/staged_set_guard_report_v1.txt
- summary/rollback_evidence_v1.txt
- summary/immediate_stop_and_lock_boundary_v1.txt
- governance/prohibition_preservation_matrix_v1.txt

## 8. Deterministic Mapping Contract
Mapping A:
- source: operator_dashboard/templates/index.html
- destination: tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/templates/index.html

Mapping B:
- source: operator_dashboard/templates/advanced_dashboard.html
- destination: tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/templates/advanced_dashboard.html

Any alternate mapping is out of scope and denied.

## 9. Scope And Staging Contract
- allowed_file_count must match exact authorized evidence files for this slice
- out_of_scope_staged_count must be 0
- missing_allowed_count must be 0
- strict staged-set guard must pass before lock

## 10. Completion Criteria
A compliant execution under this gate must prove:
- pre-copy hashes captured for both source files and both destination states
- runtime/templates directory creation performed only if absent
- exact two-template copy performed with deterministic path mapping
- post-copy hash parity confirms destination equals source for both files
- no out-of-scope package changes
- rollback evidence produced
- immediate stop boundary enforced

## 11. Gate Decision
- gate_status: APPROVED_FOR_EXACT_TWO_TEMPLATE_COPY_EXECUTION_ONLY
- execution_count_limit: EXACTLY_ONE
- endpoint_or_workflow_rerun_authority: DENIED
- broader_mutation_authority: DENIED
- post_execution_requirement: separate docs-only evidence proof-and-review lock before any rerun authority request

## 12. Final Gate Statement
This gate authorizes only one bounded two-template copy remediation execution for packaged UI template closure under strict fail-closed scope control. Endpoint rerun and workflow rerun remain denied until execution evidence and separate evidence proof-and-review are both locked.

# Button 3 Official Result Runtime Internal Release Candidate Startup Closure Scope Extension v2 Copy Execution Gate v1

## 1. Gate Identity
- gate_name: button3-official-result-runtime-internal-release-candidate-startup-closure-scope-extension-v2-copy-execution-gate-v1
- gate_type: docs-only startup-closure scope-extension v2 copy execution gate
- authority_mode: fail-closed
- execution_in_this_slice: prohibited

## 2. Baseline Chain
- scope_extension_v2_analysis_evidence_commit: f2a88c1
- scope_extension_v2_analysis_evidence_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-scope-extension-v2-analysis-evidence-v1
- scope_extension_v2_analysis_evidence_proof_review_commit: bfe7895
- scope_extension_v2_analysis_evidence_proof_review_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-scope-extension-v2-analysis-evidence-proof-and-review-v1
- package_root: tmp_internal_rc_package/button3_official_result_runtime_rc_v1

## 3. Purpose
Authorize only one exact one-file copy execution for the v2 minimal candidate set with bounded evidence capture and immediate stop.

This gate does not authorize startup rerun.

## 4. Authorized Sequence (Only)
The only authorized sequence under this gate is:
1. Pre-Copy Hash
2. One-File Copy
3. Post-Copy Hash Verification
4. Package-Scope Diff
5. Strict Staged-Set Guard
6. Immediate Stop

Any action outside this sequence is denied.

## 5. Exact One-File Copy Scope
Authorized source file (only):
- operator_dashboard/button1_approved_provider_config_validator_v1.py

Authorized destination file (only):
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/operator_dashboard/button1_approved_provider_config_validator_v1.py

Boundary rules:
- no additional source files are authorized
- no additional destination files are authorized
- no directory-level copy operations are authorized

## 6. Deterministic Mapping Lock
Deterministic mapping (exact):
- source: operator_dashboard/button1_approved_provider_config_validator_v1.py
- destination: tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime/operator_dashboard/button1_approved_provider_config_validator_v1.py

Mapping constraints:
- operator_dashboard namespace preserved
- one source maps to one destination only
- alternate paths are prohibited

## 7. Evidence Contract (Exact Files)
Required evidence files for this one-file copy execution:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_scope_extension_v2_copy/pre_copy_hash_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_scope_extension_v2_copy/post_copy_hash_verification_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_scope_extension_v2_copy/package_scope_diff_evidence_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_scope_extension_v2_copy/staged_set_guard_report_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_scope_extension_v2_copy/stop_after_copy_evidence_v1.txt

## 8. Pre-Copy Hash Contract
Before copy, capture SHA-256 for:
- source file (required)
- destination file if present (required when present)

Fail-closed:
- if source hash cannot be captured, copy is denied.

## 9. Post-Copy Hash Verification Contract
After copy, capture destination SHA-256 and verify:
- destination SHA-256 equals source SHA-256

Fail-closed:
- hash mismatch denies evidence pass and blocks any next-step authorization.

## 10. Package-Scope Diff Contract
Package-scope diff requirements:
- out_of_scope_count must be 0
- scope_compliant must be True
- only authorized destination file plus declared evidence files may appear in scope set

Fail-closed:
- any out-of-scope path denies evidence pass.

## 11. Strict Staged-Set Guard Contract
Guard requirements for copy-evidence commit:
- allowed_file_count must equal 6 (1 copied file + 5 evidence files)
- staged_file_count must equal 6
- out_of_scope_staged_count must be 0
- missing_allowed_count must be 0
- stage_guard_pass must be True

Fail-closed:
- any staged-set mismatch denies evidence pass.

## 12. Immediate Stop Requirement
After hash verification, scope diff, and staged-set guard evidence:
- stop immediately
- do not run startup rerun
- do not perform remediation, repair, or additional copy actions

## 13. Explicit Prohibitions (Still Denied)
Still denied in this gate slice:
- startup rerun
- copy outside the single authorized mapping
- runtime/package modification outside authorized destination file
- dependency remediation
- workflow execution
- endpoint calls
- denial-control calls
- production release
- write/customer-output authority actions
- GCID mutation
- learning mutation
- calibration mutation

## 14. Abort Conditions
Abort immediately with fail-closed status if any occurs:
- copy request deviates from exact one-file mapping
- pre-copy hash capture is incomplete
- post-copy hash verification fails
- package-scope diff shows out-of-scope paths
- strict staged-set guard fails
- any prohibited action is attempted

Abort outcome:
- stop immediately
- keep startup rerun denied
- require separate copy-evidence proof/review lock before any next authorization decision

## 15. Decision
- one_file_copy_authorization_now: AUTHORIZED_EXACT_MAPPING_ONLY
- execution_now: AUTHORIZED_ONE_FILE_COPY_EVIDENCE_ONLY
- startup_rerun_authorization_now: DENIED_PENDING_COPY_EVIDENCE_PROOF_REVIEW
- remediation_authorization_now: NOT_AUTHORIZED
- next_required_step: separate docs-only copy execution gate proof/review before any copy execution

## 16. Non-Execution Confirmation
This gate lock is docs-only.

No copy operation, no startup rerun, and no runtime/package change is performed in this slice.

## 17. Final Gate Verdict
BUTTON3_OFFICIAL_RESULT_RUNTIME_INTERNAL_RELEASE_CANDIDATE_STARTUP_CLOSURE_SCOPE_EXTENSION_V2_COPY_EXECUTION_GATE_LOCKED_FAIL_CLOSED

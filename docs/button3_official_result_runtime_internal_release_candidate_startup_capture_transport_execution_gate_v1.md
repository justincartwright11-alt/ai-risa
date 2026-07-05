# Button 3 Official Result Runtime Internal Release Candidate Startup Capture Transport Execution Gate v1

## 1. Gate Identity
- gate_name: button3-official-result-runtime-internal-release-candidate-startup-capture-transport-execution-gate-v1
- gate_type: docs-only capture-transport execution gate
- authority_mode: fail-closed
- execution_in_this_slice: prohibited

## 2. Baseline Chain
- capture_transport_design_commit: 85591c3
- capture_transport_design_tag: button3-official-result-runtime-internal-release-candidate-startup-capture-transport-remediation-design-v1
- capture_transport_design_proof_review_commit: a45e26d
- capture_transport_design_proof_review_tag: button3-official-result-runtime-internal-release-candidate-startup-capture-transport-remediation-design-proof-and-review-v1
- package_root: tmp_internal_rc_package/button3_official_result_runtime_rc_v1

## 3. Purpose
Authorize only one bounded startup attempt to execute the capture-transport design controls and collect complete evidence for first-blocking-exception identity resolution.

This gate does not authorize remediation, dependency copying, dependency repair, or runtime/package modifications.

## 4. Authorized Sequence (Only)
After separate proof/review lock, the only authorized sequence is:
1. Package Integrity Check
2. Absolute Evidence Path Resolution
3. Exact Runtime Working Directory Isolation
4. Path-Safe Process Invocation
5. Separate Raw stdout Capture
6. Separate Raw stderr Capture
7. Exit-Code Preservation
8. First-Blocking-Exception Extraction
9. Strict Evidence Set Validation
10. Strict Staged-Set Guard Validation
11. Immediate Stop

Any action outside this sequence is denied.

## 5. Exact Absolute Evidence Paths
All evidence paths must be fully resolved absolute filesystem paths before launch:
- package_integrity_check_v1.txt
- startup_command_and_exit_code_v1.txt
- raw_stdout_v1.txt
- raw_stderr_v1.txt
- first_blocking_exception_identity_v1.txt
- stop_after_exception_capture_v1.txt
- package_scope_diff_evidence_v1.txt
- staged_set_guard_report_v1.txt

Required absolute evidence root:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_capture_transport_execution

Fail-closed:
- if any absolute path cannot be resolved, launch is denied.

## 6. Exact Runtime Working Directory
The only authorized working directory for process launch is:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime

Fail-closed:
- if launch cwd differs from exact runtime root, launch is denied.

## 7. Path-Safe Process Invocation
Authorized startup command payload:
- python app.py

Invocation constraints:
- invocation method must pass absolute stdout/stderr paths directly to the process launcher
- no shell-relative redirection targets
- no command chaining
- no additional commands before or after launch in same execution token

Fail-closed:
- if invocation path safety cannot be proven, launch is denied.

## 8. Separate stdout/stderr Capture Contract
Required transport contract:
- raw stdout persisted to raw_stdout_v1.txt
- raw stderr persisted to raw_stderr_v1.txt
- both streams captured independently
- capture completeness check records file existence and readable byte count

Fail-closed:
- if either stream is missing or unreadable, identity extraction cannot claim resolved status.

## 9. Exit-Code Preservation Contract
Required contract:
- process exit code captured immediately after launch completion
- startup_command_and_exit_code_v1.txt must record command boundary, absolute stream paths, and exit code

Fail-closed:
- if exit code cannot be preserved, evidence set is invalid.

## 10. First-Blocking-Exception Extraction Contract
Required contract:
- extraction reads stderr first, then stdout fallback for first blocking signal
- if ModuleNotFoundError exists, record exact missing module token
- if other first blocking exception exists, record exact exception class and first message line
- if stream completeness fails, mark unresolved fail-closed

Output file:
- first_blocking_exception_identity_v1.txt

## 11. Exactly-One Startup Attempt Control
Required control:
- exactly one startup launch is allowed under this gate execution token
- launch count must be explicitly recorded
- any second launch in this slice is denied

Fail-closed:
- if exactly-one proof is missing, evidence cannot authorize further decisions.

## 12. Exact Evidence File Set And Scope Contract
The exact evidence file set for lock scope is fixed to 8 files:
1. package_integrity_check_v1.txt
2. startup_command_and_exit_code_v1.txt
3. raw_stdout_v1.txt
4. raw_stderr_v1.txt
5. first_blocking_exception_identity_v1.txt
6. stop_after_exception_capture_v1.txt
7. package_scope_diff_evidence_v1.txt
8. staged_set_guard_report_v1.txt

Scope policy:
- out_of_scope_count must be 0
- scope_compliant must be True

## 13. Strict Staged-Set Guard Contract
Guard policy:
- allowed_file_count must equal 8
- staged_file_count must equal 8
- out_of_scope_staged_count must be 0
- missing_allowed_count must be 0
- stage_guard_pass must be True

Fail-closed:
- if guard does not pass, evidence lock is denied.

## 14. Immediate Stop Requirement
After extraction and evidence validation:
- stop immediately
- do not run remediation, dependency copy, dependency repair, or package/runtime modifications
- do not run workflow, endpoint, denial-control, production, write/customer-output, GCID, learning, or calibration actions

Required stop evidence output file:
- stop_after_exception_capture_v1.txt

## 15. Explicit Prohibitions (Still Denied)
Still denied:
- package runtime modification
- dependency copying
- dependency remediation
- workflow execution
- endpoint calls
- denial-control calls
- production release
- write/customer-output authority actions
- GCID mutation
- learning mutation
- calibration mutation

## 16. Authorization Decision
Decision in this gate-only lock:
- startup_capture_transport_execution_authorization_now: DENIED_PENDING_GATE_PROOF_AND_REVIEW
- startup_attempt_count_authorized_after_proof_review: EXACTLY_ONE
- remediation_or_authority_elevation_now: NOT_AUTHORIZED
- next_required_step: separate docs-only gate proof/review lock before any startup attempt

## 17. Non-Execution Confirmation
This gate lock is docs-only.

No startup execution, runtime/package change, copy operation, or remediation action is performed in this slice.

## 18. Final Gate Verdict
BUTTON3_OFFICIAL_RESULT_RUNTIME_INTERNAL_RELEASE_CANDIDATE_STARTUP_CAPTURE_TRANSPORT_EXECUTION_GATE_LOCKED_FAIL_CLOSED

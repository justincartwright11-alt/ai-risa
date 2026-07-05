# Button 3 Official Result Runtime Internal Release Candidate Startup Closure Rerun Gate v2

## 1. Gate Identity
- gate_name: button3-official-result-runtime-internal-release-candidate-startup-closure-rerun-gate-v2
- gate_type: docs-only startup-closure rerun gate
- authority_mode: fail-closed
- execution_in_this_slice: prohibited

## 2. Baseline Chain
- copy_execution_evidence_v2_commit: cbf005f
- copy_execution_evidence_v2_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-scope-extension-v2-copy-execution-evidence-v1
- copy_execution_evidence_v2_proof_review_commit: ed3dad3
- copy_execution_evidence_v2_proof_review_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-scope-extension-v2-copy-execution-evidence-proof-and-review-v1
- copy_execution_gate_v2_proof_review_commit: f059510
- package_root: tmp_internal_rc_package/button3_official_result_runtime_rc_v1

## 3. Purpose
Authorize only one bounded post-copy startup rerun check for import-time startup viability evidence.

This gate does not authorize copy, remediation, workflow execution, endpoint activity, denial-control activity, or any authority/mutation path.

## 4. Authorized Sequence (Only)
The only authorized sequence under this gate is:
1. Integrity Check
2. Path-Safe Startup
3. Raw stdout/stderr Capture
4. Exit-Code Preservation
5. First-Blocking-Exception Identification
6. Immediate Stop

Any action outside this sequence is denied.

## 5. Integrity Check Requirements
Before startup command, verify all of the following:
- copy-execution evidence baseline remains locked at cbf005f and ed3dad3
- copied one-file destination exists at mapped package destination
- package runtime launch directory exists
- rerun evidence directory exists and is writable

Required integrity evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/package_integrity_check_v1.txt

## 6. Exact Path-Safe Startup Boundary
Only this startup command is authorized:
- Set-Location tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime
- python app.py

Command boundary constraints:
- command runs only from package runtime root
- no command chaining
- no alternate startup entrypoint
- no endpoint/workflow/denial-control calls
- raw stdout/stderr must be captured into separate files

Required startup capture evidence output paths:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/raw_stdout_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/raw_stderr_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/startup_command_and_exit_code_v1.txt

## 7. Exit-Code Preservation And Exception Identification Contract
After startup capture:
- preserve exact process exit code
- identify first blocking exception from raw stream evidence
- explicitly record ModuleNotFoundError missing module when present
- if non-ModuleNotFoundError, record exception class and first blocking message line

Required check evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/first_blocking_exception_check_v1.txt

## 8. Immediate Stop Requirement
After exception identification evidence is written:
- stop immediately
- do not run any second startup attempt
- do not run copy/remediation/workflow/endpoint/denial-control actions

Required stop evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_closure_rerun_v2/stop_after_startup_check_v1.txt

## 9. Explicit Prohibitions (Still Denied)
This gate continues to prohibit:
- file copying
- dependency remediation
- startup attempt count above one
- workflow execution
- endpoint calls
- denial-control calls
- production release actions
- write/customer-output authority actions
- GCID mutation actions
- learning mutation actions
- calibration mutation actions

## 10. Abort Conditions
Abort immediately with fail-closed status if any occurs:
- integrity check fails
- startup boundary deviates from exact command/cwd requirements
- raw stdout or raw stderr capture is missing
- exit code is not preserved
- first-blocking-exception identification evidence is missing
- prohibited action is invoked
- process is not stopped after first identification

Abort outcome:
- stop immediately
- preserve denied state for broader execution
- require rerun evidence proof/review before any further authorization changes

## 11. Decision
- startup_rerun_authorization_now: DENIED_PENDING_RERUN_GATE_PROOF_AND_REVIEW_V2
- execution_now: DENIED_PENDING_RERUN_GATE_PROOF_AND_REVIEW_V2
- copy_authorization_now: NOT_AUTHORIZED
- remediation_authorization_now: NOT_AUTHORIZED
- next_required_step: separate docs-only startup rerun gate proof/review v2 before one bounded startup attempt can execute

## 12. Non-Execution Confirmation
This gate lock is docs-only.

No startup command execution, no copy operation, and no remediation action is performed in this slice.

## 13. Final Gate Verdict
BUTTON3_OFFICIAL_RESULT_RUNTIME_INTERNAL_RELEASE_CANDIDATE_STARTUP_CLOSURE_RERUN_GATE_V2_LOCKED_FAIL_CLOSED

# Button 3 Official Result Runtime Internal Release Candidate Startup First Blocking Exception Capture Gate v1

## 1. Gate Identity
- gate_name: button3-official-result-runtime-internal-release-candidate-startup-first-blocking-exception-capture-gate-v1
- gate_type: docs-only first-blocking-exception capture gate
- authority_mode: fail-closed
- execution_in_this_slice: prohibited

## 2. Baseline Chain
- rerun_reauthorization_evidence_commit: 2632812
- rerun_reauthorization_evidence_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-rerun-reauthorization-evidence-v1
- rerun_reauthorization_evidence_proof_review_commit: ecd3a35
- rerun_reauthorization_evidence_proof_review_tag: button3-official-result-runtime-internal-release-candidate-startup-closure-rerun-reauthorization-evidence-proof-and-review-v1
- package_root: tmp_internal_rc_package/button3_official_result_runtime_rc_v1

## 3. Purpose
Authorize only one bounded startup attempt for complete raw capture and first blocking exception identity extraction.

This gate does not authorize remediation, package repair, or file-copying actions.

## 4. Authorized Sequence (Only)
The only sequence this gate can authorize, after separate proof/review lock, is:
1. Package Integrity Check
2. Exact Package-Root Startup Command
3. Complete Raw stdout Capture
4. Complete Raw stderr Capture
5. Exit-Code Capture
6. First Blocking Exception Identity Extraction
7. Immediate Stop

Any action outside this sequence is denied.

## 5. Package Integrity Check Requirements
Before startup command, verify all of the following:
- baseline chain remains unchanged at commits 2632812 and ecd3a35
- package runtime root exists
- startup-critical copied module exists at package destination
- evidence directory for first blocking exception capture exists and is writable

Required integrity evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/package_integrity_check_v1.txt

## 6. Exact Startup Command Boundary
Only this startup command is authorized:
- Set-Location tmp_internal_rc_package/button3_official_result_runtime_rc_v1/runtime
- python app.py

Boundary constraints:
- command must run from package runtime root only
- no command chaining
- no endpoint or denial-control calls
- no workflow execution
- no package repair or file copying

Required command and exit-code evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/startup_command_and_exit_code_v1.txt

## 7. Complete Raw Stream Capture Contract
Capture complete raw streams from the single startup attempt:
- complete raw stdout persisted without truncation
- complete raw stderr persisted without truncation
- stream capture must not normalize away traceback lines

Required stream evidence output paths:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/raw_stdout_v1.txt
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/raw_stderr_v1.txt

## 8. First Blocking Exception Identity Extraction Contract
After complete stream capture:
- extract first blocking exception identity from raw evidence
- record module path and missing symbol/module if ModuleNotFoundError
- if non-ModuleNotFoundError, record exact exception class and first blocking message
- mark extraction status as resolved or unresolved

Required extraction evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/first_blocking_exception_identity_v1.txt

## 9. Immediate Stop Requirement
After Section 8 extraction:
- stop immediately
- no remediation or patching
- no file copy actions
- no repeated rerun execution
- no workflow, endpoint, denial-control, production, write, customer-output, GCID, learning, or calibration actions

Required stop evidence output path:
- tmp_internal_rc_package/button3_official_result_runtime_rc_v1/evidence/startup_first_blocking_exception_capture/stop_after_exception_capture_v1.txt

## 10. Explicit Prohibitions (Still Denied)
This gate continues to prohibit:
- workflow execution
- endpoint calls
- denial-control calls
- package repair
- file copying
- production release
- write authority actions
- customer-output actions
- GCID mutation actions
- learning mutation actions
- calibration mutation actions

## 11. Abort Conditions
Abort immediately with fail-closed status if any occurs:
- package integrity check fails
- startup command deviates from exact boundary
- raw stdout or raw stderr capture is incomplete or missing
- exit code is not recorded
- first blocking exception identity extraction is missing
- prohibited action is attempted
- process does not stop immediately after extraction

Abort outcome:
- stop immediately
- preserve denied state for remediation or broader execution
- require separate proof/review lock before any startup execution attempt

## 12. Authorization Decision
Decision in this gate-only lock:
- startup_exception_capture_authorization_now: DENIED_PENDING_GATE_PROOF_AND_REVIEW
- startup_attempt_count_authorized_after_proof_review: EXACTLY_ONE
- remediation_or_copy_authorization_now: NOT_AUTHORIZED
- workflow_endpoint_mutation_authorization_now: NOT_AUTHORIZED
- next_required_step: lock separate docs-only gate proof/review before executing the single startup exception-capture attempt

## 13. Non-Execution Confirmation
This gate lock is docs-only.

No startup command execution or runtime action is performed in this slice.

## 14. Final Gate Verdict
BUTTON3_OFFICIAL_RESULT_RUNTIME_INTERNAL_RELEASE_CANDIDATE_STARTUP_FIRST_BLOCKING_EXCEPTION_CAPTURE_GATE_LOCKED_FAIL_CLOSED

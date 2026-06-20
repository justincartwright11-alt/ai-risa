# Button 1 Runtime Preview Contract Normalization Design v1

## 1. Purpose
Design the optional normalization of Button 1 runtime-preview field names, reason-code ordering, diagnostics readability, and proof consistency while preserving all current fail-closed behavior. This design does not approve live source calls, provider execution, network/source calls, scraping, writes, Button 2 promotion, customer output, learning/calibration, auto-save, UI changes, registry changes, or provider enabled-state changes.

## 2. Source Identity
- Worktree: C:\Users\jusin\OneDrive\Documents\Custom Office Templates
- Branch: master
- Checkpoint: 95046d3
- Tag: button1-runtime-preview-contract-hardening-implementation-review-and-runtime-validation-gate-v1

## 3. Reviewed Input Document
- docs/button1_runtime_preview_contract_hardening_implementation_review_and_runtime_validation_gate_v1.md

## 4. Current Locked Runtime State
- Registry candidates: 2
- Enabled provider: ufc_official_events
- Disabled provider: one_fc_official_events
- Decision: deny
- Reason codes:
  - execution_gate_operator_approval_missing
  - source_call_authorization_missing
  - max_result_count_unbounded
  - timeout_unbounded
  - provenance_required_missing
  - network_call_not_authorized
- no_write_flags: present
- live_save_allowed: false
- provider execution/network/source/scraping/write/promotion/output flags: all false

## 5. Normalization Goal
- Improve field naming clarity only where needed.
- Improve reason-code ordering only where needed.
- Improve diagnostics readability only where needed.
- Preserve all fail-closed behavior.

## 6. Non-Goals
- No provider execution.
- No live calls.
- No scraping.
- No writes.
- No Button 2 promotion.
- No customer output.
- No learning/calibration.
- No auto-save.
- No UI changes.
- No registry changes.

## 7. Proposed Normalization Targets
- Reason-code order stability.
- no_write_flags consistency.
- live_save_allowed placement.
- Source-call authorization field grouping.
- Provenance field grouping.
- Operator approval field grouping.

## 8. Required Preservation Rules
- Current deny reason set must remain visible.
- No deny reason may hide another blocker.
- Token state remains boolean-only.
- No token secret may appear anywhere.
- one_fc_official_events remains disabled.
- No more than one provider enabled.
- live_save_allowed remains false.

## 9. Proposed Future Implementation Scope For Later Review Only
- operator_dashboard/button1_provider_adapter_execution_gate_v1.py
- operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py
- operator_dashboard/test_button1_runtime_preview_contract_normalization_v1.py

## 10. Explicitly Excluded Unless Separately Approved
- provider registry JSON
- app.py
- templates/index.html
- orchestrator
- registration adapter
- queue/database files
- Button 2 files
- customer PDF files
- learning/calibration files
- token secret storage/logging files

## 11. Required Future Tests
- current reason-code set remains visible
- reason-code ordering is deterministic
- no-write flags remain present
- live_save_allowed remains false
- token secret absent
- no provider execution
- no network/source calls
- no scraping
- no writes
- no Button 2 promotion
- no customer output
- no learning/calibration
- one_fc_official_events disabled
- no more than one provider enabled
- protected files untouched

## 12. Rollback/Abort Policy
- Abort if protected files change without approval.
- Abort if one_fc_official_events is enabled.
- Abort if more than one provider is enabled.
- Abort if token secret appears anywhere.
- Abort if provider execution occurs.
- Abort if real network/source calls occur.
- Abort if scraping occurs.
- Abort if queue/database/customer-PDF/learning/calibration writes occur.
- Abort if Button 2 promotion occurs.
- Abort if customer output occurs.
- Abort if auto-save occurs.
- Abort if source-call authorization bypasses operator approval.
- Abort if source-call authorization bypasses provenance.
- Abort if no_write_flags disappear.
- Abort if live_save_allowed becomes true.
- Abort if staged set differs from approved scope.
- Abort if pre-existing dirty files are staged.
- Abort if pytest fails.

## 13. Final Design Verdict
BUTTON1_RUNTIME_PREVIEW_CONTRACT_NORMALIZATION_DESIGN_READY_FOR_REVIEW_ONLY

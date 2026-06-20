# Button 1 Source Call Network Authorization Contract Design v1

## 1. Purpose
Design the future authorization contract required before Button 1 may execute any provider source/network call. This document must not approve implementation, token use, provider execution, network/source calls, scraping, queue/database writes, customer PDF/report generation, Button 2 promotion, learning/calibration writes, or auto-save.

## 2. Source Identity
- Worktree path: C:\Users\jusin\OneDrive\Documents\Custom Office Templates
- Branch: master
- Checkpoint: 3aa61a0
- Tag: button1-execution-gate-source-call-network-boundary-review-v1
- Dirty state: acknowledged as pre-existing and unrelated; allowed for this docs-only slice under staged-set restriction.

## 3. Reviewed Input
- docs/button1_execution_gate_source_call_network_boundary_review_v1.md

## 4. Current Locked Runtime State
- Registry candidate count: 2
- Enabled provider IDs:
  - ufc_official_events
- Disabled provider IDs:
  - one_fc_official_events
- Execution gate decision: deny
- Remaining reason code:
  - execution_gate_operator_approval_missing
- provider execution: false
- network calls: false
- source calls: false
- scraping: false
- queue writes: false
- database writes: false
- customer PDF/report generation: false
- Button 2 promotion: false
- learning/calibration writes: false
- auto-save: false
- save allowed: false

## 5. Contract Design Conclusion
- Source-call/network authorization contract design may proceed.
- No implementation is approved.
- No real token use is approved.
- No provider execution is approved.
- No network/source call is approved.
- No scraping is approved.
- No write is approved.
- No Button 2 promotion is approved.
- No customer report generation is approved.
- No learning/calibration update is approved.
- No auto-save is approved.

## 6. Authorization Contract Envelope
Define the future request contract fields:
- provider_id
- provider_enabled
- operator_approval_present
- operator_approval_valid
- source_call_authorization_present
- source_call_authorization_valid
- requested_http_method
- requested_source_url_or_domain
- expected_response_type
- max_result_count
- timeout_seconds
- provenance_required
- save_requested
- customer_output_requested
- learning_update_requested
- button2_promotion_requested

## 7. Required Allow Conditions
A future source/network call may be considered only when:
- provider_id is approved
- provider is enabled
- operator approval is present and valid
- source-call authorization is present and valid
- requested source/domain is approved
- requested HTTP method is allowed
- expected response type is supported
- max result count is bounded
- timeout is bounded
- provenance capture is required
- no-write invariants are active
- audit diagnostics are active

## 8. Required Deny Conditions
Deny if:
- provider is disabled
- provider ID is unknown
- provider ID is not approved
- operator approval is missing
- operator approval is invalid
- source-call authorization is missing
- source-call authorization is invalid
- source URL/domain is unapproved
- requested HTTP method is unapproved
- expected response type is unsupported
- max result count is unbounded
- timeout is unbounded
- provenance capture is missing
- request attempts save/write
- request attempts Button 2 promotion
- request attempts customer output generation
- request attempts learning/calibration update
- token secret is exposed
- audit fields are missing

## 9. Source and Network Boundary
- First future source-call implementation must be read-only source retrieval only.
- No queue save.
- No database write.
- No report generation.
- No Button 2 promotion.
- No learning/calibration update.
- No auto-save.
- No credential leakage.
- No scraping bypass.
- No unbounded network call.
- No recursive crawling.
- No external call without explicit authorization.

## 10. Provider Scope
- First provider eligible for future source-call authorization review: ufc_official_events.
- one_fc_official_events remains disabled.
- No more than one provider may be active in the first source-call authorization implementation.
- Unknown providers fail closed.
- Provider-disabled state fails closed.

## 11. Operator Approval Boundary
- Operator approval alone does not authorize network/source calls.
- Operator approval alone does not authorize save.
- Operator approval alone does not authorize Button 2 promotion.
- Operator approval alone does not authorize customer PDF/report generation.
- Operator approval alone does not authorize learning/calibration writes.
- Operator token secret must never be hardcoded, returned, logged, audited, or written to proof docs.
- Audit may record token_present and token_valid booleans only.

## 12. Source-Call Authorization Boundary
- Source-call authorization must be separate from operator approval.
- Source-call authorization must be scoped to provider_id.
- Source-call authorization must be scoped to approved domain/source URL.
- Source-call authorization must be scoped to method.
- Source-call authorization must be scoped to response type.
- Source-call authorization must expire or be single-use if later implemented.
- Invalid or missing authorization fails closed.

## 13. Provenance Contract
Future source-call output must capture:
- provider_id
- source URL/domain
- request timestamp
- response timestamp
- event identity fields
- bout identity fields
- extracted fighter names
- source freshness
- source trust tier
- parser status
- result count
- provenance completeness
- manual review flag
- no-write flags

## 14. Parser Failure Contract
- Parser failure must not equal provider-disabled.
- Parser failure must not equal token-missing.
- Parser failure must not equal no-source-authorization.
- Parser failure must be reported as parser_failure.
- Parser failure fails closed.
- Parser failure blocks save readiness.
- Parser failure routes to manual review if relevant.

## 15. Stale-Feed Contract
- Stale output fails closed.
- Unavailable output fails closed.
- Stale/unavailable must be distinguished from provider-disabled.
- Stale/unavailable must be distinguished from token-missing.
- Stale/unavailable must be distinguished from parser failure.
- Stale/unavailable blocks save readiness.
- Stale/unavailable requires manual review or refresh before save.

## 16. Response Contract
Future gate response must include:
- decision
- allowed
- provider_id
- provider_enabled
- operator_approval_present
- operator_approval_valid
- source_call_authorization_present
- source_call_authorization_valid
- source_domain_authorized
- http_method_authorized
- response_type_supported
- provenance_required
- provenance_complete
- reason_codes
- audit_fields
- no_write_flags
- provider_execution_performed
- network_calls_performed
- source_calls_performed
- queue_write_performed
- database_write_performed
- customer_pdf_generation_performed
- button2_promotion_performed
- learning_write_performed
- calibration_write_performed
- auto_save_performed

## 17. Explicit No-Write Invariants
- queue_write_performed must remain false.
- database_write_performed must remain false.
- customer_pdf_generation_performed must remain false.
- button2_promotion_performed must remain false.
- learning_write_performed must remain false.
- calibration_write_performed must remain false.
- auto_save_performed must remain false.
- save_allowed must remain false unless a later separate save-readiness gate approves it.

## 18. Required Future Tests
- provider disabled denies source call.
- unknown provider denies source call.
- enabled provider without operator approval denies source call.
- enabled provider with invalid operator approval denies source call.
- enabled provider with valid operator approval but missing source-call authorization denies source call.
- enabled provider with valid operator approval but invalid source-call authorization denies source call.
- unapproved source domain denies source call.
- unapproved HTTP method denies source call.
- unsupported response type denies source call.
- unbounded result count denies source call.
- unbounded timeout denies source call.
- valid authorization does not trigger queue/database writes.
- valid authorization does not trigger customer PDF/report generation.
- valid authorization does not trigger Button 2 promotion.
- valid authorization does not trigger learning/calibration.
- parser failure fails closed and is reported separately.
- stale feed fails closed and is reported separately.
- unavailable feed fails closed and is reported separately.
- provenance missing blocks save readiness.
- provenance conflict routes manual review.
- token secret never appears in response, logs, audit, or proofs.
- one_fc_official_events remains disabled.
- no more than one provider enabled.
- pre-existing dirty files are not staged.

## 19. Required Future Implementation Gates
- source-call/network authorization contract review
- provider execution adapter activation design
- source-call implementation readiness gate
- provenance contract implementation readiness gate
- parser/stale-feed implementation readiness gate
- runtime validation gate
- no-write invariant proof

## 20. Explicit Blocked Scope
- No implementation in this slice.
- No real token use.
- No provider execution.
- No network/source calls.
- No scraping.
- No app.py change.
- No template change.
- No registry JSON change.
- No provider enabled-state change.
- No queue/database writes.
- No Button 2 promotion.
- No customer PDF/report generation.
- No learning/calibration writes.
- No auto-save.
- No worktree cleanup.
- No staging of pre-existing dirty files.

## 21. Final Contract-Design Verdict
BUTTON1_SOURCE_CALL_NETWORK_AUTHORIZATION_CONTRACT_DESIGN_READY_FOR_REVIEW_ONLY

## 22. Safe Next Action
Docs-only source-call/network authorization contract review and file-scope gate.

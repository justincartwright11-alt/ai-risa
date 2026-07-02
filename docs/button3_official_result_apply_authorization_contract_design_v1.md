# Button 3 Official Result Apply Authorization Contract Design v1

## 1. Baseline
- branch: master
- HEAD: 000d35f
- tag: button3-official-result-identity-match-contract-design-review-v1

## 2. Purpose
Define the apply-authorization contract for Button 3 as a design-only gate that controls who or what may request apply authority and under what explicit operator approval conditions.

This contract preserves fail-closed behavior and does not authorize implementation or mutation.

## 3. Source Artifacts Reviewed
- docs/button3_official_result_identity_match_contract_design_review_v1.md
- docs/button3_official_result_source_trust_contract_design_review_v1.md
- docs/button3_official_result_apply_ledger_learning_boundary_review_v1.md

## 4. Scope And Non-Scope
In scope:
- request eligibility for apply authorization
- operator approval prerequisites and decision controls
- deterministic request/response contract for future implementation
- fail-closed deny states and no-authority defaults

Out of scope:
- endpoint implementation
- apply execution
- result persistence
- any mutation path beyond authorization design

## 5. Authorization Subjects (Who/What May Request)
Allowed request subjects for future consideration are narrowly defined as:
- operator_dashboard_button3_apply_request: human operator request initiated from Button 3 review surface
- operator_dashboard_button3_apply_replay_request: explicit operator replay request using prior denied/expired operation context

All other request subjects are denied by default, including:
- background schedulers
- autonomous jobs
- external webhooks
- Button 1 flows
- Button 2 flows
- test harness shortcuts outside explicit operator-gated mode

## 6. Operator Approval Requirements
A request is eligible only if all required operator approval controls are present:
- explicit operator identity present (operator_id)
- explicit operator action intent present (approval_action=authorize_apply)
- approval timestamp present and inside bounded validity window
- approval scope bound to one canonical fight identity key
- approval scope bound to one source_result_record_id
- approval scope bound to one operation_id (single-use token model)
- no replay of consumed, expired, or revoked approval
- no conflict flag from source-trust or identity-match gate states

Approval display alone is never authority.

## 7. Required Precondition Inputs
Before future apply authorization can return eligible, the following precondition evidence must be carried in request context:
- source_trust_state
- identity_match_state
- canonical_fight_identity_key
- source_result_record_id
- event_identity_fingerprint
- fighter_identity_fingerprint_a
- fighter_identity_fingerprint_b
- operator_id
- approval_action
- approval_timestamp
- approval_operation_id
- request_id

Missing any required precondition input results in deny.

## 8. Deterministic Authorization Decision States
- apply_authorization_eligible
- apply_authorization_denied_missing_operator
- apply_authorization_denied_missing_approval
- apply_authorization_denied_approval_expired
- apply_authorization_denied_approval_consumed
- apply_authorization_denied_scope_mismatch
- apply_authorization_denied_source_trust_not_passed
- apply_authorization_denied_identity_match_not_passed
- apply_authorization_denied_conflict_detected
- apply_authorization_denied_unknown_state

## 9. Fail-Closed Deny Rules
- If source trust is not in a trusted eligible state, deny.
- If identity match is not confirmed, deny.
- If operator identity is missing, deny.
- If operator approval action is missing or mismatched, deny.
- If approval is expired, consumed, or revoked, deny.
- If approval scope mismatches fight identity or result record, deny.
- If canonical fight identity key is missing, deny.
- If source result record id is missing, deny.
- If any conflict signal is raised, deny.
- If decision mapping is unknown, deny.

## 10. Request Contract (Design)
Required request fields for any future apply-authorization API:
- request_id
- operation_id
- requester_subject
- operator_id
- approval_action
- approval_timestamp
- approval_operation_id
- canonical_fight_identity_key
- source_result_record_id
- source_trust_state
- identity_match_state
- event_identity_fingerprint
- fighter_identity_fingerprint_a
- fighter_identity_fingerprint_b
- client_surface
- requested_at_utc

Design contract rule: partial payloads are invalid and must fail closed.

## 11. Response Contract (Design)
Required response fields:
- operation_id
- request_id
- authorization_state
- authorized (boolean)
- deny_reason_code
- deny_reason_detail
- required_next_gate
- operator_action_required
- approval_consumed (boolean)
- conflict_detected (boolean)
- evaluated_at_utc

Design contract rule:
- authorized=true only when state is apply_authorization_eligible.
- all deny states must return authorized=false with explicit reason code.

## 12. Authority Boundary (No Mutation Granted)
This design grants no authority for:
- official result save
- apply execution
- database write
- queue write
- accuracy-ledger write
- Structural Accuracy Ledger update
- Calibration Deviation Index write
- controlled learning candidate creation
- learning application
- calibration application
- GCID update
- customer report update
- Button 1 source execution
- Button 2 report generation

## 13. Future Implementation Requirements
Any future implementation must include:
- exact allowed files
- exact blocked files
- request contract validation tests
- response contract validation tests
- deny/allow matrix tests for authorization states
- operator approval expiry and replay denial tests
- source-trust-not-passed denial tests
- identity-match-not-passed denial tests
- scope-mismatch denial tests
- no-save/no-write tests
- no-ledger tests
- no-learning tests
- no-calibration tests
- no-GCID tests
- no-customer-output tests
- staged-set guard
- proof/review artifact before any expanded authority

## 14. Sequence Confirmation
The required separated gate chain remains:
- Source Trust
- Identity Match
- Apply Authorization
- Accuracy Ledger
- Controlled Learning
- GCID

## 15. Review Decision
This apply-authorization contract is approved as design-only Gate 3.

It defines authorization controls only and grants no implementation or mutation authority.

## 16. Final Verdict
BUTTON3_OFFICIAL_RESULT_APPLY_AUTHORIZATION_CONTRACT_DESIGN_LOCKED_FAIL_CLOSED
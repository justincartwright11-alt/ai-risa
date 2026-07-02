# Button 3 Official Result Accuracy Ledger Contract Design v1

## 1. Baseline
- branch: master
- HEAD: 74e45a6
- tag: button3-official-result-apply-authorization-contract-design-review-v1

## 2. Purpose
Define the Button 3 accuracy-ledger contract as a design-only gate for how accuracy evidence may be recorded in the future.

This design separates outcome accuracy, method accuracy, timing accuracy, and structural accuracy.

This design explicitly prevents winner-only learning and blocks lucky prediction reinforcement.

This design does not authorize implementation or mutation.

## 3. Source Artifacts Reviewed
- docs/button3_official_result_apply_authorization_contract_design_review_v1.md
- docs/button3_official_result_apply_authorization_contract_design_v1.md
- docs/button3_official_result_apply_ledger_learning_boundary_review_v1.md

## 4. Scope And Non-Scope
In scope:
- ledger evidence domain model and field contract
- separated accuracy dimensions and scoring boundaries
- preconditions required before any future ledger mutation is eligible
- fail-closed states for incomplete, contradictory, stale, and lucky-only evidence

Out of scope:
- endpoint implementation
- persistence implementation
- learning candidate generation
- calibration updates
- GCID updates
- customer-output updates

## 5. Required Upstream Preconditions
No future ledger mutation may be considered unless all upstream gates have passed:
- source trust gate passed
- identity match gate passed
- apply authorization gate passed

If any required upstream gate is missing, non-passed, stale, ambiguous, or unknown, ledger mutation must be denied.

## 6. Accuracy Dimensions (Separated)
The ledger contract must store and evaluate separate dimensions:
- outcome_accuracy: predicted winner versus official winner
- method_accuracy: predicted finish/decision method versus official method
- timing_accuracy: predicted round/time band versus official round/time
- structural_accuracy: evidence quality and structure alignment confidence

Design rule: no collapsed single-score may replace dimension-level recording.

## 7. Evidence Record Contract (Design)
Required evidence fields for any future write path:
- ledger_operation_id
- request_id
- canonical_fight_identity_key
- source_result_record_id
- source_trust_state
- identity_match_state
- apply_authorization_state
- official_winner
- official_method
- official_round
- official_time
- predicted_winner
- predicted_method
- predicted_round
- predicted_time
- outcome_accuracy_state
- method_accuracy_state
- timing_accuracy_state
- structural_accuracy_state
- structural_evidence_score
- contradiction_flags
- stale_evidence_flag
- lucky_prediction_flag
- operator_id
- evaluated_at_utc

Partial records are invalid and must fail closed.

## 8. Deterministic Ledger Decision States
- accuracy_ledger_eligible
- accuracy_ledger_denied_missing_preconditions
- accuracy_ledger_denied_source_trust_not_passed
- accuracy_ledger_denied_identity_match_not_passed
- accuracy_ledger_denied_apply_authorization_not_passed
- accuracy_ledger_denied_incomplete_evidence
- accuracy_ledger_denied_contradictory_evidence
- accuracy_ledger_denied_stale_evidence
- accuracy_ledger_denied_winner_only_signal
- accuracy_ledger_denied_lucky_prediction_signal
- accuracy_ledger_denied_unknown_state

## 9. Winner-Only And Lucky-Reinforcement Guardrails
Winner-only guard:
- If only winner matches while method/timing/structural dimensions are absent or failed, mutation eligibility is denied.

Lucky reinforcement guard:
- If winner appears correct but structural evidence is weak, contradictory, or insufficient, mutation eligibility is denied.
- Lucky prediction signals must never produce a positive reinforcement path.

Design rule:
- Outcome-only agreement is insufficient for reinforcement eligibility.

## 10. Structural Accuracy Contract
Structural accuracy must remain independent from outcome correctness and must include:
- source evidence completeness
- contradiction detection across records
- provenance consistency checks
- temporal freshness checks
- identity and event alignment checks

If structural accuracy is insufficient, ledger eligibility is denied regardless of winner agreement.

## 11. Fail-Closed Rules
- Missing required fields deny.
- Missing upstream gate pass states deny.
- Contradictory result records deny.
- Stale evidence deny.
- Winner-only signal deny.
- Lucky prediction signal deny.
- Unknown state mapping deny.

Default decision is deny unless all required conditions are explicitly satisfied.

## 12. Authority Boundary (No Mutation Granted)
This design grants no authority for:
- ledger write execution
- official result save
- apply execution
- database write
- queue write
- controlled learning candidate creation
- learning application
- calibration application
- Calibration Deviation Index write
- GCID update
- customer report update
- Button 1 source execution
- Button 2 report generation

## 13. Future Implementation Requirements
Any future implementation must include:
- exact allowed files
- exact blocked files
- request/response contract validation tests
- dimension-separation tests (outcome/method/timing/structural)
- winner-only denial tests
- lucky-prediction denial tests
- stale and contradictory evidence denial tests
- upstream precondition gate denial tests
- no-save/no-write/no-learning/no-calibration/no-GCID/no-customer-output tests
- staged-set guard
- proof/review artifact before any expanded authority

## 14. Sequence Confirmation
The protected gate chain remains:
- Source Trust
- Identity Match
- Apply Authorization
- Accuracy Ledger
- Controlled Learning
- GCID

No gate collapse is authorized by this design.

## 15. Review Decision
This accuracy-ledger contract is approved as design-only Gate 4.

It defines future evidence and scoring boundaries only and grants no implementation or mutation authority.

## 16. Final Verdict
BUTTON3_OFFICIAL_RESULT_ACCURACY_LEDGER_CONTRACT_DESIGN_LOCKED_FAIL_CLOSED
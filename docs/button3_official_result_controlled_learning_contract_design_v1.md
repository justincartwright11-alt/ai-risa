# Button 3 Official Result Controlled Learning Contract Design v1

## 1. Baseline
- branch: master
- HEAD: 67a3d99
- tag: button3-official-result-accuracy-ledger-contract-design-review-v1

## 2. Purpose
Define the controlled-learning contract as a design-only gate for when an accuracy result may become a learning candidate in the future.

This design blocks winner-only learning and lucky-prediction learning.

This design separates learning candidate creation from learning application.

This design does not authorize implementation or mutation.

## 3. Source Artifacts Reviewed
- docs/button3_official_result_accuracy_ledger_contract_design_review_v1.md
- docs/button3_official_result_accuracy_ledger_contract_design_v1.md
- docs/button3_official_result_apply_ledger_learning_boundary_review_v1.md

## 4. Scope And Non-Scope
In scope:
- learning candidate eligibility contract
- candidate evidence requirements and deny states
- explicit separation from learning application
- fail-closed handling for weak, stale, contradictory, and lucky-only signals

Out of scope:
- learning application implementation
- model parameter updates
- calibration updates
- GCID updates
- customer-output updates
- endpoint implementation

## 5. Mandatory Upstream Gate Preconditions
No controlled-learning candidate may be eligible unless all required upstream gates are passed:
- source trust passed
- identity match passed
- apply authorization passed
- accuracy-ledger review passed

If any upstream gate is missing, non-passed, stale, ambiguous, revoked, or unknown, candidate eligibility is denied.

## 6. Candidate Signal Requirements
A future candidate record must include all required signal dimensions:
- outcome signal (winner correctness)
- method signal (finish/decision correctness)
- timing signal (round/time-band correctness)
- structural signal (evidence integrity and consistency)

Design rule: no candidate may be created from outcome-only signals.

## 7. Winner-Only And Lucky-Prediction Blocks
Winner-only learning block:
- winner-only correctness without method/timing/structural support is denied.

Lucky-prediction learning block:
- if winner appears correct but structural evidence is weak, contradictory, sparse, or stale, candidate eligibility is denied.
- lucky prediction indicators must never open a candidate path.

## 8. Candidate Record Contract (Design)
Required fields for any future controlled-learning candidate request:
- candidate_operation_id
- request_id
- canonical_fight_identity_key
- source_result_record_id
- source_trust_state
- identity_match_state
- apply_authorization_state
- accuracy_ledger_review_state
- outcome_accuracy_state
- method_accuracy_state
- timing_accuracy_state
- structural_accuracy_state
- structural_evidence_score
- winner_only_signal_flag
- lucky_prediction_signal_flag
- contradiction_flags
- stale_evidence_flag
- operator_id
- proposed_at_utc

Partial payloads are invalid and must fail closed.

## 9. Deterministic Candidate Decision States
- controlled_learning_candidate_eligible
- controlled_learning_candidate_denied_missing_preconditions
- controlled_learning_candidate_denied_source_trust_not_passed
- controlled_learning_candidate_denied_identity_match_not_passed
- controlled_learning_candidate_denied_apply_authorization_not_passed
- controlled_learning_candidate_denied_accuracy_ledger_not_reviewed
- controlled_learning_candidate_denied_incomplete_signals
- controlled_learning_candidate_denied_winner_only_signal
- controlled_learning_candidate_denied_lucky_prediction_signal
- controlled_learning_candidate_denied_contradictory_evidence
- controlled_learning_candidate_denied_stale_evidence
- controlled_learning_candidate_denied_unknown_state

## 10. Candidate Creation Versus Learning Application
Controlled-learning candidate creation is a preparation step only.

It does not authorize:
- learning application
- model behavior change
- weighting change
- calibration change
- GCID change

Learning application requires a separate future gate and remains blocked.

## 11. Fail-Closed Rules
- Missing required fields deny.
- Missing or non-passed upstream gate states deny.
- Winner-only signal deny.
- Lucky-prediction signal deny.
- Contradictory evidence deny.
- Stale evidence deny.
- Unknown decision state deny.

Default decision is deny unless all requirements are explicitly satisfied.

## 12. Authority Boundary (No Mutation Granted)
This design grants no authority for:
- candidate persistence implementation
- learning application
- calibration application
- Calibration Deviation Index write
- GCID update
- customer report update
- ledger write execution
- official result save
- apply execution
- database write
- queue write
- Button 1 source execution
- Button 2 report generation

## 13. Future Implementation Requirements
Any future implementation must include:
- exact allowed files
- exact blocked files
- candidate request/response contract tests
- upstream gate precondition denial tests
- winner-only denial tests
- lucky-prediction denial tests
- contradictory/stale evidence denial tests
- explicit candidate-versus-application separation tests
- no-learning-application tests
- no-calibration/no-GCID/no-customer-output tests
- staged-set guard
- proof/review artifact before any expanded authority

## 14. Sequence Confirmation
Protected sequence remains:
- Source Trust
- Identity Match
- Apply Authorization
- Accuracy Ledger
- Controlled Learning
- GCID

No gate collapse is authorized by this design.

## 15. Review Decision
This controlled-learning contract is approved as design-only Gate 5.

It defines candidate eligibility boundaries only and grants no implementation or mutation authority.

## 16. Final Verdict
BUTTON3_OFFICIAL_RESULT_CONTROLLED_LEARNING_CONTRACT_DESIGN_LOCKED_FAIL_CLOSED
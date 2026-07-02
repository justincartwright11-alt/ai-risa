# Button 3 Official Result Identity Match Contract Design v1

## 1. Baseline
- branch: master
- HEAD: 2a29635
- tag: button3-official-result-source-trust-contract-design-review-v1
- active planning month: July 2026

## 2. Purpose
Define the identity-match contract required to prove an official result belongs to the exact fight record before any future apply path is considered.

This design is docs-only and does not authorize implementation, save, apply, ledger write, learning, calibration, GCID update, or customer output.

## 3. Source Artifacts Reviewed
- docs/button3_official_result_source_trust_contract_design_v1.md
- docs/button3_official_result_source_trust_contract_design_review_v1.md
- docs/button3_official_result_apply_ledger_learning_boundary_review_v1.md

## 4. Identity Match Scope
Identity match must prove the same contest across all required dimensions:
- fighter A identity
- fighter B identity
- event identity
- event date context
- promotion context
- ruleset context
- weight class context
- bout sequence context when available

Identity match is Gate 2 and is separate from source trust (Gate 1).

## 5. Required Identity Fields
- source_result_record_id (or stable source key)
- source_url
- source_tier
- source_timestamp
- event_name_raw
- event_date_raw
- promotion_raw
- ruleset_raw
- weight_class_raw
- fighter_a_name_raw
- fighter_b_name_raw
- fighter_a_profile_refs (if available)
- fighter_b_profile_refs (if available)
- winner_raw
- method_raw
- round_raw
- time_raw
- alias_resolution_notes
- rematch_disambiguation_notes
- discrepancy_notes
- operator_review_status
- identity_match_state

## 6. Deterministic Identity Match States
- identity_match_confirmed
- fighter_alias_needs_review
- fighter_order_mismatch_blocked
- rematch_ambiguous_blocked
- duplicate_fight_ambiguous_blocked
- event_page_mismatch_blocked
- event_date_mismatch_blocked
- promotion_mismatch_blocked
- ruleset_mismatch_blocked
- weight_class_mismatch_blocked
- stale_card_context_blocked
- incomplete_identity_blocked
- unknown_identity_state_blocked

## 7. Fail-Closed Identity Rules
- Missing fighter A or fighter B identity blocks mutation.
- Aliases without deterministic resolution block mutation.
- Fighter order mismatch blocks mutation unless resolved with explicit identity proof.
- Rematch ambiguity blocks mutation.
- Duplicate fight ambiguity blocks mutation.
- Wrong event page blocks mutation.
- Event/date mismatch blocks mutation.
- Promotion mismatch blocks mutation.
- Ruleset mismatch blocks mutation.
- Weight class mismatch blocks mutation.
- Stale card context blocks mutation.
- Incomplete identity context blocks mutation.
- Unknown identity state blocks mutation.
- Operator review display is not mutation authority.

## 8. Explicit Ambiguity Blocks
The following are always blocked until separately resolved:
- alias collisions (same surname, nickname, transliteration variants)
- rematch collisions (same fighters, different dates)
- duplicate event naming collisions
- wrong event page carrying similarly named fighters
- stale pre-event card snapshots presented as final result pages
- conflicting result records for same bout identity key

## 9. Separation From Later Gates
Identity match is only Gate 2.

It does not authorize:
- official result save
- apply endpoint execution
- accuracy-ledger write
- Structural Accuracy Ledger update
- controlled learning candidate creation
- learning application
- calibration application
- GCID update
- customer output update

Each remains blocked until separate later contracts are approved.

## 10. Future Test Requirements
Any future implementation must include, at minimum:
1. Exact fighter A and fighter B identity confirmation.
2. Alias resolution deterministic pass path.
3. Alias unresolved blocked path.
4. Fighter order mismatch blocked.
5. Rematch ambiguity blocked.
6. Duplicate fight ambiguity blocked.
7. Wrong event page blocked.
8. Event/date mismatch blocked.
9. Promotion mismatch blocked.
10. Ruleset mismatch blocked.
11. Weight class mismatch blocked.
12. Stale card context blocked.
13. Incomplete identity context blocked.
14. Unknown identity state blocked.
15. No official result save.
16. No apply execution.
17. No database write.
18. No queue write.
19. No ledger write.
20. No learning mutation.
21. No calibration mutation.
22. No GCID write.
23. No customer output.
24. Operator approval not consumed as mutation authority.

## 11. Risks and Guardrails
- alias accepted as identity proof without deterministic mapping
- rematch confusion writes result to wrong historical bout
- duplicate fight records collapse into one identity key
- stale event snapshot matched to wrong final result
- event landing page treated as exact bout proof
- source trust mistaken for identity certainty
- identity match mistaken for apply authority
- Button 1 or Button 2 authority inferred from Button 3 identity logic

## 12. Review Decision
This identity-match contract is approved as design-only Gate 2.

No implementation or mutation authority is granted by this design.

## 13. Sequence Confirmation
Required separation remains:
- Source Trust
- Identity Match
- Apply Authorization
- Accuracy Ledger
- Controlled Learning
- GCID

## 14. Final Verdict
BUTTON3_OFFICIAL_RESULT_IDENTITY_MATCH_CONTRACT_DESIGN_LOCKED_FAIL_CLOSED

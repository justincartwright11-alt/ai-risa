# official-source-one-record-guardrails-review-v1

Reviewed input:
- docs/official_source_one_record_lookup_guardrails_v1.md

## 1) Risk Gaps
- Confidence threshold is referenced but not numerically defined. This can cause inconsistent operator decisions.
- Conflict resolution policy does not define tie-break behavior when Tier A and Tier B disagree.
- Approval replay risk is mentioned indirectly (possible stale token) but there is no explicit anti-replay mechanism in the design contract.
- Data freshness is not bounded (for example, how old a source date can be before manual review is forced).

## 2) Missing Guardrails
- Require an explicit source domain allowlist enforcement mode: exact host match or vetted subdomain match, with deny-by-default.
- Require deterministic parser confidence criteria for winner extraction (for example, minimum extraction certainty score).
- Require a mandatory identity lock check between selected_key context and citation page entities before any write-eligible state.
- Require immutable audit hash/fingerprint over selected_key + source citation + extracted winner for traceability.

## 3) Ambiguous Source Rules
- Tier B is described as review-gated, but the exact conditions for promotion from manual review to approval-ready are not defined.
- "Official or highly reliable" is conceptually clear but operationally ambiguous without a machine-checkable confidence threshold and corroboration rule.
- Source date acceptance is unspecified (event date versus publication date precedence).

## 4) Approval/Write Boundaries
- Boundary direction is strong: preview first, explicit approval before write, no silent mutations.
- Boundary needs one additional explicit rule: approval must be bound to a single selected_key and a citation fingerprint, and expire quickly.
- Boundary should explicitly state that any change to citation fields invalidates approval and forces new preview.

## 5) Test Coverage Needed Before Preview Implementation
- Contract validation tests:
  - Reject multi-key and invalid mode/phase combinations.
  - Reject execute/apply intents without valid preview state.
- Source policy tests:
  - Allowlist enforcement for official domains and deny-by-default for others.
  - Tier B handling forces manual review unless corroboration rule is satisfied.
- Citation integrity tests:
  - Missing URL/title/date always blocked from write-eligible state.
  - Identity mismatch between selected_key entities and citation content forces manual review.
- Safety boundary tests:
  - No page-load calls.
  - No retries and no background execution.
  - No writes and scoring_semantics_changed=false across dry-run/lookup-preview phases.
- Approval integrity tests:
  - Approval invalidates on any selected_key or citation change.
  - Approval expiry is enforced.
  - Replay attempt is rejected.

## 6) Recommendation
- Recommendation: CONDITIONAL GO.
- Rationale: The design is mature enough to proceed to preview design/implementation planning, but only after adding explicit definitions for confidence threshold, domain matching policy, approval binding/expiry, and Tier B corroboration behavior.

CONDITIONAL GO: safe only after listed guardrail edits

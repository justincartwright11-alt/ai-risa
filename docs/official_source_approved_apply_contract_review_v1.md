# official-source-approved-apply-contract-review-v1

## 1. Review scope
Review the docs-only contract defined in `official_source_approved_apply_contract_v1.md` against the already locked guardrail, acceptance-gate, and approved-write design documents.

This review is design-only. It introduces no implementation, no runtime wiring, and no behavior change.

## 2. Overall assessment
The approved-apply contract is directionally correct and already preserves the most important safety boundaries:
- one-record only
- explicit operator invocation only
- no batch apply
- no page-load apply
- no automatic apply
- no write without `acceptance_gate.state == write_eligible`
- no write without `acceptance_gate.write_eligible == true`
- manual actual-results file as the only allowed future write target
- rollback requirement present

However, the contract is not yet tight enough to begin implementation design safely without further amendment.

## 3. Approval-token safety
Assessment:
- The contract correctly requires an approval token.
- The contract correctly requires single-use and replay-safe behavior.
- The contract correctly requires binding to `selected_key`, `citation_fingerprint`, `source_url`, and `extracted_winner`.

Gap:
- The contract does not yet require the token to carry or validate an issuance timestamp, expiry timestamp, or explicit consumed/revoked state in the contract surface.
- The contract does not yet require the token to bind to `source_date` even though earlier design documents include `source_date` as a bound approval field.

Review result:
- Strong direction, but incomplete for anti-replay and expiry reviewability.

## 4. selected_key binding integrity
Assessment:
- The contract correctly requires exactly one `selected_key`.
- The contract correctly requires the request key to match the approval binding and preview snapshot.

Gap:
- The contract says the key must still resolve to the same waiting-row identity in future implementation, but the request contract does not yet require a stable identity echo such as `record_fight_id` or normalized row identity in the request-side approval binding.

Review result:
- Adequate baseline, but stronger identity anchoring is needed.

## 5. citation_fingerprint binding integrity
Assessment:
- The contract correctly makes `citation_fingerprint` mandatory.
- The contract correctly requires exact match across approval binding, citation, and acceptance gate.

Gap:
- The contract does not define the canonical fingerprint input set inside the apply-contract doc itself.
- That definition exists in earlier design context, but the apply contract should restate the canonical fields to prevent drift.

Review result:
- Good core rule, but canonicalization needs to be explicit in the contract.

## 6. source_url binding integrity
Assessment:
- The contract correctly requires exact `source_url` match and policy-compliant HTTPS.

Gap:
- The contract does not explicitly require that the bound `source_url` equals the final canonical citation URL after any redirect normalization already performed at preview time.

Review result:
- Sufficient in spirit, but canonical URL normalization should be stated explicitly.

## 7. extracted_winner binding integrity
Assessment:
- The contract correctly requires exact `extracted_winner` match.
- The contract correctly requires `proposed_write.actual_winner` to equal previewed `extracted_winner`.

Gap:
- The contract does not explicitly say winner normalization rules must be identical between preview and apply validation.

Review result:
- Correct boundary, but normalization parity should be stated.

## 8. acceptance_gate state requirements
Assessment:
- The contract correctly requires `state == write_eligible`.
- The contract correctly requires `write_eligible == true`.
- The contract correctly blocks `manual_review` and `rejected`.
- The contract correctly blocks Tier B alone.

Gap:
- The contract does not explicitly require fresh server-side re-evaluation of acceptance-gate inputs before any future apply, rather than trusting a client-returned preview snapshot alone.

Review result:
- Good state policy, but the revalidation boundary must be explicit.

## 9. Deny/manual-review boundaries
Assessment:
- The contract has a strong minimum deny-state set.
- The contract preserves manual-review blocking outcomes.

Gap:
- The contract does not yet separate contract-level validation failures from gate-policy failures in a way that makes future status-code mapping deterministic.
- The contract also leaves one ambiguity: whether `identity_conflict` is always deny or sometimes manual-review.

Review result:
- Strong coverage, but classification and transport mapping should be tightened.

## 10. Write target restriction
Assessment:
- The contract correctly restricts the future target to `ops/accuracy/actual_results_manual.json` only.
- The contract clearly disallows the other actual-results files and all batch/external destinations.

Gap:
- None material at the contract level.

Review result:
- Strong and sufficient.

## 11. Rollback guarantees
Assessment:
- The contract correctly requires exact restoration of `ops/accuracy/actual_results_manual.json` on failure.
- The contract correctly disallows surviving partial writes.

Gap:
- The contract does not yet require a pre-write snapshot/hash/version field in the audit contract to make rollback verification explicit.

Review result:
- Correct requirement, but auditability of rollback should be stronger.

## 12. Replay/expiry protection
Assessment:
- The contract clearly requires replay-safe and single-use token behavior.

Gap:
- The contract does not expose explicit fields or invariants for token TTL, issued-at time, consumed-at time, or replay-detection result codes beyond high-level denial names.

Review result:
- Needs amendment before implementation design.

## 13. No-batch / no-page-load / no-auto-apply guarantees
Assessment:
- The contract is explicit that apply is one-record only.
- The contract is explicit that batch, page-load, and automatic apply are forbidden.

Gap:
- None material for the contract layer.

Review result:
- Strong and sufficient.

## 14. Audit field completeness
Assessment:
- The contract includes a solid audit envelope for allow/deny outcomes.

Gaps:
- `attempted_sources` and `provider_attempted` are not present in the apply contract audit schema even though they are present in the preview path and approved-write design context.
- No explicit rollback audit fields are defined, such as rollback attempted, rollback succeeded, and pre-write snapshot/hash identifiers.
- No approval-token metadata fields are defined in audit, such as token id or expiry decision basis.

Review result:
- Good base, but incomplete for forensics and rollback proof.

## 15. Missing guardrails
The following contract amendments are recommended before any implementation design:
- Require server-side revalidation from authoritative preview-derived fields rather than trusting client-supplied `preview_snapshot` alone.
- Add explicit approval-token contract fields or invariants for `issued_at_utc`, `expires_at_utc`, single-use consumption, and replay rejection.
- Add `source_date` to the required approval binding set in the apply contract to match prior design documents.
- Restate the canonical citation-fingerprint field set directly in the apply contract.
- Require a stable identity binding field such as `record_fight_id` or equivalent normalized row identity in the apply binding surface.
- Add rollback audit fields and pre-write snapshot/hash requirements for the manual actual-results file.
- Clarify deterministic status-code mapping for schema failure, deny, and manual-review outcomes.
- Clarify whether `identity_conflict` is always deny in apply, or can ever remain manual-review.

## 16. Test coverage required before implementation
Before any implementation design proceeds, the contract should require tests for:
- exact one-record request enforcement
- token missing / expired / replayed denial
- token-binding mismatch denial for each bound field
- changed `selected_key` denial
- changed `citation_fingerprint` denial
- changed `source_url` denial
- changed `extracted_winner` denial
- changed `source_date` denial once added to the apply contract
- `manual_review` and `rejected` acceptance-gate blocking
- Tier B-only blocking
- manual actual-results target-only enforcement
- rollback restoring the exact pre-write manual file
- no page-load apply behavior
- no auto-apply behavior
- no batch apply behavior
- no scoring semantics change
- audit completeness for success, denial, and rollback

## 17. Go / no-go recommendation
Recommendation:
- CONDITIONAL GO: safe only after listed contract amendments

Rationale:
- The contract already enforces the major architectural guardrails.
- The remaining gaps are not implementation details; they are contract-level safety requirements.
- Starting approval-token or apply-guard implementation before tightening those fields would create avoidable ambiguity around replay protection, identity anchoring, rollback proof, and server-side revalidation.

## 18. Required amendments before implementation design
Minimum amendments required before any implementation-design slice:
1. Add explicit `source_date` binding to the apply contract.
2. Add explicit token expiry/issued/single-use invariants to the contract surface.
3. Add stable record identity binding beyond raw `selected_key`.
4. Add explicit server-side revalidation requirement rather than trusting client snapshot alone.
5. Add rollback audit fields and pre-write snapshot/hash requirements.
6. Add preview-context audit carry-forward fields such as `provider_attempted` and `attempted_sources`.
7. Clarify deterministic deny/manual-review classification for `identity_conflict` and related boundary cases.

---

Review outcome: CONDITIONAL GO: safe only after listed contract amendments
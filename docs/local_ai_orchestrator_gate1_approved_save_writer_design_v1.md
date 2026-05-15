# local-ai-orchestrator-gate1-approved-save-writer-design-v1

## 1. Purpose
Design the first real Gate 1 approved save writer for the AI-RISA Button 1 workflow. This writer will enable saving operator-approved fight candidates to the queue/database, but only after passing all required safety, provenance, and approval gates. This document defines the full design boundary, requirements, and constraints. **No code or write behavior is implemented in this slice.**

## 2. Current Locked Preconditions
- **Gate 1 token preview contract:** Preview-only validation of approval tokens.
- **Gate 1 token check preview:** Deterministic, fail-closed token check logic.
- **Gate 1 dry-run apply preview:** Simulates save, checks for would-save/blocked status, no mutation.
- **Gate 1 dry-run API:** Preview-only API route, no write or mutation.
- **Gate 1 dashboard preview wire:** UI displays only dry-run evidence, no save or write action.

## 3. Future Writer Scope
- Save only operator-approved, eligible Button 1 fight candidates to the queue/database.
- Enforce all approval, provenance, and safety gates before any write.
- Generate audit and rollback records for every write.
- Support idempotency and duplicate-apply protection.
- Expose a controlled, explicit save route (future slice).

## 4. Future Writer Non-Goals
- No auto-save or background write.
- No learning, calibration, or result apply.
- No PDF export or report generation.
- No weakening of approval, provenance, or safety gates.
- No modification of dashboard or preview API in this slice.

## 5. Required Approval Contract
- `operator_approved=true` (explicit operator action required)
- `valid_gate1_token` (token must be valid and not expired)
- `token_check_ok=true` (token check must pass)
- `dry_run.eligible_for_future_approval=true` (must pass dry-run preview)

## 6. Required Save Candidate Contract
- Candidate must match the dry-run previewed set.
- Must include all required fields: fight_id, event_id, fighter_a, fighter_b, source_button, provenance, etc.
- Must not be a fake or placeholder fight.

## 7. Required Duplicate/Conflict Check
- Must check for existing fights in queue/database with same fight_id or conflicting identity.
- Must block duplicate or conflicting candidates.
- Must enforce idempotency key per save attempt.

## 8. Required Source Provenance Check
- Source provenance must be present and valid (e.g., source_url, discovery method, timestamp).
- Must block candidates with missing or invalid provenance.

## 9. Required Audit Record
- Every save must generate an audit record: operator, timestamp, token, candidate details, action, result.
- Audit record must be immutable and queryable.

## 10. Required Rollback Pointer
- Every save must generate a rollback pointer (e.g., previous queue state, undo token, or version id).
- Rollback must be operator-accessible and testable.

## 11. Required Idempotency / Duplicate-Apply Protection
- Each save must be idempotent: same candidate, same idempotency key = no duplicate write.
- Must reject repeated or replayed requests unless explicitly allowed by operator.

## 12. Required Fail-Closed Behavior
- Any failure in approval, provenance, duplicate/conflict, or audit/rollback generation must block the write.
- Default to blocking unless all checks pass.

## 13. Required Telemetry Flags
- All save attempts (success/failure) must emit telemetry: action, operator, candidate, result, reason.
- Telemetry must not leak sensitive data.

## 14. Required Tests Before Implementation
- Test: Save only occurs with all required approvals and provenance.
- Test: Duplicate/conflict candidates are blocked.
- Test: Audit and rollback records are generated for every write.
- Test: Idempotency is enforced.
- Test: Fail-closed on any missing/invalid input.
- Test: No write occurs without explicit operator approval.

## 15. Route Design for Future Implementation
- New explicit POST route: `/api/local-ai/gate1/save-fights/approved`
- Route requires: valid Gate 1 token, operator_approved=true, dry_run.eligible_for_future_approval=true, all candidate and provenance fields present.
- Route must not allow auto-save or background write.

## 16. Storage/Write Boundary
- Write target (queue/database) must be explicitly declared and testable.
- No implicit or background writes.
- All writes must be atomic and auditable.

## 17. Rollback Design
- Rollback pointer generated for every write.
- Operator can trigger rollback via explicit action (future slice).
- Rollback must restore previous queue/database state.

## 18. Operator Workflow
- Operator reviews dry-run preview evidence.
- Operator explicitly approves save (UI/route, future slice).
- Save only occurs if all checks pass and operator_approved=true.
- Operator can view audit and trigger rollback if needed.

## 19. Safety Risks
- Accidental or unauthorized writes (mitigated by approval/token checks).
- Duplicate/conflict entries (mitigated by idempotency and conflict checks).
- Loss of provenance or audit trail (mitigated by required fields and audit/rollback records).
- Rollback failure (mitigated by atomic write and test coverage).

## 20. Final Verdict
- This design defines the full boundary and requirements for the first real Gate 1 approved save writer.
- **No code, route, or write behavior is implemented in this slice.**
- All safety, approval, provenance, and audit/rollback requirements are locked for future implementation.
- Next slice may safely implement a controlled, test-first Gate 1 approved save writer scaffold.

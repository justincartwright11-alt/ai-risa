# Button 1 Provider Enablement and Operator Approval Token Design Plan v1

## 1. Purpose
Design the future safe path for Button 1 provider enablement and operator approval token handling, without enabling providers, using tokens, running provider execution, making network/source calls, or writing queue/database/customer-PDF/learning/calibration outputs.

## 2. Source Identity
- Worktree path: C:\Users\jusin\OneDrive\Documents\Custom Office Templates
- Branch: master
- Checkpoint: ffead09
- Tag: button1-provider-enablement-and-operator-approval-token-readiness-review-v1
- Dirty state: acknowledged as pre-existing and unrelated; allowed for this docs-only slice under staged-set restriction.

## 3. Reviewed Input
- docs/button1_provider_enablement_and_operator_approval_token_readiness_review_v1.md

## 4. Current Locked Runtime State
- Registry candidate count: 2
- Provider IDs visible:
  - ufc_official_events
  - one_fc_official_events
- Enabled candidate count: 0
- Live feed status: unavailable
- Diagnostics:
  - provider_disabled
  - no_enabled_provider
- Execution gate decision: deny
- Reason codes:
  - execution_gate_operator_approval_missing
  - execution_gate_provider_not_enabled
- Provider execution: false
- Network calls: false
- Source calls: false
- Queue writes: false
- Database writes: false
- Button 2 promotion: false
- Save allowed: false

## 5. Design Conclusion
- Design planning may proceed only.
- No provider enablement is approved.
- No operator token creation/use is approved.
- No provider execution is approved.
- No network/source calls are approved.
- No queue/database/customer-PDF/learning/calibration writes are approved.
- No Button 2 promotion is approved.
- No auto-save is approved.

## 6. Provider Enablement Design
- First provider candidate under future review: ufc_official_events.
- Provider enablement must require a separate implementation readiness gate.
- Provider enabled state must not automatically trigger provider execution.
- Provider enabled state must not bypass operator approval.
- Provider enabled state must not bypass provenance requirements.
- Provider enabled state must not save rows.
- Provider enabled state must not promote rows to Button 2.
- Provider enabled state must not generate PDFs.
- Provider enabled state must not write database/queue/learning/calibration.
- Disabled provider state must remain deny/fail-closed.
- Unknown provider ID must fail closed.
- Stale or unavailable provider output must fail closed.

## 7. Operator Approval Token Design
- Token must be explicit.
- Token must not be hardcoded in source code.
- Token must be runtime/operator supplied only if separately approved.
- Token must be scoped to Button 1 provider preview gate only.
- Token must not bypass provider enabled check.
- Token must not bypass provenance check.
- Token must not cause writes.
- Token must not trigger Button 2 promotion.
- Token must not trigger customer report generation.
- Missing token must fail closed.
- Invalid token must fail closed.
- Valid token must be audit-visible.
- Audit record must include token-present state, not token secret value.

## 8. Execution Gate Design
- Decision remains deny-by-default.
- provider_enabled must be true before any allow state can be considered.
- Operator approval token must be valid before any allow state can be considered.
- Provenance/source-backed requirements must remain required.
- Execution permission must remain separate from save permission.
- Provider execution permission must remain separate from queue-save permission.
- Button 2 promotion permission must remain separate and blocked.
- No-write flags must be emitted in every gate response.

## 9. Source-Call and Network-Call Boundary
- No external source call in this design slice.
- Future source-call authorization requires separate execution-gate design review.
- First implementation may only model readiness, not execute calls.
- Any future live source call must identify provider ID, source URL/domain, timestamp, result count, and provenance status.
- Source call failure must fail closed.
- Stale source output must fail closed.
- Parser failure must be reported separately from provider-disabled and token-missing states.

## 10. UI and Operator Action Boundary
- No UI changes approved in this design.
- No button click behavior change approved.
- Dashboard may display readiness only if later approved.
- Dashboard must not expose token secret values.
- Dashboard must not enable save/generate/promote actions from token presence alone.
- All operator actions must remain explicit and gated.

## 11. Required Future File-Scope Review
- Registry JSON change, if any, requires separate gate.
- Loader change, if any, requires separate gate.
- Execution gate module change, if any, requires separate gate.
- app.py change blocked unless later proven unavoidable.
- Template change blocked unless later proven unavoidable.
- Provider adapter activation blocked unless separately authorized.
- Queue/database/Button 2/PDF/learning/calibration paths blocked.

## 12. Required Future Tests
- Disabled provider remains denied.
- Unknown provider fails closed.
- Enabled provider without token remains denied.
- Token present but provider disabled remains denied.
- Invalid token fails closed.
- Valid token does not cause writes.
- Valid token does not bypass provenance.
- Valid token does not trigger provider execution unless separately authorized.
- Valid token does not trigger Button 2 promotion.
- Valid token does not trigger auto-save.
- Stale source output fails closed.
- Parser failure is reported separately.
- Audit record includes provider ID, token-present state, decision, reason codes, and no-write flags.
- Queue/database/customer-PDF/learning/calibration write flags remain false.

## 13. Required Future Readiness Gates
- Provider enablement file-scope gate.
- Operator token contract review.
- Execution gate review.
- Source-call/network boundary review.
- No-write invariant review.
- Implementation readiness gate.
- Runtime validation gate after implementation.

## 14. Explicit Blocked Scope
- No implementation in this slice.
- No provider enablement.
- No operator token creation/use.
- No provider execution.
- No network/source calls.
- No scraping.
- No app.py change.
- No template change.
- No registry JSON change.
- No queue/database writes.
- No Button 2 promotion.
- No customer PDF/report generation.
- No learning/calibration writes.
- No worktree cleanup.
- No staging of pre-existing dirty files.

## 15. Final Design-Plan Verdict
BUTTON1_PROVIDER_ENABLEMENT_AND_OPERATOR_APPROVAL_TOKEN_DESIGN_PLAN_READY_FOR_REVIEW_ONLY

## 16. Safe Next Action
Docs-only provider enablement and operator approval token design review and file-scope gate.

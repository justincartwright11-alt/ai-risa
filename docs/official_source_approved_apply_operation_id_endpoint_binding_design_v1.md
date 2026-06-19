# Official Source Approved Apply Operation ID Endpoint Binding Design v1

**Slice:** official-source-approved-apply-operation-id-endpoint-binding-design-v1  
**Date:** 2026-06-18  
**Status:** Docs-only design, no implementation  
**Verdict:** APPROVED_AS_DOCS_ONLY_DESIGN

---

## Design Scope

This design defines a future **additive, deterministic, test-gated** approach to surface an optional top-level `operation_id` parameter in the official-source-approved apply request/response contract, without modifying any endpoint behavior, mutation semantics, token validation, or authorization logic.

**Hard boundaries:**
- Docs-only design slice
- No code changes
- No endpoint behavior changes
- No mutation execution changes
- No token digest/consume semantic changes
- No UI/scoring/batch/dashboard/ledger/prediction/intake changes
- No learning/calibration writes
- No queue/database writes
- No apply execution

---

## Current Governance Baseline

### Locked Authorization Chain

The Button 3 apply authorization is defined by the following locked docs-only slices:

1. **button3-results-accuracy-boundary-diagnosis-only-v1** — confirms boundary as diagnosis-only
2. **button3-official-result-governance-design-v1** — defines official-source trust and conflict handling
3. **button3-apply-path-boundary-design-v1** — specifies apply-path as fail-closed, diagnosis-optional, execution-blocked
4. **button3-apply-authorization-contract-design-details-v1** — details operator approval gate contract
5. **button3-apply-authorization-test-gating-matrix-index-v1** — pre-implementation test matrix (G1-G7)

### Current Apply Request Contract

**Endpoint:** `POST /api/button3/apply/official-result` (future, not implemented)

**Current request shape (no operation_id):**
```json
{
  "result_comparison_id": "uuid",
  "operator_approval_token": "token_string",
  "conflict_resolution": "strategy_enum",
  "dry_run": false
}
```

**Current response shape:**
```json
{
  "apply_status": "not_executed",
  "authorization_passed": false,
  "apply_executed": false,
  "mutation_performed": false,
  "learning_write_performed": false,
  "calibration_write_performed": false,
  "queue_write_performed": false,
  "audit_id": "uuid",
  "error_message": "string or null"
}
```

---

## Proposed Future Request Contract (Additive Only)

### Request Shape

**New optional top-level field (additive):**

```json
{
  "operation_id": "uuid or string (optional, client-provided)",
  "result_comparison_id": "uuid",
  "operator_approval_token": "token_string",
  "conflict_resolution": "strategy_enum",
  "dry_run": false
}
```

**Field details:**
- `operation_id` (NEW, OPTIONAL)
  - **Type:** UUID or opaque string
  - **Source:** Client-provided
  - **Purpose:** Operational tracing and idempotency hints (future use; not used in authorization decision in this design)
  - **Default:** if omitted, server may generate one internally for audit purposes
  - **Required migration:** NONE — clients without operation_id continue to work unchanged
  - **Determinism:** Server handling is deterministic regardless of whether operation_id is provided
  - **No authorization dependency:** Authorization decision and token validation are independent of operation_id value

**Additive principle:**
- All existing required fields remain unchanged
- No existing fields are reinterpreted
- No existing fields are made optional
- operation_id does NOT change the contract semantics

---

## Proposed Future Response Surfacing (Additive Only)

### Response Shape

**New optional field in response (additive):**

```json
{
  "apply_status": "not_executed",
  "authorization_passed": false,
  "apply_executed": false,
  "mutation_performed": false,
  "learning_write_performed": false,
  "calibration_write_performed": false,
  "queue_write_performed": false,
  "audit_id": "uuid",
  "operation_id": "uuid or string (echoed from request, or server-generated if omitted)",
  "error_message": "string or null"
}
```

**Field details:**
- `operation_id` (NEW, OPTIONAL in response)
  - **Value:** Either the client-provided operation_id from the request, OR a server-generated UUID if the request omitted it
  - **Purpose:** Allow operators and audit systems to correlate apply requests with responses and downstream audit logs
  - **No semantic dependency:** Presence or value of operation_id does NOT affect authorization, apply execution, or mutation logic
  - **Auditable:** Must be logged in apply audit trail for future correlation

**Backward compatibility:**
- Existing clients that ignore operation_id continue to work unchanged
- New clients may use operation_id for correlation without breaking old code paths

---

## Explicit Token Digest Invariants

### Token Digest Computation

**INVARIANT 1: No change to token digest algorithm**
- Token digest computation remains unchanged in this design
- All fields currently included in digest remain included
- operation_id is NOT included in token digest (unless a separate, future design explicitly approves this)

**INVARIANT 2: operation_id does not weaken token validation**
- Token validation logic remains unchanged
- operation_id is parsed AFTER token validation, not used in validation
- A request with an invalid operation_id but valid token still passes token validation

**INVARIANT 3: Token digest semantic invariance**
- Two requests with identical payloads except for operation_id must produce identical token digests
- Token validation must not depend on operation_id value or presence
- No token re-derivation or regeneration based on operation_id

### Future Reconsideration

Any future design that wishes to include `operation_id` in the token digest MUST:
1. Be approved as a separate, distinct design slice
2. Include comprehensive regression tests for all existing token validation paths
3. Preserve backward compatibility through a version field or feature-flag
4. Not be bundled with this additive design

---

## Explicit Token Consume Invariants

### Token Consume Timing

**INVARIANT 4: No change to consume timing**
- Token consume timing remains unchanged
- operation_id does not trigger early consume or deferred consume
- Consume semantics are identical with or without operation_id in request

### Token Consume Success/Failure Semantics

**INVARIANT 5: No change to consume success/failure logic**
- Token success/failure determination is independent of operation_id
- operation_id validation errors do NOT cause token consume failure
- Token consume succeeds or fails based only on token validity and authorization decision, not operation_id

### No Retry Loophole

**INVARIANT 6: operation_id does not create retry loophole**
- Presence or change of operation_id does NOT allow bypass of consume-once-per-token semantics
- If a client submits the same token with different operation_ids, consume logic prevents replay
- operation_id is NOT a retry key; token is the only retry boundary

---

## Endpoint/Mutation Invariants

### No Behavior Change in This Design Slice

**INVARIANT 7: Apply endpoint remains non-activated**
- This design does not implement or activate the apply endpoint
- No actual apply execution occurs
- All apply-execution behaviors remain blocked until a separate implementation slice is approved

**INVARIANT 8: No apply execution**
- apply_executed remains false
- mutation_performed remains false
- No database writes
- No queue mutations
- No learning writes
- No calibration writes
- No provider execution

**INVARIANT 9: Endpoint semantics unchanged**
- Request parsing for operation_id is independent of endpoint behavior
- Response surfacing of operation_id does not change authorization decision
- Operation_id surfacing is audit/tracing only

---

## Future Implementation Requirements

Any future implementation slice that activates endpoint-binding for operation_id must include:

### Additive Request Parsing Test
- Test: Request with operation_id parses correctly
- Test: Request without operation_id parses correctly
- Test: operation_id parsing does not interfere with existing required fields
- Test: Malformed operation_id is rejected or normalized deterministically

### Additive Response Surfacing Test
- Test: Response includes operation_id when provided in request
- Test: Response includes server-generated operation_id when omitted from request
- Test: operation_id value is unchanged (not modified/normalized in response)
- Test: Existing response fields unchanged

### Token Digest Regression Test
- Test: Token digest is identical with or without operation_id in request
- Test: Token validation success/failure is independent of operation_id
- Test: Two requests differing only in operation_id produce identical token digests

### Token Consume Regression Test
- Test: Token consume behavior unchanged with operation_id present
- Test: Token consume behavior unchanged with operation_id absent
- Test: Token consume once-per-token semantics enforced regardless of operation_id
- Test: No operation_id-based retry loophole

### Missing Operation_ID Compatibility Test
- Test: Requests without operation_id continue to work
- Test: Legacy clients not sending operation_id are unaffected
- Test: Server generates valid operation_id for audit when request omits it

### Malformed Operation_ID Handling Test
- Test: Non-UUID operation_id values are accepted or deterministically normalized
- Test: Invalid UTF-8 or oversized operation_id is rejected with clear error
- Test: No security bypass through operation_id injection or encoding attack
- Test: Error messages do not expose internal state

### No Mutation Behavior Change Test
- Test: apply_executed remains false
- Test: mutation_performed remains false
- Test: No database writes occur
- Test: No queue mutations occur
- Test: No learning/calibration writes occur
- Test: No side effects beyond audit logging

### Audit/Provenance Test
- Test: operation_id is included in apply audit record
- Test: operation_id is correlated with audit_id in logs
- Test: Audit trail supports future replay/investigation using operation_id

---

## Risk Register

### Risk 1: Operation_ID Becomes Authorization Vector
**Severity:** HIGH  
**Mitigation:** This design explicitly separates operation_id (tracing) from authorization (token-based). Future implementations MUST NOT use operation_id for authorization decisions. Test-gating matrix G3 validates this separation.

### Risk 2: Token Digest Inclusion Loophole
**Severity:** HIGH  
**Mitigation:** This design explicitly forbids operation_id inclusion in token digest. Any future design proposing this MUST be approved separately with full token validation regression testing.

### Risk 3: Retry Loophole via Operation_ID Variation
**Severity:** MEDIUM  
**Mitigation:** Token consume-once semantics is based on token, not operation_id. Changing operation_id does not bypass consume logic. Test (token consume regression) validates this.

### Risk 4: UI Binding Creep
**Severity:** MEDIUM  
**Mitigation:** This design is endpoint-only. No UI changes are approved in this slice. Any dashboard display of operation_id requires separate design and approval.

### Risk 5: Learning Path Unblocking
**Severity:** HIGH  
**Mitigation:** This design is additive to endpoint-binding only. Learning execution remains blocked. Learning writes require separate governance approval chain (not this design). All locked Button 3 invariants preserved.

---

## Explicit Non-Goals

This design does NOT:

- Implement the apply endpoint
- Activate any apply execution
- Enable learning/calibration writes
- Enable database mutations
- Enable queue writes
- Change token validation logic
- Change token digest computation
- Change UI or dashboard behavior
- Change scoring, batch, ledger, prediction, or intake behavior
- Create any durable writes
- Change provider execution strategy
- Add retry semantics
- Add operation_id-based authorization

---

## Design Verdict

**STATUS: APPROVED_AS_DOCS_ONLY_DESIGN**

**Conditions:**
1. This design slice remains docs-only (no code implementation in this slice)
2. Any future implementation slice MUST remain additive, deterministic, and test-gated
3. All token digest, token consume, authorization, and mutation invariants (1-9) MUST be preserved
4. All locked Button 3 governance rules remain in force
5. All implementation requirements (8 test categories) MUST pass before activation
6. Cross-track isolation with Button 1 and Button 2 MUST be preserved

**Approved for:**
- Design review in companion review-artifact slice
- Future implementation planning (subject to design review pass)
- Pre-implementation test-gating matrix alignment

**Blocked until:**
- Design review artifact validates all coverage items
- Implementation slice passes full test-gating matrix (G1-G7)
- All risks in risk register are addressed or mitigated

---

## Locked Governance References

This design slice preserves and references:

1. **Button 3 Results/Accuracy Boundary Diagnosis** — `button3-results-accuracy-boundary-diagnosis-only-v1`
2. **Official Result Governance** — `button3-official-result-governance-design-v1`
3. **Apply Path Boundary** — `button3-apply-path-boundary-design-v1`
4. **Apply Authorization Contract** — `button3-apply-authorization-contract-design-details-v1`
5. **Apply Authorization Test-Gating Matrix** — `button3-apply-authorization-test-gating-matrix-index-v1`
6. **Button 2 Stop State and Cross-Track Index** — `ai-risa-three-button-factory-button2-stop-state-and-next-track-governance-index-v1`

All locked rules from these slices remain in force.

---

## Next Slice

**Name:** official-source-approved-apply-operation-id-endpoint-binding-design-review-v1

**Purpose:** Review this design artifact against governance requirements, coverage checklist, and readiness for future implementation planning.

**Hard Constraints:** Docs-only review, no code changes, no behavior changes.

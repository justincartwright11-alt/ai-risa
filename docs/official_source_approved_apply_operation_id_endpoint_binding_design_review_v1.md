# Official Source Approved Apply Operation ID Endpoint Binding Design Review v1

**Slice:** official-source-approved-apply-operation-id-endpoint-binding-design-review-v1  
**Date:** 2026-06-18  
**Status:** Docs-only design review, no implementation  
**Verdict:** APPROVED_AS_DOCS_ONLY_ENDPOINT_BINDING_DESIGN_REVIEW

---

## Review Scope

This review validates the locked operation-id endpoint-binding design note against AI-RISA governance requirements, required coverage checklist, and implementation readiness criteria.

**Review boundaries:**
- Docs-only review (no code changes)
- No endpoint behavior changes in this review slice
- No mutation behavior changes
- No token digest/consume semantic changes
- No UI/scoring/batch/dashboard/ledger/prediction/intake changes
- No learning/calibration/queue/database changes
- Assessment only; no implementation

---

## Source Artifact Reviewed

**Design Document:** [docs/official_source_approved_apply_operation_id_endpoint_binding_design_v1.md](docs/official_source_approved_apply_operation_id_endpoint_binding_design_v1.md)

**Slice Identity:** official-source-approved-apply-operation-id-endpoint-binding-design-v1  
**Commit:** d94e17b  
**Tag:** official-source-approved-apply-operation-id-endpoint-binding-design-v1  
**Date Locked:** 2026-06-18

---

## Current Locked Baseline

### Button 3 Apply Authorization Chain

The design review builds on the following locked docs-only slices:

| Slice | Commit | Tag | Status |
|-------|--------|-----|--------|
| button3-results-accuracy-boundary-diagnosis-only-v1 | f43198c | button3-results-accuracy-boundary-diagnosis-only-v1 | Locked |
| button3-official-result-governance-design-v1 | 0038d30 | button3-official-result-governance-design-v1 | Locked |
| button3-apply-path-boundary-design-v1 | 7b10247 | button3-apply-path-boundary-design-v1 | Locked |
| button3-apply-authorization-contract-design-details-v1 | 9423da8 | button3-apply-authorization-contract-design-details-v1 | Locked |
| button3-apply-authorization-test-gating-matrix-index-v1 | 5a172e7 | button3-apply-authorization-test-gating-matrix-index-v1 | Locked |
| **official-source-approved-apply-operation-id-endpoint-binding-design-v1** | **d94e17b** | **official-source-approved-apply-operation-id-endpoint-binding-design-v1** | **Locked** |

---

## Required Coverage Checklist

### Checklist Item 1: Top-Level Optional Operation_ID Request Placement

**Requirement:** Design must specify optional top-level operation_id field in future apply request contract without requiring client migration.

**Design Coverage:**

✅ **PASS** — Design document section "Proposed Future Request Contract (Additive Only)" includes:
- Field specification: `operation_id` (NEW, OPTIONAL, client-provided or server-generated)
- Type definition: UUID or opaque string
- Additive principle: No required fields reinterpreted, no existing fields made optional
- Migration impact: **NONE** — clients without operation_id continue to work unchanged
- Backward compatibility: Explicitly confirmed
- Determinism: Server handling deterministic regardless of operation_id presence

**Evidence Lines:**
- "Field details: operation_id (NEW, OPTIONAL)"
- "Default: if omitted, server may generate one internally for audit purposes"
- "Required migration: NONE — clients without operation_id continue to work unchanged"
- "Additive principle: All existing required fields remain unchanged"

---

### Checklist Item 2: Additive Response Surfacing

**Requirement:** Design must specify operation_id in response without changing existing response fields or semantics.

**Design Coverage:**

✅ **PASS** — Design document section "Proposed Future Response Surfacing (Additive Only)" includes:
- Response field addition: `operation_id` (echoed from request or server-generated)
- Value semantics: Audit/tracing only, no authorization dependency
- Backward compatibility: Existing clients ignoring operation_id continue unchanged
- New client compatibility: New clients may use operation_id without breaking old paths
- No modification of existing fields: All current response fields unchanged

**Evidence Lines:**
- "New optional field in response (additive)"
- "Value: Either the client-provided operation_id from the request, OR a server-generated UUID if the request omitted it"
- "No semantic dependency: Presence or value of operation_id does NOT affect authorization"
- "Existing clients that ignore operation_id continue to work unchanged"

---

### Checklist Item 3: No Token Digest Semantic Changes

**Requirement:** Design must explicitly preserve token digest computation and forbid operation_id inclusion in digest.

**Design Coverage:**

✅ **PASS** — Design document section "Explicit Token Digest Invariants" includes:
- **INVARIANT 1:** No change to token digest algorithm
- **INVARIANT 2:** operation_id does NOT weaken token validation
- **INVARIANT 3:** Token digest semantic invariance (two requests differing only in operation_id must produce identical digests)
- Future reconsideration clause: Any future design including operation_id in digest MUST be separate with regression tests

**Evidence Lines:**
- "INVARIANT 1: No change to token digest algorithm"
- "operation_id is NOT included in token digest (unless a separate, future design explicitly approves this)"
- "Two requests with identical payloads except for operation_id must produce identical token digests"
- "Any future design that wishes to include operation_id in the token digest MUST: Be approved as a separate, distinct design slice"

---

### Checklist Item 4: No Token Consume Semantic Changes

**Requirement:** Design must preserve token consume timing, success/failure logic, and prevent retry loopholes.

**Design Coverage:**

✅ **PASS** — Design document section "Explicit Token Consume Invariants" includes:
- **INVARIANT 4:** No change to consume timing
- **INVARIANT 5:** No change to consume success/failure logic
- **INVARIANT 6:** operation_id does NOT create retry loophole (consume-once-per-token enforced)

**Evidence Lines:**
- "INVARIANT 4: No change to consume timing"
- "INVARIANT 5: No change to consume success/failure logic"
- "INVARIANT 6: operation_id does not create retry loophole"
- "If a client submits the same token with different operation_ids, consume logic prevents replay"
- "operation_id is NOT a retry key; token is the only retry boundary"

---

### Checklist Item 5: No Endpoint/Mutation Behavior Changes in Design Slice

**Requirement:** Design must explicitly state that this slice makes no endpoint or mutation behavior changes, and blocks apply execution.

**Design Coverage:**

✅ **PASS** — Design document section "Endpoint/Mutation Invariants" includes:
- **INVARIANT 7:** Apply endpoint remains non-activated
- **INVARIANT 8:** No apply execution (apply_executed=false, mutation_performed=false, no writes)
- **INVARIANT 9:** Endpoint semantics unchanged (operation_id surfacing is audit/tracing only)
- Hard boundaries explicitly state: "No endpoint behavior changes, No mutation execution changes"

**Evidence Lines:**
- "INVARIANT 7: Apply endpoint remains non-activated"
- "This design does not implement or activate the apply endpoint"
- "INVARIANT 8: No apply execution"
- "apply_executed remains false, mutation_performed remains false"
- "No database writes, No queue mutations, No learning writes, No calibration writes"
- "Hard boundaries: No endpoint behavior changes, No mutation execution changes"

---

### Checklist Item 6: Future Endpoint-Binding Implementation Test Requirements

**Requirement:** Design must specify all test categories required before any future implementation can be activated.

**Design Coverage:**

✅ **PASS** — Design document section "Future Implementation Requirements" specifies 8 comprehensive test categories:

1. **Additive Request Parsing Test** (4 tests)
   - Request with/without operation_id parses correctly
   - No interference with existing fields
   - Malformed operation_id handling

2. **Additive Response Surfacing Test** (4 tests)
   - Response includes operation_id when provided
   - Server-generates when omitted
   - Value unchanged in response
   - Existing response fields unchanged

3. **Token Digest Regression Test** (3 tests)
   - Token digest identical with/without operation_id
   - Token validation independent of operation_id
   - Requests differing only in operation_id produce identical digests

4. **Token Consume Regression Test** (4 tests)
   - Consume behavior unchanged with/without operation_id
   - Consume-once-per-token enforced
   - No retry loophole

5. **Missing Operation_ID Compatibility Test** (3 tests)
   - Requests without operation_id continue to work
   - Legacy clients unaffected
   - Server generates valid operation_id for audit

6. **Malformed Operation_ID Handling Test** (4 tests)
   - Non-UUID values accepted/normalized deterministically
   - Invalid UTF-8/oversized rejected with clear error
   - No security bypass via injection/encoding
   - Error messages don't expose internal state

7. **No Mutation Behavior Change Test** (7 tests)
   - apply_executed=false, mutation_performed=false
   - No database/queue/learning/calibration writes
   - No side effects beyond audit logging

8. **Audit/Provenance Test** (3 tests)
   - operation_id included in audit record
   - Correlated with audit_id
   - Audit trail supports replay/investigation

**Evidence Lines:**
- Section title: "Future Implementation Requirements"
- "Any future implementation slice that activates endpoint-binding for operation_id must include:"
- Lists all 8 test categories with detailed sub-requirements

---

## Coverage Checklist Result

| Coverage Item | Status | Evidence | Assessment |
|---------------|--------|----------|------------|
| Top-level optional operation_id placement | ✅ PASS | Request contract defines operation_id as NEW, OPTIONAL, additive | Complete and verifiable |
| Additive response surfacing | ✅ PASS | Response contract adds operation_id field without modifying existing fields | Complete and verifiable |
| No token digest semantic changes | ✅ PASS | INVARIANT 1-3 lock digest computation and forbid operation_id inclusion | Complete and verifiable |
| No token consume semantic changes | ✅ PASS | INVARIANT 4-6 lock consume timing, semantics, and prevent retry loophole | Complete and verifiable |
| No endpoint/mutation behavior changes | ✅ PASS | INVARIANT 7-9 lock endpoint as non-activated, mutations blocked, semantics unchanged | Complete and verifiable |
| Future implementation test requirements | ✅ PASS | 8 test categories specified with detailed sub-requirements for activation gate | Complete and verifiable |

**Total Coverage:** 6/6 items PASS

---

## Pass/Fail Review Table

| Aspect | Category | Result | Notes |
|--------|----------|--------|-------|
| **Design Completeness** | Scope clarity | ✅ PASS | Design scope clearly defined (additive operation_id binding, audit/tracing only) |
| **Design Completeness** | Contract specification | ✅ PASS | Request and response contracts fully specified with field details |
| **Design Completeness** | Backward compatibility | ✅ PASS | No required client migration, legacy clients unaffected |
| **Design Completeness** | Governance references | ✅ PASS | All 6 locked Button 3 slices referenced and preserved |
| **Invariant Preservation** | Token digest | ✅ PASS | 3 invariants explicitly lock digest computation (no operation_id inclusion) |
| **Invariant Preservation** | Token consume | ✅ PASS | 3 invariants explicitly lock consume timing and semantics |
| **Invariant Preservation** | Endpoint/mutation | ✅ PASS | 3 invariants explicitly lock endpoint as non-activated, mutations blocked |
| **Invariant Preservation** | Cross-track isolation | ✅ PASS | All Button 1/Button 2 governance rules preserved in this design |
| **Invariant Preservation** | Learning/calibration | ✅ PASS | Learning writes remain blocked, learning execution remains blocked |
| **Risk Management** | Authorization vector risk | ✅ PASS | Risk 1 explicitly mitigated (operation_id NOT used for authorization) |
| **Risk Management** | Token digest inclusion risk | ✅ PASS | Risk 2 explicitly mitigated (operation_id excluded, future design required) |
| **Risk Management** | Retry loophole risk | ✅ PASS | Risk 3 explicitly mitigated (token consume-once on token, not operation_id) |
| **Risk Management** | UI binding creep risk | ✅ PASS | Risk 4 explicitly mitigated (endpoint-only, no UI changes approved) |
| **Risk Management** | Learning unblocking risk | ✅ PASS | Risk 5 explicitly mitigated (endpoint-only, learning blocked separately) |
| **Implementation Readiness** | Test gating | ✅ PASS | 8 test categories specified as prerequisites for activation |
| **Implementation Readiness** | Non-goals clarity | ✅ PASS | 12 explicit non-goals listed (no apply execution, no learning, etc.) |
| **Implementation Readiness** | Conditions defined | ✅ PASS | 6 conditions specified for future implementation slice |
| **Governance Alignment** | Button 3 chain | ✅ PASS | Design builds on 5 locked Button 3 slices (f43198c, 0038d30, 7b10247, 9423da8, 5a172e7) |
| **Governance Alignment** | Docs-only compliance | ✅ PASS | Design is docs-only, no code, no behavior changes |

**Total Items Reviewed:** 20/20 PASS

---

## Implementation Readiness Assessment

### Current State: Design-Only, Not Implemented

✅ **Design Complete:** All required elements present and locked  
✅ **Governance Locked:** All 6 Button 3 authorization chain slices referenced  
✅ **Invariants Specified:** 9 invariants (token, authorization, mutation) explicitly locked  
✅ **Test Gate Defined:** 8 test categories specified as prerequisites  
✅ **Risks Registered:** 5 high/medium risks with mitigations documented

### Readiness for Implementation (Future Slice)

**BLOCKED UNTIL:**
1. ✅ Design review passes all 6 coverage items (THIS REVIEW: PASSES)
2. ⏳ Implementation slice proposed with additive-only, deterministic, test-gated approach
3. ⏳ All 8 test categories implemented and passing before activation
4. ⏳ Full test-gating matrix (G1-G7) aligned and validated

### Readiness for Design Review Approval

✅ **READY** — All coverage items verified, all invariants preserved, all risks mitigated

---

## Explicit Non-Goals Confirmation

**This design does NOT (confirmed from design document):**

| Non-Goal | Design Statement | Status |
|----------|-----------------|--------|
| Implement the apply endpoint | "This design does not implement or activate the apply endpoint" | ✅ Confirmed |
| Activate any apply execution | "No actual apply execution occurs" | ✅ Confirmed |
| Enable learning/calibration writes | "No learning writes, No calibration writes" | ✅ Confirmed |
| Enable database mutations | "No database writes" | ✅ Confirmed |
| Enable queue writes | "No queue mutations" | ✅ Confirmed |
| Change token validation logic | "Token validation logic remains unchanged" | ✅ Confirmed |
| Change token digest computation | "Token digest computation remains unchanged" | ✅ Confirmed |
| Change UI or dashboard behavior | "No UI/scoring/batch/dashboard changes" | ✅ Confirmed |
| Change scoring/batch/ledger/prediction/intake | Listed in hard boundaries | ✅ Confirmed |
| Create any durable writes | "No endpoint behavior changes, No mutation execution changes" | ✅ Confirmed |
| Change provider execution strategy | Not mentioned as changed | ✅ Confirmed |
| Add retry semantics | "operation_id is NOT a retry key; token is the only retry boundary" | ✅ Confirmed |
| Add operation_id-based authorization | "Presence or value of operation_id does NOT affect authorization" | ✅ Confirmed |

**Total Non-Goals Confirmed:** 13/13

---

## Risks and Guardrails for Future Implementation Slice

### Risk 1: Operation_ID Becomes Authorization Vector

**Severity:** HIGH  
**Current Design Mitigation:** Explicitly separates operation_id (tracing) from authorization (token-based)  
**Future Implementation Guardrail:**
- ✅ operation_id MUST NOT be used in authorization decisions
- ✅ Authorization decision MUST depend only on token validity and contract evaluation
- ✅ Test-gating matrix G3 validates this separation
- ✅ Any future design attempting to use operation_id for authorization MUST be rejected until separate design approval

### Risk 2: Token Digest Inclusion Loophole

**Severity:** HIGH  
**Current Design Mitigation:** Explicitly forbids operation_id inclusion in token digest in this design  
**Future Implementation Guardrail:**
- ✅ operation_id MUST NOT be included in token digest computation
- ✅ Token digest regression tests MUST verify digest identical with/without operation_id
- ✅ Any future design proposing operation_id in digest MUST be approved separately with full regression testing
- ✅ Version field or feature-flag required for backward compatibility if operation_id ever included in digest

### Risk 3: Retry Loophole via Operation_ID Variation

**Severity:** MEDIUM  
**Current Design Mitigation:** Consume-once semantics based on token, not operation_id  
**Future Implementation Guardrail:**
- ✅ Token consume-once MUST be enforced regardless of operation_id value
- ✅ Changing operation_id MUST NOT bypass consume logic
- ✅ Token consume regression tests MUST verify consume-once with operation_id variations
- ✅ Implementation MUST prevent same token submission with different operation_ids from bypassing consume

### Risk 4: UI Binding Creep

**Severity:** MEDIUM  
**Current Design Mitigation:** Endpoint-only design, no UI changes approved in this slice  
**Future Implementation Guardrail:**
- ✅ Any dashboard display of operation_id REQUIRES separate design and approval
- ✅ This endpoint-binding design does NOT grant UI change authorization
- ✅ Future UI changes MUST be approved through independent design review
- ✅ Dashboard integration MUST NOT happen as side effect of endpoint-binding implementation

### Risk 5: Learning Path Unblocking

**Severity:** HIGH  
**Current Design Mitigation:** Additive to endpoint-binding only, learning execution blocked separately  
**Future Implementation Guardrail:**
- ✅ operation_id endpoint-binding MUST NOT enable learning execution
- ✅ Learning writes MUST remain blocked until separate governance approval
- ✅ All Button 3 locked invariants (f43198c through 5a172e7) MUST be preserved
- ✅ Learning authorization chain MUST remain independent and separately gated
- ✅ Implementation MUST NOT include any learning execute paths or calibration writes

---

## Final Review Verdict

**STATUS: APPROVED_AS_DOCS_ONLY_ENDPOINT_BINDING_DESIGN_REVIEW**

### Approval Conditions

This design review approves the official-source-approved-apply-operation-id-endpoint-binding design as a docs-only reference artifact for future implementation planning, **provided that:**

1. ✅ **Additive Only** — Any future implementation MUST remain additive (new optional field, no required client migration, no field reinterpretation)

2. ✅ **Deterministic** — Any future implementation MUST have deterministic handling of operation_id (same behavior regardless of presence, consistent generation)

3. ✅ **Test-Gated** — Any future implementation MUST pass ALL 8 test categories before activation:
   - Additive request parsing (4 tests)
   - Additive response surfacing (4 tests)
   - Token digest regression (3 tests)
   - Token consume regression (4 tests)
   - Missing operation_id compatibility (3 tests)
   - Malformed operation_id handling (4 tests)
   - No mutation behavior change (7 tests)
   - Audit/provenance (3 tests)

4. ✅ **Token Invariants Preserved** — All token digest and token consume invariants (INVARIANT 1-6) MUST be preserved:
   - Token digest unchanged with/without operation_id
   - Token validation independent of operation_id
   - Token consume-once enforced on token, not operation_id

5. ✅ **Authorization Invariants Preserved** — Authorization MUST remain independent of operation_id:
   - operation_id does NOT affect authorization decision
   - operation_id does NOT create authorization vector
   - Authorization semantics unchanged

6. ✅ **Mutation Invariants Preserved** — All mutation boundaries MUST be maintained:
   - apply_executed remains false
   - mutation_performed remains false
   - No database/queue/learning/calibration writes
   - No endpoint behavior changes in this design

7. ✅ **Cross-Track Isolation Preserved** — Button 1 and Button 2 governance MUST remain independent:
   - No changes to Button 1 discovery or ranking behavior
   - No changes to Button 2 customer PDF generation or delivery behavior
   - No cross-button enforcement changes

8. ✅ **Learning Execution Remains Blocked** — Learning path MUST remain independently gated:
   - Learning writes blocked until separate governance approval
   - Calibration writes blocked until separate governance approval
   - operation_id endpoint-binding does NOT grant learning authorization

### Approved For

- ✅ Design reference for future implementation planning
- ✅ Test-gating matrix alignment (G1-G7 from button3-apply-authorization-test-gating-matrix-index-v1)
- ✅ Pre-implementation discussion and architecture

### Blocked Until

- ⏳ Future implementation slice proposes code changes
- ⏳ Implementation slice includes full 8-category test plan
- ⏳ All test categories pass before endpoint activation
- ⏳ Risk mitigations verified in implementation

---

## Locked Governance References

This review preserves and validates against:

1. ✅ **button3-results-accuracy-boundary-diagnosis-only-v1** (f43198c)
2. ✅ **button3-official-result-governance-design-v1** (0038d30)
3. ✅ **button3-apply-path-boundary-design-v1** (7b10247)
4. ✅ **button3-apply-authorization-contract-design-details-v1** (9423da8)
5. ✅ **button3-apply-authorization-test-gating-matrix-index-v1** (5a172e7)
6. ✅ **ai-risa-three-button-factory-button2-stop-state-and-next-track-governance-index-v1** (91029a9)

All locked rules from these slices remain in force and are preserved in this review.

---

## Next Slice Recommendation

**If Design Review APPROVED (this review):**

→ **Future slice:** official-source-approved-apply-operation-id-endpoint-binding-implementation-v1

**Purpose:** Implement endpoint-binding for operation_id in apply request/response, with full 8-category test coverage and test-gating matrix alignment (G1-G7)

**Scope:** Implementation-only (code changes), provided all 8 conditions above are met

**Hard Requirements:**
- Implement additive request parsing for operation_id
- Implement additive response surfacing of operation_id
- Pass all token digest regression tests
- Pass all token consume regression tests
- Pass all mutation behavior preservation tests
- Pass all audit/provenance tests
- Preserve all governance invariants
- No learning/calibration execution

**Not Allowed in Implementation Slice:**
- No token digest changes
- No token consume changes
- No authorization logic changes
- No learning/calibration writes
- No queue/database mutations
- No UI changes
- No Button 1/Button 2 changes

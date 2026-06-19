# Official Source Approved Apply Operation ID Endpoint Binding Implementation Plan v1

**Slice:** official-source-approved-apply-operation-id-endpoint-binding-implementation-plan-v1  
**Date:** 2026-06-18  
**Status:** Docs-only implementation plan, no code, no execution  
**Verdict:** READY_FOR_NARROW_IMPLEMENTATION_SLICE

---

## Implementation Planning Scope

This plan translates the locked design, design review, and readiness gate into a narrow, actionable code architecture plan for a future implementation slice of optional `operation_id` endpoint-binding in Button 3 apply authorization chain.

**Plan boundaries:**
- Docs-only planning (no code changes in this slice)
- No tests executed in this slice
- No endpoint behavior changes in this slice
- Code architecture and test structure planning only
- Clear module boundaries for future implementation
- All invariants preserved throughout planning

**Planning objective:** Define exact module touchpoints, test structure, and stop conditions so future implementation slice can be narrow, deterministic, and fully test-gated.

---

## Source Artifacts Reviewed

This plan builds on three locked source artifacts:

### Design Artifact (d94e17b)
- **File:** `docs/official_source_approved_apply_operation_id_endpoint_binding_design_v1.md`
- **Slice:** official-source-approved-apply-operation-id-endpoint-binding-design-v1
- **Verdict:** APPROVED_AS_DOCS_ONLY_DESIGN
- **Key Content Locked:**
  - Optional top-level operation_id field (UUID or opaque string)
  - Response surfacing of operation_id (echoed or server-generated)
  - 9 explicit invariants (token digest 1-3, token consume 4-6, mutation 7-9)
  - 8 test categories (32+ total tests)
  - 5 identified risks with mitigations
  - 12 explicit non-goals

### Design Review Artifact (cb119ed)
- **File:** `docs/official_source_approved_apply_operation_id_endpoint_binding_design_review_v1.md`
- **Slice:** official-source-approved-apply-operation-id-endpoint-binding-design-review-v1
- **Verdict:** APPROVED_AS_DOCS_ONLY_ENDPOINT_BINDING_DESIGN_REVIEW
- **Key Content Locked:**
  - 6/6 coverage items verified PASS
  - 20/20 pass/fail items verified PASS
  - 13/13 non-goals confirmed
  - 5 risks with guardrails
  - 8 implementation conditions specified

### Readiness Gate Artifact (edc7142)
- **File:** `docs/official_source_approved_apply_operation_id_endpoint_binding_implementation_readiness_gate_v1.md`
- **Slice:** official-source-approved-apply-operation-id-endpoint-binding-implementation-readiness-gate-v1
- **Verdict:** READY_FOR_NARROW_IMPLEMENTATION_PLANNING_ONLY
- **Key Content Locked:**
  - 10/10 readiness checklist items ready
  - 8 test categories with 32+ tests required
  - 9 blocked paths documented
  - 6 stop conditions defined
  - All governance rules preserved

---

## Current Locked Baseline

### Button 3 Apply Authorization Chain

This plan preserves all locked docs-only slices:

| Slice | Commit | Status |
|-------|--------|--------|
| button3-results-accuracy-boundary-diagnosis-only-v1 | f43198c | Locked |
| button3-official-result-governance-design-v1 | 0038d30 | Locked |
| button3-apply-path-boundary-design-v1 | 7b10247 | Locked |
| button3-apply-authorization-contract-design-details-v1 | 9423da8 | Locked |
| button3-apply-authorization-test-gating-matrix-index-v1 | 5a172e7 | Locked |
| official-source-approved-apply-operation-id-endpoint-binding-design-v1 | d94e17b | Locked |
| official-source-approved-apply-operation-id-endpoint-binding-design-review-v1 | cb119ed | Locked |
| official-source-approved-apply-operation-id-endpoint-binding-implementation-readiness-gate-v1 | edc7142 | Locked |

---

## Future Implementation Objective

The future implementation slice will add support for optional `operation_id` field in Button 3 apply authorization chain with the following scope:

### In-Scope

- ✅ Optional top-level `operation_id` request field (UUID or opaque string)
- ✅ Additive request parsing (no breaking changes)
- ✅ Additive response field `operation_id` (echoed or server-generated)
- ✅ Deterministic operation_id normalization or rejection (for malformed input)
- ✅ Audit/provenance integration (operation_id logged and correlated with audit_id)
- ✅ No authorization dependency (operation_id does NOT affect authz)
- ✅ No token digest dependency (operation_id NOT in digest)
- ✅ No token consume dependency (operation_id NOT affecting consume)
- ✅ No mutation expansion (apply_executed, mutation_performed remain false)

### Out-of-Scope (Explicitly Forbidden)

- ❌ Apply endpoint activation
- ❌ Apply execution
- ❌ Mutation execution
- ❌ Database writes
- ❌ Queue mutations
- ❌ Learning writes or execution
- ❌ Calibration writes
- ❌ Token digest computation changes
- ❌ Token consume timing or semantics changes
- ❌ Authorization logic changes
- ❌ UI/dashboard/template changes
- ❌ Button 1 or Button 2 runtime changes

---

## Proposed Module Boundary Plan

Future implementation must remain within these defined module boundaries, touching ONLY the specified touchpoints:

### A. Endpoint Route Touchpoint

**Module:** `operator_dashboard/app.py` (Flask application endpoint routing)

**Specific Touchpoint:** `POST /api/button3/apply/official-result` endpoint handler

**Current Signature (Not Implemented Yet):**
```python
# Future endpoint location (not yet implemented)
# This endpoint remains unactivated (apply_executed=false)
@app.route('/api/button3/apply/official-result', methods=['POST'])
def apply_official_result_endpoint():
    # Current: endpoint blocked/not implemented
    # Future: accepts request with optional operation_id
    pass
```

**Future Changes (In Implementation Slice):**
- ✅ Accept `operation_id` in request JSON (OPTIONAL field)
- ✅ Pass operation_id to request handler
- ✅ Include operation_id in response JSON (OPTIONAL field)
- ❌ Do NOT activate apply execution
- ❌ Do NOT change authorization logic
- ❌ Do NOT change endpoint behavior beyond request parsing and response surfacing

**Invariant Preservation:** Endpoint remains non-activated; no execution logic changes

---

### B. Request Parsing Touchpoint

**Module:** `operator_dashboard/button3_apply_authorization_context_v1.py` (or equivalent request parsing module)

**Specific Touchpoint:** Request contract validation and field extraction

**Current Function (Hypothetical):**
```python
def parse_apply_request(request_json):
    """Extract and validate apply request fields."""
    return {
        "result_comparison_id": request_json.get("result_comparison_id"),
        "operator_approval_token": request_json.get("operator_approval_token"),
        "conflict_resolution": request_json.get("conflict_resolution"),
        "dry_run": request_json.get("dry_run", False),
        # Future: add operation_id parsing below
    }
```

**Future Changes (In Implementation Slice):**
- ✅ Extract `operation_id` from request JSON (OPTIONAL)
- ✅ Normalize or reject malformed operation_id deterministically
- ✅ Generate server-generated operation_id if omitted (UUID)
- ✅ Preserve all existing field parsing unchanged
- ❌ Do NOT use operation_id in authorization decision
- ❌ Do NOT include operation_id in token digest

**Implementation Details:**
- Operation_id parsing MUST occur AFTER token validation (not before)
- Malformed operation_id must be rejected or normalized deterministically
- Server generation must use UUID.uuid4() or equivalent
- Invalid UTF-8 or oversized operation_id (>255 bytes) must be rejected

**Invariant Preservation:** Token validation unchanged; authorization independent

---

### C. Response Serialization Touchpoint

**Module:** `operator_dashboard/button3_apply_response_builder_v1.py` (or equivalent response builder)

**Specific Touchpoint:** Response JSON structure and field serialization

**Current Function (Hypothetical):**
```python
def build_apply_response(status, audit_id, error_message=None):
    """Build apply endpoint response."""
    return {
        "apply_status": status,
        "authorization_passed": True/False,
        "apply_executed": False,
        "mutation_performed": False,
        "learning_write_performed": False,
        "calibration_write_performed": False,
        "queue_write_performed": False,
        "audit_id": audit_id,
        "error_message": error_message,
        # Future: add operation_id field below
    }
```

**Future Changes (In Implementation Slice):**
- ✅ Add `operation_id` field to response (OPTIONAL)
- ✅ Echo operation_id from request or use server-generated value
- ✅ Preserve all existing response fields unchanged
- ✅ Ensure backward compatibility (existing clients ignoring operation_id)
- ❌ Do NOT modify apply_executed, mutation_performed, or other existing fields
- ❌ Do NOT change response semantics

**Implementation Details:**
- Response operation_id is REQUIRED in output if request included it
- Response operation_id is REQUIRED in output even if request omitted (server-generated)
- operation_id value MUST NOT be modified/normalized in response
- Existing clients that don't use operation_id must continue unchanged

**Invariant Preservation:** Response structure additive; no existing field changes

---

### D. Audit/Provenance Touchpoint

**Module:** `operator_dashboard/button3_apply_audit_logger_v1.py` (or equivalent audit logging)

**Specific Touchpoint:** Audit trail logging for apply operations

**Current Function (Hypothetical):**
```python
def log_apply_audit(audit_id, operator_token_digest, result_comparison_id):
    """Log apply operation to audit trail."""
    audit_record = {
        "audit_id": audit_id,
        "timestamp": datetime.utcnow(),
        "operator_token_digest": operator_token_digest,
        "result_comparison_id": result_comparison_id,
        # Future: add operation_id logging below
    }
    # Write to audit log
```

**Future Changes (In Implementation Slice):**
- ✅ Include `operation_id` in audit record (OPTIONAL)
- ✅ Correlate operation_id with audit_id in logs
- ✅ Enable future replay/investigation using operation_id
- ✅ Preserve all existing audit fields unchanged
- ❌ Do NOT change audit semantics
- ❌ Do NOT change authorization audit logging

**Implementation Details:**
- Audit record MUST include operation_id for traceability
- Audit record MUST include audit_id for correlation
- Audit record MUST be queryable by operation_id for investigation
- Existing audit fields remain unchanged

**Invariant Preservation:** Audit trail extended; no existing record semantics changed

---

### E. Tests-Only Support Touchpoint

**Module:** New test files (no modification to production code)

**Specific Touchpoints:**
- `operator_dashboard/test_button3_apply_operation_id_request_parsing_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_response_surfacing_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_token_digest_regression_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_token_consume_regression_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_compatibility_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_malformed_handling_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_no_mutation_v1.py`
- `operator_dashboard/test_button3_apply_operation_id_audit_provenance_v1.py`

**Future Changes (In Implementation Slice):**
- ✅ Create test files for all 8 test categories
- ✅ All 32+ tests organized by category
- ✅ Tests validate invariants and boundaries
- ✅ Tests provide evidence for stop condition monitoring
- ❌ Do NOT modify non-test files beyond the 4 touchpoints above (A-D)

---

### F. Explicitly Blocked Touchpoints

The following module/file categories MUST NOT be modified in any implementation slice:

#### Button 1 Modules (Blocked)
- ❌ `operator_dashboard/button1_*`
- ❌ `operator_dashboard/test_button1_*`
- ❌ Any discovery, ranking, or provider code

#### Button 2 Modules (Blocked)
- ❌ `operator_dashboard/button2_*`
- ❌ `operator_dashboard/test_button2_*`
- ❌ Any PDF generation, template, or delivery code
- ❌ Any WeasyPrint or rendering code

#### Learning/Calibration Modules (Blocked)
- ❌ Any learning execution modules
- ❌ Any calibration update modules
- ❌ Any model training code

#### Queue/Database Modules (Blocked)
- ❌ Any queue writing modules
- ❌ Any database write modules
- ❌ Any fighter/fight record mutation code

#### Dashboard/UI Modules (Blocked)
- ❌ Any dashboard template code
- ❌ Any UI rendering code
- ❌ Any static asset modification

#### Token/Authorization Modules (Blocked)
- ❌ Token digest computation (UNCHANGED)
- ❌ Token validation logic (UNCHANGED)
- ❌ Authorization decision logic (UNCHANGED)
- ❌ Token consume semantics (UNCHANGED)

---

## Proposed Test File Plan

All 8 test categories will be implemented in separate test files for clarity, organization, and independent validation:

### Test Category 1: Additive Request Parsing (4 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_request_parsing_v1.py`

**Test 1.1:** Request with operation_id field parses successfully
- Validation: Confirm operation_id extracted from request JSON
- Evidence: Parsed operation_id matches provided value
- Scope: Verify parsing doesn't break existing fields

**Test 1.2:** Request without operation_id field parses successfully
- Validation: Confirm parsing succeeds even when operation_id omitted
- Evidence: Parser returns success; server-generated operation_id available
- Scope: Verify backward compatibility with existing clients

**Test 1.3:** operation_id parsing does not interfere with existing required fields
- Validation: Confirm result_comparison_id, operator_approval_token, conflict_resolution, dry_run all parsed correctly regardless of operation_id presence
- Evidence: All existing fields have correct values in parsed result
- Scope: Verify additive principle preserved

**Test 1.4:** Malformed operation_id is deterministically handled (normalized or rejected)
- Validation: Confirm non-UUID operation_id values are handled deterministically
- Evidence: Same input produces same handling (rejection or normalization)
- Scope: Verify determinism; no random behavior

**Pass Criteria:** All 4 tests pass, no regression in existing client paths

---

### Test Category 2: Additive Response Surfacing (4 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_response_surfacing_v1.py`

**Test 2.1:** Response includes operation_id when provided in request
- Validation: Confirm operation_id field present in response JSON when request included it
- Evidence: Response JSON contains "operation_id" key with correct value
- Scope: Verify response surfacing works

**Test 2.2:** Response includes server-generated operation_id when omitted from request
- Validation: Confirm operation_id field present in response even if request omitted it
- Evidence: Response JSON contains "operation_id" key with UUID value
- Scope: Verify server generation works

**Test 2.3:** operation_id value is unchanged in response (not normalized/stripped)
- Validation: Confirm operation_id value echoed exactly in response
- Evidence: Response operation_id equals request operation_id (when provided)
- Scope: Verify no modification of operation_id

**Test 2.4:** Existing response fields unchanged (apply_status, audit_id, error_message, etc.)
- Validation: Confirm all existing response fields present and unchanged
- Evidence: apply_executed=false, mutation_performed=false, all existing fields present
- Scope: Verify additive response principle

**Pass Criteria:** All 4 tests pass, backward compatibility maintained

---

### Test Category 3: Token Digest Regression (3 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_token_digest_regression_v1.py`

**Test 3.1:** Token digest identical with operation_id in request vs. without
- Validation: Compute token digest for two requests: one with operation_id, one without (identical otherwise)
- Evidence: Both digests are identical (bit-for-bit match)
- Scope: Verify operation_id doesn't affect digest computation

**Test 3.2:** Token validation success/failure independent of operation_id value
- Validation: Valid token passes regardless of operation_id; invalid token fails regardless of operation_id
- Evidence: Authorization passed/failed independent of operation_id presence/value
- Scope: Verify authorization independence

**Test 3.3:** Two requests differing only in operation_id produce identical token digests
- Validation: Request A with operation_id="id1", Request B with operation_id="id2", all else identical
- Evidence: Computed digests are identical
- Scope: Verify operation_id excluded from digest

**Pass Criteria:** All 3 tests pass, no token digest changes

---

### Test Category 4: Token Consume Regression (4 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_token_consume_regression_v1.py`

**Test 4.1:** Token consume behavior unchanged with operation_id present
- Validation: Submit request with operation_id; verify consume-once semantics enforced
- Evidence: Same token reused = consume blocked (same as without operation_id)
- Scope: Verify consume logic unchanged

**Test 4.2:** Token consume behavior unchanged with operation_id absent
- Validation: Submit request without operation_id; verify consume-once semantics enforced
- Evidence: Consume behavior identical to requests with operation_id
- Scope: Verify backward compatibility for consume

**Test 4.3:** Token consume-once-per-token semantics enforced regardless of operation_id value
- Validation: Submit two requests with same token, different operation_ids
- Evidence: Second request blocked by consume logic (token already consumed)
- Scope: Verify operation_id doesn't enable retry

**Test 4.4:** No operation_id-based retry loophole (same token + different operation_ids blocked)
- Validation: Attempt bypass using operation_id variation
- Evidence: Consume logic rejects replay regardless of operation_id change
- Scope: Verify retry protection

**Pass Criteria:** All 4 tests pass, consume-once enforced on token

---

### Test Category 5: Missing Operation_ID Compatibility (3 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_compatibility_v1.py`

**Test 5.1:** Requests without operation_id continue to work unchanged
- Validation: Submit request without operation_id field; verify processing succeeds
- Evidence: Response indicates success; existing fields correct
- Scope: Verify backward compatibility

**Test 5.2:** Legacy clients not sending operation_id are unaffected
- Validation: Simulate legacy client (no operation_id support); verify behavior unchanged
- Evidence: Request/response cycle identical to pre-implementation behavior
- Scope: Verify no breaking changes

**Test 5.3:** Server generates valid operation_id for audit when request omits it
- Validation: Submit request without operation_id; examine audit log
- Evidence: Audit record includes operation_id (server-generated UUID)
- Scope: Verify audit still functional

**Pass Criteria:** All 3 tests pass, backward compatibility guaranteed

---

### Test Category 6: Malformed Operation_ID Handling (4 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_malformed_handling_v1.py`

**Test 6.1:** Non-UUID operation_id values are accepted or deterministically normalized
- Validation: Submit request with non-UUID operation_id (e.g., "my-operation-123")
- Evidence: Processing succeeds; handling is deterministic (same input = same output)
- Scope: Verify flexible operation_id handling

**Test 6.2:** Invalid UTF-8 or oversized operation_id is rejected with clear error
- Validation: Submit request with invalid UTF-8 bytes or operation_id > 255 bytes
- Evidence: Request rejected with specific error message (no internal state exposed)
- Scope: Verify validation and security

**Test 6.3:** No security bypass through operation_id injection or encoding attack
- Validation: Attempt injection/encoding attacks via operation_id field
- Evidence: All attack attempts rejected or safely handled; no security bypass
- Scope: Verify security hardening

**Test 6.4:** Error messages do not expose internal state
- Validation: Trigger malformed operation_id errors; examine error messages
- Evidence: Error messages are generic (no stack traces, internal paths, or secrets)
- Scope: Verify error message safety

**Pass Criteria:** All 4 tests pass, deterministic and secure handling

---

### Test Category 7: No Mutation Behavior Change (7 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_no_mutation_v1.py`

**Test 7.1:** apply_executed remains false
- Validation: Verify apply_executed=false in response
- Evidence: Response field is always false
- Scope: Verify no apply execution

**Test 7.2:** mutation_performed remains false
- Validation: Verify mutation_performed=false in response
- Evidence: Response field is always false
- Scope: Verify no mutation execution

**Test 7.3:** No database writes
- Validation: Check database before/after request; verify no new records
- Evidence: Database state identical before/after
- Scope: Verify no persistence

**Test 7.4:** No queue mutations
- Validation: Check queue before/after request; verify no new messages
- Evidence: Queue state identical before/after
- Scope: Verify no queueing

**Test 7.5:** No learning writes or execution
- Validation: Verify learning execution blocked; no learning logs
- Evidence: No learning writes detected
- Scope: Verify learning remains blocked

**Test 7.6:** No calibration writes
- Validation: Verify calibration data unchanged; no calibration logs
- Evidence: Calibration state identical before/after
- Scope: Verify calibration remains blocked

**Test 7.7:** No side effects beyond audit logging
- Validation: Verify only audit log modified; all other state unchanged
- Evidence: Audit log includes new record; all other logs/state unchanged
- Scope: Verify isolated side effects

**Pass Criteria:** All 7 tests pass, no mutations executed

---

### Test Category 8: Audit/Provenance (3 tests)

**Test File:** `operator_dashboard/test_button3_apply_operation_id_audit_provenance_v1.py`

**Test 8.1:** operation_id is included in apply audit record
- Validation: Submit request with operation_id; check audit log
- Evidence: Audit record includes operation_id field with correct value
- Scope: Verify audit inclusion

**Test 8.2:** operation_id is correlated with audit_id in logs
- Validation: Verify audit record contains both operation_id and audit_id
- Evidence: Audit record shows operation_id and audit_id linked for tracing
- Scope: Verify correlation

**Test 8.3:** Audit trail supports future replay/investigation using operation_id
- Validation: Query audit log by operation_id; verify full trace recoverable
- Evidence: Audit records queryable by operation_id; full operation context available
- Scope: Verify traceability

**Pass Criteria:** All 3 tests pass, audit trail operational

---

## Required Implementation Test Matrix

**Summary of all 8 test categories:**

| Test Category | Test Count | Location | Lock Status | Execution Gate |
|---|---|---|---|---|
| Additive request parsing | 4 | test_button3_apply_operation_id_request_parsing_v1.py | ✅ Locked in design | Must pass |
| Additive response surfacing | 4 | test_button3_apply_operation_id_response_surfacing_v1.py | ✅ Locked in design | Must pass |
| Token digest regression | 3 | test_button3_apply_operation_id_token_digest_regression_v1.py | ✅ INVARIANT 1-3 | Must pass |
| Token consume regression | 4 | test_button3_apply_operation_id_token_consume_regression_v1.py | ✅ INVARIANT 4-6 | Must pass |
| Missing operation_id compatibility | 3 | test_button3_apply_operation_id_compatibility_v1.py | ✅ Locked in design | Must pass |
| Malformed operation_id handling | 4 | test_button3_apply_operation_id_malformed_handling_v1.py | ✅ Locked in design | Must pass |
| No mutation behavior change | 7 | test_button3_apply_operation_id_no_mutation_v1.py | ✅ INVARIANT 8 | Must pass |
| Audit/provenance | 3 | test_button3_apply_operation_id_audit_provenance_v1.py | ✅ Locked in design | Must pass |

**Total Tests Required:** 32 minimum tests (all categories) must pass before implementation can be activated

**Activation Gate:** Implementation slice MUST pass ALL tests in ALL categories before endpoint activation can be considered

---

## Invariant Preservation Plan

The implementation plan preserves all 9 locked invariants from the design through structured verification:

### Token Digest Invariants (3 invariants)

**INVARIANT 1: No change to token digest algorithm**
- **Verification:** Token digest regression tests (Category 3) verify digest computation unchanged
- **Implementation Approach:** Do NOT modify `operator_dashboard/button3_token_digest_v1.py` or token computation logic
- **Stop Condition:** If Test 3.1 fails (digests differ), STOP immediately

**INVARIANT 2: operation_id does NOT weaken token validation**
- **Verification:** Authorization independence tests verify token validation independent of operation_id
- **Implementation Approach:** Parse operation_id AFTER token validation completes
- **Stop Condition:** If Test 3.2 fails (validation depends on operation_id), STOP immediately

**INVARIANT 3: Token digest semantic invariance**
- **Verification:** Test 3.3 verifies two requests differing only in operation_id produce identical digests
- **Implementation Approach:** Exclude operation_id from all digest computation
- **Stop Condition:** If Test 3.3 fails (digests differ by operation_id), STOP immediately

### Token Consume Invariants (3 invariants)

**INVARIANT 4: No change to consume timing**
- **Verification:** Token consume regression tests (Category 4) verify timing unchanged
- **Implementation Approach:** Do NOT modify token consume timing logic
- **Stop Condition:** If Test 4.1 or 4.2 fails (timing changed), STOP immediately

**INVARIANT 5: No change to consume success/failure logic**
- **Verification:** Tests 4.1-4.2 verify success/failure semantics unchanged
- **Implementation Approach:** Do NOT modify consume success/failure determination
- **Stop Condition:** If consume logic behavior changes, STOP immediately

**INVARIANT 6: operation_id does not create retry loophole**
- **Verification:** Tests 4.3-4.4 verify consume-once enforced despite operation_id variation
- **Implementation Approach:** Enforce consume-once on token, not operation_id
- **Stop Condition:** If Test 4.4 fails (retry loophole exists), STOP immediately

### Endpoint/Mutation Invariants (3 invariants)

**INVARIANT 7: Apply endpoint remains non-activated**
- **Verification:** No mutation tests (Category 7) verify apply_executed remains false
- **Implementation Approach:** Do NOT add apply execution logic
- **Stop Condition:** If Test 7.1 fails (apply_executed=true), STOP immediately

**INVARIANT 8: No apply execution**
- **Verification:** Tests 7.1-7.7 verify no execution and no writes
- **Implementation Approach:** Response parsing/surfacing only; no execution
- **Stop Condition:** If any Test 7.x fails, STOP immediately

**INVARIANT 9: Endpoint semantics unchanged**
- **Verification:** All additive tests verify request/response structure changed only for operation_id
- **Implementation Approach:** Add only operation_id field to request parsing and response surfacing
- **Stop Condition:** If any existing behavior changes, STOP immediately

---

## Implementation Stop Conditions

Implementation MUST STOP immediately if ANY of these conditions occur:

### Stop Condition 1: Token Digest Drift Detected

**Trigger:** Test Category 3 (Token Digest Regression) fails any test
- Test 3.1 fails: Digests differ with/without operation_id
- Test 3.2 fails: Token validation depends on operation_id
- Test 3.3 fails: Different operation_ids produce different digests

**Action:** STOP implementation immediately
- Revert all changes
- Escalate to governance review
- Document root cause

**Reason:** Token digest is foundational to token security; any drift violates core design

---

### Stop Condition 2: Token Consume Drift Detected

**Trigger:** Test Category 4 (Token Consume Regression) fails any test
- Test 4.1/4.2 fails: Consume timing or semantics changed
- Test 4.3/4.4 fails: Retry loophole detected

**Action:** STOP implementation immediately
- Revert all changes
- Escalate to governance review
- Investigate consume logic

**Reason:** Token consume is foundational to replay protection; any drift violates security

---

### Stop Condition 3: Authorization Semantic Drift Detected

**Trigger:** Authorization decision changes based on operation_id
- operation_id affects token validation
- operation_id affects authorization decision
- authorization behavior differs with/without operation_id

**Action:** STOP implementation immediately
- Revert all changes
- Escalate to governance review
- Investigate authorization logic

**Reason:** Authorization independence is locked; any drift violates design

---

### Stop Condition 4: Mutation/Write Behavior Change Detected

**Trigger:** Test Category 7 (No Mutation Behavior Change) fails any test
- Test 7.1-7.7 fails: apply_executed changes, mutation_performed changes, or writes occur

**Action:** STOP implementation immediately
- Revert all changes
- Escalate to governance review
- Investigate mutation logic

**Reason:** Mutation suppression is foundational to governance; any drift violates invariants

---

### Stop Condition 5: Customer-Visible Behavior Change Outside Operation_ID Surfacing

**Trigger:** Response structure changes in any field OTHER than operation_id
- apply_status changes
- authorization_passed changes
- error_message changes
- Any existing field modified or removed

**Action:** STOP implementation immediately
- Revert all changes
- Verify only operation_id field added
- Escalate if other fields changed

**Reason:** Backward compatibility requires unchanged behavior for all existing fields

---

### Stop Condition 6: Backward Compatibility Loss Without Operation_ID

**Trigger:** Test Category 5 (Missing Operation_ID Compatibility) fails any test
- Test 5.1 fails: Requests without operation_id fail to process
- Test 5.2 fails: Legacy client behavior breaks
- Test 5.3 fails: Audit trail broken when operation_id omitted

**Action:** STOP implementation immediately
- Revert all changes
- Fix compatibility issues
- Re-run backward compatibility tests

**Reason:** Backward compatibility is non-negotiable; legacy clients must continue working

---

### Stop Condition 7: Test Category Missing or Not Fully Passing

**Trigger:** Any test category is missing or has failing tests
- Fewer than 4 tests in request parsing category
- Any test in any category fails
- Test file incomplete or not executable

**Action:** STOP implementation immediately
- Do NOT proceed to production
- Complete all test categories
- Ensure all tests passing before deployment

**Reason:** Test matrix completeness is prerequisite for activation

---

### Stop Condition 8: Unexpected Button 1/Button 2 Change Detected

**Trigger:** Button 1 or Button 2 code/behavior changes detected
- Button 1 discovery or ranking modified
- Button 2 PDF generation or delivery modified
- Cross-button enforcement changed

**Action:** STOP implementation immediately
- Revert all changes
- Verify changes scoped to Button 3 only
- Escalate if cross-button impact

**Reason:** Cross-track isolation is locked; Button 1/2 must remain unaffected

---

## Explicit Blocked Paths

The following code paths MUST NOT be modified in any implementation slice:

### Blocked Path 1: Apply Endpoint Activation
- ❌ No apply execution logic added
- ❌ No apply_executed=true logic
- ❌ No actual apply operations triggered
- **Scope:** Endpoint remains non-activated; response-only operations

### Blocked Path 2: Database Mutations
- ❌ No writes to fights database
- ❌ No writes to fighter records
- ❌ No writes to matchup data
- **Scope:** No durable writes beyond audit logging

### Blocked Path 3: Queue Write Operations
- ❌ No writes to fight queue
- ❌ No writes to analysis queue
- ❌ No writes to processing queue
- **Scope:** No queue mutations

### Blocked Path 4: Calibration/Learning Execution
- ❌ No learning logic enabled
- ❌ No calibration data written
- ❌ No model updates triggered
- **Scope:** Learning remains separately gated

### Blocked Path 5: Token Digest Changes
- ❌ No modification to token digest algorithm
- ❌ No inclusion of operation_id in digest
- ❌ No token generation changes
- **Scope:** Token digest computation unchanged

### Blocked Path 6: Token Consume Changes
- ❌ No modification to consume timing
- ❌ No changes to consume success/failure logic
- ❌ No operation_id-based retry bypass
- **Scope:** Token consume semantics locked

### Blocked Path 7: Authorization Logic Changes
- ❌ No operation_id-based authorization
- ❌ No changes to authorization contract
- ❌ No modification of token validation logic
- **Scope:** Authorization independent of operation_id

### Blocked Path 8: Dashboard/UI Changes
- ❌ No display of operation_id in dashboard
- ❌ No modification of dashboard template
- ❌ No UI changes based on operation_id
- **Scope:** Endpoint-binding only; no UI changes approved

### Blocked Path 9: Provider/Cross-Track Changes
- ❌ No modification to Button 1 discovery or ranking
- ❌ No changes to Button 2 PDF generation
- ❌ No unrelated Button 3 runtime changes
- **Scope:** Scoped to Button 3 apply endpoint-binding

---

## Future Implementation Execution Checklist

Before the future implementation slice is approved for execution, this checklist MUST be completed:

### Pre-Implementation Validation

- [ ] All 3 source artifacts (design, review, gate) locked and reviewed
- [ ] Implementation plan created and reviewed (this slice)
- [ ] Module boundaries clearly defined (Section: Proposed Module Boundary Plan)
- [ ] Test file structure established (Section: Proposed Test File Plan)
- [ ] All 8 test categories planned with sub-requirements
- [ ] Stop conditions documented and understood
- [ ] Blocked paths clearly identified
- [ ] Governance rules preserved

### Implementation Phase

- [ ] Module A (Endpoint Route Touchpoint) implemented with operation_id parsing
- [ ] Module B (Request Parsing) implemented with deterministic operation_id handling
- [ ] Module C (Response Serialization) implemented with operation_id surfacing
- [ ] Module D (Audit/Provenance) implemented with operation_id logging
- [ ] Module E (Test Files) created with all 8 categories (32+ tests)

### Test Execution Phase

- [ ] Category 1 (Additive Request Parsing): 4/4 tests passing
- [ ] Category 2 (Additive Response Surfacing): 4/4 tests passing
- [ ] Category 3 (Token Digest Regression): 3/3 tests passing
- [ ] Category 4 (Token Consume Regression): 4/4 tests passing
- [ ] Category 5 (Missing Operation_ID Compatibility): 3/3 tests passing
- [ ] Category 6 (Malformed Operation_ID Handling): 4/4 tests passing
- [ ] Category 7 (No Mutation Behavior Change): 7/7 tests passing
- [ ] Category 8 (Audit/Provenance): 3/3 tests passing

### Stop Condition Verification

- [ ] Stop Condition 1 (Token Digest): Not triggered
- [ ] Stop Condition 2 (Token Consume): Not triggered
- [ ] Stop Condition 3 (Authorization): Not triggered
- [ ] Stop Condition 4 (Mutation): Not triggered
- [ ] Stop Condition 5 (Customer Behavior): Not triggered
- [ ] Stop Condition 6 (Backward Compatibility): Not triggered
- [ ] Stop Condition 7 (Test Matrix): Not triggered
- [ ] Stop Condition 8 (Cross-Track): Not triggered

### Governance Verification

- [ ] All 9 invariants preserved (design review)
- [ ] All blocked paths respected (no code outside boundaries)
- [ ] Cross-track isolation maintained (Button 1/2 unchanged)
- [ ] Learning remains blocked (separately gated)
- [ ] Token/auth/mutation invariants locked

### Production Readiness

- [ ] All 32+ tests passing
- [ ] No stop conditions triggered
- [ ] All invariants verified
- [ ] Governance aligned
- [ ] Ready for production deployment

---

## Future Implementation Execution Checklist

When the future implementation slice is proposed, this checklist must be completed BEFORE approval:

### Implementation Approval Gate

**All of the following MUST be true before implementation can be approved:**

1. ✅ **Additive Only:** Code changes remain strictly additive (no required client migration)
2. ✅ **Deterministic:** operation_id handling is deterministic (same input = same output)
3. ✅ **Test-Gated:** All 8 test categories passing (32+ tests)
4. ✅ **Invariants Verified:** All 9 locked invariants preserved
5. ✅ **Token/Auth/Mutation:** No drift in token, authorization, or mutation behavior
6. ✅ **Cross-Track:** Button 1 and Button 2 governance unchanged
7. ✅ **Learning Blocked:** No learning execution, separately gated
8. ✅ **Blocked Paths Respected:** No database/queue/learning/dashboard/authz changes

**Approval authority:** All 8 conditions must be verified by governance review before implementation slice is tagged

---

## Final Planning Verdict

**STATUS: READY_FOR_NARROW_IMPLEMENTATION_SLICE**

This implementation plan defines a clear, narrow scope for future code implementation of optional `operation_id` endpoint-binding. The plan:

✅ **Translates design into code architecture** — Module boundaries (A-D) specify exact touchpoints  
✅ **Defines test structure** — 8 categories, 32+ tests, organized by file  
✅ **Locks invariant preservation** — All 9 invariants verified through tests  
✅ **Specifies stop conditions** — 8 conditions define when to halt and escalate  
✅ **Identifies blocked paths** — 9 paths explicitly forbidden  
✅ **Provides execution checklist** — Clear pre/during/post-implementation validation

**Approved For:**
- ✅ Implementation slice code writing (next slice)
- ✅ Test file creation
- ✅ Narrow, scoped code changes (only touchpoints A-D)
- ✅ Production deployment (if all tests pass)

**Blocked Until:**
- ⏳ Implementation slice created and proposed
- ⏳ All 8 test categories implemented
- ⏳ All 32+ tests passing
- ⏳ No stop conditions triggered
- ⏳ Governance approval obtained

---

## Locked Governance References

This implementation plan preserves all locked governance:

1. ✅ button3-results-accuracy-boundary-diagnosis-only-v1 (f43198c)
2. ✅ button3-official-result-governance-design-v1 (0038d30)
3. ✅ button3-apply-path-boundary-design-v1 (7b10247)
4. ✅ button3-apply-authorization-contract-design-details-v1 (9423da8)
5. ✅ button3-apply-authorization-test-gating-matrix-index-v1 (5a172e7)
6. ✅ official-source-approved-apply-operation-id-endpoint-binding-design-v1 (d94e17b)
7. ✅ official-source-approved-apply-operation-id-endpoint-binding-design-review-v1 (cb119ed)
8. ✅ official-source-approved-apply-operation-id-endpoint-binding-implementation-readiness-gate-v1 (edc7142)

All locked rules remain in force.

---

## Next Safe Slice Recommendation

**If Implementation Plan APPROVED (this plan):**

→ **Next slice:** `official-source-approved-apply-operation-id-endpoint-binding-implementation-v1`

**Purpose:** Narrow implementation slice activating operation_id endpoint-binding with full test coverage

**Scope:** Code changes ONLY to the 4 defined module touchpoints (A-D) + test files (E)

**Requirements:**
- All 8 test categories implemented (32+ tests)
- All tests passing before deployment
- All 9 invariants verified
- All stop conditions monitored during development
- All blocked paths respected

**Constraints:**
- Additive only (no required migration)
- Deterministic (consistent handling)
- Test-gated (all categories pass)
- Cross-track isolated (Button 1/2 unchanged)
- Learning blocked (separately gated)

**Success Criteria:**
- All 32+ tests passing
- No stop conditions triggered
- All invariants preserved
- Governance aligned
- Ready for production

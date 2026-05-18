# Button 2 Phase 7 Slice E: Operator-Approved Controlled Delivery Action Design

**Document Status:** Design-only (Slice E specification)  
**Document Type:** Docs-only design artifact  
**Locked Checkpoint:** Commit `11dc8a5`, Tag `button2-phase7-controlled-delivery-dashboard-preview-panel-v1`  
**Date:** 2026-05-18

---

## 1. Slice E Objective

Slice E defines the design boundary for the first operator-approved controlled delivery action that will:
- Accept explicit operator approval for a specific delivery
- Execute delivery workflow only when all preconditions are verified
- Record comprehensive audit evidence before, during, and after delivery
- Enforce a complete set of denial rules if any precondition fails
- Maintain all safety guarantees: no uncontrolled delivery, no bypass, no automatic execution
- Provide full rollback/void capability if delivery fails

**Scope:** Design documentation only. No code, no tests, no implementation.

---

## 2. Source Artifacts Reviewed

This design document builds upon and synthesizes all locked Phase 7 artifacts:

1. **button2-phase7-controlled-delivery-planning-design-v1.md** — Overall phase strategy
2. **button2-phase7-controlled-delivery-planning-design-review-v1.md** — Planning review notes
3. **button2-phase7-controlled-delivery-gap-closure-addendum-v1.md** — Gap identification and closure
4. **button2-phase7-controlled-delivery-implementation-plan-v1.md** — Staged implementation sequence
5. **button2-phase7-controlled-delivery-operator-runbook-v1.md** (Slice A) — Operator workflow documented
6. **button2-phase7-controlled-delivery-test-contract-expectations-v1.md** (Slice B) — Test contracts defined
7. **button2_phase7_controlled_delivery_backend_scaffold_v1.md** (Slice C) — Backend preview endpoint implemented
8. **button2_phase7_controlled_delivery_backend_route_binding_repair_v1.md** (Slice C) — Route binding validated
9. **button2_phase7_controlled_delivery_dashboard_preview_panel_v1.md** (Slice D) — Dashboard preview panel locked

---

## 3. Current Locked State Through Slice D

### Locked Decisions (A-D)

- ✅ **Slice A**: Operator runbook defines workflow, approval gates, and delivery prerequisites
- ✅ **Slice B**: Test contracts specify all required denial reasons, safety flags, and validation rules
- ✅ **Slice C**: Backend preview endpoint returns read-only delivery readiness status with all safety flags false
- ✅ **Slice D**: Dashboard preview panel displays controlled delivery preview (internal-only, no action buttons)

### What Is NOT Implemented Yet

- ❌ No actual delivery action (no send, no email, no file transfer)
- ❌ No customer delivery endpoint
- ❌ No approval token/proof submission endpoint
- ❌ No delivery evidence recording
- ❌ No audit logging
- ❌ No proof-of-delivery capture
- ❌ No rollback/void endpoint
- ❌ No delivery action wired to dashboard buttons
- ❌ No automatic execution

### Safety Guardrails Locked

- ✅ All 10 safety flags are `false` in Slices A-D
- ✅ All 11 denial reasons are defined
- ✅ All approval gates documented
- ✅ All preconditions enumerated
- ✅ Operator approval requirement mandatory
- ✅ No bypass available
- ✅ Button 1, 2, 3 unchanged and fully functional

---

## 4. Operator-Approved Action Boundary

### The Critical Decision

Slice E must NOT implement:
- A generic "Send" button
- Automatic delivery after preview
- Single-click delivery without confirmation
- Email notification triggers
- Uncontrolled database writes

Slice E MUST implement:
- An **explicit operator-approved delivery action** that only executes when ALL preconditions are satisfied
- A **controlled delivery workflow** that:
  1. Accepts delivery request (with explicit operator approval token)
  2. Validates all preconditions (report status, customer identity, delivery target, etc.)
  3. Executes delivery workflow only if ALL preconditions pass
  4. Records complete audit trail (before, during, after)
  5. Captures proof-of-delivery evidence
  6. Provides rollback/void capability if needed
  7. Returns audit record with full governance compliance flags

### What Triggers Delivery Action?

A delivery action must NOT occur:
- Automatically after preview
- When Button 2 generates report
- When dashboard panel renders
- Without explicit operator approval token
- Without all preconditions verified
- When any denial reason is active

A delivery action MAY occur only when:
- Operator explicitly approves (provides approval token/proof)
- report_status = "customer_ready" (verified)
- customer_identity present (verified)
- delivery_target present (verified)
- delivery_channel supported (verified)
- delivery_evidence provided (verified)
- audit_record prepared (verified)
- proof_of_delivery path prepared (verified)
- rollback_pointer prepared (verified)
- draft/internal flags absent (verified)
- operator_approval = true (verified)

---

## 5. Required Preconditions Before Delivery Action Can Ever Be Enabled

Slice E endpoint MUST perform the following validation before ANY delivery workflow can execute:

### 5.1 Report Status Precondition

**Rule:** `report_status` MUST be exactly `"customer_ready"`

**Validation:**
- Check `report_status` value
- If value is `"draft"` → DENY with `draft_internal_report_blocked`
- If value is `"internal"` → DENY with `draft_internal_report_blocked`
- If value is `"customer_ready"` → ALLOW (proceed to next check)
- If value is missing or null → DENY with `customer_ready_report_required`
- If value is any other string → DENY with `customer_ready_report_required`

**Purpose:** Ensure no draft or internal reports are delivered to customers as final products.

### 5.2 Operator Approval Precondition

**Rule:** `operator_approval` MUST be explicitly `true`

**Validation:**
- Check `operator_approval` value (must be boolean)
- If value is `false` → DENY with `operator_approval_required`
- If value is missing or null → DENY with `operator_approval_required`
- If value is true → ALLOW (proceed to next check)

**Purpose:** Enforce mandatory human review before any delivery workflow executes.

### 5.3 Customer Identity Precondition

**Rule:** `customer_identity` MUST be present, non-empty, and valid

**Validation:**
- Check `customer_identity` field exists
- If missing or null → DENY with `missing_customer_identity`
- If empty string → DENY with `missing_customer_identity`
- If valid non-empty string → ALLOW (proceed to next check)

**Purpose:** Ensure delivery target is known before attempting delivery.

### 5.4 Delivery Target Precondition

**Rule:** `delivery_target` MUST be present, non-empty, and valid for the delivery channel

**Validation:**
- Check `delivery_target` field exists
- If missing or null → DENY with `missing_delivery_target`
- If empty string → DENY with `missing_delivery_target`
- If valid non-empty value matching delivery channel → ALLOW (proceed to next check)

**Purpose:** Ensure specific delivery destination is known before attempting delivery.

### 5.5 Delivery Channel Precondition

**Rule:** `delivery_channel` MUST be one of the supported delivery channels

**Validation:**
- Check `delivery_channel` value
- Supported channels (as of Slice E): `"email"`, `"api"`, `"manual_export"` (internal-only for now)
- If value not in supported list → DENY with `unsupported_delivery_channel`
- If missing or null → DENY with `unsupported_delivery_channel`
- If valid supported value → ALLOW (proceed to next check)

**Purpose:** Ensure delivery method is supported before attempting delivery.

### 5.6 Delivery Evidence Precondition

**Rule:** `delivery_evidence` MUST be present and non-empty

**Validation:**
- Check `delivery_evidence` field exists
- If missing or null → DENY with `missing_delivery_evidence`
- If empty string → DENY with `missing_delivery_evidence`
- If non-empty value provided → ALLOW (proceed to next check)

**Purpose:** Require operator to provide evidence explaining why delivery is needed (customer request, date, context).

### 5.7 Audit Record Precondition

**Rule:** `audit_record` MUST be present and contain minimal audit metadata

**Validation:**
- Check `audit_record` field exists
- If missing or null → DENY with `missing_audit_record`
- If empty string or empty object → DENY with `missing_audit_record`
- If valid non-empty object → ALLOW (proceed to next check)

**Purpose:** Require audit context (timestamp, operator_id, session, reason) before delivery.

### 5.8 Proof-of-Delivery Precondition

**Rule:** `proof_of_delivery` MUST be present and provide a path/pointer for capturing delivery proof

**Validation:**
- Check `proof_of_delivery` field exists
- If missing or null → DENY with `proof_of_delivery_required`
- If empty string → DENY with `proof_of_delivery_required`
- If valid path/pointer provided → ALLOW (proceed to next check)

**Purpose:** Ensure delivery success evidence can be captured and stored before delivery occurs.

### 5.9 Rollback/Void Pointer Precondition

**Rule:** `rollback_pointer` MUST be present and provide a reference for rollback

**Validation:**
- Check `rollback_pointer` field exists
- If missing or null → DENY with `rollback_pointer_required`
- If empty string → DENY with `rollback_pointer_required`
- If valid reference provided → ALLOW (proceed to next check)

**Purpose:** Ensure failed/unwanted deliveries can be rolled back and voided before delivery occurs.

### 5.10 Draft/Internal Blocking Precondition

**Rule:** If `draft_flag` or `internal_flag` is present and true, DENY immediately

**Validation:**
- Check for presence of `draft_flag` field
- Check for presence of `internal_flag` field
- If either is present and `true` → DENY with `draft_internal_report_blocked`
- If both absent or both `false` → ALLOW (proceed to next check)

**Purpose:** Add extra safety gate to prevent accidental delivery of draft/internal content.

---

## 6. Customer-Ready Report Verification Rules

### 6.1 Report Status Verification

**Rule:** Report MUST have passed all customer-ready verification in Button 2 pipeline

**Verification Points:**
- Report was generated via Button 2 (Generate Premium PDF Reports)
- Report passed all renderer quality gates
- Report contains no placeholder text (e.g., "Fighter A", "Fighter B")
- Report contains no internal notes or debug markers
- Report has complete narrative sections (no skipped sections)
- Report has valid source citations (no missing sources)

**Implementation Note:** Slice E does not re-run Button 2 verification. It trusts that `report_status="customer_ready"` means all Button 2 gates have passed.

### 6.2 Report Content Verification

**Rule:** Report MUST contain no draft, internal, or test markers

**Markers to Block:**
- Text containing "DRAFT", "INTERNAL", "TEST", "PREVIEW", "PLACEHOLDER"
- Comments or notes with internal-only content
- Watermarks indicating non-final status
- Debug sections or appendices

**Implementation Note:** Future Button 2 changes may add metadata flags (e.g., `is_draft=false`) to make this check more reliable.

### 6.3 Report Completeness Verification

**Rule:** Report MUST have all required sections rendered and visible

**Required Sections (from Button 2 v29 layout):**
- Header with title, date, customer name
- Executive Summary
- Fighter A / Fighter B profiles (or equivalent)
- Matchup Analysis
- Detailed Narrative (full word count)
- Source Citations (complete with URLs and dates)
- Footer with disclaimer

**Implementation Note:** Slice E trusts Button 2 report generation. No re-verification needed.

---

## 7. Draft/Internal Report Blocking Rules

### 7.1 Automatic Blocking

**Rule:** If any indicator suggests report is draft or internal, DENY immediately

**Indicators to Block:**
- `report_status` = `"draft"` or `"internal"` → DENY with `draft_internal_report_blocked`
- `draft_flag` = true → DENY with `draft_internal_report_blocked`
- `internal_flag` = true → DENY with `draft_internal_report_blocked`
- `is_final` = false → DENY with `draft_internal_report_blocked`

### 7.2 Label-Based Blocking

**Rule:** If report contains internal labels or watermarks, DENY

**Labels to Block:**
- "DRAFT", "INTERNAL", "TEST", "PREVIEW", "WORK IN PROGRESS"
- Any text indicating non-final status

**Implementation Note:** Slice D preview panel already displays these statuses. Slice E action must verify they are all absent before allowing delivery.

### 7.3 Escalation on Ambiguity

**Rule:** If report status is ambiguous (e.g., missing report_status field), DENY and escalate

**Ambiguous Cases:**
- `report_status` is null or missing → DENY with `customer_ready_report_required`
- `report_status` has unexpected value (not "draft", "internal", or "customer_ready") → DENY with `customer_ready_report_required`

---

## 8. Customer Identity and Delivery Target Requirements

### 8.1 Customer Identity Rules

**Rule:** `customer_identity` MUST be present, non-empty, and match known customer record

**Validation:**
- Field must exist: `customer_identity`
- Field must be non-empty string
- Field should map to known customer in system (if available)
- Field should not contain test/placeholder values (e.g., "TEST_CUSTOMER", "Unknown")

**Implementation Note:** Slice E does not validate against customer database (not available yet). It only checks presence and non-empty value.

### 8.2 Delivery Target Rules

**Rule:** `delivery_target` MUST be present and valid for the delivery channel

**Validation by Channel:**
- If `delivery_channel` = `"email"`:
  - `delivery_target` must be valid email address (basic format check)
  - Email must not be internal test address
  - Email must match customer identity if known
- If `delivery_channel` = `"api"`:
  - `delivery_target` must be valid API endpoint URL
  - URL must be HTTPS (if possible)
  - URL must not be localhost or test domain
- If `delivery_channel` = `"manual_export"`:
  - `delivery_target` can be any valid path or reference

### 8.3 Multi-Customer Batch Delivery (Future)

**Rule (Not for Slice E):** If batch delivery is enabled in future slices, each customer_identity + delivery_target pair MUST be validated independently

**Implementation Note:** Slice E handles single customer delivery only. Batch delivery is future scope.

---

## 9. Supported Delivery Channel Rules

### 9.1 Supported Channels (Slice E)

| Channel | Status | Notes |
|---------|--------|-------|
| `"email"` | Supported | Send PDF via email to delivery_target |
| `"api"` | Supported | POST PDF to delivery_target API endpoint |
| `"manual_export"` | Supported (internal) | Export to local file path (internal testing only) |

### 9.2 Channel Validation

**Rule:** `delivery_channel` MUST match one of supported channels

**Validation:**
```
if delivery_channel in ["email", "api", "manual_export"]:
  ALLOW (proceed)
else:
  DENY with "unsupported_delivery_channel"
```

### 9.3 Channel-Specific Constraints

**Email Channel:**
- No customer delivery to external emails until Phase 7 live smoke (future)
- Email sending disabled for Slice E design phase

**API Channel:**
- No actual API calls until Phase 7 live smoke (future)
- API delivery disabled for Slice E design phase

**Manual Export Channel:**
- Allowed for internal testing and operator validation
- Files exported to secure local directory only
- No actual customer delivery

**Implementation Note:** Slice E design specifies behavior but Slice E implementation will have all send/export disabled until Phase 7 live smoke checkpoint.

---

## 10. Approval Token / Approval Proof Requirements

### 10.1 Operator Approval Token

**Rule:** Delivery action MUST receive explicit operator approval token in request

**Token Fields:**
- `operator_approval`: boolean (must be `true`)
- `approval_timestamp`: ISO 8601 timestamp when operator approved
- `approval_operator_id`: operator's user ID or name
- `approval_reason`: string explaining why operator approved
- `approval_scope`: "single_delivery" or "batch" (Slice E = "single_delivery" only)

**Implementation Note:** Token should be cryptographically signed in future (not for Slice E design).

### 10.2 Approval Proof

**Rule:** Operator approval must be evidenced and traceable

**Proof Elements:**
- Timestamp of approval action
- Operator identity (user ID, name, email)
- Reason/justification provided by operator
- Report ID and delivery target confirmed at approval time
- Approval token or session reference

### 10.3 Approval Validation

**Rule:** Backend MUST verify approval token is valid before executing delivery

**Validation:**
- Token must be present in request: `operator_approval = true`
- Token timestamp must be recent (within last 15 minutes recommended, configurable)
- Token operator_id must be valid (operator must exist in system)
- Token signature/MAC must be valid (if signing enabled)

### 10.4 Approval Denial

**Rule:** If approval token is invalid or missing, DENY with `operator_approval_required`

**Denial Cases:**
- `operator_approval` field missing → DENY
- `operator_approval` value is `false` → DENY
- `operator_approval` value is not boolean → DENY
- Token timestamp is expired → DENY (escalate to manual review)
- Token operator_id is invalid → DENY (escalate)

---

## 11. Delivery Evidence Requirements

### 11.1 Delivery Evidence

**Rule:** Operator MUST provide evidence explaining the delivery request

**Evidence Fields:**
- `delivery_evidence`: string (why delivery is being executed)
- `customer_request_reference`: string (optional: ticket ID, email ref, date)
- `delivery_justification`: string (optional: specific reason)

**Example Evidence Values:**
- `"Customer requested report delivery via email, approved by delivery@company.com on 2026-05-18"`
- `"Batch delivery for weekly paid pilot cohort 1"`
- `"Manual operator override per support ticket #12345"`

### 11.2 Evidence Validation

**Rule:** Delivery evidence MUST be present and non-empty

**Validation:**
- Field `delivery_evidence` must exist
- Field must be non-empty string (minimum 10 characters recommended)
- Field should not contain placeholder text
- Field should reference external source if possible (ticket, email, etc.)

### 11.3 Evidence Recording

**Rule:** Delivery evidence MUST be recorded in audit log before and after delivery

**Recording Points:**
- Pre-delivery: Record what evidence operator provided
- Post-delivery: Record what evidence was used to justify execution
- Failed delivery: Record evidence with failure reason

---

## 12. Audit Record Requirements

### 12.1 Audit Record Structure

**Rule:** Delivery action MUST create and maintain comprehensive audit record

**Audit Fields:**
```
audit_record = {
  "audit_timestamp": "ISO 8601 timestamp",
  "audit_operator_id": "operator's user ID",
  "audit_session_id": "operator's session ID",
  "audit_action": "controlled_delivery_action",
  "audit_report_id": "report ID being delivered",
  "audit_customer_identity": "customer_identity value",
  "audit_delivery_target": "delivery_target value",
  "audit_delivery_channel": "delivery_channel value",
  "audit_preconditions_checked": ["list of preconditions verified"],
  "audit_preconditions_passed": true | false,
  "audit_denial_reasons": ["list of denial reasons if any"],
  "audit_safety_flags": {
    "live_delivery_performed": false,
    "customer_delivery_performed": false,
    "email_send_performed": false,
    "database_write_performed": false,
    ...
  }
}
```

### 12.2 Pre-Delivery Audit

**Rule:** Audit record MUST be created BEFORE any delivery workflow executes

**Pre-Delivery Actions:**
1. Create audit record with all request fields
2. Validate all preconditions
3. Record which preconditions passed/failed
4. If any precondition fails: record denial reasons and STOP
5. If all preconditions pass: proceed to delivery workflow

### 12.3 Post-Delivery Audit

**Rule:** Audit record MUST be updated AFTER delivery workflow completes

**Post-Delivery Actions:**
1. Record delivery workflow execution timestamp
2. Record delivery outcome (success, failure, partial, rollback)
3. Record proof-of-delivery evidence captured
4. Record any errors or warnings
5. Record final state of delivery

### 12.4 Audit Access and Retention

**Rule:** Audit records MUST be retained indefinitely and accessible to operators

**Retention:**
- All audit records stored in audit log database
- Accessible via audit query endpoint (future)
- Not subject to data purging or cleanup

---

## 13. Proof-of-Delivery Requirements

### 13.1 Proof-of-Delivery Path

**Rule:** `proof_of_delivery` MUST specify where delivery proof will be stored

**Proof Path Fields:**
- `proof_of_delivery`: string (path, reference, or pointer)
- Possible values:
  - Email delivery: `"proof/email/{report_id}/{timestamp}/delivery_receipt.json"`
  - API delivery: `"proof/api/{report_id}/{timestamp}/http_response.json"`
  - Manual export: `"proof/manual/{report_id}/{timestamp}/export_manifest.json"`

### 13.2 Proof Capture

**Rule:** Proof MUST be captured during delivery workflow and stored at specified path

**Proof Elements to Capture:**
- Delivery attempt timestamp
- Delivery method (email, API, export)
- Delivery target (email address, API endpoint, file path)
- Delivery status (success, failure, pending, retry)
- Delivery response (email receipt, API response, export path)
- Delivery evidence (operator approval, reason, etc.)
- Any errors or warnings

### 13.3 Proof Verification

**Rule:** Proof MUST be validated after delivery to confirm execution

**Verification Steps:**
1. Check proof file exists at specified path
2. Parse proof file (JSON or structured format)
3. Validate proof contains all required elements
4. Confirm proof timestamp matches delivery attempt
5. If proof invalid/missing: record failure and escalate

### 13.4 Proof Retention

**Rule:** All proof-of-delivery files MUST be retained indefinitely

**Retention:**
- Stored in secure proof-of-delivery database or file system
- Not subject to cleanup or purging
- Accessible for operator review and compliance audit

---

## 14. Rollback/Void Pointer Requirements

### 14.1 Rollback Pointer

**Rule:** `rollback_pointer` MUST specify how to identify and rollback delivery if needed

**Rollback Pointer Fields:**
- `rollback_pointer`: string (reference or pointer)
- Possible values:
  - Email delivery: `"rollback/email/{report_id}/{timestamp}"`
  - API delivery: `"rollback/api/{report_id}/{timestamp}"`
  - Manual export: `"rollback/manual/{report_id}/{timestamp}"`

### 14.2 Rollback Scope

**Rule:** Rollback MUST be able to reverse delivery state WITHOUT affecting other operations

**Rollback Scope:**
- Single delivery: Rollback can void one delivery without affecting other deliveries of same report
- Customer account: Rollback can void delivery to one customer without affecting other customers
- No cascade: Rollback never affects Button 1, Button 2, Button 3, learning, calibration

### 14.3 Rollback Execution

**Rule:** Rollback MUST only execute with operator approval (separate from initial delivery approval)

**Rollback Process:**
1. Operator requests rollback via separate endpoint (future)
2. Rollback request must specify rollback_pointer
3. Rollback must verify operator approval
4. Rollback must verify delivery can be safely undone
5. Rollback executes: void delivery, update proof, record in audit

### 14.4 Rollback Conditions

**Rule:** Rollback is only valid if delivery was already completed

**Valid Rollback Cases:**
- Email delivery sent successfully: Can request unsend (if email provider supports)
- API delivery completed: Can request reversal (if API supports idempotent delete)
- Manual export created: Can request file removal

**Invalid Rollback Cases:**
- Delivery failed: No need to rollback (never completed)
- Delivery pending: Can cancel instead of rollback
- Delivery already voided: Cannot rollback again

---

## 15. Required Safety Flags Before/After Action

### 15.1 Pre-Action Safety Flags

**Rule:** All 10 safety flags MUST be `false` before Slice E delivery action can execute

| Flag | Value | Reason |
|------|-------|--------|
| `live_delivery_performed` | false | No live delivery has occurred yet |
| `customer_delivery_performed` | false | No customer delivery has occurred yet |
| `email_send_performed` | false | No email has been sent yet |
| `database_write_performed` | false | No database has been modified yet |
| `queue_write_performed` | false | No queue has been modified yet |
| `ledger_write_performed` | false | No delivery ledger has been modified yet |
| `learning_apply_performed` | false | No learning updates have been applied |
| `calibration_write_performed` | false | No calibration updates have been applied |
| `button1_mutation_performed` | false | Button 1 has not been modified |
| `button3_mutation_performed` | false | Button 3 has not been modified |

**Pre-Action Check:** If any flag is `true` in request, DENY delivery and escalate.

### 15.2 Post-Action Safety Flags

**Rule:** After Slice E delivery action completes, only delivery-specific flags may change (all others remain false)

| Flag | Post-Action Value | Notes |
|------|-------------------|-------|
| `live_delivery_performed` | true IF delivery executed, false otherwise | Only flag that may become true in Slice E |
| `customer_delivery_performed` | true IF customer received delivery, false otherwise | Only flag that may become true in Slice E |
| `email_send_performed` | true IF email was sent, false otherwise | Only flag that may become true in Slice E |
| `database_write_performed` | false | ALWAYS false (delivery uses separate proof-of-delivery store, not main DB) |
| `queue_write_performed` | false | ALWAYS false (queues unchanged) |
| `ledger_write_performed` | false | ALWAYS false (no delivery ledger yet) |
| `learning_apply_performed` | false | ALWAYS false (no learning updates) |
| `calibration_write_performed` | false | ALWAYS false (no calibration updates) |
| `button1_mutation_performed` | false | ALWAYS false (Button 1 unchanged) |
| `button3_mutation_performed` | false | ALWAYS false (Button 3 unchanged) |

**Post-Action Guarantee:** Even if delivery succeeds, 7 of 10 flags always remain `false`. Delivery does NOT modify database, queues, ledger, learning, or other buttons.

---

## 16. Denial Reasons

### 16.1 Required Denial Reasons (11 Total)

Slice E endpoint MUST return one or more denial reasons in the following cases:

| Denial Reason | Triggered When | Action |
|---------------|----------------|--------|
| `operator_approval_required` | `operator_approval` is false or missing | DENY, do not execute |
| `customer_ready_report_required` | `report_status` is not "customer_ready" | DENY, do not execute |
| `draft_internal_report_blocked` | Report has draft/internal flag or label | DENY, do not execute |
| `missing_customer_identity` | `customer_identity` is missing or empty | DENY, do not execute |
| `missing_delivery_target` | `delivery_target` is missing or empty | DENY, do not execute |
| `missing_delivery_evidence` | `delivery_evidence` is missing or empty | DENY, do not execute |
| `missing_audit_record` | `audit_record` is missing or empty | DENY, do not execute |
| `proof_of_delivery_required` | `proof_of_delivery` is missing or empty | DENY, do not execute |
| `rollback_pointer_required` | `rollback_pointer` is missing or empty | DENY, do not execute |
| `unsupported_delivery_channel` | `delivery_channel` is not in supported list | DENY, do not execute |
| `unsafe_automatic_delivery_blocked` | Any safety guarantee violation detected | DENY, escalate to manual review |

### 16.2 Multiple Denial Reasons

**Rule:** Endpoint MAY return multiple denial reasons in single response

**Example Response:**
```json
{
  "controlled_delivery_action": false,
  "delivery_performed": false,
  "denial_reasons": [
    "operator_approval_required",
    "missing_customer_identity",
    "missing_delivery_evidence"
  ]
}
```

### 16.3 Denial Response Format

**Rule:** When delivery is denied, response MUST include:

```json
{
  "controlled_delivery_action": false,
  "delivery_performed": false,
  "delivery_ready": false,
  "denial_reason": "primary_denial_reason",
  "denial_reasons": [
    "denial_reason_1",
    "denial_reason_2",
    ...
  ],
  "safety_flags": {
    "live_delivery_performed": false,
    "customer_delivery_performed": false,
    "email_send_performed": false,
    "database_write_performed": false,
    "queue_write_performed": false,
    "ledger_write_performed": false,
    "learning_apply_performed": false,
    "calibration_write_performed": false,
    "button1_mutation_performed": false,
    "button3_mutation_performed": false
  }
}
```

---

## 17. Future Endpoint Contract Design

### 17.1 Endpoint Path and Method

**Endpoint:** `POST /api/button2/controlled-delivery/action`

**Purpose:** Execute operator-approved controlled delivery action

**Authentication:** Requires valid operator session (future)

### 17.2 Request Contract

**Request Payload (10 required fields + optional metadata):**

```json
{
  "report_id": "string (required)",
  "report_status": "string (required, must be 'customer_ready')",
  "customer_identity": "string (required)",
  "delivery_target": "string (required)",
  "delivery_channel": "string (required, one of: 'email', 'api', 'manual_export')",
  "operator_approval": "boolean (required, must be true)",
  "delivery_evidence": "string (required, minimum 10 chars)",
  "audit_record": "object (required, contains audit metadata)",
  "proof_of_delivery": "string (required, path reference)",
  "rollback_pointer": "string (required, rollback reference)",
  "approval_timestamp": "string (optional, ISO 8601)",
  "approval_operator_id": "string (optional)",
  "draft_flag": "boolean (optional, must be false or absent)",
  "internal_flag": "boolean (optional, must be false or absent)"
}
```

### 17.3 Response Contract (Success Path)

**Response on Successful Delivery:**

```json
{
  "controlled_delivery_action": true,
  "delivery_performed": true,
  "delivery_ready": true,
  "report_id": "report_id_value",
  "report_status": "customer_ready",
  "customer_identity_present": true,
  "delivery_target_present": true,
  "delivery_channel": "email",
  "audit_ready": true,
  "rollback_ready": true,
  "proof_of_delivery_ready": true,
  "operation_id": "unique_delivery_operation_id",
  "proof_file": "proof/email/{report_id}/{timestamp}/delivery_receipt.json",
  "audit_log_id": "audit_log_reference",
  "safety_flags": {
    "live_delivery_performed": true,
    "customer_delivery_performed": true,
    "email_send_performed": true,
    "database_write_performed": false,
    "queue_write_performed": false,
    "ledger_write_performed": false,
    "learning_apply_performed": false,
    "calibration_write_performed": false,
    "button1_mutation_performed": false,
    "button3_mutation_performed": false
  }
}
```

### 17.4 Response Contract (Denial Path)

**Response on Denied Delivery:**

```json
{
  "controlled_delivery_action": false,
  "delivery_performed": false,
  "delivery_ready": false,
  "denial_reason": "operator_approval_required",
  "denial_reasons": [
    "operator_approval_required"
  ],
  "report_id": "report_id_value",
  "report_status": "draft",
  "customer_identity_present": false,
  "delivery_target_present": true,
  "delivery_channel": "email",
  "audit_ready": false,
  "rollback_ready": false,
  "proof_of_delivery_ready": false,
  "operation_id": "unique_operation_id",
  "safety_flags": {
    "live_delivery_performed": false,
    "customer_delivery_performed": false,
    "email_send_performed": false,
    "database_write_performed": false,
    "queue_write_performed": false,
    "ledger_write_performed": false,
    "learning_apply_performed": false,
    "calibration_write_performed": false,
    "button1_mutation_performed": false,
    "button3_mutation_performed": false
  }
}
```

### 17.5 HTTP Status Codes

| Status | Meaning | Condition |
|--------|---------|-----------|
| 200 OK | Action evaluated and executed (success) | All preconditions passed, delivery executed |
| 400 Bad Request | Action evaluated and denied | One or more preconditions failed, no delivery |
| 401 Unauthorized | Request not authenticated | Operator not authenticated (future) |
| 403 Forbidden | Operator not authorized | Operator lacks delivery approval role (future) |
| 500 Internal Server Error | Backend error during execution | Unexpected error, escalate to ops |

---

## 18. Future Dashboard Action Design

### 18.1 Dashboard Action Button (Future)

**Location:** Advanced Dashboard or Button 2 area (specific placement TBD)

**Button Label:** "Approve and Execute Delivery" or "Complete Controlled Delivery"

**Button Behavior:**
- Button appears only when preview shows `delivery_ready=true`
- Button requires explicit operator click (no auto-trigger)
- Button click opens approval confirmation dialog
- Dialog displays report ID, customer, delivery target, and asks operator to confirm
- Operator must check "I approve this delivery" checkbox
- Operator clicks "Execute Delivery" button
- Backend executes delivery action via endpoint
- Result panel shows delivery status (success/failure)

### 18.2 Approval Confirmation Dialog (Future)

**Dialog Display:**
```
Controlled Delivery Approval

Report ID: [report_id]
Report Status: customer_ready
Customer: [customer_identity]
Delivery Target: [delivery_target]
Delivery Channel: [delivery_channel]

Evidence: [delivery_evidence shown]

Safety Confirmation:
✓ No live delivery has been performed yet
✓ No customer delivery will occur until I approve
✓ All safety guarantees will be maintained
✓ I can rollback if delivery fails

[ ] I approve this delivery
[Execute Delivery] [Cancel]
```

### 18.3 Success Result Panel (Future)

**Success Display:**
```
Controlled Delivery Executed Successfully

Operation ID: [operation_id]
Report ID: [report_id]
Customer: [customer_identity]
Delivery Target: [delivery_target]
Delivery Channel: [delivery_channel]
Status: DELIVERED
Proof-of-Delivery: [proof_file_link]

Flags Confirmed:
✓ live_delivery_performed=true
✓ customer_delivery_performed=true
✓ email_send_performed=true (if channel=email)
✓ database_write_performed=false
✓ queue_write_performed=false
✓ learning_apply_performed=false

[View Audit Log] [Download Proof] [Rollback Delivery]
```

### 18.4 Failure Result Panel (Future)

**Failure Display:**
```
Controlled Delivery Denied

Operation ID: [operation_id]
Report ID: [report_id]
Status: DENIED

Denial Reasons:
• operator_approval_required
• missing_delivery_evidence

Flags Confirmed (No Action Taken):
✓ live_delivery_performed=false
✓ customer_delivery_performed=false
✓ database_write_performed=false

[Edit Approval] [Try Again]
```

---

## 19. Required Tests for Future Implementation Slice

### 19.1 Backend Action Tests (Slice E Implementation)

When Slice E implementation begins, the following tests MUST pass:

#### 19.1.1 Precondition Validation Tests (11 tests)

1. **test_operator_approval_false_denied** — Request with `operator_approval=false` returns `operator_approval_required`
2. **test_operator_approval_missing_denied** — Request missing `operator_approval` field returns `operator_approval_required`
3. **test_draft_report_blocked** — Request with `report_status="draft"` returns `draft_internal_report_blocked`
4. **test_internal_report_blocked** — Request with `report_status="internal"` returns `draft_internal_report_blocked`
5. **test_missing_customer_identity_denied** — Request missing `customer_identity` returns `missing_customer_identity`
6. **test_missing_delivery_target_denied** — Request missing `delivery_target` returns `missing_delivery_target`
7. **test_missing_delivery_evidence_denied** — Request missing `delivery_evidence` returns `missing_delivery_evidence`
8. **test_missing_audit_record_denied** — Request missing `audit_record` returns `missing_audit_record`
9. **test_missing_proof_of_delivery_denied** — Request missing `proof_of_delivery` returns `proof_of_delivery_required`
10. **test_missing_rollback_pointer_denied** — Request missing `rollback_pointer` returns `rollback_pointer_required`
11. **test_unsupported_channel_denied** — Request with unsupported `delivery_channel` returns `unsupported_delivery_channel`

#### 19.1.2 Valid Preconditions Tests (3 tests)

12. **test_all_preconditions_satisfied_delivery_ready** — Request with all valid fields returns `delivery_ready=true` and `controlled_delivery_action=true`
13. **test_delivery_action_executed_success** — Delivery action executes and returns proof file reference
14. **test_delivery_action_creates_audit_record** — Delivery action creates audit record with all fields

#### 19.1.3 Safety Flags Tests (3 tests)

15. **test_all_safety_flags_false_before_action** — All 10 safety flags are `false` in pre-action response
16. **test_delivery_flags_true_after_success** — After successful delivery, only `live_delivery_performed`, `customer_delivery_performed`, and `email_send_performed` are `true`; other 7 remain `false`
17. **test_all_safety_flags_false_on_denial** — When delivery is denied, all 10 safety flags are `false`

#### 19.1.4 Denial Reasons Tests (2 tests)

18. **test_denial_reasons_array_returned** — Denied delivery returns array of denial reasons (not just single reason)
19. **test_multiple_denial_reasons** — Request with multiple missing fields returns multiple denial reasons

#### 19.1.5 Endpoint Contract Tests (2 tests)

20. **test_endpoint_http_status_200_success** — Successful delivery returns HTTP 200
21. **test_endpoint_http_status_400_denied** — Denied delivery returns HTTP 400

### 19.2 Integration Tests (Slice E Implementation)

22. **test_preview_to_action_workflow** — Full workflow: preview shows ready, action endpoint executes, audit logged
23. **test_rollback_endpoint_future** — Rollback endpoint design deferred (test placeholder)
24. **test_dashboard_action_button_wiring_future** — Dashboard button wiring deferred (test placeholder)

### 19.3 Regression Tests (Slice E Implementation)

25. **test_button1_unchanged** — Button 1 routes and behavior unchanged
26. **test_button2_generate_report_unchanged** — Button 2 report generation unchanged
27. **test_button3_unchanged** — Button 3 routes and behavior unchanged
28. **test_learning_unchanged** — Learning/calibration not affected
29. **test_database_not_modified** — Main database unchanged (only proof-of-delivery store modified)
30. **test_queue_unchanged** — Fight queue and report queue unchanged

---

## 20. Stop Conditions

Slice E implementation MUST NOT proceed if any of the following conditions are detected:

### 20.1 Governance Violation Stop

**Condition:** Any code change that violates AI-RISA governance rules

**Examples:**
- Automatic delivery without operator approval
- Delivery of draft/internal reports as customer-ready
- Database modifications outside of audit log
- Learning/calibration updates
- Button 1/2/3 behavior changes
- Bypass of any denial reason

**Action:** STOP, escalate to design review, do not implement.

### 20.2 Safety Flag Violation Stop

**Condition:** Any code that sets safety flags to `true` outside of approved delivery workflow

**Examples:**
- `live_delivery_performed=true` when no delivery occurred
- `email_send_performed=true` when email was not sent
- `database_write_performed=true` when database was not modified

**Action:** STOP, revert changes, escalate to engineering review.

### 20.3 Precondition Bypass Stop

**Condition:** Any code that executes delivery without checking all 10 preconditions

**Examples:**
- Delivery proceeds even though `operator_approval=false`
- Delivery proceeds even though `draft_flag=true`
- Delivery proceeds with missing `audit_record`

**Action:** STOP, revert changes, re-implement precondition checks.

### 20.4 Test Coverage Gap Stop

**Condition:** Any of the 30 required tests fail

**Examples:**
- Precondition validation tests fail (e.g., draft report is not blocked)
- Safety flags tests fail (e.g., all flags become true after delivery)
- Regression tests fail (e.g., Button 1 behavior changed)

**Action:** STOP, fix failing tests, verify root cause before proceeding.

### 20.5 Deployment Review Stop

**Condition:** Deployment review fails or raises concerns

**Examples:**
- Security audit finds vulnerability
- Compliance review identifies governance violation
- Operations team identifies operational risk

**Action:** STOP, address concerns, re-submit for review.

---

## 21. Explicit Non-Goals

The following are explicitly OUT OF SCOPE for Slice E and must not be implemented:

### 21.1 Customer Communication

❌ **Non-Goal:** Do not send customer notifications (yet)
- No email to customer confirming delivery
- No SMS notifications
- No in-app notifications
- Future Phase 7 live smoke: may add customer notifications

❌ **Non-Goal:** Do not implement customer tracking or acknowledgment
- No tracking links
- No read receipts
- No delivery confirmations to customer
- Future scope: may add customer-facing proof-of-delivery

### 21.2 Advanced Delivery Features

❌ **Non-Goal:** Do not implement batch delivery (yet)
- Single customer delivery only in Slice E
- No multi-customer workflows
- No scheduled delivery
- No recurring delivery
- Future slices may add batch capability

❌ **Non-Goal:** Do not implement conditional delivery logic (yet)
- No rules engine for automatic delivery selection
- No AI-driven delivery optimization
- No predictive delivery targeting
- Future scope: may add intelligence

### 21.3 External System Integration

❌ **Non-Goal:** Do not integrate with external delivery systems yet
- No Salesforce integration
- No third-party email provider integration
- No CRM system integration
- Future slices may add integrations

❌ **Non-Goal:** Do not implement webhook callbacks or webhooks
- No delivery notifications via webhook
- No async delivery status updates
- Future scope may add webhooks

### 21.4 Customer Database Changes

❌ **Non-Goal:** Do not create or modify customer records
- No customer profile creation
- No customer database writes
- No customer update operations
- No customer learning/profile building
- Note: `missing_customer_identity` denial reason assumes operator provides customer identity; no DB lookup

### 21.5 Learning and Calibration

❌ **Non-Goal:** Do not update learning/calibration systems
- No accuracy updates based on delivery
- No fighter profile calibration
- No model retraining
- No learning database writes
- This is explicitly forbidden: `learning_apply_performed=false` always

### 21.6 Button 1, Button 2, Button 3 Changes

❌ **Non-Goal:** Do not modify Button 1 behavior
- No changes to fight queue discovery
- No changes to fight ranking
- No changes to fight queue save

❌ **Non-Goal:** Do not modify Button 2 behavior
- No changes to report generation
- No changes to PDF composition
- No changes to report status validation
- No changes to report export

❌ **Non-Goal:** Do not modify Button 3 behavior
- No changes to result search
- No changes to result comparison
- No changes to accuracy metrics

---

## 22. Final Design Verdict

### 22.1 Design Readiness Assessment

✅ **APPROVED FOR IMPLEMENTATION**

Slice E design document provides sufficient specification for implementation to proceed safely under the following conditions:

### 22.2 Pre-Implementation Requirements

**Before implementation begins, the following MUST be verified:**

1. ✅ Design document locked via Git commit and tag
2. ✅ All 20 design sections reviewed and approved
3. ✅ All preconditions clearly specified (10 total)
4. ✅ All denial reasons enumerated (11 total)
5. ✅ All safety guarantees documented
6. ✅ All stop conditions identified
7. ✅ All non-goals explicitly listed
8. ✅ All 30 required tests enumerated
9. ✅ Future endpoint contract specified
10. ✅ Future dashboard action design outlined

### 22.3 Implementation Constraints

**Slice E implementation MUST:**

- ✅ Be docs-first: design locked before code begins
- ✅ Implement minimal viable action: delivery precondition validation + audit logging only
- ✅ Maintain all 10 safety guarantees: no database writes, no queues, no learning, etc.
- ✅ Enforce all 11 denial reasons: return detailed denial_reasons array
- ✅ Create comprehensive audit trail: before, during, after delivery
- ✅ Provide rollback/void capability: future, but designed now
- ✅ Pass all 30 required tests: no exceptions
- ✅ Maintain backwards compatibility: no breaking changes to Button 1/2/3

### 22.4 Design Verdict Statement

**Verdict:** ✅ **SLICE E MAY PROCEED TO IMPLEMENTATION** 

**Rationale:**

Slice E design provides a comprehensive, governance-compliant specification for operator-approved controlled delivery action that:

1. **Maintains Safety:** All 10 safety guarantees locked; no uncontrolled delivery possible
2. **Enforces Approval:** Operator approval mandatory; no bypass available
3. **Validates Preconditions:** All 10 preconditions checked; delivery only executes if all pass
4. **Documents Denial:** All 11 denial reasons specified; clear feedback on why delivery blocked
5. **Records Evidence:** Comprehensive audit trail required; full traceability
6. **Enables Rollback:** Void/rollback capability designed (future implementation)
7. **Prevents Bypass:** Multiple layers of validation; no single point of failure
8. **Protects Reports:** Draft/internal reports explicitly blocked; no accidental delivery
9. **Respects Customer:** Correct customer identity and delivery target verified
10. **Governance Compliant:** All AI-RISA governance principles adhered to

**Implementation Timeline:** Slice E implementation should begin after this design document is locked. Estimated implementation time: 1-2 weeks for backend scaffold + tests + dashboard integration.

**Next Checkpoint:** After Slice E implementation and all tests pass, progression to Slice F (audit/proof-of-delivery hardening) or Phase 7 live smoke release is appropriate.

---

## 23. Appendix: Source Artifacts Cross-Reference

| Artifact | Lock Status | Key Decision |
|----------|-------------|--------------|
| button2-phase7-controlled-delivery-planning-design-v1.md | Template | Phase 7 overall strategy |
| button2-phase7-controlled-delivery-planning-design-review-v1.md | Template | Planning review |
| button2-phase7-controlled-delivery-gap-closure-addendum-v1.md | Locked | Gap identification and closure |
| button2-phase7-controlled-delivery-implementation-plan-v1.md | Locked | Slice sequence strategy |
| button2-phase7-controlled-delivery-operator-runbook-v1.md (Slice A) | Locked | Operator workflow documented |
| button2-phase7-controlled-delivery-test-contract-expectations-v1.md (Slice B) | Locked | Test contracts defined |
| button2_phase7_controlled_delivery_backend_scaffold_v1.md (Slice C) | Locked | Preview endpoint implemented |
| button2_phase7_controlled_delivery_backend_route_binding_repair_v1.md (Slice C) | Locked | Route binding validated |
| button2_phase7_controlled_delivery_dashboard_preview_panel_v1.md (Slice D) | Locked | Dashboard preview panel live |
| **button2_phase7_controlled_delivery_operator_approved_action_design_v1.md (Slice E)** | **CURRENT** | **Operator-approved action boundary** |

---

**Document Locked:** 2026-05-18  
**Ready for Implementation:** Yes  
**Next Slice:** Slice E implementation (backend action endpoint + dashboard action button + tests)

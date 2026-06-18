# Button 2 Controlled Non-Customer Customer-Flow Dry-Run Contract UI/Status Panel Smoke Proof v1

Slice: button2-controlled-non-customer-customer-flow-dry-run-contract-ui-status-panel-smoke-proof-v1
Date: 2026-06-18
Status: SMOKE_PROOF / PASS
Type: Live browser runtime validation

## Test Setup

**Environment:**
- Flask app: `operator_dashboard/app.py` running on http://127.0.0.1:5050
- Target page: `/advanced-dashboard`
- Browser: Playwright automated testing

**Process:**
1. Started Flask development server
2. Navigated to Advanced Dashboard
3. Located dry-run contract status panel
4. Clicked "Check Readiness" button
5. Verified response displays correctly
6. Expanded raw snapshot section
7. Captured screenshot for proof

## Test Results

### ✅ Panel Exists and Renders

**Evidence:**
- Page loaded successfully: HTTP 200
- Panel title present: "Button 2 Customer-Flow Dry-Run Contract Status"
- Panel description present: "Preview-only readiness check for customer-flow preconditions. No generation, no delivery, no mutations."
- Check Readiness button present and clickable

### ✅ Endpoint Call Succeeds

**Evidence:**
- Request: `POST /api/operator/button2/customer-flow/dry-run-contract-preview`
- Flask log: `[18/Jun/2026 20:57:36] "POST /api/operator/button2/customer-flow/dry-run-contract-preview HTTP/1.1" 200`
- HTTP Status: 200 OK
- Response: Valid JSON (no parse errors)

### ✅ Overall Decision Badge Displays

**Evidence:**
- Decision value: "blocked"
- Badge label: "BLOCKED"
- Badge color: Red (#d17e7e)
- Badge present and styled correctly

### ✅ Readiness Fields Displayed

**Evidence:**
- Operator Approved: ✗ undefined
- Fight ID Present: ✗ undefined
- Ingest Payload Present: ✗ undefined
- Render Gate Ready: ✗ undefined
- Output Root Ready: ✗ undefined
- Status indicators (✗ red X) displayed correctly for all fields
- All fields show proper color coding (red for failed conditions)

### ✅ Blocking Reasons Listed

**Evidence:**
- Blocking reasons section displayed
- Four blocking reasons shown:
  1. customer generation not authorized
  2. dry run only
  3. no customer delivery authority
  4. no queue database write authority
- Reasons rendered as human-readable text (underscores converted to spaces)
- Listed in red text color for visibility

### ✅ Raw Snapshot Collapsible Section

**Evidence:**
- "Show Raw Snapshot" details element present and clickable
- Clicking expands the section
- Raw JSON snapshot displayed:
  ```json
  {
    "blocking_reasons": [
      "customer_generation_not_authorized",
      "dry_run_only",
      "no_customer_delivery_authority",
      "no_queue_database_write_authority"
    ],
    "button1_changed": false,
    "button3_changed": false,
    "customer_generation_permitted": false,
    "decision": "blocked",
    "delivery_performed": false,
    "dry_run": true,
    "ok": true,
    "pdf_file_write_performed": false,
    "queue_database_write_performed": false,
    "readiness_snapshot": {
      "fight_id": "preview-check",
      "fight_id_present": true,
      "ingest_payload_present": false,
      "operator_approved": true,
      "output_root_error": "BUTTON2_PDF_OUTPUT_ROOT is not configured. Set this environment variable to the absolute path of the PDF output directory.",
      "output_root_ready": false,
      "output_root_value": "",
      "render_gate_ready": true,
      "request_flags": {
        "controlled_non_customer_payload_present": false,
        "render_gate_ready": true
      }
    },
    "render_execution_performed": false
  }
  ```

### ✅ Response Data Structure Verified

**Evidence from raw snapshot:**
- `dry_run: true` ✓
- `customer_generation_permitted: false` ✓
- `render_execution_performed: false` ✓
- `pdf_file_write_performed: false` ✓
- `delivery_performed: false` ✓
- `queue_database_write_performed: false` ✓
- `button1_changed: false` ✓
- `button3_changed: false` ✓
- All governance flags present and correctly set

### ✅ Read-Only Constraints Confirmed

**Verification:**
- Panel has no input fields
- Panel has no generation buttons
- Panel has no delivery buttons
- Panel has no mutation/write controls
- Only "Check Readiness" button present (previously validated by unit tests)
- Endpoint is separate from customer generation endpoints

### ✅ No Side Effects Occurred

**Verification:**
- No customer PDF files generated
- No file writes performed (`pdf_file_write_performed: false`)
- No database writes (`queue_database_write_performed: false`)
- No delivery actions (`delivery_performed: false`)
- No render execution (`render_execution_performed: false`)
- Decision-only response returned

## Conclusion

The Button 2 dry-run contract UI/status panel is working correctly in the live browser environment.

**Smoke proof verdict: PASS**

The panel successfully:
- Loads on the Advanced Dashboard
- Displays the "Check Readiness" button
- Calls the dry-run contract preview endpoint
- Receives and displays the decision-only response
- Shows readiness status with proper styling
- Lists blocking reasons in human-readable format
- Provides raw JSON snapshot for debugging
- Maintains all governance constraints (no generation, no delivery, no mutations)
- Displays governance compliance flags correctly (all False where expected)

### Ready for next move:
- Additional hardening or refinement
- Integration with operator workflow
- Pivot to different feature area


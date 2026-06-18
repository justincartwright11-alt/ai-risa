# Button 2 Controlled Non-Customer Customer-Flow Dry-Run Contract UI/Status Panel Design v1

Slice: button2-controlled-non-customer-customer-flow-dry-run-contract-ui-status-panel-design-v1
Date: 2026-06-18
Status: Docs-only design

## Purpose

Design a read-only dry-run contract UI/status panel on the operator dashboard that displays customer-flow readiness posture without triggering customer PDF generation.

This panel remains preview-only and decision-only. It reports back the same decision-only contract result that the `/api/operator/button2/customer-flow/dry-run-contract-preview` route returns.

## Core Rule

Design first. No implementation in this slice.

- No dashboard HTML rendering code
- No JavaScript action bindings
- No API call wiring to the dry-run route
- No panel styling or layout styling
- No panel state management
- No customer-report activation

## 1) UI Panel Purpose

The dry-run contract panel is a preview-only status surface that an operator can invoke to check whether the customer-flow preconditions are ready before any generation attempt is made.

The panel displays a decision-only readiness snapshot without advancing into customer generation or mutation.

## 2) Panel Location and Context

The panel appears in the Advanced Dashboard only, not the main 3-button dashboard.

Proposed location: below the Button 2 section, alongside existing advanced tools.

Label: "Button 2 Customer-Flow Readiness Preview" or "Dry-Run Contract Status"

## 3) Required Display Fields

The panel must display:

- `operator_approved`: approval gate posture (true/false)
- `fight_id_present`: fight identifier presence (true/false)
- `ingest_payload_present`: ingest payload presence (true/false)
- `render_gate_ready`: render-gate readiness flag (true/false)
- `output_root_ready`: output-root readiness status (true/false)
- `output_root_value`: output-root path (if available)
- `decision`: readiness decision string (e.g., "blocked" or "preconditions_validated_readonly")
- `blocking_reasons`: list of blocking reason codes

## 4) Panel Behavior

The panel is read-only and stateless.

When the operator opens it:

1. Display a "Check Readiness" button or similar action trigger
2. On button click, call the `/api/operator/button2/customer-flow/dry-run-contract-preview` route
3. Receive a decision-only JSON response
4. Display the result fields on the panel
5. Highlight any blocking reasons in human-readable text
6. Display the overall decision as a badge or status indicator

No fields are editable in the panel. No automatic refresh or polling.

## 5) Status Indicators and Styling

The panel uses status indicators to communicate readiness without language barriers.

Proposed indicators:

- Green checkmark: precondition met
- Red X or warning icon: precondition not met
- Gray or neutral: not yet checked or N/A

Overall decision display:

- "BLOCKED" badge: preconditions not met, customer flow not ready
- "READY (Preview)" badge: preconditions met, but customer generation still not activated

## 6) Blocking Reasons Display

Blocking reasons are displayed as a list below the main readiness indicators.

Each blocking reason is presented in human-readable text, not code.

Example mappings:

- `customer_generation_not_authorized` → "Customer generation is not authorized in this context."
- `dry_run_only` → "This is a preview-only readiness check."
- `operator_gate_required` → "Operator approval is required."
- `no_customer_delivery_authority` → "Customer delivery authority is not configured."
- `no_queue_database_write_authority` → "Queue/database write authority is not configured."

## 7) Readiness Snapshot Display

Below the blocking reasons, display the full readiness snapshot as a collapsible details section.

This section shows the raw state data from the contract preview and helps operators debug readiness issues.

Included:

- operator_approved
- fight_id (if present)
- ingest_payload_present
- render_gate_ready
- output_root_ready
- output_root_value
- output_root_error (if any)

## 8) Interaction Constraints

The panel has no side effects.

Prohibited interactions:

- No "Approve Generation" button in this panel
- No "Trigger Generation" button in this panel
- No "Generate Now" shortcut
- No automatic or background actions
- No state mutations on the operator dashboard
- No queue or database writes from the panel

Allowed interactions:

- View readiness status
- Expand/collapse details sections
- Refresh/re-check readiness
- Navigate to other advanced dashboard tools

## 9) Relationship to the Locked Dry-Run Contract

This panel is a direct UI manifestation of the locked dry-run contract route.

The panel calls the same route and displays the same decision object fields. The panel adds no new contract behavior or validation logic.

## 10) Non-Goals

This design does not:

- implement the panel code
- add styling or CSS
- wire the panel to the backend route
- add JavaScript action handlers
- introduce panel state management
- add automatic polling or refresh
- add customer-generation buttons
- add delivery or export capabilities
- alter the dry-run contract behavior

## 11) Future Implementation Sequence

When implementation is approved, use narrow, focused slices:

1. dry-run contract UI panel scaffold (HTML structure only)
2. dry-run contract UI status indicators and styling (CSS and badges)
3. dry-run contract UI readiness snapshot display (collapsible details)
4. dry-run contract UI route integration (API call and response binding)
5. dry-run contract UI final acceptance and handoff

Each step must preserve:

- no customer-generation activation
- no delivery automation
- no queue/database writes
- no approval bypass
- no uncontrolled side effects
- no state mutations

## Conclusion

The Button 2 dry-run contract UI/status panel is designed as a read-only, decision-only preview surface on the Advanced Dashboard.

It displays customer-flow readiness posture by calling the locked dry-run contract preview route and rendering the decision-only result fields without advancing into customer generation or mutation.

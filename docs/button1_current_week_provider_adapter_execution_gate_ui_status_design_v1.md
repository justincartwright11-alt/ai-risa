# Button 1 Provider Adapter Execution Gate UI Status Design v1

Slice: button1-current-week-provider-adapter-execution-gate-ui-status-design-v1
Date: 2026-06-18
Status: Design-only

## Purpose

Define how execution_gate_status should be represented in the Button 1 UI before any UI rendering code is changed.

This slice is specification only. It does not add UI rendering, does not change runtime behavior, and does not alter execution policy.

## Scope

In scope:
- UI information architecture for execution_gate_status
- Field-to-display mapping
- State/label/color semantics
- Fail-closed display behavior
- Acceptance criteria for a future UI wiring slice

Out of scope:
- Editing templates or JavaScript
- Runtime payload changes
- Provider execution enablement
- Source calls/scraping
- Queue/database writes
- Button 2 promotion

## Baseline Inputs

Current payload evidence for execution_gate_status in Button 1 preview:
- has_execution_gate_status=True
- execution_gate_checked=True
- execution_gate_allowed=False
- execution_gate_decision=deny
- preview_only=True
- provider_execution_performed=False
- network_calls_performed=False
- source_calls_performed=False
- scraping_performed=False
- queue_write_performed=False
- database_write_performed=False
- button2_promotion_performed=False
- reason_codes include:
  - execution_gate_operator_approval_missing
  - execution_gate_provider_not_enabled

## Proposed UI Placement

In Button 1 result surface, add a new read-only panel section after Registry Adapter Status and before Source-Backed Event Cards.

Proposed section title:
- Execution Gate Status (Preview-Only)

Proposed section badges:
- Read-Only
- Operator Approval Required

## Proposed UI Fields

Required display fields:
- Gate Checked
- Gate Allowed
- Decision
- Reason Codes
- Provider ID
- Source Button
- Preview Only
- Side-Effect Safety (group)
  - Provider Execution
  - Network Calls
  - Source Calls
  - Scraping
  - Queue/DB Writes
  - Button 2 Promotion

Optional metadata fields:
- Decision Timestamp (UTC)

## Field Mapping Contract

Map UI fields from execution_gate_status payload keys:
- Gate Checked <- execution_gate_checked
- Gate Allowed <- execution_gate_allowed
- Decision <- execution_gate_decision
- Reason Codes <- execution_gate_reason_codes
- Provider ID <- provider_id
- Source Button <- source_button
- Preview Only <- preview_only
- Provider Execution <- provider_execution_performed
- Network Calls <- network_calls_performed
- Source Calls <- source_calls_performed
- Scraping <- scraping_performed
- Queue/DB Writes <- queue_write_performed OR database_write_performed
- Button 2 Promotion <- button2_promotion_performed
- Decision Timestamp <- decision_timestamp_utc

## Display Semantics

Decision state labels:
- deny -> DENY (default)
- allow -> ALLOW (preview-shape only; must still show non-executing safety flags)
- unknown/missing -> UNAVAILABLE (fail-closed)

Boolean display style:
- true -> YES
- false -> NO

Safety flags style:
- false should be rendered as NO (expected)
- true should be rendered as YES (unexpected) and highlighted as governance-risk state

Reason codes:
- Render as compact list chips or comma-separated text
- If empty/missing, render execution_gate_status_unavailable_fail_closed

## Color/Severity Guidance

- DENY: amber or red-accent informational warning
- ALLOW (preview-only): neutral/green label with explicit "Preview only, no execution" text
- UNAVAILABLE/fail-closed: red-accent fail-closed status
- Side-effect flags false: green/neutral safe markers
- Side-effect flags true: red critical markers

## Fail-Closed UI Rules

If execution_gate_status is missing, malformed, or incomplete:
- Show section with Decision=UNAVAILABLE
- Show Gate Allowed=NO
- Show Preview Only=YES
- Show all side-effect flags as NO (expected) in display contract
- Show reason code fallback: execution_gate_status_unavailable_fail_closed

UI must not infer ALLOW from partial data.

## Interaction Rules

The section must remain non-interactive in this phase:
- No execute button
- No provider enable toggle
- No approval token input
- No source call trigger
- No save/persist action
- No Button 2 promotion action

## Accessibility and Readability

- Section heading must be keyboard discoverable
- Labels should be explicit (avoid abbreviations without tooltip)
- Reason codes should wrap safely without layout overlap
- High contrast for DENY/UNAVAILABLE indicators

## Backward Compatibility

- Existing Registry Adapter Status panel remains unchanged
- Existing Button 1 preview flow remains unchanged
- Button 2 and Button 3 UI unaffected

## Future UI Wiring Acceptance Criteria

When UI wiring is implemented in a future slice, it must prove:
1. Execution Gate Status section appears only when execution_gate_status is present, or fail-closed placeholder appears when missing.
2. Decision defaults to DENY/UNAVAILABLE in all uncertain states.
3. Side-effect flags display as NO and match payload values.
4. No new interactive controls are introduced.
5. Button 2 and Button 3 visual/behavioral surfaces remain unchanged.

## Governance Commitments

This design-only slice preserves:
- Runtime behavior changed: false
- UI behavior changed: false
- Provider execution: false
- Source/network calls: false
- Scraping: false
- Queue/database writes: false
- Button 2 promotion: false
- Button 2 unaffected
- Button 3 unaffected

## Conclusion

The UI representation for execution_gate_status is defined and fail-closed by design. Actual UI rendering changes are intentionally deferred to a future isolated implementation slice.

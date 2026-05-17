# Button 1 Read-Only Dossier Export Preview to Button 2 Report Handoff Design (v1)

## Purpose
Design a safe handoff model where Button 1 read-only dossier export preview context can inform Button 2 report generation later, without opening any file writes, PDF generation, delivery, or mutation behavior from Button 1.

This slice is docs-only.

## Core Rule
- Button 1 may prepare read-only intelligence context.
- Button 2 remains the only place where report generation and export behavior belongs.
- No Button 1 PDF, export, or delivery path is permitted.

## Governance Alignment
This design preserves the three-button governance model:
- Button 1: discovery and read-only preview context only.
- Button 2: operator-gated report generation behavior only.
- Button 3: result comparison and accuracy workflows only.

## In Scope
- Define a read-only handoff contract from Button 1 to Button 2.
- Define UI and API boundary rules that prevent Button 1 export behavior.
- Define fail-closed handling when handoff payload safety checks fail.
- Define telemetry constraints for handoff readiness without mutation.

## Out of Scope
- Implementing new runtime code.
- Button 1 file output, PDF generation, delivery, publish, or customer export.
- Any new persistence, write, merge, ranking, learning, or calibration path.
- Any change that lets Button 1 bypass Button 2 operator gates.

## Handoff Concept
Button 1 produces a read-only context package that Button 2 can consume as optional report input hints.
The package is informational only and cannot trigger report generation by itself.

## Proposed Read-Only Handoff Contract
### Allowed fields
- fighter_identity_summary: sanitized text summary
- matchup_context_summary: sanitized text summary
- known_records_snapshot_refs: read-only references only
- projection_context_refs: read-only references only
- confidence_signals: read-only confidence descriptors
- preview_contract_flags:
  - preview_only=true
  - export_performed=false
  - file_write_performed=false
  - delivery_performed=false
  - profile_create_update_merge=false
  - database_ranking_writes=false
  - result_report_learning_calibration=false

### Forbidden fields
- internal_notes
- raw_source_payloads
- write_authorized
- merge_instruction
- database_pointer
- file_path_output
- pdf_output_ref
- delivery_target
- publish_instruction
- auto_generate_report

## Button Boundary Rules
### Button 1 rules
- May render copy-safe summary and handoff readiness status.
- May expose only read-only context fields.
- May not expose any generate, export, deliver, publish, or save controls for handoff.
- May not call report generation routes.

### Button 2 rules
- May accept read-only handoff context as optional prefill.
- Must still require Button 2 operator approval for any report generation/export action.
- Must not treat handoff payload as implicit approval.

## Safety Gates and Fail-Closed Behavior
- If any forbidden field appears in handoff payload, reject handoff payload and show blocked status.
- If any preview contract flag is missing or not false/true as expected, reject payload.
- If sanitization status is unknown, do not render handoff data in Button 2 prefill.
- Rejection must not mutate state and must not perform writes.

## Telemetry Constraints
### Allowed telemetry
- handoff_payload_validated
- handoff_payload_blocked
- handoff_payload_consumed_readonly

### Forbidden telemetry data
- raw internal fields
- sensitive operator free-text notes
- write instructions or delivery targets

## Acceptance Criteria
- Button 1 can provide read-only intelligence context only.
- Button 1 cannot open any report generation, export, PDF, or delivery action.
- Button 2 remains exclusive owner of report/export behavior.
- Handoff payload includes explicit zero-write preview contract flags.
- Forbidden fields are blocked and not surfaced.
- Three-button governance and gate boundaries remain intact.

## Non-Goals
- No runtime implementation in this slice.
- No new API write endpoints.
- No migration of Button 2 responsibilities into Button 1.

## Implementation Prerequisite
A separate implementation slice is required after this design lock.
That implementation slice must include executable tests proving Button 1 remains read-only and Button 2 remains the only export/report execution path.

## Final Verdict
The design safely enables Button 1 to inform Button 2 via read-only intelligence context while strictly preserving governance boundaries: Button 1 stays preview-only and Button 2 remains the sole report/export execution surface.
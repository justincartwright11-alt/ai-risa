# Button 2 Dossier Handoff Report Context Preview Design (v1)

## Purpose
Design how Button 2 can use ingested read-only handoff as report-context preview data without generating PDFs, writing files, delivering reports, or bypassing Gate 2 approval.

This slice is docs-only.

## Core Rule
- Button 2 may preview report context.
- Button 2 may not generate, export, write, deliver, or approve reports automatically.

## Locked Foundation
This design builds on the frozen handoff and ingest chain:
- button1-readonly-dossier-export-preview-to-button2-report-handoff-design-v1 (9091919)
- button1-to-button2-readonly-dossier-handoff-preview-v1 (f0c9a4c)
- button1-to-button2-readonly-dossier-handoff-api-preview-v1 (663d73f)
- button1-to-button2-readonly-dossier-handoff-api-smoke-v1 (c399f2c)
- button2-readonly-dossier-handoff-ingest-design-v1 (08fed3b)
- button2-readonly-dossier-handoff-ingest-preview-v1 (b22eb50)
- button2-readonly-dossier-handoff-ingest-api-preview-v1 (eda600c)
- button2-readonly-dossier-handoff-ingest-api-smoke-v1 (2c1db62)
- button1-to-button2-readonly-dossier-handoff-final-handoff-v1 (b7782d6)

## Button 2 Report Context Preview Boundary
Button 2 may present a preview panel that displays report-context hints derived from the ingested handoff payload.
This preview is informational only and must not trigger generation or approval actions.

## Allowed Preview Context Fields
Allowed fields are read-only, sanitized context hints only:
- destination_marker
- dossier_summary_preview
- ingest_mode
- context_kind
- preview_only
- gate2_approval_required

Allowed value constraints:
- destination_marker must be button2_report_generation_preview
- preview_only must be true
- gate2_approval_required must be true
- write/generation/export/delivery flags must remain false

## Forbidden Preview Context Fields
Do not render or propagate:
- internal_notes
- raw_source_payload
- write_authorized
- merge_instruction
- database_pointer
- file_path_output
- pdf_output_ref
- delivery_target
- publish_instruction
- auto_generate_report
- auto_approve_gate2

## Preview Rendering Behavior
Button 2 preview may:
- show a read-only report-context summary panel
- show safety badges and flag states
- show blocked state when validation fails

Button 2 preview may not:
- call report generation flows
- call export/PDF flows
- perform file writes
- perform delivery/publish operations

## Gate 2 Relationship
Gate 2 remains the only approval authority for report generation.
Preview context is never equivalent to approval and cannot satisfy Gate 2 preconditions.
No automatic approval transition is allowed from preview state.

## Report Generation Boundary
Report generation remains a separate explicit workflow.
Preview code paths must not invoke generation handlers, queue report jobs, or emit report-write commands.

## Export, PDF, Write, Delivery Restrictions
The preview path must maintain:
- button2_generation_performed=false
- pdf_generation_performed=false
- export_performed=false
- file_write_performed=false
- report_write_performed=false
- delivery_performed=false

## Fail-Closed Behavior
Preview context should fail closed when:
- destination marker is invalid
- preview_only is missing or false
- gate2_approval_required is missing or false
- forbidden fields are present
- payload is malformed

Fail-closed outcome:
- return blocked preview status
- keep all write/generation/export/delivery flags false
- perform no filesystem or network side effects

## Safety Telemetry
Allowed telemetry events:
- button2_report_context_preview_rendered
- button2_report_context_preview_blocked
- button2_report_context_preview_validation_failed

Telemetry data restrictions:
- no raw/internal/write fields
- no secrets or operator-private notes
- no approval override hints

## Future Implementation Test Expectations
- valid ingest payload renders report-context preview only
- invalid destination marker blocks preview
- forbidden fields are excluded
- preview flags remain read-only and false for mutations
- no generation/export/write/delivery side effects
- Gate 2 approval flow remains unchanged and required

## Non-Goals
This slice does not:
- implement runtime report generation integration
- add new export/PDF/delivery code
- modify Gate 2 approval semantics
- open any write or mutation pathway

## Final Verdict
Button 2 report-context preview is designed as a strict read-only presentation layer on top of ingested handoff data. It preserves Gate 2 approval authority and prevents automatic generation, export, write, delivery, or mutation behavior.
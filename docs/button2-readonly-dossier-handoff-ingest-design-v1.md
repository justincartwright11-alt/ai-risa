# Button 2 Read-Only Dossier Handoff Ingest Design (v1)

## 1. Purpose
Design how Button 2 may ingest Button 1 read-only dossier handoff context later, without weakening Button 2 approval gates or opening automatic report generation, export, or delivery behavior.

This slice is docs-only.

## 2. Locked Button 1 Handoff Foundation
This design depends on the locked Button 1 handoff chain:
- button1-to-button2-readonly-dossier-handoff-preview-v1 (f0c9a4c)
- button1-to-button2-readonly-dossier-handoff-api-preview-v1 (663d73f)
- button1-to-button2-readonly-dossier-handoff-api-smoke-v1 (c399f2c)

Foundation guarantees:
- Sanitized handoff payload
- destination_marker=button2_report_generation_preview
- preview_only=true and all write/mutation flags false

## 3. Button 2 Ingest Boundary
Button 2 ingest is preview-only context intake.
Button 2 ingest must not perform generation, export, write, delivery, or gate bypass.
Ingest context is advisory input only and cannot trigger report actions.

## 4. Allowed Ingest Fields
Button 2 may ingest only these read-only fields:
- destination_marker
- dossier_summary_preview
- preview_only
- button1_export_performed
- button2_generation_performed
- pdf_generation_performed
- file_write_performed
- delivery_performed
- report_write_performed
- profile_create_update_merge
- database_ranking_writes
- result_report_learning_calibration

Allowed field expectations:
- destination_marker must equal button2_report_generation_preview
- preview_only must be true
- all write/generation/delivery flags must be false

## 5. Forbidden Fields
Button 2 ingest must reject or ignore:
- raw_source_payload
- internal_notes
- write_authorized
- merge_instruction
- database_pointer
- file_path_output
- pdf_output_ref
- delivery_target
- publish_instruction
- auto_generate_report
- any hidden control token that implies auto-run behavior

## 6. Preview-Only Ingest Behavior
Button 2 may render ingested context in a preview panel only.
Button 2 may show read-only status badges that confirm:
- ingest_preview_only=true
- generation_not_started=true
- export_not_started=true
- delivery_not_started=true

Ingest preview must remain non-mutating and side-effect free.

## 7. Gate 2 Relationship
Gate 2 remains mandatory for report generation and export actions.
Ingest preview must not be interpreted as Gate 2 approval.
No ingest payload can satisfy, emulate, or pre-authorize Gate 2.

## 8. Report Generation Boundary
Report generation is strictly separate from ingest preview.
Generation can only occur in explicit Button 2 report generation flows after approval checks pass.
Ingest code path must not call generation functions or generation routes.

## 9. PDF/Export/Delivery Restrictions
Ingest path must not:
- generate PDF
- export files
- write reports
- deliver/publish content
- write to filesystem

All related flags must remain false during ingest preview.

## 10. Safety Telemetry
Allowed telemetry events:
- button2_handoff_ingest_preview_rendered
- button2_handoff_ingest_preview_blocked
- button2_handoff_ingest_payload_rejected

Telemetry requirements:
- include preview-only safety flags
- exclude sensitive/raw/internal fields
- never include write directives

## 11. Fail-Closed Behavior
Button 2 ingest must fail closed when:
- destination_marker is missing or invalid
- preview_only is not true
- any generation/export/write/delivery flag is true
- forbidden fields appear
- payload is malformed

Fail-closed response behavior:
- block ingest preview render
- show safe non-actionable warning
- keep all write/generation/export/delivery flags false
- perform no mutation or IO side effects

## 12. Future Implementation Tests
Required future tests:
- ingest accepts valid sanitized payload and renders preview-only context
- invalid destination_marker is rejected
- forbidden fields are rejected or stripped
- any true write/generation flag blocks ingest
- malformed payload fails safe
- Gate 2 approval path remains separate
- ingest path does not trigger generation/export/delivery/file/report writes
- telemetry contains only allowed fields

## 13. Non-Goals
This slice does not:
- implement runtime ingest code
- implement Gate 2 changes
- allow auto-generation from ingest
- allow export/PDF/delivery from ingest
- introduce persistence or mutation behavior

## 14. Final Verdict
Button 2 read-only dossier handoff ingest is designed as a strict preview-only boundary. Button 2 may display context, but may not auto-generate, auto-export, auto-deliver, or bypass approval gates. Governance integrity remains preserved across the Button 1 to Button 2 handoff path.
# button2-selected-matchup-picker-and-pdf-payload-binding-repair-v1

## Defect Reproduced
- Button 2 generated PDFs could continue using a previously persisted selected matchup preview instead of an explicitly selected current queued row.
- The Button 2 panel did not render a dedicated selectable queued-matchup list, so operators could not reliably switch matchup context inside Button 2 before generation.
- Filename freshness alone could appear correct while payload binding was stale.

## Root Cause
- Frontend: Button 2 used persisted `window.button2SelectedMatchupPreview` and auto-generated immediately in `handleButton2Click()` when that object existed, without requiring an explicit current-row selection from a Button 2 queue picker.
- Backend: `/api/button2/selected-matchup/generate-guarded-v1` accepted `selected_matchup_preview` directly from request body and did not require `selected_matchup_id` resolution against approved queue rows.
- Quality gate: Success response did not enforce strict selected-payload PDF text assertions (event/source/report slug/path/page-count) beyond basic marker checks.

## Files Changed
- `operator_dashboard/app.py`
- `operator_dashboard/templates/index.html`
- `operator_dashboard/button2_jbalia_direct_template_renderer_v1.py`
- `operator_dashboard/test_button2_selected_matchup_picker_and_pdf_payload_binding_repair_v1.py`

## Route / Payload Binding Repair
- Guarded generate route now requires:
  - `selected_matchup_id`
  - `approved_queue_rows`
- Route resolves selected row server-side from approved queue rows only.
- Route fails closed with controlled errors and no write when:
  - id missing
  - queue rows missing
  - id unknown
  - id duplicated
  - row incomplete
  - row not ready
  - row not source-backed
- Direct trust of request `selected_matchup_preview` removed for generation binding.

## UI Selection Repair
- Added Button 2 in-panel queued matchup list (`Queued Matchups (Select One)`) with explicit row selection controls.
- Row display includes required minimum fields:
  - matchup title
  - event
  - source/provider
  - readiness
  - matchup_id
- Selected row is visibly highlighted and updates existing selected preview block:
  - Selected matchup
  - Event
  - Source
  - Button 2 readiness
  - Next action
- Generate action now fails closed with clear status if no selected row exists.

## PDF Text Quality Gate
- Added strict selected-payload quality gate before success:
  - fighter A present
  - fighter B present
  - event present (when available)
  - source URL/domain present (when available)
  - selected slug appears in output filename
  - output path exists and is inside `BUTTON2_PDF_OUTPUT_ROOT`
  - 24-page contract enforced
  - stale hard-bound name pairs blocked unless selected
- If strict gate fails, generated file is removed and route returns `422 customer_pdf_quality_gate_failed`.

## Renderer Payload Surface Repair
- Updated direct Jbalia renderer source-map section to render selected event/source/report-id text into PDF content.
- Renderer now returns `report_id` metadata.

## Output/Open Route Repair
- Dynamic generation/open/library responses now include `Cache-Control: no-store` and `Pragma: no-cache` to reduce stale metadata/file selection effects.
- `Open Generated PDF` remains exact-path/filename based.

## Tests Run
- `python -m pytest operator_dashboard/test_button2_selected_matchup_picker_and_pdf_payload_binding_repair_v1.py -q`
  - Result: `10 passed`
- `python -m pytest operator_dashboard/test_operator_dashboard_generate_panel_customer_ready_pdf_actions_v1.py -q`
  - Result: file not found in this workspace
- `python -m pytest operator_dashboard/test_operator_dashboard_report_generation_checkbox_render_hard_block_v4.py -q`
  - Result: file not found in this workspace

## Live Smoke Result
- Executed temporary local HTTP smoke on localhost with non-Joshua/Dubois selected matchup (`Nadaka Yoshinari vs Songchainoi Kiatsongrit`).
- Generate route returned `200 ok`, output path existed under reports root, strict quality gate passed, open route returned `200`, governance flags remained false.
- Proof output path:
  - `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\nadaka_yoshinari_vs_songchainoi_kiatsongrit_one_samurai_1_premium_20260519T080440Z_fcc1bd6f88c2.pdf`

## Governance Proof
- Confirmed unchanged and false in guarded generation response:
  - `delivery_performed=false`
  - `external_api_delivery_performed=false`
  - `queue_write_performed=false`
  - `learning_apply_performed=false`
  - `calibration_write_performed=false`
  - `button3_mutation_performed=false`

## Final Verdict
- PASS: Button 2 now binds generation to explicit selected queue matchup id, resolves server-side from approved rows, renders selectable queued rows in-panel, and blocks stale/default payload success via strict PDF quality gate.

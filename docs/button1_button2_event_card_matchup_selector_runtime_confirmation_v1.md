# button1-button2-event-card-matchup-selector-runtime-confirmation-v1

## Runtime Confirmation Scope
Validated live dashboard runtime at `http://127.0.0.1:5050/` for the selector slice.

## Confirmed Outcomes
1. Source-Backed Event Cards appear in Button 1 runtime surface.
2. Event card shows matchup rows.
3. Selecting one matchup populates Button 2 selected-matchup preview.
4. No PDF is generated automatically.
5. No queue/delivery/learning/calibration mutation occurs.

## Runtime Evidence (Live)
- Button 1 runtime selector panel rendered with heading: `Source-Backed Event Cards`.
- Runtime counts observed from live DOM:
  - `cardCount=1`
  - `matchupCount=15`
- Operator selection action succeeded and surfaced in Button 2:
  - Status: `Selection accepted for Button 2 preview. Operator action still required to generate report.`
  - Selected preview fields populated (matchup/event/source/readiness/next action).

## Network-Call Confirmation During Runtime Interaction
Observed calls in sequence:
- `POST /api/local-ai/orchestrator/workflow-preview`
- `POST /api/local-ai/gate1/save-fights/approved-save-writer-preview`
- `POST /api/global-fighters/known-records/loader-preview`
- `POST /api/local-ai/gate1/save-fights/dry-run-apply-preview`
- `POST /api/button1-button2/event-card-matchup/select-preview`

No `/api/button2/*` generation/delivery action endpoint was triggered by selector click.

## Safety/Governance Confirmation
From runtime selected preview payload:
- `selected_for_button2=true`
- `selection_preview=true`
- `report_ready_status=ready_for_button2_preview`
- `safety_flags` all false:
  - `pdf_generation_performed=false`
  - `queue_write_performed=false`
  - `delivery_performed=false`
  - `email_send_performed=false`
  - `external_api_delivery_performed=false`
  - `learning_apply_performed=false`
  - `calibration_write_performed=false`
  - `button3_mutation_performed=false`

## Runtime Defect Found and Repaired
Issue:
- Selector click could deny with `missing_matchup` when runtime rows had no stable candidate identifier.

Fix:
- Added `selected_index` fallback path from UI selector payload to preview endpoint.
- Endpoint now resolves selected row by index when id-based lookup is unavailable.

Files updated:
- `operator_dashboard/templates/index.html`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button1_button2_event_card_matchup_selector_v1.py`

## Validation
- `operator_dashboard/test_button1_button2_event_card_matchup_selector_v1.py`: passed (`11 passed`)
- Focused adjacent regression bundle: passed (`98 passed`, `0 failed`)

# button2-explicit-operator-generate-from-selected-matchup-guarded-v1

## Purpose
Allow Button 2 to generate from the selected persisted matchup only after explicit operator action.

## Governance Scope
- Explicit operator action required.
- Selected matchup must already be confirmed for Button 2.
- Source-backed selected matchup required.
- No queue write.
- No delivery/external API delivery.
- No learning/calibration write.
- No Button 3 mutation.

## Backend
File: `operator_dashboard/app.py`

Added route:
- `POST /api/button2/selected-matchup/generate-guarded-v1`

Route behavior:
1. Rejects invalid JSON body.
2. Requires `operator_approved=true`.
3. Requires `selected_matchup_preview` object.
4. Requires `selected_for_button2=true`.
5. Requires source-backed `source_url`.
6. Derives `fight_id` from selected matchup names/event.
7. Builds safe ingest payload with destination marker:
   - `button2_report_generation_preview`
8. Delegates to existing Gate2 generation integration.
9. Returns explicit guard flags:
   - `queue_write_performed=false`
   - `delivery_performed=false`
   - `external_api_delivery_performed=false`
   - `learning_apply_performed=false`
   - `calibration_write_performed=false`
   - `button3_mutation_performed=false`

## Frontend
File: `operator_dashboard/templates/index.html`

Added:
- `BUTTON2_SELECTED_MATCHUP_GENERATE_GUARDED_ENDPOINT`
- `postButton2SelectedMatchupGenerateGuarded(selectedPreview)`
- `renderButton2GuardedGenerateResult(response)`
- `runButton2WorkflowHealthPreview()`

Updated `handleButton2Click()`:
- Restores persisted selected matchup preview.
- If no selection, shows workflow health preview + explicit selection-required message.
- If selection exists, runs guarded generation route with explicit operator-approved payload.

## Tests
Added file:
- `operator_dashboard/test_button2_explicit_operator_generate_from_selected_matchup_guarded_v1.py`

Coverage:
- invalid request body denied
- operator approval required
- selected matchup object required
- selected_for_button2 required
- source-backed requirement enforced
- delegates to generation integration with derived fight_id and safe ingest payload
- dashboard JS wiring present

## Runtime Confirmation
Live runtime at `http://127.0.0.1:5050/` showed:
- Guarded route called only after explicit Button 2 operator action.
- Selected matchup preview remained visible while generating.
- No delivery API call observed.
- No Button 3 mutation call observed.
- Main dashboard buttons remained 3.

Runtime environment blocker observed:
- PDF render dependency missing in local environment: `No module named 'weasyprint'`.
- Guarded flow still correctly enforced approval + selected-matchup constraints and no-delivery/no-mutation flags.

## Validation
- New guarded suite: `7 passed`
- Focused governed regression bundle: `107 passed`

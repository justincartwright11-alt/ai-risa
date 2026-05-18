# button1-button2-selected-matchup-runtime-persistence-preview-v1

## Purpose
Preview-only runtime persistence for selected matchup state between Button 1 selector and Button 2 preview.

## Scope Guard
- Preview-only persistence.
- No PDF generation.
- No queue write.
- No delivery.
- No learning/calibration write.
- No Button 3 mutation.

## Implementation
- File: `operator_dashboard/templates/index.html`
- Added browser-local preview persistence key:
  - `ai_risa_button2_selected_matchup_preview_v1`
- Added helper functions:
  - `getPreviewOnlySelectionPersistenceFlags()`
  - `sanitizeSelectedMatchupPreviewForPersistence(data)`
  - `persistButton2SelectedMatchupPreview(data)`
  - `loadButton2SelectedMatchupPreviewFromPersistence()`
  - `restoreButton2SelectedMatchupPreviewFromPersistence()`
- Selection success path now persists sanitized preview state.
- Selection-denied/failure paths clear persisted state.
- Runtime restore paths:
  - `DOMContentLoaded` restore
  - `handleButton2Click()` restore before rendering

## Runtime Confirmation (Live)
Validated live at `http://127.0.0.1:5050/`.

1. Operator selects matchup in Button 1.
- `selected=true`
- `persisted=true`
- Button 2 preview populated.

2. Browser reload.
- persisted state still present in localStorage.
- runtime selected preview restored automatically on load.

3. Button 2 click after reload.
- Selected matchup preview remains populated.
- No auto PDF/delivery calls observed.

## Runtime Observed Call Pattern
- `POST /api/local-ai/orchestrator/workflow-preview`
- `POST /api/local-ai/gate1/save-fights/approved-save-writer-preview`
- `POST /api/global-fighters/known-records/loader-preview`
- `POST /api/local-ai/gate1/save-fights/dry-run-apply-preview`
- `POST /api/button1-button2/event-card-matchup/select-preview`

After reload + Button 2 click:
- `POST /api/local-ai/orchestrator/workflow-preview`
- No `POST /api/button2/*` auto-generation/delivery endpoint call observed.

## Safety Flags
Persisted selected preview carries hard-false flags:
- `pdf_generation_performed=false`
- `queue_write_performed=false`
- `delivery_performed=false`
- `email_send_performed=false`
- `external_api_delivery_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

## Validation
- Selector suite: `13 passed`
- Focused governed regression bundle: `100 passed`

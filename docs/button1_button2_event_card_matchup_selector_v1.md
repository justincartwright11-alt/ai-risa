# button1-button2-event-card-matchup-selector-v1

## Scope
- Added an Event Cards / Matchup Selector surface between Button 1 and Button 2.
- Kept three main dashboard buttons unchanged.
- Added explicit operator-only selection preview for Button 1 -> Button 2 handoff.
- Enforced source-backed-only readiness/selectability.

## UI Changes
- File: `operator_dashboard/templates/index.html`
- Added `Source-Backed Event Cards` panel inside Button 1 result area.
- Added event-card metadata display fields:
  - Event Name
  - Promotion
  - Event Date
  - Source URL
  - Source Type
  - Provenance Status
  - Matchup Count
- Added matchup rows with:
  - Fighter A
  - Fighter B
  - Weight class
  - Bout order
  - Source-backed status
  - Button2 readiness status
- Added explicit `Select for PDF` control per matchup.
- Added Button 2 selected-matchup preview panel and next-action message.

## API Changes
- File: `operator_dashboard/app.py`
- Added preview-only route:
  - `POST /api/button1-button2/event-card-matchup/select-preview`
- Returns:
  - `selection_preview`
  - `selected_for_button2`
  - event and matchup fields
  - `report_ready_status`
  - `denial_reasons`
  - `safety_flags`
- Enforced denial reasons:
  - `source_backed_matchup_required`
  - `provenance_missing`
  - `missing_event_card`
  - `missing_matchup`
  - `unsupported_selection`
  - `operator_selection_required`

## Governance Guards
- No auto-generate PDFs.
- No queue save writes.
- No delivery/email/API sends.
- No learning/calibration writes.
- No Button 3 mutation behavior.

## Test Coverage
- File: `operator_dashboard/test_button1_button2_event_card_matchup_selector_v1.py`
- Covers:
  - Selector panel rendering and three-button preservation
  - Endpoint wiring in template
  - Source-backed selection success
  - Denial paths for all required denial reasons
  - Safety flags all false
  - Button 2 and Button 3 surfaces untouched

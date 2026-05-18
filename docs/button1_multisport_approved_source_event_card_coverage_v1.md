# button1-multisport-approved-source-event-card-coverage-v1

## Scope
- Added coverage-focused tests for multisport event-card source governance.
- Included a quick registry audit to verify UFC and UFC Stats remain MMA-classified.
- Kept this slice preview-only and side-effect free.
- Did not change queue-save behavior, delivery, learning, calibration, or UI.

## Coverage Goals
- Confirm event-card coverage approval for core Tier A sports (MMA, boxing, kickboxing).
- Confirm multi-sport Tier A source compatibility for MMA/kickboxing/muay_thai discovery coverage.
- Confirm Tier C coverage approval still requires secondary confirmation and blocks queue-save eligibility.
- Confirm Tier D alert-only source remains ineligible for event-card coverage and queue-save.

## Registry Audit Included
- UFC official event pages classify as `sport=mma`, `modality=mma`.
- UFC Stats classify as `sport=mma`, `modality=mma`.
- Explicit anti-regression assertion: UFC entries must not classify as boxing.

## Files Changed
- `operator_dashboard/test_button1_multisport_approved_source_event_card_coverage_v1.py`
- `docs/button1_multisport_approved_source_event_card_coverage_v1.md`
- `ops/release_checks/button1_multisport_approved_source_event_card_coverage_v1/source_event_card_coverage_summary.json`

## Validation Plan
- Run the new event-card coverage test file.
- Run the existing multisport registry test file to confirm no regressions.

## Note
- Prior documentation typo corrected: UFC/UFC Stats removed from the boxing list in the previous registry doc.

# button1-multisport-approved-source-event-card-fixtures-v1

## Scope
- Added one governed URL-backed event-card fixture each for Boxing, MMA, Kickboxing, and Muay Thai.
- Added preview-only Button 1 preparation helper for those fixtures.
- Added proof tests that each fixture classifies correctly and remains operator-gated.
- Kept this slice side-effect free and preview-only.

## Fixture Set
- Boxing fixture: Matchroom URL (Tier A)
- MMA fixture: UFC URL (Tier A)
- Kickboxing fixture: GLORY URL (Tier A)
- Muay Thai fixture: Muay Thai Records URL (Tier B, secondary confirmation required)

## Preparation Contract (Button 1)
- Every prepared row is URL-backed and source-backed.
- Every prepared row is `preview_only=true` and `approval_required=true`.
- Tier A prepared rows can be queue-save eligible but remain operator-gated.
- Muay Thai fixture remains `needs_review` with unsafe queue-save blocked until secondary confirmation.

## Proof Coverage
- One fixture per target sport exists and uses governed HTTPS URLs.
- Fixture preparation preserves provenance and sport mapping.
- Expected tier classification holds for all four fixtures.
- Muay Thai fixture remains non-eligible for queue-save without additional confirmation.
- Gate 1 dry-run preview confirms no writes, no mutation, and no auto-queue-save side effects.

## Files Changed
- `operator_dashboard/button1_multisport_approved_source_event_card_fixtures_v1.py`
- `operator_dashboard/test_button1_multisport_approved_source_event_card_fixtures_v1.py`
- `docs/button1_multisport_approved_source_event_card_fixtures_v1.md`
- `ops/release_checks/button1_multisport_approved_source_event_card_fixtures_v1/source_event_card_fixtures_summary.json`

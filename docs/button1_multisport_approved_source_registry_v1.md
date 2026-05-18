# button1-multisport-approved-source-registry-v1

## Scope
- Added a governed approved combat-sport source registry for Button 1 discovery.
- Kept source policy logic preview-only and side-effect free.
- Did not change dashboard UI, backend routes, PDF rendering, queue writes, delivery, or learning/calibration.

## Source Tiers Added
- Tier A: official / primary sources.
- Tier B: structured records / ranking databases.
- Tier C: card calendars / media calendars.
- Tier D: speed / alert sources only.

## Sources Included by Sport
### Boxing
- UFC official / UFC Stats (structured verification support)
- Matchroom official event pages
- Queensberry official event pages
- Top Rank official event pages
- No Limit Boxing official event pages
- BoxRec
- BoxingScene
- Bad Left Hook

### MMA
- UFC official event pages
- UFC Stats
- ONE Championship official
- Fight Matrix
- Tapology
- Sherdog

### Kickboxing
- GLORY official event pages
- Combat Press

### Muay Thai
- Muay Thai Records
- AusMuayThai
- Muaythai Victoria

### Multi-sport alert
- ONE Championship official
- Flashscore
- Venum News

## Governance Rules
- Tier A can validate event-card provenance directly.
- Tier B can support records, stats, or structured verification.
- Tier C can support discovery but may require Tier A or Tier B confirmation before queue-save.
- Tier D can alert only and must not be enough by itself for queue-save.
- No source with missing URL can pass provenance.
- No social-only source can pass unless explicitly approved in a future slice.
- Every event card must carry URL-backed provenance.
- Every matchup must inherit event-level provenance or carry matchup-level provenance.
- If a source requires secondary confirmation, Button 1 must mark the row needs_review, not ready_to_save.

## Files Changed
- `operator_dashboard/approved_combat_sport_source_registry.py`
- `operator_dashboard/test_button1_multisport_approved_source_registry_v1.py`

## Validation
- New registry tests cover Tier A/B/C/D classification, sport coverage, missing/unknown URL rejection, and governance flags.

## Next Safe Slice
- `button1-multisport-approved-source-event-card-coverage-v1`

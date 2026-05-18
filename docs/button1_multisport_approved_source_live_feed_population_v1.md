# button1-multisport-approved-source-live-feed-population-v1

## Scope
- Populate the governed Button 1 approved-source live feed with URL-backed multisport event cards.
- Prove runtime/dashboard visibility for Boxing, MMA, Kickboxing, and Muay Thai.
- Preserve strict preview-only and operator-gated governance.

## Files Updated
- `ops/approved_sources/button1_live_event_source_rows.json`
- `ops/approved_sources/button1_live_event_ingestion_config.json`
- `operator_dashboard/test_button1_multisport_approved_source_live_feed_population_v1.py`

## Files Added
- `docs/button1_multisport_approved_source_live_feed_population_v1.md`
- `ops/release_checks/button1_multisport_approved_source_live_feed_population_v1/live_feed_population_summary.json`

## Live Feed Population Result
Approved-source feed now contains four URL-backed event cards with explicit multisport coverage.

### 1) Boxing Event Card
- Event: `Joshua vs Dubois`
- Promotion: `Matchroom Boxing`
- Sport/Modality: `boxing / boxing`
- Source URL: `https://www.matchroomboxing.com/events/joshua-vs-dubois`
- Source tier: `A`
- Matchup count: `1`
- Provenance status: `source_backed_ready`

### 2) MMA Event Card
- Event: `UFC 300`
- Promotion: `UFC`
- Sport/Modality: `mma / mma`
- Source URL: `https://www.ufc.com/event/ufc-300`
- Source tier: `A`
- Matchup count: `1`
- Provenance status: `source_backed_ready`

### 3) Kickboxing Event Card
- Event: `GLORY 100`
- Promotion: `GLORY`
- Sport/Modality: `kickboxing / kickboxing`
- Source URL: `https://www.glorykickboxing.com/events/glory-100`
- Source tier: `A`
- Matchup count: `1`
- Provenance status: `source_backed_ready`

### 4) Muay Thai Event Card
- Event: `ONE SAMURAI 1`
- Promotion: `ONE Championship`
- Sport/Modality: `muay_thai / muay_thai`
- Source URL: `https://www.muaythairecords.com/events/one-samurai-1`
- Source tier: `B`
- Matchup count: `2`
- Provenance status: `needs_review`
- Secondary confirmation required: `true`

## Runtime Validation Evidence
Runtime probe values:
- `approved_source_event_rows_count`: `4`
- `diagnostics`: `[]`
- Sports present in approved-source rows: `boxing`, `mma`, `kickboxing`, `muay_thai`

Dashboard/runtime visibility proof:
- Dashboard root exposes `Source-Backed Event Cards` panel.
- Runtime workflow preview includes source-backed candidate rows for all four sports.
- Candidate rows include fighter pairs for all four event cards, allowing event-card panel rendering.

## Gate 1 Dry-Run Evidence (Preview-Only)
Tested approved rows plus one non-source control row.

Observed:
- `would_save_count`: `4`
- `blocked_count`: `1`
- blocked candidate: `non_source_control_001`
- `preview_only`: `true`
- `write_authorized`: `false`
- `queue_write_performed`: `false`
- `database_write_performed`: `false`
- `mutation_performed`: `false`

Interpretation:
- Source-backed URL rows remain eligible in preview dry-run.
- Non-source row remains blocked (fail-closed).

## Governance Confirmation
- No Gate 1 weakening.
- No auto-save queue writes.
- No PDF generation.
- No delivery.
- No learning/calibration writes.
- No Button 3 mutation.
- Operator approval preserved.
- Muay Thai structured row remains `needs_review` with secondary confirmation required.

## Test Results
- `operator_dashboard/test_button1_multisport_approved_source_live_feed_population_v1.py`: `18 passed`
- `operator_dashboard/test_button1_multisport_approved_source_event_card_dashboard_runtime_confirmation_v1.py`: `5 passed`

## Verdict
Slice passed: Button 1 live approved-source feed now surfaces one URL-backed event card per target sport with preserved governance and preview-only behavior.

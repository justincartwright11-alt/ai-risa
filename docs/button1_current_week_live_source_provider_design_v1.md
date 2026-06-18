# Button 1 Current-Week Live Source Provider Design v1

## Slice
button1-current-week-live-source-provider-design-v1

## Goal
Design the production-ready live provider path so Button 1 can move from stale-feed fail-closed mode to real approved-source current-week/upcoming discovery, while preserving operator-approval governance and existing safety rails.

## Scope
- In scope: Button 1 live source discovery provider design, contracts, validation, fail-closed behavior, observability, rollout, and proof plan.
- Out of scope: Button 2 rendering/generation, Button 3 result/learning/calibration, queue auto-save, customer delivery, or any approval bypass.

## Current Baseline
- Runtime loader already enforces fail-closed status states and emits `live_source_status` in workflow payload.
- UI now binds and displays:
  - Last Source Refresh
  - Discovery Window
  - Feed Status
  - Source Freshness
  - Live Discovery Result
  - Current-Week Ready
  - Save Allowed
- Current live feed source is file-based and currently stale, resulting in:
  - `feed_status=stale`
  - `current_week_ready=false`
  - `save_allowed=false`

## Design Principles
1. Approved-source only: ingest only from governed provider allowlist and approved URL patterns.
2. Fail closed by default: any provider fault/freshness/schema issue yields non-ready status and no save eligibility.
3. Read-only discovery first: provider refresh and ingestion do not auto-save queue rows.
4. Operator gate intact: queue writes still require explicit Gate 1 approval.
5. Explainable status: every non-ready state must emit deterministic diagnostics.

## Target Architecture

### 1) Provider Orchestrator (Button 1)
Introduce a provider orchestrator service (design target module):
- `operator_dashboard/button1_live_source_provider_orchestrator_v1.py`

Responsibilities:
- Resolve configured providers from governed config.
- Execute provider collectors with bounded timeouts and retries.
- Normalize provider events into canonical source-backed event-card rows.
- Persist a refreshed governed feed artifact for runtime loader consumption.
- Emit refresh metadata and diagnostics.

### 2) Provider Adapters
Design adapter interface (read-only collection):
- `collect_current_week_upcoming(provider_config, now_utc) -> ProviderCollectResult`

Expected adapter targets:
- UFC official event pages
- Matchroom official boxing events
- GLORY official event pages
- Optional tier-B corroborators only where explicitly approved by config and governance policy

Adapter constraints:
- No queue/database writes.
- No auto-promotion to Button 2.
- Strict source URL provenance capture for each event and matchup.

### 3) Canonical Feed Artifact
Design refresh output artifact:
- `ops/approved_sources/button1_live_event_source_rows.json`

Proposed top-level structure:
- `generated_at_utc`
- `provider_run_id`
- `provider_results[]`
- `rows[]` (canonical event-card rows)
- `diagnostics[]`
- `schema_version`

Each canonical row includes:
- event metadata: `event_name`, `event_date`, `promotion`, `sport`, `modality`
- provenance: `source_url`, `canonical_source_url`, `source_urls[]`, `source_name`, `source_type`, `source_tier`
- card quality: `matchups[]`, `matchup_count`, completeness fields
- governance hints: `approval_required`, `preview_only`, `provenance_status`

### 4) Runtime Loader Integration
Existing loader remains source of truth for preview payload binding.
Design extension:
- Loader reads refreshed canonical artifact + freshness metadata.
- Loader maps provider refresh metadata into `live_source_status`.
- Loader keeps existing fail-closed statuses and adds provider-run diagnostics where relevant.

No change to:
- Gate 1 write authorization flow.
- queue save write paths.
- Button 2/3 routes.

## Required Runtime Contract (Live Source Status)
`workflow.jobs[0].input_ref.metadata.payload.live_source_status` must include:
- `feed_status`
- `generated_at_utc`
- `current_week_start`
- `current_week_end`
- `upcoming_window_days`
- `source_freshness`
- `feed_age_seconds`
- `current_week_ready`
- `save_allowed`
- `fallback_used`
- `diagnostics`
- `feed_used`
- `approved_source_event_rows_count`
- `current_week_rows_count`
- `source_backed_event_cards`

## Status Semantics

### unavailable
- Trigger: provider artifact missing or refresh runner unreachable.
- Required flags: `current_week_ready=false`, `save_allowed=false`, `fallback_used=true`.

### stale
- Trigger: artifact age exceeds freshness SLA.
- Required flags: `current_week_ready=false`, `save_allowed=false`.

### demo_or_fixture_feed
- Trigger: fixture/demo markers or invalid temporal profile.
- Required flags: `current_week_ready=false`, `save_allowed=false`.

### no_current_week_source_backed_matchups
- Trigger: valid artifact but no source-backed rows in current-week+upcoming window.
- Required flags: `current_week_ready=false`, `save_allowed=false`.

### current_week_ready
- Trigger: source-backed rows in current-week/upcoming window present and fresh.
- Required flags: `current_week_ready=true`, `save_allowed=true` (preview eligibility only).

## Freshness and Window Policy
- Freshness SLA default: 24 hours.
- Window policy:
  - `current_week_start`: Monday of current week.
  - `current_week_end`: Sunday + upcoming extension endpoint display uses current implementation convention.
  - `upcoming_window_days`: 14 (configurable future extension).

## Governance and Safety
- No auto-save fights.
- No queue write on provider refresh.
- No profile/learning/calibration writes.
- All permanent action candidates remain gate-protected.
- Any provider contract violation -> fail-closed.

## Observability and Proof
Design telemetry fields for provider runs:
- run id, provider name, duration, status, error class, rows accepted/rejected, stale reason.

Required proof artifacts for implementation slice:
- refreshed workflow preview JSON with `feed_status` non-unknown and full contract
- UI proof screenshot showing all bound status lines
- diagnostics summary JSON for provider run

## Rollout Plan
1. Design lock (this slice).
2. Provider orchestrator scaffold with mock adapters and governed config wiring.
3. One production provider implementation (UFC official) + canonical normalization.
4. Multi-provider fan-in + dedupe + quality scoring.
5. Runtime smoke and UI proof showing transition from stale fail-closed to current-week-ready (when live data available).

## Test Strategy (for upcoming implementation slice)
- Unit:
  - provider adapter contract validation
  - canonical normalization
  - freshness and status mapping
- Integration:
  - orchestrator -> artifact -> loader -> workflow preview contract
- UI smoke:
  - Find Fights panel status lines match payload for each feed status
- Governance:
  - Gate required and write flags remain false in preview paths

## Explicit Non-Goals
- No modification of Button 2 report generation/rendering.
- No modification of Button 3 result/learning apply flows.
- No bypass of operator approval.

## Open Decisions
1. Provider scheduling model:
- On-demand refresh from UI only, scheduled pre-refresh, or hybrid.
2. Tier-B corroborator policy:
- Include now vs defer until Tier-A is stable.
3. Freshness SLA override:
- Keep global 24h or provider-specific thresholds.

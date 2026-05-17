# Global Fighter Known Records Source Pack Design v1

## Slice
- Name: global-fighter-known-records-source-pack-design-v1
- Type: docs-only
- Status: design lock candidate

## Purpose
Design where safe known fighter records come from before implementation.

This slice defines allowed read/sanitize sources for Button 1 identity resolver preview workflows.

## Hard Rule (Locked)
- Known records may be read and sanitized for identity preview.
- Known records may not create, update, merge, rank, or write fighter profiles.

## Governance and Safety Boundaries
- Preview-only behavior is mandatory.
- No profile create flow.
- No profile update flow.
- No merge flow.
- No ranking write flow.
- No database write flow.
- No learning/calibration write flow.
- Normal dashboard remains 3 buttons and 3 gates.

## Source Pack Overview
The source pack is a read-only aggregator that normalizes known records into one safe resolver-compatible shape.

Defined source classes:
1. Local seed known-record packs
2. Approved historical fighter records
3. Report-history fighter references
4. Result-ledger projections
5. Future global fighter database read-only projection
6. Manual operator-supplied known records

## Source Class Definitions

### 1. Local Seed Known-Record Packs
Purpose:
- Deterministic baseline source for preview mode.
- Stable fallback for smoke tests and offline runs.

Constraints:
- Local file inputs only.
- Treated as read-only reference data.
- Unsafe/internal fields dropped at sanitize step.

### 2. Approved Historical Fighter Records
Purpose:
- Read-only projection of records previously approved in trusted workflows.
- Improves identity confidence with durable known fighter attributes.

Constraints:
- Must come from approved, immutable snapshot or equivalent read-only export.
- Projection can include only comparison-safe fields.
- No writeback channel to original source.

### 3. Report-History Fighter References
Purpose:
- Reuse historical report fighter references as weak corroboration signals.
- Improve alias and identity continuity in preview matching.

Constraints:
- Read-only projection only (no report mutation).
- Fields limited to identity-safe references.
- Any missing core identity fields fail closed.

### 4. Result-Ledger Projections
Purpose:
- Reuse result-ledger fighter references as additional identity evidence.
- Improve match confidence in preview where source quality is sufficient.

Constraints:
- Projection-only read path.
- No mutation of ledger records.
- No coupling to calibration writes in this path.

### 5. Future Global Fighter Database Read-Only Projection
Purpose:
- Future source for high-quality canonical identity references.
- Read-only fetch of comparison-safe fields only.

Constraints:
- Strict projection contract (no internal storage pointers, no write controls).
- Optional source enabled by policy/config.
- Failure must degrade safely to other sources or empty context.

### 6. Manual Operator-Supplied Known Records
Purpose:
- Allow operator to provide temporary known records for preview matching.
- Support controlled investigative workflows without DB mutation.

Constraints:
- Scope-limited to preview request/session.
- Must pass full sanitize/validate pipeline.
- Never interpreted as save authorization.

## Source Precedence and Merge Policy
Precedence (highest to lowest):
1. Manual operator-supplied known records
2. Local seed known-record packs
3. Approved historical fighter records
4. Report-history fighter references
5. Result-ledger projections
6. Future global fighter database read-only projection

Merge behavior:
- Aggregate all available sanitized records.
- Deduplicate by fighter_global_id first, normalized full_name second.
- Prefer highest-precedence non-null field values per attribute.
- Preserve per-field provenance metadata.

Safety behavior:
- If a source fails, continue with remaining sources.
- If all sources fail or are absent, return empty safe context.
- Never emit raw source objects.

## Sanitization and Validation Contract
Required fields per accepted record:
- fighter_global_id
- full_name

Safe optional fields:
- known_aliases
- nationality
- promotion
- sport_ruleset
- division
- date_of_birth
- height
- reach
- stance
- record
- active_years
- confidence_grade
- completeness_flags

Required transforms:
- known_aliases coerced to list of strings.
- confidence_grade normalized to A/B/C/D/F, default C.
- unknown fields dropped.
- write-intent or internal-control fields dropped.

Fail-closed rules:
- Missing fighter_global_id or full_name -> reject record.
- Malformed non-dict record -> reject record.
- Source-level exception -> source contributes zero records + error telemetry.

## Required Provenance Model
Each accepted record should carry safe provenance fields:
- loader_source_type
- loader_source_name
- loader_snapshot_ts (optional)
- loader_record_origin_id (optional safe reference)

Provenance constraints:
- Provenance informs confidence shaping only.
- Provenance cannot authorize writes.
- Missing provenance should reduce trust but not enable mutation.

## Resolver Compatibility Contract
Source-pack output must remain resolver-preview compatible.

Target envelope:
- preview_only: true
- known_records: [sanitized dict]
- records_received_count
- records_accepted_count
- malformed_records_count
- source_type: source_pack
- errors: []
- profile_create_performed: false
- profile_update_performed: false
- merge_performed: false
- database_write_performed: false
- ranking_write_performed: false
- learning_apply_performed: false
- calibration_write_performed: false

## Normal Dashboard Exposure Rules
Allowed:
- known record counts
- source summary labels
- confidence labels
- manual review requirements

Not allowed:
- raw source payloads
- hidden internal IDs beyond safe preview IDs
- profile create/update/merge controls
- ranking/database write controls

## Explicit Non-Goals
This docs-only slice does not include:
- implementation code
- route additions
- resolver algorithm changes
- schema migrations
- profile write behavior
- ranking/database/learning writes
- dashboard button/gate redesign

## Implementation Readiness Criteria (for next slice)
Before locking global-fighter-known-records-source-pack-preview-v1, tests must prove:
1. All six source classes accepted through sanitize/validate gate.
2. Strict source precedence applied deterministically.
3. Dedupe and merge preserve safe fields + provenance.
4. Malformed records rejected fail closed.
5. Non-list/non-dict inputs handled safely.
6. Resolver-compatible output envelope preserved.
7. Internal/write fields excluded in all outputs.
8. All write flags remain false.
9. No filesystem writes outside approved read-only source paths.
10. No live web calls.
11. Normal dashboard remains 3 buttons and 3 gates.
12. No create/update/merge/ranking/database controls exposed.

## Final Verdict
The known-records source pack is approved as a read-only, sanitize-first, preview-only design.

It may improve identity preview quality by aggregating safe known records from defined sources.

It may not create, update, merge, rank, or write fighter profiles under any condition in this slice.

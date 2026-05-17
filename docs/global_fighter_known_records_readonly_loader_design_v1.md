# Global Fighter Known Records Readonly Loader Design v1

## Slice
- Name: global-fighter-known-records-readonly-loader-design-v1
- Type: docs-only
- Status: design lock candidate

## Purpose
Design how AI-RISA reads known fighter records safely for identity resolver comparison in preview-only workflows.

This design covers read paths only.

## Core Rule
- Known fighter records may be read for preview matching.
- Known fighter records may not be written, merged, ranked, or updated.

## Governance and Safety Boundaries
- Preview-only behavior remains mandatory.
- No profile create flow.
- No profile update flow.
- No merge flow.
- No ranking writes.
- No database writes.
- No queue/result/learning/calibration mutation behavior.
- Normal dashboard remains 3 buttons and 3 gates.

## Current Locked Foundation
This design assumes locked prior slices:
- Button 1 candidate context preview foundation.
- Row-level identity evidence + Gate 1 blocker alignment.
- Known-records context preview builder and wire integration.
- Known-records wire smoke proof.

No implementation behavior is opened by this design document.

## 1. Read-Only Known Fighter Source Model
Known records loader should support a read-only layered source model:
1. Safe local seed records (immediate, deterministic fallback).
2. Future global fighter database read path (read-only projection).
3. Optional in-memory override for test/preview harnesses.

Precedence model (preview read only):
- If explicit in-memory records are provided, use them first.
- Else use local seed records if available.
- Else use global read projection when enabled and healthy.
- If all unavailable, return empty safe context.

## 2. Safe Local Seed Records
Local seeds are intended for deterministic preview behavior and smoke stability.

Seed constraints:
- File must be local and read-only by contract.
- Seeds include only safe comparison fields.
- Seeds never include write directives or hidden mutation flags.
- Seed loading failures must fail closed to empty context.

Seed schema target:
- fighter_global_id
- full_name
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

## 3. Future Global Fighter Database Read Path
Future global source should be read projection only:
- Query returns comparison-safe fields only.
- Query excludes internal storage pointers and write controls.
- Query includes provenance metadata suitable for audit.
- Query is optional and can be disabled by policy/config.

Read-path guardrails:
- Never return SQL/raw driver/internal objects into dashboard context.
- Never expose write authorization or write capability in read loader output.
- Any malformed row from source is skipped (fail closed per record).

## 4. Source Provenance Requirements
Every known record fed to resolver preview should carry source provenance metadata in loader telemetry:
- loader_source_type: seed | global_read | in_memory
- loader_source_name
- loader_snapshot_ts (optional)
- loader_record_origin_id (safe preview identifier)

Provenance policy:
- Missing provenance for a record marks it reduced-trust for confidence shaping.
- Missing provenance must not trigger writes or merges.
- Loader-level provenance failures should produce empty safe context rather than partial unsafe output.

## 5. Confidence and Data Completeness Fields
Loader should standardize confidence/completeness hints for resolver usage:
- confidence_grade (A/B/C/D/F)
- completeness_flags:
  - has_identity_core
  - has_aliases
  - has_birthdate
  - has_nationality
  - has_division

Resolver usage intent:
- These hints may influence preview confidence ranking.
- These hints may not authorize profile actions.

## 6. Resolver-Compatible Output Shape
Readonly loader output must be directly compatible with resolver preview known_records shape.

Target output envelope:
- ok: bool
- preview_only: true
- known_records: [sanitized KnownFighterRecord-like dict]
- records_received_count
- records_accepted_count
- malformed_records_count
- errors: []
- profile_create_performed: false
- profile_update_performed: false
- merge_performed: false
- database_write_performed: false
- ranking_write_performed: false
- learning_apply_performed: false
- calibration_write_performed: false

## 7. Fail-Closed Behavior for Malformed Records
Per-record fail-closed rules:
- Missing fighter_global_id or full_name -> reject record.
- Non-list aliases -> coerce to empty list.
- Invalid active_years format -> set null.
- Invalid confidence_grade -> default to C.
- Unknown/internal fields -> drop.

Batch fail-closed rules:
- Non-list input -> return empty safe context + error.
- Source read exceptions -> return empty safe context + error.
- Mixed records -> keep only valid sanitized rows.

## 8. Normal Dashboard Exposure Rules
Normal dashboard may display:
- Known records compared count.
- Match confidence label.
- Manual review required.
- Canonical blocked reason labels.

Normal dashboard must not display:
- raw known-record payloads.
- raw resolver internals.
- hidden internal IDs beyond safe preview IDs.
- create/update/merge/ranking/database controls.

## 9. Explicit Non-Goals
This slice does not include:
- loader implementation code.
- new routes.
- resolver engine changes.
- profile creation/update/merge behavior.
- ranking/database writers.
- advanced dashboard redesign.
- new main buttons.
- new gates.

## 10. Future Tests Required Before Implementation Lock
Before implementation lock for readonly loader preview:
1. Safe seed records load as read-only sanitized context.
2. Global read projection path returns only safe fields.
3. Malformed records are rejected fail closed.
4. Non-list inputs return empty safe context.
5. Resolver-compatible output shape is preserved.
6. Raw/internal fields are excluded.
7. No filesystem writes beyond read-only loader access policy.
8. No live web calls.
9. All write flags remain false.
10. Button 1 preview remains summary-only in normal dashboard.
11. No create/update/merge/ranking/database controls appear.
12. Normal dashboard remains 3 buttons and 3 gates.

## Final Verdict
AI-RISA may read known fighter records through a readonly loader to improve preview identity comparison quality.

AI-RISA may not write, merge, rank, create, or update fighter profiles through this loader path.

This slice is docs-only and preserves all zero-mutation safeguards.

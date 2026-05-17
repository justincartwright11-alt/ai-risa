# global-fighter-record-readonly-projection-ledger-design-v1

## 1) Purpose
The Global Fighter Record Read-Only Projection Ledger is a preview-only projection layer for known fighter records.
It feeds identity resolver preview and known-records source packs.
It does not mutate fighter records and does not open any permanent write behavior.

## 2) Current Locked Foundation
This design builds on the currently locked read-only and preview-only foundation:
- Global fighter database schema design: docs/global_fighter_database_master_schema_design_v1.md
- Global fighter identity resolver design: docs/global_fighter_identity_resolver_design_v1.md
- Identity resolver preview scaffold: operator_dashboard/test_global_fighter_identity_resolver_preview_scaffold_v1.py
- Identity resolver preview API route (preview-only): operator_dashboard/app.py (/api/global-fighters/identity-resolver/preview)
- Button 1 candidate context hook: operator_dashboard/button1_candidate_context_hook.py
- Known-records context builder/wire surfaces in Button 1 preview flow: operator_dashboard/templates/index.html
- Readonly known-records loader: operator_dashboard/global_fighter_known_records_readonly_loader.py
- Source-pack builder: operator_dashboard/global_fighter_known_records_source_pack_preview.py
- Source-pack API preview route: operator_dashboard/app.py (/api/global-fighters/known-records/loader-preview)
- Button 1 advanced source-pack wire smoke lock: global-fighter-known-records-button1-advanced-source-pack-wire-smoke-v1 (commit 318018a)

## 3) Projection Source Classes
Projection classes (all preview-only, read-only):
1. Approved fighter record projection
2. Report-history fighter reference projection
3. Result-ledger fighter projection
4. Future global fighter database read-only projection
5. Manual operator known-record projection
6. Local seed projection

## 4) Resolver-Compatible Output Shape
Projection output must contain resolver-compatible safe fields only:
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
- completeness_flags
- source_refs
- projection_source_type
- projection_source_name
- projection_generated_at_preview

Notes:
- source_refs is required provenance evidence for comparison-grade matching.
- projection_source_type and projection_source_name must be populated for every projected row.
- projection_generated_at_preview is read-only preview metadata.

## 5) Excluded Fields
The projection ledger must exclude all unsafe/internal/write-oriented fields, including:
- database write pointers
- merge instructions
- ranking write instructions
- internal primary keys not safe for display
- private operator notes
- raw ledger internals
- unverified source payloads
- write_authorized
- any mutation flag set true

## 6) Projection Governance
Governance rules for this ledger:
- Projection may read approved/safe records.
- Projection may not create/update/merge profiles.
- Projection may not update rankings.
- Projection may not write ledgers.
- Projection may not trigger learning/calibration.
- Projection may not expose raw internals to the normal dashboard.

## 7) Provenance Requirements
Every projected known_record must satisfy provenance rules:
- source_refs required
- source_type required
- source_confidence optional
- projection confidence required
- data completeness required
- missing provenance becomes a manual-review/blocking reason

Operational interpretation:
- If source_refs is absent or empty, the row is not eligible for clear identity resolution and must be blocked/escalated.
- If source_type is absent, projection is malformed and fails closed.

## 8) Confidence and Completeness Model
Standard projection state model:
- high confidence: strong identity evidence and complete core fields
- medium confidence: acceptable evidence, minor optional gaps
- low confidence: weak evidence, higher ambiguity risk
- incomplete: required identity/provenance/completeness data missing
- conflict: contradictory identity signals across sources
- source_missing: provenance is missing or unverifiable

## 9) Dedupe and Precedence
Deterministic precedence order (highest to lowest):
1. manual operator verified known records
2. approved fighter records
3. result-ledger fighter projections
4. report-history fighter references
5. local seed known records
6. future global read-only projection

Dedupe rules:
- Primary key: fighter_global_id
- Secondary key: normalized full_name
- Merge behavior is field-fill only from lower precedence for missing optional fields.
- No profile merge action is performed; this is projection-time normalization only.

## 10) Fail-Closed Behavior
Fail-closed rules:
- malformed projection skipped
- missing name skipped
- missing provenance blocked
- conflicting identity escalates manual review
- same-name ambiguity blocks permanent actions
- no fallback to fake fighter record

## 11) Normal Dashboard Exposure
Allowed summary-only normal dashboard exposure:
- known records loaded
- known records compared
- source type
- confidence summary
- manual review count
- conflict count
- profile write disabled
- merge disabled
- database write disabled

Forbidden normal dashboard exposure:
- raw projection payloads
- raw ledger internals
- create profile control
- update profile control
- merge control
- database write control
- ranking write control

## 12) Relationship to Gate 1
Gate 1 alignment requirements:
- Identity blockers from projections should feed Gate 1 dry-run.
- conflict/source-missing/ambiguous projections block would_save.
- profile writes remain disabled.
- merge remains disabled.
- database writes remain disabled.

## 13) Future Implementation Tests
Required tests before any preview implementation lock:
- approved fighter projection normalizes
- result-ledger projection normalizes
- report-history projection normalizes
- local seed projection normalizes
- global read-only projection normalizes
- malformed records skipped
- raw internals excluded
- all write flags false
- no filesystem writes
- no live web calls
- normal dashboard remains 3 buttons / 3 gates

## 14) Non-Goals
Explicit non-goals for this slice:
- real global fighter database
- profile writer
- merge writer
- ranking writer
- public fighter profile UI
- automatic learning
- calibration writes
- new main dashboard buttons
- new gates

## 15) Final Verdict
The projection ledger may supply clean read-only fighter references for identity preview, but all permanent fighter database actions remain sealed behind future approval-gated writers.

## Governance Lock Statement
This is a docs-only design lock.
No code changes, route changes, dashboard changes, database files, or writer behavior are introduced by this slice.
Preview-only behavior and normal 3-button / 3-gate governance remain intact.

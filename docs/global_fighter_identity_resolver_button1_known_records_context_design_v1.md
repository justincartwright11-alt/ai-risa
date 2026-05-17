# Global Fighter Identity Resolver Button 1 Known Records Context Design v1

## Slice
- Name: global-fighter-identity-resolver-button1-known-records-context-design-v1
- Type: docs-only
- Status: design

## Purpose
Define how Button 1 should supply known fighter records into the identity resolver preview flow so candidate fighters can be compared safely against known records.

This design is comparison-only.

## Core rule
- Button 1 may compare candidate fighters against known records.
- Button 1 may not create, update, merge, rank, or write fighter profiles.

## Governance constraints
- Preview-only behavior remains required.
- No profile creation.
- No profile update.
- No merge behavior.
- No ranking writes.
- No database writes.
- No queue/result/learning/calibration mutation behavior.
- Normal dashboard remains 3 buttons and 3 gates.

## Current locked foundation
This design builds on locked preview-only slices:
- Button 1 candidate context hook and smoke.
- Row-level identity evidence preview.
- Gate 1 identity blocker alignment.
- Canonical reason rendering.
- Preview smoke evidence lock.

No implementation behavior is opened by this document.

## Known records context goal
Button 1 identity preview should be able to evaluate each incoming fighter candidate against an optional known-records context bundle.

Expected benefits:
- Better preview match confidence explanation.
- Fewer ambiguous/no-match outcomes when known records are available.
- Cleaner manual-review routing for low-confidence conflicts.

## Proposed preview-only context contract
Button 1 should supply two preview inputs to the resolver layer:
- candidates: derived from Button 1 candidate rows.
- known_records_context_preview: a safe, read-only list of known fighter records.

Suggested payload shape (preview-only contract target):
- source: button1_discovery
- preview_only: true
- candidates: []
- known_records_context_preview: []
- known_records_context_version: optional string
- known_records_context_source: optional label (for operator transparency)

## Known record preview fields
Each known record preview item should include only comparison-safe fields:
- fighter_global_id_preview
- full_name
- known_aliases
- nationality
- promotion
- sport_ruleset
- division
- date_of_birth
- stance
- confidence_grade

Optional, still preview-safe:
- height
- reach
- active_years

Fields intentionally excluded from dashboard display surfaces:
- private/internal indexing fields
- raw storage pointers
- write authorization metadata
- merge directives

## Button 1 to resolver preview flow
1. Button 1 extracts candidate fighters from candidate rows.
2. Button 1 obtains a known-records context preview bundle (read-only).
3. Button 1 posts candidate + known-records context into resolver preview.
4. Resolver returns row-level identity evidence and blocker reasons.
5. Gate 1 dry-run preview uses those blocker signals for would_save vs blocked projection.

## Resolver interaction rules
When known records are present:
- Resolver preview may compare names, aliases, nationality, division, sport ruleset, date_of_birth, and other safe comparison fields.
- Resolver preview may adjust confidence tier and manual-review recommendations.
- Resolver preview must keep all write flags false.

When known records are absent:
- Resolver preview must fail safe to no-match/manual-review behavior where appropriate.
- No synthetic write behavior may be introduced.

## Safety telemetry requirements
All known-records-assisted preview responses must include:
- preview_only=true
- profile_create_performed=false
- profile_update_performed=false
- merge_performed=false
- database_write_performed=false
- ranking_write_performed=false
- learning_apply_performed=false
- calibration_write_performed=false

## Operator UX requirements
Normal dashboard may show:
- Known records compared: count
- Match confidence label
- Manual review required
- Blocked reason labels (canonicalized)
- Profile write disabled
- Merge disabled
- Database write disabled

Normal dashboard must not show:
- raw known-record payload dumps
- raw resolver internals
- hidden internal IDs beyond safe preview ID
- create/update/merge/ranking/database controls

## Gate 1 dry-run relationship
Known-records context only influences preview classification quality.

Gate 1 dry-run still enforces:
- identity_conflict blocks would_save
- identity_source_missing blocks would_save
- identity_ambiguous blocks would_save
- write_authorized remains false
- mutation_performed remains false

## Non-goals
This slice explicitly excludes:
- implementing known-records retrieval logic
- adding new routes
- modifying resolver engine behavior
- profile creation/update/merge flows
- ranking/database writers
- advanced dashboard redesign
- new main buttons
- new gates

## Future implementation test requirements
The implementation slice should prove:
- known-records context is accepted in preview payload path
- resolver preview compares against known records without writes
- confidence/manual-review evidence remains safe and deterministic
- canonical blocked reasons remain stable
- no raw internals are exposed
- no create/update/merge/rank/database controls appear
- all write flags remain false
- normal dashboard remains 3 buttons and 3 gates

## Final verdict
Known-records context may be introduced into Button 1 identity resolver preview as a read-only comparison dependency.

All profile/database/merge/ranking actions remain sealed.

This is a docs-only design slice.

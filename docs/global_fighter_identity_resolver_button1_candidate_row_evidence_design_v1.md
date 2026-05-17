# Global Fighter Identity Resolver Button 1 Candidate Row Evidence Design v1

## 1. Purpose
This design defines how Button 1 candidate rows should display identity evidence beside each discovered matchup row in normal dashboard workflow, while keeping all write behavior sealed.

The objective is row-level identity clarity for operator review only:
- Show resolver evidence state for Fighter A and Fighter B per row.
- Show match confidence and manual review requirements per row.
- Improve save-preview safety decisions.
- Keep profile create, profile update, merge, ranking write, and database write disabled.

## 2. Current locked foundation
This design builds on the following locked foundation slices:
- Identity resolver design foundation: global fighter identity resolver preview design slice.
- Preview scaffold: resolver preview scaffold slice.
- Preview API: resolver preview API slice.
- Dashboard evidence wire: resolver preview dashboard wire slice.
- Integration smoke: resolver preview integration smoke slice.
- Button 1 candidate context hook: global-fighter-identity-resolver-button1-candidate-context-hook-v1.
- Button 1 candidate context smoke: global-fighter-identity-resolver-button1-candidate-context-smoke-v1.

No new behavior is opened by this document.

## 3. Candidate row evidence fields
Each Button 1 candidate row should carry row-level identity evidence fields:
- fighter_a_identity_status
- fighter_b_identity_status
- fighter_a_match_confidence
- fighter_b_match_confidence
- fighter_a_manual_review_required
- fighter_b_manual_review_required
- fighter_a_conflict_reasons
- fighter_b_conflict_reasons
- fighter_a_matched_record_id_preview
- fighter_b_matched_record_id_preview
- identity_blocking_reasons
- identity_ready_for_queue_review

Field intent:
- identity status fields: user-facing row state for each fighter.
- match confidence fields: numeric or banded confidence for preview only.
- manual review fields: explicit row-level intervention flags.
- conflict reasons fields: short safe reasons suitable for operator display.
- matched record id preview fields: safe preview identifier only.
- identity_blocking_reasons: consolidated block reasons used by save preview.
- identity_ready_for_queue_review: boolean summary gate for row readiness.

## 4. Display rules
Normal dashboard may show the following labels:
- Identity: Clear
- Identity: Needs Review
- Identity: Conflict
- Identity: No Match
- Identity: Source Missing
- Manual Review Required
- Profile Write Disabled
- Merge Disabled
- Database Write Disabled

Normal dashboard must not show:
- raw resolver payload
- raw candidate internals
- full source trace
- hidden database IDs beyond safe preview ID
- merge controls
- create profile controls
- profile update controls
- ranking write controls
- global database write controls

Display policy:
- Keep per-row evidence compact and human-readable.
- Keep internals and raw debug structures hidden.
- Maintain current normal dashboard shape and flow.

## 5. Candidate row statuses
The row-level status model is:
- identity_clear
- identity_needs_review
- identity_conflict
- identity_no_match
- identity_source_missing
- identity_ambiguous

Status meaning:
- identity_clear: confident non-conflicting preview match for both row fighters.
- identity_needs_review: low confidence or partial evidence requiring operator check.
- identity_conflict: conflicting candidate evidence that blocks row save path.
- identity_no_match: no matching record found in preview; can remain preview-only.
- identity_source_missing: source provenance missing or weak for safe progression.
- identity_ambiguous: multiple plausible matches without clear winner.

## 6. Queue approval impact
Identity evidence influences Button 1 approval preview as follows:
- identity_clear can proceed to queue approval preview.
- identity_needs_review requires operator review before save preview can proceed.
- identity_conflict blocks save.
- identity_source_missing blocks save.
- identity_no_match can proceed only as new fighter candidate preview and cannot create profile.
- identity_ambiguous blocks save until reviewed.

Queue-impact policy is preview-only and does not perform writes.

## 7. Gate 1 relationship
Identity row evidence should feed Gate 1 dry-run and approved-save preview with strict safety:
- identity_blocking_reasons must be included in dry-run preview outputs.
- conflict and manual-review rows must be blocked from would_save outcomes.
- profile writes remain disabled.
- merge remains disabled.
- database writes remain disabled unless a future approved writer is explicitly designed and approved.

This design only specifies evidence flow into existing preview surfaces.

## 8. Source provenance requirements
Source provenance requirements for row evidence:
- identity evidence requires source refs.
- missing source refs must create manual-review or blocking status.
- default Button 1 discovery source refs are preview-only.
- any future permanent profile write path must require stronger provenance than preview defaults.

## 9. Manual review model
Manual review metadata design for each fighter row side:
- manual_review_required
- manual_review_reason
- reviewer_decision_preview
- conflict_resolution_required
- approval_required_before_profile_write

Manual review policy:
- reviewer_decision_preview is preview-only metadata.
- no reviewer action in this slice writes profile or merge changes.
- approval_required_before_profile_write remains true for all non-clear write paths.

## 10. Safety telemetry
Every row-level identity evidence payload must include:
- preview_only=true
- profile_create_performed=false
- profile_update_performed=false
- merge_performed=false
- database_write_performed=false
- ranking_write_performed=false
- learning_apply_performed=false
- calibration_write_performed=false

Telemetry intent:
- make non-mutation guarantees explicit in row evidence outputs.
- preserve audit visibility without exposing internals.

## 11. Future implementation tests
Future implementation slice must add tests proving:
- row evidence renders confidence.
- conflict blocks save preview.
- source missing blocks save preview.
- no raw internals exposed.
- no create and merge controls.
- no database and ranking writes.
- normal dashboard remains 3 buttons and 3 gates.

## 12. Non-goals
This slice explicitly excludes:
- real profile creation
- profile update
- merge writer
- global database writer
- ranking writer
- public fighter profile UI
- advanced dashboard redesign
- new main buttons
- new gates

## 13. Final verdict
The next implementation may display identity evidence per Button 1 candidate row in normal dashboard preview flow.

All profile, database, merge, and ranking actions remain sealed in this design.

This is a docs-only design slice and does not open implementation behavior.

# Button1 Provenance Missing Candidate Review v1

## Slice
button1-provenance-missing-candidate-review-v1

## Scope and Constraints
This slice is diagnostic/evidence-only.
No code changes, no UI changes, no endpoint changes, no forced-save, no provenance bypass, and no gate weakening were performed.

## 1) Summary of 31 candidate rows
Runtime Button 1 preview currently builds `31` candidate rows.
Composition:
- `1` row from `event_coverage_queue.csv` (event-level row)
- `30` rows from `fighter_intake_unresolved_queue.csv` (fighter/opponent intake rows)

Observed Button 1 runtime summary from workflow preview:
- discovered_count: 31
- extracted_count: 31
- ready_for_report_count: 0
- draft_only_count: 31
- blocked_on_missing_fighter_count: 0
- duplicate_or_conflict_count: 0

Observed Gate 1 outcomes on same runtime payload:
- blocked rows: 31
- would-save rows: 0
- writer blocking reason: provenance_missing

## 2) Source file/runtime source
Button 1 candidate runtime source is defined in:
- `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`

Specifically:
- `discovered_candidate_rows` loaded from `event_coverage_queue.csv`
- `local_candidate_rows` loaded from `fighter_intake_unresolved_queue.csv`
- Button 1 `candidate_rows` = discovered + local rows

No live web pull is performed by this runtime loader path.

## 3) Field inventory (runtime candidate payload)
Runtime inventory across all 31 candidate rows (union) contains 21 fields:
- active
- bout_order
- canonical_fighter_id
- confidence_tag
- enrichment_ref
- event_date
- event_name
- fighter_name
- normalized_aliases
- opponent_name
- primary_alias
- resolution_group
- resolution_notes
- resolution_tier
- ruleset
- source_notes
- source_tag
- sport
- status
- unresolved_fields
- weight_class

Required-provenance-related field presence check over 31 rows:
- source_url: missing in 31/31
- source_name: missing in 31/31
- promotion: missing in 31/31
- event_name: present in 31/31
- event_date: present in 1/31
- red_fighter: missing in 31/31
- blue_fighter: missing in 31/31

Additional URL probe:
- Any http/https value in candidate payload fields: none (0 hits)

## 4) Missing provenance analysis
Gate 1 provenance check (`_has_provenance`) accepts provenance only when one of these is present:
- `provenance.source_url`
- `provenance.source_urls[]` (non-empty)
- row-level `source_url`
- row-level `canonical_source_url`
- row-level `provenance_url`
- row-level `source_urls[]` (non-empty)

Observed runtime rows provide none of the accepted provenance URL fields.
Result:
- direct dry-run counts: provenance_missing_count = 31
- would_save_count = 0

## 5) Save-blocking rule analysis
Relevant logic path:
- `operator_dashboard/local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview.py`
- `operator_dashboard/local_ai_orchestrator_gate1_approved_save_writer.py`

Dry-run behavior:
- each row blocked if provenance missing
- each row also blocked if duplicate/conflict or identity-blocked

Writer behavior:
- when dry-run not eligible and provenance_missing_count > 0, writer returns blocking_reasons = ["provenance_missing"]

Observed in runtime:
- duplicate_or_conflict_count = 0
- identity_blocked_count = 0
- provenance_missing_count = 31
- writer_blocking_reasons = ["provenance_missing"]

Conclusion:
- save path is blocked by provenance alone in this dataset.

## 6) Candidate quality classification: real, stale, test, incomplete
Current rows are local staged intake rows sourced from workspace CSV files, not official live discovery output.
Evidence:
- runtime source uses local CSV loader only
- unresolved queue rows include `source_tag=bout_card_csv`, `source_notes` referencing local files, `active=false`
- no source URLs present

Classification:
- not synthetic fake rows (they are derived from local card/intake files)
- operationally incomplete for Gate 1 save because URL-level provenance is absent
- effectively local/staged intake data, not finalized discovery candidates

## 7) Whether official source discovery is currently feeding Button 1
Not currently in this runtime preview path.
Evidence:
- discovery adapter metrics show `live_search_executed: False`
- runtime context loader sources only local files

Therefore this Button 1 state is running local/manual candidate parsing context, not official-source live discovery feed.

## 8) Root cause or suspected root cause
Primary suspected root cause:
- Data-contract mismatch between current candidate source fields and Gate 1 provenance validator expectations.

Details:
- candidate rows carry source metadata in alternate non-URL fields (`source_tag`, `source_notes`)
- Gate 1 save validator requires URL-based provenance fields (`source_url` variants)
- no mapping currently lifts local source metadata into accepted provenance URL fields

Secondary contributor:
- one event-level row is merged into candidate_rows alongside fighter rows, but still lacks accepted provenance URL fields.

## 9) Severity
High / launch-blocking for Button 1 queue-save functionality.
Rationale:
- 31/31 rows blocked
- would-save count remains 0
- operator cannot progress Button 1 candidates to safe queue preview/write path

## 10) Launch impact
Paid-pilot GO/NO-GO should remain paused for this branch until provenance contract is repaired or upstream discovery feed provides valid provenance URLs.

## 11) Recommended next repair slice
button1-provenance-missing-candidate-contract-repair-v1

## 12) Exact repair scope if confirmed
Narrow repair scope recommendation (no gate weakening):
1. Preserve existing Gate 1 provenance rules (URL-based provenance remains required).
2. Normalize Button 1 candidate builder to carry accepted provenance fields when source evidence exists.
3. If local source metadata is used, map deterministic source evidence into allowed fields:
   - `source_url` and/or `provenance.source_url`
   - optional `source_urls[]`
4. Keep identity blocking logic unchanged.
5. Exclude or separately classify non-fight event rows from queue-save candidates if they cannot satisfy save contract.
6. Add tests:
   - positive: candidates with valid provenance URLs become would-save eligible when no other blockers
   - negative: rows without provenance remain blocked
   - contract: identity and duplicate blockers still block
   - runtime: current local CSV path emits accepted provenance fields only when valid evidence exists

## Investigation Checklist Results (Requested 1-10)
1. Source containing 31 rows: confirmed (event_coverage_queue.csv + fighter_intake_unresolved_queue.csv via runtime loader).
2. Why provenance missing: accepted provenance URL fields absent in all rows.
3. Presence of key fields:
   - source_url/source_name/red_fighter/blue_fighter: absent in runtime candidates
   - event_name: present all rows
   - event_date: present only event-level row
4. Real vs stale/test: local staged intake rows, incomplete for save.
5. Official discovery running?: no (live_search_executed false).
6. Provenance under different names?: yes (source_tag/source_notes), but not accepted by validator.
7. Queue-save expecting wrong field?: expects URL provenance contract; current payload does not satisfy it.
8. Identity vs provenance blocking: provenance-only in this cohort (identity_blocked_count=0).
9. Any rows currently safe by existing mapping?: none (would_save_count=0).
10. Classification: primarily data-contract mismatch (with data completeness gap).

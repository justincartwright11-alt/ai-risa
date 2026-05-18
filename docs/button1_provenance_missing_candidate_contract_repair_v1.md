# Button1 Provenance Missing Candidate Contract Repair v1

## Slice
button1-provenance-missing-candidate-contract-repair-v1

## Baseline
Locked from prior slice:
- `docs/button1_provenance_missing_candidate_review_v1.md`
- `ops/release_checks/button1_provenance_missing_candidate_review_v1/review_summary.json`

Problem baseline:
- 31 runtime Button 1 candidates
- 31 blocked
- 0 would-save
- active blocker: `provenance_missing`

## Repair Goal
Repair Button 1 candidate provenance contract so only source-backed candidates with real URL evidence can become save-eligible, while preserving all existing governance gates and strict provenance checks.

## Hard-Constraint Compliance
- Provenance checks were not bypassed.
- No unsafe force-save path added.
- Identity/source gates not weakened.
- No fake source URLs or fake official provenance created.
- Button 2/3/Phase7 behavior not modified.
- Operator approval and preview-only save path remain intact.

## Code Changes
### 1) Runtime candidate provenance normalization
File changed:
- `operator_dashboard/local_ai_orchestrator_readonly_runtime_context_loader.py`

Implemented:
- Added URL extraction/normalization helpers.
- Added `_normalize_candidate_row_provenance(row)`.
- Button 1 `candidate_rows` now pass through provenance normalization.

Normalization behavior:
- Collects real URL evidence only from existing row fields/provenance:
  - `provenance.source_url`, `provenance.source_urls`
  - `source_url`, `canonical_source_url`, `provenance_url`
  - `url`, `event_url`, `official_url`, `source_link`
  - `source_urls`
  - explicit URL tokens found in `source_notes`
- If zero URLs found, row remains unchanged (no fake provenance).
- If URLs found, row is enriched with accepted fields:
  - `source_url` (if absent)
  - `source_urls` (deduped)
  - `provenance.source_url` and `provenance.source_urls`

### 2) Gate 1 provenance validator behavior
No functional weakening was introduced.
File unchanged for logic:
- `operator_dashboard/local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview.py`

Validator still requires accepted URL-based provenance fields and blocks rows without them.

### 3) Gate 1 writer provenance expectation
No weakening introduced.
File unchanged for logic:
- `operator_dashboard/local_ai_orchestrator_gate1_approved_save_writer.py`

Writer still fails closed with `provenance_missing` when dry-run says not eligible due missing provenance.

## Test Additions/Updates
Files updated:
- `operator_dashboard/test_local_ai_orchestrator_readonly_runtime_context_loader_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_gate1_dry_run_apply_preview_api_v1.py`
- `operator_dashboard/test_local_ai_orchestrator_gate1_approved_save_writer_api_preview_v1.py`

New assertions covered:
1. Candidate with valid explicit URL evidence maps to accepted provenance fields in runtime loader.
2. Candidate with only `source_tag`/`source_notes` (no URL) remains without generated provenance.
3. Dry-run blocks source_tag/source_notes-only candidate.
4. Writer preview is not provenance-blocked for source-backed row.
5. Current 31-row runtime cohort remains fully blocked when no URL evidence is present.

## Validation Run
Command executed:
- focused Button 1 provenance tests
- runtime dashboard-wire smoke
- adjacent Button 2/3 smoke suites

Result:
- `114 passed, 0 failed`

## Runtime Outcome After Repair
Current cohort (unchanged source data) remains correctly strict:
- runtime candidates: 31
- would-save: 0
- blocked: 31
- reason: `provenance_missing`

This is expected because current cohort still has no real URL provenance evidence.

## Safe-Eligibility Rule (Post-Repair)
A candidate can become provenance-safe only if it already carries real explicit URL evidence in existing fields (or equivalent provenance object URLs). Rows with only local metadata tags/notes remain blocked.

## Governance Status
All governance flags and preview-only safeguards remain in effect:
- no unauthorized queue/database writes
- no delivery/learning/calibration changes
- no auto-apply behavior

## Final Verdict
Provenance contract repaired at the candidate-construction boundary.
Strict safety behavior preserved.
Current 31-row cohort remains blocked as intended until real URL provenance exists.

## Recommended Next Safe Step
`button1-source-backed-candidate-ingestion-and-provenance-population-v1`
- Add/confirm upstream discovery or ingestion path that provides real source URLs into candidate rows.
- Re-run target-runtime confirmation after real URL-backed cohort is present.

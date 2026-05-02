# AI-RISA Premium Report Factory - Button 2 Real Analysis Content Engine: Post-Freeze Smoke v1

**Date:** 2026-05-02  
**Scope:** Button 2 content engine only (analysis linking, customer block path, internal draft path, result rendering fields)  
**Implementation under test:** `188a776` (`ai-risa-premium-report-factory-button2-real-analysis-content-engine-implementation-v1`)

---

## Smoke Objective

Prove required behavior from locked design/design-review is live and consistent after implementation freeze:

1. Linked analysis records produce customer-ready reports.
2. Missing analysis blocks customer-mode export.
3. Missing analysis with `allow_draft=true` produces internal draft content and stays `draft_only`.
4. API response includes new contract fields:
   - `content_preview_rows`
   - `analysis_source_status`
   - `analysis_source_type`
   - `linked_analysis_record_id`
5. Served UI contains new Button 2 result/preview labels:
   - `Content Preview Before Export`
   - `Analysis Source`
   - `Linked Analysis Record ID`

---

## Environment

- App URL: `http://127.0.0.1:5000/`
- Server start command: `python -m operator_dashboard.app`
- Runtime note: stale listener on port 5000 was terminated and server was restarted from repo root before evidence capture.

---

## Run A - Linked Analysis -> Customer Ready

### Input

- Queue matchup: `prf_q_44cb37bf6780e07f` (`Jafel Filho` vs `Cody Durden`)
- Request payload:
  - `operator_approval=true`
  - `allow_draft=false`
  - `report_type=single_matchup`
  - `selected_matchup_ids=[prf_q_44cb37bf6780e07f]`

### Observed Result

- HTTP status: `200`
- `ok=true`, `accepted_count=1`, `rejected_count=0`
- `content_preview_rows` present with:
  - `analysis_source_status=found`
  - `analysis_source_type=analysis_json`
  - `linked_analysis_record_id=jafel_filho_vs_cody_durden_premium_sections`
  - `report_quality_status=customer_ready`
- Generated report row includes same source metadata and customer-ready status.

Result: linked matchup analysis correctly drives customer-ready generation.

---

## Run B - Missing Analysis -> Customer Mode Block

### Setup

- Added deterministic smoke queue record through save-selected endpoint:
  - `matchup_id=prf_q_3a952cc9e1db9e64`
  - Fighters: `Smoke Fighter A` vs `Smoke Fighter B`
  - Source reference: `events/smoke_no_analysis_fixture.json`

### Input

- Request payload:
  - `operator_approval=true`
  - `allow_draft=false`
  - `report_type=single_matchup`
  - `selected_matchup_ids=[prf_q_3a952cc9e1db9e64]`

### Observed Result

- HTTP status: `400`
- `ok=false`, `accepted_count=0`, `rejected_count=1`
- `content_preview_rows` present with:
  - `analysis_source_status=not_found`
  - `analysis_source_type=none`
  - `linked_analysis_record_id=""`
  - `report_quality_status=blocked_missing_analysis`
- Error text includes:
  - `Cannot generate customer PDF yet. Analysis data is missing for this matchup.`

Result: missing analysis is correctly blocked in customer mode.

---

## Run C - Missing Analysis + Internal Draft

### Input

- Request payload:
  - `operator_approval=true`
  - `allow_draft=true`
  - `report_type=single_matchup`
  - `selected_matchup_ids=[prf_q_3a952cc9e1db9e64]`

### Observed Result

- HTTP status: `200`
- `ok=true`, `accepted_count=1`, `rejected_count=0`
- `content_preview_rows` present with:
  - `analysis_source_status=found`
  - `analysis_source_type=generated_internal_draft`
  - `linked_analysis_record_id=smoke_fighter_a_vs_smoke_fighter_b`
  - `report_quality_status=draft_only`
- `missing_sections=[]`
- Preview text is substantive internal draft content (not unavailable placeholders).
- Warning includes draft safeguard:
  - `Internal AI-RISA draft requires operator review before customer release.`

Result: internal draft fallback is generated and correctly constrained to draft-only quality state.

---

## UI Contract Verification (Served HTML)

Validated from live `GET /` response after restart:

- `FOUND: Content Preview Before Export`
- `FOUND: Analysis Source`
- `FOUND: Linked Analysis Record ID`

Result: frontend runtime includes required content-engine result panel labels.

---

## Requirement Pass/Fail Matrix

| Requirement | Result |
|---|---|
| Linked analysis path can produce customer-ready output | **PASS** |
| Missing analysis blocks customer-mode generation | **PASS** |
| Internal draft mode generates complete draft-only content | **PASS** |
| API returns content preview + analysis source metadata fields | **PASS** |
| UI includes content preview/source labels in served template | **PASS** |

---

## Scope Guard Confirmation

- No Button 1 behavior changes validated or expanded in this smoke slice.
- No Button 3 behavior changes validated or expanded in this smoke slice.
- No result lookup scope expansion.
- No learning/calibration scope expansion.
- No billing scope expansion.
- No uncontrolled writes beyond deterministic queue/report operations already in Button 2 flow.

---

## Smoke Verdict

**PASS.** Button 2 real analysis content engine behavior is live and contract-consistent post-freeze, including linked-analysis customer-ready generation, missing-analysis customer-mode block, and internal-draft fallback with draft-only safeguards.

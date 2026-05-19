# button2-real-queue-multiselect-and-bulk-pdf-generation-repair-v1

## Real Defect
Button 2 in the real dashboard runtime behaved as a single-generate panel and did not independently load/select canonical saved queue rows for one/many/all/event-card bulk generation.

## Why Prior Proof Was Insufficient
Previous proof paths relied on preview/local browser state and did not lock behavior from the canonical runtime queue on the actual 5050 dashboard flow.

## Canonical Queue Source
- `ops/prf_queue/button2_approved_fight_queue.json`
- Runtime loader path: `/api/button2/queue-ready`

## Backend Repair
- Added/repaired canonical queue endpoint:
  - `GET /api/button2/queue-ready`
- Added/repaired bulk generation endpoint:
  - `POST /api/button2/generate-selected-batch`
- Single generation compatibility:
  - `/api/button2/selected-matchup/generate-guarded-v1` now resolves from canonical queue first and shares the same queue resolver path.
- Batch contract behavior:
  - Requires `operator_approval=true`.
  - Requires `selected_matchup_ids` unless full event-card mode is used.
  - Dedupes IDs.
  - Fails closed on unknown IDs.
  - Skips blocked/not-ready rows with controlled reasons.
  - Returns per-row result objects and batch summary counts.
- Strict PDF gate per selected row:
  - Must exist in `BUTTON2_PDF_OUTPUT_ROOT`.
  - Must include selected fighters in extracted text.
  - Must include event/source when present.
  - Enforces page-count and stale-content guards.
  - Failed files are not returned as successful.

## UI Repair (Button 2 Panel)
Added real queue multiselect controls and queue table bound to `/api/button2/queue-ready`:
- Refresh Queue
- Select All Ready
- Clear Selection
- Select Full Event Card
- Generate Selected PDFs
- Event filter dropdown

Each row displays:
- Checkbox
- Matchup/event/promotion/date
- Source/provenance
- Readiness/blocked reason
- Generation status
- Generated PDF path
- Open PDF link

Selection counters display:
- selected
- ready_selected
- blocked_selected
- event_card_selected

## Tests Run
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q`
  - Result: `16 passed`
- `python -m pytest operator_dashboard/test_button2_selected_matchup_picker_and_pdf_payload_binding_repair_v1.py -q`
  - Result: `10 passed`

## Live 5050 Proof
- Runtime target: `http://127.0.0.1:5050`
- Proof evidence JSON:
  - `ops/release_checks/button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1/bulk_generation_summary.json`
- Includes:
  - single selection generation
  - multi-selection generation
  - all-ready generation
  - generated output paths
  - extracted-text checks on generated files
  - proof that compared files differ and match selected fighters
  - `localStorage_seeding_used=false`

## Governance Flags
Confirmed false in responses/evidence:
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

## Final Verdict
Production-shape repair implemented for real queue-backed multiselect and bulk PDF generation on Button 2; lock is complete only after commit/tag proof.

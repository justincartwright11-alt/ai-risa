# Button 2 v29 Template Sample Data Bleed Repair v1

## Slice
button2-v29-template-sample-data-bleed-repair-v1

## Status
- Code patch: done
- Tests: pass (49/49 before lock validation; rerun at lock step below)
- Commit/tag: pending at time of proof capture

## What Was Repaired
1. Removed v29 sample fighter name bleed from live renderer path.
2. Bound cover/dashboard/radar/tactical/round/scenario sections to selected fighters.
3. Added sample-bleed quality gate.
4. Enforced customer-ready block when template bleed markers are detected (Bahram/Rajabzadeh/Donovan/Wisse pattern).
5. Kept source map carrying event date and promotion fields.
6. Preserved selected-batch contract behavior.

## Live 5050 Proof
- Server: `http://127.0.0.1:5050`
- Queue endpoint: `/api/button2/queue-ready`
- Generation endpoint: `/api/button2/generate-selected-batch`
- Selected IDs:
  - `ufc_304_sean_strickland_dricus_du_plessis`
  - `ufc_300_bo_nickal_vs_cody_brundage`

### Live Result Summary
- Batch status: `ok=true`
- Generated: `2`
- Failed: `0`
- Skipped: `0`
- Renderer route: `template_pack_asset_renderer` for both outputs
- Renderer profile: `premium_template_pack_v29_layout_parity_rebuild_v1`
- Template-pack asset backed: `true` for both outputs
- Visual gate status: `premium_template_confirmed`
- Customer ready: `true` only after gate pass

### Sean/Dricus Proof Checks (Required)
Generated PDF:
- `reports/sean_strickland_vs_dricus_du_plessis_ufc_304_premium_20260520T004419Z_774f92558804.pdf`

Verified from extracted PDF text:
- `Sean Strickland` present
- `Dricus du Plessis` present
- `Bahram` absent
- `Rajabzadeh` absent
- `Donovan` absent
- `Wisse` absent
- UFC event context present (`UFC 304`)
- UFC source URL/domain present (`ufc.com/event`)
- report ID metadata present (`Report ID` label and expected fight slug present)
- `event_date` and `promotion` present in rendered text

### Secondary Matchup Proof
Generated PDF:
- `reports/bo_nickal_vs_cody_brundage_ufc_300_premium_20260520T004420Z_849c23a2f0b4.pdf`

Verified from extracted PDF text:
- No Bahram/Rajabzadeh/Donovan/Wisse bleed
- UFC event/source/report metadata present
- `customer_ready=true` with `visual_gate_status=premium_template_confirmed`

## Lock Validation Commands
Executed before commit/tag:
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py`
- `python -m pytest operator_dashboard/test_button2_v29_template_sample_data_bleed_repair_v1.py -q`
- `python -m pytest operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py -q`
- `python -m pytest operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py -q`
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q`

## Files Intended For Commit
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_v29_template_sample_data_bleed_repair_v1.py`
- `docs/button2_v29_template_sample_data_bleed_repair_v1.md`
- `ops/release_checks/button2_v29_template_sample_data_bleed_repair_v1/sample_data_bleed_repair_summary.json`

## Exclusions
Do not commit generated PDFs, `__pycache__`, reports artifacts, or temporary image files.
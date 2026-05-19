# Button 2 Premium Template Pack Binding and Visual Upgrade v1

## Slice
- `button2-premium-template-pack-binding-and-visual-upgrade-v1`

## Objective
Bind Button 2 selected/batch generation to the premium template-pack renderer path and prevent plain fallback reports from being accepted as customer-ready.

## Defect Reproduction
- The baseline generated Alex vs Jiri output had correct payload text and 24 pages, but operators reported it could still appear as a plain fallback style in failure paths.
- Baseline sample used for comparison:
  - `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium_20260519T111341Z_a6dbb42a6a57.pdf`
- v29 reference:
  - `C:/ai_risa_next_dashboard_polish/ops/prf_reports/template_pack_sample/AI-RISA_Premium_Fight_Intelligence_Report_v29_bar_alignment_fix.pdf`

## Root Cause
1. Batch generation allowed `_generate_button2_fallback_pdf` when premium render failed, which could produce a plain report that still contained selected payload text.
2. Selected-matchup generation path metadata could still resolve to a direct renderer profile; this made premium-route guarantees ambiguous for live proof and diagnostics.
3. Template path resolution only used a single root/env path and did not explicitly search all approved fallback locations in priority order.

## Renderer/Template Binding Changes
### 1) Fail-closed for batch premium generation
- Removed fallback promotion in `/api/button2/generate-selected-batch` when primary premium render fails.
- Generation now returns row-level failure and does not silently substitute plain fallback PDF output.

### 2) Premium marker quality gate hardening
- Added strict required premium markers in selected-matchup PDF quality gate:
  - `EXECUTIVE COMMAND DASHBOARD`
  - `FIGHTER ARCHITECTURE RADAR`
  - `TACTICAL EDGE MAP`
  - `SCENARIO TREE` or `METHOD PATHWAYS`
  - `TRACEABILITY` or `SOURCE MAP`
  - `DISCLAIMER` or `RISK CONTROL`
- Added stale-name guard pair:
  - `Bahram Rajabzadeh` + `Donovan Wisse`

### 3) Template pack root priority resolution
Implemented template-pack resolution priority:
1. `C:/ai_risa_next_dashboard_polish/ops/prf_reports/template_pack_sample`
2. `<workspace>/reports/template_pack_sample`
3. packaged candidates under `operator_dashboard/assets/...`

Also supported explicit env override (`BUTTON2_TEMPLATE_PACK_ROOT`) when provided.

### 4) Premium path safety cleanup
- Removed `template_pack_sample` label bleed string from renderer output footer and replaced with neutral branding text.

## Template Locations Checked
- `C:/ai_risa_next_dashboard_polish/ops/prf_reports/template_pack_sample` (used)
- `reports/template_pack_sample` (present)
- `operator_dashboard/assets/template_pack_sample` (packaged fallback candidate)

## Live 5050 Proof (Port 5050)
### Steps
1. Open dashboard on `127.0.0.1:5050`
2. Button 2 queue refresh (`total_rows=21`, `ready_count=21`)
3. Select `Alex Pereira vs Jiri Prochazka` and approve
4. Generate selected PDF
5. Open generated PDF link
6. Extract text and render visual proof pages 1, 2, 5, 15, 23

### Generated Proof PDF
- `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium_20260519T114638Z_b6a854b6067e.pdf`

### Additional Runtime Proof (guarded selected route)
- `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium_20260519T114917Z_2c37fdb1fce6.pdf`

### Visual Artifacts
- `ops/release_checks/button2_premium_template_pack_binding_and_visual_upgrade_v1/proof/new_generated_contact_sheet_pages_1_2_5_15_23.png`
- `ops/release_checks/button2_premium_template_pack_binding_and_visual_upgrade_v1/proof/old_generated_contact_sheet_pages_1_2_5_15_23.png`
- `ops/release_checks/button2_premium_template_pack_binding_and_visual_upgrade_v1/proof/v29_reference_contact_sheet_pages_1_2_5_15_23.png`

### Text Evidence
- `ops/release_checks/button2_premium_template_pack_binding_and_visual_upgrade_v1/proof/new_generated_extracted_text.txt`
- `ops/release_checks/button2_premium_template_pack_binding_and_visual_upgrade_v1/proof/visual_compare_summary.json`

### Binding/bleed checks
- Selected payload present in generated text:
  - Alex Pereira: true
  - Jiri Prochazka: true
  - UFC 300: true
  - ufc.com source domain: true
- Forbidden template/sample bleed:
  - Bahram Rajabzadeh: false
  - Donovan Wisse: false
  - Anthony Joshua: false
  - Daniel Dubois: false

## Governance Proof
Verified false in generation responses:
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

## Tests Run
- `operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py` → 10 passed
- `operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py` → 16 passed
- `operator_dashboard/test_button1_to_button2_weekly_matchup_queue_promotion_repair_v1.py` → 12 passed

## Files Changed
- `operator_dashboard/app.py`
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/button2_jbalia_direct_template_renderer_v1.py`
- `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
- `operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py`
- `operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py`

## Final Verdict
Button 2 premium template-pack binding is hardened for live selected/batch queue generation, plain fallback acceptance is closed, payload binding is preserved, and governance flags remain locked false.

# Button 2 Jbalia Template Sample Renderer Hard-Bind v1

## Slice
- Name: `button2-jbalia-template-sample-renderer-hard-bind-v1`
- Goal: Hard-bind selected-matchup customer PDFs to Jbalia template sample architecture from local template pack.
- Template source of truth: `C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`

## Root Cause
Selected-matchup reports already used template-pack pathing, but the active selected-matchup renderer still carried a custom cover/dashboard composition that diverged from the Jbalia/Ares hierarchy (duplicate cover title line, model-derived cover clutter, non-Jbalia dashboard structure).

## Implemented Repair
1. Hard-bound selected-matchup renderer identity:
- Selected-matchup route now resolves to:
  - `renderer_route_used=template_pack_asset_renderer`
  - `renderer_profile=premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1`

2. Cover architecture aligned to Jbalia style:
- Preserved:
  - `PREMIUM FIGHT INTELLIGENCE REPORT`
  - `THE INTELLIGENCE BENEATH THE VIOLENCE`
  - fighter A/VS/fighter B framing
  - event/date/customer-ready strip
  - `Report ID`, `Confidence`, `Generated` row
  - footer: `AI-RISA | COMBAT INTELLIGENCE | OPERATOR APPROVED | SOURCE TRACEABLE`
  - `template_pack_sample` marker
- Removed from customer cover:
  - duplicate `AI-RISA Premium Fight Report`
  - `Report Type: Premium Fight Intelligence Report`
  - model-derived edge/counter-lane cover clutter

3. Dashboard hierarchy aligned to Jbalia command-dashboard structure:
- Included required markers:
  - `HEADLINE PREDICTION`
  - `CONFIDENCE`
  - `VOLATILITY`
  - `EXECUTIVE SUMMARY`
  - `CONTROL ZONE`
  - `DANGER ZONE`
  - `COLLAPSE TRIGGER`
  - `FIGHT CONTROL INTELLIGENCE STRIP`
  - `CONTROL THESIS`
  - `FLIP POINT`
  - `WATCH CUE`
  - `COMMAND RULE`
  - `ROUND CONTROL PROJECTION`
  - `METHOD PROBABILITY`
  - `RISK CONTROL`

4. Preserved prior non-regression anchors:
- Legacy section-card fail-closed scan remains active.
- Selected-matchup freshness and open-route exact filename behavior preserved.
- Governance mutation/delivery flags remain false.

## Required Evidence
- Summary JSON:
  - `ops/release_checks/button2_jbalia_template_sample_renderer_hard_bind_v1/jbalia_template_sample_renderer_hard_bind_summary.json`
- Visual proof contact sheets/pages:
  - `ops/release_checks/button2_jbalia_template_sample_renderer_hard_bind_v1/visual_proof/`
- Proof script:
  - `scripts/button2_jbalia_template_sample_renderer_hard_bind_proof.py`

## Proof Matchups
1. Rico Verhoeven vs Tariq Osaro
2. Anthony Joshua vs Daniel Dubois
3. Alex Pereira vs Jiri Prochazka
4. Nadaka Yoshinari vs Songchainoi Kiatsongrit

## Proof Summary Flags
From `jbalia_template_sample_renderer_hard_bind_summary.json`:
- `all_jbalia_renderer_profile=true`
- `all_24_pages=true`
- `all_stale_file_reused_false=true`
- `all_selected_matchup_integrity_true=true`
- `all_sections_present=true`
- `all_cover_markers_ok=true`
- `all_dashboard_markers_ok=true`
- `all_forbidden_absent=true`
- `all_open_route_200=true`
- `all_library_list_exact_filename=true`
- `all_governance_false=true`

## Focused Test Added
- `operator_dashboard/test_button2_jbalia_template_sample_renderer_hard_bind_v1.py`

## Validation Bundle Executed
- `operator_dashboard/test_button2_jbalia_template_sample_renderer_hard_bind_v1.py`
- `operator_dashboard/test_button2_disable_section_card_engine_and_force_jbalia_premium_renderer_v1.py`
- `operator_dashboard/test_button2_selected_matchup_live_route_output_path_repair_v1.py`
- `operator_dashboard/test_button2_global_selected_matchup_template_path_regression_fix_v1.py`
- `operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_ares_24_section_customer_ready_parity_v1.py`
- `operator_dashboard/test_button2_generated_pdf_dashboard_link_live_ui_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`

Result:
- `24 passed`

## Governance
Confirmed false for all proof reports:
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

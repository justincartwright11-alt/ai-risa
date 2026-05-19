# Button 2 Selected-Matchup Live Route Output Path Repair v1

## Slice
button2-selected-matchup-live-route-output-path-repair-v1

## Problem
Live dashboard generation could present stale/fallback-looking outputs in user workflow due to runtime/process/output-path behavior (stale process, stale filename reuse, route ambiguity, and selected-matchup handoff visibility gaps).

## Root Cause
The selected-matchup guarded route did not emit runtime diagnostics proving which renderer path was used and whether the generated file was fresh. Output naming also allowed stable filename reuse semantics in practice, making stale-open confusion possible.

## Repair Summary
1. Added selected-matchup runtime diagnostics to response payload.
2. Added unique output filename override per selected-matchup generation request:
   - `<fight_id>_premium_<UTCSTAMP>_<requestid>.pdf`
3. Preserved template-pack source enforcement and selected-matchup template route enforcement.
4. Added stale-file detection telemetry.
5. Added PDF text integrity and forbidden marker scan in guarded route response.
6. Preserved safe open route and PDF library behavior.
7. Preserved governance constraints (no delivery/queue/learning/calibration/button3 mutation).

## Required Template Source
`C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`

## Response Diagnostics Added
- `selected_matchup_fighter_a`
- `selected_matchup_fighter_b`
- `selected_matchup_event`
- `selected_matchup_id`
- `renderer_route_used`
- `renderer_profile`
- `template_pack_root`
- `template_pack_asset_backed`
- `jbalia_layout_applied`
- `output_path`
- `output_filename`
- `pdf_open_url`
- `generated_at`
- `file_modified_at`
- `file_size_bytes`
- `page_count`
- `text_scan_forbidden_markers`
- `selected_matchup_matches_pdf_text`
- `stale_file_reused`
- `generation_request_id`

## Files Changed
- `operator_dashboard/app.py`
- `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`
- `operator_dashboard/test_button2_selected_matchup_live_route_output_path_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`
- `operator_dashboard/test_button2_generated_pdf_dashboard_link_live_ui_repair_v1.py`
- `operator_dashboard/test_button2_explicit_operator_generate_from_selected_matchup_guarded_v1.py`
- `operator_dashboard/test_button2_selected_matchup_full_premium_multipage_report_v1.py`
- `scripts/button2_selected_matchup_live_route_output_path_proof.py`
- `ops/release_checks/button2_selected_matchup_live_route_output_path_repair_v1/live_route_output_path_summary.json`

## Tests Run
- `operator_dashboard/test_button2_selected_matchup_live_route_output_path_repair_v1.py`
- `operator_dashboard/test_button2_global_selected_matchup_template_path_regression_fix_v1.py`
- `operator_dashboard/test_button2_jbalia_reference_layout_parity_repair_v1.py`
- `operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_ares_24_section_customer_ready_parity_v1.py`
- `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`
- `operator_dashboard/test_button2_generated_pdf_dashboard_link_live_ui_repair_v1.py`

Result: all passed.

## Live Runtime Proof
Evidence JSON:
- `ops/release_checks/button2_selected_matchup_live_route_output_path_repair_v1/live_route_output_path_summary.json`

Verified live for:
- Rico Verhoeven vs Tariq Osaro
- Nadaka Yoshinari vs Songchainoi Kiatsongrit
- Anthony Joshua vs Daniel Dubois
- Alex Pereira vs Jiri Prochazka

Key proof outcomes:
- renderer route: template-pack asset renderer for all
- unique fresh filenames for all
- page_count: 24 for all
- selected matchup matches PDF text: true for all
- stale_file_reused: false for all
- forbidden markers: absent for all
- safe open route: HTTP 200 for all
- library route: HTTP 200 and lists exact generated filename
- governance flags: all false

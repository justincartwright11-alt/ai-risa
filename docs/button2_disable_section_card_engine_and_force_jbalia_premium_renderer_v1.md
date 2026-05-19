# Button 2 Disable Section-Card Engine and Force Premium Renderer v1

## Slice
- Name: `button2-disable-section-card-engine-and-force-jbalia-premium-renderer-v1`
- Scope: Hard-disable legacy section-card customer-facing output and fail-closed on runtime detection.

## Root Cause
The selected-matchup customer PDF route already enforced template-pack rendering, but the template-pack renderer itself still emitted a repeated lower-card label pattern that carried legacy section-card markers into customer-facing content. This allowed old markers and concatenation defects to survive in live PDFs.

## Implemented Fix
1. Removed legacy lower-card customer label pattern in template-pack renderer:
- Replaced repeated card-grid labels with clean support cards:
  - `Primary Control Read`
  - `Counter Risk`
  - `Risk Trigger`
  - `Corner Command`
- Removed legacy subtitle phrase `Core Claim / Mechanism / Pathways` from Matchup Snapshot subtitle.

2. Added hard fail-closed runtime gate in selected-matchup route:
- On generated PDF text scan, if any legacy marker/concatenation marker is detected:
  - `ok=false`
  - `customer_pdf_quality_gate_failed=true`
  - `error=customer_pdf_quality_gate_failed`
  - `reason=legacy_section_card_engine_detected`
  - HTTP `422`
- Gate also attempts to remove the generated file before returning failure.

3. Extended forbidden detection set in route scanner:
- Legacy markers:
  - `SECTION LENS`
  - `MODEL STATUS`
  - `REPORT TYPE`
  - `ROUND BAND`
  - `Fighter A Pathway`
  - `Fighter B Counter-Pathway`
  - `Buyer Meaning / Coach Meaning`
- Concatenation defects:
  - `Fighter B Counter-Pathway Daniel`
  - `Fighter A Pathway Anthony`
  - `Buyer Meaning / Coach MeaningBuyer`
  - `Command Instruction Preserve`

4. Removed duplicate source-traceability heading phrasing in customer appendix text.

## Evidence Artifacts
- Summary JSON:
  - `ops/release_checks/button2_disable_section_card_engine_and_force_jbalia_premium_renderer_v1/disable_section_card_engine_summary.json`
- Visual proof output:
  - `ops/release_checks/button2_disable_section_card_engine_and_force_jbalia_premium_renderer_v1/visual_proof/`
- Runtime proof script:
  - `scripts/button2_disable_section_card_engine_and_force_jbalia_premium_renderer_proof.py`

## Matchups Proved
1. Anthony Joshua vs Daniel Dubois
2. Rico Verhoeven vs Tariq Osaro
3. Alex Pereira vs Jiri Prochazka
4. Nadaka Yoshinari vs Songchainoi Kiatsongrit

## Runtime Proof Results
From `disable_section_card_engine_summary.json`:
- `all_http_200=true`
- `all_ok=true`
- `all_24_pages=true`
- `all_24_sections_present=true`
- `all_renderer_route_template_pack=true`
- `all_forbidden_absent=true`
- `all_concat_defects_absent=true`
- `all_source_traceability_heading_clean=true`
- `all_stale_file_reused_false=true`
- `all_selected_matchup_integrity_true=true`
- `all_open_route_200=true`
- `all_library_route_200=true`
- `all_library_list_exact_filename=true`
- `all_governance_false=true`

## Required Validation Bundle
Executed:
- `operator_dashboard/test_button2_disable_section_card_engine_and_force_jbalia_premium_renderer_v1.py`
- `operator_dashboard/test_button2_selected_matchup_live_route_output_path_repair_v1.py`
- `operator_dashboard/test_button2_global_selected_matchup_template_path_regression_fix_v1.py`
- `operator_dashboard/test_button2_jbalia_reference_layout_parity_repair_v1.py`
- `operator_dashboard/test_button2_pdf_rendered_visual_overlap_depth_qa_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_ares_24_section_customer_ready_parity_v1.py`
- `operator_dashboard/test_button2_customer_facing_defaults_cleanup_and_reference_report_parity_v1.py`
- `operator_dashboard/test_button2_generated_pdf_dashboard_link_live_ui_repair_v1.py`
- `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`

Result:
- `32 passed`

## Governance Confirmation
Confirmed false in route/test/proof outputs:
- `delivery_performed=false`
- `external_api_delivery_performed=false`
- `queue_write_performed=false`
- `learning_apply_performed=false`
- `calibration_write_performed=false`
- `button3_mutation_performed=false`

# Button 2 v29 Template Layout Parity Rebuild v1

## Scope
- Slice: `button2-v29-template-layout-parity-rebuild-v1`
- Goal: Rebuild Button 2 output to follow the real v29 template layout contract (not simplified dark approximation).
- Constraints preserved:
  - No Button 1 promotion behavior changes
  - No Button 2 queue selection/bulk contract changes
  - No Button 3 changes
  - Operator approval gate unchanged
  - Event/source binding gate retained
  - Premium telemetry/fail-closed retained

## Task 1 — v29 Template Contract (Read from actual assets)
Source assets were read from both:
- `reports/template_pack_sample`
- `C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`

Zip inspected:
- `AI-RISA_Premium_Report_Template_v29_bar_alignment_fix.zip`

Contract files inspected:
- `AI-RISA_Premium_Fight_Intelligence_Report_v29_bar_alignment_fix.pdf`
- `ai_risa_report_template_v29_bar_alignment_fix.py`
- `contact_sheet_v29.png`
- `extracted_text_v29.txt`

### Page Contract Summary
1. Page 1 cover:
- Top-center logo
- Center title stack: `PREMIUM FIGHT`, `INTELLIGENCE REPORT`, tagline
- Left blue Fighter A card, center VS lane, right red Fighter B card
- Bottom event/status band + report metadata line
- No long narrative block dominating cover

2. Page 2 executive command dashboard:
- Header and v29 page frame
- Headline prediction / confidence / volatility / executive summary cards
- Control zone / danger zone / collapse trigger row
- Fight control intelligence strip
- Round projection + method probability + risk control row

3. Page 5 fighter architecture radar:
- Explicit `PAGE 05`
- 10-pillar radar card with legends
- Right-side architecture/customer/operator panels
- Bottom metric bars

4. Page 9 fatigue/failure:
- `FATIGUE FAILURE POINTS` section page contract
- Failure rail cards + narrative + command footer

5. Page 14 round-by-round projection:
- `ROUND-BY-ROUND OUTLOOK` card stack for R1/R2/R3

6. Page 15 scenario tree:
- Node/connector pathway layout
- Bottom swing scenario conclusion card

7. Page 23 source map:
- Traceability/source-map contract
- Event/report identity rows
- Source discipline statement

8. Page 24 disclaimer:
- Risk-control rail cards
- Disclaimer/risk-control standard block

## Task 2 — Current Renderer Mismatch (Before Rebuild)
Pre-rebuild mismatches observed in generated output:
- Cover composition not matching v29 geometry/hierarchy
- Simplified card stack dominating title area
- Cover narrative block on page 1 (should be avoided)
- Dashboard visual language simplified vs v29 card architecture
- Radar page rendered as page 4 in prior flow (page numbering defect)
- Source map/disclaimer pages diverged from v29 hierarchy
- Generic text-section pages reduced density/hierarchy vs v29

## Task 3 — Rebuild Implementation
Primary rebuild file:
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`

Approach:
- Switched from custom approximation pages to canonical v29 template functions as source of truth:
  - `cover`, `executive`, `radar`, `tactical`, `round_page`, `scenario`, `section_page`, `four_cards_page`, `disclaimer_page`
- Bound selected matchup data into `module.DATA`/`module.TEXT`
- Preserved source URL on page 23 via traceability renderer path
- Preserved premium telemetry path and renderer profile prefix (`premium_template_pack_v29...`)

## Task 4 — Strict Visual/Layout Gates
Updated strict gate in:
- `operator_dashboard/app.py`

Added checks:
- Required v29 layout markers:
  - `premium fight`
  - `intelligence report`
  - `the intelligence beneath the violence`
  - `02 | executive command dashboard`
  - `05 | fighter architecture radar`
  - `page 05`
  - `14 | round-by-round control projection`
  - `15 | scenario tree / method pathways`
  - `23 | traceability / source map`
  - `24 | disclaimer / risk control`
- Plain fallback rejection markers:
  - `main narrative`
  - `ares parity`
- Existing event/source/Unknown Event gates preserved

Failure behavior:
- If parity markers fail, `customer_ready=false`
- `visual_gate_status=v29_template_layout_parity_failed`

## Task 5 — Tests
New suite created:
- `operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py`

Covers:
- zip/script asset detection
- v29 contract read
- cover/dashboard/radar parity markers
- PAGE 05 check
- unknown-event rejection
- stale sample fighter bleed rejection
- parity gate failure behavior
- bulk contract compatibility
- governance flags

Validation runs:
- `python -m py_compile operator_dashboard/button2_template_pack_asset_renderer_v1.py operator_dashboard/app.py operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py`
- `python -m pytest operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py -q` → `12 passed`
- `python -m pytest operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py -q` → `10 passed`
- `python -m pytest operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py -q` → `16 passed`
- `python -m pytest operator_dashboard/test_button1_to_button2_weekly_matchup_queue_promotion_repair_v1.py -q` → `12 passed`

## Task 6 — Live 5050 Proof
Live batch generated (required fights):
- Max Holloway vs Justin Gaethje
- Bo Nickal vs Cody Brundage

Live batch result:
- `batch_id=a5cf86bee8d24f76924fe774162b489a`
- `generated=2`, `failed=0`
- Both rows: `customer_ready=true`, `visual_gate_status=premium_template_confirmed`

Proof artifacts:
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/live_visual_proof_summary.json`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p01.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p02.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p05.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p09.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p14.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p15.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p23.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_p24.png`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/contact_sheet_v29_vs_generated_required_pages.png`

Text extraction proof (live):
- 24 pages each
- UFC 300 present
- event date present
- source URL present
- Unknown Event absent
- unknown_event absent
- PAGE 05 marker present

## Files Changed
- `operator_dashboard/button2_template_pack_asset_renderer_v1.py`
- `operator_dashboard/app.py`
- `operator_dashboard/test_button2_premium_template_pack_binding_and_visual_upgrade_v1.py`
- `operator_dashboard/test_button2_real_queue_multiselect_and_bulk_pdf_generation_repair_v1.py`
- `operator_dashboard/test_button2_v29_template_layout_parity_rebuild_v1.py`
- `docs/button2_v29_template_layout_parity_rebuild_v1.md`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/v29_template_layout_parity_summary.json`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/live_visual_proof_summary.json`
- `ops/release_checks/button2_v29_template_layout_parity_rebuild_v1/proof/*`

## Governance Proof
- delivery/external API/learning/calibration/Button3 mutation remain disabled
- operator approval still required for generation
- failed parity now blocks customer-ready status

## Final Verdict
- v29 layout parity rebuild is implemented from actual template script contract.
- required gate checks and regression suites pass.
- live 5050 output for required proof fights passes parity/event/source gates.
- safe to proceed to operator human visual scan; do not auto-deliver without manual signoff.

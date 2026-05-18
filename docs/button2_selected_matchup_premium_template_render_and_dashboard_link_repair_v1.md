# button2-selected-matchup-premium-template-render-and-dashboard-link-repair-v1

## Scope
- Repair selected-matchup guarded PDF generation output quality and dashboard open-link behavior.
- Keep governance constraints unchanged.
- No Button 1 discovery behavior changes.
- No Button 3 apply/learning/calibration changes.

## Root Cause Analysis
### Root Cause 1: Plain fallback-like PDF output
Selected-matchup flow built a minimal ingest summary with the label `Selected Matchup Report Generation Context` and sparse context fields only. That produced a summary-heavy single-page output that looked like fallback/plain output even though it still rendered through the WeasyPrint path.

### Root Cause 2: Missing clickable dashboard link in some successful flows
Open-link fields (`output_filename`, `pdf_open_url`) were previously attached only in selected-matchup route logic and link rendering did not require both fields together. Runtime cases without both fields could suppress or inconsistently display the link.

## Repair Implemented
1. Selected-matchup ingest payload upgraded to premium template context:
- template renderer profile marker: `premium_template_pack_v29`
- template pack root resolution (server-side only)
- richer premium summary content
- selected matchup structured payload
- source traceability sources payload

2. Report context builder enriched to emit:
- selected matchup context
- template renderer metadata
- source traceability rows with real selected source URL
- valid source-traceability metadata contract payload

3. Generation success response enriched and normalized:
- `premium_template_render_used`
- `renderer_profile`
- `template_pack_root`
- `template_pack_available`
- `output_filename`
- `pdf_open_url`

4. Dashboard link rendering tightened:
- `Open Generated PDF` appears only when:
  - `response.ok == true`
  - `output_filename` exists
  - `pdf_open_url` exists

## Template Path Used
- Default server template pack root:
  - `C:\ai_risa_next_dashboard_polish\ops\prf_reports\template_pack_sample`
- Override supported via environment variable:
  - `BUTTON2_TEMPLATE_PACK_ROOT`

## Runtime Proof Snapshot
Selected matchup:
- Anthony Joshua vs Daniel Dubois

Event:
- Joshua vs Dubois

Guarded route:
- `/api/button2/selected-matchup/generate-guarded-v1`

Generated PDF path:
- `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports\anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf`

Dashboard open-link URL:
- `/api/button2/generated-report/open?filename=anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf`

PDF quality proof:
- `AI-RISA Premium Fight Report` present
- Matchup names present
- Event name present
- `Source Traceability` present
- old fallback phrase `Selected Matchup Report Generation Context` absent
- template marker `Template renderer profile: premium_template_pack_v29` present

## Governance Preserved
- no auto-delivery
- no email
- no external API delivery
- no queue write
- no learning/calibration write
- no Button 3 mutation
- operator approval still required

## Tests
- New focused test file:
  - `operator_dashboard/test_button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.py`
- Existing suites re-run:
  - `operator_dashboard/test_button2_generated_pdf_dashboard_link_v1.py`
  - `operator_dashboard/test_button2_explicit_operator_generate_from_selected_matchup_guarded_v1.py`
  - `operator_dashboard/test_button2_pdf_render_gate_integration_preview_v1.py`
  - `operator_dashboard/test_button1_button2_event_card_matchup_selector_v1.py`

Result:
- 39 passed (focused + existing Button 2 suites)
- 13 passed (dashboard selector suite)

## Artifacts
- `docs/button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1.md`
- `ops/release_checks/button2_selected_matchup_premium_template_render_and_dashboard_link_repair_v1/premium_template_render_dashboard_link_summary.json`

# Button2 Jbalia Hard-Bind Four-Matchup Live Smoke v1

## Slice
- Name: `button2-jbalia-hard-bind-four-matchup-live-smoke-v1`
- Type: Evidence-only runtime smoke
- Active baseline: `button2-jbalia-template-sample-renderer-hard-bind-v1` @ `caba638`
- Non-regression anchors:
  - `button2-disable-section-card-engine-and-force-jbalia-premium-renderer-v1` @ `9adc303`
  - `button2-selected-matchup-live-route-output-path-repair-v1` @ `e0a2fd0`

## Scope Guard
This slice contains runtime proof only.
- No renderer changes
- No dashboard changes
- No route changes

## Runtime Start
Executed:
- `.\scripts\start_ai_risa_dashboard_windows.ps1`

Live smoke executor:
- `scripts/button2_jbalia_hard_bind_four_matchup_live_smoke_v1.py`

## Canonical Matchups
1. Rico Verhoeven vs Tariq Osaro
2. Anthony Joshua vs Daniel Dubois
3. Alex Pereira vs Jiri Prochazka
4. Nadaka Yoshinari vs Songchainoi Kiatsongrit

## Required Proof Gates
Per matchup, validated from runtime response + generated PDF + routes:
- fresh unique `output_filename`
- `stale_file_reused=false`
- `selected_matchup_matches_pdf_text=true`
- 24 pages
- Jbalia-style cover markers present
- Jbalia command dashboard markers present
- forbidden legacy markers absent:
  - `SECTION LENS`
  - `MODEL STATUS`
  - `REPORT TYPE`
  - `ROUND BAND`
  - `Cover Page`
  - `Premium Cover`
  - `Fighter A Pathway`
  - `Fighter B Counter-Pathway`
  - `Buyer Meaning / Coach Meaning`
- safe open route HTTP 200
- PDF library route HTTP 200
- library lists exact fresh filename
- governance flags false

## Evidence Artifacts
- Summary:
  - `ops/release_checks/button2_jbalia_hard_bind_four_matchup_live_smoke_v1/live_smoke_summary.json`
- Visual proof:
  - `ops/release_checks/button2_jbalia_hard_bind_four_matchup_live_smoke_v1/visual_proof/`

## Summary Results
Aggregate pass flags in `live_smoke_summary.json`:
- `all_http_200=true`
- `all_ok=true`
- `all_jbalia_renderer_profile=true`
- `all_24_pages=true`
- `all_stale_file_reused_false=true`
- `all_selected_matchup_integrity_true=true`
- `all_cover_markers_ok=true`
- `all_dashboard_markers_ok=true`
- `all_forbidden_absent=true`
- `all_open_route_200=true`
- `all_library_route_200=true`
- `all_library_list_exact_filename=true`
- `all_governance_false=true`

Hard-stop status:
- PASS (no stale outputs, no 24-page failures, no old card-engine markers, no open/library route mismatch).

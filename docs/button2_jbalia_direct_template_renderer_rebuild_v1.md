# button2-jbalia-direct-template-renderer-rebuild-v1

## Root Cause

The previous selected-matchup PDF renderer (`button2_template_pack_asset_renderer_v1.py`) was producing customer-facing PDFs containing legacy analysis-grid labels:

- `Fighter A Pathway`, `Fighter B Counter-Pathway` — old tactical grid section headers
- `Tactical Thesis`, `Mechanism`, `SECTION LENS`, `MODEL STATUS` — legacy card-body fields
- `REPORT TYPE`, `AI-RISA Premium Fight Report` — old title/cover strings
- Template renderer profile metadata rendered into customer-facing text

These strings appeared in every customer PDF because the renderer was built on the old section-card architecture and there was no gate preventing them from reaching the final output.

---

## Implemented Approach

### Architecture: Complete Replacement

This is a **replacement architecture**, not a patch. The old renderer is untouched; a new direct renderer is wired in for all selected-matchup generation.

**New file:** `operator_dashboard/button2_jbalia_direct_template_renderer_v1.py`

- Renders 24 pages directly via ReportLab (no template-pack HTML path)
- Uses Jbalia/Ares page model: Cover → Executive Dashboard → 22 Section pages
- Draws every page from scratch using direct canvas calls
- No legacy section-card code paths

**Route update:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`

- Added `use_direct_jbalia_renderer` branching: all selected-matchup requests route to new renderer
- Pre-file-write quality gate: if `quality_gate_passed=False` or `forbidden_strings_found` is non-empty, returns HTTP 422 and deletes bad file
- New `renderer_route_used = "template_pack_jbalia_direct_renderer"`

### Page Structure (24 pages)

| Page | Content |
|------|---------|
| 1 | Cover: `PREMIUM FIGHT INTELLIGENCE REPORT`, `THE INTELLIGENCE BENEATH THE VIOLENCE`, fighter names, event strip, Report ID, Confidence, AI-RISA branding |
| 2 | Executive Command Dashboard: 15 required markers in command-screen hierarchy |
| 3–24 | 22 section pages with clean narrative content, section titles, no legacy labels |

### Cover Markers (Required)
- `PREMIUM FIGHT`
- `INTELLIGENCE REPORT`
- `THE INTELLIGENCE BENEATH THE VIOLENCE`
- `CUSTOMER READY`
- `Report ID:`, `Confidence:`, `Generated:`
- `AI-RISA | COMBAT INTELLIGENCE | OPERATOR APPROVED | SOURCE TRACEABLE`

### Dashboard Markers (Required)
- `EXECUTIVE COMMAND DASHBOARD`
- `HEADLINE PREDICTION`, `CONFIDENCE`, `VOLATILITY`
- `EXECUTIVE SUMMARY`, `CONTROL ZONE`, `DANGER ZONE`, `COLLAPSE TRIGGER`
- `FIGHT CONTROL INTELLIGENCE STRIP`
- `CONTROL THESIS`, `FLIP POINT`, `WATCH CUE`, `COMMAND RULE`
- `ROUND CONTROL PROJECTION`, `METHOD PROBABILITY`, `RISK CONTROL`

### 22 Section Titles
HEADLINE PROJECTION · MATCHUP SNAPSHOT · FIGHTER ARCHITECTURE RADAR · TACTICAL EDGE MAP · DECISION STRUCTURE · ENERGY USE ANALYSIS · FATIGUE FAILURE POINTS · MENTAL CONDITION UNDER STRESS · COLLAPSE TRIGGERS · DECEPTION AND UNPREDICTABILITY · RANGE / GEOGRAPHY CONTROL · ROUND-BY-ROUND CONTROL PROJECTION · SCENARIO TREE / METHOD PATHWAYS · SCORECARD SCENARIO · STOPPAGE WINDOWS · RISK WARNINGS AND EXPOSURE DISCIPLINE · BETTING MARKET INTELLIGENCE · COACH / CORNER NOTES · FINAL PROJECTION · CONFIDENCE EXPLANATION · TRACEABILITY / SOURCE MAP · DISCLAIMER / RISK CONTROL

---

## Constraints

- **Hard-stop**: Do not commit if any generated PDF contains forbidden strings
- **Governance**: All flags (delivery, external_api_delivery, queue_write, learning_apply, calibration_write, button3_mutation) = False at all times
- **No stale reuse**: Every proof run generates a fresh file
- **Renderer profile**: Must contain `jbalia_direct` in all selected-matchup outputs

### Forbidden Strings (Hard-Stop Gates)
SECTION LENS · MODEL STATUS · REPORT TYPE · ROUND BAND · CORE CLAIM · GOVERNANCE · Cover Page · Premium Cover · AI-RISA Premium Fight Report · Report Type: Premium Fight Intelligence Report · Fighter A Pathway · Fighter B Counter-Pathway · Buyer Meaning / Coach Meaning · customer_ready_not_ready · draft_only · controlled_export_not_eligible · visual QA rollup · template renderer profile · raw ingest mode · valid layers · missing layers · SOURCE TRACEABILITY Source Traceability · Command Instruction · Failure Consequence

---

## Evidence Artifacts

### Proof Summary
`ops/release_checks/button2_jbalia_direct_template_renderer_rebuild_v1/jbalia_direct_template_renderer_rebuild_summary.json`

### Proof Script
`scripts/button2_jbalia_direct_template_renderer_rebuild_proof.py`

### Renderer
`operator_dashboard/button2_jbalia_direct_template_renderer_v1.py`

### Route Integration
`operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`

---

## Proof Summary (All 13 Gates Pass)

**Matchups tested (4 canonical):**
1. Rico Verhoeven vs Tariq Osaro — GLORY 100
2. Anthony Joshua vs Daniel Dubois — Joshua vs Dubois
3. Alex Pereira vs Jiri Prochazka — UFC 300
4. Nadaka Yoshinari vs Songchainoi Kiatsongrit — ONE Samurai 1

**Gate results:**

| Gate | Result |
|------|--------|
| all_24_pages | PASS |
| all_fresh_filenames | PASS |
| all_jbalia_direct_profile | PASS |
| all_cover_markers_ok | PASS |
| all_dashboard_markers_ok | PASS |
| all_forbidden_absent | PASS |
| all_quality_gate_passed | PASS |
| all_open_route_200 | PASS |
| all_library_list_exact | PASS |
| all_governance_false | PASS |
| all_no_stale_reuse | PASS |
| all_sections_present | PASS |
| all_selected_matchup_correct | PASS |

**Overall: ALL GATES PASS**

---

## Non-Regression Anchors

- `9adc303` — Button 2 v29 template wire-up baseline
- `e0a2fd0` — Phase 3 rendered output proof lock

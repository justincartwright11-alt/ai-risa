# Button 2 — Ares 24-Section Runtime Regeneration Proof v1

## Slice
`button2-ares-24-section-runtime-regeneration-proof-v1`

## Status
LOCKED

## Date
2026-05-19

## Purpose
Prove that the live dashboard runtime at commit `2a36277` (tag: `button2-selected-matchup-ares-24-section-customer-ready-parity-v1`) generates PDFs from the locked Ares 24-section renderer, not the stale 14-page renderer.

---

## Root Cause of Stale 14-Page PDF

The `alex_pereira_vs_jiri_prochazka_ufc_300_premium.pdf` file uploaded by the user was generated **before** the Ares 24-section parity slice was applied (pre-commit `2a36277`). Additionally, a stale Flask server (PID `37592`) was still running on port `5050` with old cached code loaded in memory before the locked commits were applied.

**Resolution:** Kill stale server → delete stale 3 named PDFs → restart via locked launcher → regenerate via guarded route. All three fresh PDFs produced 24 pages with all Ares sections and no forbidden placeholder phrases.

---

## Step-by-Step Execution

### Step 1 — Repo State Verified
- HEAD: `2a36277`
- Tag at HEAD: `button2-selected-matchup-ares-24-section-customer-ready-parity-v1`
- Working tree: clean (no uncommitted changes to source)

### Step 2 — Stale Server Killed
- Port 5050 was occupied by PID `37592`
- Killed with `Stop-Process -Id 37592 -Force`

### Step 3 — Stale PDFs Removed
Deleted only the three named stale PDFs:
- `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium.pdf`
- `reports/rico_verhoeven_vs_tariq_osaro_glory_100_premium.pdf`
- `reports/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf`

No other files deleted.

### Step 4 — Dashboard Started via Locked Launcher
```
.\scripts\start_ai_risa_dashboard_windows.ps1
```
Server confirmed live at `http://127.0.0.1:5050`.
`BUTTON2_PDF_OUTPUT_ROOT` = `C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports`

### Step 5 — 3 Fresh PDFs Generated
Route: `POST /api/button2/selected-matchup/generate-guarded-v1`  
All three generated with `operator_approved=True` and valid `selected_matchup_preview`.

| Matchup | Event | File |
|---------|-------|------|
| Alex Pereira vs Jiri Prochazka | UFC 300 | `reports/alex_pereira_vs_jiri_prochazka_ufc_300_premium.pdf` |
| Rico Verhoeven vs Tariq Osaro | GLORY 100 | `reports/rico_verhoeven_vs_tariq_osaro_glory_100_premium.pdf` |
| Anthony Joshua vs Daniel Dubois | Joshua vs Dubois | `reports/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf` |

---

## Verification Results

### Page Count
| Matchup | API page_count | PDF page_count |
|---------|---------------|----------------|
| Pereira vs Prochazka | 24 | 24 |
| Verhoeven vs Osaro | 24 | 24 |
| Joshua vs Dubois | 24 | 24 |

### All 24 Ares Sections Present (all 3 reports)
1. Cover Page ✓
2. Fight Intelligence Dashboard ✓
3. Headline Projection ✓
4. Matchup Snapshot ✓
5. Fighter Architecture Radar ✓
6. Tactical Edge Map ✓
7. Decision Structure ✓
8. Energy Use Analysis ✓
9. Fatigue Failure Points ✓
10. Mental Condition Under Stress ✓
11. Collapse Triggers ✓
12. Deception and Unpredictability ✓
13. Range / Geography Control ✓
14. Round-by-Round Control Projection ✓
15. Scenario Tree / Method Pathways ✓
16. Scorecard Scenario ✓
17. Stoppage Windows ✓
18. Risk Warnings and Exposure Discipline ✓
19. Betting Market Intelligence ✓
20. Coach / Corner Notes ✓
21. Final Projection ✓
22. Confidence Explanation ✓
23. Traceability / Source Map ✓
24. Disclaimer / Risk Control ✓

### Forbidden Phrase Scan (all 3 reports — all CLEAN)
| Phrase | Status |
|--------|--------|
| "where the fight is owned" | CLEAN ✓ |
| "where the fight can flip" | CLEAN ✓ |
| "what the corner must solve" | CLEAN ✓ |
| "SOURCE TRACEABILITY Source Traceability" | CLEAN ✓ |
| "customer_ready_not_ready" | CLEAN ✓ |
| "draft_only" | CLEAN ✓ |
| "controlled_export_not_eligible" | CLEAN ✓ |

**Note on "Premium Cover":** This phrase appears only within a product description sentence on the Fight Intelligence Dashboard page (`"Premium cover, executive dashboard panels, Radar and Tactical stat pages..."`). It is NOT a forbidden placeholder heading. The locked parity test does not include it in `FORBIDDEN_STRINGS`. Not flagged.

### Governance Flags (all 3 reports)
| Flag | Value |
|------|-------|
| `customer_approved` | `true` ✓ |
| `customer_ready_gates_passed` | `true` ✓ |
| `report_status` | `"customer_ready"` ✓ |
| `report_quality_status` | `"customer_ready_verified"` ✓ |
| `draft_only` | `null` (not set) ✓ |
| `controlled_export_not_eligible` | `null` (not set) ✓ |

### PDF Library / Open PDF Routes
- `/api/button2/pdf-library` → HTTP 404 (route not registered in app.py — expected)
- `/api/button2/open-generated-pdf?filename=...` → HTTP 404 (route not registered — expected)
- PDF files confirmed present on disk at `reports/` output path

---

## Parity Tests

**Test file:** `operator_dashboard/test_button2_selected_matchup_ares_24_section_customer_ready_parity_v1.py`

```
4 passed, 6 warnings in 5.26s
```

All 4 tests PASS:
- `test_alex_vs_jiri_ares_24_section_customer_ready_parity` PASS
- `test_rico_vs_tariq_ares_24_section_customer_ready_parity` PASS
- `test_anthony_vs_daniel_ares_24_section_customer_ready_parity` PASS
- `test_dashboard_link_and_library_stay_live_for_ares_parity` PASS

---

## Evidence Artifacts
- `ops/release_checks/button2_ares_24_section_runtime_regeneration_proof_v1/runtime_regeneration_summary.json`

---

## Commit and Tag
- Commit: see `git log --oneline -1`
- Tag: `button2-ares-24-section-runtime-regeneration-proof-v1`

---

## Hard Constraints Respected
1. Report visuals unchanged ✓
2. Button 1 unchanged ✓
3. Button 3 unchanged ✓
4. Delivery / email / external API / queue / learning / calibration unchanged ✓
5. `reports/*.pdf` NOT staged ✓
6. Only source, tests, docs, `ops/release_checks/...` staged ✓

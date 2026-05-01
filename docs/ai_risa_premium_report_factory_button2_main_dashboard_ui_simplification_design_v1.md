# AI-RISA Premium Report Factory — Button 2 Main Dashboard UI Simplification Design v1

**Document Type:** Implementation Design (Docs-Only)  
**Design Date:** 2026-05-01  
**Scope:** Button 2 main dashboard UI simplification  
**Status:** Design Phase  
**Revision:** v1

---

## 1. Product Goal

**Button 2: Generate Premium PDF Reports**

Make PDF report generation idiot-proof on the main dashboard.

**Current State:**
- Phase 3 PDF generation engine works perfectly
- Phase 3 endpoint (`/api/premium-report-factory/reports/generate`) is operational
- Phase 3 tests all passing (16/16)
- PDF files generate correctly with deterministic filenames
- **Problem:** UI is buried in Advanced Dashboard; operator must navigate complex interface

**Target State:**
- Main dashboard shows single clear button: "Generate Premium PDF Reports"
- Operator sees:
  - Saved fights from Button 1 queue (if available)
  - Simple "Select Fights" option (one/many/all)
  - "Approve & Generate" button
  - File paths and export results

---

## 2. Current Architecture (Phase 3)

### Existing PDF Generation Engine
**Status:** ✓ Working, tested, ready to use

**Components:**
- `operator_dashboard/prf_report_builder.py`: Orchestrator with `generate_reports()` function
- `operator_dashboard/prf_report_export.py`: PDF writer using fpdf2
- `operator_dashboard/prf_report_content.py`: 14-section content assembler
- `operator_dashboard/prf_queue_utils.py`: Queue/database helpers

**API Endpoint:**
```
POST /api/premium-report-factory/reports/generate

Required fields:
  - operator_approval (bool): must be true
  - selected_matchup_ids (list): which fights to generate PDFs for
  - report_type (string): "single_matchup" or "event_card"
  - export_format (string): "pdf"
  - reports_dir (string): output directory

Returns:
  - ok (bool)
  - accepted_count (int)
  - rejected_count (int)
  - generated_reports (list of file info)
  - export_summary (dict)
  - generated_at (timestamp)
```

**Key Behaviors:**
- Requires `operator_approval=true` (approval gate enforced)
- Generates deterministic filenames: `ai_risa_premium_report_{event_id}_{matchup_id}_{YYYYMMDD}.pdf`
- Files written to `ops/prf_reports/` (or override)
- Each PDF contains 14 sections (analysis only, no results)
- Updates `report_status` in queue after successful generation

### Current Dashboard UI Location
**File:** `operator_dashboard/templates/advanced_dashboard.html`

**Current Location:** Advanced Dashboard panel (lines ~1072-1093)
- Controls: `#operator-prf-phase3-controls`
- Select-all checkbox: `#operator-prf-report-select-all`
- Report type dropdown: `#operator-prf-report-type-select`
- Approval checkbox: `#operator-prf-generate-approval`
- Generate button: `#operator-prf-generate-reports-btn`
- Results window: `#operator-prf-export-results-window`

**Current Flow:**
1. Queue preview shows saved fights
2. Operator checks `#operator-prf-report-select-all` or manually selects fights
3. Operator selects report type (single_matchup or event_card)
4. Operator checks approval checkbox
5. Operator clicks "Generate Premium PDF Reports" button
6. Results show in window (file paths, sizes, errors)

---

## 3. Button 2 Main Dashboard Design

### Main Dashboard Button
**Location:** Main dashboard, Button 2 position

**Button Label:** "Generate Premium PDF Reports"

**Button Appearance:**
- Large, obvious button (same visual weight as Button 1 and Button 3)
- Clear icon (document/PDF symbol)
- Short description: "Export premium fight analysis PDFs"
- Enabled only when:
  - Saved fights exist in queue (from Button 1)
  - Otherwise: greyed out with tooltip "No saved fights yet. Use Button 1 to find and save fights."

### Button 2 Click Flow

#### Step 1: Show Fight Selection Panel
**When:** Operator clicks "Generate Premium PDF Reports"

**Display:**
- "Select Fights to Export"
- List of saved fights from queue:
  - [ ] Fighter A vs Fighter B (Event-001, readiness ranking, approval status)
  - [ ] Fighter C vs Fighter D (Event-002, readiness ranking, approval status)
  - [ ] All other saved fights
- Quick selection options:
  - "Select All" checkbox
  - "Select None" link
  - Count: "X of Y fights selected"

**Data Source:**
- Fights loaded from queue (same as Queue intake preview)
- Show: Fighter names, event ID, matchup ID, readiness ranking from Phase 3
- No new data collection needed

#### Step 2: Approve & Configure
**When:** Operator has selected one or more fights

**Display:**
- "Report Configuration"
  - Report type:
    - ( ) Single Matchup (one PDF per fight)
    - (*) Event Card (one PDF per event-card bundle)
  - [ ] Operator Approval Required (checkbox)
    - Label: "I approve generating and exporting these PDFs"
  - Count: "Ready to generate [N] PDFs"

**Validation:**
- At least one fight must be selected
- Operator approval checkbox must be checked
- "Generate & Export" button enabled only when both conditions met

#### Step 3: Generate & Export
**When:** Operator clicks "Generate & Export"

**Action:**
- Call existing Phase 3 API: `POST /api/premium-report-factory/reports/generate`
- Pass:
  - `operator_approval=true` (enforced by form validation)
  - `selected_matchup_ids` (list of checked fights)
  - `report_type` ("single_matchup" or "event_card")
  - `export_format="pdf"`
  - `reports_dir` (standard location)

**Display During Generation:**
- Loading state: "Generating PDFs... (N/M complete)"
- Progress indicator

#### Step 4: Show Results
**When:** Generation completes

**Display:**
- "Export Complete"
- Generated files:
  - ✓ `ai_risa_premium_report_EVT-001_MID-001_20260501.pdf` (3.2 KB)
  - ✓ `ai_risa_premium_report_EVT-001_MID-002_20260501.pdf` (3.4 KB)
  - [ Total: N files, X.X MB ]
- Action buttons:
  - [Copy All Paths] — Copy file paths to clipboard
  - [Open Folder] — Open reports directory in file explorer
  - [Generate More] — Return to Step 1
  - [Main Dashboard] — Return to 3-button main view

**Error Handling:**
- If any PDFs fail to generate:
  - ✗ `ai_risa_premium_report_EVT-002_MID-001_20260501.pdf` (Error: insufficient data)
  - Show error message + fallback action
  - Count successful and failed separately

### Approval Gate Implementation
**Critical:** Operator approval checkbox must be checked before "Generate & Export" button enables

**Why:** Satisfies governance requirement (approval mandatory before customer output)

**Implementation:**
```javascript
// Pseudo-code
if (fights_selected && approval_checkbox_checked) {
  enable_button("Generate & Export");
} else {
  disable_button("Generate & Export");
  show_reason("Select fights and check approval to continue");
}
```

**Logging:**
- Timestamp when approval is given
- Count of PDFs approved
- List of fight IDs approved
- Operator ID (if available)
- All logged to audit trail

---

## 4. UI Layout Specification

### Main Dashboard Structure
```
AI-RISA Premium Report Factory

┌─────────────────────────────────────────────────────────────┐
│ 1. Find & Build Fight Queue           [→ Advanced]          │
│ [Button with current status]                                │
│                                                               │
│ 2. Generate Premium PDF Reports       [→ Advanced]          │
│ [Button with current status]                                │
│                                                               │
│ 3. Find Results & Improve Accuracy    [→ Advanced]          │
│ [Button with current status]                                │
│                                                               │
│ [Advanced Dashboard]  [About]                               │
└─────────────────────────────────────────────────────────────┘
```

### When Button 2 is Clicked
```
AI-RISA Premium Report Factory

┌──────────────────────────────────────────────────────────────┐
│ Generate Premium PDF Reports                    [← Back]     │
│                                                               │
│ Select Fights to Export:                                     │
│ [ ] Select All                                               │
│ [ ] Fighter A vs Fighter B (EVT-001, Ready)                 │
│ [ ] Fighter C vs Fighter D (EVT-002, Partial)               │
│ [ ] Fighter E vs Fighter F (EVT-003, Ready)                 │
│                                                               │
│ Selected: 2 of 3 fights                                      │
│                                                               │
│ Report Type:                                                 │
│ ( ) Single Matchup (one PDF per fight)                      │
│ (*) Event Card (bundle by event)                            │
│                                                               │
│ [ ] Operator Approval Required                              │
│     (check to confirm PDF generation)                       │
│                                                               │
│ Ready to generate 2 PDFs                                    │
│                                                               │
│                         [Generate & Export] (disabled)      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### When Results Display
```
AI-RISA Premium Report Factory

┌──────────────────────────────────────────────────────────────┐
│ Generate Premium PDF Reports — Export Complete [← Back]      │
│                                                               │
│ ✓ Successfully generated 2 PDFs:                             │
│                                                               │
│ ✓ ai_risa_premium_report_EVT-001_MID-001_20260501.pdf (3KB) │
│ ✓ ai_risa_premium_report_EVT-001_MID-002_20260501.pdf (3KB) │
│                                                               │
│ Total: 2 files, 6 KB                                         │
│                                                               │
│ [Copy All Paths]  [Open Folder]  [Generate More]           │
│                                                               │
│ [Return to Main Dashboard]                                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. Technical Constraints

### Phase 3 Engine — Use As-Is
✓ DO use existing:
- `prf_report_builder.py` orchestrator
- `prf_report_export.py` PDF writer (fpdf2)
- `prf_report_content.py` section assembly
- `/api/premium-report-factory/reports/generate` endpoint
- Phase 3 tests (all passing, 16/16)

✗ DO NOT:
- Modify PDF generation logic
- Add new report sections
- Change filenames or output format
- Add result lookup
- Add learning/calibration
- Add billing automation
- Add web discovery
- Modify approval gate logic

### UI Changes Only
**Scope:** Dashboard HTML/CSS/JavaScript

**What Changes:**
- Main dashboard layout (add Button 2 button)
- Button 2 click handler (show selection panel)
- Fight selection UI (checkboxes, counts)
- Approval checkbox validation
- Results display panel

**What Stays the Same:**
- Backend endpoint unchanged
- PDF generation unchanged
- Queue data unchanged
- Advanced Dashboard unchanged (internal tools)
- All Phase 1/2/3 code unchanged

### No New Data Collection
- Reuse saved fights from Button 1 queue
- Reuse readiness ranking (if available from Phase 3)
- No new fields
- No new database tables
- No new API endpoints

---

## 6. Current Build Status After This Slice

| Component | Status | Notes |
|-----------|--------|-------|
| Phase 3 PDF engine | ✓ Works | No changes needed |
| Backend endpoint | ✓ Works | No changes needed |
| Main dashboard layout | ⏳ To build | Add Button 2 button |
| Button 2 selection panel | ⏳ To build | Checkboxes + counts |
| Button 2 approval logic | ⏳ To build | Validation + enable/disable |
| Button 2 results display | ⏳ To build | File paths + copy/open actions |
| Advanced Dashboard | ✓ Unchanged | Internal tools untouched |

**After This Slice:**
- Main dashboard shows clean 3-button interface
- Button 2 generates PDFs with idiot-proof UI
- Commercial ready for immediate use (Phase 3 baseline + Button 2 UI)

---

## 7. Implementation Strategy

### Slice Type
**UI-only design & implementation.** No backend changes.

### Files to Modify
1. `operator_dashboard/templates/advanced_dashboard.html` — Add/move Button 2 main dashboard button
2. `operator_dashboard/static/css/dashboard.css` (if needed) — Style Button 2 on main dashboard
3. `operator_dashboard/templates/main_dashboard.html` (or create new) — Button 2 workflow panels
4. JavaScript handlers (inline or separate) — Click handlers, validation, API calls

### Files to Create
- None (reuse Phase 3 UI components where possible)

### Files NOT to Touch
- All Python backend files (unchanged)
- Phase 1/2/3 code (unchanged)
- Test files (unchanged)
- API endpoints (unchanged)
- Queue logic (unchanged)

### Testing Strategy
After implementation:
- Verify Phase 3 PDF tests still pass (16/16)
- Verify main dashboard button is visible and enabled/disabled correctly
- Manual test: Select fights → Approve → Generate → Verify files created
- Manual test: Check approval checkbox requirement works
- Manual test: Verify results display shows correct filenames and paths

---

## 8. Non-Goals

✗ DO NOT:
- Implement result lookup (Button 3)
- Implement result comparison (Button 3)
- Add learning/calibration (Button 3)
- Modify Button 1 (Find & Build remains unchanged)
- Add auto-web discovery
- Add billing automation
- Add global ledger
- Modify fighter profiles
- Change PDF content or format
- Add new sections to reports
- Implement Phase 4 behavior

**Scope:** Button 2 UI simplification only. Use existing Phase 3 engine.

---

## 9. Success Criteria

**Button 2 slice is complete when:**

1. ✓ Main dashboard shows "Generate Premium PDF Reports" button
2. ✓ Button is enabled only when saved fights exist
3. ✓ Clicking button shows fight selection panel
4. ✓ Operator can select one/many/all fights
5. ✓ Operator can choose report type (single/event)
6. ✓ Approval checkbox is required and validated
7. ✓ "Generate & Export" button only enables when fights + approval checked
8. ✓ Clicking "Generate & Export" calls Phase 3 API
9. ✓ Results display shows file paths, sizes, and error messages
10. ✓ Phase 3 PDF tests still pass (16/16)
11. ✓ Manual generation produces correct PDFs with correct filenames
12. ✓ Approval gate is enforced (no PDF generation without approval)
13. ✓ All existing Phase 1/2/3 code unchanged
14. ✓ All existing tests passing

---

## 10. Implementation Blockers

**None identified.**

- Phase 3 engine works perfectly
- Backend endpoint is ready
- No design conflicts
- UI is straightforward
- Approval gate pattern is established
- Can start implementation immediately

---

## 11. Next Steps After This Slice

**After Button 2 is complete:**

1. **Commercial readiness achieved** — 3-button main dashboard with working PDF generation
2. **Begin Button 1 enhancement** — Add auto-discovery + readiness ranking
3. **Begin Button 3 implementation** — Add result search + comparison + learning (most complex)

---

## Document Metadata

| Key | Value |
|-----|-------|
| Slice | Button 2 Main Dashboard UI Simplification |
| Phase | Design (docs-only) |
| Created | 2026-05-01 |
| Status | Ready for Implementation |
| Files to Modify | HTML/CSS/JS only (no backend changes) |
| Files to Create | None (reuse Phase 3 components) |
| Phase 3 Changes | Zero (use as-is) |
| Testing | Verify Phase 3 tests pass + manual UI testing |
| Blocking Issues | None |

---

## Design Review Checklist

- ✓ Scope clearly defined (UI simplification only)
- ✓ Current state documented (Phase 3 engine works)
- ✓ Target state documented (idiot-proof main dashboard button)
- ✓ UI flows specified (selection → approval → generation → results)
- ✓ Approval gate enforced (checkbox requirement)
- ✓ Non-goals stated (no result lookup, learning, discovery, billing)
- ✓ Implementation strategy clear (HTML/CSS/JS only)
- ✓ Success criteria defined (14 checkpoints)
- ✓ No blocking issues
- ✓ Ready to implement

---

**End of Design Document**

**Next Action:** Lock this design via commit/tag, then begin implementation of Button 2 UI.

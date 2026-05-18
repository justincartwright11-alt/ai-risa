# AI-RISA Premium Report Factory — Three-Button Dashboard Design v1

**Document Type:** Product Surface Design (Docs-Only)  
**Date:** 2026-05-01  
**Status:** Approved Design, Ready for Implementation Slices  
**Revision:** v1

---

## 1. Product Purpose

**Product Name:** AI-RISA Premium Report Factory

**Mission:**  
Deliver a final sellable operator dashboard that enables a single operator to find, build, generate, validate, and improve fight intelligence at commercial scale—without requiring software engineering, database management, or API integration knowledge.

**Core Value:**
- Automatic search, collection, and analysis allowed
- Operator approval required for permanent writes, customer outputs, and learning updates
- Auditable control gates on all significant actions
- Simple enough for a non-technical operator to run alone

---

## 2. Main Dashboard Rule

**The Surface:**
Only **three primary buttons** visible on the main dashboard.

**Everything Else:**
All advanced tools, internal diagnostics, configuration, v100 research, and debugging moves to the **Advanced Dashboard** (separate navigation path).

**Layout:**
```
AI-RISA Premium Report Factory

┌─────────────────────────────────────────────────────────────┐
│ 1. Find & Build Fight Queue                                 │
│ [Auto-discover, manual input, review, approve, save queue]  │
│                                                               │
│ 2. Generate Premium PDF Reports                             │
│ [Select fights, approve, export customer PDFs]              │
│                                                               │
│ 3. Find Results & Improve Accuracy                          │
│ [Search results, compare, approve, update learning]         │
│                                                               │
│ [Advanced Dashboard →]  [About →]                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Button 1: Find & Build Fight Queue

**What the operator sees:**
A simple workflow to discover upcoming fights and build a queue ready for report generation.

### 3.1 Automatic Web Discovery

**Capability:**  
AI-RISA automatically searches official-source boxing websites, promoter announcements, and event databases for upcoming event cards and matchups.

**Scope:**
- Weekly/upcoming event cards
- Scheduled bout information
- Fighter names, weights, records, styles
- Event dates and venues

**Approval Gate:**  
Auto-search is **allowed without approval**. Results shown in review window.

### 3.2 Manual Input

**Capability:**  
Operator can paste event cards, write matchups freeform, or upload CSV/JSON fight data.

**Formats:**
- Paste raw event card text
- Type `Fighter A vs Fighter B` freeform
- Upload structured data (CSV/JSON)
- Copy/paste from social media, promoter sites

**Approval Gate:**  
Manual input is **allowed without approval**. Results shown in review window.

### 3.3 Fight Extraction & Analysis

**What happens:**
1. AI-RISA extracts fighter names, matchups, and event data
2. Analyzes "report readiness" for each fight:
   - Fighter data quality
   - Record completeness
   - Historical style info available
   - Injury/conditioning info available
3. Ranks fights by readiness level (Ready / Partial / Needs More Data)
4. Shows analysis summary

**Approval Gate:**  
Analysis is **allowed without approval**. Results shown in review window.

### 3.4 Review Window

**What the operator sees:**
- All discovered + manually entered fights
- Extraction status (✓ extracted, ⚠ partial, ✗ failed)
- Report readiness ranking
- Quick preview of available fighter data
- Checkbox to select one/many/all fights

**Operator actions:**
- Read through the list
- Select fights to save
- Reject/delete individual fights
- Edit fighter names or matchup details

### 3.5 Operator Approval

**Prompt:**  
"Approve saving these selected fights to the queue?"

**What operator must confirm:**
- Count of fights to save
- Selected event card(s)
- Consequence: These fights will be saved to the database and available in Button 2

### 3.6 Database/Queue Save

**Only after approval:**  
1. Selected fights written to global database
2. Fights appear in Button 2 (Generate PDFs)
3. Fights available for Button 3 (result comparison)
4. Save action logged with timestamp and operator ID

**Approval Gate:**  
Save to database is **only after operator approval**.

---

## 4. Button 2: Generate Premium PDF Reports

**What the operator sees:**
A simple workflow to generate and export customer-ready AI-RISA premium fight intelligence PDFs.

### 4.1 Fight Selection

**What the operator selects:**
- Individual fighter matchup from saved queue
- Multiple matchups from an event card
- Entire event card (all fights)

**Data Source:**
- Only from fights saved in Button 1 (post-approval)
- No automatic web lookup in this button
- No result lookup in this button
- Only analysis, not real results

### 4.2 Report Type

**Options:**
- Single matchup report (Fighter A vs Fighter B)
- Event card report (all fights in one card, multi-page)

### 4.3 Operator Approval

**Prompt:**  
"Approve generation and export of [N] premium PDF reports?"

**What operator must confirm:**
- Count of reports
- Report type (single/event)
- Consequence: Reports will be generated and exported for customer delivery

### 4.4 Automatic Generation

**Only after approval:**  
1. AI-RISA generates customer-ready PDF for each selected fight
2. PDF includes:
   - 14 standard sections (Cover, Executive Summary, Decision Structure, etc.)
   - Deterministic filename: `ai_risa_premium_report_{event_id}_{matchup_id}_{YYYYMMDD}.pdf`
   - Analysis only (no real results, no learning markers)
3. Files written to export directory
4. Generation action logged with timestamp and operator ID

### 4.5 Export Results

**Operator sees:**
- Count of successfully generated PDFs
- Filenames and paths
- File sizes
- Any errors or failed exports
- Download/copy buttons for each file

**Approval Gate:**  
PDF generation and export is **only after operator approval**.

### 4.6 Constraints

**What this button does NOT do:**
- Does not look up real-life results
- Does not compare analysis to actual outcomes
- Does not update accuracy tracking
- Does not trigger learning/calibration updates
- Does not create billing records
- Does not access global ledger
- Does not modify fighter profiles
- Reports contain analysis only, not real results

---

## 5. Button 3: Find Results & Improve Accuracy

**What the operator sees:**
A workflow to find official fight results, compare against AI-RISA analysis, and approve learning/calibration updates.

### 5.1 Automatic Result Search

**Capability:**  
AI-RISA automatically searches official boxing databases, promoter results, and public record sources for fight outcomes.

**Scope:**
- Official fight results (winner, method, round)
- Ringside reports
- Judge scorecards
- Referee reports
- Public records

**Approval Gate:**  
Auto-search is **allowed without approval**. Results shown in review window.

### 5.2 Manual Result Input

**Capability:**  
Operator can paste real results, type outcome freeform, or upload result data.

**Formats:**
- Paste official result text
- Type `Winner: Fighter A, Method: KO Round 3` freeform
- Upload structured result data (CSV/JSON)
- Copy/paste from boxing news sites

**Approval Gate:**  
Manual input is **allowed without approval**. Results shown in review window.

### 5.3 Result Matching

**What happens:**
1. AI-RISA matches discovered/entered results to saved fights
2. Links each result to the corresponding analysis/report from Button 2
3. Shows match confidence (✓ exact match, ⚠ fuzzy match, ✗ no match)
4. Allows operator to manually confirm or correct matches

### 5.4 Automatic Comparison

**What AI-RISA compares:**
- Real outcome vs AI-RISA prediction
- Real method vs predicted outcome method
- Real round vs predicted outcome round
- Fighter performance vs predicted conditioning/energy use
- Actual strategy vs predicted decision structure
- Actual mistakes vs predicted vulnerability/collapse points

**Approval Gate:**  
Comparison is **allowed without approval**. Results shown in review window.

### 5.5 Accuracy Review Window

**What the operator sees:**

#### Per-Fight Accuracy:
- Single fighter accuracy: Did AI-RISA predict this fighter's performance correctly?
- Matchup accuracy: Did AI-RISA predict the outcome of Fighter A vs Fighter B correctly?
- Prediction details:
  - Predicted outcome: [Fighter A wins / Fighter B wins / Draw]
  - Actual outcome: [same format]
  - Match: ✓ Yes / ✗ No
  - Confidence delta: [percentage points]

#### Event-Card Accuracy:
- Event accuracy: Of N fights in this card, how many did AI-RISA predict correctly?
- Card summary: M/N fights correct (X%)

#### Segment Accuracy:
- Decision structure accuracy: How often did AI-RISA predict the actual decision method?
- Energy use accuracy: How often did predicted energy dynamics match actual performance?
- Fatigue accuracy: How often did predicted fatigue points match where fighter failed?
- Mental condition accuracy: How often did predicted mental state predict actual decision?
- Collapse trigger accuracy: How often did predicted collapse points match actual problems?
- Deception accuracy: How often did predicted deception/unpredictability match actual tactics?
- Strategy accuracy: How often did predicted control shifts match actual round-by-round performance?

#### Total AI-RISA Accuracy:
- Historical average across all fights analyzed to date
- Current session accuracy
- Trend (improving/stable/declining)

### 5.6 Operator Approval

**Prompt:**  
"Approve applying these results and updating AI-RISA learning/calibration?"

**What operator must confirm:**
- Count of fights with new results
- Accuracy deltas (new accuracy data)
- Learning scope (which segments to update)
- Consequence: AI-RISA will update its calibration database with these results

### 5.7 Learning/Calibration Update

**Only after approval:**  
1. AI-RISA records actual outcomes against predictions
2. Recalculates accuracy metrics per fighter, per segment
3. Updates:
   - Single fighter accuracy
   - Matchup accuracy
   - Segment accuracy (decision structure, energy, fatigue, mental, collapse, deception, strategy)
   - Total AI-RISA accuracy
4. Learning action logged with timestamp, operator ID, and results applied
5. Updates do not modify fighter profiles or global ledger yet (Phase 5+)

**Approval Gate:**  
Learning/calibration update is **only after operator approval**.

### 5.8 Constraints

**What this button does NOT do:**
- Does not modify fighter profiles (Phase 5+)
- Does not write to global result ledger (Phase 5+)
- Does not modify billing records
- Does not trigger automatic re-analysis
- Does not change saved reports retroactively
- Only updates accuracy/calibration metrics

---

## 6. Governance Model

### 6.1 Core Rule

```
AI-RISA may search, collect, compare, generate, save, and learn automatically.

But permanent database writes, customer PDFs, and learning/calibration 
updates must pass through an operator approval gate.
```

### 6.2 Automatic Capabilities (No Approval Required)

- Web discovery of upcoming fights
- Web discovery of real-life results
- Analysis and ranking of report readiness
- Comparison of analysis to real outcomes
- Calculation of accuracy metrics
- Display of all intermediate results in review windows

### 6.3 Approval-Gated Capabilities (Require Operator Approval)

| Action | Approval Required | Consequence |
|--------|------------------|-------------|
| Save fights to database | Yes | Fights appear in Button 2 |
| Generate/export customer PDFs | Yes | PDFs delivered to customer |
| Update learning/calibration | Yes | AI-RISA improves from results |

### 6.4 Audit Trail

**Every approval must log:**
- Timestamp
- Operator ID (if available)
- Action taken (save / export / learn)
- Count of items affected
- Brief summary of content

**Queries:**
- "Show me all PDFs generated on [date]"
- "Show me all fights saved by operator [ID]"
- "Show me all learning updates applied"
- "Show me the approval history for fight [ID]"

### 6.5 No Hidden Automation

- No automatic writes without visible approval prompt
- No background learning without operator awareness
- No silent data collection
- No billing automation
- All actions user-initiated or explicitly logged

---

## 7. Current Build Status

### Button 1: Find & Build Fight Queue
- **Manual paste + queue save:** ✓ Implemented (Phase 2)
- **Automatic web discovery:** ✗ Not built (needs design/implementation)
- **Report readiness ranking/analysis:** ✗ Not built (needs design/implementation)
- **Review window UI:** ⚠ Partial (basic queue preview exists, needs enhancement)
- **Global database save:** ✓ Basic implementation exists (needs approval gate review)

### Button 2: Generate Premium PDF Reports
- **PDF generation from saved queue:** ✓ Implemented (Phase 3)
- **Select fights UI:** ⚠ Partial (advanced dashboard has selection, needs main dashboard simplification)
- **Generate/export:** ✓ Implemented (Phase 3)
- **File path display:** ✓ Implemented (Phase 3)
- **Main dashboard button simplification:** ✗ Not done (currently buried in advanced dashboard)

### Button 3: Find Results & Improve Accuracy
- **Result search/input:** ✗ Not built
- **Result matching:** ✗ Not built
- **Comparison logic:** ✗ Not built
- **Accuracy metrics display:** ✗ Not built
- **Learning/calibration update:** ✗ Not built

---

## 8. Advanced Dashboard Boundary

**Advanced Dashboard contains all non-primary-workflow tools:**

### Diagnostics & Debugging
- Event queue internals (raw JSON, debug views)
- Report generation logs
- Search result raw data
- Comparison result debugging
- Accuracy calculation trace

### Configuration & Administration
- Global database settings
- v100 calibration parameters
- Fighter profile database access
- API key management
- Export directory configuration

### Calibration Internals
- Segment accuracy history
- Fighter accuracy profiles
- Matchup accuracy matrix
- Learning log viewer
- Calibration rollback/reset

### Manual Overrides
- Force save a fight without auto-analysis
- Force generate a report without approval (operator password)
- Force apply a result without review window
- Manually edit fighter data
- Manually adjust accuracy metrics

### v100 Research Tools
- Method pathway analysis
- Scenario tree modeling
- Decision structure deep-dive
- Energy use modeling parameters
- Fatigue/collapse prediction debugging
- Deception/unpredictability analysis tools
- Control shift analysis
- Accuracy trending dashboard

### Developer & Operator Debugging
- Full API endpoint testing
- Request/response inspection
- Token generation and validation
- Search result raw data
- Database query interface
- Error logs and stack traces

**Access Rule:**  
Advanced Dashboard visible only to operator, behind "Advanced Dashboard" button on main interface.

---

## 9. AI-RISA v100 Alignment

**Two-Track Architecture:**

### Track 1: Premium Report Factory (This Design)
- Sells the output (premium PDFs)
- Operator-approved automation gates
- Customer-facing interface
- Revenue generation
- Commercial liability boundary

### Track 2: AI-RISA v100 Core (Long-Term Improvement)
- Improves the intelligence underneath
- 10 core v100 research priorities
- Accuracy and calibration enhancement
- Method and scenario modeling
- Global knowledge layer (Phase 5+)

**Design Constraint:**
This dashboard design must **not block** future v100 improvements:
- Segment accuracy can expand as v100 adds new segments
- Learning updates can include new calibration vectors
- Fighter profile enhancements don't break operator workflow
- Global ledger integration (Phase 5) doesn't change operator approvals

---

## 10. Non-Goals

**What this design explicitly does NOT do:**

- ✗ No implementation code
- ✗ No endpoint changes
- ✗ No UI patches or CSS changes
- ✗ No automatic write without approval prompt
- ✗ No hidden learning
- ✗ No billing automation
- ✗ No uncontrolled web automation
- ✗ No modification of existing Phase 1/2/3 code
- ✗ No test changes
- ✗ No runtime file creation
- ✗ No global ledger in Phase 4 (reserved for Phase 5)
- ✗ No fighter profile modification in Phase 4 (reserved for Phase 5+)

---

## 11. Final Design Verdict

**Status:** ✓ **Approved as Docs-Only Product Surface Design**

**What This Design Establishes:**
1. Final operator workflow (3 buttons, clear approval gates)
2. Feature scope for each button (what happens, what doesn't)
3. Approval gates (when operator must confirm)
4. Audit trail requirements
5. Advanced Dashboard boundary
6. v100 alignment and constraints
7. Non-implementation contract

**What This Design Does NOT:**
1. Implement any code
2. Modify any endpoints
3. Create any UI changes
4. Execute any logic
5. Create runtime files
6. Commit Phase 4 work

**Next Safe Steps:**

After this design is locked via commit/tag, proceed with **separate implementation slices**:

1. **Slice 1A:** Button 1 — Auto-discovery and ranking (design → implementation)
2. **Slice 1B:** Button 1 — Review window UI enhancement (design → implementation)
3. **Slice 2:** Button 2 — Main dashboard button simplification (design → implementation)
4. **Slice 3:** Button 3 — Result search and matching (design → implementation)
5. **Slice 4:** Button 3 — Comparison and accuracy display (design → implementation)
6. **Slice 5:** Button 3 — Learning/calibration update flow (design → implementation)

Each slice: design-locked → implementation → tests → validation → commit/tag.

**Governance Constraint:**
All implementation slices must respect operator approval gates defined in this design.

---

## Document Metadata

| Key | Value |
|-----|-------|
| Product | AI-RISA Premium Report Factory |
| Design Version | v1 |
| Document Type | Product Surface Design (Docs-Only) |
| Created | 2026-05-01 |
| Status | Approved, Ready for Implementation Slices |
| Scope | 3-button main dashboard + Advanced Dashboard boundary |
| Implementation Blocked Until | Design review passed (this document) |
| Next Phase | Separate implementation slices per button |
| Review Required | No further design review needed; implementation slices will validate |

---

## Appendix: Operator Approval Gate Checklist

Use this checklist to validate implementation:

### Button 1 Approval Gate
- [ ] "Approve saving these fights?" prompt shown
- [ ] Count of fights displayed
- [ ] Event card(s) identified
- [ ] Operator must click "Approve" button
- [ ] Only after click: database save executed
- [ ] Action logged with timestamp and operator ID

### Button 2 Approval Gate
- [ ] "Approve PDF generation?" prompt shown
- [ ] Count of PDFs displayed
- [ ] Report types shown
- [ ] Operator must click "Approve" button
- [ ] Only after click: export executed
- [ ] Action logged with timestamp and operator ID

### Button 3 Approval Gate
- [ ] "Approve learning update?" prompt shown
- [ ] Count of results to apply
- [ ] Accuracy deltas displayed
- [ ] Segments to update shown
- [ ] Operator must click "Approve" button
- [ ] Only after click: calibration update executed
- [ ] Action logged with timestamp and operator ID

---

**End of Design Document**

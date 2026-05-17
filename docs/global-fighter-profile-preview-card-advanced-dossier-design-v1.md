# Advanced Fighter Intelligence Dossier Card — Design Lock

**Date:** May 17, 2026  
**Status:** DESIGN LOCK (docs-only)  
**Revision:** v1

---

## Overview

The Advanced Fighter Intelligence Dossier expands the read-only fighter profile preview card with richer context from multiple data sources. It remains display-only and respects the zero-mutation governance constraint.

**Foundation:** [global-fighter-record-profile-preview-card-v1](../operator_dashboard/templates/index.html) (commit a922300)

**Core Rule (ENFORCED):**
> AI-RISA may preview fighter profile intelligence.  
> AI-RISA may not create, update, merge, rank, or write fighter profiles.

---

## What Changes vs. Profile Preview Card

### Profile Preview Card (CURRENT)
```
Display-only fighter intelligence from sanitized known-records only.

6 sections:
- Header (name + confidence grade)
- Identity (aliases, nationality)
- Context (promotion, division, ruleset)
- Physical (stance, height, reach)
- Record (W-L-D format + active years)
- Footer (read-only warning)

Data sources:
- sanitized known_records loader

Safety:
- All write flags false
- No form inputs
- No action buttons
- No API mutations
```

### Advanced Dossier Card (NEW)
```
Richer fighter intelligence from multiple sanitized data sources.

9-12 sections (expandable):
- Header (name + confidence grade + metadata badge)
- Identity (aliases, nationality, legacy names)
- Context (promotion, division, ruleset, weight class)
- Physical (stance, height, reach, reach advantage calc)
- Record (W-L-D format + active years + record breakdown by year)
- Performance Trends (peak years, record by division, record by opponent type)
- Report History (references to available AI-RISA reports)
- Result Context (recent opponent records, result patterns)
- Analysis Summary (key observations from reports, NOT rankings)
- Reliability Indicators (confidence grade + sources used + data recency)
- Footer (read-only warning + data source attribution)

Data sources:
- sanitized known_records loader (fighter identity + record)
- projection_ledger_readonly (field calculations + confidence)
- report_history_reference (which reports analyze this fighter)
- result_ledger_reference (recent results + opponent records)

Safety:
- All write flags remain false
- No form inputs
- No action buttons
- No mutations of any kind
- No ranking writes
- No profile writes
- No result writes
```

---

## Data Sources (Sanitized, Read-Only)

### 1. **Known Records Loader** (existing)
```json
{
  "full_name": "Anderson Silva",
  "known_aliases": ["Spider", "Demigod"],
  "nationality": "Brazil",
  "promotion": "UFC",
  "division": "Middleweight",
  "sport_ruleset": "MMA",
  "stance": "Orthodox",
  "height": "6'2\"",
  "reach": "77\"",
  "record": "34W-11L-0D",
  "active_years": [1997, 2024],
  "confidence_grade": "A",
  "loader_source_type": "official"
}
```

### 2. **Projection Ledger (Read-Only Adapter)**
```json
{
  "fighter_id": "Anderson Silva",
  "projection_confidence": "A",
  "field_calculations": {
    "reach_advantage_vs_middleweight_avg": "+3.0 inches",
    "stance_prevalence_in_division": "20.5%",
    "record_strength_vs_ranked_opponents": "22W-8L-0D (73.3%)"
  },
  "projection_source": "projection_ledger_readonly_adapter",
  "projection_recency": "2026-05-17"
}
```

### 3. **Report History Reference** (read-only catalog)
```json
{
  "fighter_id": "Anderson Silva",
  "report_references": [
    {
      "report_id": "nikita-tszyu-vs-oscar-diaz-v4",
      "report_title": "Nikita Tszyu vs Oscar Diaz - Premium Analysis v4",
      "mentions_this_fighter": "opponent_context",
      "report_status": "published",
      "reference_type": "opponent_record_context"
    },
    {
      "report_id": "anderson-silva-prime-years-analysis",
      "report_title": "Anderson Silva Prime Years Analysis",
      "mentions_this_fighter": "primary_subject",
      "report_status": "draft",
      "reference_type": "primary_analysis"
    }
  ],
  "total_reports_mentioning": 5,
  "total_reports_as_primary": 2
}
```

### 4. **Result Ledger Reference** (read-only history)
```json
{
  "fighter_id": "Anderson Silva",
  "recent_results": [
    {
      "date": "2024-04-13",
      "opponent": "opponent_name",
      "opponent_record_at_time": "12W-3L-0D",
      "result": "Win",
      "result_source": "official_record",
      "time_in_fight": "5:32 R2 (submission)"
    }
  ],
  "result_patterns": {
    "finish_rate": "58.8%",
    "submission_rate": "35.3%",
    "ko_tko_rate": "23.5%",
    "decision_rate": "41.2%"
  },
  "record_by_opponent_caliber": {
    "vs_top_10": "18W-7L",
    "vs_ranked": "22W-8L",
    "vs_unranked": "12W-3L"
  }
}
```

---

## Data Flow & Integration

### **Loading Sequence**
1. User opens Button 1 discovery workflow
2. Known records loaded (sanitized) ✅
3. Projection ledger adapter called for field calculations ✅
4. Report history reference fetched (read-only catalog) ✅
5. Result ledger reference fetched (read-only history) ✅
6. Advanced dossier cards rendered with all 4 data sources
7. Cards display ONLY (no mutations, no writes)

### **Error Handling**
- Missing known_record → Show "Unknown Fighter" card (header + footer)
- Missing projection_ledger → Show fields as "Not calculated" (graceful)
- Missing report_history → Show "No reports available" (graceful)
- Missing result_ledger → Show "No result history available" (graceful)

### **Timeout Strategy**
- Known records load: <500ms (critical path)
- Projection ledger: <1000ms (defer if timeout)
- Report history: <2000ms (defer if timeout, show "loading...")
- Result ledger: <2000ms (defer if timeout, show "loading...")

If any data source times out, cards render with available data only (fail-safe).

---

## Layout & Sections

### **Advanced Dossier Card Structure**

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                      │
│ [Grade A] Anderson Silva · Born 1975 · Brazil             │
│                                                             │
│ IDENTITY                                                    │
│ Aliases: Spider, Demigod                                   │
│ Full Record: Anderson Luis da Silva de Freitas            │
│                                                             │
│ CONTEXT                                                     │
│ Promotion: UFC │ Division: Middleweight                   │
│ Ruleset: MMA (5oz gloves) │ Weight Class: 185 lbs         │
│                                                             │
│ PHYSICAL                                                    │
│ Stance: Orthodox │ Height: 6'2" │ Reach: 77"             │
│ Reach Advantage: +3.0" vs MW avg │ Stance: 20.5% in div  │
│                                                             │
│ RECORD                                                      │
│ Overall: 34W-11L-0D (75.6%)                              │
│ Active: 1997–2024 (27 years)                             │
│ vs Top 10: 18W-7L (72%)                                   │
│ vs Ranked: 22W-8L (73.3%)                                │
│ vs Unranked: 12W-3L (80%)                                │
│                                                             │
│ PERFORMANCE TRENDS                                         │
│ Peak Years: 2004-2013 (W-L by year chart reference)      │
│ By Division: MW 30W-9L · LHW 4W-2L                       │
│ Finish Rate: 58.8% (35.3% submissions, 23.5% KO/TKO)    │
│                                                             │
│ REPORT HISTORY                                             │
│ 5 reports mention this fighter                             │
│ 2 reports with this as primary subject                    │
│ Latest: Anderson Silva Prime Years Analysis (draft)       │
│ ⚠ Note: Reports are preview references only, not live     │
│                                                             │
│ RESULT CONTEXT                                             │
│ Recent Result: W vs [opponent] (12W-3L) · 4/13/24        │
│ Last 5: 4W-1L (recent form trending positive)           │
│ Opponent Record Pattern: 18W-7L vs top caliber           │
│                                                             │
│ ANALYSIS SUMMARY                                           │
│ Notable: Elite-level record across 27 years in combat     │
│ Context: Confidence Grade A from sanitized known-records  │
│ Data Recency: 2026-05-17                                  │
│ ⚠ This is preview intelligence only. Not a ranking.      │
│                                                             │
│ RELIABILITY INDICATORS                                      │
│ Confidence Grade: A (official_record source)              │
│ Sources: known_records + projection_ledger + report_hist  │
│ Data Verified: 2026-05-17 (0 days stale)                 │
│                                                             │
│ READ-ONLY WARNING (FOOTER)                                 │
│ ⚠ Read-only fighter intelligence reference only.          │
│ No profile create/update/merge. No ranking or writes.     │
│ For analysis and context only. Not for decisions.         │
└─────────────────────────────────────────────────────────────┘
```

### **Section Definitions**

| Section | Source | Display | Purpose |
|---------|--------|---------|---------|
| Header | known_records | Name, confidence grade, birth year, nationality | Quick identification |
| Identity | known_records | Legal name, aliases, full registrations | Disambiguate fighters |
| Context | known_records + projection | Promotion, division, ruleset, weight class | Fighter classification |
| Physical | known_records + projection | Stance, height, reach, reach calculations | Physical attributes |
| Record | known_records + projection | W-L-D, active years, record by opponent caliber | Performance snapshot |
| Trends | projection_ledger + result_ledger | Peak years, by division, finish rates | Career patterns |
| Report History | report_history_reference | Count, titles, status, subject role | Available context |
| Result Context | result_ledger_reference | Recent results, opponent records, patterns | Recent activity |
| Analysis Summary | all sources | Key observations (NOT rankings) | Interpretive summary |
| Reliability | all sources | Confidence grade, sources, recency | Trust indicators |
| Footer | implementation | Read-only warning, source attribution | Safety reminder |

---

## Safety Perimeter (FROZEN)

### **What IS Allowed**
✅ Display fighter intelligence from 4 sanitized data sources  
✅ Show confidence grades and data recency  
✅ Reference report titles and subject roles  
✅ Show opponent record patterns and trends  
✅ Calculate and display reach advantages  
✅ Show record breakdowns by opponent caliber  
✅ Render HTML with escaped values (XSS-safe)  
✅ Handle missing data gracefully (fail-safe)  

### **What IS NOT Allowed**
❌ Create fighter profiles  
❌ Update fighter profiles  
❌ Merge fighter records  
❌ Rank fighters by confidence  
❌ Write to profile database  
❌ Write to ranking database  
❌ Write to result ledger  
❌ Write to report ledger  
❌ Write to learning/calibration database  
❌ Add form inputs to cards  
❌ Add action buttons to cards  
❌ Add onclick handlers that mutate  
❌ Call any mutation endpoints  
❌ Apply learning or calibration updates  
❌ Modify queue or fight order  

### **Write Flags (ALL REMAIN FALSE)**
```
profile_create_performed = false (LOCKED)
profile_update_performed = false (LOCKED)
merge_performed = false (LOCKED)
database_write_performed = false (LOCKED)
ranking_write_performed = false (LOCKED)
result_write_performed = false (LOCKED)
report_write_performed = false (LOCKED)
learning_apply_performed = false (LOCKED)
calibration_write_performed = false (LOCKED)
```

### **No Write Endpoints Called**
- No `/create-profile` ❌
- No `/update-profile` ❌
- No `/merge-profile` ❌
- No `/save-ranking` ❌
- No `/write-result` ❌
- No `/write-report` ❌
- No `/apply-learning` ❌

---

## Implementation Constraints

### **No Changes to Existing Safety**
- Profile preview card remains UNCHANGED
- Button 1 flow structure remains UNCHANGED
- Gate 1 blockers remain UNCHANGED
- Dashboard shape (3 buttons / 3 gates) remains UNCHANGED
- All existing write flags remain false

### **Code Quality**
- All field values HTML-escaped (XSS prevention)
- All null/undefined handled with "Not available" fallback
- Error responses hardcoded with write flags = false
- Card rendering pure display (returns HTML string only)
- No async side effects in rendering functions

### **Performance**
- Card rendering: <500ms
- Report history load: <2000ms (deferrable)
- Result ledger load: <2000ms (deferrable)
- Timeout on any data source: graceful degradation

### **Testing Requirements** (Future)
- 15+ unit tests for data display correctness
- 8+ tests for missing field handling
- 6+ tests for timeout/error handling
- 10+ tests for XSS prevention on new fields
- 5+ tests for new data source integration
- Integration tests with Button 1 flow

---

## Integration Points

### **Button 1 Discovery Workflow**
```
1. User initiates Button 1
2. Workflow preview requested
3. Known records loaded (existing)
4. Projection ledger adapter called (NEW)
5. Report history reference loaded (NEW)
6. Result ledger reference loaded (NEW)
7. Advanced dossier cards rendered with all 4 sources
8. User reviews cards (display-only, no controls)
9. User approves selection
10. [OPERATOR APPROVAL GATE] triggered
11. Save to queue (separate flow, after approval)
```

**Key:** Dossier cards are display-only. They do NOT trigger saves or profile operations. Saves happen in separate operator-approval flow, AFTER cards are reviewed.

### **Data Source Calls**
```javascript
// Existing calls (unchanged)
postGlobalFighterKnownRecordsLoaderPreview(candidates)
postGlobalFighterIdentityResolverPreview(payload)

// New calls (for dossier)
postGlobalFighterProjectionLedgerReadonlyPreview(fighters)
postGlobalFighterReportHistoryReferencePreview(fighters)
postGlobalFighterResultLedgerReferencePreview(fighters)
```

### **New API Contracts** (preview-only)
```json
// /api/global-fighters/projection-ledger/readonly-preview
{
  "ok": true,
  "fighter_projections": [
    {
      "fighter_id": "anderson-silva",
      "projection_confidence": "A",
      "field_calculations": {...},
      "profile_create_performed": false,
      "database_write_performed": false
    }
  ]
}

// /api/global-fighters/report-history/reference-preview
{
  "ok": true,
  "report_references": [
    {
      "fighter_id": "anderson-silva",
      "report_references": [...],
      "database_write_performed": false
    }
  ]
}

// /api/global-fighters/result-ledger/reference-preview
{
  "ok": true,
  "result_references": [
    {
      "fighter_id": "anderson-silva",
      "recent_results": [...],
      "result_patterns": {...},
      "database_write_performed": false
    }
  ]
}
```

---

## Design Decisions & Rationale

### **Why Read-Only Display Only?**
The advanced dossier must remain display-only to respect the core governance rule. No form inputs, buttons, or mutations allowed. This keeps the feature focused on **intelligence preview**, not **profile management**.

### **Why 4 Data Sources?**
1. **Known records** — Fighter identity & official record
2. **Projection ledger** — Field calculations & confidence improvements
3. **Report history** — Context on available analysis & coverage
4. **Result ledger** — Recent activity & opponent patterns

These 4 sources provide rich context without requiring new write operations.

### **Why Reference Report History Instead of Embedding Reports?**
Embedding full report content in dossier cards would:
- Create dependency on report rendering
- Increase payload size
- Risk stale report references
- Complicate maintenance

Instead, we reference available reports and let users navigate to them separately. This keeps dossier cards focused and maintains separation of concerns.

### **Why Not Allow Ranking?**
Ranking would require writing to a ranking database, which violates the zero-mutation constraint. Confidence grades are metadata from known-records only (not AI-RISA rankings).

### **Why Fail-Safe on Data Source Timeout?**
If result ledger times out, we show "result history loading..." rather than blocking the card. This prioritizes display over completeness. Cards render with available data first, enrich as data loads.

---

## File Locations & References

| Item | Location | Status |
|------|----------|--------|
| Profile Preview Card Design | [docs/global-fighter-record-profile-preview-card-design-v1.md](../docs/global-fighter-record-profile-preview-card-design-v1.md) | LOCKED (commit a3a1d97) |
| Profile Preview Card Implementation | [operator_dashboard/templates/index.html](../operator_dashboard/templates/index.html) | LOCKED (commit a922300) |
| Profile Preview Card Tests | [operator_dashboard/test_global_fighter_record_profile_preview_card_v1.py](../operator_dashboard/test_global_fighter_record_profile_preview_card_v1.py) | LOCKED (49/49 tests) |
| Button 1 Integration Smoke | [operator_dashboard/test_global_fighter_profile_preview_card_button1_integration_smoke_v1.py](../operator_dashboard/test_global_fighter_profile_preview_card_button1_integration_smoke_v1.py) | LOCKED (42/42 tests) |
| Advanced Dossier Design | This document | **DESIGN LOCK** |

---

## Next Steps

### **After Design Lock**
1. ✅ Design locked (this document)
2. ⏳ Implementation slice: Create advanced dossier rendering functions
3. ⏳ Implement 4 data source integration points
4. ⏳ Add tests (40+ expected for new sections)
5. ⏳ Integration tests with Button 1 workflow

### **Implementation Order** (suggested)
1. **Phase 1** — Render new sections with mock data (verify layout)
2. **Phase 2** — Integrate projection_ledger source (field calculations)
3. **Phase 3** — Integrate report_history source (reference catalog)
4. **Phase 4** — Integrate result_ledger source (recent activity)
5. **Phase 5** — Timeout handling & error cases
6. **Phase 6** — Full test suite & Button 1 integration tests

---

## Scope Lock & Change Control

**This design is locked.** No modifications allowed without:
1. Explicit user request for new design slice
2. New design document with rationale
3. Updated proof points and test strategy

### **Permitted Changes**
- Styling/colors (CSS-only)
- Field display names/labels
- Section ordering
- Timeout values

### **Prohibited Changes Without New Design Slice**
- Adding write operations
- Enabling ranking
- Adding form inputs or buttons
- Changing data sources
- Modifying safety constraints
- Enabling profile mutations

---

## Sign-Off

**Design Status:** LOCKED  
**Data Sources:** 4 sanitized read-only sources  
**Sections:** 11 display-only sections  
**Safety:** All write flags false, no mutations  
**Integration:** Button 1 workflow compatible  
**Dependencies:** Profile Preview Card (stable foundation)  

**Ready for implementation slice after design review approval.**

---

*Advanced Fighter Intelligence Dossier — Design lock freezes scope before implementation begins. Zero-mutation governance enforced throughout.*

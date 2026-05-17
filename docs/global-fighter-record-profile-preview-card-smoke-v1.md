# Global Fighter Record Profile Preview Card — Smoke Test Design v1

**Date:** May 17, 2026  
**Design Status:** LOCKED (Design-only — No implementation code)  
**Slice Name:** `global-fighter-record-profile-preview-card-smoke-v1`

---

## Overview

Comprehensive smoke test suite validating that the fighter profile preview card implementation:
- Renders correctly in Button 1 discovery workflow
- Displays all required fighter intelligence fields
- Handles missing data safely
- Prevents HTML injection attacks
- Maintains readonly/preview-only guarantees
- Preserves dashboard integrity (3 buttons, 3 gates)
- Enforces zero-mutation architecture

---

## Design Scope

### What This Smoke Test Will Validate

#### 1. **Card Rendering & Display**
- Profile cards render in Button 1 discovery result panel
- Fighter A card appears on left (blue border)
- Fighter B card appears on right (yellow border)
- Cards display side-by-side in 2-column grid layout
- Cards hide when no known records available
- Cards appear before text status summary

#### 2. **Data Display & Completeness**
- Fighter name displayed prominently (header)
- Confidence grade badge shown with color coding:
  - Grade A: Green (#98c379)
  - Grade B: Blue (#61afef)
  - Grade C: Gold (#c9aa71)
  - Grade D: Orange (#e5c07b)
  - Grade F: Red (#e06c75)
- All 13 required fields display when available:
  - Name, aliases, nationality
  - Promotion, division, ruleset
  - Stance, height, reach
  - Record (W-L-D format)
  - Active years (start–end format)
  - Confidence grade
  - Source type/loader info

#### 3. **Missing Field Handling**
- Null/undefined fields show "Not available" label
- Missing fields don't break card layout
- Card sections hide if no data in that section
- No placeholder text or fake data
- No console errors on missing fields
- Error cards display gracefully if record lookup fails

#### 4. **HTML Safety & XSS Prevention**
- All fighter names escaped (no HTML injection)
- All aliases escaped
- All promotion names escaped
- Special characters rendered as safe text:
  - `&` → `&amp;`
  - `<` → `&lt;`
  - `>` → `&gt;`
  - `"` → `&quot;`
  - `'` → `&#039;`
- No `<script>` tags in card output
- No event handlers in dynamic content
- Test with XSS payloads (e.g., `<img src=x onerror=alert(1)>`)

#### 5. **Readonly & Warning Display**
- Read-only warning footer displayed on all cards
- Footer text explains no profile operations possible
- Warning visible and readable
- Warning cannot be dismissed/hidden
- Warning persists across multiple interactions

#### 6. **No Interactive Controls**
- No "Create Profile" button
- No "Update Profile" / "Edit" button
- No "Merge Profile" button
- No "Rank" or ranking controls
- No "Save to Database" button
- No input fields (text, select, checkbox, radio)
- No forms or form controls
- No dropdown menus for profile actions
- No context menu or right-click handlers
- No keyboard shortcuts for profile operations

#### 7. **Write Flag Verification**
- `profile_create_performed` = false
- `profile_update_performed` = false
- `merge_performed` = false
- `database_write_performed` = false
- `ranking_write_performed` = false
- `learning_apply_performed` = false
- `calibration_write_performed` = false
- All flags verified in API responses and stored state

#### 8. **API Integration**
- Known records loaded from `/api/global-fighters/known-records/loader-preview`
- Records are sanitized/safe
- Card receives only sanitized known-records data
- No profile write endpoints called
- No filesystem writes triggered
- No live web API calls from card rendering
- All API calls are preview-only (dry-run mode)

#### 9. **Dashboard Integrity**
- Dashboard still shows exactly 3 main buttons
- Button 1: "Find & Build Fight Queue"
- Button 2: "Generate Premium PDF Reports"
- Button 3: "Find Results & Improve Accuracy"
- All buttons functional and clickable
- No new buttons added
- Exactly 3 operator gates visible
- Gate badges (🔒) still present and styled
- No new routes or workflow endpoints

#### 10. **Error Scenarios**
- Missing fighter record: Error card displays
- Empty known_records: Cards hidden gracefully
- Malformed record data: Falls back to defaults
- Network error: No crash, graceful handling
- Identity resolver failure: Cards not rendered
- Loader API timeout: Cards hidden, status shows error

#### 11. **Performance**
- Card rendering completes in < 500ms
- No memory leaks on repeated renders
- No cascading reflows/repaints
- DOM updates batched efficiently
- CSS animations smooth (60fps)

#### 12. **Accessibility**
- Cards readable with screen readers
- Semantic HTML structure (headings, lists)
- Sufficient color contrast
- Font sizes readable
- No ARIA violations
- Tab order logical

#### 13. **Cross-Browser Compatibility**
- Renders correctly in Chrome/Edge (modern)
- Renders correctly in Firefox
- CSS Grid layout works without fallbacks
- No vendor prefixes required (modern CSS)
- HTML escaping works universally

---

## Implementation Constraints (Locked)

**What the smoke test MUST NOT do:**
- ✗ Implement any profile create/update/merge operations
- ✗ Add write buttons or form controls
- ✗ Call live API endpoints
- ✗ Write to filesystem or database
- ✗ Change any existing API routes
- ✗ Modify dashboard button layout
- ✗ Add new operator gates
- ✗ Accept user input on cards
- ✗ Store mutable state in cards
- ✗ Change workflow plan structure

**What the smoke test MUST preserve:**
- ✓ 3-button dashboard layout
- ✓ 3 operator gates (Button 1, 2, 3)
- ✓ All existing Button 1 functionality
- ✓ Readonly/preview-only architecture
- ✓ Zero-mutation invariants
- ✓ All write flags false
- ✓ Identity resolver blocking logic
- ✓ Queue save approval workflow

---

## Test Execution Strategy

### Phase 1: Unit Tests
- Card rendering functions (formatValue, escapeHtml, renderCard)
- Data validation and field extraction
- HTML escaping verification
- Confidence badge color calculation
- Missing field fallback logic

### Phase 2: Integration Tests
- Card rendering in Button 1 flow
- Known records loader → card rendering pipeline
- Identity resolver → card matching
- Error recovery paths
- Multiple runs (idempotency)

### Phase 3: Smoke Tests
- Full Button 1 flow with profile cards
- End-to-end from click to card display
- Multiple fights (candidate rows)
- Edge cases:
  - High-confidence fighters (Grade A)
  - Low-confidence fighters (Grade F)
  - Conflicting sources
  - Missing records
  - XSS payloads in fighter names
- Verification of all 13 proof points

### Phase 4: Safety Validation
- Write flags frozen false (no mutations)
- No new routes visible
- No database writes triggered
- No filesystem writes
- Dashboard shape unchanged
- API endpoints unchanged
- Operator gates preserved

---

## Success Criteria

### All 13 Proofs Must Pass
1. ✓ Renders Fighter A and Fighter B profile preview cards
2. ✓ Uses sanitized known_records only
3. ✓ Shows all 13 required fields
4. ✓ Handles missing fields safely
5. ✓ Escapes HTML / unsafe text
6. ✓ Shows read-only warning
7. ✓ No create profile button
8. ✓ No update profile button
9. ✓ No merge button
10. ✓ No database/ranking controls
11. ✓ All write flags remain false
12. ✓ No new main buttons
13. ✓ No new gates (Normal dashboard remains 3 buttons / 3 gates)

### Critical Safety Checks
- [ ] Zero mutations verified (all write flags = false)
- [ ] No profile create operations triggered
- [ ] No profile update operations triggered
- [ ] No database writes attempted
- [ ] No filesystem writes
- [ ] No live web execution
- [ ] Dashboard integrity preserved
- [ ] Operator gates unchanged
- [ ] Identity resolver blocking logic preserved

### Performance Targets
- [ ] Card rendering: < 500ms
- [ ] No memory leaks
- [ ] No console errors
- [ ] No cascading reflows

---

## Known Test Data

### Test Case 1: High-Confidence Fighter
```
fighter_name: "Anderson Silva"
confidence_grade: "A"
record: { wins: 34, losses: 11, draws: 0 }
promotion: "UFC"
division: "Middleweight"
active_years: [1997, 2020]
```

### Test Case 2: Low-Confidence Fighter (Missing Data)
```
fighter_name: "Unknown Fighter"
confidence_grade: "D"
record: null
promotion: null
active_years: null
```

### Test Case 3: XSS Payload (HTML Injection)
```
fighter_name: "<img src=x onerror='alert(1)'>"
aliases: ["Fighter & Friend", "<script>alert('xss')</script>"]
```

### Test Case 4: Conflicting Sources
```
fighter_name: "Duplicate Name"
confidence_grade: "F"
conflicting_sources: true
```

---

## Failure Modes (Expected Behavior)

| Scenario | Expected Behavior |
|----------|-------------------|
| **Missing known_records** | Cards container hidden, status shows "No records loaded" |
| **Malformed record** | Error card displays gracefully |
| **XSS payload in name** | Payload escaped and displayed as literal text |
| **Network timeout** | Card rendering skipped, status shows timeout error |
| **Empty active_years** | Field not displayed, no "Not available" shown |
| **Null confidence_grade** | Defaults to "C" with neutral colors |
| **No matching fighter** | Error card: "Fighter not found in known records" |
| **Identity resolver fails** | Cards not rendered, status shows check failed |

---

## Test Artifacts

### Test Files to Create
- `test_global_fighter_record_profile_preview_card_v1_smoke.py` (this implementation)
- Fixture data files (sample known_records JSON)
- XSS payload library
- Edge case data sets

### Coverage Targets
- **Line Coverage:** ≥ 95%
- **Branch Coverage:** ≥ 90%
- **Function Coverage:** 100%
- **Proof Coverage:** 13/13 ✓

---

## Design Lock Notes

### Changes Allowed During Implementation
- ✓ CSS styling (colors, spacing, fonts)
- ✓ HTML structure optimization (semantic improvements)
- ✓ JavaScript performance improvements
- ✓ Field order in card sections
- ✓ Missing field fallback messages
- ✓ Error message wording

### Changes NOT Allowed
- ✗ Add create/update/merge buttons
- ✗ Change readonly/preview guarantees
- ✗ Add new API endpoints
- ✗ Modify write flag handling
- ✗ Change dashboard layout
- ✗ Add new operator gates
- ✗ Accept form input
- ✗ Trigger database writes
- ✗ Execute live web APIs

---

## Next Phase: Implementation Handoff

**When smoke test is locked:**
1. Implementation slice begins (separate work item)
2. Code follows design specification exactly
3. All 13 proofs must pass
4. All safety constraints must hold
5. No deviations from design without review

**Gate before next phase:**
- [ ] Design document reviewed
- [ ] All proof points understood
- [ ] No safety concerns raised
- [ ] Team alignment confirmed
- [ ] Ready to implement

---

## Status

| Item | Status |
|------|--------|
| Design Document | ✅ LOCKED |
| Proof Points | ✅ 13/13 Defined |
| Safety Constraints | ✅ Specified |
| Test Strategy | ✅ Outlined |
| Implementation | ⏳ Pending (Next Phase) |
| Date Locked | May 17, 2026 |

---

**Core Rule (From User):** 
> AI-RISA may preview fighter profile intelligence. 
> AI-RISA may not create, update, merge, rank, or write fighter profiles.

**Design Lock Status:** ✅ COMPLETE  
**Ready for implementation:** YES  
**No implementation code written:** CONFIRMED

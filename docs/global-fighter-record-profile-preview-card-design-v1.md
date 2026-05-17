---
# Fighter Profile Preview Card — Design Lock (v1)

**Date:** May 17, 2026

**Status:** DESIGN LOCKED (no implementation yet)

**Previous Handoff Commit:** 9679196  
**Previous Handoff Tag:** `global-fighter-known-records-projection-ledger-button1-final-handoff-v1`

---

## Executive Summary

This design document specifies a read-only fighter profile preview card that displays sanitized known-record and projection-ledger intelligence in Button 1's discovery preview workflow. The card is **informational only**—no profile creation, updates, merges, ranking, or database writes occur.

**Core Rule:**
> AI-RISA may preview fighter profile intelligence.  
> AI-RISA may not create, update, merge, rank, or write fighter profiles.

---

## Card Purpose & Context

### When Card Appears
Button 1 discovery preview workflow:
1. User searches for fights or pastes fight cards
2. System identifies fighters in the matchup
3. For each fighter, known-records loader API returns sanitized records
4. Profile preview card renders side-by-side with candidate fight data
5. User reviews fighter intelligence for context before approving save

### What Card Does
- **Display:** Aggregated fighter identity from multiple trusted sources (approved history, report history, result ledger, global projection)
- **Show:** Confidence, aliases, promotion context, recent appearance history
- **Enable:** Informed decision-making during fight discovery
- **Preserve:** No mutations, no writes, no side effects

### What Card Does NOT Do
- ❌ Create new fighter profiles
- ❌ Update existing fighter profiles
- ❌ Merge fighters
- ❌ Write to ranking database
- ❌ Write to fighter queue
- ❌ Apply learning/calibration
- ❌ Perform filesystem writes
- ❌ Call live web APIs
- ❌ Change any operator approval gates

---

## Card Data Model

### Input Data Source
Profile preview card consumes sanitized known-records from:

```
POST /api/global-fighters/known-records/loader-preview

Response:
{
  "ok": true,
  "known_records": [
    {
      "fighter_global_id": "fighter_001",
      "full_name": "Anderson Silva",
      "known_aliases": ["The Spider", "Silva"],
      "nationality": "BR",
      "promotion": "UFC",
      "sport_ruleset": "MMA",
      "division": "Middleweight",
      "date_of_birth": "1975-07-14",
      "height": "6'2\"",
      "reach": "77\"",
      "stance": "Southpaw",
      "record": {"wins": 34, "losses": 11, "draws": 0},
      "active_years": [1997, 2020],
      "confidence_grade": "A",
      "loader_source_type": "approved_historical|report_history|result_ledger|global_read_projection"
    }
  ],
  "preview_only": true,
  "profile_create_performed": false,
  "profile_update_performed": false,
  "merge_performed": false,
  "database_write_performed": false,
  "ranking_write_performed": false
}
```

### Card Output Model (No Mutations)

```
ProfilePreviewCard {
  fighter_global_id: str          # Readonly identifier
  display_name: str               # Full name (ASCII-normalized)
  aliases_display: List[str]      # Aliases (max 3, comma-separated)
  
  nationality: str                # Country code or name
  promotion: str                  # Current/last promotion
  division: str                   # Weight class / division
  ruleset: str                    # MMA / Boxing / etc
  
  stance: str                     # Fighter stance
  height: str                     # Physical attribute (display only)
  reach: str                      # Physical attribute (display only)
  
  record: {wins, losses, draws}   # Career record (display only)
  active_years: (start, end)      # Career span (display only)
  
  confidence_grade: str           # A/B/C/D/F confidence tier
  source_type: str                # approved_historical|report_history|result_ledger|global_read_projection
  
  preview_only: bool = True       # Always true
  write_authorized: bool = False  # Always false
}
```

---

## Card Layout & Structure

### Visual Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│  FIGHTER PROFILE PREVIEW                                │
│  [Information icon] Read-only intelligence              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Full Name: Anderson Silva                              │
│  Known As: The Spider, Silva                            │
│                                                         │
│  Context                                                │
│  ├─ Promotion: UFC                                      │
│  ├─ Division: Middleweight                              │
│  ├─ Ruleset: MMA                                        │
│  └─ Active: 1997–2020                                   │
│                                                         │
│  Physical Profile (Reference)                           │
│  ├─ Height: 6'2"  Reach: 77"  Stance: Southpaw         │
│  └─ Record: 34W–11L–0D                                  │
│                                                         │
│  Identity Confidence                                    │
│  ├─ Grade: A (High Confidence)                          │
│  ├─ Source: approved_historical                         │
│  └─ Verified across: 1 known source                     │
│                                                         │
│  ⓘ This is read-only reference intelligence.           │
│    No profile operations can be performed here.         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Card Sections

#### 1. Header
- **Title:** "Fighter Profile Preview"
- **Icon:** Information icon (read-only indicator)
- **Subtitle:** "Read-only intelligence from trusted sources"

#### 2. Primary Identity
- **Full Name:** Large, prominent display
- **Known Aliases:** Comma-separated list (max 3, truncate with "...")
- **Nationality:** Country code or flag icon + name

#### 3. Context Section
- **Promotion:** Current/last known promotion (UFC, Bellator, ONE, etc.)
- **Division:** Weight class or age group
- **Ruleset:** MMA, Boxing, Kickboxing, etc.
- **Active Years:** Career span (1997–2020) or current if active

#### 4. Physical Profile (Reference Only)
- **Height:** Display value with unit (6'2")
- **Reach:** Display value with unit (77")
- **Stance:** Southpaw, Orthodox, Southpaw, Sideways, etc.
- **Record:** Wins–Losses–Draws format (34W–11L–0D)

#### 5. Identity Confidence
- **Grade:** A/B/C/D/F confidence tier with color indicator
  - A: Green (High confidence)
  - B: Blue (Good confidence)
  - C: Yellow (Moderate confidence)
  - D: Orange (Low confidence)
  - F: Red (No match / ambiguous)
- **Source Type:** Which projection ledger provided this record
  - approved_historical
  - report_history
  - result_ledger
  - global_read_projection
- **Source Count:** "Verified across N known sources" (useful for multi-source confidence)

#### 6. Safety Footer
- **Info Badge:** "This is read-only reference intelligence"
- **Read-Only Notice:** "No profile operations can be performed here"
- **Expected Action:** "Review and approve fight discovery to proceed"

---

## Integration Points

### Button 1 Discovery Preview Workflow

```
User Action: Paste or select fight card
        ↓
System: Extract fighter names (Fighter A vs Fighter B)
        ↓
System: POST to /api/global-fighters/known-records/loader-preview
        ↓
System: Receive sanitized known_records
        ↓
UI: Render two profile preview cards side-by-side
        ↓
    ┌─────────────────┬─────────────────┐
    │  Fighter A      │  Fighter B      │
    │  Profile Card   │  Profile Card   │
    └─────────────────┴─────────────────┘
        ↓
User: Review both fighters' intelligence
        ↓
User: Approve or reject fight for save
```

### Data Flow in HTML Template

**Button 1 Template (`button1_find_fights.html`):**

```html
<!-- Candidate row with two profile cards -->
<div class="candidate-row">
  <div class="candidate-info">
    <h3>Fight {{ candidate.fight_name }}</h3>
    
    <!-- Profile preview cards side-by-side -->
    <div class="profile-cards-container">
      <div class="profile-preview-card" id="card-fighter-a">
        <!-- Populated by JavaScript from workflow data -->
      </div>
      <div class="profile-preview-card" id="card-fighter-b">
        <!-- Populated by JavaScript from workflow data -->
      </div>
    </div>
  </div>
</div>
```

**JavaScript Integration:**

```javascript
// After workflow preview returns discovery_preview context
function renderProfilePreviewCards(workflowData) {
  const knownRecords = workflowData.discovery_preview.known_records || [];
  
  // Assuming first two records are Fighter A and Fighter B
  knownRecords.slice(0, 2).forEach((record, index) => {
    const card = buildProfilePreviewCard(record);
    const container = document.getElementById(`card-fighter-${String.fromCharCode(65 + index)}`);
    container.innerHTML = card;
  });
}

function buildProfilePreviewCard(knownRecord) {
  // Safe field rendering (no mutations)
  return `
    <div class="profile-card">
      <div class="card-header">
        <span class="card-title">Fighter Profile Preview</span>
        <span class="card-icon">ⓘ</span>
      </div>
      
      <div class="card-body">
        <div class="section primary-identity">
          <h3>${escapeHtml(knownRecord.full_name)}</h3>
          <p class="aliases">Also known as: ${escapeHtml(knownRecord.known_aliases.join(', '))}</p>
        </div>
        
        <div class="section context">
          <dl>
            <dt>Promotion</dt>
            <dd>${escapeHtml(knownRecord.promotion || 'Unknown')}</dd>
            
            <dt>Division</dt>
            <dd>${escapeHtml(knownRecord.division || 'Unknown')}</dd>
            
            <dt>Active</dt>
            <dd>${knownRecord.active_years ? `${knownRecord.active_years[0]}–${knownRecord.active_years[1]}` : 'Unknown'}</dd>
          </dl>
        </div>
        
        <div class="section physical-profile">
          <dl>
            <dt>Stance</dt>
            <dd>${escapeHtml(knownRecord.stance || 'Unknown')}</dd>
            
            <dt>Record</dt>
            <dd>${knownRecord.record ? `${knownRecord.record.wins}W–${knownRecord.record.losses}L–${knownRecord.record.draws}D` : 'Unknown'}</dd>
          </dl>
        </div>
        
        <div class="section confidence">
          <p>Confidence: <span class="grade grade-${knownRecord.confidence_grade}">${knownRecord.confidence_grade}</span></p>
          <p class="source">Source: ${knownRecord.loader_source_type}</p>
        </div>
      </div>
      
      <div class="card-footer">
        <p class="read-only-notice">⚠ This is read-only reference intelligence. No profile operations can be performed here.</p>
      </div>
    </div>
  `;
}
```

---

## Safety & Mutation Prevention

### Write Flag Invariants

All profile preview card rendering **must** maintain:

```javascript
assert card.preview_only === true
assert card.write_authorized === false
assert card.profile_create_performed === false
assert card.profile_update_performed === false
assert card.merge_performed === false
assert card.database_write_performed === false
assert card.ranking_write_performed === false
assert card.learning_apply_performed === false
assert card.calibration_write_performed === false
```

### Readonly Enforcement

1. **No Input Fields:** Card displays data only, no text inputs or editable cells
2. **No Action Buttons:** No "Create Profile", "Update", "Merge", "Approve", etc. buttons in card
3. **No Hidden Forms:** No sneaky form submissions or AJAX mutations
4. **No Local Storage Writes:** Card does not persist any fighter data
5. **No API Calls:** Card makes zero POST/PATCH/DELETE requests

### Data Sanitization

All displayed values **must** be HTML-escaped to prevent injection:

```javascript
function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return String(text).replace(/[&<>"']/g, (m) => map[m]);
}
```

### Nullable Field Handling

All optional fields **must** display safe fallback or be omitted:

```javascript
// ✓ SAFE: Show fallback or omit
if (knownRecord.height) {
  display = `Height: ${escapeHtml(knownRecord.height)}`;
} else {
  display = "Height: Not available";  // Safe fallback
}

// ✗ UNSAFE: Don't attempt dangerous coercion
display = `Height: ${knownRecord.height || ""}`;  // Risky if undefined
```

---

## Design Lock Constraints

### What May Change During Implementation
- Exact CSS styling (colors, spacing, typography)
- HTML structure within the card (order of sections, class names)
- JavaScript utility functions (naming, organization)
- Responsive breakpoints (mobile, tablet, desktop)

### What Must NOT Change During Implementation
- ✅ Card displays readonly intelligence only
- ✅ No create/update/merge/write operations
- ✅ No new buttons or action controls
- ✅ No form submissions or API mutations
- ✅ All write flags remain false
- ✅ All safety invariants preserved
- ✅ HTML escaping on all displayed values
- ✅ No local storage or persistent writes
- ✅ No live web API calls from card rendering

### Dashboard Shape Preserved
- ✅ Normal Button 1 UI still visible
- ✅ 3-button dashboard shape unchanged (Button 1, 2, 3 visible)
- ✅ No new operator gates introduced
- ✅ Approval workflow unchanged

---

## Test Strategy (Design Level)

### Unit Tests (Not Yet Implemented)
Tests will verify:

1. **Card Component Rendering**
   - Accepts valid known-record object
   - Renders all safe fields
   - Escapes HTML in all displayed values
   - Shows fallback for nullable fields

2. **Safety Flag Validation**
   - Card has `preview_only = true`
   - Card has `write_authorized = false`
   - All mutation flags false

3. **No Input/Action Controls**
   - No text input fields in rendered HTML
   - No form elements
   - No submit buttons
   - No dangerous onclick handlers

4. **Data Isolation**
   - Card does not modify input object
   - Card does not store data locally
   - Card does not call POST/PATCH/DELETE

### Integration Tests (Not Yet Implemented)
Tests will verify:

1. **Loader API → Card Flow**
   - Workflow preview returns known_records
   - Card renders from loader output
   - No mutations occur during rendering

2. **Button 1 Discovery Preview**
   - Two cards render side-by-side for Fighter A and Fighter B
   - User can review both fighters
   - User can approve/reject fight without card interference

3. **Dashboard Integrity**
   - Button 1 still works after card integration
   - Button 2 and 3 unaffected
   - Operator gates unchanged

### Smoke Tests (Not Yet Implemented)
Tests will verify:

1. **Preview-Only Invariant**
   - All write flags false after card render
   - No database mutations occurred
   - No queue/result/learning writes

2. **Safety Constraints**
   - No filesystem writes
   - No live web calls
   - HTML injection prevented on all fields

---

## Failure Modes & Error Handling

### Missing or Malformed Known-Record

**Scenario:** Known-records loader returns empty or invalid data

**Response:**
```javascript
if (!knownRecord || typeof knownRecord !== 'object') {
  displayErrorCard('Unable to load fighter intelligence. Review manually.');
  return;
}
```

**Display:**
```
┌─────────────────────────┐
│ Fighter Profile Preview │
├─────────────────────────┤
│ ⚠ Unable to load        │
│   fighter intelligence. │
│ Review manually.        │
└─────────────────────────┘
```

### Null/Undefined Fields

**Scenario:** A field like `promotion` or `height` is missing

**Response:**
- Omit the field or display "Not available"
- Never display "undefined" or null to user
- Never crash or throw exception

### HTML Injection Attempt

**Scenario:** A fighter name contains `<script>alert('xss')</script>`

**Response:**
- Escape all HTML special characters
- Display as literal text: `<script>alert('xss')</script>`
- No script execution

---

## Visual Examples

### Example 1: High-Confidence Fighter

```
┌──────────────────────────────────────┐
│  Fighter Profile Preview    ⓘ       │
├──────────────────────────────────────┤
│                                      │
│  Anderson Silva                      │
│  Also known as: The Spider, Silva    │
│                                      │
│  Promotion: UFC                      │
│  Division: Middleweight              │
│  Active: 1997–2020                   │
│                                      │
│  Stance: Southpaw                    │
│  Record: 34W–11L–0D                  │
│                                      │
│  Confidence: [A] High                │
│  Source: approved_historical         │
│                                      │
│  ⚠ This is read-only reference.     │
│    No profile operations possible.   │
│                                      │
└──────────────────────────────────────┘
```

### Example 2: Low-Confidence Fighter

```
┌──────────────────────────────────────┐
│  Fighter Profile Preview    ⓘ       │
├──────────────────────────────────────┤
│                                      │
│  Rising Star                         │
│  Also known as: Not available        │
│                                      │
│  Promotion: Not available            │
│  Division: Not available             │
│  Active: Not available               │
│                                      │
│  Stance: Not available               │
│  Record: Not available               │
│                                      │
│  Confidence: [D] Low                 │
│  Source: global_read_projection      │
│                                      │
│  ⚠ Limited intelligence available.  │
│    Review manually before approving. │
│                                      │
└──────────────────────────────────────┘
```

### Example 3: Conflicting Sources

```
┌──────────────────────────────────────┐
│  Fighter Profile Preview    ⓘ       │
├──────────────────────────────────────┤
│                                      │
│  Fighter Name                        │
│  Also known as: Alias 1, Alias 2     │
│                                      │
│  Promotion: UFC                      │
│  Division: Middleweight              │
│  Active: 2015–Present                │
│                                      │
│  Stance: Unknown                     │
│  Record: 15W–3L–0D                   │
│                                      │
│  Confidence: [C] Moderate            │
│  Source: report_history              │
│  Verified across: 2 sources          │
│                                      │
│  ⚠ Multiple sources differ on some  │
│    details. Manual review recommended.│
│                                      │
└──────────────────────────────────────┘
```

---

## Handoff to Implementation

### Implementation Slice Will:
1. Create `ProfilePreviewCard` component/class
2. Implement rendering logic from `known_record` data model
3. Wire component into Button 1 template
4. Add unit tests for component
5. Add integration tests for workflow → card flow
6. Add smoke tests for safety invariants

### Implementation Slice Will NOT:
- Change this design
- Add write operations
- Add create/update/merge buttons
- Modify dashboard shape
- Change operator gates
- Open any mutation paths

### Commit & Tag:
```
Commit: [to be assigned during implementation]
Tag: global-fighter-record-profile-preview-card-v1
```

---

## Checklist: Design Lock Complete

- [x] Card purpose and context defined
- [x] Data model specified
- [x] Layout and structure locked
- [x] Integration points documented
- [x] Safety constraints locked
- [x] Write flag invariants specified
- [x] HTML escaping strategy documented
- [x] Error handling modes defined
- [x] Visual examples provided
- [x] Test strategy outlined (not implemented)
- [x] Implementation handoff documented
- [x] Design lock constraints listed
- [x] No implementation code written

---

## Status: DESIGN LOCKED

Ready for implementation slice: `global-fighter-record-profile-preview-card-v1`

**Design Lock Date:** May 17, 2026  
**Design Lock Commit:** 9679196 (handoff reference)  
**Next Phase:** Implementation with zero mutation constraints

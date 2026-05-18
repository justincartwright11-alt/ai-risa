# Button 2 Customer PDF - Phase 3 Dashboard Proof Display Design v1

## Status

Design-only slice.

- Slice: button2-customer-pdf-phase3-dashboard-proof-display-design-v1
- Type: docs-only
- Purpose: define operator dashboard display for Phase 3 rendered-output proof stack results

---

## Core Rule

Display only. No generation. No delivery. No certification automation. No approval bypass.

- Read-only UI components
- No new generation workflows
- No delivery expansion
- No automatic certification
- No operator approval gate modification
- No file writes
- No dashboard state mutations

---

## Objective

Design how operator dashboard displays Phase 3 proof stack results so operators can review rendered-output proof signals without triggering generation, delivery, certification, or approval changes.

---

## Display Constraints

**What CAN be displayed:**
- Proof stack signal (clear | detected | unavailable)
- Individual channel signals
- Failure reason summaries
- Channel name labels
- Proof status (passed | failed_closed)
- Read-only collapsible sections
- Timestamp of proof run

**What CANNOT be displayed as actionable:**
- Generate PDF buttons (generation still gated by existing approval)
- Delivery buttons (delivery still gated by existing approval)
- Certification buttons (no automation)
- Override proof results (no operator toggle)
- Auto-refresh proof (no continuous polling)
- Proof-based approval bypass

---

## UI Component Structure

### 1. Proof Stack Summary Panel

**Location:** Main dashboard (e.g., right sidebar or below fight selection)

**Display:**

```
┌─────────────────────────────────────┐
│ Phase 3 Rendered-Output Proof Stack │
├─────────────────────────────────────┤
│                                     │
│  Stack Signal: [CLEAR|DETECTED|UNA] │
│  Proof Status: [PASSED|FAILED]      │
│                                     │
│  ▼ Channel Signals (7 total)        │
│    ✓ Text Extraction: clear         │
│    ✓ Geometry: clear                │
│    ✓ Page-Section: clear            │
│    ✓ Typography-Style: clear        │
│    ✓ Header/Footer/Watermark: clear │
│    ✓ Source-Traceability: clear     │
│    ✓ Visual QA Rollup: clear        │
│                                     │
│  ▼ Failure Reasons (if detected)    │
│    [expand/collapse]                │
│                                     │
│  Last Updated: HH:MM:SS             │
└─────────────────────────────────────┘
```

### 2. Channel Status Display

**Each channel row shows:**
- Channel name (exact label)
- Signal icon or label (✓ clear | ⚠ detected | ✗ unavailable)
- Optional: click to expand channel-specific failure reasons

**Signal visual encoding:**
- Clear: ✓ green text or checkmark icon
- Detected: ⚠ orange/yellow text or warning icon
- Unavailable: ✗ red text or error icon

**No interpretation of signal by operator:**
- Display signal as-is from proof orchestrator
- Do NOT show "ready to generate" or "not ready to generate" inference
- Do NOT show "blocking delivery" or "delivery allowed" inference

---

### 3. Failure Reason Display

**Location:** Expandable section within proof stack summary

**Display (if stack_signal = detected or unavailable):**

```
▼ Failure Reasons

[Reason from Channel 1]
[Reason from Channel 2]
...
[Reason from Channel N]
```

**Content:**
- List of deterministic reason strings from all channels
- Aggregate of channel_failure_reasons from proof orchestrator result
- No formatting interpretation (display as provided)
- Optional: channel name prefix for clarity
  ```
  [geometry] out_of_range_margins
  [source_traceability] missing_required_citations
  ```

**No operator action:**
- Reasons are informational only
- No "fix this" buttons
- No "retry proof" buttons
- No "override result" options

---

### 4. Signal Labels and Semantics

**Clear Signal Display:**

```
Stack Signal: ✓ CLEAR
Proof Status: PASSED

All channels clear. Rendered output meets proof requirements.
```

**Detected Signal Display:**

```
Stack Signal: ⚠ DETECTED
Proof Status: FAILED_CLOSED

One or more channels detected violations.
Review failure reasons below.
```

**Unavailable Signal Display:**

```
Stack Signal: ✗ UNAVAILABLE
Proof Status: FAILED_CLOSED

One or more channels unavailable or malformed.
Review failure reasons below.
```

---

### 5. Operator Review Guidance

**Static help text (not operational):**

```
Phase 3 Proof Stack

This read-only display shows rendered-output proof signals.
Signals do not automatically trigger generation, delivery, or certification.
Existing approval gates remain in place for all operations.

Signal meanings:
- CLEAR: All 7 proof channels passed.
- DETECTED: One or more channels detected violations.
- UNAVAILABLE: One or more channels unavailable.

For details on each channel, expand the channel signals section.
```

---

### 6. No New Action Buttons

**Existing buttons remain unchanged:**
- Generate PDF (still requires existing approval gate)
- Request manual review (still requires existing approval gate)
- Export/download (still requires existing delivery gate)

**New buttons NOT added:**
- "Run Proof Again" button (proof runs on render, not user-triggered)
- "Override Proof" button (proof results not overrideable)
- "Auto-Fix Issues" button (no automation)
- "Generate Despite Violations" button (no gate bypass)

---

### 7. Proof Display States

**Proof not yet run:**

```
Phase 3 Rendered-Output Proof Stack

Status: Not yet run

(Proof runs automatically when rendered output is generated)
```

**Proof running (if async):**

```
Phase 3 Rendered-Output Proof Stack

Status: Running...

(Proof validation in progress)
```

**Proof completed (clear):**

```
Phase 3 Rendered-Output Proof Stack

Stack Signal: ✓ CLEAR
Proof Status: PASSED

[Channel signals...]
Last Updated: 14:32:15
```

**Proof completed (detected):**

```
Phase 3 Rendered-Output Proof Stack

Stack Signal: ⚠ DETECTED
Proof Status: FAILED_CLOSED

[Channel signals...]

▼ Failure Reasons
  [reason 1]
  [reason 2]

Last Updated: 14:32:15
```

**Proof failed_closed (unavailable):**

```
Phase 3 Rendered-Output Proof Stack

Stack Signal: ✗ UNAVAILABLE
Proof Status: FAILED_CLOSED

[Channel signals with unavailable flags...]

▼ Failure Reasons
  [reason 1]

Last Updated: 14:32:15
```

---

### 8. No File Writes or Dashboard Mutations

**Display implementation:**
- All data read from proof orchestrator result
- No file writes during display
- No local caching that requires writes
- No dashboard state mutations triggered by display
- No side effects from expanding/collapsing sections

**Proof result data contract (immutable input):**
```python
proof_result = {
    "stack_signal": "clear|detected|unavailable",
    "proof_status": "passed|failed_closed",
    "channel_signals": {channel_name: signal, ...},
    "channel_failure_reasons": {channel_name: [reasons], ...},
}
```

---

### 9. Fail-Closed Display States

**If proof result malformed:**

```
Phase 3 Rendered-Output Proof Stack

Status: Error - Proof result invalid

(Unable to display proof result. Contact administrator.)
```

**If proof data unavailable:**

```
Phase 3 Rendered-Output Proof Stack

Status: Unavailable

(Proof data not available for this render.)
```

**If channel data missing:**

```
Phase 3 Rendered-Output Proof Stack

Stack Signal: ✗ UNAVAILABLE
Proof Status: FAILED_CLOSED

Channel Signals:
  ✓ Text Extraction: clear
  ✗ [missing]: unavailable
  ✓ Geometry: clear
  ...
```

---

### 10. Placement in Operator Dashboard

**Recommended locations:**
- Option A: Right sidebar panel (2nd column if 3-column layout)
- Option B: Below fight card selection
- Option C: Modal/panel triggered by "View Proof Details" button
- Option D: Collapsible section on PDF generation card

**Sizing:**
- Minimum width: 320px (mobile)
- Recommended width: 400-500px
- Height: Expandable based on content (7 channels + reasons)
- Scrollable if reason list is long

---

## Implementation Sequence Link

After design lock:

1. dashboard-proof-display-preview (HTML/CSS mock)
2. dashboard-proof-display-integration (wire proof results to dashboard UI)
3. dashboard-proof-display-smoke (UI state tests for all signal states)
4. dashboard-proof-display-final-handoff (ready for operator use)

---

## Integration Points (Not Yet Implemented)

These will be defined in preview/integration slices:

- Dashboard component receives proof_result dict from proof orchestrator
- Component extracts stack_signal, channel_signals, channel_failure_reasons
- Component renders summary panel with current signal state
- Component handles expand/collapse of channel sections and failure reasons
- No API calls or state mutations during display
- All data read-only

---

## Governance Guarantee

Dashboard proof display:

- Does NOT generate PDFs
- Does NOT write files
- Does NOT modify renderer
- Does NOT modify approval gates
- Does NOT bypass certification
- Does NOT change delivery workflow
- Does NOT perform mutations
- Does NOT cache with side effects

Display is read-only reference layer on top of proof stack orchestrator results.

---

## Final Statement

This design locks a governance-safe read-only display contract for Phase 3 proof stack results, enabling operators to review rendered-output proof signals without triggering generation, delivery, certification, or approval changes.

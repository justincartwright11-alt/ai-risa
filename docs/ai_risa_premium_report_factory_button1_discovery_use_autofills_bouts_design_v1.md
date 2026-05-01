# AI-RISA Premium Report Factory — Button 1 Discovery Use Autofills Bouts Design v1

**Slice:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-v1`
**Design date:** 2026-05-02
**Baseline commit:** `10c3528`
**Baseline tag:** `ai-risa-premium-report-factory-three-button-usability-repair-archive-lock-v1`
**Type:** docs-only design — no implementation in this slice

---

## Problem statement

Button 1 discovery finds events from local event card files and returns them in a panel with a **Use** button per row. The current **Use** behavior pre-fills only event metadata fields (event_name, event_date, promotion). It does not populate the **Manual Input** textarea with the bout list extracted from the discovered event's card data.

**Observed failure sequence:**

1. Operator clicks "Run Official-Source Discovery".
2. Discovery panel shows: `Ares FC 39: Jbalia vs. Diatta — 1 bouts`.
3. Operator clicks **Use** on that row.
4. Event metadata fields are pre-filled.
5. Manual Input (raw card text) still shows only placeholder text.
6. Operator clicks "Parse Preview".
7. Result: `No matchup rows found. Add manual input or run discovery then preview again.`
8. Queue stays empty. Button 2 blocked.

**Root cause:** The discovery API response returns event-level rows with a `bouts_count` integer, but the current frontend **Use** handler only reads `event_name`, `event_date`, and `promotion` from the row. It does not access or surface the actual bout list. The bout details (fighter names) are available in the local event card files but are not currently included in the discovery API response rows.

---

## Design requirements

### R1 — Use button pre-fills all available event fields

When the operator clicks **Use** on a discovered event row, the following intake fields must be populated if data is available:

| Field | Source |
|---|---|
| `event_name` | `row.event_name` |
| `event_date` | `row.date` |
| `promotion` | `row.promotion` |
| `location` | `row.location` (if present in row data) |
| `source_reference` | `row.source` (the local file path used as reference) |
| raw matchup text | derived from `row.bouts` bout list (see R2) |

---

### R2 — Use fills Manual Input with one matchup line per bout

If the discovered event row contains a usable bout list, the **Manual Input** textarea must be populated with one line per bout in the format:

```
Fighter A vs Fighter B
```

**Example:**

Discovered event: `Ares FC 39: Jbalia vs. Diatta`, bout count: 1, bouts: `[{fighter_a: "Aboubakar Jbalia", fighter_b: "Cherif Diatta"}]`

**Use fills Manual Input with:**
```
Aboubakar Jbalia vs Cherif Diatta
```

**Multi-bout example:**

Discovered event with 3 bouts:
```
Fighter A vs Fighter B
Fighter C vs Fighter D
Fighter E vs Fighter F
```

---

### R3 — No-bouts fallback message

If the discovered event row has `bouts_count: 0` or the bout list is empty or unavailable, clicking **Use** must:

- Still pre-fill all available metadata fields.
- Clear the Manual Input textarea (do not leave stale previous content).
- Show a plain-English status message:

  > `This discovered event has no bout list. Paste matchups manually.`

---

### R4 — Status message guides operator to next step

After **Use** fires, the Button 1 status bar must update with one of two messages:

**If bouts were loaded into Manual Input:**
> `Event and bout list loaded. Click Parse Preview.`

**If only metadata was loaded (no bouts):**
> `Event loaded, but no bout list was available. Paste matchups manually, then click Parse Preview.`

The message must make "Parse Preview" the obvious next action.

---

### R5 — Button 1 status shows discovery context

After discovery completes and an event is selected, the Button 1 status bar must show:

- Discovered events count (already shown post-discovery).
- Which event was selected (event_name).
- Loaded bout count (e.g. `3 bouts loaded into Manual Input`).
- Whether manual input was filled from discovery or left for manual paste.

---

### R6 — Backend must include bout detail in discovery response rows

The current `scan_upcoming_events` response rows contain only `bouts_count` (an integer). To support R2, the backend must include the actual bout list in each discovery row so the frontend can construct the matchup lines.

**Required addition to each discovery row:**

```json
{
  "event_id": "...",
  "event_name": "...",
  "date": "...",
  "promotion": "...",
  "location": "...",
  "source": "...",
  "bouts_count": 1,
  "bouts": [
    { "fighter_a": "Aboubakar Jbalia", "fighter_b": "Cherif Diatta" }
  ]
}
```

The `bouts` array is the minimal new field required. Each element must contain at minimum `fighter_a` and `fighter_b`. Additional bout fields (weight_class, main_event, etc.) may be included but are not required for this repair.

**Scope note:** The event card files already contain a `bouts` array (used to compute `bouts_count`). The backend change is to pass that array through to the response rather than discarding it.

---

### R7 — Governance constraints

| Constraint | Requirement |
|---|---|
| Use is not a permanent write | **REQUIRED** — Use only populates form fields in the browser. No API call to a write endpoint. |
| Use does not save to queue/database | **REQUIRED** — queue write only happens on "Save Selected" with operator approval. |
| Operator approval still required before save | **REQUIRED** — approval gate is unchanged. |
| No customer PDFs generated by Button 1 | **REQUIRED** — report generation remains Button 2 only. |
| No learning/calibration updates | **REQUIRED** — no accuracy, calibration, or ledger writes. |
| No hidden automatic writes | **REQUIRED** — all writes remain explicit and approval-gated. |

---

### R8 — Non-goals (explicitly out of scope)

The following are out of scope for this slice at design, implementation, smoke, and archive:

- Phase 4 expansion of any kind.
- Result lookup changes.
- Learning or calibration pipeline changes.
- Billing or customer output logic.
- Button 2 behavior changes.
- Button 3 behavior changes.
- Global ledger changes.
- Any new API endpoint.
- Any change to existing endpoint contracts beyond adding `bouts` and `location` fields to the discovery row response (additive, non-breaking).

---

## Implementation plan (for next slice — not implemented here)

### Backend change

**File:** `operator_dashboard/phase1_ops.py`
**Function:** `_extract_event_fields`

Current: extracts `bouts_count = len(bouts)`, discards `bouts` list.

Required: pass `bouts` list through to the returned row, with each element normalized to `{"fighter_a": str, "fighter_b": str, ...original_bout_fields}`.

**File:** `operator_dashboard/app.py`
**Function:** `scan_upcoming_events` route is a passthrough — no change needed if `_extract_event_fields` is updated.

### Frontend change

**File:** `operator_dashboard/templates/index.html`
**Function:** Use button click handler in `runMainPrfDiscovery` panel render block.

Current handler sets only:
```js
mainPrfIntakeEventName.value = btn.getAttribute('data-event-name');
mainPrfIntakeEventDate.value = btn.getAttribute('data-event-date');
mainPrfIntakePromotion.value = btn.getAttribute('data-event-promotion');
```

Required: handler must also set `location`, `source_reference`, and populate `mainPrfIntakeRawCardText` from the bout list.

Bout list must be stored in a `data-bouts` attribute on the button (JSON-encoded) or passed through the row object held in the JS discovery array.

**Recommended approach:** store the full row object in `button3State`-style JS state array keyed by event_id, then look up on Use click. This avoids attribute size limits for multi-bout events.

---

## Future implementation test plan

| Test | Expected |
|---|---|
| Use on event with 1 bout | `raw_card_text` textarea = `"Fighter A vs Fighter B"`, status = "Event and bout list loaded. Click Parse Preview." |
| Use on event with 3 bouts | `raw_card_text` = 3 lines, one per bout |
| Use on event with 0 bouts | `raw_card_text` cleared, status = "no bout list" message |
| Parse Preview after Use (bouts loaded) | Returns `matchup_previews` with correct fighter names, `parse_status: "parsed"` |
| Parse Preview after Use (no bouts) | Returns `No matchup rows found` (expected) |
| Use does not call save endpoint | No POST to `/api/premium-report-factory/queue/save-selected` |
| Use does not call generate endpoint | No POST to `/api/premium-report-factory/reports/generate` |
| Save Selected still requires operator approval | `operator_approval: false` → rejected |
| Button 2 works after save | Queue reflects saved fights correctly |
| Existing 253 backend tests remain green | 253 passed, 0 failed |

---

## Design summary

| Req | Description | Status |
|---|---|---|
| R1 | Use pre-fills all event metadata including location and source_reference | Designed |
| R2 | Use fills Manual Input with one matchup line per bout | Designed |
| R3 | No-bouts fallback: clear textarea, show paste prompt | Designed |
| R4 | Status message guides to Parse Preview | Designed |
| R5 | Status shows selected event name and loaded bout count | Designed |
| R6 | Backend discovery response includes `bouts` array per row | Designed |
| R7 | All governance constraints preserved | Confirmed |
| R8 | Non-goals explicitly excluded | Confirmed |

---

## Next safe slice

```text
ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-review-v1
```

No implementation until design review is locked.

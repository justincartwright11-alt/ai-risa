# AI-RISA Premium Report Factory — Button 1 Discovery Use Autofills Bouts Design Review v1

**Slice:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-review-v1`
**Design commit:** `0f3c819`
**Design tag:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-v1`
**Review date:** 2026-05-02
**Reviewer:** Operator

---

## Purpose

This document is a formal design review of the discovery-Use-autofills-bouts design locked at `0f3c819`. It confirms each design requirement is understood, scoped, and safe to implement. No implementation occurs in this slice.

---

## Review Checklist

### R1 — Use button pre-fills all available event fields

- **Design intent:** Clicking **Use** on a discovered event row must populate `event_name`, `event_date`, `promotion`, `location`, and `source_reference` in the intake form — not just the first three fields as at present.
- **Scope:** Frontend only. Use button click handler in `runMainPrfDiscovery` panel render block (`operator_dashboard/templates/index.html`). No backend endpoint change for this field set.
- **Risk:** Low. Additive form-fill. Cannot corrupt data that was not already being set.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R2 — Use fills Manual Input with one matchup line per bout

- **Design intent:** After the operator clicks **Use**, the Manual Input textarea must be populated with one `Fighter A vs Fighter B` line per bout. This removes the need to paste fight data manually when discovery has already found it.
- **Scope:** Frontend click handler. Requires `bouts` array to be available in the JS state at click time (see R6). Output format: one plain-text line per bout, `\n`-joined.
- **Risk:** Low. Writes only to a textarea. Operator can still overwrite before Parse Preview. Does not auto-submit or auto-save.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R3 — No-bouts fallback: clear textarea, show paste prompt

- **Design intent:** If the discovered event row carries zero bouts or an empty bouts list, the handler must clear the Manual Input textarea (do not leave stale content from a prior Use) and display: _"This discovered event has no bout list. Paste matchups manually."_
- **Scope:** Frontend click handler — conditional branch when `bouts` array is absent or empty. Single status string, single textarea clear.
- **Risk:** None. Pure UI state. No write path involved.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R4 — Status message guides operator to next step

- **Design intent:** After **Use** fires, the Button 1 status bar must update to one of two messages:
  - Bouts loaded: `"Event and bout list loaded. Click Parse Preview."`
  - No bouts: `"Event loaded, but no bout list was available. Paste matchups manually, then click Parse Preview."`
- **Scope:** Frontend only. Status bar element in the Button 1 panel. Single conditional string assignment.
- **Risk:** None. Purely informational display.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R5 — Status shows discovery context after event selection

- **Design intent:** Post-Use, the status bar must reflect the selected event name and loaded bout count (e.g. `"3 bouts loaded into Manual Input"`) so the operator can confirm the correct event was applied.
- **Scope:** Frontend click handler — same status update as R4, extended with event name and count.
- **Risk:** None. Additive display detail.
- **Review verdict:** APPROVED. Acceptable to implement. R4 and R5 may be fulfilled in one combined status string — implementation may consolidate.

---

### R6 — Backend discovery response must include `bouts` array per row

- **Design intent:** The `/api/phase1/scan-upcoming-events` response rows currently include only `bouts_count` (an integer). The backend must pass through the full `bouts` array so the frontend has the fighter names needed to construct matchup lines.
- **Scope:** `operator_dashboard/phase1_ops.py` — `_extract_event_fields` function. Change is additive: retain `bouts_count`, add `bouts` list with each element normalized to `{"fighter_a": str, "fighter_b": str}`. The route handler in `app.py` is a passthrough and requires no change.
- **Risk:** Low. Additive response field. Existing callers that read only `bouts_count` are unaffected. The `bouts` array was already computed to derive `bouts_count` — change is pass-through, not new extraction.
- **Verified source:** Event card files already contain a `bouts` array. `_extract_event_fields` reads it and calls `len()` only. No new parsing required.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### R7 — Governance constraints preserved

- **Design intent:** Use is not a write. No API call to a save or generate endpoint fires on Use. Operator approval gate for queue save is unchanged. No PDF generation triggered by Button 1. No learning/calibration writes.
- **Scope:** Implementation must not add any `fetch()` or XHR call to a write endpoint inside the Use handler. Existing approval gate in `/api/premium-report-factory/queue/save-selected` is untouched.
- **Risk:** None if scoped correctly. Reviewer must verify no write call is added to the Use handler during implementation review.
- **Review verdict:** CONFIRMED. Constraint must be enforced in implementation.

---

### R8 — Non-goals confirmed out of scope

The following must not appear in the implementation slice:

- Phase 4 expansion.
- Result lookup changes.
- Learning or calibration pipeline changes.
- Billing or customer output logic.
- Button 2 or Button 3 behavior changes.
- Global ledger changes.
- Any new API endpoint.
- Any change to existing endpoint request contracts (response changes only, additive).

- **Review verdict:** CONFIRMED. Implementation must stay within R1–R6 only.

---

## Implementation scope summary

| File | Change |
|---|---|
| `operator_dashboard/phase1_ops.py` | `_extract_event_fields`: pass `bouts` list through to row dict |
| `operator_dashboard/templates/index.html` | Use handler: set `location`, `source_reference`, populate textarea from bouts, update status bar |
| `operator_dashboard/app.py` | No change required |

**State storage approach (recommended):** Store the full discovery row objects in a JS-side dict keyed by `event_id` at render time. Look up on Use click. This avoids HTML attribute size limits for multi-bout events and keeps the handler clean.

---

## Design gaps — none identified

No ambiguities requiring redesign were found. All requirements are internally consistent and implementable within the approved file scope.

---

## Summary Verdict

All eight requirements reviewed. All approved or confirmed. No scope gaps. No design ambiguities requiring redesign.

**Design review outcome: PASS — safe to proceed to implementation slice.**

---

## Next slice

```text
ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-implementation-v1
```

Implementation must reference this review commit and must not exceed the approved scope (R1–R6, files listed above).

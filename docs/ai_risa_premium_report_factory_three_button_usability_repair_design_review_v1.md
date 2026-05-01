# AI-RISA Premium Report Factory — Three-Button Usability Repair Design Review v1

**Slice:** `ai-risa-premium-report-factory-three-button-usability-repair-design-review-v1`
**Design commit:** `adcef67`
**Design tag:** `ai-risa-premium-report-factory-three-button-usability-repair-design-v1`
**Review date:** 2026-05-02
**Reviewer:** Operator

---

## Purpose

This document is a formal design review of the usability repair design locked at `adcef67`. It confirms each design requirement is understood, scoped, and safe to implement. No implementation occurs in this slice.

---

## Review Checklist

### Requirement 1 — Button 1 parser: accept `vs`, `vs.`, `v`, `versus`

- **Design intent:** The matchup parser must recognise all common fight separator tokens.
- **Scope:** Parser function in `operator_dashboard/app.py` (Button 1 intake endpoint). Frontend display is unaffected.
- **Risk:** Low. Additive token matching. Cannot break existing `vs` parsing.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 2 — Missing `event_date` becomes warning, not blocker

- **Design intent:** When `event_date` is absent from the intake payload, Button 1 must continue to the preview/save flow with a visible warning rather than returning an error that halts the operator.
- **Scope:** Validation logic in the Button 1 intake endpoint. Warning surfaced in the review panel. No change to the save path itself.
- **Risk:** Low. Relaxes a guard. Warning still surfaces the absence so the operator is informed.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 3 — Discovery rows must show in Button 1 review window

- **Design intent:** Rows parsed from the intake input (the "discovered" fights) must be rendered in the Button 1 preview panel so the operator can see what was found before approving a save.
- **Scope:** Frontend template (`operator_dashboard/templates/index.html`) — Button 1 preview render block. Backend endpoint may need to return discovery row data if it does not already.
- **Risk:** Low. Read-only display change. Does not alter save logic.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 4 — Button 1 status: parsed / selected / saved counts + clear save blockers

- **Design intent:** The Button 1 panel must show three counts (parsed, selected, saved) and must clearly communicate any condition that would block a save (e.g., missing required fields, duplicate detection).
- **Scope:** Frontend template Button 1 status bar. Backend endpoint must return counts and blocker reasons in the response payload.
- **Risk:** Low. Additive display only. Does not alter save logic.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 5 — Button 2 empty-queue message

- **Design intent:** When Button 2 loads and the queue is empty, the operator must see: _"No saved fights yet. Use Button 1 first."_
- **Scope:** Frontend template Button 2 empty-state render block. No backend change expected.
- **Risk:** None. Pure UI string change.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 6 — Button 3 pre-apply clarity panel

- **Design intent:** Before the operator can approve an Apply, Button 3 must show:
  1. The selected waiting row.
  2. The selected candidate result.
  3. The current approval state.
  4. An exact write preview (field, old value → new value).
- **Scope:** Frontend template Button 3 pre-apply section. Backend `/api/operator/actual-result-lookup/manual-single-apply` may need to return write-preview data alongside the dry-run response.
- **Risk:** Low-medium. Dry-run data is already computed; this surfaces it explicitly. No new write path introduced.
- **Review verdict:** APPROVED. Acceptable to implement.

---

### Requirement 7 — No new features

- **Design intent:** This repair slice must not introduce Phase 4 expansion, billing, hidden learning loops, or any uncontrolled writes.
- **Scope:** All files touched during implementation must be reviewed against this boundary.
- **Risk:** N/A (constraint, not a feature).
- **Review verdict:** CONFIRMED. Implementation must stay within the six repair items above.

---

## Summary Verdict

All seven requirements reviewed. All approved. No scope gaps identified. No design ambiguities requiring redesign.

**Design review outcome: PASS — safe to proceed to implementation slice.**

---

## Next slice

```text
ai-risa-premium-report-factory-three-button-usability-repair-implementation-v1
```

Implementation must reference this review commit and must not exceed the approved scope.

# AI-RISA Premium Report Factory - Three-Button Usability Repair Design v1

Document Type: Design (Docs-Only)
Date: 2026-05-02
Slice Name: ai-risa-premium-report-factory-three-button-usability-repair-design-v1

---

## 1. Design Purpose

Make the three-button dashboard idiot-proof before any additional sales/demo work.

This slice is design-only and defines the minimum usability repair needed to make the existing three-button flow operationally reliable for non-technical operators.

---

## 2. Problem Statement

Current dashboard behavior can expose all three buttons while still failing practical workflow completion when input format or intermediate state handling is unclear.

Observed friction pattern:
1. Button 1 can fail to produce saved fights when parsing/discovery context is ambiguous.
2. Button 2 then correctly blocks due to empty saved queue, but user confidence drops.
3. Button 3 can show accuracy data while apply remains functionally blocked without explicit row/candidate clarity.

The product currently requires too much operator interpretation of parser constraints, date handling, and state prerequisites.

---

## 3. In-Scope Usability Repairs

### 3.1 Button 1 Parser Repair

Requirement:
- Accept matchup separators in all of the following forms:
  - vs
  - vs.
  - v
  - versus

Design intent:
- Normalize common separator variants to one internal canonical parse path.
- Avoid operator failure due to punctuation/style differences.

### 3.2 Event Date Handling

Requirement:
- Missing event_date is a warning, not a blocker.

Design intent:
- Keep parse/save workflow available when date is absent.
- Surface warning text clearly and allow continuation with explicit operator awareness.

### 3.3 Discovery Rows Visibility

Requirement:
- If discovery finds rows, show them in Button 1 review window.

Design intent:
- Align discovery summary and review table so operators can act on discovered rows without hidden state.
- Prevent “discovery found rows but review is empty” confusion.

### 3.4 Button 1 Status Clarity

Requirement:
- Show explicit counts/states for:
  - parsed fights
  - selected fights
  - saved fights
  - clear save blockers

Design intent:
- Provide deterministic checkpoint visibility from input through save.
- Replace implicit/derived status with simple explicit workflow state.

### 3.5 Button 2 Empty Queue Explanation

Requirement:
- Display exact guidance text:
  - No saved fights yet. Use Button 1 first.

Design intent:
- Convert passive empty-state into actionable next step.
- Reduce operator guesswork when generation is blocked.

### 3.6 Button 3 Apply Clarity

Requirement:
- Before Apply, clearly show:
  - selected waiting row
  - selected candidate
  - approval state
  - exact write preview

Design intent:
- Eliminate ambiguity around why Apply is blocked.
- Ensure operator can verify write target and payload before committing.

---

## 4. Step Status Model (Cross-Button)

Dashboard should expose a simple step status summary that reflects the workflow chain in plain language.

Minimum status expression:
1. Button 1: X saved
2. Button 2: blocked because queue empty (when applicable)
3. Button 3: waiting for selected result (when applicable)

Design intent:
- Give operators immediate process location and next action without deep panel reading.

---

## 5. Non-Goals and Guardrails

No new feature expansion in this slice.

Explicitly excluded:
1. No Phase 4 expansion
2. No billing additions
3. No hidden learning behaviors
4. No uncontrolled writes

Governance continuity:
- Approval-gated permanent writes remain mandatory.
- Automatic search/analysis may continue; permanent write paths must remain explicit and operator-approved.

---

## 6. Acceptance Criteria (Design Level)

This design is considered satisfied when implementation later demonstrates:
1. Matchup parser accepts vs / vs. / v / versus inputs with equivalent behavior.
2. Missing event_date appears as warning-only and does not block save path.
3. Discovery results are visible in Button 1 actionable review table.
4. Button 1 displays parsed/selected/saved counts and explicit save blockers.
5. Button 2 empty-state message reads: No saved fights yet. Use Button 1 first.
6. Button 3 pre-apply state shows selected row, selected candidate, approval state, and exact write preview.
7. No out-of-scope feature expansion or governance regression introduced.

---

## 7. Implementation Planning Note (For Next Slice)

The next slice after this design should be implementation-only for usability repair, bounded to the scope above.

Recommended implementation slice name:
- ai-risa-premium-report-factory-three-button-usability-repair-implementation-v1

Design-first order remains required:
1. Design (this document)
2. Design review
3. Implementation
4. Post-freeze smoke
5. Final review
6. Release manifest
7. Archive lock

---

## 8. Design Verdict

Verdict: APPROVED FOR DESIGN REVIEW

This design defines the required usability repair to make the existing three-button dashboard operationally idiot-proof without adding new feature scope.

End of design document.

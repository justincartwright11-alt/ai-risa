# AI-RISA Premium Report Factory MVP — Phase 2 Dashboard Runtime Mismatch Diagnostic Closure v1

## Closure Purpose

This document records the final result of the Phase 2 dashboard runtime mismatch diagnostic.

- Record and preserve the diagnostic outcome
- Close the runtime mismatch as resolved with no code change
- Prevent unnecessary patching of correct defensive behavior
- Preserve the integrity of the Phase 2 archived baseline

---

## Baseline

| Field | Value |
|-------|-------|
| Diagnostic design review commit | `068f16e` |
| Diagnostic design review tag | `ai-risa-premium-report-factory-mvp-phase2-dashboard-runtime-mismatch-diagnostic-design-review-v1` |
| Underlying Phase 2 archived baseline commit | `dfbacd4` |
| Underlying Phase 2 archived baseline tag | `ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-archive-lock-v1` |

---

## Original Symptom

During the initial live operator demo attempt following Phase 2 archive lock:

- The dashboard appeared to show older preview-only behavior
- The **Save Selected to Upcoming Fight Queue** button appeared absent
- The **Upcoming Fight Queue** window appeared absent
- The preview `POST /api/premium-report-factory/intake/preview` did not reach Flask when the Preview Event Card button was clicked

---

## Known-Good Evidence Prior to Diagnostic

The following checks had already confirmed the Phase 2 implementation was present and healthy before the diagnostic run:

- Local Phase 2 HTML tokens present in `operator_dashboard/templates/advanced_dashboard.html`
- Served HTML Phase 2 tokens present in live browser session
- Backend endpoints responded correctly via Flask test client (230/230 tests passing)
- Temp queue path override (`PRF_QUEUE_PATH_OVERRIDE`) isolated writes correctly
- Browser DOM nodes (`#operator-prf-preview-btn`, `#operator-prf-phase2-controls`, `#operator-prf-save-selected-btn`, `#operator-prf-upcoming-queue-window`) confirmed present in live session

---

## Runtime Diagnostic Findings

All findings from the `2026-05-01` runtime diagnostic evidence run:

| Probe | Finding |
|-------|---------|
| Button exists in DOM | Yes — `#operator-prf-preview-btn` found, `display:block`, `visibility:visible` |
| Button type | `type="submit"` with no enclosing form — no form-submission side-effect per HTML spec |
| Duplicate element IDs | None — `#operator-prf-preview-btn` ×1, `#operator-prf-raw-card-text` ×1, `#operator-prf-event-name` ×1 |
| onclick handler bound | Yes — closure-scoped async arrow function, bound as expected |
| Closure variable accessibility | `premiumFactoryRawCardTextInput` and siblings are DOMContentLoaded-scoped, not on `window` — expected by design |
| Direct `page.evaluate` fetch | `POST /api/premium-report-factory/intake/preview` → 200 OK, 2 matchups parsed (`tmp_660bd51b23d0`, `tmp_778b4ab7c1b5`) |
| Handler with fields filled | `btn.onclick()` called with fields populated → fetch fired → 200 OK → preview rendered → Phase 2 controls became visible |
| Save Selected flow | `POST /api/premium-report-factory/queue/save-selected` → 200 OK, `accepted_count: 2`, `readiness_score: 100` each |
| Queue list refresh | GET `/api/premium-report-factory/queue` → 2 saved rows returned, rendered in upcoming queue window |
| Background 500 error | Unrelated background polling endpoint — no effect on PRF handler path |
| Code changes made | None — diagnostic was entirely read-only and runtime-only |

---

## Root Cause

**`raw_card_text` was empty at click time during the failed procedure.**

The handler execution path when `raw_card_text` is empty:

1. `setStatus('Loading premium report factory preview...')` — executes unconditionally  
   → **this is the observer-visible state change that was mistaken for a working click**
2. `if (!String(rawCardText || '').trim())` — empty-guard fires synchronously
3. `renderPremiumFactoryPreviewOutput({ parse_warnings: ['empty_raw_card_text'] })` — renders empty-input warning
4. `return` — handler exits early
5. **`fetch(...)` is never called** → Flask receives no `POST` → no preview response

This is **defensive behavior**. The handler is correct. Flask received no request because the guard operated as intended.

---

## Classification

| Category | Verdict |
|----------|---------|
| Overall classification | **Test-procedure gap** |
| Code defect | No |
| Stale checkout | No |
| Stale Flask process | No |
| Backend endpoint failure | No |
| DOM token absence | No |
| Network transport failure | No |
| Handler binding failure | No |
| Duplicate ID shadow | No |
| Script execution order failure | No |

---

## Operator Instruction

To use the Phase 2 Preview Event Card flow correctly:

1. Paste or type fight card text into the **raw_card_text** field before pressing **Preview Event Card**
2. Include at least one non-whitespace line, e.g. `Fighter A vs Fighter B`
3. Optionally fill `event_name`, `event_date`, `promotion`, `location`, `source_reference`, `notes`
4. Click **Preview Event Card** — the preview renders, Phase 2 controls become visible
5. Select rows using the per-matchup checkboxes or **Select All**
6. Click **Save Selected to Upcoming Fight Queue** — confirm approval checkbox is set
7. The Upcoming Fight Queue window refreshes with saved rows

---

## No Fix Required

- No code change is recommended
- No patch slice is authorized
- The empty-field guard is correct defensive behavior and must not be removed
- **Optional future UX improvement only** (not authorized by this slice): a clearer inline validation message when the operator clicks Preview with an empty `raw_card_text` field
  - If desired, this would require a separate docs-only UX/fix design slice opened under normal governance
  - It must not be implemented as part of this closure

---

## Governance Confirmation

| Constraint | Status |
|------------|--------|
| No code changed | Confirmed |
| No tests changed | Confirmed |
| No endpoint behavior changed | Confirmed |
| No dashboard frontend changed | Confirmed |
| No token/scoring/ledger/report/pipeline behavior changed | Confirmed |
| Runtime artifacts cleaned (`ops/runtime_health_log.jsonl`, `ops/intake_tracking`) | Confirmed |
| Final git status clean | Confirmed |
| `ops/prf_queue/` untracked runtime-only directory | Confirmed excluded |

---

## Final Closure Verdict

- Diagnostic is **closed**
- Phase 2 dashboard behavior is **valid**
- The operator demo can proceed using the correct input procedure (fill `raw_card_text` before clicking Preview)
- No fix implementation is authorized under this slice
- The Phase 2 archived baseline at `dfbacd4` / `ai-risa-premium-report-factory-mvp-phase2-approved-save-queue-archive-lock-v1` remains the canonical release artifact, unchanged and intact

# AI-RISA Premium Report Factory — Button 1 Discovery Use Autofills Bouts Release Manifest v1

**Slice:** `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-release-manifest-v1`
**Release date:** 2026-05-02
**Branch:** `next-dashboard-polish`

---

## Commit chain

| Step | Commit | Tag |
|---|---|---|
| Design | `0f3c819` | `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-v1` |
| Design review | `c3980cc` | `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-design-review-v1` |
| Implementation | `e7edc98` | `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-implementation-v1` |
| Post-freeze smoke | `c0f295c` | `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-post-freeze-smoke-v1` |
| Final review | `0865557` | `ai-risa-premium-report-factory-button1-discovery-use-autofills-bouts-final-review-v1` |

---

## Files changed

| File | Change |
|---|---|
| `operator_dashboard/phase1_ops.py` | `_extract_event_fields` now includes additive `location` and normalized `bouts` pass-through in discovery row payload |
| `operator_dashboard/templates/index.html` | Button 1 discovery Use handler now hydrates metadata, source reference, Manual Input bout lines, and status messaging for both success and no-bouts branches |

---

## Delivered behavior

| # | Behavior | Status |
|---|---|---|
| 1 | Use pre-fills event metadata (`event_name`, `event_date`, `promotion`, `location`) | DELIVERED |
| 2 | Use pre-fills `source_reference` from selected discovery row | DELIVERED |
| 3 | Use fills Manual Input with one `Fighter A vs Fighter B` line per discovered bout | DELIVERED |
| 4 | Use success status directs operator to Parse Preview | DELIVERED |
| 5 | Use status includes selected event context and loaded bout count | DELIVERED |
| 6 | No-bouts Use branch clears Manual Input and shows fallback guidance | DELIVERED |
| 7 | Parse Preview after Use works on loaded bout text | DELIVERED |
| 8 | Save Selected (with approval) succeeds and Button 2 sees saved fight | DELIVERED |

---

## Smoke results

| Scenario | Result |
|---|---|
| Ares FC 39 Use fills metadata and Manual Input with `Aboubakar Jbalia vs Cherif Diatta` | PASS |
| Parse Preview succeeds from Use-loaded text | PASS |
| Save Selected succeeds with operator approval | PASS |
| Button 2 loads and shows saved Ares fight | PASS |
| Zero-bout Use fallback clears Manual Input and shows required message | PASS |

**Focused regression:** `tests/test_event_decomposition_adapter_regression.py` -> 5 passed, 0 failed.

---

## Constraints respected

- No `operator_dashboard/app.py` changes.
- No endpoint additions.
- No Button 2 or Button 3 feature expansion.
- Save path remains explicit and approval-gated.
- No hidden writes introduced by Use action.

---

## Release verdict

**RELEASED — Button 1 discovery Use autofills bouts v1 complete.**

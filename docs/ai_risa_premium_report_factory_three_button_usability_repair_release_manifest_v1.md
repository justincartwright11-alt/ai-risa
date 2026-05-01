# AI-RISA Premium Report Factory — Three-Button Usability Repair Release Manifest v1

**Slice:** `ai-risa-premium-report-factory-three-button-usability-repair-release-manifest-v1`
**Release date:** 2026-05-02
**Branch:** `next-dashboard-polish`

---

## Commit chain

| Step | Commit | Tag |
|---|---|---|
| Design | `adcef67` | `ai-risa-premium-report-factory-three-button-usability-repair-design-v1` |
| Design review | `44655dc` | `ai-risa-premium-report-factory-three-button-usability-repair-design-review-v1` |
| Implementation | `5f43f12` | `ai-risa-premium-report-factory-three-button-usability-repair-implementation-v1` |
| Post-freeze smoke | `1962edf` | `ai-risa-premium-report-factory-three-button-usability-repair-post-freeze-smoke-v1` |
| Final review | `c573cc6` | `ai-risa-premium-report-factory-three-button-usability-repair-final-review-v1` |

---

## Files changed

| File | Change |
|---|---|
| `operator_dashboard/app.py` | Parser separator loop + `looks_like_matchup` filter expanded for `vs.`, `versus`, `vs`, `v` |
| `operator_dashboard/templates/index.html` | Discovery rows panel, parsed/saved count spans, B2 empty msg, B3 pre-apply panel + all JS |

---

## Delivered repairs

| # | Repair | Status |
|---|---|---|
| 1 | Button 1 parser accepts `vs`, `vs.`, `v`, `versus` | DELIVERED |
| 2 | Missing `event_date` is warning, not blocker | DELIVERED |
| 3 | Discovery rows panel with Use button in Button 1 | DELIVERED |
| 4 | Parsed / ready / needs_review counts + save blocker messages in Button 1 | DELIVERED |
| 5 | Button 2 empty queue: "No saved fights yet. Use Button 1 first." | DELIVERED |
| 6 | Button 3 pre-apply panel: selected row, candidate, write preview, approval state | DELIVERED |
| 7 | No new features, no uncontrolled writes | CONFIRMED |

---

## Smoke results

| Scenario | Result |
|---|---|
| Button 1 parse `vs.` | PASS |
| Button 1 save with approval | PASS |
| Button 2 queue + generate | PASS |
| Button 3 pre-apply panel construct | PASS |

**Regression tests:** 253 passed, 0 failed.

---

## Constraints respected

- No Phase 4 scope.
- No billing.
- No hidden learning.
- No uncontrolled writes.
- All existing save/apply approval gates unchanged.

---

## Release verdict

**RELEASED — Three-button usability repair v1 complete.**

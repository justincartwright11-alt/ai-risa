# AI RISA Premium Report Factory — Global Engine-Pack Registry Wiring Design Review
**Slice:** `ai-risa-premium-report-factory-global-engine-pack-registry-wiring-design-review-v1`
**Date:** 2026-05-02
**Branch:** `next-dashboard-polish`
**Design commit reviewed:** `c3ba547`
**Design tag reviewed:** `ai-risa-premium-report-factory-global-engine-pack-registry-wiring-design-v1`
**Type:** Design review — docs-only. No code, no test, no template changes.

---

## Review Verdict

**APPROVED — proceed to implementation with clarifications noted below.**

All 13 design sections are complete, internally consistent, and safe relative to the scaffold smoke baseline at `c73680e`. No design section requires revision before implementation begins. Clarifications and implementation guidance are recorded in each section below.

---

## Section-by-Section Review

### Section 1 — Review of Locked Scaffold Baseline
**Status: APPROVED**

The baseline inventory is accurate and complete. All 8 scaffold modules are confirmed unimported by any live route, template, or PDF path at `c73680e`. The 43-test count matches the smoke artifact. No gaps.

**Clarification:** Implementation must verify baseline is still clean with `git status --short` and a full scaffold test run before any route file is touched.

---

### Section 2 — Engine Registry Wiring Goal
**Status: APPROVED**

The goal is precisely scoped. "Which engines are registered and available?" is the only question this layer answers. The three deferred questions (output readiness, report generation trigger, learning application) are correctly excluded.

**Clarification:** The phrase "availability" in API response keys is correct. Do not use "status" or "readiness" as key names — those imply gate decisions and are reserved for future layers.

---

### Section 3 — Button 1 Wiring Plan
**Status: APPROVED**

Additive-only. `build_button1_ranking_contracts()` is called for serialization only. `compute_composite_ranking_score()` and `build_ranked_matchup_rows()` are correctly excluded.

**Clarification 1:** The serialization of `RankingScoreContract` to `{ engine_id, label, required, active }` should treat `active` as a static `true` at this layer — contracts are all registered, none are conditionally disabled yet. Document this assumption in code comment.

**Clarification 2:** `label` is not a field on `RankingScoreContract` as designed. Implementation must derive a display label from `engine_id` (e.g., replace underscores with spaces, title-case) or add a `label` field to the contract. Resolve before implementing the serialization helper.

**Clarification 3:** No queue read or write is added. The `ranking_engine_availability` key is appended to the response dict after all existing logic completes. This ordering must be enforced in code review.

---

### Section 4 — Button 2 Wiring Plan
**Status: APPROVED WITH ONE CAUTION**

Additive-only for betting, generation, section manifest keys.

**Caution — `report_readiness_preview`:** `evaluate_report_readiness_status()` requires a populated report content payload to produce a meaningful result. At the Button 2 route, the report payload may be partially built or absent depending on queue state. Implementation must handle the case where `evaluate_report_readiness_status()` cannot be called meaningfully (e.g., no matched analysis record exists) and must return `"unavailable"` rather than raise an exception or return a misleading `blocked_missing_analysis`. This fallback case must be tested.

**Clarification 1:** `build_section_output_manifest()` returns a manifest of section-to-engine mappings derived from `SECTION_ENGINE_MAPPINGS`. This is static data. It does not require a live report payload and is safe to call unconditionally.

**Clarification 2:** All four sub-keys (`betting_engines`, `generation_engines`, `section_manifest`, `report_readiness_preview`) are nested under the single `engine_availability` key. This nesting must be consistent between the route response and any template or test that reads it.

**Clarification 3:** The `report_readiness_preview` label is correct. No template may render this value with language implying it is an active gate (e.g., "Report Status: blocked"). It must be rendered as "Readiness Preview:" with an informational badge only.

---

### Section 5 — Button 3 Wiring Plan
**Status: APPROVED**

Additive-only. `build_accuracy_calibration_contracts()` is called for serialization only. `evaluate_button3_gate()` is correctly excluded.

**Clarification 1:** Same label derivation issue as Button 1 — `approval_gate_required` is a bool field on the contract and can be serialized directly. `label` must be derived or added. Resolve consistently with Button 1 approach.

**Clarification 2:** Approval-gate-required engines (`btn3_approved_learning_gate`) must not have any clickable or actionable UI element at this layer. The badge is display-only.

---

### Section 6 — Registry-to-Runtime Contract Boundaries
**Status: APPROVED**

The boundary table is complete and unambiguous. The single permitted global-registry call (`to_manifest_rows()`) is correctly scoped to the optional manifest endpoint only.

**Clarification:** Add a comment in the implementation wherever a scaffold function is called that it is called "display-only — no gate enforcement, no side effects." This makes future review unambiguous.

---

### Section 7 — UI Visibility Plan
**Status: APPROVED**

Collapsible panels default-collapsed is the correct approach to preserve existing operator workflow.

**Clarification 1:** Panel collapse state must be managed with a simple CSS `details`/`summary` element or equivalent. No JavaScript state management framework is introduced at this layer.

**Clarification 2:** Panel section headings must include the word "Scaffold" or "Availability" to signal to the operator that these are informational panels, not live gate controls. Examples: "Ranking Engine Availability", "Calibration Engine Availability".

**Clarification 3:** The global `/registry-manifest` UI mention references the optional endpoint. If the endpoint is not added in the implementation slice, the UI panel for it is also not added. They are linked.

---

### Section 8 — API Visibility Plan
**Status: APPROVED**

Additive-only API contract is correct.

**Clarification 1:** The optional `/api/engine-registry-manifest` endpoint must be listed in a route comment as "operator-only, read-only, no database reads." If it is added, it must be covered by at least one test verifying response shape.

**Clarification 2:** The endpoint path `/api/engine-registry-manifest` (with hyphen) is preferred over `/api/engine_registry_manifest` (with underscore) for consistency with REST conventions. Lock the path before implementation.

---

### Section 9 — Non-Goals
**Status: APPROVED**

The 11-item non-goals list is complete. No gaps identified.

**Clarification:** Non-goals must be reviewed at PR time. Any implementation PR that touches a non-goal item (even partially) must be rejected and rescheduled as a future slice.

---

### Section 10 — Governance Guardrails
**Status: APPROVED**

All 8 guardrails are sound and enforceable.

**Clarification — Guardrail 8 (rollback is a one-file revert):** This guardrail must be verified during implementation by ensuring that:
- All route additions are isolated in the route handler functions (not extracted into new helpers imported from a shared module that would be harder to revert).
- Template additions are confined to a single clearly marked block in `index.html` per button section.

If a shared serialization helper is introduced (e.g., `_serialize_contract_list()`), it must live in `app.py` or the route file itself, not in a new shared module, so reversion is contained.

---

### Section 11 — Validation Plan
**Status: APPROVED**

All 8 checks are necessary and sufficient.

**Clarification 1:** The "no new runtime writes" check (grep for db/file/queue mutations) should be run as part of CI or documented as a manual pre-merge step. A simple `grep -r "csv\|write\|insert\|update\|save" [new files]` is sufficient.

**Clarification 2:** The "UI panels collapse by default" check must be verified by opening the dashboard in a browser after server restart, not just by code review. Add this to the smoke checklist.

**Clarification 3:** Add a ninth check: **New availability keys are present in API response without disrupting existing response key access.** Verify with a targeted API test that reads a known pre-existing key from the Button 1/2/3 response after wiring is added.

---

### Section 12 — Risks and Rollback Plan
**Status: APPROVED**

All 5 risks are correctly assessed. Rollback plan is clean.

**Clarification — Risk: `report_readiness_preview` misleads operator (Medium):** Given this is rated medium, implementation must include a visual treatment (e.g., a grey informational badge, not a red/green status badge) that visually distinguishes it from actionable gate indicators. This must be verified in the UI smoke step.

**Clarification — Circular import risk (Low):** Confirm at implementation start by running `python -c "from operator_dashboard.app import app"` after adding each import. If this raises a circular import error, the import must be moved inside the route function body (lazy import) rather than at the module level.

---

### Section 13 — Recommended First Implementation Slice
**Status: APPROVED**

The 5-step ordered implementation plan is correct. Steps 1–4 (route changes) committed separately from step 5 (template) is the right split.

**Clarification 1:** Step 4 (registry manifest endpoint) is optional and should be deferred to last within the route commit group. If it causes any complication, it can be dropped from this slice entirely and added in a follow-on slice.

**Clarification 2:** The label derivation decision (Section 3 Clarification 2 and Section 5 Clarification 1) must be resolved before step 1 begins. Decision: add a `label` derived property or helper to the scaffold dataclasses, or use a local label-map dict inside the serialization helper. This is a pre-implementation decision, not a design change.

**Clarification 3:** Confirm that `build_section_output_manifest()` is already implemented and returns a list. Read `prf_section_output_contracts.py` before starting step 2.

---

## Cross-Cutting Review Findings

### Finding 1 — Label field gap (Medium, actionable before implementation)
`RankingScoreContract`, `BettingOutputContract`, `GenerationOutputContract`, `AccuracyCalibrationContract` (and similar) do not have an explicit `label` field. The design assumes a `{ engine_id, label, required, active }` serialization shape. Implementation must resolve this consistently before writing any serialization code.

**Recommended resolution:** Add a local `_engine_label_map` dict in the route handler or in a `_serialize_contract_list()` helper function that derives display labels from engine IDs. Do not modify the scaffold contract dataclasses — that would be a scaffold layer change outside this slice's scope.

### Finding 2 — `report_readiness_preview` fallback case (Medium, actionable before implementation)
The design does not specify the fallback value when `evaluate_report_readiness_status()` cannot be called (missing payload). This must be `"unavailable"` and must be tested.

**Recommended resolution:** Wrap the `evaluate_report_readiness_status()` call in a try/except or an explicit pre-check for payload completeness. Return `"unavailable"` if the check fails. Add one test for this case in `test_app_backend.py`.

### Finding 3 — Optional endpoint decision (Low, pre-implementation)
The design marks `/api/engine-registry-manifest` as optional. This ambiguity should be resolved before implementation starts to avoid mid-slice scope drift.

**Recommended resolution:** Implement it. It is a 5-line route handler with no database reads and a simple test. Deferring it would leave the global registry unverifiable at runtime.

---

## Summary of Pre-Implementation Actions Required

| Action | Priority | Owner |
|---|---|---|
| Decide label derivation approach for contract serialization | High | Implementation slice start |
| Confirm `build_section_output_manifest()` returns a list (read file) | High | Implementation slice start |
| Decide `/api/engine-registry-manifest` in or out of this slice | Medium | Before route code is written |
| Resolve `report_readiness_preview` fallback to `"unavailable"` | High | Before Button 2 route code is written |
| Add 9th validation check (existing keys still accessible after wiring) | Medium | Validation plan addendum |

---

## Scope Confirmation

This review is **docs-only**. No changes were made to:

- Any scaffold module
- Any route handler
- `app.py`
- `index.html`
- Any test file
- Any existing doc

---

## Next Safe Slice

Review approved. Proceed to implementation.

**Next slice:** `ai-risa-premium-report-factory-global-engine-pack-registry-wiring-implementation-v1`

Implementation order (confirmed from design Section 13 + clarifications above):

1. Resolve label derivation approach (pre-implementation decision, no file changes required)
2. Routes: Button 1 `ranking_engine_availability` + Button 2 `engine_availability` + Button 3 `calibration_engine_availability` + optional `/api/engine-registry-manifest` — commit together
3. Template: collapsed operator-only availability panels in `index.html` — separate commit
4. Full test suite run + manual smoke
5. Lock + tag

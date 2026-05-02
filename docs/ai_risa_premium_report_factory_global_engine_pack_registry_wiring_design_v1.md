# AI RISA Premium Report Factory — Global Engine-Pack Registry Wiring Design
**Slice:** `ai-risa-premium-report-factory-global-engine-pack-registry-wiring-design-v1`
**Date:** 2026-05-02
**Branch:** `next-dashboard-polish`
**Baseline commit:** `c73680e`
**Baseline tag:** `ai-risa-premium-report-factory-global-engine-pack-scaffold-integration-smoke-v1`
**Type:** Design-only. No code, no test, no template changes.

---

## 1. Review of Locked Scaffold Baseline

At `c73680e` all 8 scaffold contract modules coexist cleanly with 43 tests passing and zero runtime wiring:

| Scaffold Module | Engine Family | Tests |
|---|---|---|
| `prf_engine_registry.py` | Global registry (6 families) | 6 |
| `prf_section_output_contracts.py` | Combat Intelligence / Fighters Analytics | 5 |
| `prf_report_readiness_scaffold.py` | Report readiness + sparse-case completion | 7 |
| `prf_ranking_scaffold.py` | Button 1 ranking (7 engine IDs) | 5 |
| `prf_betting_market_scaffold.py` | Button 2 betting market (8 engine IDs) | 5 |
| `prf_generation_scaffold.py` | Generation / audience-specific output (12 IDs) | 5 |
| `prf_global_ledger_scaffold.py` | Global database / ledger (9 engine IDs) | 5 |
| `prf_accuracy_calibration_scaffold.py` | Button 3 accuracy / calibration | 5 |

None of these modules are imported by any live Flask route, template, report builder, or PDF path. They exist only as contracts and tests.

---

## 2. Engine Registry Wiring Goal

The goal of the first live wiring layer is to **expose engine registry availability information** to the Premium Report Factory operator dashboard without changing any live decision, write, report generation, or learning behavior.

This layer answers one question for each button: *which scaffold engines are registered and available?*

It does not answer: *are their outputs ready?*, *should a report be generated?*, *should a queue record be saved?*, or *should learning be applied?*

The registry wiring layer is strictly read-only and display-only.

---

## 3. Button 1 Wiring Plan

### Goal
Show ranking-engine availability to the operator when viewing the Button 1 (fighter intake / queue) panel.

### What changes
- Import `build_button1_ranking_contracts()` from `prf_ranking_scaffold` inside the Button 1 API route handler.
- Call it to retrieve the list of `RankingScoreContract` objects.
- Append a `ranking_engine_availability` key to the existing Button 1 API response payload — a list of `{ engine_id, label, required, active }` entries derived from the contracts.
- No change to how the queue record is read, filtered, displayed, or saved.

### What does not change
- Queue save logic.
- Queue read logic.
- Fighter intake record structure.
- Ranking score computation (`compute_composite_ranking_score` is not called at this layer).
- `build_ranked_matchup_rows()` is not called at this layer.
- No automatic writes to any global database table.
- No matchup ranking results are surfaced to any customer-facing path.
- No PDF or report content is generated.

### Response shape (additive only)
```json
{
  "ranking_engine_availability": [
    { "engine_id": "rank_composite_score", "label": "Composite Ranking Score", "required": true, "active": true },
    { "engine_id": "rank_stylistic_alignment", "label": "Stylistic Alignment", "required": false, "active": true },
    ...
  ]
}
```

The existing Button 1 response keys are preserved verbatim. The new key is appended and is additive.

---

## 4. Button 2 Wiring Plan

### Goal
Show combat / betting / generation / readiness engine availability to the operator when viewing the Button 2 (premium report factory) panel.

### What changes
- Import `build_betting_market_contracts()` from `prf_betting_market_scaffold`.
- Import `build_generation_contracts()` from `prf_generation_scaffold`.
- Import `build_section_output_manifest()` from `prf_section_output_contracts`.
- Import `evaluate_report_readiness_status()` from `prf_report_readiness_scaffold` — called in display-only mode (no output written, no gate enforced).
- Append an `engine_availability` key to the existing Button 2 API response payload containing:
  - `betting_engines`: list of `{ engine_id, label, required, active }` from betting contracts.
  - `generation_engines`: list of `{ engine_id, label, required, active }` from generation contracts.
  - `section_manifest`: list of section-to-engine mappings from `build_section_output_manifest()`.
  - `report_readiness_preview`: the `status` string from `evaluate_report_readiness_status()` computed on the current report payload in read-only / preview mode.

### What does not change
- Customer-ready PDF generation logic.
- `allow_draft` gate.
- `analysis_source_status` / `analysis_type` computation.
- `content_preview_rows` construction.
- Any existing Button 2 response keys.
- No writes to queue records, report records, or any database table.
- No new customer outputs.
- No billing events.

### Response shape (additive only)
```json
{
  "engine_availability": {
    "betting_engines": [...],
    "generation_engines": [...],
    "section_manifest": [...],
    "report_readiness_preview": "draft_only"
  }
}
```

`report_readiness_preview` is labeled *preview* explicitly so it is never confused with a gate decision. The existing gate logic (`allow_draft`, PDF block) is unchanged.

---

## 5. Button 3 Wiring Plan

### Goal
Show accuracy / calibration scaffold availability to the operator when viewing the Button 3 (accuracy review) panel.

### What changes
- Import `build_accuracy_calibration_contracts()` from `prf_accuracy_calibration_scaffold`.
- Append a `calibration_engine_availability` key to the existing Button 3 API response payload — a list of `{ engine_id, label, required, approval_gate_required, active }` entries.

### What does not change
- No learning updates are applied.
- No calibration writes are executed.
- `evaluate_button3_gate()` is not called at this layer.
- Pattern memory update logic is not triggered.
- Operator approval gate logic for learning is not changed.
- No customer-facing behavior changes.
- All existing Button 3 response keys are preserved.

### Response shape (additive only)
```json
{
  "calibration_engine_availability": [
    { "engine_id": "btn3_accuracy_segment", "label": "Accuracy Segment", "required": true, "approval_gate_required": false, "active": true },
    { "engine_id": "btn3_approved_learning_gate", "label": "Approved Learning Gate", "required": true, "approval_gate_required": true, "active": true },
    ...
  ]
}
```

---

## 6. Registry-to-Runtime Contract Boundaries

The wiring layer observes the following strict boundaries:

| Boundary | Allowed at this layer | Deferred to future layer |
|---|---|---|
| Read engine contract definitions | Yes | — |
| Append availability lists to API responses | Yes | — |
| Call scoring / computation functions | No | Future ranking integration slice |
| Enforce readiness gates | No | Future report readiness integration slice |
| Trigger PDF generation | No | Existing behavior only |
| Write to queue / database | No | Future ledger integration slice |
| Apply learning / calibration | No | Future Button 3 integration slice |
| Surface data to customer paths | No | Controlled by existing gates only |
| Change operator approval gate behavior | No | Preserved as-is |

The `EngineRegistry.to_manifest_rows()` method on `build_global_engine_pack_registry()` may be called globally to produce a single registry manifest surfaced to an operator-only metadata endpoint. This is the only global-registry call permitted at this layer.

---

## 7. UI Visibility Plan

### Button 1
A collapsible **Ranking Engines** panel in the Button 1 operator view shows the `ranking_engine_availability` list. Each row: engine ID, label, required badge, active badge. This panel is visible only to operator sessions. It has no customer-facing render path.

### Button 2
A collapsible **Engine Availability** panel in the Button 2 operator view shows:
- Betting engine list
- Generation engine list
- Section manifest (14 sections with contributing engine IDs)
- Report readiness preview badge (`customer_ready` / `draft_only` / `blocked_missing_analysis`) displayed as informational only, not as a gate

All panels are collapsible and default to collapsed so they do not disrupt existing operator workflow.

### Button 3
A collapsible **Calibration Engines** panel shows the `calibration_engine_availability` list. Approval-gate-required engines are highlighted with an operator-attention badge. No action is wired to these badges.

### Global Registry (optional)
An operator-only `/registry-manifest` endpoint may be added that returns `build_global_engine_pack_registry().to_manifest_rows()`. This is not customer-facing and requires no auth change since it is already behind the operator session boundary.

---

## 8. API Visibility Plan

### Additive response keys
All new keys are appended to existing route response dicts. No existing key is renamed, removed, or changed.

### No new writes
All new route logic is read-only. `GET` semantics are preserved on all affected routes.

### Global registry manifest endpoint (optional, operator-only)
```
GET /api/engine-registry-manifest
Response: { "engines": [ { engine_id, group, label, button, required } ] }
```

This endpoint calls `build_global_engine_pack_registry().to_manifest_rows()` and returns the result. It makes no database reads and has no side effects. It is behind the existing operator session check.

### No customer-facing API changes
No customer-visible route, PDF endpoint, or report download endpoint is changed.

---

## 9. Non-Goals

The following are explicitly out of scope for this wiring layer:

- Computing live ranking scores for fighters.
- Enforcing readiness gates on reports beyond the existing logic.
- Triggering PDF generation from engine availability data.
- Writing engine outputs to any database table.
- Applying calibration or learning updates.
- Surfacing engine availability to customer-facing views.
- Changing Button 1/2/3 save behavior.
- Adding billing events.
- Changing operator approval gate logic.
- Adding new authentication or authorization layers.
- Removing or renaming any existing API response keys.

---

## 10. Governance Guardrails

1. **Operator-only visibility.** All new UI panels and API keys are gated behind the existing operator session boundary. No new session logic is added.
2. **Additive-only API contract.** Existing response keys are frozen. New keys may be added but none may be removed or modified.
3. **No write path.** Any code added in this layer must be reviewed to confirm it contains no database writes, queue updates, file writes, or learning triggers before merge.
4. **Approval gate preservation.** `approval_gate_required` contract fields must not be bypassed or overridden by this layer. They are display-only metadata.
5. **Scaffold tests remain green.** All 43 scaffold tests must pass after wiring is added.
6. **Existing test suite remains green.** All pre-existing Button 1/2/3 backend tests must pass after wiring is added.
7. **Customer PDF behavior frozen.** The `allow_draft` and customer-ready PDF gate must produce identical output before and after this wiring layer is added.
8. **Rollback is a one-file revert.** The wiring additions must be isolated to the route handler functions such that reverting them does not require changes to scaffold modules, test files, or templates.

---

## 11. Validation Plan

The following checks must all pass before the wiring implementation slice is considered locked:

| Check | Method |
|---|---|
| Registry availability surfaced without queue/report/result behavior change | Manual smoke: call Button 1/2/3 endpoints before and after; verify only additive keys appear in responses |
| All 43 scaffold tests still pass | `pytest operator_dashboard/test_prf_*.py` |
| All existing Button 1/2/3 tests still pass | Full backend test suite: `pytest operator_dashboard/` |
| No new runtime writes | Code review: grep for db write / file write / queue mutation calls in all new code |
| No customer PDF behavior change | Manual smoke: generate a draft report and a customer-ready report; verify output is identical to pre-wiring baseline |
| No calibration behavior change | Manual smoke: trigger Button 3 review; verify no learning updates are applied |
| Global registry manifest endpoint returns correct shape | `GET /api/engine-registry-manifest` returns list of all registered engine IDs with correct group labels |
| UI panels collapse by default | Visual check: all new engine availability panels are collapsed on first load |

---

## 12. Risks and Rollback Plan

### Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Scaffold import added to route causes circular import | Low | Scaffold modules have no Flask/app dependencies; import is one-directional |
| `report_readiness_preview` value misleads operator into thinking gate has changed | Medium | Label explicitly as "preview"; add tooltip or badge note; never expose to customer path |
| `ranking_engine_availability` list grows stale if contracts change | Low | List is generated from live contracts at request time, not cached |
| New endpoint `/api/engine-registry-manifest` adds undocumented surface area | Low | Endpoint is operator-only, read-only, and returns no PII or sensitive data |
| Template change required to render new UI panels breaks existing layout | Medium | Panels are additive DOM elements; existing layout is preserved using collapsible containers |

### Rollback Plan

1. Revert the route handler changes (remove new import lines and new response keys).
2. Remove `/api/engine-registry-manifest` endpoint if added.
3. Remove the new collapsible panel template blocks.
4. Re-run full test suite to confirm return to baseline.

Scaffold modules are not touched during rollback. Their tests remain passing. The rollback leaves the system at the `c73680e` scaffold smoke baseline.

---

## 13. Recommended First Implementation Slice

**Slice name:** `ai-risa-premium-report-factory-global-engine-pack-registry-wiring-implementation-v1`

**Implementation order within the slice:**

1. Add `ranking_engine_availability` to Button 1 route response — import `build_button1_ranking_contracts`, serialize to list, append to response dict.
2. Add `engine_availability` to Button 2 route response — import betting, generation, section output, and readiness modules; serialize and append.
3. Add `calibration_engine_availability` to Button 3 route response — import accuracy/calibration contracts; serialize and append.
4. Add `/api/engine-registry-manifest` operator-only endpoint — import `build_global_engine_pack_registry`; return `to_manifest_rows()`.
5. Add collapsible UI panels to `index.html` for each button's availability list (template changes last, after route contracts are verified).
6. Run full test suite.
7. Run manual smoke on Button 1/2/3 responses and PDF generation paths.

**Each step is individually committable.** The slice should not be merged as a single large commit. Steps 1–4 (route changes) can be committed together; step 5 (template) is a separate commit.

**Do not begin implementation until this design is locked and tagged.**

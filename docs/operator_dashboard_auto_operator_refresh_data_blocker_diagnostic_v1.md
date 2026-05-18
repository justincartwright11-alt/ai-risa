# Operator Dashboard Auto-Operator Refresh Data Blocker Diagnostic v1

## 1) Blocker Summary
Reported blocker: dashboard loads but workflow cards remain at zeros / "Waiting for refresh".

Diagnostic result at checkpoint `c1276ba` (`operator-dashboard-button-functionality-target-runtime-confirmation-v1`):
- Dashboard route and button actions are functional.
- The specific reported card text surface (e.g., "Waiting for refresh", "Ready to save", "Customer Ready", "Rows scanned") is **not present** in current `index.html` runtime UI.
- Current preview endpoint contracts return zero summaries under runtime-context defaults and current source data mapping.

## 2) Reproduction Steps
1. Start app in target runtime: `python operator_dashboard/app.py` on `127.0.0.1:5050`.
2. Fresh browser cycle: `about:blank` -> `http://127.0.0.1:5050/`.
3. Observe initial page-load network behavior.
4. Probe for reported card labels in rendered body text.
5. Click `Find Fights`, `Generate Report`, `Find Results`.
6. Capture console/page errors and API response statuses.
7. Call `/api/local-ai/orchestrator/workflow-preview` directly for each source button and inspect `jobs[0].output_preview.summary`.

## 3) Dashboard Cards Affected
Reported cards:
- Find Fights: Ready to save / Needs review / Blocked / Waiting for refresh
- Generate PDFs: Customer Ready / Not Ready / Waiting for refresh
- Find Results & Compare: Rows scanned / Results found / Needs source / Conflicts / Ready to compare / Waiting for refresh

Observed in current runtime UI:
- These exact card labels are not present in current `operator_dashboard/templates/index.html` surface.
- Current UI shows three buttons and click-driven status panels.

## 4) Expected Behavior
- Auto-operator dashboard cards hydrate/refresh with real counts.
- "Waiting for refresh" clears automatically after data hydration.
- Values align with backend preview/queue/result state.

## 5) Actual Behavior
- On page load, dashboard renders static 3-button surface.
- No auto-refresh API calls fire on initial load.
- Reported card labels are absent in current page text.
- On button click, preview calls execute and return status summaries, currently with zero metrics in key fields.

## 6) Frontend JS Findings
From `operator_dashboard/templates/index.html`:
- No `setInterval`/polling loop for auto-refresh hydration of top-level workflow cards.
- No page-load fetch that hydrates the reported "Waiting for refresh" card surface.
- Data fetch is click-driven via:
  - `handleButton1Click()`
  - `handleButton2Click()`
  - `handleButton3Click()`
- `renderSimpleWorkflowSummary(...)` displays job-count/gate summary text, not the reported auto-operator metric card set.

## 7) Backend Endpoint Findings
Endpoint reachability and click-flow calls:
- `POST /api/local-ai/orchestrator/workflow-preview` -> `200` (during button flows)
- `POST /api/local-ai/gate1/save-fights/approved-save-writer-preview` -> `200`
- `POST /api/global-fighters/known-records/loader-preview` -> `200`
- `POST /api/local-ai/gate1/save-fights/dry-run-apply-preview` -> `200`

Direct workflow-preview checks (`use_runtime_context=true`, `execute_preview=true`) returned:
- Button1 summary: `discovered_count=0`, `ready_for_report_count=0`, etc.
- Button2 summary: `selected_fight_count=0`, `report_ready_count=0`, etc.
- Button3 summary: `total_rows=0`, `Results Found=0`, `Needs Source=0`, `Ready to Compare=0`.

## 8) Data-Source / Path Findings
Runtime context loader sources:
- `event_coverage_queue.csv` exists (small dataset)
- `fighter_intake_unresolved_queue.csv` exists (~31 rows)
- `one_samurai_1_bouts.csv` exists
- `ops/accuracy/accuracy_ledger.json` missing

Key mapping observations:
- Button2 selected refs are derived from `fight_key` / `fight_name`, but `one_samurai_1_bouts.csv` columns are `red_fighter/blue_fighter/...`; selected refs resolve empty -> zero selected_fight_count.
- Button1 runtime payload uses `candidate_rows`, but adapter summary computes from `discovered_rows` / `extracted_rows` defaults -> zero counters.
- Button3 runtime uses accuracy ledger waiting rows; ledger file missing -> zero result rows.

## 9) Browser Console Findings
- Browser `pageerror`: none.
- Browser console `error`: none.
- No blocking frontend runtime exceptions observed.

## 10) Runtime / Port Findings
- Runtime verified: `C:/Users/jusin/AppData/Local/Python/pythoncore-3.14-64/python.exe`
- URL/port verified: `http://127.0.0.1:5050`
- Server request logs match browser interactions.
- No evidence of wrong port.

## 11) Suspected Root Cause
Primary suspected root causes:
1. **Surface mismatch**: reported "Waiting for refresh" card UI appears to be from an older auto-operator dashboard surface not present in current template.
2. **Hydration contract gap**: current UI is click-driven and does not auto-poll/hydrate those reported cards on load.
3. **Runtime-context/data mapping gaps** causing zero summaries even when some CSV source files exist:
   - Button1 adapter expects different summary source keys than runtime loader provides.
   - Button2 selected fight extraction relies on keys absent from current bout CSV schema.
   - Button3 depends on missing `ops/accuracy/accuracy_ledger.json`.

## 12) Wrong Runtime / Stale Browser / Empty Data Source Assessment
- Wrong runtime instance: not indicated.
- Stale browser/cache: fresh cycle performed; not indicated for this run.
- Empty/unmapped data source: implicated (especially Button2 schema mismatch and missing accuracy ledger).
- Older/alternate dashboard expectation: implicated by label mismatch (reported strings absent in current code/runtime surface).

## 13) Severity Classification
**CRITICAL DASHBOARD DATA / AUTO-REFRESH BLOCKER** (diagnosed).
Reason: management launch decision requires reliable operator-facing workflow state, and current observed/expected hydration contract is inconsistent.

## 14) Launch Impact
Paid-pilot GO/NO-GO remains blocked pending remediation or explicit acceptance of current click-only zero-summary behavior.

## 15) Recommended Repair Slice Name
`operator-dashboard-auto-operator-refresh-data-critical-repair-v1`

## 16) Exact Repair Scope (If Confirmed)
Repair scope should stay narrow:
1. Align dashboard surface expectations and implemented UI contract (auto-card hydration vs click-only status).
2. Add explicit page-load refresh flow (if required by product decision).
3. Fix runtime-context -> adapter summary mapping for Button1 counters.
4. Fix Button2 selected-fight extraction mapping for current CSV schema.
5. Define/restore Button3 source ledger contract or clear fail-closed messaging.
6. Preserve governance and no-mutation safety constraints.

## 17) Tests Needed For Repair
1. Page-load auto-refresh smoke test (or explicit no-auto-refresh contract test if intentionally disabled).
2. Card hydration contract test for Button1/2/3 summary fields.
3. Runtime-context mapping tests for actual CSV schemas in workspace.
4. Missing-ledger fail-closed UI message test for Button3.
5. Browser integration test validating non-zero when source fixtures exist.

## 18) Final Blocker Verdict
Blocker is **diagnosed and confirmed as a data-hydration/contract mismatch**, not a button-click failure.

- Buttons are clickable and endpoint calls succeed.
- Reported auto-operator card surface is not present in current runtime template.
- Current runtime-context summaries resolve to zeros under present mappings/data availability.

Verdict: **Do not resume paid-pilot management GO/NO-GO yet. Open repair slice only for targeted hydration/data-contract remediation.**

---

## Diagnostics Run
- Fresh runtime/browser load confirmation on `127.0.0.1:5050`
- Network/API capture on load and click
- Browser console/pageerror capture
- Direct Flask test-client endpoint probes
- Source-data file/path checks
- Targeted tests proving zero-state contract currently expected:
  - `test_no_fake_fights_are_created`
  - `test_no_fake_reports_are_created`
  - `test_no_fake_results_are_created`
  - Result: `3 passed`

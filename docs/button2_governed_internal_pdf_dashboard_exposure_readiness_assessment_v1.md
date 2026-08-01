# Button 2 Governed Internal PDF Dashboard Exposure Readiness Assessment v1

## 1. Executive Verdict

READY_WITH_BLOCKERS

This assessment records current readiness only. It does not authorize implementation, customer generation, customer release, production launch, or any permanent mutation.

## 2. Proven Baseline

- Closure commit: `35299ac`.
- Locked route-integration commit: `9f7a824`.
- Endpoint: `POST /api/button2/governed-internal-pdf/generate-v1`.
- Live-route proof: `BUTTON2_GOVERNED_INTERNAL_PDF_LIVE_ROUTE_PROOF=PASS`.
- Visual artifact proof: `BUTTON2_GOVERNED_INTERNAL_PDF_VISUAL_ARTIFACT_PROOF=PASS`.
- Classification: fictional local fixture, internal/test-only, governed internal test PDF.
- Customer-ready count remains zero for this route and fixture.

The proven route requires local fixture mode, a server-side writable internal output root, exact fixture/report identity, and `internal_test_artifact_acknowledged=true`. It generates one deterministic artifact, blocks an existing target with HTTP 422, and does not overwrite or persist queue, ledger, learning, calibration, GCID, or customer state.

## 3. Existing Button 2 Interface Boundary

### Existing internal-preview panel

`operator_dashboard/templates/index.html` contains `#b2-internal-preview-panel`, rendered by `button2RenderInternalPreview()`. It displays governed preview metadata including report ID, report version, fixture identity, prediction schema, structured prediction, immutable provenance, and internal/test-only read-only status. Its available action is `Select Internal Preview for Button 3`.

### Existing customer queue/report controls

The Button 2 result area contains canonical queue refresh, event filtering, row selection, select-all-ready, full-event selection, operator approval, and `Generate Selected PDFs`. The main Button 2 card describes generation of a customer-ready PDF and its action is `Generate Report`.

### Current selected internal-report state

The internal preview is represented by `window.button2InternalPreviewRows`. Selecting it creates `window.button3SelectedGeneratedReportPreview` with `internal_test_only=true`, `read_only=true`, `preview_only=true`, and customer release unavailable. This state is for Button 3 comparison preview; it is not an internal PDF generation request state.

### Current PDF-generation controls

`button2GenerateSelectedBatch()` requires the existing `b2-operator-approval` checkbox and sends selected matchup IDs to `/api/button2/generate-selected-batch`. That is a multi-row customer-oriented generation path. The template has no control that calls `/api/button2/governed-internal-pdf/generate-v1`.

### Existing result/status surfaces

Existing surfaces include `b2-status`, `b2-generation-result-panel`, queue-row status/path/open-link cells, and the internal preview panel. They report batch generated/failed/skipped counts and delivery flags, but do not render the governed route's required artifact classification, report identity/version, hash, signature, collision reason, or explicit no-PDF blocked state.

### Boundary assessment

The template distinguishes an internal preview from Button 2's customer-oriented queue flow by label and preview metadata, but it does not yet distinguish a governed internal PDF generation control from customer generation. The existing internal preview is not itself a safe exposure of the proven route.

## 4. Proposed Operator Workflow

1. Select the governed internal preview.
2. Review the internal/test warnings.
3. Acknowledge the fictional internal artifact explicitly.
4. Request one internal PDF.
5. Receive generated-artifact metadata.
6. See a visible collision or blocked state when generation is refused.
7. Take no customer-release action; no such action is present in this control.

## 5. Required UI Controls

The future narrow surface must contain:

- Governed internal report identity display.
- Report version display.
- Prominent `INTERNAL TEST FIXTURE` warning.
- Prominent `NOT FOR CUSTOMER RELEASE` warning.
- Explicit, unchecked-by-default acknowledgement checkbox.
- One `Generate Internal Test PDF` button.
- Generated-artifact result panel.
- Deterministic collision message.
- Disabled state while the request is running.
- No customer-release control.

## 6. Output-Root Boundary

`AI_RISA_INTERNAL_PDF_OUTPUT_ROOT` must be configured server-side only. The browser must never enter or submit an output root. The request must not accept a path, filename, extension, or overwrite instruction. The operator UI may show only `configured` or `not configured` status; an absolute filesystem path should not be unnecessarily displayed.

The existing template displays runtime output-root values in the general preflight panel. That display must not be reused for the narrow internal control as a substitute for the required internal-root status boundary.

## 7. Request Contract

The UI may send exactly these fields:

- `fixture_id`;
- `report_id`;
- `report_version`;
- `internal_test_artifact_acknowledged: true`.

The UI must not send or accept:

- output path;
- filename;
- extension;
- overwrite flag;
- customer-ready flag;
- customer-release flag;
- arbitrary report content.

## 8. Button-State Rules

Generation must be disabled when any of the following is true:

- no internal preview is selected;
- report identity or version is wrong;
- acknowledgement is unchecked;
- fixture mode is unavailable;
- internal output root is unavailable;
- a request is in progress;
- a successful deterministic artifact already exists;
- the backend returned a blocked state.

## 9. Response Rendering

### Success

The result panel must display:

- internal artifact classification;
- filename;
- report ID and version;
- file size;
- SHA-256;
- PDF signature status;
- generation count;
- `customer_release_authorized=false`;
- `queue_write_performed=false`;
- `artifact_overwritten=false`.

### Blocked

The result panel must display:

- blocked reason;
- no PDF generated;
- no overwrite;
- operator next action.

## 10. Collision Behavior

A second click must not silently rename the artifact and must not overwrite it. HTTP 422 or an equivalent blocked response must be visible. Prior artifact metadata may remain visible, but it must be marked as already existing. The UI must not automatically retry.

## 11. Customer-Boundary Separation

The new control must not:

- enter existing customer PDF batch selection;
- change the customer-ready count;
- mark a report customer ready;
- enable customer delivery;
- reuse customer-release language as an approval state;
- invoke `/api/button2/generate-selected-batch` or another existing customer generation endpoint.

## 12. Safety and Governance Gates

The following flags must remain false:

```text
customer_ready_possible = false
customer_release_authorized = false
queue_write_performed = false
learning_applied = false
calibration_applied = false
accuracy_ledger_written = false
gcid_written = false
model_weights_changed = false
fighter_ratings_changed = false
prediction_logic_changed = false
artifact_overwritten = false
permanent_mutation_performed = false
```

## 13. Accessibility and Operator Clarity

The control must use plain-language warnings. It must not use an ambiguous `Generate Report` label; the button text must explicitly say internal/test. Blocked reasons must be readable, and status must not rely only on colour. The acknowledgement checkbox must never be preselected.

## 14. Proven Blockers

### Blocker 1: Existing Button 2 control is customer-oriented and batch-capable

- Owning file: `operator_dashboard/templates/index.html`.
- Owning section/functions: Button 2 result area; `button2GenerateSelectedBatch()`.
- Observed limitation: the card says `customer-ready PDF report`; the controls support multiple selected rows, full-event selection, operator approval, and `Generate Selected PDFs`; the handler calls `/api/button2/generate-selected-batch`.
- Smallest remediation: add a separate, single-artifact internal/test control that does not share the customer batch selection or endpoint.

### Blocker 2: Internal preview has no governed PDF-generation action

- Owning file: `operator_dashboard/templates/index.html`.
- Owning section/functions: `#b2-internal-preview-panel`; `button2RenderInternalPreview()`; `button2SelectInternalPreview()`.
- Observed limitation: the only internal-preview action selects a report for Button 3 comparison preview and explicitly records preview-only state; no acknowledgement checkbox, internal/test generation button, governed route call, or governed artifact result panel exists.
- Smallest remediation: add the narrow selection, acknowledgement, request, disabled-state, and result rendering flow for the proven endpoint.

### Blocker 3: Governed route is not wired to the dashboard

- Owning file: `operator_dashboard/app.py`.
- Owning function: `button2_governed_internal_pdf_generate_v1()`.
- Observed limitation: the endpoint exists and is proven, but the inspected template has no request to `/api/button2/governed-internal-pdf/generate-v1`.
- Smallest remediation: wire only the proposed internal/test UI request to this existing route; do not alter the route or adapters.

### Blocker 4: General preflight exposes an output-root value

- Owning file: `operator_dashboard/templates/index.html`.
- Owning section: `#runtime-preflight-panel`.
- Observed limitation: the general display renders `runtime_preflight.button2_pdf_output_root.value`, which is broader than the proposed internal control's configured/not-configured-only output-root boundary.
- Smallest remediation: keep the new internal control server-configured and status-only; do not expose an absolute internal output path through it. Any broader preflight change requires separate authorization.

## 15. Smallest Implementation Slice

Recommend one future implementation slice that adds only the governed internal/test exposure and its focused test. It must not modify the fixture, adapters, renderer, Button 1, or Button 3.

Preferred authorized files:

- `operator_dashboard/templates/index.html`;
- `operator_dashboard/test_button2_governed_internal_pdf_dashboard_exposure_v1.py`.

Modify `operator_dashboard/app.py` only if a read-only configuration-status endpoint is strictly required. The future slice must not change the existing governed route contract.

## 16. Proposed Targeted Test

The exact future command is:

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_dashboard_exposure_v1.py
```

This assessment does not run that command.

## 17. Explicit Exclusions

This assessment does not authorize:

- customer-ready classification;
- customer release;
- production generation;
- bulk generation;
- caller-controlled paths;
- overwrite;
- canonical output directories;
- queue or report-ledger writes;
- learning;
- calibration;
- accuracy-ledger writes;
- GCID writes;
- deployment.

## 18. Final Verdict

BUTTON2_GOVERNED_INTERNAL_PDF_DASHBOARD_EXPOSURE=READY_WITH_BLOCKERS

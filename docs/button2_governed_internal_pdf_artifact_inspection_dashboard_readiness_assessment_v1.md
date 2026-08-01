# Button 2 Governed Internal PDF Artifact Inspection Dashboard Readiness Assessment v1

## 1. Executive verdict

READY_WITH_BLOCKERS

The read-only inspection endpoint, planner, adapter, route contract, and live proof are complete. The existing Governed Internal Report Preview section is the correct containment location, but dashboard exposure is not yet implemented or tested. The smallest safe next step is an isolated read-only status control and focused dashboard test.

This assessment defines readiness only. It does not implement or authorize UI changes, lifecycle mutation, customer release, or deployment.

## 2. Proven baseline

- Proof-closure commit: `3ac5c48`
- Implementation commit: `b517d8952b395074b95afdb24d23621f1d4efc66`
- Endpoint: `POST /api/button2/governed-internal-pdf/inspect-v1`
- Planner: `build_button2_governed_internal_pdf_inspection_plan_v1`
- Adapter: `inspect_button2_governed_internal_pdf_artifact_v1`
- Request contract: exactly `fixture_id`, `report_id`, and `report_version`
- Proven states: `ABSENT`, `ACTIVE_INTERNAL_TEST_ARTIFACT`, and bounded blocked/corrupt states
- Live proof established no artifact mutation, no generation, no archive, no removal, no overwrite, no customer release, and no unrestricted filesystem disclosure
- `build_button2_governed_internal_pdf_preflight_v1` still blocks an existing target with `proposed_output_target_exists`

## 3. Dashboard purpose

A future dashboard control may inspect and display the bounded state of the server-derived deterministic governed internal PDF artifact:

- not generated;
- present and valid;
- blocked, corrupt, or mismatched;
- bounded artifact metadata.

It must not generate automatically, archive, remove, delete, rename, move, copy, overwrite, regenerate, repair, quarantine, scan directories, expose unrestricted paths, or mutate lifecycle state.

## 4. UI location

The control should live only inside the existing `Governed Internal Report Preview` section and its `b2-governed-internal-pdf-control` container in `operator_dashboard/templates/index.html`.

It must remain separate from customer queue rows, `Generate Selected PDFs`, customer delivery or release controls, and Button 3 comparison controls. The existing panel already displays internal/test-only and not-for-customer-release warnings, making it the narrowest containment location.

## 5. Proposed operator workflow

```text
select governed internal preview
  -> inspect internal artifact status
  -> display ABSENT, PRESENT VALID, or BLOCKED
  -> preserve generation and customer boundaries
  -> take no lifecycle action
```

Inspection should be operator-triggered by the dedicated status button. The inspected code provides no evidence that automatic inspection on every page load is necessary or desirable; automatic page-load calls should not be added by this assessment.

## 6. Required UI controls

The minimum future controls are:

- one button labelled `Check Internal PDF Status`;
- request-in-progress disabled state;
- bounded result panel.

No acknowledgement checkbox is required for read-only inspection because the endpoint has no generation acknowledgement contract. The existing generation acknowledgement must remain separate.

The control must not add an archive button, remove/delete button, regenerate button, overwrite option, or customer-release action.

## 7. Request contract

The UI may send exactly:

- `fixture_id`;
- `report_id`;
- `report_version`.

It must never send an output root, output path, filename, extension, directory, wildcard, overwrite, archive, removal, deletion, regeneration, customer-ready, customer-release, or arbitrary report-content field.

## 8. Button-state rules

`Check Internal PDF Status` must be disabled when:

- no governed internal preview is selected;
- fixture ID is missing;
- `fixture_only` is not true;
- report ID or report version is missing;
- internal/test governance is invalid;
- provenance or prediction contract is missing;
- a request is already in progress;
- fixture mode is unavailable;
- the internal output root is unavailable.

A prior `ABSENT` result must not permanently disable future inspection. A `PRESENT VALID` result may be refreshed through another read-only request. Selection validation must use the existing governed row contract and must not broaden authority.

## 9. ABSENT response rendering

Display:

- `Internal test PDF not present`
- artifact state: `ABSENT`
- expected filename;
- fixture ID;
- report ID;
- report version;
- classification;
- inspection completed;
- generation performed: false;
- archive performed: false;
- removal performed: false;
- overwrite performed: false;
- customer release authorised: false;
- queue write performed: false.

Absence is a normal status, not an error.

## 10. PRESENT VALID response rendering

Display:

- `Internal test PDF present and valid`
- artifact state: `ACTIVE_INTERNAL_TEST_ARTIFACT`
- filename;
- file size;
- SHA-256;
- page count;
- PDF signature verified;
- fixture ID;
- report ID;
- report version;
- classification;
- internal/test warnings verified;
- customer ready false;
- customer release false;
- queue write false;
- generation false;
- archive false;
- removal false;
- overwrite false;
- permanent mutation false.

## 11. BLOCKED response rendering

Display:

- `Internal PDF inspection blocked`
- bounded blocked reason;
- artifact exists where safely known;
- inspection completed or not completed;
- generation false;
- archive false;
- removal false;
- overwrite false;
- customer release false;
- queue write false;
- an operator next action that does not offer mutation.

Plain-language mappings must cover at least:

- invalid signature;
- parse failure;
- identity mismatch;
- classification mismatch;
- missing warning;
- forbidden release claim;
- non-regular file;
- linked or reparse-point target;
- target outside approved root.

No automatic repair, deletion, rename, archive, overwrite, or regeneration may be offered.

## 12. Filesystem-disclosure boundary

The UI may display:

- filename;
- size;
- SHA-256;
- page count;
- bounded validation results;
- configured or unavailable status.

It must not display:

- unrestricted absolute output root;
- absolute target path;
- customer directory details;
- unrelated directory entries;
- full extracted PDF text.

The server-controlled deterministic target and bounded response contract remain authoritative.

## 13. Generation-control relationship

`Generate Internal Test PDF` and `Check Internal PDF Status` must remain separate:

- status inspection must not generate;
- `ABSENT` may leave generation available subject to the existing acknowledgement;
- `PRESENT VALID` must preserve client-side duplicate-generation blocking;
- `BLOCKED` must not enable overwrite, rename, repair, or regeneration;
- inspection must not reset the generation acknowledgement unexpectedly;
- inspection must not call the generation endpoint.

The existing template calls only `/api/button2/governed-internal-pdf/generate-v1` for generation and has no inspection call. The existing backend generation route must remain unchanged in the future dashboard slice.

## 14. Customer-flow isolation

The future inspection control must leave `customer_ready_count` unchanged, preserve selected customer rows, never call the customer batch endpoint, never assign customer-ready classification, never enable delivery/release controls, and never reuse the customer result panel for inspection status.

## 15. Button 3 isolation

Inspection must leave Button 3 selected-report state unchanged. It must not select, clear, or replace Button 3 state. The existing Button 3 selector and result-preview state must remain separate from the internal artifact status panel.

## 16. Refresh and stale-state rules

- Changing the internal-preview selection must clear the prior inspection result.
- A result must be bound to fixture ID, report ID, and report version.
- A result for one report must never display under another.
- Request-in-progress state must prevent duplicate clicks.
- Failed requests must not retain misleading success metadata.
- Refreshing inspection must remain read-only.

## 17. Accessibility and operator clarity

The future UI must use plain-language state headings, must not convey status only through colour, must present SHA-256 readably, and must clearly distinguish `ABSENT` from `BLOCKED`.

The button label must be `Check Internal PDF Status`, not an ambiguous `Check Report`. No generic Delete or Fix button may be added. Internal/test-only warnings must remain visible.

## 18. Safety flags

The UI must accurately render these values as false from inspection responses:

```text
customer_ready_possible = false
customer_release_authorized = false
queue_write_performed = false
pdf_generation_performed = false
learning_applied = false
calibration_applied = false
accuracy_ledger_written = false
gcid_written = false
model_weights_changed = false
fighter_ratings_changed = false
prediction_logic_changed = false
artifact_archived = false
artifact_removed = false
artifact_overwritten = false
permanent_mutation_performed = false
```

## 19. Proven blockers

### No dashboard call to the inspection endpoint

- Owning file: `operator_dashboard/templates/index.html`
- Owning section: Button 2 governed internal preview control
- Observed limitation: the inspected dashboard calls the generation endpoint but contains no call to `/api/button2/governed-internal-pdf/inspect-v1`
- Safety consequence: operators cannot view bounded artifact status through the dashboard
- Smallest remediation: add one operator-triggered read-only status call using the exact three-field request

### No inspection status panel or state rendering

- Owning file: `operator_dashboard/templates/index.html`
- Owning section: `b2-governed-internal-pdf-control`
- Observed limitation: the existing result panel renders generation success or generation-blocked output only; it has no `ABSENT`, `PRESENT VALID`, or inspection `BLOCKED` renderer
- Safety consequence: inspection results cannot be displayed without conflating them with generation
- Smallest remediation: add a separate bounded inspection result panel and state renderer inside the governed internal preview section

### No inspection request-state handling

- Owning file: `operator_dashboard/templates/index.html`
- Owning section: Button 2 JavaScript state
- Observed limitation: `button2GovernedInternalPdfInProgress` controls generation, but no inspection-specific in-progress, failure, or duplicate-click state exists
- Safety consequence: a future control could issue duplicate requests or retain stale success metadata
- Smallest remediation: add inspection-specific request state and clear-on-failure behavior

### No selection-bound stale-result clearing for inspection

- Owning file: `operator_dashboard/templates/index.html`
- Owning section: governed preview selection and queue refresh handlers
- Observed limitation: existing selection logic clears generation state but there is no inspection result state to clear or bind to report identity
- Safety consequence: a future status result could appear under a different selected fixture/report/version
- Smallest remediation: bind inspection results to the selected identity and clear them on selection or queue refresh

### No dashboard-focused inspection test

- Owning file: `operator_dashboard/test_button2_governed_internal_pdf_dashboard_exposure_v1.py`
- Owning section: governed internal dashboard exposure contract
- Observed limitation: the test asserts generation controls, generation request fields, generation acknowledgement, and duplicate-generation blocking, but no inspection control or inspection rendering
- Safety consequence: dashboard exposure could regress the read-only boundary without targeted detection
- Smallest remediation: add the separately authorized dashboard inspection test file named below

No blocker is claimed for the backend endpoint, planner, adapter, fixture validation, response disclosure boundary, or generation collision invariant; those are covered by the locked implementation and live proof records.

## 20. Smallest implementation slice

Recommend one future frontend-only, narrowly bounded implementation slice:

- add the status control and bounded rendering to `operator_dashboard/templates/index.html`;
- add the focused dashboard test in a new authorized test file;
- preserve the existing endpoint, planner, adapter, fixture, generation route, customer flow, and Button 3 code.

No `app.py` change is currently indicated because the proven endpoint and configured/unavailable output-root status already exist. Permit `app.py` modification only if a bounded read-only configured/unavailable status is demonstrably missing during that future slice.

Do not authorize adapter changes, fixture changes, generation-route changes, inspection-route changes, archive code, removal code, or customer-flow changes.

## 21. Proposed targeted test

Record exactly:

```text
py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_artifact_inspection_dashboard_v1.py
```

Do not run it during this assessment.

The future test should prove:

- separate status control exists;
- exact three-field request;
- no path fields;
- `ABSENT` rendering;
- `PRESENT VALID` rendering;
- `BLOCKED` rendering;
- no generation endpoint call;
- generation acknowledgement preserved;
- duplicate generation remains blocked;
- customer and Button 3 isolation;
- stale state clears on selection change;
- no lifecycle mutation control.

## 22. Recommended sequencing

A. docs-only dashboard readiness assessment;
B. isolated status UI implementation;
C. focused dashboard test;
D. live localhost absent-state proof;
E. live localhost present-valid proof;
F. docs closure;
G. separate archive/removal design only if independently authorised.

## 23. Explicit exclusions

This assessment does not authorize dashboard implementation, archive, removal, deletion, rename, movement, copy, overwrite, regeneration, repair, quarantine, generation-route changes, inspection-route changes, customer-ready classification, customer release, production storage, queue writes, report-ledger writes, learning, calibration, accuracy-ledger writes, GCID writes, or deployment.

## 24. Final verdict

BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_INSPECTION_DASHBOARD=READY_WITH_BLOCKERS

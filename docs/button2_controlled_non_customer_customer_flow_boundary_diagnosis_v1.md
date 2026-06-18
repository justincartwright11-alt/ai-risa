# Button 2 Controlled Non-Customer Customer-Flow Boundary Diagnosis v1

Slice: button2-controlled-non-customer-customer-flow-boundary-diagnosis-v1
Date: 2026-06-18
Status: Diagnosis-only docs/evidence

## Purpose

Map the exact Button 2 customer-flow boundary after the controlled non-customer route-layer proof chain, without activating customer report generation.

This diagnosis records where the controlled proof chain ends, where customer-generation begins, what must be proven before customer path activation, and why customer generation remains blocked.

## Locked Upstream State

- Runtime preflight: READY
- Controlled fixture render: PASS
- Open route proof: PASS
- Library route proof: PASS
- Route-layer regression: PASS
- Customer-report path: NOT ACTIVATED

## Where the Controlled Proof Chain Ends

The controlled proof chain ends at the read-only surfaces that were already proven safe:

1. Controlled fixture render proof
2. Generated-report open route proof
3. Generated-report library route proof
4. Controlled non-customer route-layer regression test
5. Controlled non-customer route-layer regression handoff
6. Final route-layer audit index

These surfaces only confirm that Button 2 can access and enumerate the controlled fixture artifact without entering customer report generation.

## Where Customer-Generation Begins

Customer-generation begins at the operator-gated generation routes that call the report-render integration path:

1. `/api/operator/button2/generate-report`
2. `/api/button2/selected-matchup/generate-guarded-v1`

Those routes move from read-only inspection into report-context composition, rendering, output-path resolution, and file write.

The customer-generation boundary is the transition into `generate_button2_report_render_gate_integration()` in `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`, which performs the following customer-side steps after gates pass:

- build ingest context
- build report context
- choose renderer path
- render PDF bytes
- resolve output path
- write PDF to disk
- mark customer-ready response fields
- optionally run QA side-channel logic

## Required Inputs Before Customer Report Generation Is Allowed

### For `/api/operator/button2/generate-report`

- `operator_approved` must be true
- `fight_id` must be a non-empty string
- `ingest_payload` must be a non-empty dict
- ingest composition must succeed
- report-context composition must succeed
- report context must exist and be well formed
- renderer path must produce PDF bytes
- output path must resolve safely
- file write must succeed

### For `/api/button2/selected-matchup/generate-guarded-v1`

- `operator_approved` must be true
- `selected_matchup_id` must resolve in the canonical queue source
- selected matchup must be complete
- selected matchup must be confirmed for Button 2
- selected matchup must be ready for generation
- source URL must be HTTP or HTTPS
- `fight_id` must be derivable from the selected matchup
- generated payload must be accepted by the core render gate
- strict post-render quality gate must pass

## Operator Gates and Readiness Checks

- Operator approval gate: required before generation can start
- Queue resolution gate: canonical queue source must resolve a valid selected matchup
- Selected-matchup readiness gate: the matchup must be marked ready for Button 2
- Source-backed gate: selected matchup must have a valid HTTP or HTTPS source URL
- Report-context gate: ingest and report contexts must both be valid
- Render gate: the renderer must produce PDF bytes
- Output-path gate: path resolution must stay inside the configured output root
- Write gate: file write must complete successfully
- Strict quality gate: post-render customer quality checks must pass

## Output Write Locations and Mutation Risks

The customer-generation path writes PDF output through the server-controlled output root resolved by `get_pdf_output_root()` and `_build_output_path_with_optional_override()`.

Mutation risks on the customer path:

- PDF file write to the output root
- report library listing update through new filesystem-visible PDF files
- queue or database mutation if any upstream selector or promotion path is later coupled to generation
- delivery/export metadata emitted from the customer-ready response path
- customer-facing open-link generation tied to the written PDF filename

## Side-Effect Surfaces

### PDF File Write

- Occurs only after approval, composition, render, and output-path resolution pass
- Implemented in `generate_button2_report_render_gate_integration()` via `open(output_path, "wb")`

### Report Library Listing Update

- The library route reads the output root and lists PDF files present on disk
- A newly written customer PDF would appear there automatically

### Queue/Database Mutation

- Not performed in the controlled route-layer proof chain
- Remains a risk only if future customer-flow work adds write-back coupling

### Delivery/Export Path

- The customer-generation routes return customer-ready metadata and open-link metadata
- Delivery is still explicitly blocked in the locked proof chain

### Customer-Facing Report Route/Open Path

- Customer-facing open-link generation is only meaningful once a generated PDF exists in the output root
- The safe open route itself is already proven read-only on the controlled fixture surface

## Safe Non-Customer Surfaces Already Proven

- Controlled fixture render proof: PASS
- `/api/button2/generated-report/open`: HTTP 200 and `application/pdf`
- `/api/button2/generated-report/library`: HTTP 200 and `text/html`
- Library listed `controlled_fixture_render_smoke.pdf`
- Library included safe open link
- Library excluded `controlled_fixture_render_smoke_summary.json`

## Why Customer Generation Remains Blocked

Customer generation remains blocked because the only completed proofs are still read-only surface proofs.

The current evidence confirms that Button 2 can read and list controlled fixture artifacts, but it does not yet activate the customer-generation routes, the render gate, the output-path write, or the customer-ready response path.

Before customer path activation, the following must still be proven in a separate bounded slice:

- a customer-flow boundary diagnosis or contract design step
- explicit customer-generation route contract review
- customer-path safety and gating behavior
- any future customer-ready transition must still preserve the locked no-delivery and no-mutation boundaries

## Recommended Next Safe Slice

- controlled non-customer Button 2 customer-flow boundary diagnosis only, or
- docs-only audit update

Not customer report generation yet.

## Conclusion

The controlled proof chain ends at the read-only open route, library route, regression test, regression handoff, and final index.

Customer-generation begins only when the operator-gated generation routes enter report-context composition, render, output-path resolution, and file write. That boundary remains unactivated, and it should stay blocked until a new explicitly bounded customer-flow slice is opened.

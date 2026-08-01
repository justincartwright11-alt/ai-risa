# Button 2 Governed Internal PDF Generation Readiness Assessment v1

## 1. Executive Verdict

**READY_WITH_BLOCKERS**

The existing Button 2 path can compose report context, render PDF bytes, resolve a configured output path, and write a file after operator approval. It is not yet safe to use as the governed fictional internal-PDF path because its success contract presents the artifact as customer-ready and permits overwrite behavior. A narrow internal-only adapter/gate is required before the existing fictional fixture can produce one governed internal PDF artifact.

This assessment reports readiness only. It does not authorize customer release, production use, external delivery, learning, calibration, ledger writes, GCID writes, or permanent mutation.

## 2. Current Proven Baseline

- Closure commit: `c08eb92aad55389b71c2ceae9a611667aa46d41f`.
- Locked implementation commit: `b53bf8c`.
- Three-button governed closed-loop runtime proof: `THREE_BUTTON_GOVERNED_CLOSED_LOOP_RUNTIME_PROOF=PASS`.
- Data scope: governed fictional fixture only.
- Button 2 state proven by the runtime proof: internal report preview, preview-only.
- Customer-ready count: `0`.
- No PDF was generated in the closed-loop runtime proof.
- The proven chain preserved `queue_write_performed = false`, `pdf_generation_performed = false`, `customer_release_authorized = false`, `learning_applied = false`, `calibration_applied = false`, `accuracy_ledger_written = false`, `gcid_written = false`, and `permanent_mutation_performed = false`.

## 3. Current Button 2 PDF-Generation Path

### Endpoint and route

`operator_dashboard/app.py` registers `POST /api/operator/button2/generate-report`. The route passes the request body to `generate_button2_report_render_gate_integration` in `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`.

The route requires an explicit truthy `operator_approved` value before proceeding. It also requires `fight_id` and a non-empty `ingest_payload` mapping.

### Report rendering

The integration function builds the read-only Button 2 dossier handoff and report context, then chooses one of these existing render paths:

- template-pack asset renderer for a `premium_template_pack_v29` profile;
- direct Jbalia template renderer when selected by the existing implementation;
- `build_button2_report_html` followed by `render_button2_pdf` for the HTML fallback.

The render path must return PDF bytes. The existing selected-matchup path requires a premium template-pack profile. The integration function records renderer metadata and may derive page count from the resulting bytes.

### Template/document input contract

The renderers receive the composed `report_context_preview`. The structured prediction contract is built from that context and can contain:

- `predicted_winner`;
- `predicted_method`;
- `predicted_round`;
- `confidence`;
- `structural_reasoning`;
- `tactical_pathway`;
- `evidence_notes`;
- `contract_version = button2_structured_prediction_v1`.

The current integration requires the upstream handoff context, but it does not enforce a complete governed internal artifact metadata contract containing generated-artifact classification, fixture identity, deterministic timestamp, or content hash before writing.

### Output-directory behavior

The output path is server-controlled through `resolve_pdf_output_path` and the configured PDF output root. An optional filename override is accepted only when it is a basename, ends in `.pdf`, contains no traversal markers, and passes the existing character check. The resolved candidate is checked against the configured root.

After rendering, the current integration creates the output directory if needed and writes PDF bytes with `open(output_path, "wb")`. If a file already exists, the current path records overwrite metadata but does not fail closed. The current path therefore does not establish a separate deterministic internal-only directory or prohibit overwrite of a canonical/customer artifact.

### Report identity/version handling

The fictional fixture already supplies `report_id = internal_fixture_report_closed_loop_v1` and `report_version = DRAFT_INTERNAL_FIXTURE_v1`. The current generation result instead exposes `generation_request_id` and derives Button 3 preview identity from that value, the output basename, or `fight_id`; the inspected generation function does not return the fixture `report_id` and `report_version` as a governed generated-artifact record.

### Source and prediction provenance

The fixture supplies `source_provenance = fixture_only_immutable`, `prediction_provenance = fixture_only_immutable`, `source_url`, `source_type = test_fixture`, and `prediction_schema_version = button2_structured_prediction_v1`. The current structured prediction result preserves the prediction fields and contract version, but the generation success response does not provide a complete generated-artifact provenance record that explicitly binds fixture identity, source provenance, report provenance, and internal/test-only classification.

### Current readiness and release gates

The current route has an operator approval gate and render/path checks. Its successful response currently returns:

- `customer_approved: true`;
- `customer_ready_gates_passed: true`;
- `report_status: customer_ready`;
- `report_quality_status: customer_ready_verified`.

Those values are incompatible with the fictional fixture’s `customer_release_authorized = false` and `customer_ready_possible = false` boundary. The existing route therefore cannot be used unchanged for the requested internal-only artifact.

### Writes currently performed

When successful, the current route performs one filesystem write: it writes PDF bytes to the resolved output path and may create its parent directory. It does not, in the inspected function, write the queue, database, learning state, calibration, accuracy ledger, or GCID. It does perform a filesystem artifact write, so a future governed adapter must make that write explicitly internal, deterministic, non-canonical, and non-customer-ready.

## 4. Internal Preview Versus Generated PDF

- **Internal report preview:** an in-memory or UI-visible governed preview of the fictional report context. It is preview-only, selectable for downstream preview, and does not create PDF bytes or a filesystem artifact.
- **Internal generated PDF:** one filesystem PDF artifact produced from the fictional fixture under an internal/test-only classification, with an approved internal directory, deterministic filename, provenance, audit metadata, and no customer-ready promotion.
- **Customer-ready PDF:** a separately gated artifact that satisfies customer-facing content, quality, release, and approval requirements. The current slice does not authorize this state.
- **Customer-released PDF:** a customer-delivered or externally exposed artifact. It requires separate release and delivery authority and is prohibited by this slice.

An internal generated PDF is not customer-ready merely because the renderer succeeds. A renderer success response must not promote a fictional internal artifact to either customer-ready or customer-released state.

## 5. Required Fixture Inputs

The following inputs are required for one valid governed internal PDF:

| Required input | Fixture status |
|---|---|
| `fixture_id` | Present: `closed_loop_governed_local_fixture_v1` |
| governed local fixture mode | Present in the fixture/runtime contract; must be enabled at generation time |
| `report_id` | Present: `internal_fixture_report_closed_loop_v1` |
| `report_version` | Present: `DRAFT_INTERNAL_FIXTURE_v1` |
| `matchup_id` / fight identity | Present: `fixture_only_closed_loop_matchup_v1` |
| fighter A identity | Present: `Fictional Fighter Alpha` |
| fighter B identity | Present: `Fictional Fighter Beta` |
| event name | Present: `Fictional Internal Smoke Event` |
| event date | Present: `2099-01-01` |
| promotion | Present: `AI-RISA Test Promotion` |
| source URL | Present: `https://example.test/ai-risa/closed-loop-fixture` |
| source type | Present: `test_fixture` |
| source provenance | Present: `fixture_only_immutable` |
| prediction provenance | Present: `fixture_only_immutable` |
| structured prediction | Present with winner, method, round, confidence, reasoning, pathway, and evidence |
| prediction schema/version | Present: `button2_structured_prediction_v1` and matching prediction contract version |
| internal/test-only status | Present: `internal_test_only = true` |
| read-only status | Present: `read_only = true` |
| customer release status | Present: `customer_release_authorized = false` |
| queue-write status | Present: `queue_write_performed = false` |
| generated-artifact classification | Missing as a dedicated generated-PDF field; must be added by the future adapter |
| deterministic output filename | Missing as a governed fixture artifact contract; must be derived by the future adapter |
| deterministic internal output directory | Missing as a dedicated generated-PDF boundary; must be supplied by the future adapter |
| generation timestamp or deterministic fixture timestamp | Fixture has event/verification timestamps, but no generated-artifact timestamp contract |
| content/artifact hash | Not present in the inspected fixture or generation response |
| operator-visible audit metadata | Approval exists in the request path, but a generated-artifact audit record is not returned |

## 6. Safety and Governance Gates

The future internal-PDF path must fail closed unless all of these gates pass:

1. Governed local fixture mode is explicitly enabled.
2. The fixture is fictional and the fixture path resolves to the approved fixture location.
3. Source inputs remain read-only and carry non-missing provenance.
4. Output classification is explicitly `INTERNAL_TEST_FIXTURE` or equivalent.
5. No customer-ready promotion is possible or returned.
6. Customer release is explicitly false and no delivery path is invoked.
7. No queue write occurs.
8. No database write occurs.
9. No learning or calibration occurs.
10. No accuracy-ledger write occurs.
11. No GCID write occurs.
12. Output location is deterministic and contained by the approved internal directory.
13. Operator-visible audit metadata identifies approval, fixture, report, version, renderer, output, and safety flags.
14. Missing, conflicting, malformed, or unsafe input blocks before the artifact write.

## 7. Output Artifact Contract

One future internal artifact should satisfy all of the following:

- PDF content visibly marks `INTERNAL / TEST FIXTURE`.
- PDF content visibly marks `NOT FOR CUSTOMER RELEASE`.
- Filename is deterministic and safe, incorporating the report identity and version, for example `internal_fixture_report_closed_loop_v1__DRAFT_INTERNAL_FIXTURE_v1.pdf` after the adapter defines the exact canonical form.
- Output is written only below a deterministic internal directory dedicated to governed fixture artifacts.
- The path cannot overwrite a canonical or customer PDF; existing target files fail closed unless the future slice explicitly defines an immutable content-addressed reuse rule.
- Report ID and report version are embedded in the artifact metadata or visible report control block.
- Fixture identity and fictional/internal status are embedded.
- Source and prediction provenance are embedded.
- A generation timestamp is recorded, or a deterministic fixture timestamp is used when the proof requires reproducibility.
- An artifact/content hash is returned if the selected renderer or adapter supports it; otherwise the adapter must state that hash support is still pending rather than claim one exists.
- The operator response returns generated-artifact metadata, including path, filename, report identity/version, fixture ID, classification, renderer, page count if available, hash if available, and all mutation/release flags.

## 8. Fail-Closed Cases

The future path must block without writing an artifact when:

- fixture mode is disabled;
- the fixture path is invalid, outside the approved fixture directory, or absent;
- report ID or report version is missing;
- structured prediction or its schema version is missing;
- source or prediction provenance is missing;
- fighter, matchup, or event identities do not agree across fixture, handoff, and report context;
- the requested output path escapes the approved internal directory;
- customer release or customer-ready promotion is requested;
- canonical queue mutation would occur;
- a database, learning, calibration, ledger, or GCID write is requested;
- an existing customer or canonical artifact would be overwritten;
- the renderer fails, returns non-PDF bytes, or fails its applicable render/quality gate.

## 9. Existing Reusable Components

The following can be reused without change in the next implementation slice:

- Button 2 internal report-preview contract and its read-only dossier handoff.
- Existing operator approval check at the start of the generation integration.
- Existing report context composition path.
- Existing `render_button2_pdf` render gate for the HTML fallback.
- Existing template-pack asset renderer and direct template renderer where the selected fixture context supports them.
- Existing server-controlled output-root and path-traversal helpers as a starting boundary.
- Existing structured prediction contract and `button2_structured_prediction_v1` schema.
- Existing fictional fixture and its immutable source/prediction provenance fields.
- Existing safety flags in the fixture and closed-loop proof.
- Existing report identity/version fields in the fixture.

These components are reusable inputs, not proof that the current customer-ready response contract is suitable for internal generation.

## 10. Exact Proven Blockers

### Blocker 1: Customer-ready success contract

- **Owning file:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`.
- **Owning function:** `generate_button2_report_render_gate_integration`.
- **Observed limitation:** Successful generation returns `customer_approved: true`, `customer_ready_gates_passed: true`, `report_status: customer_ready`, and `report_quality_status: customer_ready_verified`.
- **Smallest remediation:** Add a separate governed internal-fixture adapter/gate that returns internal-only classification and explicitly false customer-ready/release fields without reusing the customer-ready success contract.

### Blocker 2: Non-deterministic and overwrite-capable artifact boundary

- **Owning file:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`.
- **Owning function:** `generate_button2_report_render_gate_integration`, including `_build_output_path_with_optional_override` and the file-write block.
- **Observed limitation:** The configured output root is generic, the filename may be overridden, and an existing file is overwritten after metadata is captured; the function does not fail closed for an existing canonical/customer artifact.
- **Smallest remediation:** Restrict the internal adapter to a deterministic fixture output directory and filename, reject existing canonical/customer targets, and prevent path selection from escaping that directory.

### Blocker 3: Missing generated-artifact metadata contract

- **Owning files:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py` and `operator_dashboard/fixtures/closed_loop_governed_local_fixture_v1.json`.
- **Owning function/data:** `generate_button2_report_render_gate_integration` response and the `button2` fixture object.
- **Observed limitation:** The fixture has report identity, version, provenance, and structured prediction, but the inspected generation response does not return a dedicated fixture ID, generated-artifact classification, deterministic artifact filename, internal directory classification, or artifact hash.
- **Smallest remediation:** Define and return a narrow internal generated-artifact metadata object in the adapter, deriving only from the validated fixture and render result. Do not broaden the canonical fixture or customer report contract unless a later slice explicitly permits it.

### Blocker 4: Missing complete pre-write fail-closed validation

- **Owning file:** `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py`.
- **Owning function:** `generate_button2_report_render_gate_integration`.
- **Observed limitation:** The current inspected function validates operator approval, request shape, composition, rendering, and output path, but does not validate all requested fixture-only identity/provenance/internal-classification fields before the file write, and visual QA is best effort rather than a required internal artifact gate.
- **Smallest remediation:** Add one narrow adapter validation gate before rendering/writing that checks the fixture mode, fixture identity, report metadata, prediction schema, provenance, identity consistency, internal flags, and non-customer state; make required render/path/artifact checks fail closed.

## 11. Recommended Implementation Sequence

### Slice 1: Internal-PDF generation adapter or gate

Add the smallest adapter around the existing Button 2 composition/render path. It should accept only the governed fictional fixture, enforce the internal artifact contract, use a deterministic internal output boundary, reject overwrites and customer promotion, and return operator-visible metadata. Preserve the one-slice, one-test, commit-and-stop rule.

### Slice 2: Focused fictional-fixture generation test

Add one focused pytest test proving one valid internal PDF artifact and the fail-closed cases for missing fixture mode, invalid metadata, unsafe output, and attempted customer promotion. Use a temporary internal output root and assert all mutation/release flags remain false. Do not run this test as part of this assessment.

### Slice 3: Live local internal-PDF proof and closure record

Run one bounded local proof against the fictional fixture, inspect the generated artifact and returned metadata, verify the internal markings and path boundary, then create the separate closure record authorized by that future slice. No customer delivery, production generation, bulk generation, or permanent mutation is included.

## 12. Authorized Files for the Next Implementation Slice

The smallest likely file set is:

- `operator_dashboard/button2_governed_internal_pdf_generation_adapter_v1.py` (new adapter, if the implementation slice permits a new module);
- `operator_dashboard/button2_report_generation_route_render_gate_integration_v1.py` (only if a route wire is required);
- `operator_dashboard/test_button2_governed_internal_pdf_generation_adapter_v1.py` (the focused test).

The fixture, template, canonical queue, database, learning, ledger, GCID, and customer delivery files should remain unchanged unless a later slice explicitly names them. A future slice must confirm the exact set before editing.

## 13. Recommended Targeted Test

Proposed future command; do not run during this docs-only assessment:

`pytest -q operator_dashboard/test_button2_governed_internal_pdf_generation_adapter_v1.py`

## 14. Explicit Exclusions

This assessment does not authorize:

- customer-ready classification;
- customer release;
- external delivery;
- production generation;
- bulk PDF generation;
- canonical queue writes;
- report ledger persistence;
- learning;
- calibration;
- accuracy-ledger writes;
- GCID writes;
- model changes;
- fighter-rating changes;
- deployment.

## 15. Final Verdict

`BUTTON2_GOVERNED_INTERNAL_PDF_READINESS=READY_WITH_BLOCKERS`

# Button 2 Governed Internal PDF Artifact Inspection Endpoint Readiness Assessment v1

## 1. Executive verdict

READY_WITH_BLOCKERS

The read-only inspection adapter is directly proven and is suitable as the narrow backend foundation. Endpoint integration is not yet implemented or proven. The smallest safe next step is a separate backend-only inspection route with strict fixture, environment, identity, target, response, and non-mutation boundaries.

This assessment defines future endpoint readiness only. It does not authorize endpoint implementation, dashboard exposure, customer release, production launch, or any filesystem or persistent mutation.

## 2. Proven baseline

- Proof-closure commit: `b73e81f`.
- Inspection-adapter commit: `c70afaea8a3fda202387c8803cc0c4099ae2d32e`.
- Public inspection function: `inspect_button2_governed_internal_pdf_artifact_v1(preflight_plan, expected_row=None)`.
- Direct proof: `BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_INSPECTION_DIRECT_PROOF=PASS`.
- Inspection is limited to the deterministic target from the preflight plan.
- Both absent and valid-present target states were proven.
- No-mutation behavior was proven for the artifact, inputs, and inspected directory contents.

The proof used the fictional governed local fixture only. It did not prove Flask endpoint behavior, dashboard exposure, customer readiness, customer release, production storage, queue or ledger persistence, learning, calibration, archive, removal, rename, overwrite, regeneration, or deployment.

## 3. Endpoint purpose

A future endpoint shall report bounded status for the expected governed internal PDF artifact and nothing more. It may determine:

- artifact absent;
- artifact present and valid;
- artifact present but blocked or corrupt/mismatched.

It must not generate, archive, remove, rename, move, copy, repair, overwrite, regenerate, scan directories, accept arbitrary paths, or mutate lifecycle state. It must not reuse the generation endpoint because generation has a write-capable renderer and a different request and response contract.

## 4. Proposed endpoint

Recommend:

`POST /api/button2/governed-internal-pdf/inspect-v1`

POST is preferable because the operation requires a validated fixture/report identity contract and a server-side fixture resolution step without exposing that contract as a query string. The request remains an inspection request; POST does not grant write authority.

The endpoint must be separate from `POST /api/button2/governed-internal-pdf/generate-v1`.

## 5. Environment gates

The endpoint must fail closed unless all of these gates pass:

- `AI_RISA_LOCAL_FIXTURE_MODE=1`.
- The governed fixture path is validated by the existing loader or equivalent locked validation boundary.
- `AI_RISA_INTERNAL_PDF_OUTPUT_ROOT` is configured.
- The configured output root is absolute, existing, writable as required by the existing route gate, and not a forbidden customer or canonical queue root.
- The server resolves the output root; the caller cannot provide it.
- The server derives the target path and filename; the caller cannot provide either.

The endpoint must not accept a caller-provided output root, path, or filename.

## 6. Request contract

The only permitted request fields are:

- `fixture_id`;
- `report_id`;
- `report_version`.

No acknowledgement field is required. Inspection is strictly read-only, and the inspected repository contracts do not establish a need for an acknowledgement separate from the environment and fixture gates.

The endpoint must reject or ignore no unlisted authority by silently accepting it. Explicitly prohibited fields include:

- output root;
- output path;
- filename;
- extension;
- wildcard;
- directory;
- overwrite;
- archive authority;
- removal authority;
- regeneration authority;
- customer-ready authority;
- customer-release authority;
- arbitrary report content.

A request with a non-object JSON body, missing identity, unsafe identity, or prohibited path/authority fields must be blocked deterministically.

## 7. Fixture and identity validation

Reuse the existing governed fixture loader and its validated metadata boundary. Do not create a weaker duplicate validator. The route must verify:

- fixture mode is enabled;
- the fixture source is accepted;
- the fixture ID matches the validated fixture;
- fixture-only governance is true;
- the report ID matches;
- the report version matches;
- `internal_test_only` is true;
- `read_only` is true;
- `structured_prediction` is present;
- prediction schema/version is present and consistent;
- source and report provenance are present;
- `customer_ready_possible` is false;
- `customer_release_authorized` is false.

The validated Button 2 row must be rebuilt from the governed fixture, with the validated fixture ID and fixture-only marker, before preflight. Caller-supplied report content must never be used.

## 8. Preflight reconstruction

The required future flow is:

```text
validated governed fixture row
  -> build_button2_governed_internal_pdf_preflight_v1
  -> confirm preflight success
  -> inspect_button2_governed_internal_pdf_artifact_v1
  -> return bounded inspection response
```

The route must call `build_button2_governed_internal_pdf_preflight_v1` with the server-derived output root and `fixture_mode=True`. It must pass the resulting plan and validated row to `inspect_button2_governed_internal_pdf_artifact_v1`.

The route must not call the render adapter or any generation route. Preflight must remain non-writing; an already-existing target must be inspectable by the inspection flow rather than treated as a generation collision.

## 9. Target boundary

Only `preflight_plan["proposed_output_path"]` may be inspected. The route and adapter chain must prohibit:

- directory listing;
- recursive scanning;
- fallback lookup;
- newest-file selection;
- similarly named artifact search;
- customer directory access;
- canonical queue directory access;
- caller-controlled paths.

Containment, deterministic filename, regular-file status, link/reparse-point rejection, PDF signature, parseability, page count, identity, classification, and internal warning checks remain bounded to that target.

## 10. Absent response

A valid absent target is not a server error. The endpoint should return HTTP 200 with a bounded response equivalent to:

```json
{
  "ok": true,
  "status": "absent",
  "artifact_state": "ABSENT",
  "artifact_exists": false,
  "expected_filename": "<deterministic filename>",
  "fixture_id": "<validated fixture id>",
  "report_id": "<validated report id>",
  "report_version": "<validated report version>",
  "artifact_classification": "governed_internal_test_pdf",
  "inspection_performed": true,
  "pdf_generation_performed": false,
  "artifact_archived": false,
  "artifact_removed": false,
  "artifact_overwritten": false,
  "permanent_mutation_performed": false
}
```

The response must not include an unrestricted absolute path. Absence must not create the output directory or any artifact.

## 11. Present-valid response

A valid present target should return HTTP 200 with a bounded response equivalent to:

```json
{
  "ok": true,
  "status": "present_valid",
  "artifact_state": "ACTIVE_INTERNAL_TEST_ARTIFACT",
  "artifact_exists": true,
  "regular_file": true,
  "path_contained": true,
  "filename_matches": true,
  "pdf_signature_valid": true,
  "file_size_bytes": 11094,
  "sha256": "<sha-256>",
  "page_count": 1,
  "fixture_id": "<validated fixture id>",
  "report_id": "<validated report id>",
  "report_version": "<validated report version>",
  "artifact_classification": "governed_internal_test_pdf",
  "internal_only": true,
  "test_fixture_only": true,
  "customer_ready_possible": false,
  "customer_release_authorized": false,
  "queue_write_performed": false,
  "pdf_generation_performed": false,
  "artifact_archived": false,
  "artifact_removed": false,
  "artifact_overwritten": false,
  "permanent_mutation_performed": false
}
```

The exact size, hash, and page count are target metadata, not fixed constants. The adapter must return the independently computed values for the deterministic target.

## 12. Blocked response

Governance, request, fixture, preflight, or artifact validation failure should return an appropriate 4xx response, normally HTTP 403 for a disabled governance gate and HTTP 422 for a validated-but-blocked contract or artifact state. The response must be bounded and contain:

```json
{
  "ok": false,
  "status": "blocked",
  "blocked_reason": "<deterministic bounded reason>",
  "artifact_exists": false,
  "inspection_performed": false,
  "customer_release_authorized": false,
  "queue_write_performed": false,
  "pdf_generation_performed": false,
  "artifact_archived": false,
  "artifact_removed": false,
  "artifact_overwritten": false,
  "permanent_mutation_performed": false
}
```

`artifact_exists` and `inspection_performed` must reflect what was safely established before the block. Do not expose stack traces, arbitrary absolute paths, customer directory details, or unrelated filesystem entries. An unexpected internal exception is a server fault, not a normal blocked artifact state; it should return a bounded 500 response without stack details and preserve all false mutation flags.

## 13. Deterministic blocked reasons

The endpoint should preserve bounded reasons equivalent to:

- `invalid_fixture_mode`;
- `invalid_fixture_source`;
- `fixture_identity_mismatch`;
- `report_identity_mismatch`;
- `invalid_preflight_plan`;
- `target_outside_approved_root`;
- `target_filename_mismatch`;
- `non_regular_target`;
- `link_or_reparse_point_rejected`;
- `invalid_pdf_signature`;
- `pdf_parse_failure`;
- `invalid_page_count`;
- `artifact_identity_mismatch`;
- `classification_mismatch`;
- `internal_warning_missing`;
- `forbidden_release_claim_present`.

Where the existing adapter uses a more specific established spelling, the route should normalize only at the response boundary and preserve the underlying fail-closed classification. It must not convert a blocked state into success.

## 14. Filesystem disclosure

The preferred response contract may return:

- the deterministic expected filename;
- configured versus not-configured output-root state;
- bounded artifact metadata such as regular-file status, containment status, size, SHA-256, page count, signature, identity, and classification.

It must not return:

- an unrestricted absolute output root;
- an unrestricted absolute output path;
- customer directory details;
- canonical queue directory details;
- unrelated filesystem entries.

No inspected source establishes an authorised local-operator contract requiring an absolute path in this response, so absolute paths should be omitted.

## 15. Read-only and immutability guarantees

The endpoint and adapter chain must preserve:

- artifact bytes;
- artifact size;
- artifact modification timestamp;
- filename;
- directory contents;
- fixture object;
- validated row;
- preflight plan.

The endpoint must perform no cleanup, repair, deletion, quarantine, rename, archive, or regeneration. It must not create an output directory, write an audit record, or modify queue, ledger, learning, calibration, GCID, model, rating, or prediction state.

## 16. Safety flags

Every success, blocked, and unexpected-error response must preserve:

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

## 17. HTTP behavior

Recommend deterministic behavior:

| Condition | HTTP result |
| --- | --- |
| Valid governed request, target absent | `200`, `ok=true`, `status=absent` |
| Valid governed request, target present and valid | `200`, `ok=true`, `status=present_valid` |
| Missing or prohibited request contract | `400` or `422`, `status=blocked` |
| Disabled or invalid governance gate | `403` or `422`, `status=blocked` |
| Invalid fixture/report identity | `422`, `status=blocked` |
| Corrupt, mismatched, or unsafe target | `422`, `status=blocked` |
| Unexpected internal exception | bounded `500`, no stack trace |

Expected blocked artifact states must remain distinct from unexpected server faults. All responses should use `Cache-Control: no-store` and must not expose unrestricted paths.

## 18. Proven blockers

### No inspection endpoint exists

- Owning file: `operator_dashboard/app.py`.
- Owning section: governed internal PDF route area around `button2_governed_internal_pdf_generate_v1`.
- Observed limitation: the inspected route is generation-only; no `/inspect-v1` route exists.
- Safety consequence: there is no HTTP boundary that exposes the proven adapter contract.
- Smallest remediation: add the separate read-only route proposed here and reuse the existing loader, fixture-path, output-root, and preflight boundaries.

### No endpoint integration test exists

- Owning file: `operator_dashboard/test_button2_governed_internal_pdf_route_integration_v1.py`.
- Observed limitation: the inspected integration tests cover `generate-v1`, including generation, collision blocking, and renderer-failure cleanup, but contain no inspection route tests.
- Safety consequence: request rejection, response normalization, and route-level non-mutation are unproven.
- Smallest remediation: create the one focused route test file named in the implementation slice.

### No bounded HTTP response normalization exists for inspection

- Owning file: `operator_dashboard/app.py`.
- Owning section: existing `_button2_governed_internal_pdf_blocked` and generation response path.
- Observed limitation: the adapter returns bounded dictionaries, but no inspection route maps adapter results into the specified HTTP success, blocked, and unexpected-error contract.
- Safety consequence: direct proof does not establish stable HTTP status codes, disclosure limits, or complete response flags.
- Smallest remediation: implement a route-local response normalizer for this endpoint only.

### No inspection-specific route-level environment and fixture gate exists

- Owning file: `operator_dashboard/app.py`.
- Owning section: existing governed generation route and its helper gates.
- Observed limitation: environment and fixture gates exist on the generation path, but no inspection route applies them to the adapter chain.
- Safety consequence: the proven direct adapter cannot yet be reached through a controlled server boundary.
- Smallest remediation: reuse the existing validated loader metadata and server-side root helper in the separate inspection route; do not duplicate weaker validation.

### No live endpoint proof exists

- Owning file: `docs/button2_governed_internal_pdf_dashboard_live_proof_v1.md`.
- Observed limitation: the locked live proof covers `generate-v1`, not `inspect-v1`.
- Safety consequence: localhost HTTP behavior, disclosure boundaries, and route-level immutability remain unproven.
- Smallest remediation: after the focused route test passes, conduct a separate bounded localhost endpoint proof and document it in a later authorized slice.

No blocker is asserted for the adapter itself: its direct proof is locked as PASS. No dashboard, fixture, renderer, archive, removal, or generation-route change is required for this readiness assessment.

## 19. Smallest implementation slice

Recommend one future backend-only implementation slice:

- add the separate `POST /api/button2/governed-internal-pdf/inspect-v1` route;
- reuse the governed fixture loader and existing server-side environment helpers;
- rebuild the deterministic preflight plan;
- call the proven inspection adapter only;
- normalize bounded HTTP responses;
- add the focused route test;
- do not expose the route in the dashboard in that slice.

## 20. Proposed targeted test

Record exactly:

`py -m pytest -q operator_dashboard/test_button2_governed_internal_pdf_artifact_inspection_route_v1.py`

Do not run it during this assessment.

The future test should cover:

- default fixture mode blocked;
- missing output root blocked;
- invalid fixture/report identity blocked;
- absent target HTTP 200;
- present-valid target HTTP 200;
- corrupt target blocked;
- exact deterministic target only;
- no path fields accepted;
- no filesystem mutation;
- no customer, queue, learning, ledger, GCID, archive, removal, overwrite, or regeneration action.

## 21. Future sequencing

A. Docs-only endpoint assessment.

B. Backend read-only endpoint.

C. Focused route test.

D. Live localhost endpoint proof.

E. Docs closure.

F. Separate dashboard-exposure assessment.

G. Dashboard implementation and proof only if separately authorised.

## 22. Explicit exclusions

This assessment does not authorise:

- endpoint implementation;
- dashboard exposure;
- archive;
- removal;
- rename;
- movement;
- copy;
- overwrite;
- regeneration;
- generation-route modification;
- caller-controlled paths;
- customer-ready classification;
- customer release;
- production storage;
- queue writes;
- report-ledger writes;
- learning;
- calibration;
- accuracy-ledger writes;
- GCID writes;
- deployment.

## 23. Final verdict

BUTTON2_GOVERNED_INTERNAL_PDF_ARTIFACT_INSPECTION_ENDPOINT=READY_WITH_BLOCKERS

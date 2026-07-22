# Button2 Premium PDF Visual Renderer Artifact Path Integration Contract Test Design v1

## 1. Purpose
Define a docs-only contract-test design for a future test that proves renderer scaffold and internal artifact-path module integration behavior.

This design proves safe contract handoff only. It does not authorize runtime artifact creation.

## 2. Slice Boundary
This slice is docs-only and creates one file only:

- docs/button2_premium_pdf_visual_renderer_artifact_path_integration_contract_test_design_v1.md

This slice does not authorize:

- renderer implementation edits
- artifact-path module edits
- QA gate module edits
- fixture edits
- test file creation
- folder creation
- output artifact creation
- PDF or image generation
- manifest or preview generation
- customer delivery
- public publishing
- production launch
- automated delivery
- learning activation

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY
CUSTOMER_RELEASE_AUTHORIZED=NO
PUBLIC_PUBLISHING_AUTHORIZED=NO
PRODUCTION_LAUNCH_AUTHORIZED=NO
AUTOMATED_DELIVERY_AUTHORIZED=NO
LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Baseline Reviewed Inputs
This design is grounded in the following reviewed files:

- docs/button2_premium_pdf_visual_renderer_artifact_path_integration_design_v1.md
- docs/button2_premium_pdf_visual_internal_artifact_path_system_review_v1.md
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_renderer_v1.py
- operator_dashboard/test_button2_premium_pdf_visual_renderer_scaffold_contract_v1.py
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_internal_artifact_path_v1.py
- operator_dashboard/test_button2_premium_pdf_visual_internal_artifact_path_contract_v1.py
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_internal_page_prototype_v1.json
- operator_dashboard/test_button2_premium_pdf_visual_internal_page_prototype_contract_v1.py
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_qa_gate_v1.py
- operator_dashboard/test_button2_premium_pdf_visual_qa_gate_contract_v1.py
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_internal_contract_prototype_v1.json

## 5. Integration Contract Under Test
Future integration test target:

- renderer contract object from build_visual_render_contract
- QA gate contract object from validate_visual_qa_gate_contract
- page prototype contract fixture
- artifact-path contract object from build_internal_visual_artifact_path_contract

Primary handoff proof:

1. Renderer contract remains CONTRACT_OBJECT_ONLY with output_path=null.
2. QA gate output remains PASS_INTERNAL_ONLY for safe input.
3. Artifact-path builder consumes the page prototype contract object plus render_attempt_id and artifact_kind.
4. Integration result remains internal-only and non-delivery.
5. No folder/file/PDF/image/manifest/preview artifact is created.

## 6. Future Test File and Scope
Future test file (not created in this slice):

- operator_dashboard/test_button2_premium_pdf_visual_renderer_artifact_path_integration_contract_v1.py

Scope of that future test file:

- contract-only integration behavior
- fail-closed negative cases
- source and path safety checks
- no-output side effect checks

Out of scope for that future test file:

- rendering bytes
- writing PDF/image files
- creating directories
- delivery flows

## 7. Setup Design for Future Test
Use only existing contracts and fixtures.

1. Load visual payload fixture from button2_premium_pdf_visual_internal_contract_prototype_v1.json.
2. Load style registry fixture from button2_premium_pdf_visual_style_registry_v1.json.
3. Build renderer contract with build_visual_render_contract.
4. Validate renderer contract with validate_visual_render_contract.
5. Build QA input from fixture plus renderer contract.
6. Validate QA gate output with validate_visual_qa_gate_contract.
7. Load page prototype fixture from button2_premium_pdf_visual_internal_page_prototype_v1.json.
8. Replace embedded render_contract and qa_gate_output in a local deep copy.
9. Call build_internal_visual_artifact_path_contract with:
   - page prototype copy
   - render_attempt_id like RA_INT_0001
   - artifact_kind internal_visual_page_preview

No fixture file writes are allowed.

## 8. Positive Contract Case Design
Case ID: INTEGRATION_POSITIVE_INTERNAL_ONLY

Expected:

- artifact_contract_status=PASS_INTERNAL_ONLY
- qa_gate_status=PASS_INTERNAL_ONLY
- render_contract_status=CONTRACT_VALIDATED_INTERNAL_ONLY
- artifact_extension_authorized=false
- delivery_ready=false
- customer_facing_authorized=false
- learning_activation_authorized=false
- blocked_reasons=[]
- artifact_root begins with tmp_pdf_output/button2_visual_internal_prototypes/
- artifact_path has no extension

## 9. Negative Case Matrix
Case ID: INTEGRATION_BLOCKED_QA_STATUS

- mutate qa_gate_output.qa_status to BLOCKED
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains qa_status_not_pass_internal_only

Case ID: INTEGRATION_BLOCKED_QA_BLOCKED_REASONS

- set qa_gate_output.blocked_reasons to non-empty list
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains qa_blocked_reasons_non_empty

Case ID: INTEGRATION_BLOCKED_RENDER_STATUS

- mutate render_contract.render_status to invalid value
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains render_status_invalid

Case ID: INTEGRATION_BLOCKED_RENDER_OUTPUT_PATH_NON_NULL

- mutate render_contract.output_path to tmp/out.pdf
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains render_output_path_non_null

Case ID: INTEGRATION_BLOCKED_RENDER_DELIVERY_READY_TRUE

- mutate render_contract.delivery_ready to true
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains render_delivery_ready_true

Case ID: INTEGRATION_BLOCKED_RENDER_MISSING_VISUAL_SIGNALS

- mutate one of:
  - render_contract.evidence_panel_rendered=false
  - render_contract.disclaimer_footer_rendered=false
  - render_contract.severity_scale_rendered=false
- expected artifact_contract_status=BLOCKED

Case ID: INTEGRATION_BLOCKED_RELEASE_SCOPE

- mutate release_boundary.release_scope_decision=EXTERNAL
- expected artifact_contract_status=BLOCKED

Case ID: INTEGRATION_BLOCKED_CUSTOMER_RELEASE

- mutate release_boundary.customer_release_authorized=true
- expected artifact_contract_status=BLOCKED

Case ID: INTEGRATION_BLOCKED_LEARNING_ACTIVATION

- mutate release_boundary.learning_activation_authorized=true
- expected artifact_contract_status=BLOCKED

Case ID: INTEGRATION_BLOCKED_RENDER_ATTEMPT_ID

- pass empty render_attempt_id
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains invalid_render_attempt_id

Case ID: INTEGRATION_BLOCKED_ARTIFACT_KIND

- pass unknown artifact_kind
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons contains unknown_artifact_kind

Case ID: INTEGRATION_BLOCKED_UNSAFE_OVERRIDE_PATH

- set page_prototype.artifact_path_override to a forbidden path signal
- expected artifact_contract_status=BLOCKED
- expected blocked_reasons includes one or more:
  - absolute_windows_path_present
  - reference_folder_path_present
  - path_traversal_present
  - forbidden_path_zone_present

## 10. Source and Path Safety Assertions
Future test must assert all of the following for positive case output:

- no absolute Windows path in artifact_path
- no path traversal pattern in artifact_path
- no reference-folder dependency token in source or output
- no customer/public/production/delivery/learning/calibration/GCID/accuracy-ledger zone markers in artifact_path
- source_traceability object is present and includes fixture/module references

Reference folder rule for this slice and future test design:

- C:/Users/jusin/OneDrive/Pictures/New Visuals must not be read, copied, imported, or required.

## 11. No-Output Side Effect Proof Design
Future test must prove no new output artifacts are created.

Recommended assertion pattern:

1. Snapshot repo files by extension before integration call: .pdf, .png, .jpg, .jpeg.
2. Execute integration contract call(s).
3. Snapshot again.
4. Assert snapshots are identical.

Optional hardening assertion:

- monkeypatch Path.mkdir and file-open write paths to fail if called by integration flow.

## 12. Contract Completeness Assertions
Future positive-case assertions should include required output fields from artifact path module:

- artifact_contract_status
- artifact_id
- artifact_kind
- artifact_path
- artifact_filename_stem
- artifact_root
- artifact_subpath
- artifact_extension_authorized
- hash_algorithm
- source_fixture_id
- source_traceability
- release_boundary
- qa_gate_status
- render_contract_status
- operator_review_status
- delivery_ready
- customer_facing_authorized
- learning_activation_authorized
- blocked_reasons

And enforce:

- hash_algorithm=SHA256
- artifact_extension_authorized=false
- delivery_ready=false
- customer_facing_authorized=false
- learning_activation_authorized=false

## 13. Failure Classification Plan
If future targeted integration contract test fails, classify first blocker as one of:

- stale_test_harness
- changed_contract_field
- release_boundary_regression
- qa_gate_contract_regression
- renderer_contract_regression
- artifact_path_safety_regression
- side_effect_output_regression
- unknown

## 14. Validation Plan for Future Slice
For the future contract-test implementation slice, run only the targeted test file once:

- operator_dashboard/test_button2_premium_pdf_visual_renderer_artifact_path_integration_contract_v1.py

No broad pytest expansion.

## 15. Governance Carry-Forward
This design carries forward:

- INTERNAL_ONLY scope
- fail-closed behavior
- operator approval requirement
- no customer release
- no learning activation
- no output artifact creation in contract-only phase

## 16. Slice Integrity Record
DOCS_CHANGED=YES
CODE_CHANGED=NO
TEST_CHANGED=NO
FIXTURE_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
IMAGE_CHANGED=NO
WORKFLOW_CHANGED=NO
PRE_EXISTING_UNRELATED_WORKTREE_CHANGES=YES
UNRELATED_WORKTREE_CHANGES_STAGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY
LEARNING_ACTIVATION_AUTHORIZED=NO

## 17. Design Decision
BUTTON2_PREMIUM_PDF_VISUAL_RENDERER_ARTIFACT_PATH_INTEGRATION_CONTRACT_TEST_DESIGN_READY_FOR_TEST_IMPLEMENTATION

## 18. Recommended Next Slice
button2_premium_pdf_visual_renderer_artifact_path_integration_contract_test_v1

That next slice should implement only the targeted integration contract test file and must preserve all no-output and internal-only boundaries.

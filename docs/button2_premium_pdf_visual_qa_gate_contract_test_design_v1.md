# Button 2 Premium PDF Visual QA Gate Contract Test Design v1

## 1. Purpose
This document designs the future targeted contract test for the Button 2 Premium PDF Visual QA Gate.

## 2. Design Boundary
This is docs-only contract test design.

It does not authorize:

- runtime implementation
- QA gate implementation
- QA gate test creation
- renderer feature expansion
- prototype fixture creation
- PDF rendering
- image generation
- output artifact creation
- visual reference folder ingestion
- customer release
- public publishing
- production launch
- automated delivery
- learning activation
- calibration writes
- GCID writes
- accuracy-ledger writes
- database writes

## 3. Release Boundary
RELEASE_SCOPE_DECISION=INTERNAL_ONLY
CUSTOMER_RELEASE_AUTHORIZED=NO
PUBLIC_PUBLISHING_AUTHORIZED=NO
PRODUCTION_LAUNCH_AUTHORIZED=NO
AUTOMATED_DELIVERY_AUTHORIZED=NO
LEARNING_ACTIVATION_AUTHORIZED=NO

## 4. Source QA Gate Design Reviewed
Reference:

docs/button2_premium_pdf_visual_qa_gate_design_v1.md

Confirm:

DESIGN_DECISION=BUTTON2_PREMIUM_PDF_VISUAL_QA_GATE_DESIGN_READY_FOR_CONTRACT_TEST_DESIGN

## 5. Source Prototype Lock Reviewed
Reference:

docs/button2_premium_pdf_visual_internal_contract_prototype_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_BUTTON2_VISUAL_INTERNAL_CONTRACT_PROTOTYPE_LOCK_INTERNAL_ONLY
TARGETED_PROTOTYPE_TEST_RESULT=PASS
TARGETED_SCAFFOLD_CONTRACT_TEST_RESULT=PASS
REFERENCE_VISUAL_FOLDER_NOT_USED=YES
IMAGE_DEPENDENCY_FOUND=NO
OUTPUT_FILE_REFERENCE_FOUND=NO
NO_OUTPUT_ARTIFACTS_CREATED=YES

## 6. Future Contract Test Objective
The future targeted QA gate contract test must validate fail-closed QA behavior, required QA input/output fields, structural visual checks, evidence/disclaimer checks, accessibility checks, no-output-artifact behavior, and internal-only governance gates without creating a QA gate module or rendered artifact.

## 7. Proposed Future Test File
Design only. Do not create it.

Proposed future test:

operator_dashboard/test_button2_premium_pdf_visual_qa_gate_contract_v1.py

Future targeted command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_qa_gate_contract_v1.py -q

This slice does not create or run that test.

## 8. Proposed Future QA Gate Module
Design only. Do not create it.

Proposed future module:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_qa_gate_v1.py

This slice does not create that module.

## 9. Future Test Strategy
The future test should use synthetic QA gate input dictionaries and the locked prototype contract output.

It may read:

- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_internal_contract_prototype_v1.json
- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_style_registry_v1.json

It may import:

- operator_dashboard/visual_intelligence/button2_premium_pdf_visual_renderer_v1.py by file path

It must not:

- import a QA gate module unless a later implementation slice creates one
- render PDFs
- generate image files
- create output artifacts
- read the local visual reference folder
- require customer data
- require external services
- require broad repo state

## 10. Required Future Test Functions
Define these required future test functions:

- test_button2_visual_qa_gate_contract_accepts_valid_internal_contract_payload
- test_button2_visual_qa_gate_contract_requires_internal_only_release_boundary
- test_button2_visual_qa_gate_contract_rejects_customer_release_true
- test_button2_visual_qa_gate_contract_rejects_learning_activation_true
- test_button2_visual_qa_gate_contract_requires_render_contract
- test_button2_visual_qa_gate_contract_requires_approved_visual_family
- test_button2_visual_qa_gate_contract_requires_evidence_panel
- test_button2_visual_qa_gate_contract_requires_disclaimer_footer
- test_button2_visual_qa_gate_contract_requires_severity_scale_for_anatomical_visual
- test_button2_visual_qa_gate_contract_requires_non_medical_disclaimer_for_anatomical_visual
- test_button2_visual_qa_gate_contract_rejects_diagnosis_or_treatment_language
- test_button2_visual_qa_gate_contract_enforces_page_density
- test_button2_visual_qa_gate_contract_enforces_accessibility_rules
- test_button2_visual_qa_gate_contract_rejects_colour_only_meaning
- test_button2_visual_qa_gate_contract_rejects_missing_numeric_scores
- test_button2_visual_qa_gate_contract_rejects_missing_confidence_labels
- test_button2_visual_qa_gate_contract_keeps_delivery_ready_false_by_default
- test_button2_visual_qa_gate_contract_requires_operator_review
- test_button2_visual_qa_gate_contract_rejects_output_artifact_reference_in_contract_only_phase
- test_button2_visual_qa_gate_contract_has_no_reference_folder_dependency
- test_button2_visual_qa_gate_contract_creates_no_pdf_or_image_artifacts

## 11. Required Future Validation Helper
Define a future helper function:

validate_visual_qa_gate_contract(qa_input)

The helper must validate:

- required QA gate input fields
- required render contract fields
- internal-only release boundary
- approved visual family
- evidence panel rendered
- disclaimer footer rendered
- severity scale rendered where required
- tactical_non_medical disclaimer for anatomical visuals
- no diagnosis or treatment language
- page density compliance
- accessibility prerequisites
- no colour-only meaning
- numeric scores present
- confidence labels present
- no output artifact reference in contract-only phase
- visual_qa_required is true
- operator_review_status is present
- delivery_ready remains false
- customer release is not authorized
- production launch is not authorized
- learning activation is not authorized

## 12. Required QA Gate Input Fields Tested
Future test must require:

- qa_gate_id
- report_id
- analysis_id
- report_version
- visual_family_id
- page_component_id
- style_registry_id
- render_contract
- visual_payload
- qa_scope
- inspection_mode
- release_boundary
- visual_qa_required
- operator_review_status

Optional future rendered-artifact fields must not be required in the contract-only phase:

- artifact_path
- artifact_type
- artifact_hash
- page_number
- dimensions
- text_elements
- table_elements
- chart_elements
- legend_elements
- disclaimer_elements
- evidence_panel_elements

## 13. Required QA Gate Output Fields Tested
Future test must define expected QA output fields:

- qa_status
- qa_gate_id
- visual_family_id
- page_component_id
- artifact_type
- delivery_ready
- release_boundary
- checks
- failed_checks
- warning_checks
- required_operator_review
- visual_qa_timestamp_policy
- blocked_reasons

Safe defaults:

qa_status=PASS_INTERNAL_ONLY or BLOCKED
delivery_ready=false
required_operator_review=true
blocked_reasons non-empty when qa_status=BLOCKED

## 14. Required Positive Case
Future test must validate a safe anatomical_target_exposure_heat_map contract payload where:

- release boundary is INTERNAL_ONLY
- render contract is CONTRACT_OBJECT_ONLY
- output_path is null
- delivery_ready is false
- evidence_panel_rendered is true
- disclaimer_footer_rendered is true
- severity_scale_rendered is true
- visual_qa_required is true
- disclaimer_variant is tactical_non_medical
- visual payload has region labels
- visual payload has numeric exposure scores
- visual payload has severity labels
- visual payload has confidence scores
- qa_status is PASS_INTERNAL_ONLY
- delivery_ready remains false
- required_operator_review is true

## 15. Required Fail-Closed Cases
Future test must verify fail-closed rejection for:

- release_scope_decision not INTERNAL_ONLY
- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- missing render_contract
- unknown visual_family_id
- missing evidence panel
- missing disclaimer footer
- missing severity scale for anatomical visual
- anatomical visual without tactical_non_medical disclaimer
- diagnosis language
- treatment language
- page density exceeded
- accessibility rule failure
- colour-only meaning
- missing numeric scores
- missing confidence labels
- delivery_ready=true before QA
- output_path non-null in contract-only phase
- artifact_path present in contract-only phase
- local reference folder dependency
- missing operator_review_status

Each fail-closed case must return:

- qa_status=BLOCKED
- delivery_ready=false
- blocked_reasons non-empty

## 16. Anatomical Visual QA Test Coverage
Future test must cover:

visual_family_id=anatomical_target_exposure_heat_map

Required:

- tactical_non_medical disclaimer
- severity scale
- evidence panel
- confidence score
- observed_vs_modelled classification
- region labels
- numeric exposure scores
- severity labels
- limitation note
- no injury diagnosis language
- no treatment guidance
- no clinical conclusion
- no medical claim

## 17. No Output Artifact Test Rule
Future test must prove:

- no PDF files are created
- no PNG files are created
- no JPG/JPEG files are created
- no customer-facing report files are created
- no delivery packages are created
- no production artifacts are created

To avoid forbidden-source-string matches, the future test should construct output suffixes from fragments instead of hard-coding image/PDF extension strings.

## 18. Reference Folder Non-Dependency Test Rule
Future test must prove:

REFERENCE_VISUAL_FOLDER_NOT_USED=YES
IMAGE_DEPENDENCY_FOUND=NO
OUTPUT_FILE_REFERENCE_FOUND=NO

Reference path to avoid:

C:\Users\jusin\OneDrive\Pictures\New Visuals

Do not embed local visual reference paths in the future test source except through external validation commands outside the test file.

## 19. Future Targeted Validation
Future test creation slice must run only:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_qa_gate_contract_v1.py -q
python -m pytest operator_dashboard/test_button2_premium_pdf_visual_internal_contract_prototype_v1.py -q

It must not run broad pytest.

## 20. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_qa_gate_contract_test_creation_v1

The next slice may create only the QA gate contract test. It must not create the QA gate module, render PDFs, or generate images.

## 21. Design Decision
BUTTON2_PREMIUM_PDF_VISUAL_QA_GATE_CONTRACT_TEST_DESIGN_READY_FOR_TEST_CREATION

Do not use:

- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- DELIVERY_APPROVED
- LEARNING_APPROVED
- IMAGE_GENERATION_APPROVED
- PDF_RENDERING_APPROVED

## 22. Slice Integrity
DOCS_CHANGED=YES
WORKFLOW_CHANGED=NO
CODE_CHANGED=NO
TEST_CHANGED=NO
FIXTURE_CHANGED=NO
DATA_CHANGED=NO
PDF_CHANGED=NO
IMAGE_CHANGED=NO
CUSTOMER_RELEASE_AUTHORIZED=NO
RELEASE_SCOPE_DECISION=INTERNAL_ONLY
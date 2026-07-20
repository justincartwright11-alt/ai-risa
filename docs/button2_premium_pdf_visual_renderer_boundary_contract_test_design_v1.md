# Button 2 Premium PDF Visual Renderer Boundary Contract Test Design v1

## 1. Purpose
This document designs the future targeted contract test for the Button 2 Premium PDF Visual Renderer boundary.

## 2. Design Boundary
This is docs-only test design.

It does not authorize:

- runtime implementation
- renderer implementation
- test creation
- fixture creation
- PDF rendering
- image generation
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

## 4. Source Renderer Boundary Reviewed
Reference:

docs/button2_premium_pdf_visual_renderer_boundary_design_v1.md

Confirm:

DESIGN_DECISION=BUTTON2_PREMIUM_PDF_VISUAL_RENDERER_BOUNDARY_READY_FOR_CONTRACT_TEST_DESIGN

## 5. Source Style Registry Lock Reviewed
Reference:

docs/button2_premium_pdf_visual_style_registry_contract_test_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_BUTTON2_VISUAL_STYLE_REGISTRY_TEST_LOCK_INTERNAL_ONLY

TARGETED_TEST_RESULT=PASS

REFERENCE_VISUAL_FOLDER_NOT_USED=YES

IMAGE_DEPENDENCY_FOUND=NO

## 6. Future Contract Test Objective
The future targeted test must validate the renderer boundary contract without rendering PDFs, generating images, touching customer delivery logic, or depending on the local visual reference folder.

## 7. Proposed Future Test File
Design only. Do not create it.

Proposed future test file:

operator_dashboard/test_button2_premium_pdf_visual_renderer_boundary_contract_v1.py

Future targeted command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_renderer_boundary_contract_v1.py -q

This slice does not create or run that test.

## 8. Proposed Future Renderer Module
Design only. Do not create it.

Proposed future renderer module:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_renderer_v1.py

This slice does not create that module.

## 9. Future Test Fixture Strategy
The future test should use in-test synthetic renderer input dictionaries.

It may read the locked style registry fixture:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_style_registry_v1.json

It must not:

- read image files
- read C:\Users\jusin\OneDrive\Pictures\New Visuals
- generate PDFs
- generate PNG/JPG/JPEG files
- require customer data
- require external services
- require broad repo state

## 10. Required Test Functions
Define these required future test functions:

- test_button2_visual_renderer_boundary_accepts_approved_visual_family
- test_button2_visual_renderer_boundary_rejects_unknown_visual_family
- test_button2_visual_renderer_boundary_requires_internal_only_release_boundary
- test_button2_visual_renderer_boundary_rejects_customer_release_authorized_true
- test_button2_visual_renderer_boundary_rejects_learning_activation_authorized_true
- test_button2_visual_renderer_boundary_requires_evidence_panel_fields
- test_button2_visual_renderer_boundary_requires_disclaimer_footer
- test_button2_visual_renderer_boundary_rejects_heat_map_without_severity_scale
- test_button2_visual_renderer_boundary_rejects_anatomical_visual_without_non_medical_disclaimer
- test_button2_visual_renderer_boundary_enforces_page_density_limits
- test_button2_visual_renderer_boundary_keeps_delivery_ready_false_by_default
- test_button2_visual_renderer_boundary_rejects_delivery_ready_without_visual_qa_pass
- test_button2_visual_renderer_boundary_does_not_require_reference_visual_folder
- test_button2_visual_renderer_boundary_does_not_generate_pdf_or_image_outputs

## 11. Required Future Validation Helper
Define a future helper function:

validate_visual_renderer_boundary_contract(input_payload, registry)

The helper must validate:

- approved visual_family_id
- internal-only release boundary
- required renderer input fields
- required evidence panel fields
- required disclaimer variant
- heat-map severity scale requirement
- anatomical non-medical disclaimer requirement
- page-density limits
- accessibility prerequisites
- visual QA gate requirement
- delivery_ready remains false unless visual_qa_status is PASS
- no customer release authority
- no production launch authority
- no learning activation authority

## 12. Required Renderer Input Fields Tested
Future test must require these input fields:

- visual_family_id
- report_id
- analysis_id
- report_version
- fighter_a_label
- fighter_b_label
- visual_title
- visual_subtitle
- data_basis
- sample_size
- source_quality
- observed_vs_modelled
- confidence_score
- uncertainty_flags
- limitation_note
- operator_review_status
- release_boundary
- visual_data
- page_density_level
- disclaimer_variant
- visual_qa_required

## 13. Required Renderer Output Fields Tested
Future test must require contract output fields if a renderer stub/scaffold exists:

- render_status
- visual_family_id
- output_type
- output_path
- page_component_id
- style_registry_id
- evidence_panel_rendered
- disclaimer_footer_rendered
- severity_scale_rendered
- accessibility_checks_passed
- page_density_checks_passed
- visual_qa_required
- visual_qa_status
- delivery_ready
- release_boundary

Safe default:

delivery_ready=false

If renderer implementation does not exist yet, the future test may validate the boundary helper and synthetic expected output contract only.

## 14. Approved Visual Family Coverage
Future test must cover all approved visual family IDs:

- anatomical_target_exposure_heat_map
- fatigue_structural_decay_heat_map
- tactical_vulnerability_map
- fighter_architecture_radar
- tactical_edge_bar_chart
- round_control_projection_line_graph
- scenario_method_pathway_tree
- ring_geography_pressure_map
- decision_structure_map
- pace_energy_fatigue_curve
- training_priority_heat_map
- scorecard_probability_table
- button3_result_comparison_visual

## 15. Anatomical Visual Negative Cases
Future test must reject anatomical visuals when:

- disclaimer_variant is missing
- disclaimer_variant is not tactical_non_medical
- severity scale is missing
- evidence panel fields are missing
- confidence_score is missing
- observed_vs_modelled is missing
- injury diagnosis language appears in limitation_note or visual_data labels

## 16. Non-Anatomical Visual Positive Cases
Future test must confirm non-anatomical visuals do not require body graphics:

- fighter_architecture_radar
- tactical_edge_bar_chart
- round_control_projection_line_graph
- scenario_method_pathway_tree
- ring_geography_pressure_map
- decision_structure_map
- pace_energy_fatigue_curve
- scorecard_probability_table
- button3_result_comparison_visual

They must still require:

- valid visual_family_id
- evidence fields where required
- readable labels
- page-density controls
- release boundary
- disclaimer footer where required

## 17. Fail-Closed Test Cases
Future test must verify fail-closed rejection for:

- missing registry fixture
- unknown visual_family_id
- release_scope_decision not INTERNAL_ONLY
- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- missing evidence panel field
- missing disclaimer footer
- heat map without severity scale
- anatomical visual without non-medical disclaimer
- exceeded page-density limit
- delivery_ready=true without visual_qa_status=PASS

## 18. Reference Folder Non-Dependency Test
Future test must prove:

REFERENCE_VISUAL_FOLDER_NOT_USED=YES

IMAGE_DEPENDENCY_FOUND=NO

It must search its own test source or validate by construction that no image path, local Windows path, PNG, JPG, or JPEG dependency exists.

Reference path to avoid:

C:\Users\jusin\OneDrive\Pictures\New Visuals

## 19. No Output Artifact Rule
Future test must prove:

- no PDF file is created
- no PNG file is created
- no JPG/JPEG file is created
- no generated image is created
- no customer-facing output is created

The boundary contract test may validate dictionaries and metadata only.

## 20. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_renderer_boundary_contract_test_creation_v1

State:

The next slice may create only the targeted renderer boundary contract test. It must not create renderer code.

## 21. Design Decision
BUTTON2_PREMIUM_PDF_VISUAL_RENDERER_BOUNDARY_CONTRACT_TEST_DESIGN_READY_FOR_TEST_CREATION

Do not use:

- IMPLEMENTATION_APPROVED
- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- LEARNING_APPROVED

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
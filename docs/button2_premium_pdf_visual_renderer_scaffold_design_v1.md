# Button 2 Premium PDF Visual Renderer Scaffold Design v1

## 1. Purpose
This document designs the smallest future Button 2 Premium PDF Visual Renderer scaffold.

## 2. Design Boundary
This is docs-only scaffold design.

It does not authorize:

- runtime implementation
- renderer implementation
- renderer scaffold creation
- PDF rendering
- image generation
- output artifact creation
- visual reference folder ingestion
- fixture changes
- test creation
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

## 4. Source Boundary Test Lock Reviewed
Reference:

docs/button2_premium_pdf_visual_renderer_boundary_contract_test_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_BUTTON2_VISUAL_RENDERER_BOUNDARY_TEST_LOCK_INTERNAL_ONLY

TARGETED_TEST_RESULT=PASS

REFERENCE_VISUAL_FOLDER_NOT_USED=YES

IMAGE_DEPENDENCY_FOUND=NO

NO_OUTPUT_ARTIFACTS_CREATED=YES

RENDERER_MODULE_CREATED=NO

## 5. Scaffold Objective
The future scaffold must accept structured internal visual payloads, load the locked style registry, validate visual-family and governance gates, and return a safe render-contract object only.

It must not produce final report graphics.

It must not write files.

It must not mark anything delivery-ready.

## 6. Proposed Future Scaffold Module
Design only. Do not create it.

Proposed future module:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_renderer_v1.py

State:

This slice does not create that module.

## 7. Proposed Future Scaffold Test
Design only. Do not create it.

Proposed future targeted test:

operator_dashboard/test_button2_premium_pdf_visual_renderer_scaffold_contract_v1.py

Future targeted command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_renderer_scaffold_contract_v1.py -q

State:

This slice does not create or run that test.

## 8. Scaffold Public Function Contract
Define the smallest future public functions:

- load_visual_style_registry(registry_path)
- build_visual_render_contract(input_payload, registry)
- validate_visual_render_contract(render_contract, registry)
- list_supported_visual_families(registry)

State:

The scaffold must not expose customer delivery, production launch, learning activation, database write, PDF write, or image write functions.

## 9. Scaffold Input Contract
The scaffold input must use the already locked boundary input fields:

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

## 10. Scaffold Output Contract
The scaffold output must return a dictionary with:

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
- blocked_reasons

Required safe defaults:

output_type=CONTRACT_OBJECT_ONLY

output_path=null

delivery_ready=false

visual_qa_status=PENDING

render_status=CONTRACT_VALIDATED_INTERNAL_ONLY or BLOCKED

## 11. Registry Loading Boundary
The future scaffold may read only:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_style_registry_v1.json

It must fail closed if:

- registry is missing
- registry JSON is invalid
- required registry keys are absent
- style registry contract expectations are violated

It must not read:

- image folders
- local Windows visual reference folders
- customer data folders
- generated report output folders
- external URLs

## 12. Visual Family Routing Boundary
The scaffold must accept only visual_family_id values found in the locked registry.

Unknown visual_family_id must return:

render_status=BLOCKED

delivery_ready=false

The scaffold must not silently downgrade unknown visual types.

## 13. Anatomical Visual Scaffold Boundary
For anatomical/heat-map families:

- anatomical_target_exposure_heat_map
- fatigue_structural_decay_heat_map
- tactical_vulnerability_map
- training_priority_heat_map

The scaffold must require:

- severity scale
- tactical_non_medical disclaimer
- evidence panel fields
- confidence score
- observed_vs_modelled field
- no injury diagnosis language
- delivery_ready=false

## 14. Non-Anatomical Visual Scaffold Boundary
For non-anatomical families:

- fighter_architecture_radar
- tactical_edge_bar_chart
- round_control_projection_line_graph
- scenario_method_pathway_tree
- ring_geography_pressure_map
- decision_structure_map
- pace_energy_fatigue_curve
- scorecard_probability_table
- button3_result_comparison_visual

The scaffold must not require anatomical graphics.

It must still require:

- valid visual_family_id
- evidence fields where required
- release boundary
- accessibility prerequisites
- page-density controls
- disclaimer footer where required
- delivery_ready=false

## 15. Fail-Closed Scaffold Conditions
The future scaffold must return BLOCKED and delivery_ready=false if:

- release_scope_decision is not INTERNAL_ONLY
- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- unknown visual_family_id
- missing evidence fields
- missing disclaimer footer
- heat map without severity scale
- anatomical visual without tactical_non_medical disclaimer
- injury diagnosis language appears
- page-density limits are exceeded
- visual_qa_required is false
- visual_qa_status is not PASS and delivery_ready would become true

## 16. No Output Artifact Rule
The future scaffold must not create:

- PDF files
- PNG files
- JPG files
- JPEG files
- customer-facing report files
- delivery packages

It may only return in-memory dictionaries in the first implementation slice.

## 17. Reference Folder Policy
Record:

C:\Users\jusin\OneDrive\Pictures\New Visuals

Policy:

- reference-only
- no runtime dependency
- no test dependency
- no repo copy without separate asset-ingestion authorization
- no customer output use
- may guide later internal visual QA/prototype work only

## 18. Future Scaffold Test Objectives
Future targeted scaffold test must verify:

- module imports without side effects
- registry loads
- supported visual families listed from registry
- approved visual family returns safe contract object
- unknown visual family returns BLOCKED
- internal-only release boundary enforced
- customer release true rejected
- learning activation true rejected
- anatomical visual without disclaimer rejected
- heat map without severity rejected
- delivery_ready defaults false
- delivery_ready true without visual QA PASS rejected
- output_path remains null
- output_type remains CONTRACT_OBJECT_ONLY
- no PDF/image artifacts created
- reference visual folder not used

## 19. Implementation Direction
Implementation should proceed in narrow slices:

1. scaffold contract test creation
2. scaffold module creation with contract-object-only behavior
3. targeted scaffold test run
4. scaffold review lock
5. one internal non-customer visual contract prototype
6. visual QA gate design
7. internal-only sample page generation
8. review lock

Do not authorize implementation in this slice.

## 20. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_renderer_scaffold_contract_test_creation_v1

State:

The next slice may create only the targeted scaffold contract test. It must not create renderer code.

## 21. Design Decision
Use:

BUTTON2_PREMIUM_PDF_VISUAL_RENDERER_SCAFFOLD_DESIGN_READY_FOR_CONTRACT_TEST_CREATION

Do not use:

- IMPLEMENTATION_APPROVED
- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- LEARNING_APPROVED

## 22. Slice Integrity
State:

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
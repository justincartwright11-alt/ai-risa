# Button 2 Premium PDF Visual Internal Contract Prototype Design v1

## 1. Purpose
This document designs the first internal Button 2 Premium PDF Visual contract prototype.

## 2. Design Boundary
This is docs-only prototype design.

It does not authorize:

- runtime implementation
- renderer feature expansion
- prototype fixture creation
- test creation
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

## 4. Source Scaffold Module Lock Reviewed
Reference:

docs/button2_premium_pdf_visual_renderer_scaffold_module_review_v1.md

Confirm:

REVIEW_DECISION=APPROVED_FOR_BUTTON2_VISUAL_RENDERER_SCAFFOLD_MODULE_LOCK_INTERNAL_ONLY

TARGETED_SCAFFOLD_CONTRACT_TEST_RESULT=PASS

MODULE_IMPORT_VALIDATION_RESULT=PASS

REFERENCE_VISUAL_FOLDER_NOT_USED=YES

IMAGE_DEPENDENCY_FOUND=NO

NO_OUTPUT_ARTIFACTS_CREATED=YES

## 5. Prototype Objective
The prototype must prove that an internal anatomical heat-map visual payload can pass through the scaffold as a safe contract object while preserving the style registry, severity scale, non-medical disclaimer, evidence panel, page-density, accessibility, and internal-only release gates.

## 6. Prototype Visual Family
visual_family_id=anatomical_target_exposure_heat_map

This is a tactical exposure heat map, not an injury diagnosis, medical assessment, treatment recommendation, or claim of anatomical damage.

## 7. Proposed Future Prototype Fixture
Design only. Do not create it.

Proposed future file:

operator_dashboard/visual_intelligence/button2_premium_pdf_visual_internal_contract_prototype_v1.json

This slice does not create that file.

## 8. Proposed Future Prototype Contract Test
Design only. Do not create it.

Proposed future test:

operator_dashboard/test_button2_premium_pdf_visual_internal_contract_prototype_v1.py

Future targeted command:

python -m pytest operator_dashboard/test_button2_premium_pdf_visual_internal_contract_prototype_v1.py -q

This slice does not create or run that test.

## 9. Prototype Input Contract
Define required prototype input fields:

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

## 10. Prototype Release Boundary
Prototype input must use:

release_scope_decision=INTERNAL_ONLY

customer_release_authorized=false

public_publishing_authorized=false

production_launch_authorized=false

automated_delivery_authorized=false

learning_activation_authorized=false

Any unsafe value must fail closed.

## 11. Prototype Visual Data Contract
visual_data must include:

- severity_scale_present
- severity_scale_name
- heat_map_regions
- region_id
- region_label
- tactical_meaning
- exposure_score
- confidence_score
- observed_vs_modelled
- evidence_basis
- uncertainty_flags
- labels

Required safe value:

severity_scale_present=true

## 12. Heat Map Region Contract
Each heat_map_region must include:

- region_id
- region_label
- exposure_score
- severity_band
- tactical_meaning
- evidence_basis
- observed_vs_modelled
- confidence_score
- uncertainty_flags

Allowed severity_band values:

- very_low
- low
- moderate
- high
- very_high
- critical_only_if_threshold_supported

## 13. Non-Medical Disclaimer Contract
Prototype must require:

disclaimer_variant=tactical_non_medical

The visible disclaimer meaning must be equivalent to:

TACTICAL ANALYSIS — NOT A MEDICAL DIAGNOSIS

Prohibit:

- diagnosed
- diagnosis
- fracture
- concussion
- torn ligament
- medical injury
- brain injury
- treatment recommendation
- clinical conclusion

## 14. Evidence Panel Contract
Prototype must include or preserve:

- analysis_id
- report_version
- data_basis
- sample_size
- source_quality
- observed_vs_modelled
- confidence_score
- uncertainty_flags
- limitation_note
- operator_review_status

## 15. Page Density Contract
Prototype must use:

page_density_level=level_1_hero

The anatomical heat map is a Level 1 hero visual and must not be crowded with dense chart clusters on the same future PDF page.

## 16. Accessibility Contract
Prototype must require:

- region labels
- numeric scores
- severity labels
- confidence labels
- no colour-only meaning
- no unlabeled glow
- no tiny unreadable text
- no table numbers on glowing backgrounds

## 17. Scaffold Output Expectation
When passed through the scaffold, expected safe contract output must be:

render_status=CONTRACT_VALIDATED_INTERNAL_ONLY

output_type=CONTRACT_OBJECT_ONLY

output_path=null

delivery_ready=false

visual_qa_status=PENDING

evidence_panel_rendered=true

disclaimer_footer_rendered=true

severity_scale_rendered=true

blocked_reasons=[]

This is not a rendered visual. It is only a contract object proving the payload is safe for a later internal prototype.

## 18. Fail-Closed Conditions
Prototype must fail closed if:

- registry missing
- unknown visual_family_id
- release boundary is not INTERNAL_ONLY
- customer_release_authorized=true
- public_publishing_authorized=true
- production_launch_authorized=true
- automated_delivery_authorized=true
- learning_activation_authorized=true
- severity_scale_present is false
- disclaimer_variant is not tactical_non_medical
- evidence panel fields are missing
- heat_map_regions are missing
- region labels are missing
- numeric exposure scores are missing
- injury diagnosis language appears
- visual_qa_required is false
- delivery_ready=true is requested
- output_path is not null
- output_type is not CONTRACT_OBJECT_ONLY

## 19. Reference Folder Policy
Record:

C:\Users\jusin\OneDrive\Pictures\New Visuals

Policy:

- reference-only
- not read in this slice
- not copied in this slice
- not a runtime dependency
- not a test dependency
- may guide later internal visual QA/prototype layout only after separate authorization

## 20. No Output Artifact Rule
Prototype must not create:

- PDF files
- PNG files
- JPG files
- JPEG files
- customer-facing report files
- delivery packages
- production artifacts

## 21. Future Implementation Direction
Implementation should proceed in narrow slices:

1. internal prototype fixture creation
2. internal prototype contract test creation
3. scaffold pass-through validation
4. prototype review lock
5. visual QA gate design
6. internal-only non-customer page prototype design
7. internal-only page prototype creation
8. review lock

Do not authorize implementation in this slice.

## 22. Recommended Next Slice
Recommend:

button2_premium_pdf_visual_internal_contract_prototype_fixture_creation_v1

The next slice may create only the internal contract prototype JSON fixture. It must not generate PDFs or images.

## 23. Design Decision
Use:

BUTTON2_PREMIUM_PDF_VISUAL_INTERNAL_CONTRACT_PROTOTYPE_DESIGN_READY_FOR_FIXTURE_CREATION

Do not use:

- CUSTOMER_RELEASE_APPROVED
- PRODUCTION_APPROVED
- DELIVERY_APPROVED
- LEARNING_APPROVED
- IMAGE_GENERATION_APPROVED
- PDF_RENDERING_APPROVED

## 24. Slice Integrity
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
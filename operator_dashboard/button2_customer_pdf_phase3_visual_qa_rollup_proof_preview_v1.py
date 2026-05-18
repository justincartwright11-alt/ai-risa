"""
Button 2 Customer PDF Phase 3 - Visual QA Rollup Proof Preview v1

Fail-closed, governance-safe proof channel for validating visual quality assertions
from rendered-output evidence input without PDF generation, file writes, or behavior changes.

Reference: docs/button2-customer-pdf-phase3-visual-qa-rollup-proof-design-v1.md
Commit lock: 2d132f6
"""


def run_visual_qa_rollup_proof(
    visual_qa_hits,
    required_margin_ranges,
    required_padding_ranges,
    required_typography_consistency_markers,
    required_color_consistency_markers,
    required_alignment_markers,
    required_spacing_consistency_markers,
    visual_qa_channel_available=True,
):
    """
    Validate visual QA rollup assertions from rendered-output proof input.

    Args:
        visual_qa_hits: list of visual QA evidence records
        required_margin_ranges: dict mapping page_section -> [min_margin, max_margin]
        required_padding_ranges: dict mapping component_type -> [min_padding, max_padding]
        required_typography_consistency_markers: list of required typography consistency tokens
        required_color_consistency_markers: list of required color consistency tokens
        required_alignment_markers: list of required alignment tokens
        required_spacing_consistency_markers: list of required spacing consistency tokens
        visual_qa_channel_available: bool, default True (channel availability flag)

    Returns:
        dict with proof status, signal, failure reasons, and hard safety flags

    Each hit should have:
        - section_name (str)
        - check_id (str)
        - check_type (str: margin|padding|typography|color|alignment|spacing|hierarchy)
        - component_name (str)
        - value (int/float for ranges, str for token presence)
        - status (str: pass|fail)
        - optional marker_id (str)
    """

    result = {
        "schema_version": "button2.phase3.visual_qa_rollup_proof.v1",
        "proof_channel": "visual_qa_rollup",
        "proof_status": "failed_closed",
        "rollup_signal": "unavailable",
        "failure_reasons": [],
        "discovered_visual_qa_hit_count": 0,
        "out_of_range_margins": [],
        "out_of_range_padding": [],
        "missing_typography_consistency_markers": [],
        "missing_color_consistency_markers": [],
        "missing_alignment_markers": [],
        "missing_spacing_consistency_markers": [],
        "visual_hierarchy_failures": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    # Channel availability check
    if not visual_qa_channel_available:
        result["rollup_signal"] = "unavailable"
        result["failure_reasons"].append("visual_qa_channel_unavailable")
        return result

    # Normalize inputs (raise RuntimeError on malformed shape)
    try:
        if not isinstance(visual_qa_hits, list):
            raise RuntimeError("visual_qa_hits must be list")
        if not isinstance(required_margin_ranges, dict):
            raise RuntimeError("required_margin_ranges must be dict")
        if not isinstance(required_padding_ranges, dict):
            raise RuntimeError("required_padding_ranges must be dict")
        if not isinstance(required_typography_consistency_markers, list):
            raise RuntimeError("required_typography_consistency_markers must be list")
        if not isinstance(required_color_consistency_markers, list):
            raise RuntimeError("required_color_consistency_markers must be list")
        if not isinstance(required_alignment_markers, list):
            raise RuntimeError("required_alignment_markers must be list")
        if not isinstance(required_spacing_consistency_markers, list):
            raise RuntimeError("required_spacing_consistency_markers must be list")

        # Validate each hit shape
        for idx, hit in enumerate(visual_qa_hits):
            if not isinstance(hit, dict):
                raise RuntimeError(f"hit {idx} must be dict, got {type(hit)}")
            required_fields = [
                "section_name",
                "check_id",
                "check_type",
                "component_name",
                "value",
                "status",
            ]
            for field in required_fields:
                if field not in hit:
                    raise RuntimeError(f"hit {idx} missing required field: {field}")

            # Validate field types
            if not isinstance(hit["section_name"], str):
                raise RuntimeError(f"hit {idx}.section_name must be str")
            if not isinstance(hit["check_id"], str):
                raise RuntimeError(f"hit {idx}.check_id must be str")
            if not isinstance(hit["check_type"], str):
                raise RuntimeError(f"hit {idx}.check_type must be str")
            if hit["check_type"] not in [
                "margin",
                "padding",
                "typography",
                "color",
                "alignment",
                "spacing",
                "hierarchy",
            ]:
                raise RuntimeError(
                    f"hit {idx}.check_type must be one of: margin, padding, typography, color, alignment, spacing, hierarchy"
                )
            if not isinstance(hit["component_name"], str):
                raise RuntimeError(f"hit {idx}.component_name must be str")
            if not isinstance(hit["value"], (int, float, str)):
                raise RuntimeError(f"hit {idx}.value must be int, float, or str")
            if not isinstance(hit["status"], str):
                raise RuntimeError(f"hit {idx}.status must be str")
            if hit["status"] not in ["pass", "fail"]:
                raise RuntimeError(f"hit {idx}.status must be 'pass' or 'fail'")

    except RuntimeError:
        result["rollup_signal"] = "unavailable"
        result["failure_reasons"].append("invalid_visual_qa_hit_shape")
        return result

    # Collect evidence
    result["discovered_visual_qa_hit_count"] = len(visual_qa_hits)

    discovered_margin_sections = {}
    discovered_padding_components = {}
    discovered_typography_markers = set()
    discovered_color_markers = set()
    discovered_alignment_markers = set()
    discovered_spacing_markers = set()
    discovered_hierarchy_markers = {}

    for hit in visual_qa_hits:
        section_name = hit["section_name"]
        check_type = hit["check_type"]
        component_name = hit["component_name"]
        value = hit["value"]
        status = hit["status"]

        if check_type == "margin":
            section_key = section_name
            if section_key not in discovered_margin_sections:
                discovered_margin_sections[section_key] = []
            discovered_margin_sections[section_key].append(
                {"value": value, "status": status, "component": component_name}
            )

        elif check_type == "padding":
            component_key = component_name
            if component_key not in discovered_padding_components:
                discovered_padding_components[component_key] = []
            discovered_padding_components[component_key].append(
                {"value": value, "status": status}
            )

        elif check_type == "typography":
            if isinstance(value, str):
                discovered_typography_markers.add(value)

        elif check_type == "color":
            if isinstance(value, str):
                discovered_color_markers.add(value)

        elif check_type == "alignment":
            if isinstance(value, str):
                discovered_alignment_markers.add(value)

        elif check_type == "spacing":
            if isinstance(value, str):
                discovered_spacing_markers.add(value)

        elif check_type == "hierarchy":
            hierarchy_key = f"{section_name}:{component_name}"
            if hierarchy_key not in discovered_hierarchy_markers:
                discovered_hierarchy_markers[hierarchy_key] = status

    # Check 1: Margin ranges
    for section_name, (min_margin, max_margin) in required_margin_ranges.items():
        if section_name in discovered_margin_sections:
            for measurement in discovered_margin_sections[section_name]:
                if isinstance(measurement["value"], (int, float)):
                    if (
                        measurement["value"] < min_margin
                        or measurement["value"] > max_margin
                    ):
                        result["out_of_range_margins"].append(
                            {
                                "section": section_name,
                                "component": measurement["component"],
                                "value": measurement["value"],
                                "required_range": [min_margin, max_margin],
                            }
                        )
                        result["failure_reasons"].append("out_of_range_margins")
        else:
            result["out_of_range_margins"].append(
                {
                    "section": section_name,
                    "missing": True,
                    "required_range": [min_margin, max_margin],
                }
            )
            result["failure_reasons"].append("out_of_range_margins")

    # Check 2: Padding ranges
    for component_type, (min_padding, max_padding) in required_padding_ranges.items():
        if component_type in discovered_padding_components:
            for measurement in discovered_padding_components[component_type]:
                if isinstance(measurement["value"], (int, float)):
                    if (
                        measurement["value"] < min_padding
                        or measurement["value"] > max_padding
                    ):
                        result["out_of_range_padding"].append(
                            {
                                "component_type": component_type,
                                "value": measurement["value"],
                                "required_range": [min_padding, max_padding],
                            }
                        )
                        result["failure_reasons"].append("out_of_range_padding")
        else:
            result["out_of_range_padding"].append(
                {
                    "component_type": component_type,
                    "missing": True,
                    "required_range": [min_padding, max_padding],
                }
            )
            result["failure_reasons"].append("out_of_range_padding")

    # Check 3: Typography consistency markers
    for required_marker in required_typography_consistency_markers:
        if required_marker not in discovered_typography_markers:
            result["missing_typography_consistency_markers"].append(required_marker)
            result["failure_reasons"].append("missing_typography_consistency_markers")

    # Check 4: Color consistency markers
    for required_marker in required_color_consistency_markers:
        if required_marker not in discovered_color_markers:
            result["missing_color_consistency_markers"].append(required_marker)
            result["failure_reasons"].append("missing_color_consistency_markers")

    # Check 5: Alignment markers
    for required_marker in required_alignment_markers:
        if required_marker not in discovered_alignment_markers:
            result["missing_alignment_markers"].append(required_marker)
            result["failure_reasons"].append("missing_alignment_markers")

    # Check 6: Spacing consistency markers
    for required_marker in required_spacing_consistency_markers:
        if required_marker not in discovered_spacing_markers:
            result["missing_spacing_consistency_markers"].append(required_marker)
            result["failure_reasons"].append("missing_spacing_consistency_markers")

    # Check 7: Visual hierarchy (any hierarchy marker with status=fail is a failure)
    for hierarchy_key, status in discovered_hierarchy_markers.items():
        if status == "fail":
            result["visual_hierarchy_failures"].append(hierarchy_key)
            result["failure_reasons"].append("visual_hierarchy_validation_failed")

    # Determine signal and status
    if result["failure_reasons"]:
        result["rollup_signal"] = "detected"
        result["proof_status"] = "failed_closed"
    else:
        result["rollup_signal"] = "clear"
        result["proof_status"] = "passed"

    return result

"""
Button 2 Customer PDF Phase 3 - Source Traceability Proof Preview v1

Fail-closed, governance-safe proof channel for validating source-traceability claims
from rendered-output evidence input without PDF generation, file writes, or behavior changes.

Reference: docs/button2-customer-pdf-phase3-source-traceability-proof-design-v1.md
Commit lock: df633a3
"""


def run_source_traceability_proof(
    source_traceability_hits,
    required_source_classes,
    required_citations_per_section,
    forbidden_source_classes,
    required_verification_statuses,
    source_channel_available=True,
):
    """
    Validate source-traceability claims from rendered-output proof input.

    Args:
        source_traceability_hits: list of source traceability evidence records
        required_source_classes: list of required source class tokens
        required_citations_per_section: dict mapping section_name -> minimum citation count
        forbidden_source_classes: list of forbidden source class tokens
        required_verification_statuses: list of required verification status tokens
        source_channel_available: bool, default True (channel availability flag)

    Returns:
        dict with proof status, signal, failure reasons, and hard safety flags

    Each hit should have:
        - section_name (str)
        - source_index (int >= 0)
        - source_type (str)
        - source_class (str)
        - citation_count (int >= 0)
        - verification_status (str)
        - optional marker_id (str)
        - optional source_label (str)
        - optional source_confidence (str)
        - optional source_footer_marker (str or bool)
    """

    result = {
        "schema_version": "button2.phase3.source_traceability_proof.v1",
        "proof_channel": "source_traceability",
        "proof_status": "failed_closed",
        "source_signal": "unavailable",
        "failure_reasons": [],
        "discovered_source_hit_count": 0,
        "missing_required_source_classes": [],
        "missing_required_citations": {},
        "missing_required_verification_statuses": [],
        "forbidden_source_classes_detected": [],
        "invalid_source_label_shapes": [],
        "invalid_source_confidence_shapes": [],
        "missing_source_footer_markers": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    # Channel availability check
    if not source_channel_available:
        result["source_signal"] = "unavailable"
        result["failure_reasons"].append("source_channel_unavailable")
        return result

    # Normalize inputs (raise RuntimeError on malformed shape)
    try:
        if not isinstance(source_traceability_hits, list):
            raise RuntimeError("source_traceability_hits must be list")
        if not isinstance(required_source_classes, list):
            raise RuntimeError("required_source_classes must be list")
        if not isinstance(required_citations_per_section, dict):
            raise RuntimeError("required_citations_per_section must be dict")
        if not isinstance(forbidden_source_classes, list):
            raise RuntimeError("forbidden_source_classes must be list")
        if not isinstance(required_verification_statuses, list):
            raise RuntimeError("required_verification_statuses must be list")

        # Validate each hit shape
        for idx, hit in enumerate(source_traceability_hits):
            if not isinstance(hit, dict):
                raise RuntimeError(f"hit {idx} must be dict, got {type(hit)}")
            required_fields = [
                "section_name",
                "source_index",
                "source_type",
                "source_class",
                "citation_count",
                "verification_status",
            ]
            for field in required_fields:
                if field not in hit:
                    raise RuntimeError(f"hit {idx} missing required field: {field}")

            # Validate field types
            if not isinstance(hit["section_name"], str):
                raise RuntimeError(f"hit {idx}.section_name must be str")
            if not isinstance(hit["source_index"], int) or hit["source_index"] < 0:
                raise RuntimeError(f"hit {idx}.source_index must be int >= 0")
            if not isinstance(hit["source_type"], str):
                raise RuntimeError(f"hit {idx}.source_type must be str")
            if not isinstance(hit["source_class"], str):
                raise RuntimeError(f"hit {idx}.source_class must be str")
            if not isinstance(hit["citation_count"], int) or hit["citation_count"] < 0:
                raise RuntimeError(f"hit {idx}.citation_count must be int >= 0")
            if not isinstance(hit["verification_status"], str):
                raise RuntimeError(f"hit {idx}.verification_status must be str")

            # Optional field shape validation
            if "source_label" in hit:
                if not isinstance(hit["source_label"], str) and hit["source_label"] is not None:
                    raise RuntimeError(f"hit {idx}.source_label must be str or None")
            if "source_confidence" in hit:
                if not isinstance(hit["source_confidence"], str) and hit["source_confidence"] is not None:
                    raise RuntimeError(f"hit {idx}.source_confidence must be str or None")

    except RuntimeError:
        result["source_signal"] = "unavailable"
        result["failure_reasons"].append("invalid_source_hit_shape")
        return result

    # Collect evidence
    result["discovered_source_hit_count"] = len(source_traceability_hits)

    discovered_source_classes = set()
    discovered_verification_statuses = set()
    discovered_citations_by_section = {}
    discovered_footer_markers_by_section = {}

    for hit in source_traceability_hits:
        section_name = hit["section_name"]
        source_class = hit["source_class"]
        citation_count = hit["citation_count"]
        verification_status = hit["verification_status"]

        discovered_source_classes.add(source_class)
        discovered_verification_statuses.add(verification_status)

        # Track citations per section
        if section_name not in discovered_citations_by_section:
            discovered_citations_by_section[section_name] = 0
        discovered_citations_by_section[section_name] += citation_count

        # Track footer marker presence
        if section_name not in discovered_footer_markers_by_section:
            discovered_footer_markers_by_section[section_name] = False
        if "source_footer_marker" in hit and hit["source_footer_marker"]:
            discovered_footer_markers_by_section[section_name] = True

    # Check 1: Required source classes
    for required_class in required_source_classes:
        if required_class not in discovered_source_classes:
            result["missing_required_source_classes"].append(required_class)
            result["failure_reasons"].append("missing_required_source_classes")

    # Check 2: Required verification statuses
    for required_status in required_verification_statuses:
        if required_status not in discovered_verification_statuses:
            result["missing_required_verification_statuses"].append(required_status)
            result["failure_reasons"].append("missing_required_verification_statuses")

    # Check 3: Citation minimums per section
    for section_name, min_citations in required_citations_per_section.items():
        discovered_count = discovered_citations_by_section.get(section_name, 0)
        if discovered_count < min_citations:
            result["missing_required_citations"][section_name] = {
                "required": min_citations,
                "discovered": discovered_count,
            }
            result["failure_reasons"].append("missing_required_citations")

    # Check 4: Forbidden source classes
    for forbidden_class in forbidden_source_classes:
        if forbidden_class in discovered_source_classes:
            result["forbidden_source_classes_detected"].append(forbidden_class)
            result["failure_reasons"].append("forbidden_source_classes_detected")

    # Check 5: Source label/confidence shape validation
    for hit in source_traceability_hits:
        if "source_label" in hit and hit["source_label"] is not None:
            if not isinstance(hit["source_label"], str) or not hit["source_label"].strip():
                result["invalid_source_label_shapes"].append(hit.get("marker_id", "unknown"))
                result["failure_reasons"].append("invalid_source_label_shape")
        if "source_confidence" in hit and hit["source_confidence"] is not None:
            if not isinstance(hit["source_confidence"], str) or not hit["source_confidence"].strip():
                result["invalid_source_confidence_shapes"].append(hit.get("marker_id", "unknown"))
                result["failure_reasons"].append("invalid_source_confidence_shape")

    # Check 6: Source footer marker presence
    for section_name in required_citations_per_section.keys():
        if not discovered_footer_markers_by_section.get(section_name, False):
            result["missing_source_footer_markers"].append(section_name)
            result["failure_reasons"].append("missing_source_footer_markers")

    # Determine signal and status
    if result["failure_reasons"]:
        result["source_signal"] = "detected"
        result["proof_status"] = "failed_closed"
    else:
        result["source_signal"] = "clear"
        result["proof_status"] = "passed"

    return result

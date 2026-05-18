"""Phase 3 Page-Section Proof Preview (v1).

Proof helper only.
No rendering changes.
No PDF writes.
No certification automation.
"""

_SCHEMA_VERSION = "button2.phase3.page_section_proof.v1"


def _normalize_section_hits(section_hits):
    if not isinstance(section_hits, list):
        raise RuntimeError("invalid_section_hit_shape")

    normalized = []
    for hit in section_hits:
        if not isinstance(hit, dict):
            raise RuntimeError("invalid_section_hit_shape")

        section_name = hit.get("section_name")
        page_index = hit.get("page_index")
        marker_id = hit.get("marker_id")

        if not section_name or not isinstance(section_name, str):
            raise RuntimeError("invalid_section_hit_shape")
        if not isinstance(page_index, int) or page_index < 0:
            raise RuntimeError("invalid_section_hit_shape")
        if marker_id is not None and not isinstance(marker_id, str):
            raise RuntimeError("invalid_section_hit_shape")

        normalized.append(
            {
                "section_name": section_name,
                "page_index": page_index,
                "marker_id": marker_id,
            }
        )
    return normalized


def _normalize_required_sections(required_sections):
    if required_sections is None:
        return []
    if not isinstance(required_sections, list):
        raise RuntimeError("invalid_section_hit_shape")
    for section_name in required_sections:
        if not section_name or not isinstance(section_name, str):
            raise RuntimeError("invalid_section_hit_shape")
    return list(required_sections)


def _allowed_pages_for_section(rule):
    if isinstance(rule, (list, tuple, set)):
        pages = set()
        for page in rule:
            if not isinstance(page, int) or page < 0:
                raise RuntimeError("missing_allowed_page_rules")
            pages.add(page)
        return pages

    if isinstance(rule, dict):
        min_page = rule.get("min_page")
        max_page = rule.get("max_page")
        if not isinstance(min_page, int) or not isinstance(max_page, int):
            raise RuntimeError("missing_allowed_page_rules")
        if min_page < 0 or max_page < min_page:
            raise RuntimeError("missing_allowed_page_rules")
        return set(range(min_page, max_page + 1))

    raise RuntimeError("missing_allowed_page_rules")


def _normalize_allowed_section_pages(allowed_section_pages, required_sections):
    if not isinstance(allowed_section_pages, dict):
        raise RuntimeError("missing_allowed_page_rules")

    normalized = {}
    for section_name in required_sections:
        if section_name not in allowed_section_pages:
            raise RuntimeError("missing_allowed_page_rules")
        normalized[section_name] = _allowed_pages_for_section(allowed_section_pages[section_name])
    return normalized


def _normalize_page_count(value):
    if value is None:
        return None
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError("invalid_section_hit_shape")
    return value


def run_page_section_proof(
    section_hits,
    required_sections,
    allowed_section_pages,
    observed_page_count=None,
    expected_page_count=None,
    forbid_duplicate_required_sections=True,
    section_channel_available=True,
):
    """Run fail-closed page-section proof from supplied section-hit inputs."""
    result = {
        "schema_version": _SCHEMA_VERSION,
        "proof_channel": "page_section",
        "proof_status": "failed_closed",
        "section_signal": "unavailable",
        "failure_reasons": [],
        "discovered_section_count": 0,
        "missing_required_sections": [],
        "section_order_violations": [],
        "out_of_bounds_sections": [],
        "ambiguous_sections": [],
        "page_count_validation": {
            "observed_page_count": observed_page_count,
            "expected_page_count": expected_page_count,
            "matches_expected": None,
        },
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    if not section_channel_available:
        result["failure_reasons"].append("section_channel_unavailable")
        return result

    try:
        normalized_hits = _normalize_section_hits(section_hits)
        required = _normalize_required_sections(required_sections)
        allowed_pages = _normalize_allowed_section_pages(allowed_section_pages, required)
        observed = _normalize_page_count(observed_page_count)
        expected = _normalize_page_count(expected_page_count)
    except RuntimeError as exc:
        result["failure_reasons"].append(str(exc))
        return result

    result["discovered_section_count"] = len(normalized_hits)
    by_name = {}
    first_positions = {}
    for idx, hit in enumerate(normalized_hits):
        section_name = hit["section_name"]
        by_name.setdefault(section_name, []).append(hit)
        if section_name not in first_positions:
            first_positions[section_name] = idx

    missing_required = [name for name in required if name not in by_name]
    result["missing_required_sections"] = missing_required
    if missing_required:
        result["failure_reasons"].append("missing_required_sections")

    ambiguous_sections = []
    if forbid_duplicate_required_sections:
        for section_name in required:
            if len(by_name.get(section_name, [])) > 1:
                ambiguous_sections.append(section_name)
    if ambiguous_sections:
        result["ambiguous_sections"] = sorted(set(ambiguous_sections))
        result["failure_reasons"].append("ambiguous_section_mapping")

    out_of_bounds = []
    for section_name in required:
        if section_name in missing_required:
            continue
        allowed = allowed_pages[section_name]
        for hit in by_name.get(section_name, []):
            if hit["page_index"] not in allowed:
                out_of_bounds.append(section_name)
                break
    if out_of_bounds:
        result["out_of_bounds_sections"] = sorted(set(out_of_bounds))
        result["failure_reasons"].append("section_page_out_of_bounds")

    order_violations = []
    present_required = [name for name in required if name in first_positions]
    for idx in range(1, len(present_required)):
        left = present_required[idx - 1]
        right = present_required[idx]
        if first_positions[left] > first_positions[right]:
            order_violations.append([left, right])
    if order_violations:
        result["section_order_violations"] = order_violations
        result["failure_reasons"].append("section_order_mismatch")

    matches_expected = None
    if observed is not None and expected is not None:
        matches_expected = observed == expected
        if not matches_expected:
            result["failure_reasons"].append("page_count_mismatch")
    result["page_count_validation"] = {
        "observed_page_count": observed,
        "expected_page_count": expected,
        "matches_expected": matches_expected,
    }

    if not result["failure_reasons"]:
        result["proof_status"] = "passed"
        result["section_signal"] = "clear"
    else:
        result["section_signal"] = "detected"

    return result

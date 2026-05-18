"""Phase 3 Typography-Style Proof Preview (v1).

Proof helper only.
No rendering changes.
No PDF writes.
No certification automation.
"""

_SCHEMA_VERSION = "button2.phase3.typography_style_proof.v1"


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalize_string_list(values, error_reason):
    if values is None:
        return []
    if not isinstance(values, list):
        raise RuntimeError(error_reason)
    output = []
    for value in values:
        if not value or not isinstance(value, str):
            raise RuntimeError(error_reason)
        output.append(value)
    return output


def _normalize_style_hits(style_hits):
    if not isinstance(style_hits, list):
        raise RuntimeError("invalid_style_hit_shape")

    normalized = []
    for hit in style_hits:
        if not isinstance(hit, dict):
            raise RuntimeError("invalid_style_hit_shape")

        section_name = hit.get("section_name")
        token = hit.get("token")
        class_name = hit.get("class_name")
        marker_id = hit.get("marker_id")
        font_size = hit.get("font_size")
        font_weight = hit.get("font_weight")
        line_height = hit.get("line_height")

        if not section_name or not isinstance(section_name, str):
            raise RuntimeError("invalid_style_hit_shape")
        if not token or not isinstance(token, str):
            raise RuntimeError("invalid_style_hit_shape")
        if class_name is not None and not isinstance(class_name, str):
            raise RuntimeError("invalid_style_hit_shape")
        if marker_id is not None and not isinstance(marker_id, str):
            raise RuntimeError("invalid_style_hit_shape")
        if font_size is not None and not _is_number(font_size):
            raise RuntimeError("invalid_style_hit_shape")
        if font_weight is not None and not isinstance(font_weight, (int, str)):
            raise RuntimeError("invalid_style_hit_shape")
        if line_height is not None and not _is_number(line_height):
            raise RuntimeError("invalid_style_hit_shape")

        normalized.append(
            {
                "section_name": section_name,
                "token": token,
                "class_name": class_name,
                "marker_id": marker_id,
                "font_size": None if font_size is None else float(font_size),
                "font_weight": None if font_weight is None else str(font_weight),
                "line_height": None if line_height is None else float(line_height),
            }
        )

    return normalized


def _normalize_range(range_value, field_name):
    if range_value is None:
        return None
    if not isinstance(range_value, (list, tuple)) or len(range_value) != 2:
        raise RuntimeError("invalid_style_hit_shape")
    low, high = range_value
    if not _is_number(low) or not _is_number(high) or low > high:
        raise RuntimeError("invalid_style_hit_shape")
    return (float(low), float(high), field_name)


def _in_range(value, range_triplet):
    low, high, _name = range_triplet
    return low <= value <= high


def run_typography_style_proof(
    style_hits,
    required_style_tokens,
    forbidden_style_tokens,
    section_style_rules,
    required_style_classes=None,
    required_typography_markers=None,
    allowed_font_weights=None,
    font_size_range=None,
    line_height_range=None,
    style_channel_available=True,
):
    """Run fail-closed typography/style proof from supplied style evidence."""
    result = {
        "schema_version": _SCHEMA_VERSION,
        "proof_channel": "typography_style",
        "proof_status": "failed_closed",
        "style_signal": "unavailable",
        "failure_reasons": [],
        "discovered_style_hit_count": 0,
        "missing_required_style_tokens": [],
        "forbidden_style_tokens_detected": [],
        "missing_typography_markers": [],
        "missing_required_style_classes": [],
        "invalid_style_values": [],
        "section_style_violations": {},
        "ambiguous_style_sections": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    if not style_channel_available:
        result["failure_reasons"].append("style_channel_unavailable")
        return result

    try:
        normalized_hits = _normalize_style_hits(style_hits)
        required_tokens = _normalize_string_list(required_style_tokens, "invalid_style_hit_shape")
        forbidden_tokens = _normalize_string_list(forbidden_style_tokens, "invalid_style_hit_shape")
        required_classes = _normalize_string_list(required_style_classes, "invalid_style_hit_shape")
        required_markers = _normalize_string_list(required_typography_markers, "invalid_style_hit_shape")
        allowed_weights = _normalize_string_list(allowed_font_weights, "invalid_style_hit_shape")

        if not isinstance(section_style_rules, dict):
            raise RuntimeError("missing_section_style_rules")
        for section_name, required_section_tokens in section_style_rules.items():
            if not section_name or not isinstance(section_name, str):
                raise RuntimeError("missing_section_style_rules")
            _normalize_string_list(required_section_tokens, "missing_section_style_rules")

        size_range = _normalize_range(font_size_range, "font_size")
        height_range = _normalize_range(line_height_range, "line_height")
    except RuntimeError as exc:
        result["failure_reasons"].append(str(exc))
        return result

    result["discovered_style_hit_count"] = len(normalized_hits)

    discovered_tokens = {hit["token"] for hit in normalized_hits}
    discovered_classes = {hit["class_name"] for hit in normalized_hits if hit["class_name"]}
    discovered_markers = {hit["marker_id"] for hit in normalized_hits if hit["marker_id"]}

    missing_tokens = [token for token in required_tokens if token not in discovered_tokens]
    if missing_tokens:
        result["missing_required_style_tokens"] = missing_tokens
        result["failure_reasons"].append("missing_required_style_tokens")

    detected_forbidden = sorted(token for token in forbidden_tokens if token in discovered_tokens)
    if detected_forbidden:
        result["forbidden_style_tokens_detected"] = detected_forbidden
        result["failure_reasons"].append("forbidden_style_tokens_detected")

    missing_classes = [name for name in required_classes if name not in discovered_classes]
    if missing_classes:
        result["missing_required_style_classes"] = missing_classes
        result["failure_reasons"].append("missing_required_style_classes")

    missing_markers = [marker for marker in required_markers if marker not in discovered_markers]
    if missing_markers:
        result["missing_typography_markers"] = missing_markers
        result["failure_reasons"].append("missing_typography_markers")

    by_section = {}
    for hit in normalized_hits:
        by_section.setdefault(hit["section_name"], []).append(hit)

    section_violations = {}
    ambiguous_sections = []
    for section_name, required_section_tokens in section_style_rules.items():
        section_hits = by_section.get(section_name, [])
        section_tokens = {hit["token"] for hit in section_hits}

        missing_section_tokens = [
            token for token in required_section_tokens if token not in section_tokens
        ]
        if missing_section_tokens:
            section_violations[section_name] = missing_section_tokens

        duplicated_token = len(section_hits) != len(section_tokens)
        if duplicated_token:
            ambiguous_sections.append(section_name)

    if section_violations:
        result["section_style_violations"] = section_violations
        result["failure_reasons"].append("missing_section_style_tokens")

    if ambiguous_sections:
        result["ambiguous_style_sections"] = sorted(set(ambiguous_sections))
        result["failure_reasons"].append("ambiguous_style_mapping")

    invalid_values = []
    for hit in normalized_hits:
        if size_range and hit["font_size"] is not None and not _in_range(hit["font_size"], size_range):
            invalid_values.append(
                {
                    "section_name": hit["section_name"],
                    "token": hit["token"],
                    "field": "font_size",
                }
            )
        if height_range and hit["line_height"] is not None and not _in_range(
            hit["line_height"], height_range
        ):
            invalid_values.append(
                {
                    "section_name": hit["section_name"],
                    "token": hit["token"],
                    "field": "line_height",
                }
            )
        if allowed_weights and hit["font_weight"] is not None and hit["font_weight"] not in allowed_weights:
            invalid_values.append(
                {
                    "section_name": hit["section_name"],
                    "token": hit["token"],
                    "field": "font_weight",
                }
            )

    if invalid_values:
        result["invalid_style_values"] = invalid_values
        result["failure_reasons"].append("invalid_style_values")

    if not result["failure_reasons"]:
        result["proof_status"] = "passed"
        result["style_signal"] = "clear"
    else:
        result["style_signal"] = "detected"

    return result

"""Phase 3 Header-Footer-Watermark Proof Preview (v1).

Proof helper only.
No rendering changes.
No PDF writes.
No certification automation.
"""

_SCHEMA_VERSION = "button2.phase3.header_footer_watermark_proof.v1"


def _normalize_hfw_hits(hfw_hits):
    if not isinstance(hfw_hits, list):
        raise RuntimeError("invalid_hfw_hit_shape")

    valid_area_types = {"header", "footer", "watermark"}
    normalized = []
    for hit in hfw_hits:
        if not isinstance(hit, dict):
            raise RuntimeError("invalid_hfw_hit_shape")

        page_index = hit.get("page_index")
        area_type = hit.get("area_type")
        token = hit.get("token")
        marker_id = hit.get("marker_id")

        if not isinstance(page_index, int) or page_index < 0:
            raise RuntimeError("invalid_hfw_hit_shape")
        if not area_type or area_type not in valid_area_types:
            raise RuntimeError("invalid_hfw_hit_shape")
        if not token or not isinstance(token, str):
            raise RuntimeError("invalid_hfw_hit_shape")
        if marker_id is not None and not isinstance(marker_id, str):
            raise RuntimeError("invalid_hfw_hit_shape")

        normalized.append(
            {
                "page_index": page_index,
                "area_type": area_type,
                "token": token,
                "marker_id": marker_id,
            }
        )
    return normalized


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


def _normalize_page_list(pages, error_reason):
    if pages is None:
        return []
    if not isinstance(pages, (list, tuple, set)):
        raise RuntimeError(error_reason)
    output = []
    for page in pages:
        if not isinstance(page, int) or page < 0:
            raise RuntimeError(error_reason)
        output.append(page)
    return output


def run_header_footer_watermark_proof(
    hfw_hits,
    required_header_tokens,
    required_footer_tokens,
    required_watermark_tokens,
    forbidden_watermark_tokens,
    required_page_coverage,
    hfw_channel_available=True,
):
    """Run fail-closed header/footer/watermark proof from supplied evidence."""
    result = {
        "schema_version": _SCHEMA_VERSION,
        "proof_channel": "header_footer_watermark",
        "proof_status": "failed_closed",
        "hfw_signal": "unavailable",
        "failure_reasons": [],
        "discovered_hfw_hit_count": 0,
        "missing_required_header_tokens": [],
        "missing_required_footer_tokens": [],
        "missing_required_watermark_tokens": [],
        "forbidden_watermark_tokens_detected": [],
        "missing_required_page_coverage": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    if not hfw_channel_available:
        result["failure_reasons"].append("hfw_channel_unavailable")
        return result

    try:
        normalized_hits = _normalize_hfw_hits(hfw_hits)
        required_header = _normalize_string_list(required_header_tokens, "invalid_hfw_hit_shape")
        required_footer = _normalize_string_list(required_footer_tokens, "invalid_hfw_hit_shape")
        required_watermark = _normalize_string_list(required_watermark_tokens, "invalid_hfw_hit_shape")
        forbidden_watermark = _normalize_string_list(forbidden_watermark_tokens, "invalid_hfw_hit_shape")
        coverage_pages = _normalize_page_list(required_page_coverage, "invalid_hfw_hit_shape")
    except RuntimeError as exc:
        result["failure_reasons"].append(str(exc))
        return result

    result["discovered_hfw_hit_count"] = len(normalized_hits)

    by_area_type = {}
    by_page = {}
    for hit in normalized_hits:
        area_type = hit["area_type"]
        by_area_type.setdefault(area_type, []).append(hit)
        page_idx = hit["page_index"]
        by_page.setdefault(page_idx, []).append(hit)

    header_tokens = {hit["token"] for hit in by_area_type.get("header", [])}
    footer_tokens = {hit["token"] for hit in by_area_type.get("footer", [])}
    watermark_tokens = {hit["token"] for hit in by_area_type.get("watermark", [])}

    missing_header = [token for token in required_header if token not in header_tokens]
    if missing_header:
        result["missing_required_header_tokens"] = missing_header
        result["failure_reasons"].append("missing_required_header_tokens")

    missing_footer = [token for token in required_footer if token not in footer_tokens]
    if missing_footer:
        result["missing_required_footer_tokens"] = missing_footer
        result["failure_reasons"].append("missing_required_footer_tokens")

    missing_watermark = [token for token in required_watermark if token not in watermark_tokens]
    if missing_watermark:
        result["missing_required_watermark_tokens"] = missing_watermark
        result["failure_reasons"].append("missing_required_watermark_tokens")

    detected_forbidden = sorted(token for token in forbidden_watermark if token in watermark_tokens)
    if detected_forbidden:
        result["forbidden_watermark_tokens_detected"] = detected_forbidden
        result["failure_reasons"].append("forbidden_watermark_tokens_detected")

    pages_with_hfw = {page for page in by_page if by_page[page]}
    missing_coverage = sorted(page for page in coverage_pages if page not in pages_with_hfw)
    if missing_coverage:
        result["missing_required_page_coverage"] = missing_coverage
        result["failure_reasons"].append("required_page_coverage_missing")

    if not result["failure_reasons"]:
        result["proof_status"] = "passed"
        result["hfw_signal"] = "clear"
    else:
        result["hfw_signal"] = "detected"

    return result

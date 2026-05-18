"""Phase 3 Geometry Proof Preview (v1).

Proof helper only.
No rendering changes.
No PDF writes.
No certification automation.
"""

_SCHEMA_VERSION = "button2.phase3.geometry_proof.v1"


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _rectangles_overlap(first, second):
    return (
        first["x0"] < second["x1"]
        and first["x1"] > second["x0"]
        and first["y0"] < second["y1"]
        and first["y1"] > second["y0"]
    )


def _normalize_page_bounds(page_bounds):
    if not isinstance(page_bounds, dict) or not page_bounds:
        raise RuntimeError("missing_page_bounds")

    normalized = {}
    for page_index, bounds in page_bounds.items():
        if not isinstance(bounds, dict):
            raise RuntimeError("missing_page_bounds")
        width = bounds.get("width")
        height = bounds.get("height")
        if not _is_number(width) or not _is_number(height) or width <= 0 or height <= 0:
            raise RuntimeError("missing_page_bounds")
        normalized[int(page_index)] = {"width": float(width), "height": float(height)}
    return normalized


def _validate_geometry_blocks(geometry_blocks):
    if not isinstance(geometry_blocks, list):
        raise RuntimeError("invalid_region_geometry_shape")

    normalized = []
    for block in geometry_blocks:
        if not isinstance(block, dict):
            raise RuntimeError("invalid_region_geometry_shape")

        region_name = block.get("region_name")
        page_index = block.get("page_index")
        x0 = block.get("x0")
        y0 = block.get("y0")
        x1 = block.get("x1")
        y1 = block.get("y1")
        region_kind = block.get("region_kind", "text")

        if not region_name or not isinstance(region_name, str):
            raise RuntimeError("invalid_region_geometry_shape")
        if not isinstance(page_index, int):
            raise RuntimeError("invalid_region_geometry_shape")
        if not _is_number(x0) or not _is_number(y0) or not _is_number(x1) or not _is_number(y1):
            raise RuntimeError("invalid_region_geometry_shape")
        if not isinstance(region_kind, str):
            raise RuntimeError("invalid_region_geometry_shape")

        x0 = float(x0)
        y0 = float(y0)
        x1 = float(x1)
        y1 = float(y1)

        if x0 >= x1 or y0 >= y1:
            raise RuntimeError("invalid_region_geometry_shape")

        normalized.append(
            {
                "region_name": region_name,
                "page_index": page_index,
                "x0": x0,
                "y0": y0,
                "x1": x1,
                "y1": y1,
                "region_kind": region_kind,
            }
        )

    return normalized


def run_geometry_proof(
    geometry_blocks,
    page_bounds,
    required_regions=None,
    protected_non_overlap_pairs=None,
    required_on_page_regions=None,
    geometry_channel_available=True,
):
    """Run fail-closed geometry proof against safe geometry block inputs."""
    required_regions = list(required_regions or [])
    non_overlap_pairs = list(protected_non_overlap_pairs or [])
    required_on_page_regions = list(required_on_page_regions or [])

    result = {
        "schema_version": _SCHEMA_VERSION,
        "proof_channel": "geometry",
        "proof_status": "failed_closed",
        "geometry_signal": "unavailable",
        "failure_reasons": [],
        "extracted_region_count": 0,
        "missing_required_regions": required_regions.copy(),
        "off_page_required_regions": [],
        "protected_overlap_pairs_detected": [],
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    if not geometry_channel_available:
        result["failure_reasons"].append("geometry_library_unavailable")
        return result

    try:
        normalized_bounds = _normalize_page_bounds(page_bounds)
        normalized_blocks = _validate_geometry_blocks(geometry_blocks)
    except RuntimeError as exc:
        result["failure_reasons"].append(str(exc))
        return result

    result["extracted_region_count"] = len(normalized_blocks)
    by_name = {}
    for block in normalized_blocks:
        by_name.setdefault(block["region_name"], []).append(block)

    missing_regions = [name for name in required_regions if name not in by_name]
    result["missing_required_regions"] = missing_regions
    if missing_regions:
        result["failure_reasons"].append("missing_required_regions")

    off_page_regions = []
    for block in normalized_blocks:
        bounds = normalized_bounds.get(block["page_index"])
        if bounds is None:
            result["failure_reasons"].append("missing_page_bounds")
            result["off_page_required_regions"] = []
            result["geometry_signal"] = "unavailable"
            return result

        is_required_text_region = (
            block["region_name"] in required_on_page_regions and block["region_kind"] == "text"
        )
        if not is_required_text_region:
            continue

        if (
            block["x0"] < 0
            or block["y0"] < 0
            or block["x1"] > bounds["width"]
            or block["y1"] > bounds["height"]
        ):
            off_page_regions.append(block["region_name"])

    off_page_regions = sorted(set(off_page_regions))
    result["off_page_required_regions"] = off_page_regions
    if off_page_regions:
        result["failure_reasons"].append("off_page_required_regions")

    overlaps = []
    for left_name, right_name in non_overlap_pairs:
        left_blocks = by_name.get(left_name, [])
        right_blocks = by_name.get(right_name, [])
        for left in left_blocks:
            for right in right_blocks:
                if left["page_index"] != right["page_index"]:
                    continue
                if _rectangles_overlap(left, right):
                    overlaps.append([left_name, right_name, left["page_index"]])
                    break

    if overlaps:
        result["protected_overlap_pairs_detected"] = overlaps
        result["failure_reasons"].append("protected_overlap_detected")

    if not result["failure_reasons"]:
        result["proof_status"] = "passed"
        result["geometry_signal"] = "clear"
    else:
        result["geometry_signal"] = "detected"

    return result

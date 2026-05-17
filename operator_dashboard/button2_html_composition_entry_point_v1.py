# Button 2 HTML Composition Entry Point (v1)
# Slice: button2-html-composition-entry-point-preview-v1
#
# Purpose: Convert an approved report_context_preview dict into a safe, complete
#          HTML document string for render_button2_pdf().
#
# Governance: HTML composition only. No PDF rendering. No file writes.
#             No export, delivery, or Gate 2 bypass. preview_only=True always.

import html as _html
import json as _json
from operator_dashboard.button2_customer_pdf_typography_tokens_v1 import (
    generate_typography_css_stylesheet,
    get_typography_token,
)

_DESTINATION_MARKER = "button2_report_generation_preview"
_CONTEXT_KIND = "dossier_handoff_report_context_preview"

_BASE_FLAGS = {
    "preview_only": True,
    "pdf_generation_performed": False,
    "file_write_performed": False,
    "export_performed": False,
    "delivery_performed": False,
}

_HIERARCHY_LEVELS = {"H0", "H1", "H2", "Body", "Meta"}
_PAGE_BLOCK_ROLES = {
    "report_identity_block",
    "fighter_context_block",
    "matchup_signal_block",
    "analysis_block",
    "sources_calibration_block",
    "footer_metadata_block",
}
_CANONICAL_SECTION_ORDER = [
    "fighter_a_context",
    "fighter_b_context",
    "matchup_signal",
    "detailed_analysis",
    "sources_and_calibration",
]
_BREAK_POLICIES = {"keep_together", "allow_internal_break", "split_by_chunk"}
_OVERFLOW_REASONS = {"section_size", "chart_height", "widow_rule", "source_chunking"}
_FORBIDDEN_BREAK_BOUNDARIES = {
    "after_header_without_two_lines",
    "inside_chart_or_table",
    "between_claim_and_citation",
}
_WIDOW_ORPHAN_RULES = [
    "header_requires_two_following_lines",
    "no_single_list_item_orphan",
    "no_lonely_chart_under_one_inch_space",
]
_CHART_TYPES = {
    "scenario_tree",
    "method_pathway",
    "round_control",
    "risk_collapse_markers",
    "comparison_chart",
}
_ALLOWED_CHART_PLACEMENT_BLOCK_ROLES = {
    "matchup_signal_block",
    "analysis_block",
}
_DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES = {
    "report_identity_block",
    "footer_metadata_block",
}
_METHOD_TYPES = {"ko_tko", "submission", "decision", "attritional_breakdown"}
_RISK_TYPES = {
    "gas_tank_drop",
    "damage_accumulation",
    "defensive_breakdown",
    "pace_collapse",
}
_RISK_SEVERITIES = {"watch", "elevated", "critical"}
_ROUND_CONTROL_EXPECTATIONS = {"fighter_a", "fighter_b", "swing", "contested"}
_DOMINANCE_SIGNALS = {"low", "medium", "high"}
_STATUS_LABELS = {"DRAFT", "FINAL", "INTERNAL_REVIEW"}
_CONFIDENTIALITY_LABELS = {"PUBLIC", "CONFIDENTIAL", "STRICTLY_CONFIDENTIAL"}
_WATERMARK_TYPES = {"none", "draft", "confidential"}


def _default_section_block_metadata():
    return [
        {
            "block_id": "report_identity",
            "role": "report_identity_block",
            "break_policy": "keep_together",
            "can_split": False,
            "continuation_header_required": False,
            "min_lines_after_header": 2,
            "min_space_for_chart_in": 1.0,
            "approved_break_boundaries": ["between_h1_sections"],
        },
        {
            "block_id": "report_summary",
            "role": "analysis_block",
            "break_policy": "allow_internal_break",
            "can_split": True,
            "continuation_header_required": False,
            "min_lines_after_header": 2,
            "min_space_for_chart_in": 1.0,
            "approved_break_boundaries": ["between_h2_subsections"],
        },
        {
            "block_id": "source_traceability",
            "role": "sources_calibration_block",
            "break_policy": "split_by_chunk",
            "can_split": True,
            "continuation_header_required": True,
            "chunk_size": 10,
            "min_lines_after_header": 2,
            "min_space_for_chart_in": 1.0,
            "approved_break_boundaries": ["between_source_chunks"],
        },
        {
            "block_id": "meta_footer",
            "role": "footer_metadata_block",
            "break_policy": "keep_together",
            "can_split": False,
            "continuation_header_required": False,
            "min_lines_after_header": 2,
            "min_space_for_chart_in": 1.0,
            "approved_break_boundaries": ["never_split"],
        },
    ]


def _default_page_break_metadata():
    return [
        {
            "break_id": "pb_001",
            "trigger_block_id": "source_traceability",
            "trigger_section": "Source Traceability",
            "overflow_reason": "source_chunking",
            "previous_page_content_height_in": 8.0,
            "atomic_unit_preserved": True,
            "widow_orphan_rule_applied": False,
        }
    ]

def _default_header_footer_watermark_metadata():
    return {
        "header": {
            "report_title": "AI-RISA Premium Fight Report",
            "event_name": "Sample Event",
            "event_date": "2026-05-17",
            "status_label": "DRAFT",
            "confidentiality_label": "CONFIDENTIAL",
        },
        "footer": {
            "page_number_format": "Page {n} of {m}",
            "operator_label": "Operator",
            "generated_timestamp": "2026-05-17T12:00:00Z",
        },
        "watermark": {
            "watermark_enabled": True,
            "watermark_type": "draft",
            "watermark_text": "DRAFT",
            "watermark_opacity": 0.12,
            "watermark_angle": 45,
        },
    }

def _default_chart_and_scenario_metadata():
    return {
        "charts": [
            {
                "chart_id": "chart_scenario_tree_001",
                "chart_type": "scenario_tree",
                "title": "Primary Scenario Pathways",
                "intent": "Explain major tactical branches",
                "placement_block_id": "matchup_signal",
                "placement_block_role": "matchup_signal_block",
                "size_contract": {
                    "max_width_in": 6.5,
                    "max_height_in": 3.5,
                },
                "print_readability_contract": {
                    "min_label_pt": 9,
                    "min_stroke_pt": 1,
                    "min_contrast_ratio": 4.5,
                },
                "source_citations": ["SRC-001"],
            }
        ],
        "scenario_tree": {
            "root_node": "baseline",
            "branches": ["pace_advantage", "distance_control"],
            "terminal_nodes": ["late_finish", "decision_path"],
            "confidence_band": "58-66%",
        },
        "method_pathways": [
            {
                "pathway_id": "method_001",
                "method_type": "decision",
                "trigger_factors": ["jab_volume", "distance_management"],
                "counter_factors": ["pressure_pocket_entries"],
                "evidence_links": ["SRC-001"],
                "confidence_band": "52-60%",
            }
        ],
        "round_control": [
            {
                "window_id": "round_window_001",
                "round_range": "R1-R2",
                "control_expectation": "fighter_a",
                "dominance_signal": "medium",
                "evidence_links": ["SRC-001"],
            }
        ],
        "risk_collapse_markers": [
            {
                "marker_id": "risk_001",
                "risk_type": "damage_accumulation",
                "trigger_window": "R3-R5",
                "severity": "elevated",
                "mitigation_note": "Prioritize distance reset and clinch exits.",
                "evidence_links": ["SRC-001"],
            }
        ],
    }


def _validate_section_block_metadata(section_blocks):
    if section_blocks is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_section_block_metadata"],
            "forbidden_break_boundaries_detected": [],
        }
    if not isinstance(section_blocks, list):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["section_block_metadata_not_list"],
            "forbidden_break_boundaries_detected": [],
        }
    if not section_blocks:
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["section_block_metadata_empty"],
            "forbidden_break_boundaries_detected": [],
        }

    issues = []
    detected_forbidden_boundaries = []

    for index, block in enumerate(section_blocks):
        if not isinstance(block, dict):
            issues.append(f"section_block_{index}_not_dict")
            continue

        role = block.get("role")
        policy = block.get("break_policy")
        can_split = block.get("can_split")
        boundary = block.get("break_boundary")

        if role not in _PAGE_BLOCK_ROLES:
            issues.append(f"section_block_{index}_invalid_role")
        if policy not in _BREAK_POLICIES:
            issues.append(f"section_block_{index}_invalid_break_policy")
        if not isinstance(can_split, bool):
            issues.append(f"section_block_{index}_invalid_can_split")
        if boundary in _FORBIDDEN_BREAK_BOUNDARIES:
            issues.append(f"section_block_{index}_forbidden_break_boundary")
            detected_forbidden_boundaries.append(boundary)

        if policy == "keep_together" and can_split:
            issues.append(f"section_block_{index}_keep_together_can_split_conflict")

    return {
        "valid": len(issues) == 0,
        "status": "valid" if not issues else "invalid",
        "issues": issues,
        "forbidden_break_boundaries_detected": detected_forbidden_boundaries,
    }


def _validate_page_break_metadata(page_breaks, section_block_ids):
    if page_breaks is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_page_break_metadata"],
        }
    if not isinstance(page_breaks, list):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["page_break_metadata_not_list"],
        }
    if not page_breaks:
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["page_break_metadata_empty"],
        }

    issues = []
    for index, page_break in enumerate(page_breaks):
        if not isinstance(page_break, dict):
            issues.append(f"page_break_{index}_not_dict")
            continue

        trigger_block_id = page_break.get("trigger_block_id")
        overflow_reason = page_break.get("overflow_reason")
        atomic_preserved = page_break.get("atomic_unit_preserved")
        widow_orphan_applied = page_break.get("widow_orphan_rule_applied")
        boundary = page_break.get("break_boundary")

        if trigger_block_id not in section_block_ids:
            issues.append(f"page_break_{index}_unknown_trigger_block")
        if overflow_reason not in _OVERFLOW_REASONS:
            issues.append(f"page_break_{index}_invalid_overflow_reason")
        if not isinstance(atomic_preserved, bool):
            issues.append(f"page_break_{index}_invalid_atomic_unit_preserved")
        if not isinstance(widow_orphan_applied, bool):
            issues.append(f"page_break_{index}_invalid_widow_orphan_rule_applied")
        if boundary in _FORBIDDEN_BREAK_BOUNDARIES:
            issues.append(f"page_break_{index}_forbidden_break_boundary")

    return {
        "valid": len(issues) == 0,
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


def _validate_chart_and_scenario_metadata(chart_metadata):
    if chart_metadata is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_chart_metadata"],
        }
    if not isinstance(chart_metadata, dict):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["chart_metadata_not_dict"],
        }

    issues = []

    charts = chart_metadata.get("charts")
    if not isinstance(charts, list) or not charts:
        issues.append("charts_missing_or_empty")
    else:
        for index, chart in enumerate(charts):
            if not isinstance(chart, dict):
                issues.append(f"chart_{index}_not_dict")
                continue
            chart_type = chart.get("chart_type")
            placement_role = chart.get("placement_block_role")
            citations = chart.get("source_citations")
            size_contract = chart.get("size_contract")
            readability_contract = chart.get("print_readability_contract")

            if chart_type not in _CHART_TYPES:
                issues.append(f"chart_{index}_invalid_chart_type")
            if placement_role not in _ALLOWED_CHART_PLACEMENT_BLOCK_ROLES:
                issues.append(f"chart_{index}_invalid_placement_role")
            if placement_role in _DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES:
                issues.append(f"chart_{index}_disallowed_placement_role")
            if not isinstance(citations, list) or not citations:
                issues.append(f"chart_{index}_missing_source_citations")
            if not isinstance(size_contract, dict):
                issues.append(f"chart_{index}_invalid_size_contract")
            else:
                max_width = size_contract.get("max_width_in")
                max_height = size_contract.get("max_height_in")
                if not isinstance(max_width, (int, float)) or max_width > 6.5:
                    issues.append(f"chart_{index}_invalid_max_width")
                if not isinstance(max_height, (int, float)) or max_height > 4.0:
                    issues.append(f"chart_{index}_invalid_max_height")
            if not isinstance(readability_contract, dict):
                issues.append(f"chart_{index}_invalid_readability_contract")
            else:
                min_label_pt = readability_contract.get("min_label_pt")
                if not isinstance(min_label_pt, (int, float)) or min_label_pt < 9:
                    issues.append(f"chart_{index}_invalid_min_label_pt")

    scenario_tree = chart_metadata.get("scenario_tree")
    if not isinstance(scenario_tree, dict):
        issues.append("scenario_tree_missing_or_invalid")
    else:
        if not scenario_tree.get("root_node"):
            issues.append("scenario_tree_missing_root_node")
        if not isinstance(scenario_tree.get("branches"), list) or not scenario_tree.get("branches"):
            issues.append("scenario_tree_missing_branches")
        if not isinstance(scenario_tree.get("terminal_nodes"), list) or not scenario_tree.get("terminal_nodes"):
            issues.append("scenario_tree_missing_terminal_nodes")
        if not scenario_tree.get("confidence_band"):
            issues.append("scenario_tree_missing_confidence_band")

    method_pathways = chart_metadata.get("method_pathways")
    if not isinstance(method_pathways, list) or not method_pathways:
        issues.append("method_pathways_missing_or_empty")
    else:
        for index, pathway in enumerate(method_pathways):
            if not isinstance(pathway, dict):
                issues.append(f"method_pathway_{index}_not_dict")
                continue
            if pathway.get("method_type") not in _METHOD_TYPES:
                issues.append(f"method_pathway_{index}_invalid_method_type")
            if not isinstance(pathway.get("trigger_factors"), list) or not pathway.get("trigger_factors"):
                issues.append(f"method_pathway_{index}_missing_trigger_factors")
            if not isinstance(pathway.get("counter_factors"), list) or not pathway.get("counter_factors"):
                issues.append(f"method_pathway_{index}_missing_counter_factors")
            if not isinstance(pathway.get("evidence_links"), list) or not pathway.get("evidence_links"):
                issues.append(f"method_pathway_{index}_missing_evidence_links")
            if not pathway.get("confidence_band"):
                issues.append(f"method_pathway_{index}_missing_confidence_band")

    round_control = chart_metadata.get("round_control")
    if not isinstance(round_control, list) or not round_control:
        issues.append("round_control_missing_or_empty")
    else:
        for index, window in enumerate(round_control):
            if not isinstance(window, dict):
                issues.append(f"round_control_{index}_not_dict")
                continue
            if not window.get("round_range"):
                issues.append(f"round_control_{index}_missing_round_range")
            if window.get("control_expectation") not in _ROUND_CONTROL_EXPECTATIONS:
                issues.append(f"round_control_{index}_invalid_control_expectation")
            if window.get("dominance_signal") not in _DOMINANCE_SIGNALS:
                issues.append(f"round_control_{index}_invalid_dominance_signal")
            if not isinstance(window.get("evidence_links"), list) or not window.get("evidence_links"):
                issues.append(f"round_control_{index}_missing_evidence_links")

    risk_markers = chart_metadata.get("risk_collapse_markers")
    if not isinstance(risk_markers, list) or not risk_markers:
        issues.append("risk_markers_missing_or_empty")
    else:
        for index, marker in enumerate(risk_markers):
            if not isinstance(marker, dict):
                issues.append(f"risk_marker_{index}_not_dict")
                continue
            if marker.get("risk_type") not in _RISK_TYPES:
                issues.append(f"risk_marker_{index}_invalid_risk_type")
            if marker.get("severity") not in _RISK_SEVERITIES:
                issues.append(f"risk_marker_{index}_invalid_severity")
            if marker.get("severity") == "critical" and not marker.get("mitigation_note"):
                issues.append(f"risk_marker_{index}_missing_mitigation_note")
            if not isinstance(marker.get("evidence_links"), list) or not marker.get("evidence_links"):
                issues.append(f"risk_marker_{index}_missing_evidence_links")

    return {
        "valid": len(issues) == 0,
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


def _chart_and_scenario_payload(report_context_preview):
    """Build and validate deterministic chart/scenario metadata payload."""
    chart_metadata = report_context_preview.get("chart_and_scenario_metadata")
    chart_metadata_provided = "chart_and_scenario_metadata" in report_context_preview
    if not chart_metadata_provided:
        chart_metadata = _default_chart_and_scenario_metadata()

    validation = _validate_chart_and_scenario_metadata(chart_metadata)

    return {
        "schema_version": "button2.chart_and_scenario.v1",
        "validation_status": validation["status"],
        "validation_issues": validation["issues"],
        "allowed_chart_types": sorted(_CHART_TYPES),
        "allowed_placement_block_roles": sorted(_ALLOWED_CHART_PLACEMENT_BLOCK_ROLES),
        "disallowed_placement_block_roles": sorted(_DISALLOWED_CHART_PLACEMENT_BLOCK_ROLES),
        "chart_and_scenario": chart_metadata,
    }


def _page_breaks_and_section_blocks_payload(report_context_preview):
    """Build and validate deterministic page-break/section-block metadata payload."""
    section_blocks = report_context_preview.get("section_block_metadata")
    page_breaks = report_context_preview.get("page_break_metadata")

    section_blocks_provided = "section_block_metadata" in report_context_preview
    page_breaks_provided = "page_break_metadata" in report_context_preview

    if not section_blocks_provided:
        section_blocks = _default_section_block_metadata()
    if not page_breaks_provided:
        page_breaks = _default_page_break_metadata()

    section_block_validation = _validate_section_block_metadata(section_blocks)
    section_block_ids = []
    if isinstance(section_blocks, list):
        section_block_ids = [
            block.get("block_id")
            for block in section_blocks
            if isinstance(block, dict)
        ]
    page_break_validation = _validate_page_break_metadata(page_breaks, section_block_ids)

    combined_issues = (
        section_block_validation["issues"] + page_break_validation["issues"]
    )
    status = "valid"
    if section_block_validation["status"] == "missing" or page_break_validation["status"] == "missing":
        status = "missing"
    elif combined_issues:
        status = "invalid"

    return {
        "schema_version": "button2.page_breaks_and_blocks.v1",
        "validation_status": status,
        "validation_issues": combined_issues,
        "forbidden_break_boundaries": sorted(_FORBIDDEN_BREAK_BOUNDARIES),
        "forbidden_break_boundaries_detected": section_block_validation[
            "forbidden_break_boundaries_detected"
        ],
        "widow_orphan_rules": _WIDOW_ORPHAN_RULES,
        "section_blocks": section_blocks,
        "page_breaks": page_breaks,
    }


def _canonical_hierarchy_blocks():
    """Return canonical hierarchy blocks and levels for metadata emission."""
    return [
        {
            "block_id": "report_identity",
            "role": "report_identity_block",
            "level": "H0",
            "title": "AI-RISA Premium Fight Report",
            "sequence": 0,
            "children": [
                {
                    "level": "H2",
                    "title": "Report Summary",
                    "sequence": 1,
                }
            ],
        },
        {
            "block_id": "report_summary",
            "role": "analysis_block",
            "level": "H1",
            "title": "Report Summary",
            "sequence": 1,
            "children": [],
        },
        {
            "block_id": "source_traceability",
            "role": "sources_calibration_block",
            "level": "H1",
            "title": "Source Traceability",
            "sequence": 2,
            "children": [
                {
                    "level": "H2",
                    "title": "Source Citations",
                    "sequence": 1,
                }
            ],
        },
        {
            "block_id": "meta_footer",
            "role": "footer_metadata_block",
            "level": "Meta",
            "title": "Metadata Footer",
            "sequence": 3,
            "children": [
                {
                    "level": "Body",
                    "title": "QA and provenance rows",
                    "sequence": 1,
                }
            ],
        },
    ]


def _validate_hierarchy_markers(hierarchy_markers):
    """Validate optional hierarchy markers. Missing/invalid markers are not certified."""
    if hierarchy_markers is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_hierarchy_markers"],
        }

    if not isinstance(hierarchy_markers, list):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["hierarchy_markers_not_list"],
        }

    if not hierarchy_markers:
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["hierarchy_markers_empty"],
        }

    issues = []
    for index, marker in enumerate(hierarchy_markers):
        if not isinstance(marker, dict):
            issues.append(f"marker_{index}_not_dict")
            continue
        level = marker.get("level")
        role = marker.get("role")
        # Backward compatibility: legacy markers used block/order keys only.
        if level is None and role is None and "block" in marker:
            continue
        if level not in _HIERARCHY_LEVELS:
            issues.append(f"marker_{index}_invalid_level")
        if role is not None and role not in _PAGE_BLOCK_ROLES:
            issues.append(f"marker_{index}_invalid_role")

    if issues:
        return {
            "valid": False,
            "status": "invalid",
            "issues": issues,
        }

    return {
        "valid": True,
        "status": "valid",
        "issues": [],
    }


def _hierarchy_metadata_payload(report_context_preview):
    """Build a deterministic hierarchy payload for HTML embedding."""
    validation = _validate_hierarchy_markers(
        report_context_preview.get("hierarchy_markers")
    )

    return {
        "schema_version": "button2.page_hierarchy.v1",
        "report_id": _esc(report_context_preview.get("fight_id"), "unknown_fight"),
        "hierarchy_validation_status": validation["status"],
        "hierarchy_validation_issues": validation["issues"],
        "required_levels": ["H0", "H1", "H2", "Body", "Meta"],
        "canonical_section_order": _CANONICAL_SECTION_ORDER,
        "blocks": _canonical_hierarchy_blocks(),
    }


def _esc(value, fallback=""):
    """Escape a value for safe insertion into HTML text."""
    if value is None:
        return _html.escape(str(fallback))
    text = str(value).strip()
    if not text:
        return _html.escape(str(fallback))
    return _html.escape(text)


def _validate_header_footer_watermark_metadata(hfw_metadata):
    """Validate header/footer/watermark metadata. Invalid metadata is not certified."""
    if hfw_metadata is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_header_footer_watermark_metadata"],
        }
    if not isinstance(hfw_metadata, dict):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["header_footer_watermark_metadata_not_dict"],
        }

    issues = []

    header = hfw_metadata.get("header")
    if not isinstance(header, dict):
        issues.append("header_missing_or_invalid")
    else:
        if not header.get("report_title"):
            issues.append("header_missing_report_title")
        status_label = header.get("status_label")
        if status_label is not None and status_label not in _STATUS_LABELS:
            issues.append("header_invalid_status_label")
        confidentiality_label = header.get("confidentiality_label")
        if confidentiality_label is not None and confidentiality_label not in _CONFIDENTIALITY_LABELS:
            issues.append("header_invalid_confidentiality_label")

    footer = hfw_metadata.get("footer")
    if not isinstance(footer, dict):
        issues.append("footer_missing_or_invalid")
    else:
        page_num_format = footer.get("page_number_format")
        if not page_num_format:
            issues.append("footer_missing_page_number_format")
        elif "{n}" not in page_num_format or "{m}" not in page_num_format:
            issues.append("footer_page_number_format_missing_tokens")

    watermark = hfw_metadata.get("watermark")
    if not isinstance(watermark, dict):
        issues.append("watermark_missing_or_invalid")
    else:
        if not isinstance(watermark.get("watermark_enabled"), bool):
            issues.append("watermark_invalid_watermark_enabled")
        watermark_type = watermark.get("watermark_type")
        if watermark_type not in _WATERMARK_TYPES:
            issues.append("watermark_invalid_watermark_type")

        if watermark_type != "none":
            if not watermark.get("watermark_text"):
                issues.append("watermark_missing_text_for_non_none_type")

        opacity = watermark.get("watermark_opacity")
        if opacity is not None:
            if not isinstance(opacity, (int, float)) or opacity < 0.05 or opacity > 0.20:
                issues.append("watermark_invalid_opacity")

    return {
        "valid": len(issues) == 0,
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


def _header_footer_watermark_payload(report_context_preview):
    """Build and validate deterministic header/footer/watermark metadata payload."""
    hfw_metadata = report_context_preview.get("header_footer_watermark_metadata")
    hfw_provided = "header_footer_watermark_metadata" in report_context_preview

    if not hfw_provided:
        hfw_metadata = _default_header_footer_watermark_metadata()

    validation = _validate_header_footer_watermark_metadata(hfw_metadata)

    return {
        "schema_version": "button2.header_footer_watermark.v1",
        "validation_status": validation["status"],
        "validation_issues": validation["issues"],
        "allowed_status_labels": sorted(_STATUS_LABELS),
        "allowed_confidentiality_labels": sorted(_CONFIDENTIALITY_LABELS),
        "allowed_watermark_types": sorted(_WATERMARK_TYPES),
        "header_footer_watermark": hfw_metadata,
    }


def _proof_label(proof_value):
    """Render a proof field value as a safe escaped label string."""
    if isinstance(proof_value, dict):
        return _esc(proof_value.get("status", "unknown"))
    return _esc(proof_value, "unavailable")


def _source_traceability_html(items):
    """Render source traceability items as escaped <li> elements."""
    if not isinstance(items, list) or not items:
        return "<li>No source traceability data.</li>"
    parts = []
    for item in items:
        if not isinstance(item, dict):
            continue
        src_id = _esc(item.get("id", ""))
        src_type = _esc(item.get("type", ""))
        src_date = _esc(item.get("date", ""))
        parts.append(f"<li>{src_id} &mdash; {src_type} &mdash; {src_date}</li>")
    return "\n    ".join(parts) if parts else "<li>No source traceability data.</li>"


_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI-RISA Premium Report</title>
  <style>
    /* Base typography and layout */
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      margin: 0.75in;
      color: #111111;
      line-height: 1.5;
    }}

    /* Typography tokens stylesheet */
    {typography_css_stylesheet}

    /* Structural and semantic styling (layout only, no typography changes) */
    h1   {{ margin-bottom: 0.5em; }}
    h2   {{ margin-top: 1.5em; border-bottom: 1px solid #cccccc; }}
    ul   {{ margin: 0.5em 0; padding-left: 1.5em; }}
    pre  {{ white-space: pre-wrap; word-break: break-word; }}
    .meta-footer {{ margin-top: 2em; border-top: 1px solid #eeeeee; padding-top: 0.5em; }}
    .qa-row {{ margin: 0.2em 0; }}
    .hierarchy-metadata {{ display: none; }}
    .page-breaks-metadata {{ display: none; }}
    .chart-scenario-metadata {{ display: none; }}
    .header-footer-watermark-metadata {{ display: none; }}
  </style>
</head>
<body>
    <h1 class="typography-report-title" data-hierarchy-level="H0" data-page-block-role="report_identity_block" data-break-policy="keep_together">AI-RISA Premium Fight Report</h1>

    <section class="page-block-summary" data-page-block-role="analysis_block" data-break-policy="allow_internal_break" data-can-split="true" data-widow-orphan-rule="header_requires_two_following_lines">
        <h2 class="typography-section-header-l1" data-hierarchy-level="H1">Report Summary</h2>
        <div class="hierarchy-marker" data-hierarchy-level="H2" data-hierarchy-title="Executive Summary"></div>
        <pre class="typography-body-secondary" data-hierarchy-level="Body">{handoff_summary_preview}</pre>
    </section>

    <section class="page-block-sources" data-page-block-role="sources_calibration_block" data-break-policy="split_by_chunk" data-can-split="true" data-chunk-size="10" data-widow-orphan-rule="no_single_list_item_orphan">
        <h2 class="typography-section-header-l1" data-hierarchy-level="H1">Source Traceability</h2>
        <div class="hierarchy-marker" data-hierarchy-level="H2" data-hierarchy-title="Source Citations"></div>
        <ul class="typography-list-item" data-hierarchy-level="Body">
            {source_traceability_items}
        </ul>
    </section>

    <div class="meta-footer typography-page-metadata" data-hierarchy-level="Meta" data-page-block-role="footer_metadata_block" data-break-policy="keep_together" data-can-split="false">
    <div class="qa-row">Source context: {source_context_kind}</div>
    <div class="qa-row">Ingest mode: {source_ingest_mode}</div>
    <div class="qa-row">Overlap proof: {overlap_proof_label}</div>
    <div class="qa-row">Off-page text proof: {off_page_text_proof_label}</div>
    <div class="qa-row">Visual certification: {visual_certification_status}</div>
    <div class="qa-row">Hierarchy validation: {hierarchy_validation_status}</div>
    <div class="qa-row">Page-break metadata validation: {page_breaks_metadata_validation_status}</div>
    <div class="qa-row">Chart/scenario metadata validation: {chart_metadata_validation_status}</div>
    <div class="qa-row">Header/footer/watermark metadata validation: {hfw_metadata_validation_status}</div>
  </div>

    <section
        id="button2-hierarchy-metadata"
        class="hierarchy-metadata"
        data-hierarchy-schema-version="{hierarchy_schema_version}"
        data-hierarchy-validation-status="{hierarchy_validation_status}"
        data-canonical-section-order="{canonical_section_order}"
    >
        <pre data-hierarchy-level="Meta">{hierarchy_metadata_json}</pre>
    </section>

    <section
        id="button2-page-breaks-metadata"
        class="page-breaks-metadata"
        data-page-breaks-schema-version="{page_breaks_schema_version}"
        data-page-breaks-validation-status="{page_breaks_metadata_validation_status}"
        data-page-breaks-policy-set="{page_breaks_policy_set}"
    >
        <pre data-hierarchy-level="Meta">{page_breaks_metadata_json}</pre>
    </section>

    <section
        id="button2-chart-scenario-metadata"
        class="chart-scenario-metadata"
        data-chart-scenario-schema-version="{chart_schema_version}"
        data-chart-scenario-validation-status="{chart_metadata_validation_status}"
    >
        <pre data-hierarchy-level="Meta">{chart_metadata_json}</pre>
    </section>

    <section
        id="button2-header-footer-watermark-metadata"
        class="header-footer-watermark-metadata"
        data-header-footer-watermark-schema-version="{hfw_schema_version}"
        data-header-footer-watermark-validation-status="{hfw_metadata_validation_status}"
    >
        <pre data-hierarchy-level="Meta">{hfw_metadata_json}</pre>
    </section>
</body>
</html>"""


def _fail(error_code):
    return {
        "ok": False,
        "error": error_code,
        "html_content": None,
        "html_composition_performed": False,
        **_BASE_FLAGS,
    }


def build_button2_report_html(report_context_preview):
    """Convert an approved report_context_preview dict into a full HTML document.

    Accepts the dict produced by build_button2_dossier_handoff_report_context_preview().
    Returns a dict with html_content (str) on success, or an error dict on failure.

    No PDF rendering. No file writes. No delivery. preview_only=True always.

    Args:
        report_context_preview (dict): The report_context_preview dict.

    Returns:
        dict:
            ok (bool)
            error (str|None)
            html_content (str|None)
            html_composition_performed (bool)
            preview_only (bool)       — always True
            pdf_generation_performed (bool) — always False
            file_write_performed (bool)     — always False
            export_performed (bool)         — always False
            delivery_performed (bool)       — always False
    """
    if not isinstance(report_context_preview, dict):
        return _fail("invalid_input_type")

    dest = str(report_context_preview.get("destination_marker", "")).strip()
    if dest != _DESTINATION_MARKER:
        return _fail("invalid_destination_marker")

    ctx_kind = str(report_context_preview.get("report_context_kind", "")).strip()
    if ctx_kind != _CONTEXT_KIND:
        return _fail("invalid_report_context_kind")

    summary_raw = report_context_preview.get("handoff_summary_preview", "")
    if not isinstance(summary_raw, str) or not summary_raw.strip():
        return _fail("missing_summary_content")

    # Summary is pre-escaped by upstream _safe_text(); trust it directly.
    # All other fields are escaped at composition time.

    hierarchy_payload = _hierarchy_metadata_payload(report_context_preview)
    hierarchy_valid = hierarchy_payload["hierarchy_validation_status"] == "valid"
    page_breaks_payload = _page_breaks_and_section_blocks_payload(report_context_preview)
    page_breaks_valid = page_breaks_payload["validation_status"] == "valid"
    chart_payload = _chart_and_scenario_payload(report_context_preview)
    chart_valid = chart_payload["validation_status"] == "valid"
    hfw_payload = _header_footer_watermark_payload(report_context_preview)
    hfw_valid = hfw_payload["validation_status"] == "valid"
    visual_certification_value = report_context_preview.get(
        "visual_certification_status", "not_certified"
    )
    # Fail closed for hierarchy, page-break, chart, or hfw contract issues.
    if not hierarchy_valid or not page_breaks_valid or not chart_valid or not hfw_valid:
        visual_certification_value = "not_certified"
    
    # Generate typography CSS stylesheet from locked tokens
    typography_css = generate_typography_css_stylesheet()
    
    html_content = _HTML_TEMPLATE.format(
        typography_css_stylesheet=typography_css,
        handoff_summary_preview=summary_raw,
        source_traceability_items=_source_traceability_html(
            report_context_preview.get("source_traceability", [])
        ),
        source_context_kind=_esc(
            report_context_preview.get("source_context_kind"), "unknown"
        ),
        source_ingest_mode=_esc(
            report_context_preview.get("source_ingest_mode"), "unknown"
        ),
        overlap_proof_label=_proof_label(
            report_context_preview.get("overlap_proof", "unavailable")
        ),
        off_page_text_proof_label=_proof_label(
            report_context_preview.get("off_page_text_proof", "unavailable")
        ),
        visual_certification_status=_esc(visual_certification_value, "not_certified"),
        hierarchy_validation_status=_esc(
            hierarchy_payload["hierarchy_validation_status"], "invalid"
        ),
        hierarchy_schema_version=_esc(
            hierarchy_payload["schema_version"], "button2.page_hierarchy.v1"
        ),
        canonical_section_order=_esc(
            "|".join(hierarchy_payload["canonical_section_order"]),
            "",
        ),
        hierarchy_metadata_json=_esc(
            _json.dumps(hierarchy_payload, separators=(",", ":"), sort_keys=True),
            "{}",
        ),
        page_breaks_metadata_validation_status=_esc(
            page_breaks_payload["validation_status"], "invalid"
        ),
        page_breaks_schema_version=_esc(
            page_breaks_payload["schema_version"], "button2.page_breaks_and_blocks.v1"
        ),
        page_breaks_policy_set=_esc(
            "|".join(sorted(_BREAK_POLICIES)),
            "",
        ),
        page_breaks_metadata_json=_esc(
            _json.dumps(page_breaks_payload, separators=(",", ":"), sort_keys=True),
            "{}",
        ),
        chart_metadata_validation_status=_esc(
            chart_payload["validation_status"], "invalid"
        ),
        chart_schema_version=_esc(
            chart_payload["schema_version"], "button2.chart_and_scenario.v1"
        ),
        chart_metadata_json=_esc(
            _json.dumps(chart_payload, separators=(",", ":"), sort_keys=True),
            "{}",
        ),
        hfw_metadata_validation_status=_esc(
            hfw_payload["validation_status"], "invalid"
        ),
        hfw_schema_version=_esc(
            hfw_payload["schema_version"], "button2.header_footer_watermark.v1"
        ),
        hfw_metadata_json=_esc(
            _json.dumps(hfw_payload, separators=(",", ":"), sort_keys=True),
            "{}",
        ),
    )

    return {
        "ok": True,
        "error": None,
        "html_content": html_content,
        "html_composition_performed": True,
        **_BASE_FLAGS,
    }

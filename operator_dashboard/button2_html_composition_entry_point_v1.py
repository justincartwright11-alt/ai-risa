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
_SOURCE_TYPES = {"official", "research", "operator"}
_SOURCE_CLASSES = {"tier_a", "tier_b", "tier_c"}
_CONFIDENCE_LEVELS = {"high", "medium", "low", "uncertain"}
_CITATION_COMPLETENESS = {"complete", "partial", "minimal"}
_VERIFICATION_STATUS = {"verified", "unverified", "contradicted"}
_STATUS_LABELS = {"DRAFT", "FINAL", "INTERNAL_REVIEW"}
_CONFIDENTIALITY_LABELS = {"PUBLIC", "CONFIDENTIAL", "STRICTLY_CONFIDENTIAL"}
_WATERMARK_TYPES = {"none", "draft", "confidential"}
_ROLLUP_STATUS = {"all_valid", "mixed", "all_invalid"}
_VISUAL_CONFIDENCE_LEVELS = {"high", "medium", "low", "unknown"}
_CERTIFICATION_READINESS = {"ready", "needs_review", "not_ready"}
_LAYER_VALIDATION_STATUS = {"valid", "invalid", "missing"}
_PROOF_STATUS = {"present", "missing", "invalid"}


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

def _default_source_traceability_metadata():
    return {
        "schema_version": "button2.source_traceability.v1",
        "validation_status": "missing",
        "validation_issues": ["missing_source_traceability_metadata"],
        "total_sources": 0,
        "official_sources_count": 0,
        "research_sources_count": 0,
        "operator_sources_count": 0,
        "average_confidence_level": "uncertain",
        "corroboration_coverage": 0.0,
        "sources": [],
        "lineage_graph": {},
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


def _validate_source_traceability_metadata(src_metadata):
    """Validate source traceability metadata. Invalid metadata is not certified."""
    if src_metadata is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_source_traceability_metadata"],
        }
    if not isinstance(src_metadata, dict):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["source_traceability_metadata_not_dict"],
        }

    issues = []

    # Validate sources array
    sources = src_metadata.get("sources")
    if not isinstance(sources, list):
        issues.append("sources_not_list")
    else:
        for idx, src in enumerate(sources):
            if not isinstance(src, dict):
                issues.append(f"source_{idx}_not_dict")
                continue

            src_type = src.get("source_type")
            if src_type not in _SOURCE_TYPES:
                issues.append(f"source_{idx}_invalid_source_type")

            src_class = src.get("source_class")
            if src_class not in _SOURCE_CLASSES:
                issues.append(f"source_{idx}_invalid_source_class")

            confidence = src.get("confidence_level")
            if confidence not in _CONFIDENCE_LEVELS:
                issues.append(f"source_{idx}_invalid_confidence_level")

            completeness = src.get("citation_completeness")
            if completeness not in _CITATION_COMPLETENESS:
                issues.append(f"source_{idx}_invalid_citation_completeness")

            verification = src.get("verification_status")
            if verification not in _VERIFICATION_STATUS:
                issues.append(f"source_{idx}_invalid_verification_status")

            if not src.get("source_url"):
                issues.append(f"source_{idx}_missing_source_url")

            if not src.get("source_date"):
                issues.append(f"source_{idx}_missing_source_date")

    # Validate lineage_graph
    lineage_graph = src_metadata.get("lineage_graph")
    if not isinstance(lineage_graph, dict):
        issues.append("lineage_graph_not_dict")

    # Validate total_sources is non-negative
    total_sources = src_metadata.get("total_sources", 0)
    if not isinstance(total_sources, int) or total_sources < 0:
        issues.append("invalid_total_sources")

    # Validate corroboration_coverage is between 0 and 1
    corroboration = src_metadata.get("corroboration_coverage", 0.0)
    if not isinstance(corroboration, (int, float)) or corroboration < 0.0 or corroboration > 1.0:
        issues.append("invalid_corroboration_coverage")

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


def _source_traceability_payload(report_context_preview):
    """Build and validate deterministic source traceability metadata payload."""
    src_metadata = report_context_preview.get("source_traceability_metadata")
    src_provided = "source_traceability_metadata" in report_context_preview

    if not src_provided:
        src_metadata = _default_source_traceability_metadata()

    validation = _validate_source_traceability_metadata(src_metadata)

    return {
        "schema_version": "button2.source_traceability.v1",
        "validation_status": validation["status"],
        "validation_issues": validation["issues"],
        "allowed_source_types": sorted(_SOURCE_TYPES),
        "allowed_source_classes": sorted(_SOURCE_CLASSES),
        "allowed_confidence_levels": sorted(_CONFIDENCE_LEVELS),
        "allowed_citation_completeness": sorted(_CITATION_COMPLETENESS),
        "allowed_verification_status": sorted(_VERIFICATION_STATUS),
        "source_traceability": src_metadata,
    }


def _default_visual_qa_rollup_metadata():
    """Return deterministic default visual QA rollup metadata when not provided."""
    import datetime
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "button2.visual_qa_rollup.v1",
        "rollup_generated_timestamp": timestamp,
        "rollup_status": "all_invalid",  # All layers missing = all_invalid status
        "layer_validation_summary": {
            "layer_1_typography": {
                "schema_version": "button2.page_typography_tokens.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "layer_2_hierarchy": {
                "schema_version": "button2.page_hierarchy.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "layer_3_page_breaks": {
                "schema_version": "button2.page_breaks_and_blocks.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "layer_4_charts": {
                "schema_version": "button2.chart_and_scenario.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "layer_5_header_footer_watermark": {
                "schema_version": "button2.header_footer_watermark.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "layer_6_source_traceability": {
                "schema_version": "button2.source_traceability.v1",
                "validation_status": "missing",
                "validation_issues_count": 0,
                "required_for_certification": True,
            },
            "proof_overlap": {
                "proof_kind": "overlap_proof",
                "proof_status": "missing",
                "required_for_certification": True,
            },
            "proof_off_page_text": {
                "proof_kind": "off_page_text_proof",
                "proof_status": "missing",
                "required_for_certification": True,
            },
        },
        "visual_qa_indicators": {
            "overall_visual_completeness": 0.0,
            "overall_visual_confidence": "unknown",
            "certification_readiness": "not_ready",
            "valid_layers_count": 0,
            "invalid_layers_count": 0,
            "missing_layers_count": 8,
            "layers_requiring_attention": [
                "layer_1_typography",
                "layer_2_hierarchy",
                "layer_3_page_breaks",
                "layer_4_charts",
                "layer_5_header_footer_watermark",
                "layer_6_source_traceability",
                "proof_overlap",
                "proof_off_page_text",
            ],
        },
        "recommended_review_focus": [
            {
                "priority": 1,
                "category": "all_layers",
                "issue": "missing_visual_qa_rollup_metadata",
                "recommendation": "Provide visual QA rollup metadata",
            }
        ],
    }


def _validate_visual_qa_rollup_metadata(rollup_metadata):
    """Validate visual QA rollup metadata. Invalid metadata is not certified."""
    if rollup_metadata is None:
        return {
            "valid": False,
            "status": "missing",
            "issues": ["missing_visual_qa_rollup_metadata"],
        }
    if not isinstance(rollup_metadata, dict):
        return {
            "valid": False,
            "status": "invalid",
            "issues": ["visual_qa_rollup_metadata_not_dict"],
        }

    issues = []

    # Validate rollup_status
    rollup_status = rollup_metadata.get("rollup_status")
    if rollup_status not in _ROLLUP_STATUS:
        issues.append("invalid_rollup_status")

    # Validate layer_validation_summary
    layer_summary = rollup_metadata.get("layer_validation_summary")
    if not isinstance(layer_summary, dict):
        issues.append("layer_validation_summary_not_dict")
    else:
        expected_layers = {
            "layer_1_typography",
            "layer_2_hierarchy",
            "layer_3_page_breaks",
            "layer_4_charts",
            "layer_5_header_footer_watermark",
            "layer_6_source_traceability",
            "proof_overlap",
            "proof_off_page_text",
        }
        provided_layers = set(layer_summary.keys())
        if provided_layers != expected_layers:
            issues.append("layer_validation_summary_missing_or_extra_layers")

        for layer_name, layer_info in layer_summary.items():
            if not isinstance(layer_info, dict):
                issues.append(f"{layer_name}_not_dict")
                continue

            if "proof" in layer_name:
                # Proof structure
                proof_status = layer_info.get("proof_status")
                if proof_status not in _PROOF_STATUS:
                    issues.append(f"{layer_name}_invalid_proof_status")
            else:
                # Layer structure
                validation_status = layer_info.get("validation_status")
                if validation_status not in _LAYER_VALIDATION_STATUS:
                    issues.append(f"{layer_name}_invalid_validation_status")
                issues_count = layer_info.get("validation_issues_count")
                if not isinstance(issues_count, int) or issues_count < 0:
                    issues.append(f"{layer_name}_invalid_validation_issues_count")

    # Validate visual_qa_indicators
    indicators = rollup_metadata.get("visual_qa_indicators")
    if not isinstance(indicators, dict):
        issues.append("visual_qa_indicators_not_dict")
    else:
        completeness = indicators.get("overall_visual_completeness")
        if not isinstance(completeness, (int, float)) or completeness < 0.0 or completeness > 1.0:
            issues.append("invalid_overall_visual_completeness")

        confidence = indicators.get("overall_visual_confidence")
        if confidence not in _VISUAL_CONFIDENCE_LEVELS:
            issues.append("invalid_overall_visual_confidence")

        readiness = indicators.get("certification_readiness")
        if readiness not in _CERTIFICATION_READINESS:
            issues.append("invalid_certification_readiness")

        valid_count = indicators.get("valid_layers_count")
        if not isinstance(valid_count, int) or valid_count < 0 or valid_count > 8:
            issues.append("invalid_valid_layers_count")

        invalid_count = indicators.get("invalid_layers_count")
        if not isinstance(invalid_count, int) or invalid_count < 0 or invalid_count > 8:
            issues.append("invalid_invalid_layers_count")

        missing_count = indicators.get("missing_layers_count")
        if not isinstance(missing_count, int) or missing_count < 0 or missing_count > 8:
            issues.append("invalid_missing_layers_count")

        layers_attention = indicators.get("layers_requiring_attention")
        if not isinstance(layers_attention, list):
            issues.append("layers_requiring_attention_not_list")

    # Validate recommended_review_focus
    focus = rollup_metadata.get("recommended_review_focus")
    if not isinstance(focus, list):
        issues.append("recommended_review_focus_not_list")
    else:
        for idx, item in enumerate(focus):
            if not isinstance(item, dict):
                issues.append(f"review_focus_{idx}_not_dict")
                continue
            if not isinstance(item.get("priority"), int) or item.get("priority") < 1:
                issues.append(f"review_focus_{idx}_invalid_priority")
            if not item.get("category"):
                issues.append(f"review_focus_{idx}_missing_category")
            if not item.get("issue"):
                issues.append(f"review_focus_{idx}_missing_issue")
            if not item.get("recommendation"):
                issues.append(f"review_focus_{idx}_missing_recommendation")

    return {
        "valid": len(issues) == 0,
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


def _visual_qa_rollup_payload(report_context_preview, layer_payloads):
    """Build and validate visual QA rollup payload from all layer validations and proofs.
    
    Args:
        report_context_preview (dict): The report context
        layer_payloads (dict): Dict containing all layer payloads with keys:
            - hierarchy_payload
            - page_breaks_payload
            - chart_payload
            - hfw_payload
            - src_payload
    
    Returns:
        dict: Rollup payload with schema, validation status, and metadata
    """
    import datetime
    
    # Extract layer validation statuses
    layer_1_status = layer_payloads.get("hierarchy_payload", {}).get("hierarchy_validation_status", "missing")
    layer_2_status = layer_payloads.get("page_breaks_payload", {}).get("validation_status", "missing")
    layer_3_status = layer_payloads.get("chart_payload", {}).get("validation_status", "missing")
    layer_4_status = layer_payloads.get("hfw_payload", {}).get("validation_status", "missing")
    layer_5_status = layer_payloads.get("src_payload", {}).get("validation_status", "missing")
    
    # Extract proof statuses from report context
    overlap_proof = report_context_preview.get("overlap_proof", {})
    off_page_text_proof = report_context_preview.get("off_page_text_proof", {})
    
    overlap_proof_status = "present" if isinstance(overlap_proof, dict) and overlap_proof.get("status") == "present" else (
        "invalid" if isinstance(overlap_proof, dict) and overlap_proof.get("status") == "invalid" else "missing"
    )
    off_page_proof_status = "present" if isinstance(off_page_text_proof, dict) and off_page_text_proof.get("status") == "present" else (
        "invalid" if isinstance(off_page_text_proof, dict) and off_page_text_proof.get("status") == "invalid" else "missing"
    )
    
    # Count valid/invalid/missing
    all_statuses = [layer_1_status, layer_2_status, layer_3_status, layer_4_status, layer_5_status, overlap_proof_status, off_page_proof_status]
    # Note: Layer 6 (source traceability) - we need to get its status
    src_payload = layer_payloads.get("src_payload", {})
    layer_6_status = src_payload.get("validation_status", "missing")
    all_statuses.append(layer_6_status)
    
    valid_count = sum(1 for s in all_statuses if s == "valid" or s == "present")
    invalid_count = sum(1 for s in all_statuses if s == "invalid")
    missing_count = sum(1 for s in all_statuses if s == "missing")
    
    # Calculate completeness (0.0-1.0)
    completeness = valid_count / 8.0
    
    # Determine confidence level based on completeness
    if completeness == 1.0:
        confidence = "high"
    elif completeness >= 0.75:
        confidence = "medium"
    elif completeness >= 0.50:
        confidence = "low"
    else:
        confidence = "unknown"
    
    # Determine certification readiness
    if invalid_count == 0 and missing_count == 0:
        readiness = "ready"
    elif invalid_count > 0 and invalid_count < 3:
        readiness = "needs_review"
    else:
        readiness = "not_ready"
    
    # Determine overall rollup status
    if valid_count == 8:
        rollup_status = "all_valid"
    elif valid_count == 0:
        rollup_status = "all_invalid"
    else:
        rollup_status = "mixed"
    
    # Build layers requiring attention
    layers_attention = []
    layer_map = [
        ("layer_1_typography", layer_1_status),
        ("layer_2_hierarchy", layer_2_status),
        ("layer_3_page_breaks", layer_3_status),
        ("layer_4_charts", layer_4_status),
        ("layer_5_header_footer_watermark", layer_4_status),
        ("layer_6_source_traceability", layer_6_status),
        ("proof_overlap", overlap_proof_status),
        ("proof_off_page_text", off_page_proof_status),
    ]
    
    for layer_name, status in layer_map:
        if status != "valid" and status != "present":
            layers_attention.append(layer_name)
    
    # Build recommended review focus
    recommended_focus = []
    priority = 1
    
    # Priority 1: Missing critical proofs
    if overlap_proof_status == "missing":
        recommended_focus.append({
            "priority": priority,
            "category": "proof_overlap",
            "issue": "missing_overlap_proof",
            "recommendation": "Provide overlap proof for certification",
        })
        priority += 1
    
    if off_page_proof_status == "missing":
        recommended_focus.append({
            "priority": priority,
            "category": "proof_off_page_text",
            "issue": "missing_off_page_text_proof",
            "recommendation": "Provide off-page text proof for certification",
        })
        priority += 1
    
    # Priority 2: Missing layer metadata
    for layer_name, status in layer_map:
        if status == "missing" and "proof" not in layer_name:
            recommended_focus.append({
                "priority": priority,
                "category": layer_name,
                "issue": f"missing_{layer_name}_metadata",
                "recommendation": f"Provide {layer_name} metadata before certification",
            })
            priority += 1
    
    # Priority 3: Invalid layer metadata
    for layer_name, status in layer_map:
        if status == "invalid":
            recommended_focus.append({
                "priority": priority,
                "category": layer_name,
                "issue": f"invalid_{layer_name}_metadata",
                "recommendation": f"Review and fix {layer_name} metadata issues",
            })
            priority += 1
    
    # If no issues, add ready message
    if not recommended_focus:
        recommended_focus.append({
            "priority": 1,
            "category": "all_layers",
            "issue": "all_valid",
            "recommendation": "All visual QA metadata is valid and complete",
        })
    
    # Build layer validation summary
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    layer_validation_summary = {
        "layer_1_typography": {
            "schema_version": "button2.page_typography_tokens.v1",
            "validation_status": layer_1_status,
            "validation_issues_count": 0,
            "required_for_certification": True,
        },
        "layer_2_hierarchy": {
            "schema_version": "button2.page_hierarchy.v1",
            "validation_status": layer_2_status,
            "validation_issues_count": len(layer_payloads.get("page_breaks_payload", {}).get("validation_issues", [])),
            "required_for_certification": True,
        },
        "layer_3_page_breaks": {
            "schema_version": "button2.page_breaks_and_blocks.v1",
            "validation_status": layer_3_status,
            "validation_issues_count": len(layer_payloads.get("page_breaks_payload", {}).get("validation_issues", [])),
            "required_for_certification": True,
        },
        "layer_4_charts": {
            "schema_version": "button2.chart_and_scenario.v1",
            "validation_status": layer_3_status,
            "validation_issues_count": len(layer_payloads.get("chart_payload", {}).get("validation_issues", [])),
            "required_for_certification": True,
        },
        "layer_5_header_footer_watermark": {
            "schema_version": "button2.header_footer_watermark.v1",
            "validation_status": layer_4_status,
            "validation_issues_count": len(layer_payloads.get("hfw_payload", {}).get("validation_issues", [])),
            "required_for_certification": True,
        },
        "layer_6_source_traceability": {
            "schema_version": "button2.source_traceability.v1",
            "validation_status": layer_6_status,
            "validation_issues_count": len(layer_payloads.get("src_payload", {}).get("validation_issues", [])),
            "required_for_certification": True,
        },
        "proof_overlap": {
            "proof_kind": "overlap_proof",
            "proof_status": overlap_proof_status,
            "required_for_certification": True,
        },
        "proof_off_page_text": {
            "proof_kind": "off_page_text_proof",
            "proof_status": off_page_proof_status,
            "required_for_certification": True,
        },
    }
    
    rollup_metadata = {
        "schema_version": "button2.visual_qa_rollup.v1",
        "rollup_generated_timestamp": timestamp,
        "rollup_status": rollup_status,
        "layer_validation_summary": layer_validation_summary,
        "visual_qa_indicators": {
            "overall_visual_completeness": completeness,
            "overall_visual_confidence": confidence,
            "certification_readiness": readiness,
            "valid_layers_count": valid_count,
            "invalid_layers_count": invalid_count,
            "missing_layers_count": missing_count,
            "layers_requiring_attention": layers_attention,
        },
        "recommended_review_focus": recommended_focus,
    }
    
    validation = _validate_visual_qa_rollup_metadata(rollup_metadata)
    
    return {
        "schema_version": "button2.visual_qa_rollup.v1",
        "validation_status": validation["status"],
        "validation_issues": validation["issues"],
        "allowed_rollup_statuses": sorted(_ROLLUP_STATUS),
        "allowed_confidence_levels": sorted(_VISUAL_CONFIDENCE_LEVELS),
        "allowed_readiness_levels": sorted(_CERTIFICATION_READINESS),
        "visual_qa_rollup": rollup_metadata,
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
            max-width: 7.2in;
    }}

    /* Typography tokens stylesheet */
    {typography_css_stylesheet}

    /* Structural and semantic styling (layout only, no typography changes) */
    h1   {{ margin-bottom: 0.65em; letter-spacing: 0.01em; }}
    h2   {{ margin-top: 1.35em; margin-bottom: 0.45em; border-bottom: 1px solid #cccccc; padding-bottom: 0.15em; }}
    ul   {{ margin: 0.5em 0; padding-left: 1.5em; }}
    pre  {{ white-space: pre-wrap; word-break: break-word; margin-top: 0.4em; }}
    .page-block-summary, .page-block-sources {{ margin-top: 0.9em; }}
    .typography-body-secondary {{ line-height: 1.62; }}
    .typography-list-item li {{ margin-bottom: 0.32em; }}

        /* Phase 4 page-break/layout polish (CSS only, metadata-driven) */
        section[data-break-policy="keep_together"],
        div[data-break-policy="keep_together"] {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        section[data-break-policy="allow_internal_break"],
        section[data-break-policy="split_by_chunk"] {{
            page-break-inside: auto;
            break-inside: auto;
        }}
        h2[data-hierarchy-level="H1"] {{
            page-break-after: avoid;
            break-after: avoid-page;
            orphans: 3;
            widows: 3;
        }}
        .typography-body-secondary,
        .typography-list-item li,
        .qa-row {{
            orphans: 3;
            widows: 3;
        }}
        .typography-list-item li {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
    .meta-footer {{ margin-top: 2em; border-top: 1px solid #eeeeee; padding-top: 0.5em; }}
    .qa-row {{ margin: 0.2em 0; }}
    .hierarchy-metadata {{ display: none; }}
    .page-breaks-metadata {{ display: none; }}
    .chart-scenario-metadata {{ display: none; }}
    .header-footer-watermark-metadata {{ display: none; }}
    .source-traceability-metadata {{ display: none; }}
    .visual-qa-rollup-metadata {{ display: none; }}
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
    <div class="qa-row">Source traceability metadata validation: {src_metadata_validation_status}</div>
    <div class="qa-row">Visual QA rollup status: {rollup_status} | Certification readiness: {certification_readiness} | Completeness: {visual_completeness}</div>
    <div class="qa-row">Valid layers: {valid_layers_count}/8 | Invalid: {invalid_layers_count} | Missing: {missing_layers_count}</div>
    <div class="qa-row">Overall visual confidence: {overall_visual_confidence}</div>
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

    <section
        id="button2-source-traceability-metadata"
        class="source-traceability-metadata"
        data-source-traceability-schema-version="{src_schema_version}"
        data-source-traceability-validation-status="{src_metadata_validation_status}"
    >
        <pre data-hierarchy-level="Meta">{src_metadata_json}</pre>
    </section>

    <section
        id="button2-visual-qa-rollup-metadata"
        class="visual-qa-rollup-metadata"
        data-visual-qa-rollup-schema-version="{rollup_schema_version}"
        data-visual-qa-rollup-status="{rollup_status}"
        data-certification-readiness="{certification_readiness}"
        data-visual-completeness="{visual_completeness}"
        data-visual-confidence="{overall_visual_confidence}"
    >
        <pre data-hierarchy-level="Meta">{rollup_metadata_json}</pre>
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
    src_payload = _source_traceability_payload(report_context_preview)
    src_valid = src_payload["validation_status"] == "valid"
    
    # Generate visual QA rollup payload
    rollup_payload = _visual_qa_rollup_payload(
        report_context_preview,
        {
            "hierarchy_payload": hierarchy_payload,
            "page_breaks_payload": page_breaks_payload,
            "chart_payload": chart_payload,
            "hfw_payload": hfw_payload,
            "src_payload": src_payload,
        }
    )
    rollup_valid = rollup_payload["validation_status"] == "valid"
    
    visual_certification_value = report_context_preview.get(
        "visual_certification_status", "not_certified"
    )
    # Fail closed for hierarchy, page-break, chart, hfw, source traceability, or rollup contract issues.
    if not hierarchy_valid or not page_breaks_valid or not chart_valid or not hfw_valid or not src_valid or not rollup_valid:
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
        src_metadata_validation_status=_esc(
            src_payload["validation_status"], "invalid"
        ),
        src_schema_version=_esc(
            src_payload["schema_version"], "button2.source_traceability.v1"
        ),
        src_metadata_json=_esc(
            _json.dumps(src_payload, separators=(",", ":"), sort_keys=True),
            "{}",
        ),
        rollup_schema_version=_esc(
            rollup_payload["schema_version"], "button2.visual_qa_rollup.v1"
        ),
        rollup_status=_esc(
            rollup_payload.get("visual_qa_rollup", {}).get("rollup_status", "unknown"),
            "unknown"
        ),
        certification_readiness=_esc(
            rollup_payload.get("visual_qa_rollup", {}).get("visual_qa_indicators", {}).get("certification_readiness", "unknown"),
            "unknown"
        ),
        visual_completeness=_esc(
            f"{rollup_payload.get('visual_qa_rollup', {}).get('visual_qa_indicators', {}).get('overall_visual_completeness', 0.0) * 100:.0f}%",
            "0%"
        ),
        valid_layers_count=_esc(
            str(rollup_payload.get("visual_qa_rollup", {}).get("visual_qa_indicators", {}).get("valid_layers_count", 0)),
            "0"
        ),
        invalid_layers_count=_esc(
            str(rollup_payload.get("visual_qa_rollup", {}).get("visual_qa_indicators", {}).get("invalid_layers_count", 0)),
            "0"
        ),
        missing_layers_count=_esc(
            str(rollup_payload.get("visual_qa_rollup", {}).get("visual_qa_indicators", {}).get("missing_layers_count", 0)),
            "0"
        ),
        overall_visual_confidence=_esc(
            rollup_payload.get("visual_qa_rollup", {}).get("visual_qa_indicators", {}).get("overall_visual_confidence", "unknown"),
            "unknown"
        ),
        rollup_metadata_json=_esc(
            _json.dumps(rollup_payload, separators=(",", ":"), sort_keys=True),
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

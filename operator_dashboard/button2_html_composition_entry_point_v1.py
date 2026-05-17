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
  </style>
</head>
<body>
    <h1 class="typography-report-title" data-hierarchy-level="H0" data-page-block-role="report_identity_block">AI-RISA Premium Fight Report</h1>

    <section class="page-block-summary" data-page-block-role="analysis_block">
        <h2 class="typography-section-header-l1" data-hierarchy-level="H1">Report Summary</h2>
        <div class="hierarchy-marker" data-hierarchy-level="H2" data-hierarchy-title="Executive Summary"></div>
        <pre class="typography-body-secondary" data-hierarchy-level="Body">{handoff_summary_preview}</pre>
    </section>

    <section class="page-block-sources" data-page-block-role="sources_calibration_block">
        <h2 class="typography-section-header-l1" data-hierarchy-level="H1">Source Traceability</h2>
        <div class="hierarchy-marker" data-hierarchy-level="H2" data-hierarchy-title="Source Citations"></div>
        <ul class="typography-list-item" data-hierarchy-level="Body">
            {source_traceability_items}
        </ul>
    </section>

    <div class="meta-footer typography-page-metadata" data-hierarchy-level="Meta" data-page-block-role="footer_metadata_block">
    <div class="qa-row">Source context: {source_context_kind}</div>
    <div class="qa-row">Ingest mode: {source_ingest_mode}</div>
    <div class="qa-row">Overlap proof: {overlap_proof_label}</div>
    <div class="qa-row">Off-page text proof: {off_page_text_proof_label}</div>
    <div class="qa-row">Visual certification: {visual_certification_status}</div>
        <div class="qa-row">Hierarchy validation: {hierarchy_validation_status}</div>
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
    visual_certification_value = report_context_preview.get(
        "visual_certification_status", "not_certified"
    )
    # Fail closed for hierarchy contract issues: downgrade to not_certified.
    if not hierarchy_valid:
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
    )

    return {
        "ok": True,
        "error": None,
        "html_content": html_content,
        "html_composition_performed": True,
        **_BASE_FLAGS,
    }

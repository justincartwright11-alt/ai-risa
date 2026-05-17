# Button 2 HTML Composition Entry Point (v1)
# Slice: button2-html-composition-entry-point-preview-v1
#
# Purpose: Convert an approved report_context_preview dict into a safe, complete
#          HTML document string for render_button2_pdf().
#
# Governance: HTML composition only. No PDF rendering. No file writes.
#             No export, delivery, or Gate 2 bypass. preview_only=True always.

import html as _html

_DESTINATION_MARKER = "button2_report_generation_preview"
_CONTEXT_KIND = "dossier_handoff_report_context_preview"

_BASE_FLAGS = {
    "preview_only": True,
    "pdf_generation_performed": False,
    "file_write_performed": False,
    "export_performed": False,
    "delivery_performed": False,
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
    body {{ font-family: sans-serif; font-size: 11pt; margin: 2cm; color: #111; }}
    h1   {{ font-size: 16pt; margin-bottom: 0.5em; }}
    h2   {{ font-size: 13pt; margin-top: 1.5em; margin-bottom: 0.3em; border-bottom: 1px solid #ccc; }}
    pre  {{ font-size: 9pt; white-space: pre-wrap; word-break: break-word; }}
    ul   {{ margin: 0.5em 0; padding-left: 1.5em; }}
    .meta-footer {{ font-size: 8pt; color: #888; margin-top: 2em; border-top: 1px solid #eee; padding-top: 0.5em; }}
    .qa-row {{ margin: 0.2em 0; }}
  </style>
</head>
<body>
  <h1>AI-RISA Premium Fight Report</h1>

  <h2>Report Summary</h2>
  <pre>{handoff_summary_preview}</pre>

  <h2>Source Traceability</h2>
  <ul>
    {source_traceability_items}
  </ul>

  <div class="meta-footer">
    <div class="qa-row">Source context: {source_context_kind}</div>
    <div class="qa-row">Ingest mode: {source_ingest_mode}</div>
    <div class="qa-row">Overlap proof: {overlap_proof_label}</div>
    <div class="qa-row">Off-page text proof: {off_page_text_proof_label}</div>
    <div class="qa-row">Visual certification: {visual_certification_status}</div>
  </div>
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
    html_content = _HTML_TEMPLATE.format(
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
        visual_certification_status=_esc(
            report_context_preview.get("visual_certification_status"), "not_certified"
        ),
    )

    return {
        "ok": True,
        "error": None,
        "html_content": html_content,
        "html_composition_performed": True,
        **_BASE_FLAGS,
    }

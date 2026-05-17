# Button 2 PDF Render Gate (v1)
# Slice: button2-visual-intelligence-renderer-geometry-extractor-integration-preview-v1
#
# Purpose: Single Button 2 render call site. Provides non-invasive geometry
#          extraction side-channel, guarded off by default.
#
# Governance: No customer PDF change. No dashboard change. No delivery behavior change.
#             Instrumentation only. Guard defaults to False (disabled).
#             Visual QA extraction never runs in customer delivery mode.

import os

from operator_dashboard.button2_visual_intelligence_weasyprint_geometry_extractor_preview_v1 import (
    extract_weasyprint_page_geometry,
)


def _visual_qa_enabled():
    """Return True only when BUTTON2_VISUAL_QA env var equals '1'.

    Defaults to False — visual QA extraction never runs in customer delivery mode
    unless explicitly enabled for QA purposes.
    """
    return os.environ.get("BUTTON2_VISUAL_QA", "0").strip() == "1"


def render_button2_pdf(html_content):
    """Render Button 2 HTML to PDF bytes using WeasyPrint.

    Non-invasive geometry side-channel:
        After HTML(...).render() and before document.write_pdf(), if
        _visual_qa_enabled() is True, extract page block geometry and return it.

        The extracted data is NOT embedded in the PDF output — it is returned
        alongside pdf_bytes for QA proof chain use only.

    Fail-closed:
        Any exception during extraction → geometry_data=None.
        The proof chain will surface 'unavailable' for both proofs.

    Args:
        html_content (str): HTML string to render.

    Returns:
        dict:
            pdf_bytes     (bytes)      — rendered PDF output
            geometry_data (dict|None)  — extracted block geometry, or None
    """
    import weasyprint as _wp

    # ── Render (layout-neutral — side-channel is read-only) ──────────────────
    document = _wp.HTML(string=html_content).render()

    # ── Non-invasive geometry side-channel ───────────────────────────────────
    geometry_data = None
    if _visual_qa_enabled():
        try:
            geometry_data = extract_weasyprint_page_geometry(document)
        except Exception:
            geometry_data = None  # fail closed — proof stays 'unavailable'

    # ── Write PDF (unchanged from single-call equivalent) ────────────────────
    pdf_bytes = document.write_pdf()

    return {
        "pdf_bytes": pdf_bytes,
        "geometry_data": geometry_data,
    }

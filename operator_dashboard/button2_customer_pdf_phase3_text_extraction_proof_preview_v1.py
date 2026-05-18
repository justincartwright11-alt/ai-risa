"""
Phase 3 Text Extraction Proof Preview (v1)

In-memory proof helper only.
No PDF generation changes.
No file writes.
No renderer/dashboard/delivery/certification behavior changes.
"""

from io import BytesIO

_SCHEMA_VERSION = "button2.phase3.text_extraction_proof.v1"


def _extract_text_with_pypdf(pdf_bytes):
    """Extract text from PDF bytes using pypdf.

    Raises RuntimeError with deterministic reason when unavailable or failed.
    """
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("extraction_library_unavailable") from exc

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        chunks = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    except Exception as exc:
        raise RuntimeError("extraction_error") from exc


def run_text_extraction_proof(
    pdf_bytes,
    required_text_markers=None,
    required_section_markers=None,
):
    """Run fail-closed text extraction proof against required markers."""
    text_markers = list(required_text_markers or [])
    section_markers = list(required_section_markers or [])

    result = {
        "schema_version": _SCHEMA_VERSION,
        "proof_channel": "text_extraction",
        "proof_status": "failed_closed",
        "failure_reasons": [],
        "extracted_text_length": 0,
        "matched_text_markers": [],
        "missing_text_markers": text_markers.copy(),
        "matched_section_markers": [],
        "missing_section_markers": section_markers.copy(),
        "pdf_generation_performed": False,
        "file_write_performed": False,
        "renderer_behavior_changed": False,
        "dashboard_behavior_changed": False,
        "delivery_workflow_changed": False,
        "certification_automation_changed": False,
    }

    if not isinstance(pdf_bytes, (bytes, bytearray)) or not pdf_bytes:
        result["failure_reasons"].append("missing_pdf_bytes")
        return result

    try:
        extracted_text = _extract_text_with_pypdf(bytes(pdf_bytes))
    except RuntimeError as exc:
        result["failure_reasons"].append(str(exc))
        return result

    result["extracted_text_length"] = len(extracted_text)

    missing_text = [m for m in text_markers if m not in extracted_text]
    missing_sections = [m for m in section_markers if m not in extracted_text]

    result["missing_text_markers"] = missing_text
    result["missing_section_markers"] = missing_sections
    result["matched_text_markers"] = [m for m in text_markers if m not in missing_text]
    result["matched_section_markers"] = [m for m in section_markers if m not in missing_sections]

    if missing_text:
        result["failure_reasons"].append("missing_required_text_markers")
    if missing_sections:
        result["failure_reasons"].append("missing_required_section_markers")

    if not result["failure_reasons"]:
        result["proof_status"] = "passed"

    return result

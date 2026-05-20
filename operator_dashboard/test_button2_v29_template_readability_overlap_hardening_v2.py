from __future__ import annotations

import io
import os

from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


def _preview(
    fighter_a: str = "Ryan Curtis",
    fighter_b: str = "Adam Borics",
    event_name: str = "Bellator 298",
    event_date: str = "2026-07-19",
    source_url: str = "https://www.bellator.com/event/298",
):
    return {
        "selected_matchup": {
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "event_name": event_name,
            "event_date": event_date,
            "promotion": "Bellator",
            "source_url": source_url,
            "source_type": "official",
        },
        "handoff_summary_preview": "Selected matchup handoff summary.",
        "source_traceability": [
            {
                "source_url": source_url,
                "source_type": "official",
                "source_date": event_date,
            }
        ],
    }


def _render_pdf_bytes_to_text(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages), len(reader.pages)


def test_dense_page_layout_metadata_records_safe_bounds(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})

    page_bounds = safety.get("page_bounds", {})
    assert set(("6", "14", "16", "17")).issubset(page_bounds)

    for page_key in ("6", "14", "16", "17"):
        page_info = page_bounds.get(page_key, {})
        assert page_info.get("overlap_detected") is False
        assert float(page_info.get("min_font_size", 0.0)) >= 8.0

    footer_pages = safety.get("footer_safe_zone_pages", {})
    for page_key in ("6", "16", "17"):
        assert footer_pages.get(page_key, {}).get("safe") is True

    assert safety.get("visual_layout_safe") is True


def test_dense_page_layout_still_passes_strict_gate(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    preview = _preview()
    out = renderer.render_button2_template_pack_asset_pdf(preview)

    pdf_path = tmp_path / "ryan_curtis_vs_adam_borics_bellator_298_premium_readability_hardening_v2.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    text, page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])

    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {
            "output_path": str(pdf_path),
            "output_filename": pdf_path.name,
            "report_id": "ryan_curtis_adam_borics_bellator_298",
        },
        text,
        page_count,
        out.get("layout_safety"),
    )

    assert ok is True
    assert not any(value.startswith("readability_") for value in violations)


def test_page_bounds_overlap_metadata_fails_closed(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    preview = _preview()
    out = renderer.render_button2_template_pack_asset_pdf(preview)
    pdf_path = tmp_path / "ryan_curtis_vs_adam_borics_bellator_298_premium_readability_hardening_fail_closed.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    text, page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])

    layout_safety = dict(out.get("layout_safety", {}))
    layout_safety["page_bounds"] = dict(layout_safety.get("page_bounds", {}))
    layout_safety["page_bounds"]["6"] = dict(layout_safety["page_bounds"].get("6", {}), overlap_detected=True)

    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {
            "output_path": str(pdf_path),
            "output_filename": pdf_path.name,
            "report_id": "ryan_curtis_adam_borics_bellator_298",
        },
        text,
        page_count,
        layout_safety,
    )

    assert ok is False
    assert "visual_defect_page_6_overlap_detected" in violations
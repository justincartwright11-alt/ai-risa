from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from pypdf import PdfReader

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


@pytest.fixture
def client(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


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


def _queue_rows():
    rows = app_module.load_button2_queue_readonly()
    assert rows, "canonical queue must exist for Button 2 tests"
    return rows


def _pick_ids(count=2):
    return [row["matchup_id"] for row in _queue_rows()[:count]]


def _render_pdf_bytes_to_text(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages), len(reader.pages)


def _success_text_for_selected(selected: dict):
    fighter_a = selected["fighter_a"]
    fighter_b = selected["fighter_b"]
    event_name = selected["event_name"]
    event_date = selected["event_date"]
    source_url = selected["source_url"]
    return (
        f"{fighter_a} vs {fighter_b}\n"
        f"Event: {event_name}\n"
        f"Event Date: {event_date}\n"
        f"Source: {source_url}\n"
        + "\n".join(marker.upper() for marker in app_module._BUTTON2_REQUIRED_PREMIUM_MARKERS)
        + "\n"
        + "\n".join(f"{a.upper()} {b.upper()}" for a, b in app_module._BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES)
        + "\n"
        + "\n".join(marker.upper() for marker in app_module._BUTTON2_REQUIRED_V29_LAYOUT_MARKERS)
        + "\n"
    )


def test_tactical_edge_page_uses_readable_font_sizes():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    assert safety.get("readable_min_font_passed") is True
    assert safety.get("tactical_edge_overlap_passed") is True


def test_tactical_edge_page_has_no_footer_or_section_strip_collision():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    page_info = safety.get("footer_safe_zone_pages", {}).get("6", {})
    assert page_info.get("safe") is True
    assert float(page_info.get("card_min_y", 0.0)) >= float(page_info.get("safe_zone_y", 0.0))


def test_round_outlook_panel_is_centered():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    assert safety.get("round_outlook_centered_passed") is True


def test_scorecard_scenario_uses_readable_commentary_font():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    assert safety.get("scorecard_readability_passed") is True
    assert safety.get("readable_min_font_passed") is True


def test_scorecard_scenario_footer_safe_zone_preserved():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    page_info = out.get("layout_safety", {}).get("footer_safe_zone_pages", {}).get("16", {})
    assert page_info.get("safe") is True


def test_stoppage_windows_uses_readable_mechanism_font():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    assert safety.get("stoppage_readability_passed") is True
    assert safety.get("readable_min_font_passed") is True


def test_stoppage_windows_footer_safe_zone_preserved():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    page_info = out.get("layout_safety", {}).get("footer_safe_zone_pages", {}).get("17", {})
    assert page_info.get("safe") is True


def test_bottom_risk_corner_strip_above_footer_safe_zone():
    out = renderer.render_button2_template_pack_asset_pdf(_preview())
    safety = out.get("layout_safety", {})
    footer_pages = safety.get("footer_safe_zone_pages", {})
    for key in ("6", "16", "17"):
        assert footer_pages.get(key, {}).get("safe") is True


def test_visual_gate_blocks_customer_ready_on_readability_overlap_failure(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    row = _queue_rows()[0]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [row])

    out_path = tmp_path / "readability_gate_failure.pdf"
    out_path.write_bytes(b"%PDF-1.4\n")

    monkeypatch.setattr(
        app_module,
        "generate_button2_report_render_gate_integration",
        lambda _payload: {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": "readability_gate_failure.pdf",
            "report_id": "readability_gate_failure",
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "readable_min_font_passed": False,
                "footer_safe_zone_passed": False,
                "tactical_edge_overlap_passed": False,
                "scorecard_readability_passed": False,
                "stoppage_readability_passed": False,
                "round_outlook_centered_passed": False,
                "footer_safe_zone_pages": {"6": {"safe": False}, "16": {"safe": False}, "17": {"safe": False}},
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        },
    )
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda _p: ("coverage text", 24))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client_app:
        resp = client_app.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"]]})
        data = resp.get_json()

    assert data["results"][0]["customer_ready"] is False
    assert data["results"][0]["visual_gate_status"] == "v29_readability_overlap_failed"
    assert any(violation.startswith("readability_") for violation in data["results"][0].get("strict_quality_gate_violations", []))


def test_sample_bleed_gate_still_passes(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    preview = _preview()
    out = renderer.render_button2_template_pack_asset_pdf(preview)
    pdf_path = tmp_path / "ryan_curtis_vs_adam_borics_bellator_298_premium_check.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    text, page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "ryan_curtis_adam_borics_bellator_298"},
        text,
        page_count,
        out.get("layout_safety"),
    )
    assert ok is True
    assert not any(value.startswith("template_sample_bleed_present:") for value in violations)


def test_event_binding_gate_still_passes(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    preview = _preview()
    out = renderer.render_button2_template_pack_asset_pdf(preview)
    pdf_path = tmp_path / "ryan_curtis_vs_adam_borics_bellator_298_event_binding_check.pdf"
    pdf_path.write_bytes(out["pdf_bytes"])
    text, page_count = _render_pdf_bytes_to_text(out["pdf_bytes"])
    ok, violations = app_module._selected_matchup_passes_strict_pdf_quality_gate(
        preview["selected_matchup"],
        {"output_path": str(pdf_path), "output_filename": pdf_path.name, "report_id": "ryan_curtis_adam_borics_bellator_298"},
        text,
        page_count,
        out.get("layout_safety"),
    )
    assert ok is True
    assert "event_binding_incomplete_no_event_name" not in violations
    assert "event_binding_incomplete_no_event_date" not in violations


def test_bulk_generation_contract_still_passes(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    rows = _queue_rows()[:2]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: rows)
    text_by_path = {}

    def _generate(payload):
        out_path = tmp_path / payload["output_filename_override"]
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        out_path.write_bytes(b"%PDF-1.4\n")
        text_by_path[str(out_path)] = _success_text_for_selected(selected)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": payload["output_filename_override"],
            "report_id": Path(payload["output_filename_override"]).stem,
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "readable_min_font_passed": True,
                "footer_safe_zone_passed": True,
                "tactical_edge_overlap_passed": True,
                "scorecard_readability_passed": True,
                "stoppage_readability_passed": True,
                "round_outlook_centered_passed": True,
                "footer_safe_zone_pages": {"6": {"safe": True}, "16": {"safe": True}, "17": {"safe": True}},
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))
    monkeypatch.setattr(app_module, "_selected_matchup_passes_strict_pdf_quality_gate", lambda *args, **kwargs: (True, []))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client_app:
        resp = client_app.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": _pick_ids(2)})
        data = resp.get_json()

    assert resp.status_code == 200
    assert data["requested_count"] == 2
    assert data["generated_count"] == 2
    assert len(data.get("output_paths", [])) == 2


def test_governance_flags_remain_false(monkeypatch, tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    row = _queue_rows()[0]
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [row])
    text_by_path = {}

    def _generate(payload):
        out_path = tmp_path / "governance_flags.pdf"
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        out_path.write_bytes(b"%PDF-1.4\n")
        text_by_path[str(out_path)] = _success_text_for_selected(selected)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": out_path.name,
            "report_id": out_path.stem,
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "readable_min_font_passed": True,
                "footer_safe_zone_passed": True,
                "tactical_edge_overlap_passed": True,
                "scorecard_readability_passed": True,
                "stoppage_readability_passed": True,
                "round_outlook_centered_passed": True,
                "footer_safe_zone_pages": {"6": {"safe": True}, "16": {"safe": True}, "17": {"safe": True}},
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", lambda path: (text_by_path.get(str(path), ""), 24))
    monkeypatch.setattr(app_module, "_selected_matchup_passes_strict_pdf_quality_gate", lambda *args, **kwargs: (True, []))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client_app:
        resp = client_app.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": [row["matchup_id"]]})
        data = resp.get_json()
        result = data["results"][0]

    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False
    assert result["customer_ready"] is True

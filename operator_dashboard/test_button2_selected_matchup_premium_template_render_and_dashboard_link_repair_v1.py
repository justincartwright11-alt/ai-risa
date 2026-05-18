import json

import operator_dashboard.app as app_module
from operator_dashboard.app import app
from operator_dashboard.button2_readonly_dossier_handoff_ingest_preview import (
    build_button2_readonly_dossier_handoff_ingest_preview,
)
from operator_dashboard.button2_dossier_handoff_report_context_preview import (
    build_button2_dossier_handoff_report_context_preview,
)


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"


def _selected_matchup_preview():
    return {
        "selected_for_button2": True,
        "selection_preview": True,
        "fighter_a": "Anthony Joshua",
        "fighter_b": "Daniel Dubois",
        "event_name": "Joshua vs Dubois",
        "event_date": "2026-09-21",
        "promotion": "Matchroom",
        "source_type": "official",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "report_ready_status": "ready_for_button2_preview",
    }


def test_selected_matchup_ingest_payload_uses_premium_template_summary_not_plain_fallback_label():
    payload = app_module._build_ingest_payload_from_selected_matchup(_selected_matchup_preview())

    summary = payload["dossier_summary_preview"]
    assert "AI-RISA Premium Fight Report" in summary
    assert "Template renderer profile: premium_template_pack_v29" in summary
    assert "Anthony Joshua vs Daniel Dubois" in summary
    assert "Event: Joshua vs Dubois" in summary
    assert "Source Traceability" in summary
    assert "Selected Matchup Report Generation Context" not in summary

    assert payload["template_renderer_profile"] == "premium_template_pack_v29"
    assert payload["ingest_mode"] == "premium_template_selected_matchup"


def test_selected_matchup_report_context_emits_template_and_traceability_metadata():
    ingest_payload = app_module._build_ingest_payload_from_selected_matchup(_selected_matchup_preview())

    ingest_result = build_button2_readonly_dossier_handoff_ingest_preview(ingest_payload)
    assert ingest_result["ok"] is True

    context_result = build_button2_dossier_handoff_report_context_preview(
        {"button2_ingest_preview_context": ingest_result["button2_ingest_preview_context"]}
    )
    assert context_result["ok"] is True

    ctx = context_result["report_context_preview"]
    assert ctx["template_renderer_profile"] == "premium_template_pack_v29"
    assert ctx["source_ingest_mode"] == "premium_template_selected_matchup"

    assert ctx["selected_matchup"]["fighter_a"] == "Anthony Joshua"
    assert ctx["selected_matchup"]["fighter_b"] == "Daniel Dubois"
    assert ctx["selected_matchup"]["event_name"] == "Joshua vs Dubois"

    trace_rows = ctx["source_traceability"]
    assert trace_rows and trace_rows[0]["id"] == "SRC-001"
    assert "matchroomboxing.com" in trace_rows[0]["url"]

    src_meta = ctx["source_traceability_metadata"]
    assert src_meta["schema_version"] == "button2.source_traceability.v1"
    assert src_meta["total_sources"] >= 1
    assert src_meta["sources"][0]["source_type"] == "official"
    assert src_meta["sources"][0]["verification_status"] == "verified"
    assert src_meta["lineage_graph"]["template_renderer_profile"] == "premium_template_pack_v29"


def test_guarded_generation_returns_open_link_and_governance_flags(monkeypatch):
    app.config["TESTING"] = True

    def _fake_generate(_payload):
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": "C:/tmp/anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf",
            "premium_template_render_used": True,
            "renderer_profile": "premium_template_pack_v29",
            "template_pack_root": "C:/ai_risa_next_dashboard_polish/ops/prf_reports/template_pack_sample",
            "template_pack_available": True,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fake_generate)

    payload = {
        "operator_approved": True,
        "selected_matchup_preview": _selected_matchup_preview(),
    }

    with app.test_client() as client:
        response = client.post(ROUTE, data=json.dumps(payload), content_type="application/json")

    assert response.status_code == 200
    data = response.get_json()

    assert data["ok"] is True
    assert data["output_filename"] == "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    assert data["pdf_open_url"] == (
        "/api/button2/generated-report/open?filename="
        "anthony_joshua_vs_daniel_dubois_joshua_vs_dubois_premium.pdf"
    )
    assert data["premium_template_render_used"] is True
    assert data["renderer_profile"] == "premium_template_pack_v29"

    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_dashboard_js_only_renders_open_link_when_filename_and_url_exist():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "const openUrl = String(data.pdf_open_url || '').trim();" in html
    assert "const outputFilename = String(data.output_filename || '').trim();" in html
    assert "const openLink = (openUrl && outputFilename)" in html
    assert "Open Generated PDF" in html

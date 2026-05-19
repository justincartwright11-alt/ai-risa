from __future__ import annotations

import os
from pathlib import Path

import pytest

from operator_dashboard import app as app_module


ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"
OPEN_ROUTE = "/api/button2/generated-report/open"
LIBRARY_ROUTE = "/api/button2/generated-report/library"


@pytest.fixture
def client(tmp_path, monkeypatch):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def _queue_rows():
    return [
        {
            "matchup_id": "glory100_rico_tariq",
            "fighter_a": "Rico Verhoeven",
            "fighter_b": "Tariq Osaro",
            "event_name": "GLORY 100",
            "event_date": "2026-06-14",
            "promotion": "GLORY",
            "source_url": "https://www.glorykickboxing.com/events/glory-100",
            "source_type": "official",
            "report_ready_status": "ready_for_button2_preview",
        },
        {
            "matchup_id": "onesamurai_nadaka_songchainoi",
            "fighter_a": "Nadaka Yoshinari",
            "fighter_b": "Songchainoi Kiatsongrit",
            "event_name": "ONE Samurai 1",
            "event_date": "2026-07-07",
            "promotion": "ONE",
            "source_url": "https://www.onefc.com/events/one-samurai-1",
            "source_type": "official",
            "report_ready_status": "ready_for_button2_preview",
        },
    ]


def _install_fake_generator(monkeypatch, tmp_path):
    captured = {"request_data": []}
    text_by_file = {}

    def fake_generate(request_data):
        captured["request_data"].append(request_data)
        selected = (
            request_data.get("ingest_payload", {})
            .get("selected_matchup_payload", {})
        )
        fighter_a = selected.get("fighter_a", "")
        fighter_b = selected.get("fighter_b", "")
        event_name = selected.get("event_name", "")
        source_url = selected.get("source_url", "")

        output_filename = request_data.get("output_filename_override")
        output_path = str(Path(tmp_path) / output_filename)
        Path(output_path).write_bytes(b"%PDF-1.4\n% fake\n")

        text_by_file[output_path] = (
            f"{fighter_a} vs {fighter_b}\n"
            f"Event: {event_name}\n"
            f"Source: {source_url}\n"
            f"Report ID: ARISA-{fighter_a.replace(' ', '_').upper()}-{fighter_b.replace(' ', '_').upper()}\n"
        )

        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": output_path,
            "renderer_route_used": "template_pack_jbalia_direct_renderer",
            "renderer_profile": "premium_template_pack_v29_jbalia_direct_v1",
            "template_pack_root": "C:/fake/template_pack",
            "template_pack_asset_backed": True,
            "premium_template_render_used": True,
            "page_count": 24,
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
            "report_id": f"ARISA-{fighter_a.replace(' ', '_').upper()}-{fighter_b.replace(' ', '_').upper()}",
        }

    def fake_extract(output_path):
        return text_by_file.get(str(output_path), ""), 24

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", fake_generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", fake_extract)
    return captured


def test_button2_panel_renders_selectable_matchup_rows(client):
    response = client.get("/")
    html = response.data.decode("utf-8")

    assert "Queued Matchups (Select One)" in html
    assert "b2-queued-matchups-list" in html
    assert "selectButton2QueuedMatchupByIndex" in html


def test_generate_requires_selected_matchup_id(client):
    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "approved_queue_rows": _queue_rows(),
        },
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["ok"] is False
    assert data["error"] == "selected_matchup_id_required"


def test_generate_rejects_unknown_matchup_id_without_pdf_write(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": "unknown_matchup",
            "approved_queue_rows": _queue_rows(),
        },
    )
    assert response.status_code == 422
    data = response.get_json()
    assert data["error"] == "selected_matchup_unknown"
    assert list(Path(tmp_path).glob("*.pdf")) == []


def test_selected_matchup_payload_reaches_renderer(client, tmp_path, monkeypatch):
    captured = _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()
    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[1]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )

    assert response.status_code == 200
    call = captured["request_data"][0]
    selected_payload = call["ingest_payload"]["selected_matchup_payload"]
    assert selected_payload["fighter_a"] == "Nadaka Yoshinari"
    assert selected_payload["fighter_b"] == "Songchainoi Kiatsongrit"
    assert selected_payload["event_name"] == "ONE Samurai 1"


def test_generated_pdf_text_matches_selected_matchup_not_default(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()
    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[1]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_matchup_fighter_a"] == "Nadaka Yoshinari"
    assert data["selected_matchup_fighter_b"] == "Songchainoi Kiatsongrit"
    assert data["selected_matchup_matches_pdf_text"] is True
    assert data["strict_quality_gate_passed"] is True
    assert "stale_pair_present:anthony joshua:daniel dubois" not in data["strict_quality_gate_violations"]


def test_switching_selected_matchups_produces_different_pdf_content(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()

    response_a = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[0]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )
    response_b = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[1]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    data_a = response_a.get_json()
    data_b = response_b.get_json()

    assert data_a["output_filename"] != data_b["output_filename"]
    assert data_a["selected_matchup_fighter_a"] != data_b["selected_matchup_fighter_a"]


def test_open_generated_pdf_uses_exact_current_output_path(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()

    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[0]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )
    data = response.get_json()
    open_response = client.get(OPEN_ROUTE, query_string={"filename": data["output_filename"]})

    assert response.status_code == 200
    assert open_response.status_code == 200


def test_reports_library_lists_current_generated_pdf(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()

    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[0]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )
    data = response.get_json()

    library = client.get(LIBRARY_ROUTE)
    html = library.data.decode("utf-8")
    assert library.status_code == 200
    assert data["output_filename"] in html


def test_governance_flags_remain_false(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()

    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[0]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )
    data = response.get_json()

    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_no_button1_button3_mutation(client, tmp_path, monkeypatch):
    _install_fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()

    response = client.post(
        ROUTE,
        json={
            "operator_approved": True,
            "selected_matchup_id": rows[1]["matchup_id"],
            "approved_queue_rows": rows,
        },
    )
    data = response.get_json()

    assert data["queue_write_performed"] is False
    assert data["button3_mutation_performed"] is False

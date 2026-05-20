from __future__ import annotations

import os
from pathlib import Path

import pytest

from operator_dashboard import app as app_module


QUEUE_READY_ROUTE = "/api/button2/queue-ready"
BATCH_ROUTE = "/api/button2/generate-selected-batch"
SINGLE_ROUTE = "/api/button2/selected-matchup/generate-guarded-v1"


@pytest.fixture
def client(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def _fake_generator(monkeypatch, tmp_path):
    calls = []
    text_by_path = {}

    def _generate(payload):
        calls.append(payload)
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        fighter_a = str(selected.get("fighter_a") or "")
        fighter_b = str(selected.get("fighter_b") or "")
        event_name = str(selected.get("event_name") or "")
        event_date = str(selected.get("event_date") or "")
        source_url = str(selected.get("source_url") or "")
        out_name = payload.get("output_filename_override")
        out_path = Path(tmp_path) / out_name
        out_path.write_bytes(b"%PDF-1.4\n% fake\n")
        marker_block = "\n".join(app_module._BUTTON2_REQUIRED_PREMIUM_MARKERS)
        alt_marker_block = "\n".join(f"{a} {b}" for a, b in app_module._BUTTON2_REQUIRED_PREMIUM_MARKER_ALTERNATIVES)
        layout_marker_block = "\n".join(app_module._BUTTON2_REQUIRED_V29_LAYOUT_MARKERS)
        text_by_path[str(out_path)] = (
            f"{fighter_a} vs {fighter_b}\n"
            f"Event: {event_name}\n"
            f"Event Date: {event_date}\n"
            f"Source: {source_url}\n"
            f"{marker_block}\n"
            f"{alt_marker_block}\n"
            f"{layout_marker_block}\n"
        )
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": str(out_path),
            "output_filename": str(out_name),
            "report_id": str(payload.get("fight_id") or "fight_id_missing"),
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_layout_parity_rebuild_v1",
            "template_pack_asset_backed": True,
            "layout_safety": {
                "logo_blend_ok": True,
                "logo_black_tile_risk": False,
                "readable_min_font_passed": True,
                "footer_safe_zone_passed": True,
                "tactical_edge_overlap_passed": True,
                "scorecard_readability_passed": True,
                "stoppage_readability_passed": True,
                "round_outlook_centered_passed": True,
                "footer_safe_zone_pages": {"6": {"safe": True}, "16": {"safe": True}, "17": {"safe": True}},
                "source_map": {"rows_separated": True, "source_url_statement_separated": True},
            },
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
        }

    def _extract(path):
        return text_by_path.get(str(path), ""), 24

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _generate)
    monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count", _extract)
    return calls


def _queue_rows():
    return app_module.load_button2_queue_readonly()


def _pick_ids(count=2):
    rows = _queue_rows()
    assert rows, "canonical queue must exist for Button 2 tests"
    return [r["matchup_id"] for r in rows[:count]]


def test_button2_queue_ready_endpoint_loads_real_queue_rows(client):
    resp = client.get(QUEUE_READY_ROUTE)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert isinstance(data.get("queue_rows"), list)
    assert data.get("canonical_source_used") is True


def test_button2_queue_ready_rows_have_required_fields(client):
    resp = client.get(QUEUE_READY_ROUTE)
    rows = resp.get_json().get("queue_rows", [])
    assert rows
    required = {
        "matchup_id", "event_id", "event_name", "event_date", "promotion",
        "fighter_a", "fighter_b", "weight_class", "bout_order",
        "source_url", "source_type", "provenance_status",
        "button2_readiness_status", "customer_ready_possible", "blocked_reason", "report_ready_status",
    }
    for row in rows:
        assert required.issubset(set(row.keys()))


def test_button2_ui_contains_multiselect_controls(client):
    resp = client.get("/")
    html = resp.data.decode("utf-8")
    assert "Refresh Queue" in html
    assert "Select All Ready" in html
    assert "Clear Selection" in html
    assert "Select Full Event Card" in html
    assert "Generate Selected PDFs" in html


def test_generate_batch_requires_operator_approval(client):
    resp = client.post(BATCH_ROUTE, json={"selected_matchup_ids": _pick_ids(1), "operator_approval": False})
    assert resp.status_code == 403
    assert resp.get_json()["error"] == "operator_approval_required"


def test_generate_batch_requires_selected_ids_or_event_selection(client):
    resp = client.post(BATCH_ROUTE, json={"operator_approval": True})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "selected_matchup_ids_required"


def test_generate_batch_rejects_unknown_ids_without_pdf_write(client, tmp_path):
    resp = client.post(BATCH_ROUTE, json={
        "operator_approval": True,
        "selected_matchup_ids": ["unknown_id_123"],
    })
    assert resp.status_code == 422
    assert resp.get_json()["error"] == "unknown_matchup_ids"
    assert list(Path(tmp_path).glob("*.pdf")) == []


def test_generate_batch_dedupes_selected_ids(client, tmp_path, monkeypatch):
    calls = _fake_generator(monkeypatch, tmp_path)
    one_id = _pick_ids(1)[0]
    resp = client.post(BATCH_ROUTE, json={
        "operator_approval": True,
        "selected_matchup_ids": [one_id, one_id, one_id],
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["requested_count"] == 1
    assert data["generated_count"] == 1
    assert len(calls) == 1


def test_generate_batch_generates_one_pdf_per_ready_selected_row(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    ids = _pick_ids(2)
    resp = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": ids})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["generated_count"] == 2
    assert len(list(Path(tmp_path).glob("*.pdf"))) == 2


def test_generate_batch_returns_per_row_output_paths(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    ids = _pick_ids(2)
    data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": ids}).get_json()
    assert len(data.get("output_paths", [])) == 2
    for row in data.get("results", []):
        if row.get("ok"):
            assert row.get("output_path")
            assert row.get("output_filename")


def test_generate_batch_skips_blocked_rows_with_reason(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()
    assert rows
    blocked_row = dict(rows[0])
    blocked_row["blocked_reason"] = "manual_review_required"
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [blocked_row])
    resp = client.post(BATCH_ROUTE, json={
        "operator_approval": True,
        "selected_matchup_ids": [blocked_row["matchup_id"]],
    })
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["skipped_count"] == 1
    assert data["results"][0]["reason"] == "manual_review_required"


def test_single_generation_uses_same_queue_resolver_as_batch(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    ids = _pick_ids(1)
    count = {"calls": 0}
    real_resolver = app_module.resolve_matchup_id_from_queue

    def _resolver(*args, **kwargs):
        count["calls"] += 1
        return real_resolver(*args, **kwargs)

    monkeypatch.setattr(app_module, "resolve_matchup_id_from_queue", _resolver)
    client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": ids})
    client.post(SINGLE_ROUTE, json={"operator_approved": True, "selected_matchup_id": ids[0]})
    assert count["calls"] >= 2


def test_full_event_card_selection_generates_ready_rows(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    rows = _queue_rows()
    assert rows
    event_id = rows[0]["event_id"]
    data = client.post(BATCH_ROUTE, json={
        "operator_approval": True,
        "event_id": event_id,
        "generate_all_ready_for_event": True,
    }).get_json()
    assert data["requested_count"] >= 1
    assert data["generated_count"] >= 1


def test_pdf_text_matches_each_selected_row(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    ids = _pick_ids(2)
    data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": ids}).get_json()
    for row in data["results"]:
        if row["ok"]:
            assert row["content_gate_passed"] is True


def test_switching_or_batching_does_not_use_stale_default_payload(client, tmp_path, monkeypatch):
    calls = _fake_generator(monkeypatch, tmp_path)
    ids = _pick_ids(2)
    client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": ids})
    assert len(calls) == 2
    a = calls[0]["ingest_payload"]["selected_matchup_payload"]
    b = calls[1]["ingest_payload"]["selected_matchup_payload"]
    assert (a["fighter_a"], a["fighter_b"]) != (b["fighter_a"], b["fighter_b"])


def test_governance_flags_remain_false(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": _pick_ids(1)}).get_json()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False


def test_button1_and_button3_mutation_flags_remain_false(client, tmp_path, monkeypatch):
    _fake_generator(monkeypatch, tmp_path)
    data = client.post(BATCH_ROUTE, json={"operator_approval": True, "selected_matchup_ids": _pick_ids(1)}).get_json()
    assert data["queue_write_performed"] is False
    assert data["button3_mutation_performed"] is False

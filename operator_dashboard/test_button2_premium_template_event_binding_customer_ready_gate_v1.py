"""
button2-premium-template-event-binding-customer-ready-gate-v1

Targeted tests confirming:
1. event_name, event_date, promotion are passed through from the queue row
   into the renderer's selected_matchup payload.
2. customer_ready=True is blocked when event_name is missing, "Unknown Event",
   or when the generated PDF text contains "unknown event" / "unknown_event".
3. customer_ready=True is blocked when event_date is missing or "n/a".
4. customer_ready=True is blocked when report_id contains "unknown_event".
5. A fully-bound UFC 300 row produces customer_ready=True with correct event label.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from operator_dashboard import app as app_module

BATCH_ROUTE = "/api/button2/generate-selected-batch"

# ---------------------------------------------------------------------------
# Shared queue fixtures
# ---------------------------------------------------------------------------

_GOOD_ROW = {
    "matchup_id": "ufc_300_alex_pereira_vs_jiri_prochazka",
    "event_id": "ufc_300",
    "event_name": "UFC 300",
    "event_date": "2026-07-12",
    "promotion": "UFC",
    "fighter_a": "Alex Pereira",
    "fighter_b": "Jiri Prochazka",
    "weight_class": "Light Heavyweight",
    "bout_order": 1,
    "source_url": "https://www.ufc.com/event/ufc-300",
    "source_type": "official",
    "provenance_status": "source_backed_ready",
    "button2_readiness_status": "ready_for_button2_generation",
    "report_ready_status": "ready_for_button2_generation",
    "customer_ready_possible": True,
    "blocked_reason": "",
    "selected_for_button2": True,
}

_MISSING_EVENT_ROW = {
    **_GOOD_ROW,
    "matchup_id": "test_missing_event_alex_pereira_vs_jiri_prochazka",
    "event_name": "",
    "event_date": "",
    "promotion": "",
}

_NA_EVENT_ROW = {
    **_GOOD_ROW,
    "matchup_id": "test_na_event_alex_pereira_vs_jiri_prochazka",
    "event_name": "n/a",
    "event_date": "n/a",
    "promotion": "",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_dummy_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n% AI-RISA test\n")


_PREMIUM_MARKERS = (
    "EXECUTIVE COMMAND DASHBOARD\n"
    "FIGHTER ARCHITECTURE RADAR\n"
    "TACTICAL EDGE MAP\n"
    "SCENARIO TREE / METHOD PATHWAYS\n"
    "TRACEABILITY / SOURCE MAP\n"
    "DISCLAIMER / RISK CONTROL\n"
)


def _make_pdf_text(selected_payload: dict, *, extra: str = "") -> str:
    fa = selected_payload.get("fighter_a", "")
    fb = selected_payload.get("fighter_b", "")
    event = selected_payload.get("event_name", "")
    src = selected_payload.get("source_url", "")
    return (
        f"{fa} vs {fb}\n"
        f"Event: {event}\n"
        f"Source: {src}\n"
        + _PREMIUM_MARKERS
        + (extra + "\n" if extra else "")
    )


def _install_fake_generator(monkeypatch, tmp_path, *, pdf_text_override=None, report_id_override=None):
    """
    Monkeypatch the renderer.  pdf_text_override can be a callable(selected_payload)->str
    or a plain string.  report_id_override can be a callable(fight_id)->str or a plain string.
    """
    text_by_path: dict = {}

    def _generate(payload):
        selected = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        _write_dummy_pdf(out_path)

        if callable(pdf_text_override):
            text = pdf_text_override(selected)
        elif pdf_text_override is not None:
            text = pdf_text_override
        else:
            text = _make_pdf_text(selected)

        text_by_path[str(out_path)] = text

        fight_id = payload.get("fight_id", "")
        if callable(report_id_override):
            rid = report_id_override(fight_id)
        elif report_id_override is not None:
            rid = report_id_override
        else:
            rid = fight_id

        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": out_name,
            "report_id": rid,
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1",
            "template_pack_asset_backed": True,
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


def _client_for_rows(monkeypatch, tmp_path, rows: list):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [dict(r) for r in rows])
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def _generate(client, matchup_id: str):
    with client:
        resp = client.post(BATCH_ROUTE, json={
            "operator_approval": True,
            "selected_matchup_ids": [matchup_id],
        })
        return resp.get_json()


# ---------------------------------------------------------------------------
# Tests: event field pass-through into ingest payload
# ---------------------------------------------------------------------------

def test_event_name_is_passed_through_to_ingest_payload(monkeypatch, tmp_path):
    """event_name from the queue row must reach the renderer's selected_matchup_payload."""
    captured = {}

    def _capture(payload):
        captured["selected"] = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        _write_dummy_pdf(out_path)
        text = _make_pdf_text(captured["selected"])
        monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count",
                            lambda p: (text, 24))
        return {
            "ok": True, "output_path": str(out_path), "output_filename": out_name,
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False, "external_api_delivery_performed": False,
            "queue_write_performed": False, "learning_apply_performed": False,
            "calibration_write_performed": False, "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _capture)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly",
                        lambda: [dict(_GOOD_ROW)])
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as tc:
        tc.post(BATCH_ROUTE, json={
            "operator_approval": True,
            "selected_matchup_ids": [_GOOD_ROW["matchup_id"]],
        })

    assert "selected" in captured, "renderer was never called"
    assert captured["selected"]["event_name"] == "UFC 300", (
        f"event_name not passed through; got: {captured['selected'].get('event_name')!r}"
    )


def test_event_date_is_passed_through_to_ingest_payload(monkeypatch, tmp_path):
    """event_date from the queue row must reach the renderer's selected_matchup_payload."""
    captured = {}

    def _capture(payload):
        captured["selected"] = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        _write_dummy_pdf(out_path)
        text = _make_pdf_text(captured["selected"])
        monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count",
                            lambda p: (text, 24))
        return {
            "ok": True, "output_path": str(out_path), "output_filename": out_name,
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False, "external_api_delivery_performed": False,
            "queue_write_performed": False, "learning_apply_performed": False,
            "calibration_write_performed": False, "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _capture)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly",
                        lambda: [dict(_GOOD_ROW)])
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as tc:
        tc.post(BATCH_ROUTE, json={
            "operator_approval": True,
            "selected_matchup_ids": [_GOOD_ROW["matchup_id"]],
        })

    assert captured["selected"]["event_date"] == "2026-07-12", (
        f"event_date not passed through; got: {captured['selected'].get('event_date')!r}"
    )


def test_promotion_is_passed_through_to_ingest_payload(monkeypatch, tmp_path):
    """promotion from the queue row must reach the renderer's selected_matchup_payload."""
    captured = {}

    def _capture(payload):
        captured["selected"] = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        _write_dummy_pdf(out_path)
        text = _make_pdf_text(captured["selected"])
        monkeypatch.setattr(app_module, "_extract_pdf_text_and_page_count",
                            lambda p: (text, 24))
        return {
            "ok": True, "output_path": str(out_path), "output_filename": out_name,
            "report_id": payload["fight_id"],
            "renderer_route_used": "template_pack_asset_renderer",
            "renderer_profile": "premium_template_pack_v29_selected_matchup_jbalia_hard_bind_v1",
            "template_pack_asset_backed": True,
            "delivery_performed": False, "external_api_delivery_performed": False,
            "queue_write_performed": False, "learning_apply_performed": False,
            "calibration_write_performed": False, "button3_mutation_performed": False,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _capture)
    monkeypatch.setattr(app_module, "load_button2_queue_readonly",
                        lambda: [dict(_GOOD_ROW)])
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True

    with app_module.app.test_client() as tc:
        tc.post(BATCH_ROUTE, json={
            "operator_approval": True,
            "selected_matchup_ids": [_GOOD_ROW["matchup_id"]],
        })

    assert captured["selected"]["promotion"] == "UFC", (
        f"promotion not passed through; got: {captured['selected'].get('promotion')!r}"
    )


# ---------------------------------------------------------------------------
# Tests: customer_ready gate — event binding checks
# ---------------------------------------------------------------------------

def test_fully_bound_ufc300_row_produces_customer_ready_true(monkeypatch, tmp_path):
    """A well-formed UFC 300 queue row must yield customer_ready=True."""
    _install_fake_generator(monkeypatch, tmp_path)
    client = _client_for_rows(monkeypatch, tmp_path, [_GOOD_ROW])
    data = _generate(client, _GOOD_ROW["matchup_id"])
    row = data["results"][0]
    assert row["ok"] is True
    assert row["customer_ready"] is True
    assert row["visual_gate_status"] == "premium_template_confirmed"


def test_missing_event_name_blocks_customer_ready(monkeypatch, tmp_path):
    """Row with empty event_name must not produce customer_ready=True."""
    def _text_without_event(sel):
        # PDF text has no event name at all
        return (
            f"{sel['fighter_a']} vs {sel['fighter_b']}\n"
            f"Source: {sel['source_url']}\n"
            + _PREMIUM_MARKERS
        )
    _install_fake_generator(monkeypatch, tmp_path, pdf_text_override=_text_without_event)
    client = _client_for_rows(monkeypatch, tmp_path, [_MISSING_EVENT_ROW])
    data = _generate(client, _MISSING_EVENT_ROW["matchup_id"])
    row = data["results"][0]
    assert row["customer_ready"] is False, "customer_ready must be False when event_name is empty"
    assert row["ok"] is False


def test_missing_event_date_blocks_customer_ready(monkeypatch, tmp_path):
    """Row with empty event_date must not produce customer_ready=True."""
    _install_fake_generator(monkeypatch, tmp_path)
    client = _client_for_rows(monkeypatch, tmp_path, [_MISSING_EVENT_ROW])
    data = _generate(client, _MISSING_EVENT_ROW["matchup_id"])
    row = data["results"][0]
    assert row["customer_ready"] is False, "customer_ready must be False when event_date is empty"


def test_unknown_event_in_pdf_text_blocks_customer_ready(monkeypatch, tmp_path):
    """If the generated PDF text contains 'Unknown Event', customer_ready must be False."""
    def _text_with_unknown(sel):
        return (
            f"{sel['fighter_a']} vs {sel['fighter_b']}\n"
            "Unknown Event | n/a | CUSTOMER READY\n"  # simulates the broken cover text
            f"Source: {sel['source_url']}\n"
            + _PREMIUM_MARKERS
        )
    _install_fake_generator(monkeypatch, tmp_path, pdf_text_override=_text_with_unknown)
    client = _client_for_rows(monkeypatch, tmp_path, [_GOOD_ROW])
    data = _generate(client, _GOOD_ROW["matchup_id"])
    row = data["results"][0]
    assert row["customer_ready"] is False, (
        "customer_ready must be False when PDF text contains 'Unknown Event'"
    )


def test_unknown_event_report_id_blocks_customer_ready(monkeypatch, tmp_path):
    """If the report_id returned by the renderer contains 'unknown_event', block customer_ready."""
    _install_fake_generator(
        monkeypatch, tmp_path,
        report_id_override="alex_pereira_jiri_prochazka_unknown_event",
    )
    client = _client_for_rows(monkeypatch, tmp_path, [_GOOD_ROW])
    data = _generate(client, _GOOD_ROW["matchup_id"])
    row = data["results"][0]
    assert row["customer_ready"] is False, (
        "customer_ready must be False when report_id contains 'unknown_event'"
    )


def test_na_event_name_row_blocks_customer_ready(monkeypatch, tmp_path):
    """Row with event_name='n/a' must not produce customer_ready=True."""
    def _text_na(sel):
        return (
            f"{sel['fighter_a']} vs {sel['fighter_b']}\n"
            "Event: n/a\n"
            f"Source: {sel['source_url']}\n"
            + _PREMIUM_MARKERS
        )
    _install_fake_generator(monkeypatch, tmp_path, pdf_text_override=_text_na)
    client = _client_for_rows(monkeypatch, tmp_path, [_NA_EVENT_ROW])
    data = _generate(client, _NA_EVENT_ROW["matchup_id"])
    row = data["results"][0]
    assert row["customer_ready"] is False, "customer_ready must be False when event_name is 'n/a'"


def test_batch_generated_count_excludes_event_binding_failures(monkeypatch, tmp_path):
    """Rows that fail event-binding gate must appear in failed_count, not generated_count."""
    def _text_without_event(sel):
        return (
            f"{sel['fighter_a']} vs {sel['fighter_b']}\n"
            "Unknown Event | n/a | CUSTOMER READY\n"
            f"Source: {sel['source_url']}\n"
            + _PREMIUM_MARKERS
        )
    _install_fake_generator(monkeypatch, tmp_path, pdf_text_override=_text_without_event)
    client = _client_for_rows(monkeypatch, tmp_path, [_GOOD_ROW])
    data = _generate(client, _GOOD_ROW["matchup_id"])
    assert data["generated_count"] == 0
    assert data["failed_count"] == 1


def test_event_binding_gate_violation_appears_in_response(monkeypatch, tmp_path):
    """When event binding fails, the violation must appear in the result metadata."""
    def _text_with_unknown(sel):
        return (
            f"{sel['fighter_a']} vs {sel['fighter_b']}\n"
            "Unknown Event | n/a | CUSTOMER READY\n"
            f"Source: {sel['source_url']}\n"
            + _PREMIUM_MARKERS
        )
    _install_fake_generator(monkeypatch, tmp_path, pdf_text_override=_text_with_unknown)
    client = _client_for_rows(monkeypatch, tmp_path, [_GOOD_ROW])
    data = _generate(client, _GOOD_ROW["matchup_id"])
    row = data["results"][0]
    # The response must indicate the gate failed
    assert row.get("visual_gate_status") != "premium_template_confirmed"


def test_build_selected_matchup_preview_includes_event_fields():
    """Unit test: _build_selected_matchup_preview_from_row must copy event fields from the row."""
    from operator_dashboard.app import _build_selected_matchup_preview_from_row
    row = dict(_GOOD_ROW)
    preview = _build_selected_matchup_preview_from_row(row)
    assert preview["event_name"] == "UFC 300"
    assert preview["event_date"] == "2026-07-12"
    assert preview["promotion"] == "UFC"


def test_build_selected_matchup_preview_empty_event_fields_when_row_missing():
    """Unit test: missing event fields in row → empty strings in preview (not 'Unknown Event')."""
    from operator_dashboard.app import _build_selected_matchup_preview_from_row
    row = {
        "matchup_id": "test_no_event",
        "fighter_a": "Alex Pereira",
        "fighter_b": "Jiri Prochazka",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "source_type": "official",
        "button2_readiness_status": "ready_for_button2_generation",
        "report_ready_status": "ready_for_button2_generation",
        "selected_for_button2": True,
    }
    preview = _build_selected_matchup_preview_from_row(row)
    assert preview["event_name"] == "", f"expected empty string, got {preview['event_name']!r}"
    assert preview["event_date"] == "", f"expected empty string, got {preview['event_date']!r}"
    assert preview["promotion"] == "", f"expected empty string, got {preview['promotion']!r}"

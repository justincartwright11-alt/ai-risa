from __future__ import annotations

import os
from pathlib import Path

import pytest

from operator_dashboard import app as app_module
from operator_dashboard import button2_template_pack_asset_renderer_v1 as template_renderer


BATCH_ROUTE = "/api/button2/generate-selected-batch"


@pytest.fixture
def client(tmp_path, monkeypatch):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    queue_rows = [
        {
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
        },
        {
            "matchup_id": "ufc_300_islam_makhachev_vs_dustin_poirier",
            "event_id": "ufc_300",
            "event_name": "UFC 300",
            "event_date": "2026-07-12",
            "promotion": "UFC",
            "fighter_a": "Islam Makhachev",
            "fighter_b": "Dustin Poirier",
            "weight_class": "Lightweight",
            "bout_order": 2,
            "source_url": "https://www.ufc.com/event/ufc-300",
            "source_type": "official",
            "provenance_status": "source_backed_ready",
            "button2_readiness_status": "ready_for_button2_generation",
            "report_ready_status": "ready_for_button2_generation",
            "customer_ready_possible": True,
            "blocked_reason": "",
        },
    ]

    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: [dict(r) for r in queue_rows])

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client, tmp_path


def _write_dummy_pdf(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n% AI-RISA premium test\n")


def _premium_text_for(selected: dict, *, include_bleed: str = "") -> str:
    base = (
        f"{selected['fighter_a']} vs {selected['fighter_b']}\n"
        f"Event: {selected['event_name']}\n"
        f"Source: {selected['source_url']}\n"
        "EXECUTIVE COMMAND DASHBOARD\n"
        "FIGHTER ARCHITECTURE RADAR\n"
        "TACTICAL EDGE MAP\n"
        "SCENARIO TREE / METHOD PATHWAYS\n"
        "TRACEABILITY / SOURCE MAP\n"
        "DISCLAIMER / RISK CONTROL\n"
    )
    if include_bleed:
        base += include_bleed
    return base


def _fake_premium_generator(monkeypatch, tmp_path, *, include_bleed: str = ""):
    calls = []
    text_by_path = {}

    def _generate(payload):
        calls.append(payload)
        selected = payload["ingest_payload"]["selected_matchup_payload"]
        out_name = payload["output_filename_override"]
        out_path = Path(tmp_path) / out_name
        _write_dummy_pdf(out_path)
        text_by_path[str(out_path)] = _premium_text_for(selected, include_bleed=include_bleed)
        return {
            "ok": True,
            "output_path": str(out_path),
            "output_filename": out_name,
            "report_id": str(payload.get("fight_id") or "fight_id_missing"),
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
    return calls


def _post_generate(client, selected_ids):
    return client.post(BATCH_ROUTE, json={
        "operator_approval": True,
        "selected_matchup_ids": selected_ids,
    })


def test_generated_report_uses_premium_template_renderer_not_plain_text_fallback(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path)

    fallback_called = {"called": False}

    def _fallback(*_args, **_kwargs):
        fallback_called["called"] = True
        return {"ok": False}

    monkeypatch.setattr(app_module, "_generate_button2_fallback_pdf", _fallback)

    resp = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"])
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["generated_count"] == 1
    assert data["failed_count"] == 0
    assert fallback_called["called"] is False


def test_template_pack_paths_are_detected(monkeypatch):
    candidates = [
        r"C:\missing\path",
        r"C:\repo\template_pack_sample",
        r"C:\workspace\reports\template_pack_sample",
        r"C:\workspace\operator_dashboard\assets\template_pack_sample",
    ]
    monkeypatch.setattr(template_renderer, "_build_template_pack_root_candidates", lambda: candidates)
    monkeypatch.setattr(template_renderer.os.path, "isdir", lambda p: p == candidates[1])

    resolved, searched = template_renderer.resolve_template_pack_root_path()
    assert resolved == candidates[1]
    assert searched == candidates


def test_missing_template_assets_fail_closed_or_mark_not_customer_ready(client, monkeypatch):
    test_client, _tmp_path = client

    def _fail(_payload):
        return {
            "ok": False,
            "error": "template_pack_unavailable",
            "message": "Template pack required assets are missing.",
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fail)

    resp = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"])
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["generated_count"] == 0
    assert data["failed_count"] == 1
    assert data["results"][0]["ok"] is False
    assert data["results"][0]["error"] == "template_pack_unavailable"


def test_generated_cover_contains_selected_fighters_not_template_sample_names(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path)

    resp = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"])
    data = resp.get_json()

    assert data["generated_count"] == 1
    assert data["results"][0]["content_gate_passed"] is True


def test_generated_report_contains_premium_dashboard_markers(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path)

    data = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"]).get_json()
    assert data["generated_count"] == 1
    assert data["results"][0]["content_gate_passed"] is True


def test_generated_report_contains_radar_tactical_scenario_traceability_markers(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path)

    data = _post_generate(test_client, ["ufc_300_islam_makhachev_vs_dustin_poirier"]).get_json()
    assert data["generated_count"] == 1
    assert data["results"][0]["content_gate_passed"] is True


def test_generated_report_rejects_template_sample_name_bleed(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path, include_bleed="Bahram Rajabzadeh vs Donovan Wisse\n")

    data = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"]).get_json()
    assert data["generated_count"] == 0
    assert data["failed_count"] == 1
    assert data["results"][0]["error"] == "pdf_quality_gate_failed"


def test_generated_report_rejects_joshua_dubois_bleed_for_non_joshua_selection(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path, include_bleed="Anthony Joshua vs Daniel Dubois\n")

    data = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"]).get_json()
    assert data["generated_count"] == 0
    assert data["failed_count"] == 1
    assert data["results"][0]["error"] == "pdf_quality_gate_failed"


def test_bulk_generation_still_uses_selected_queue_rows(client, monkeypatch):
    test_client, tmp_path = client
    calls = _fake_premium_generator(monkeypatch, tmp_path)

    data = _post_generate(
        test_client,
        [
            "ufc_300_alex_pereira_vs_jiri_prochazka",
            "ufc_300_islam_makhachev_vs_dustin_poirier",
        ],
    ).get_json()

    assert data["generated_count"] == 2
    assert len(calls) == 2
    selected_pairs = [
        (
            c["ingest_payload"]["selected_matchup_payload"]["fighter_a"],
            c["ingest_payload"]["selected_matchup_payload"]["fighter_b"],
        )
        for c in calls
    ]
    assert ("Alex Pereira", "Jiri Prochazka") in selected_pairs
    assert ("Islam Makhachev", "Dustin Poirier") in selected_pairs


def test_governance_flags_remain_false(client, monkeypatch):
    test_client, tmp_path = client
    _fake_premium_generator(monkeypatch, tmp_path)

    data = _post_generate(test_client, ["ufc_300_alex_pereira_vs_jiri_prochazka"]).get_json()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False

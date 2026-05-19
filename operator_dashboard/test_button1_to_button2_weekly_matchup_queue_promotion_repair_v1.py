from __future__ import annotations

import json
import os
import re
from pathlib import Path

import pytest

from operator_dashboard import app as app_module


PROMOTE_ROUTE = "/api/button1/promote-ready-matchups-to-button2-queue"
QUEUE_READY_ROUTE = "/api/button2/queue-ready"
BATCH_ROUTE = "/api/button2/generate-selected-batch"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _sample_button1_source_payload() -> dict:
    return {
        "events": [
            {
                "candidate_id": "event_alpha",
                "event_id": "event_alpha",
                "event_name": "Event Alpha",
                "event_date": "2026-09-01",
                "promotion": "UFC",
                "source_url": "https://www.ufc.com/event/event-alpha",
                "source_type": "official",
                "provenance_status": "source_backed_ready",
                "queue_save_eligible": True,
                "button2_readiness_status": "ready_for_button2_preview",
                "matchups": [
                    {
                        "matchup_id": "alpha_ready_1",
                        "fighter_a": "Fighter Alpha One",
                        "fighter_b": "Fighter Beta One",
                        "weight_class": "Lightweight",
                        "bout_order": 1,
                        "source_url": "https://www.ufc.com/event/event-alpha",
                        "source_type": "official",
                        "provenance_status": "source_backed_ready",
                        "queue_save_eligible": True,
                        "button2_readiness_status": "ready_for_button2_preview",
                        "customer_ready_possible": True,
                        "blocked_reason": "",
                    },
                    {
                        "matchup_id": "alpha_ready_2",
                        "fighter_a": "Fighter Alpha Two",
                        "fighter_b": "Fighter Beta Two",
                        "weight_class": "Featherweight",
                        "bout_order": 2,
                        "source_url": "https://www.ufc.com/event/event-alpha",
                        "source_type": "official",
                        "provenance_status": "source_backed_ready",
                        "queue_save_eligible": True,
                        "button2_readiness_status": "ready_for_button2_generation",
                        "customer_ready_possible": True,
                        "blocked_reason": "",
                    },
                    {
                        "matchup_id": "alpha_not_ready",
                        "fighter_a": "Fighter Alpha Three",
                        "fighter_b": "Fighter Beta Three",
                        "weight_class": "Welterweight",
                        "bout_order": 3,
                        "source_url": "https://www.ufc.com/event/event-alpha",
                        "source_type": "official",
                        "provenance_status": "source_backed_ready",
                        "queue_save_eligible": True,
                        "button2_readiness_status": "review_only",
                        "customer_ready_possible": True,
                        "blocked_reason": "",
                    },
                    {
                        "matchup_id": "alpha_blocked",
                        "fighter_a": "Fighter Alpha Four",
                        "fighter_b": "Fighter Beta Four",
                        "weight_class": "Middleweight",
                        "bout_order": 4,
                        "source_url": "https://www.ufc.com/event/event-alpha",
                        "source_type": "official",
                        "provenance_status": "source_backed_ready",
                        "queue_save_eligible": True,
                        "button2_readiness_status": "ready_for_button2_preview",
                        "customer_ready_possible": True,
                        "blocked_reason": "manual_review_required",
                    },
                ],
            }
        ]
    }


def _sample_button2_queue_payload() -> dict:
    return {
        "queue": [
            {
                "matchup_id": "existing_queue_row",
                "event_name": "Existing Event",
                "event_id": "existing_event",
                "event_date": "2026-08-20",
                "promotion": "Bellator",
                "fighter_a": "Existing Fighter A",
                "fighter_b": "Existing Fighter B",
                "weight_class": "Lightweight",
                "bout_order": 1,
                "source_url": "https://www.bellator.com/events/existing",
                "source_type": "official",
                "provenance_status": "source_backed",
                "button2_readiness_status": "ready_for_button2_generation",
                "report_ready_status": "ready_for_button2_generation",
                "customer_ready_possible": True,
                "blocked_reason": "",
            }
        ],
        "metadata": {
            "source": "operator_approved_fight_queue",
            "last_updated_at": "2026-05-19T00:00:00+00:00",
            "total_rows": 1,
            "ready_count": 1,
            "blocked_count": 0,
            "canonical_source": True,
        },
    }


def _read_queue_rows(queue_path: Path) -> list[dict]:
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    rows = payload.get("queue", [])
    return [dict(r) for r in rows if isinstance(r, dict)]


def _extract_function_body(html: str, function_name: str) -> str:
    marker = f"function {function_name}("
    start = html.find(marker)
    assert start >= 0, f"{function_name} not found"
    brace_start = html.find("{", start)
    assert brace_start >= 0, f"opening brace for {function_name} not found"
    depth = 0
    idx = brace_start
    while idx < len(html):
        ch = html[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return html[brace_start + 1:idx]
        idx += 1
    raise AssertionError(f"closing brace for {function_name} not found")


@pytest.fixture
def client(tmp_path, monkeypatch):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)

    source_path = tmp_path / "ops" / "approved_sources" / "button1_live_event_source_rows.json"
    queue_path = tmp_path / "ops" / "prf_queue" / "button2_approved_fight_queue.json"
    _write_json(source_path, _sample_button1_source_payload())
    _write_json(queue_path, _sample_button2_queue_payload())

    monkeypatch.setattr(app_module, "_button1_canonical_source_path", lambda: str(source_path))
    monkeypatch.setattr(app_module, "_button2_canonical_queue_path", lambda: str(queue_path))
    monkeypatch.setattr(app_module, "load_button2_queue_readonly", lambda: _read_queue_rows(queue_path))

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client, source_path, queue_path


def test_promote_requires_operator_approval(client):
    test_client, _source_path, _queue_path = client
    resp = test_client.post(PROMOTE_ROUTE, json={"operator_approval": False, "promote_all_ready": True})
    data = resp.get_json()
    assert resp.status_code == 403
    assert data["ok"] is False
    assert data["error"] == "operator_approval_required"
    assert data["queue_write_performed"] is False


def test_promote_all_ready_writes_ready_source_backed_rows_to_button2_queue(client):
    test_client, _source_path, queue_path = client
    before = len(_read_queue_rows(queue_path))
    resp = test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True})
    data = resp.get_json()
    after = len(_read_queue_rows(queue_path))

    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["promoted_count"] == 2
    assert data["duplicate_count"] == 0
    assert data["skipped_count"] == 0
    assert data["queue_before_count"] == before
    assert data["queue_after_count"] == after
    assert after == before + 2


def test_promote_selected_rows_writes_only_selected_rows(client):
    test_client, _source_path, queue_path = client
    resp = test_client.post(
        PROMOTE_ROUTE,
        json={
            "operator_approval": True,
            "matchup_ids": ["alpha_ready_1"],
        },
    )
    data = resp.get_json()
    rows = _read_queue_rows(queue_path)
    ids = {r.get("matchup_id") for r in rows}

    assert resp.status_code == 200
    assert data["promoted_count"] == 1
    assert "alpha_ready_1" in ids
    assert "alpha_ready_2" not in ids


def test_promote_skips_not_ready_or_blocked_rows_with_reason(client):
    test_client, _source_path, _queue_path = client
    resp = test_client.post(
        PROMOTE_ROUTE,
        json={
            "operator_approval": True,
            "matchup_ids": ["alpha_not_ready", "alpha_blocked"],
        },
    )
    data = resp.get_json()
    skipped = data.get("skipped_rows", [])
    reasons = {row.get("matchup_id"): row.get("reason") for row in skipped}

    assert resp.status_code == 200
    assert data["promoted_count"] == 0
    assert data["skipped_count"] == 2
    assert reasons["alpha_not_ready"] == "not_ready_for_button2"
    assert reasons["alpha_blocked"] == "blocked_reason_present"


def test_promote_dedupes_existing_queue_rows(client):
    test_client, _source_path, queue_path = client
    first = test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True}).get_json()
    second = test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True}).get_json()
    after_rows = _read_queue_rows(queue_path)

    assert first["promoted_count"] == 2
    assert second["promoted_count"] == 0
    assert second["duplicate_count"] == 2
    assert len(after_rows) == second["queue_after_count"]


def test_button2_queue_ready_loads_promoted_rows(client):
    test_client, _source_path, _queue_path = client
    test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True})

    resp = test_client.get(QUEUE_READY_ROUTE)
    data = resp.get_json()
    ids = {row.get("matchup_id") for row in data.get("queue_rows", [])}

    assert resp.status_code == 200
    assert "alpha_ready_1" in ids
    assert "alpha_ready_2" in ids


def test_button2_queue_ready_count_increases_after_promotion(client):
    test_client, _source_path, _queue_path = client
    before = test_client.get(QUEUE_READY_ROUTE).get_json()["total_rows"]
    test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True})
    after = test_client.get(QUEUE_READY_ROUTE).get_json()["total_rows"]

    assert before == 1
    assert after == 3
    assert after > before


def test_ui_contains_save_selected_ready_to_pdf_queue_control(client):
    test_client, _source_path, _queue_path = client
    html = test_client.get("/").data.decode("utf-8")
    assert "Save Selected Ready to PDF Queue" in html
    assert "b1-save-selected-ready-to-pdf-queue-btn" in html


def test_ui_contains_save_all_ready_to_pdf_queue_control(client):
    test_client, _source_path, _queue_path = client
    html = test_client.get("/").data.decode("utf-8")
    assert "Save All Ready to PDF Queue" in html
    assert "b1-save-all-ready-to-pdf-queue-btn" in html


def test_no_localstorage_source_of_truth_for_promotion(client):
    test_client, _source_path, _queue_path = client
    html = test_client.get("/").data.decode("utf-8")

    fn_names = [
        "button1RunPromotionRequest",
        "button1SaveSelectedReadyToPdfQueue",
        "button1SaveAllReadyToPdfQueue",
        "button1PromotionSelectedIdsFromCurrentRows",
    ]
    for fn_name in fn_names:
        body = _extract_function_body(html, fn_name)
        assert "localStorage" not in body


def test_governance_flags_remain_closed_except_approved_queue_write(client):
    test_client, _source_path, _queue_path = client
    denied = test_client.post(PROMOTE_ROUTE, json={"operator_approval": False, "promote_all_ready": True}).get_json()
    approved = test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True}).get_json()

    for payload in (denied, approved):
        assert payload["delivery_performed"] is False
        assert payload["external_api_delivery_performed"] is False
        assert payload["learning_apply_performed"] is False
        assert payload["calibration_write_performed"] is False
        assert payload["button3_mutation_performed"] is False

    assert denied["queue_write_performed"] is False
    assert approved["queue_write_performed"] is True


def test_button2_bulk_generation_can_select_promoted_rows(client, tmp_path, monkeypatch):
    test_client, _source_path, _queue_path = client
    test_client.post(PROMOTE_ROUTE, json={"operator_approval": True, "promote_all_ready": True})

    calls = []

    def _fake_generate(payload):
        calls.append(payload)
        selected = payload.get("ingest_payload", {}).get("selected_matchup_payload", {})
        out_name = payload.get("output_filename_override") or "test.pdf"
        out_path = Path(tmp_path) / out_name
        out_path.write_bytes(b"%PDF-1.4\n% fake\n")
        return {
            "ok": True,
            "message": "PDF generated and saved successfully.",
            "output_path": str(out_path),
            "output_filename": str(out_name),
            "report_id": str(payload.get("fight_id") or "fight_id_missing"),
            "delivery_performed": False,
            "external_api_delivery_performed": False,
            "queue_write_performed": False,
            "learning_apply_performed": False,
            "calibration_write_performed": False,
            "button3_mutation_performed": False,
            "_selected": selected,
        }

    monkeypatch.setattr(app_module, "generate_button2_report_render_gate_integration", _fake_generate)
    monkeypatch.setattr(
        app_module,
        "_extract_pdf_text_and_page_count",
        lambda path: ("Fighter Alpha One Fighter Beta One Event Alpha", 24),
    )
    monkeypatch.setattr(
        app_module,
        "_selected_matchup_passes_strict_pdf_quality_gate",
        lambda selected_preview, result, pdf_text, page_count: (True, []),
    )
    monkeypatch.setattr(
        app_module,
        "_scan_forbidden_markers",
        lambda pdf_text: {
            "any_forbidden_found": False,
            "found_markers": [],
            "marker_hits": {},
            "found_concatenation_snippets": [],
            "concatenation_hits": {},
        },
    )

    resp = test_client.post(
        BATCH_ROUTE,
        json={
            "operator_approval": True,
            "selected_matchup_ids": ["alpha_ready_1"],
        },
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["generated_count"] == 1
    assert data["requested_count"] == 1
    assert calls, "expected generator to run for promoted row"

"""Dashboard runtime confirmation for multisport fixture-backed Button 1 event cards (v1)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.button1_multisport_approved_source_event_card_fixtures_v1 import (
    build_button1_runtime_payload_from_fixtures_v1,
)
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _fixture_rows():
    return build_button1_runtime_payload_from_fixtures_v1()["candidate_rows"]


def test_dashboard_root_exposes_button1_event_card_surface_and_runtime_wire(client):
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Source-Backed Event Cards" in html
    assert "id=\"b1-event-cards-list\"" in html
    assert "handleButton1Click()" in html
    assert "requestLocalAiWorkflowPreviewWithRuntimeContext(SOURCE_BUTTON_FIND_FIGHTS)" in html


def test_fixture_backed_rows_flow_through_button1_workflow_preview_route(client):
    rows = _fixture_rows()
    context_pack = {
        "manual_text": "fixture-backed-multisport-check",
        "approved_source_refs": [],
        "event_hint": "",
        "promotion_hint": "",
        "date_window": {},
        "candidate_rows": rows,
    }

    response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={
            "source_button": "button1_find_fights",
            "context_pack": context_pack,
            "execute_preview": True,
        },
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True

    workflow = data["workflow"]
    assert workflow["status"] == "preview_ready"

    first_job = workflow["jobs"][0]
    payload = first_job["input_ref"]["metadata"]["payload"]
    returned_rows = payload["candidate_rows"]
    returned_sports = {row["sport"] for row in returned_rows}

    assert len(returned_rows) == 4
    assert returned_sports == {"boxing", "mma", "kickboxing", "muay_thai"}

    summary = first_job["output_preview"]["summary"]
    assert summary["discovered_count"] == 4
    assert summary["extracted_count"] == 4


def test_button1_selector_preview_surfaces_fixture_rows_without_generation_or_mutation(client):
    rows = _fixture_rows()

    for row in rows:
        response = client.post(
            "/api/button1-button2/event-card-matchup/select-preview",
            json={
                "candidate_id": row["candidate_id"],
                "operator_selected": True,
                "candidate_rows": rows,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["selection_preview"] is True
        assert data["selected_for_button2"] is True
        assert data["source_url"] == row["source_url"]

        safety = data["safety_flags"]
        assert safety["pdf_generation_performed"] is False
        assert safety["queue_write_performed"] is False
        assert safety["delivery_performed"] is False
        assert safety["email_send_performed"] is False
        assert safety["external_api_delivery_performed"] is False
        assert safety["learning_apply_performed"] is False
        assert safety["calibration_write_performed"] is False
        assert safety["button3_mutation_performed"] is False


def test_dashboard_runtime_governance_stays_preview_only_and_no_write(client):
    rows = _fixture_rows()
    token = dict(
        build_three_button_workflow_plan(
            "button1_find_fights",
            LocalAIJobInputRef(ref_type="entity", ref_key="dashboard_runtime_set", snapshot_hash="snap_v1"),
        ).gate_approval_token_preview
    )

    gate_response = client.post(
        "/api/local-ai/gate1/save-fights/dry-run-apply-preview",
        json={
            "gate_approval_token_preview": token,
            "candidate_rows": rows,
        },
    )

    assert gate_response.status_code == 200
    gate_data = gate_response.get_json()
    assert gate_data["preview_only"] is True
    assert gate_data["write_authorized"] is False
    assert gate_data["mutation_performed"] is False
    assert gate_data["queue_write_performed"] is False
    assert gate_data["database_write_performed"] is False


def test_muay_thai_row_remains_needs_review_in_dashboard_runtime_surface(client):
    rows = _fixture_rows()
    muay_thai_row = next(row for row in rows if row["sport"] == "muay_thai")

    assert muay_thai_row["source_backed"] is True
    assert muay_thai_row["preview_only"] is True
    assert muay_thai_row["approval_required"] is True
    assert muay_thai_row["ready_state"] == "needs_review"
    assert muay_thai_row["requires_secondary_confirmation"] is True
    assert muay_thai_row["unsafe_queue_save_blocked"] is True

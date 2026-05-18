"""Live-feed population confirmation for Button 1 multisport approved-source event cards (v1)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import load_readonly_runtime_state
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _approved_live_rows_from_runtime_state():
    state = load_readonly_runtime_state()
    all_rows = state.get("discovered_candidate_rows", [])
    approved_rows = [
        row
        for row in all_rows
        if isinstance(row, dict) and row.get("provenance_origin") == "approved_source_live_event_ingestion"
    ]
    return state, approved_rows


def _is_http_url(value):
    return isinstance(value, str) and value.strip().lower().startswith(("http://", "https://"))


def test_live_feed_hydrates_at_least_four_approved_source_event_rows_with_all_target_sports():
    state, approved_rows = _approved_live_rows_from_runtime_state()
    live_source_status = state.get("live_source_status", {})

    assert live_source_status.get("approved_source_event_rows_count", 0) >= 4
    assert live_source_status.get("diagnostics", []) == []

    sports = {row.get("sport") for row in approved_rows}
    assert {"boxing", "mma", "kickboxing", "muay_thai"}.issubset(sports)


@pytest.mark.parametrize(
    "required_key",
    [
        "event_name",
        "promotion",
        "sport",
        "modality",
        "event_date",
        "source_url",
        "source_name",
        "source_type",
        "source_tier",
        "provenance_status",
        "matchups",
        "approval_required",
        "preview_only",
    ],
)
def test_each_approved_live_event_row_contains_required_contract_fields(required_key):
    _, approved_rows = _approved_live_rows_from_runtime_state()
    assert approved_rows, "expected approved live rows from feed"

    for row in approved_rows:
        assert required_key in row


def test_each_live_event_row_is_url_backed_and_each_matchup_has_source_backed_readiness_fields():
    _, approved_rows = _approved_live_rows_from_runtime_state()

    for row in approved_rows:
        assert _is_http_url(row.get("source_url"))
        assert row.get("approval_required") is True
        assert row.get("preview_only") is True

        matchups = row.get("matchups")
        assert isinstance(matchups, list)
        assert len(matchups) >= 1

        for matchup in matchups:
            assert isinstance(matchup.get("fighter_a"), str) and matchup["fighter_a"].strip()
            assert isinstance(matchup.get("fighter_b"), str) and matchup["fighter_b"].strip()
            assert matchup.get("source_backed") is True
            assert isinstance(matchup.get("button2_readiness_status"), str)
            assert matchup["button2_readiness_status"] in {"ready_for_button2_preview", "review_only"}


def test_dashboard_surface_and_runtime_preview_include_all_four_sports(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Source-Backed Event Cards" in html
    assert "id=\"b1-event-cards-list\"" in html

    workflow_response = client.post(
        "/api/local-ai/orchestrator/workflow-preview",
        json={
            "source_button": "button1_find_fights",
            "use_runtime_context": True,
            "execute_preview": True,
        },
    )

    assert workflow_response.status_code == 200
    payload = workflow_response.get_json()
    assert payload["ok"] is True

    workflow = payload["workflow"]
    assert workflow["status"] == "preview_ready"

    first_job = workflow["jobs"][0]
    candidate_rows = first_job["input_ref"]["metadata"]["payload"]["candidate_rows"]

    source_backed_rows = [
        row for row in candidate_rows if isinstance(row, dict) and _is_http_url(row.get("source_url"))
    ]
    sports = {row.get("sport") for row in source_backed_rows}

    assert {"boxing", "mma", "kickboxing", "muay_thai"}.issubset(sports)

    event_names_with_matchups = {
        row.get("event_name")
        for row in source_backed_rows
        if isinstance(row.get("event_name"), str)
        and row["event_name"].strip()
        and isinstance(row.get("fighter_a"), str)
        and row["fighter_a"].strip()
        and isinstance(row.get("fighter_b"), str)
        and row["fighter_b"].strip()
    }
    assert len(event_names_with_matchups) >= 4


def test_gate1_dry_run_blocks_non_source_rows_and_preserves_preview_only_no_write(client):
    _, approved_rows = _approved_live_rows_from_runtime_state()
    candidate_rows = list(approved_rows)
    candidate_rows.append(
        {
            "candidate_id": "non_source_control_001",
            "event_name": "Control Event",
            "sport": "mma",
            "fighter_a": "Control A",
            "fighter_b": "Control B",
            "source_backed": False,
            "approval_required": True,
            "preview_only": True,
        }
    )

    token = dict(
        build_three_button_workflow_plan(
            "button1_find_fights",
            LocalAIJobInputRef(ref_type="entity", ref_key="live_feed_population", snapshot_hash="snap_v1"),
        ).gate_approval_token_preview
    )

    gate_response = client.post(
        "/api/local-ai/gate1/save-fights/dry-run-apply-preview",
        json={
            "gate_approval_token_preview": token,
            "candidate_rows": candidate_rows,
        },
    )

    assert gate_response.status_code == 200
    data = gate_response.get_json()

    assert data["preview_only"] is True
    assert data["write_authorized"] is False
    assert data["mutation_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["database_write_performed"] is False

    blocked = set(data.get("blocked", []))
    would_save = set(data.get("would_save", []))
    approved_ids = {row.get("candidate_id") for row in approved_rows if isinstance(row.get("candidate_id"), str)}

    assert "non_source_control_001" in blocked
    assert "non_source_control_001" not in would_save
    assert would_save.issubset(approved_ids)


def test_muay_thai_secondary_confirmation_row_stays_needs_review_and_review_only():
    _, approved_rows = _approved_live_rows_from_runtime_state()
    muay_rows = [row for row in approved_rows if row.get("sport") == "muay_thai"]

    assert muay_rows, "expected at least one muay_thai event row"
    muay = muay_rows[0]

    assert muay.get("source_tier") == "B"
    assert muay.get("requires_secondary_confirmation") is True
    assert muay.get("provenance_status") == "needs_review"
    assert muay.get("ready_state") == "needs_review"
    assert muay.get("queue_save_eligible") is False
    assert muay.get("unsafe_queue_save_blocked") is True

    for matchup in muay.get("matchups", []):
        assert matchup.get("source_backed") is True
        assert matchup.get("button2_readiness_status") == "review_only"

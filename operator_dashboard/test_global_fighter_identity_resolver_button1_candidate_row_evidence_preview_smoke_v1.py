"""Evidence-only smoke proof for Button 1 row identity evidence + Gate 1 preview alignment + canonical reason rendering."""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app
from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef
from operator_dashboard.local_ai_orchestrator_workflow_plan import build_three_button_workflow_plan


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    return resp.data.decode("utf-8")


def _function_body(html: str, function_name: str) -> str:
    pattern = rf"function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{([\s\S]*?)\n\}}"
    match = re.search(pattern, html)
    assert match is not None
    return match.group(1)


def _valid_token(candidate_scope=None):
    ref = LocalAIJobInputRef(ref_type="entity", ref_key="smoke_seed", snapshot_hash="snap_v1")
    plan = build_three_button_workflow_plan("button1_find_fights", ref)
    token = dict(plan.gate_approval_token_preview)
    if candidate_scope is not None:
        token["candidate_scope"] = candidate_scope
    return token


def _candidate_row(candidate_id: str, with_provenance: bool = True):
    row = {
        "candidate_id": candidate_id,
        "fight_name": f"Fight {candidate_id}",
    }
    if with_provenance:
        row["source_url"] = f"https://example.com/{candidate_id}"
    return row


def test_smoke_row_identity_statuses_render_safely(client):
    html = _html(client)
    assert "identity_clear" in html
    assert "identity_needs_review" in html
    assert "identity_conflict" in html
    assert "identity_no_match" in html
    assert "identity_source_missing" in html


def test_smoke_gate1_blocks_identity_conflict_source_missing_ambiguous(client):
    route = "/api/local-ai/gate1/save-fights/dry-run-apply-preview"

    conflict_row = _candidate_row("conflict_row")
    conflict_row["fighter_a_identity_status"] = "identity_conflict"

    source_missing_row = _candidate_row("source_missing_row")
    source_missing_row["fighter_b_identity_status"] = "identity_source_missing"

    ambiguous_row = _candidate_row("ambiguous_row")
    ambiguous_row["fighter_a_identity_status"] = "identity_ambiguous"

    good_row = _candidate_row("good_row")

    resp = client.post(
        route,
        json={
            "gate_approval_token_preview": _valid_token(candidate_scope=["conflict_row", "source_missing_row", "ambiguous_row", "good_row"]),
            "candidate_scope": ["conflict_row", "source_missing_row", "ambiguous_row", "good_row"],
            "candidate_rows": [conflict_row, source_missing_row, ambiguous_row, good_row],
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()

    assert "conflict_row" in data["blocked"]
    assert "source_missing_row" in data["blocked"]
    assert "ambiguous_row" in data["blocked"]
    assert "good_row" in data["would_save"]


def test_smoke_canonical_reason_ordering_is_stable(client):
    html = _html(client)
    helper = _function_body(html, "canonicalizeOperatorIdentityReasonLabels")
    i_conflict = helper.find("Identity conflict")
    i_source = helper.find("Source missing")
    i_ambiguous = helper.find("Ambiguous identity")
    i_manual = helper.find("Manual review required")

    assert i_conflict >= 0 and i_source >= 0 and i_ambiguous >= 0 and i_manual >= 0
    assert i_conflict < i_source < i_ambiguous < i_manual


def test_smoke_duplicate_reasons_are_collapsed(client):
    html = _html(client)
    helper = _function_body(html, "canonicalizeOperatorIdentityReasonLabels")
    assert "out.indexOf(item.label) < 0" in helper


def test_smoke_raw_internal_keys_not_shown(client):
    html = _html(client)
    gate1_render = _function_body(html, "renderButton1Gate1DryRunIdentityAlignment")
    assert "rawReasons.join" not in gate1_render
    assert "JSON.stringify" not in gate1_render
    assert "candidate_matches" not in gate1_render


def test_smoke_no_create_merge_database_controls_exist(client):
    html = _html(client)
    assert "Create Profile" not in html
    assert "Update Profile" not in html
    assert "Merge Profiles" not in html
    assert "Write to Database" not in html
    assert "Write Ranking" not in html


def test_smoke_no_write_behavior_opens(client):
    id_resp = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": {
                "name": "Preview Fighter",
                "source_refs": [{"source_name": "preview", "source_type": "preview"}],
            },
            "known_records": [],
        },
    )
    assert id_resp.status_code == 200
    id_data = id_resp.get_json()
    assert id_data["preview_only"] is True
    assert id_data["profile_create_performed"] is False
    assert id_data["profile_update_performed"] is False
    assert id_data["merge_performed"] is False
    assert id_data["database_write_performed"] is False
    assert id_data["ranking_write_performed"] is False
    assert id_data["learning_apply_performed"] is False
    assert id_data["calibration_write_performed"] is False

    gate1_resp = client.post(
        "/api/local-ai/gate1/save-fights/dry-run-apply-preview",
        json={
            "gate_approval_token_preview": _valid_token(candidate_scope=["good_row"]),
            "candidate_scope": ["good_row"],
            "candidate_rows": [_candidate_row("good_row")],
        },
    )
    assert gate1_resp.status_code == 200
    gate1_data = gate1_resp.get_json()
    assert gate1_data["preview_only"] is True
    assert gate1_data["write_authorized"] is False
    assert gate1_data["mutation_performed"] is False
    assert gate1_data["queue_write_performed"] is False
    assert gate1_data["database_write_performed"] is False


def test_smoke_dashboard_remains_three_buttons_three_gates(client):
    html = _html(client)
    assert html.count('class="btn-card"') == 3
    assert html.count("Operator Gate") == 3

"""
Preview-only tests for Button 1 candidate row identity evidence rendering.

Scope:
- Dashboard JavaScript surface only
- No route changes
- No resolver behavior changes
- No write/mutation behavior
"""

import pytest
from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _dashboard_html(client):
    response = client.get("/")
    assert response.status_code == 200
    return response.data.decode("utf-8")


def test_row_identity_statuses_render_safely(client):
    html = _dashboard_html(client)
    assert "identity_clear" in html
    assert "identity_needs_review" in html
    assert "identity_conflict" in html
    assert "identity_no_match" in html
    assert "identity_source_missing" in html
    assert "Identity: Clear" in html
    assert "Identity: Needs Review" in html
    assert "Identity: Conflict" in html
    assert "Identity: No Match" in html
    assert "Identity: Source Missing" in html


def test_conflict_and_source_missing_block_queue_save_preview(client):
    html = _dashboard_html(client)
    assert "function isIdentityStatusBlockingForQueueSavePreview" in html
    assert "identityStatus === 'identity_conflict'" in html
    assert "identityStatus === 'identity_source_missing'" in html


def test_row_evidence_summary_counts_render(client):
    html = _dashboard_html(client)
    assert "Candidates checked:" in html
    assert "Manual review required:" in html
    assert "Conflicts detected:" in html
    assert "Queue-save preview blocked rows:" in html
    assert "Queue-save preview ready rows:" in html


def test_dashboard_does_not_expose_raw_resolver_internals(client):
    html = _dashboard_html(client)
    assert "JSON.stringify(result)" not in html
    assert "JSON.stringify(identityData)" not in html
    assert "raw resolver payload" not in html
    assert "candidate_matches:" not in html
    assert "evidence:" not in html


def test_dashboard_does_not_expose_write_controls(client):
    html = _dashboard_html(client)
    assert "Create Profile" not in html
    assert "Update Profile" not in html
    assert "Merge Profiles" not in html
    assert "Write Ranking" not in html
    assert "Write to Database" not in html


def test_identity_preview_write_flags_remain_false(client):
    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": {
                "name": "Preview Fighter",
                "source_refs": [{"source_name": "preview", "source_type": "preview"}],
            },
            "known_records": [],
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_normal_dashboard_remains_three_buttons_three_gates(client):
    html = _dashboard_html(client)
    assert html.count('class="btn-card"') == 3
    assert html.count("Operator Gate") == 3

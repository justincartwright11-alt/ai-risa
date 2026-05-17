"""Preview-only dashboard wire tests for Button 1 row identity evidence -> Gate 1 dry-run alignment (v1)."""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app as flask_app


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


def test_template_contains_gate1_dry_run_preview_endpoint_constant(client):
    html = _html(client)
    assert "/api/local-ai/gate1/save-fights/dry-run-apply-preview" in html


def test_template_contains_gate1_dry_run_post_helper(client):
    html = _html(client)
    body = _function_body(html, "postLocalAiGate1DryRunApplyPreview")
    assert "LOCAL_AI_GATE1_DRY_RUN_APPLY_PREVIEW_ENDPOINT" in body
    assert "method: 'POST'" in body


def test_button1_builds_identity_blocking_reasons_for_candidate_rows(client):
    html = _html(client)
    body = _function_body(html, "buildButton1CandidateRowsWithIdentityBlockingReasons")
    assert "identity_blocking_reasons" in body
    assert "fighter_a_identity_status" in body
    assert "fighter_b_identity_status" in body
    assert "identity_ready_for_queue_review" in body


def test_button1_handler_posts_identity_enriched_rows_to_gate1_dry_run(client):
    html = _html(client)
    body = _function_body(html, "handleButton1Click")
    assert "buildButton1CandidateRowsWithIdentityBlockingReasons" in body
    assert "postLocalAiGate1DryRunApplyPreview" in body
    assert "candidate_rows: rowsWithIdentityBlocking" in body


def test_gate1_alignment_render_is_preview_only_evidence(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1DryRunIdentityAlignment")
    assert "Identity-blocked rows" in body
    assert "Rows with identity blockers are held from queue-save preview until reviewed." in body
    assert "Blocked row" in body
    assert "canonicalizeOperatorIdentityReasonLabels" in body
    assert "Profile write disabled: Yes" in body
    assert "Merge disabled: Yes" in body
    assert "Database write disabled: Yes" in body


def test_gate1_alignment_render_does_not_expose_raw_identity_internals(client):
    html = _html(client)
    body = _function_body(html, "renderButton1Gate1DryRunIdentityAlignment")
    assert "candidate_matches" not in body
    assert "incoming_candidate" not in body
    assert "JSON.stringify" not in body
    assert "rawReasons.join" not in body


def test_dashboard_still_has_three_main_buttons_and_three_gates(client):
    html = _html(client)
    assert len(re.findall(r'class=\"btn-main\"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3

"""Template-only tests for reason canonicalization ordering/grouping in Button 1 + Gate 1 preview surfaces (v1)."""

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


def test_template_contains_shared_reason_canonicalization_helper(client):
    html = _html(client)
    body = _function_body(html, "canonicalizeOperatorIdentityReasonLabels")
    assert "Identity conflict" in body
    assert "Source missing" in body
    assert "Ambiguous identity" in body
    assert "Manual review required" in body
    assert "No match - review required" in body


def test_reason_order_is_conflict_then_source_then_ambiguous_then_manual(client):
    html = _html(client)
    body = _function_body(html, "canonicalizeOperatorIdentityReasonLabels")
    i_conflict = body.find("Identity conflict")
    i_source = body.find("Source missing")
    i_ambiguous = body.find("Ambiguous identity")
    i_manual = body.find("Manual review required")
    assert i_conflict >= 0 and i_source >= 0 and i_ambiguous >= 0 and i_manual >= 0
    assert i_conflict < i_source < i_ambiguous < i_manual


def test_duplicate_reasons_are_collapsed(client):
    html = _html(client)
    body = _function_body(html, "canonicalizeOperatorIdentityReasonLabels")
    assert "out.indexOf(item.label) < 0" in body


def test_button1_and_gate1_both_use_canonicalization_helper(client):
    html = _html(client)
    b1_body = _function_body(html, "buildButton1RowEvidenceSummaryHtml")
    gate1_body = _function_body(html, "renderButton1Gate1DryRunIdentityAlignment")
    assert "canonicalizeOperatorIdentityReasonLabels" in b1_body
    assert "canonicalizeOperatorIdentityReasonLabels" in gate1_body


def test_raw_internal_reason_keys_are_not_rendered_to_operator(client):
    html = _html(client)
    gate1_body = _function_body(html, "renderButton1Gate1DryRunIdentityAlignment")
    assert "rawReasons.join" not in gate1_body
    assert "identity_status_blocked:" not in gate1_body


def test_dashboard_remains_three_buttons_three_gates(client):
    html = _html(client)
    assert len(re.findall(r'class=\"btn-main\"', html)) == 3
    assert len(re.findall(r'btn-gate', html)) == 3

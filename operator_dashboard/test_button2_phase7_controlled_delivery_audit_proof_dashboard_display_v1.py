import os
from pathlib import Path

import pytest

# Allow imports from workspace root
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture
def index_source_text():
    template_path = Path(__file__).resolve().parent / 'templates' / 'index.html'
    return template_path.read_text(encoding='utf-8')


def test_dashboard_main_route_uses_root(client):
    response = client.get('/')
    assert response.status_code == 200


def test_template_contains_evidence_display_section(index_source_text):
    assert 'Controlled Delivery Audit / Proof Evidence' in index_source_text
    assert 'id="b2-cd-evidence-audit-record"' in index_source_text
    assert 'id="b2-cd-evidence-proof-record"' in index_source_text
    assert 'id="b2-cd-evidence-receipt-record"' in index_source_text
    assert 'id="b2-cd-evidence-rollback-record"' in index_source_text


def test_template_contains_required_evidence_labels(index_source_text):
    required_labels = [
        'audit_record',
        'proof_of_delivery_record',
        'delivery_receipt_record',
        'rollback_void_pointer',
        'operation_id',
        'audit_id',
        'proof_id',
        'receipt_id',
        'rollback_id',
    ]
    for label in required_labels:
        assert label in index_source_text


def test_template_contains_required_evidence_state_fields(index_source_text):
    required_state_labels = [
        'report_id',
        'report_status',
        'customer_identity_present',
        'delivery_target_present',
        'delivery_channel',
        'delivery_mode',
        'operator_approval',
        'generated_at or timestamp',
    ]
    for label in required_state_labels:
        assert label in index_source_text


def test_template_contains_safety_flags_snapshot(index_source_text):
    assert 'safety_flags snapshot' in index_source_text
    assert 'id="b2-cd-evidence-safety-flags-snapshot"' in index_source_text


def test_template_contains_scaffold_channel_labels(index_source_text):
    assert 'email_scaffold: scaffold only, no email sent' in index_source_text
    assert 'api_scaffold: scaffold only, no external API called' in index_source_text
    assert 'manual_export: operator-approved controlled manual export' in index_source_text


def test_template_renders_hardened_evidence_objects_from_action_response(index_source_text):
    assert 'const auditRecord = response.audit_record;' in index_source_text
    assert 'const proofRecord = response.proof_of_delivery_record;' in index_source_text
    assert 'const receiptRecord = response.delivery_receipt_record;' in index_source_text
    assert 'const rollbackRecord = response.rollback_void_pointer;' in index_source_text


def test_denied_action_clears_completed_evidence_fields(index_source_text):
    assert 'if (response.error || !response.controlled_delivery_action)' in index_source_text
    assert 'clearEvidenceDisplay();' in index_source_text
    assert "setField('b2-cd-action-status', 'DENIED');" in index_source_text


def test_template_preserves_preview_and_action_endpoints(index_source_text):
    assert '/api/button2/controlled-delivery/preview' in index_source_text
    assert '/api/button2/controlled-delivery/action' in index_source_text


def test_dashboard_still_has_three_main_buttons_only(index_source_text):
    assert 'id="b1-btn"' in index_source_text
    assert 'id="b2-btn"' in index_source_text
    assert 'id="b3-btn"' in index_source_text
    assert 'id="b4-btn"' not in index_source_text


def test_template_does_not_expose_uncontrolled_send_or_deliver_now(index_source_text):
    assert 'onclick="sendUncontrolled' not in index_source_text
    assert 'onclick="deliverNow' not in index_source_text
    assert 'id="uncontrolled-send-btn' not in index_source_text
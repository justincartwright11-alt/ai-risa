import os
import sys
import pytest

# Ensure the app can find the operator_dashboard module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from operator_dashboard.app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_action_endpoint_exists(client):
    response = client.post('/api/button2/controlled-delivery/action', json={})
    assert response.status_code in [200, 400]

def test_valid_manual_export_returns_hardened_evidence(client):
    valid_payload = {
        'report_id': 'test-report-123',
        'report_status': 'customer_ready',
        'customer_identity': 'test-customer',
        'delivery_target': 'test-target',
        'delivery_channel': 'manual_export',
        'operator_approval': True,
        'delivery_evidence': 'test-evidence',
        'audit_record': 'test-audit',
        'proof_of_delivery': 'test-proof',
        'rollback_pointer': 'test-rollback'
    }
    response = client.post('/api/button2/controlled-delivery/action', json=valid_payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['controlled_delivery_action'] is True
    assert 'audit_record' in data
    assert 'proof_of_delivery_record' in data
    assert 'delivery_receipt_record' in data
    assert 'rollback_void_pointer' in data
    assert data['audit_record']['operation_id'] == data['proof_of_delivery_record']['operation_id']
    assert data['audit_record']['operation_id'] == data['delivery_receipt_record']['operation_id']
    assert data['audit_record']['operation_id'] == data['rollback_void_pointer']['operation_id']

def test_denied_action_does_not_create_evidence(client):
    invalid_payload = {
        'report_id': 'test-report-123',
        'report_status': 'draft',
        'customer_identity': 'test-customer',
        'delivery_target': 'test-target',
        'delivery_channel': 'manual_export',
        'operator_approval': False,
        'delivery_evidence': 'test-evidence',
        'audit_record': 'test-audit',
        'proof_of_delivery': 'test-proof',
        'rollback_pointer': 'test-rollback'
    }
    response = client.post('/api/button2/controlled-delivery/action', json=invalid_payload)
    assert response.status_code == 400
    data = response.get_json()
    assert data['controlled_delivery_action'] is False
    assert 'audit_record' not in data
    assert 'proof_of_delivery_record' not in data
    assert 'delivery_receipt_record' not in data
    assert 'rollback_void_pointer' not in data
import pytest
from operator_dashboard import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_missing_fields(client):
    response = client.post('/api/button2/controlled-delivery/preview', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert not data['controlled_delivery_preview']
    assert not data['delivery_ready']
    assert 'missing_required_fields' in data['denial_reason']
    assert 'report_id' in data['denial_reasons']

def test_operator_approval_required(client):
    payload = {
        'report_id': '123',
        'report_status': 'customer_ready',
        'customer_identity': 'customer_1',
        'delivery_target': 'target_1',
        'delivery_channel': 'email',
        'delivery_evidence': 'evidence_1',
        'audit_record': 'audit_1',
        'proof_of_delivery': 'proof_1',
        'rollback_pointer': 'rollback_1'
    }
    response = client.post('/api/button2/controlled-delivery/preview', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'operator_approval_required' in data['denial_reasons']

def test_valid_preview(client):
    payload = {
        'report_id': '123',
        'report_status': 'customer_ready',
        'customer_identity': 'customer_1',
        'delivery_target': 'target_1',
        'delivery_channel': 'email',
        'operator_approval': True,
        'delivery_evidence': 'evidence_1',
        'audit_record': 'audit_1',
        'proof_of_delivery': 'proof_1',
        'rollback_pointer': 'rollback_1'
    }
    response = client.post('/api/button2/controlled-delivery/preview', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['controlled_delivery_preview']
    assert data['delivery_ready']
    assert data['safety_flags']['live_delivery_performed'] is False
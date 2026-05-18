import pytest
import sys
import os

# Allow imports from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestControlledDeliveryRouteBinding:
    """Verify that the /api/button2/controlled-delivery/preview endpoint is properly bound."""

    def test_endpoint_exists_and_returns_json(self, client):
        """Verify endpoint exists and returns JSON."""
        payload = {
            'report_id': 'test_123',
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
        assert data is not None
        assert isinstance(data, dict)
        assert 'controlled_delivery_preview' in data

    def test_missing_approval_denied(self, client):
        """Verify missing operator_approval is denied."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'customer_ready',
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'email',
            'operator_approval': False,
            'delivery_evidence': 'evidence_1',
            'audit_record': 'audit_1',
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        response = client.post('/api/button2/controlled-delivery/preview', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert not data['delivery_ready']
        assert 'operator_approval_required' in data['denial_reasons']

    def test_draft_report_blocked(self, client):
        """Verify draft report is blocked."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'draft',
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
        assert response.status_code == 400
        data = response.get_json()
        assert not data['delivery_ready']
        assert 'draft_internal_report_blocked' in data['denial_reasons']

    def test_fully_valid_preview_ready_no_live_delivery(self, client):
        """Verify fully valid preview returns delivery_ready=true with no live delivery."""
        payload = {
            'report_id': 'test_123',
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
        assert data['safety_flags']['customer_delivery_performed'] is False
        assert data['safety_flags']['email_send_performed'] is False
        assert data['safety_flags']['database_write_performed'] is False

    def test_all_safety_flags_false(self, client):
        """Verify all safety flags remain false in all cases."""
        payload = {
            'report_id': 'test_123',
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
        
        safety_flags = data['safety_flags']
        assert safety_flags['live_delivery_performed'] is False
        assert safety_flags['customer_delivery_performed'] is False
        assert safety_flags['email_send_performed'] is False
        assert safety_flags['database_write_performed'] is False
        assert safety_flags['queue_write_performed'] is False
        assert safety_flags['ledger_write_performed'] is False
        assert safety_flags['learning_apply_performed'] is False
        assert safety_flags['calibration_write_performed'] is False
        assert safety_flags['button1_mutation_performed'] is False
        assert safety_flags['button3_mutation_performed'] is False

    def test_button2_main_dashboard_route_regression(self, client):
        """Verify existing Button 2 main dashboard route still works."""
        response = client.get('/')
        assert response.status_code == 200

    def test_button2_advanced_dashboard_route_regression(self, client):
        """Verify existing advanced dashboard route still works."""
        response = client.get('/advanced-dashboard')
        assert response.status_code == 200

    def test_button2_generate_report_route_regression(self, client):
        """Verify existing Button 2 generate-report route still rejects properly."""
        payload = {'operator_approved': False}
        response = client.post('/api/operator/button2/generate-report', json=payload)
        # Should be 403 (forbidden) for missing approval, not 404 (route not found)
        assert response.status_code in [403, 400]
        data = response.get_json()
        assert data is not None
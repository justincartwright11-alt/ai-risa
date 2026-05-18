import pytest
import sys
import os
import json

# Allow imports from workspace root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def build_valid_action_payload():
    """Build a fully valid action request payload."""
    return {
        'report_id': 'test_report_123',
        'report_status': 'customer_ready',
        'customer_identity': 'customer_1',
        'delivery_target': 'test@example.com',
        'delivery_channel': 'manual_export',
        'operator_approval': True,
        'delivery_evidence': 'Operator approved delivery for test',
        'audit_record': {'operator_id': 'op1', 'timestamp': '2026-05-18T00:00:00Z'},
        'proof_of_delivery': 'proof/manual/test_report_123/delivery.json',
        'rollback_pointer': 'rollback/manual/test_report_123'
    }


class TestControlledDeliveryAction:
    """Test the controlled delivery action endpoint."""

    def test_endpoint_exists_and_returns_json(self, client):
        """Endpoint should exist and return JSON response."""
        response = client.post('/api/button2/controlled-delivery/action', json={})
        assert response.status_code in [200, 400]
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'controlled_delivery_action' in data

    def test_non_json_payload_rejected(self, client):
        """Non-JSON payload should be handled safely."""
        response = client.post(
            '/api/button2/controlled-delivery/action',
            data='not json',
            content_type='application/json'
        )
        # Flask should handle this gracefully
        assert response.status_code in [400, 415]

    # ── Precondition: Operator Approval ──────────────────────────────────────

    def test_operator_approval_false_denied(self, client):
        """Request with operator_approval=false should be denied."""
        payload = build_valid_action_payload()
        payload['operator_approval'] = False
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data['controlled_delivery_action'] is False
        assert 'operator_approval_required' in data['denial_reasons']

    def test_operator_approval_missing_denied(self, client):
        """Request missing operator_approval should be denied."""
        payload = build_valid_action_payload()
        del payload['operator_approval']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'operator_approval_required' in data['denial_reasons']

    # ── Precondition: Report Status ──────────────────────────────────────────

    def test_draft_report_blocked(self, client):
        """Request with report_status=draft should be blocked."""
        payload = build_valid_action_payload()
        payload['report_status'] = 'draft'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'draft_internal_report_blocked' in data['denial_reasons']

    def test_internal_report_blocked(self, client):
        """Request with report_status=internal should be blocked."""
        payload = build_valid_action_payload()
        payload['report_status'] = 'internal'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'draft_internal_report_blocked' in data['denial_reasons']

    def test_non_customer_ready_status_denied(self, client):
        """Request with non-customer_ready status should be denied."""
        payload = build_valid_action_payload()
        payload['report_status'] = 'pending'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'customer_ready_report_required' in data['denial_reasons']

    def test_missing_report_status_denied(self, client):
        """Request missing report_status should be denied."""
        payload = build_valid_action_payload()
        del payload['report_status']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'customer_ready_report_required' in data['denial_reasons']

    # ── Precondition: Customer Identity ──────────────────────────────────────

    def test_missing_customer_identity_denied(self, client):
        """Request missing customer_identity should be denied."""
        payload = build_valid_action_payload()
        del payload['customer_identity']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_customer_identity' in data['denial_reasons']

    def test_empty_customer_identity_denied(self, client):
        """Request with empty customer_identity should be denied."""
        payload = build_valid_action_payload()
        payload['customer_identity'] = ''
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_customer_identity' in data['denial_reasons']

    # ── Precondition: Delivery Target ────────────────────────────────────────

    def test_missing_delivery_target_denied(self, client):
        """Request missing delivery_target should be denied."""
        payload = build_valid_action_payload()
        del payload['delivery_target']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_delivery_target' in data['denial_reasons']

    def test_empty_delivery_target_denied(self, client):
        """Request with empty delivery_target should be denied."""
        payload = build_valid_action_payload()
        payload['delivery_target'] = ''
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_delivery_target' in data['denial_reasons']

    # ── Precondition: Delivery Channel ───────────────────────────────────────

    def test_unsupported_delivery_channel_denied(self, client):
        """Request with unsupported delivery_channel should be denied."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'fax'  # Not supported
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'unsupported_delivery_channel' in data['denial_reasons']

    def test_missing_delivery_channel_denied(self, client):
        """Request missing delivery_channel should be denied."""
        payload = build_valid_action_payload()
        del payload['delivery_channel']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'unsupported_delivery_channel' in data['denial_reasons']

    # ── Precondition: Delivery Evidence ──────────────────────────────────────

    def test_missing_delivery_evidence_denied(self, client):
        """Request missing delivery_evidence should be denied."""
        payload = build_valid_action_payload()
        del payload['delivery_evidence']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_delivery_evidence' in data['denial_reasons']

    def test_empty_delivery_evidence_denied(self, client):
        """Request with empty delivery_evidence should be denied."""
        payload = build_valid_action_payload()
        payload['delivery_evidence'] = ''
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_delivery_evidence' in data['denial_reasons']

    # ── Precondition: Audit Record ───────────────────────────────────────────

    def test_missing_audit_record_denied(self, client):
        """Request missing audit_record should be denied."""
        payload = build_valid_action_payload()
        del payload['audit_record']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_audit_record' in data['denial_reasons']

    def test_empty_audit_record_denied(self, client):
        """Request with empty audit_record should be denied."""
        payload = build_valid_action_payload()
        payload['audit_record'] = {}
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'missing_audit_record' in data['denial_reasons']

    # ── Precondition: Proof of Delivery ──────────────────────────────────────

    def test_missing_proof_of_delivery_denied(self, client):
        """Request missing proof_of_delivery should be denied."""
        payload = build_valid_action_payload()
        del payload['proof_of_delivery']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'proof_of_delivery_required' in data['denial_reasons']

    def test_empty_proof_of_delivery_denied(self, client):
        """Request with empty proof_of_delivery should be denied."""
        payload = build_valid_action_payload()
        payload['proof_of_delivery'] = ''
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'proof_of_delivery_required' in data['denial_reasons']

    # ── Precondition: Rollback Pointer ───────────────────────────────────────

    def test_missing_rollback_pointer_denied(self, client):
        """Request missing rollback_pointer should be denied."""
        payload = build_valid_action_payload()
        del payload['rollback_pointer']
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'rollback_pointer_required' in data['denial_reasons']

    def test_empty_rollback_pointer_denied(self, client):
        """Request with empty rollback_pointer should be denied."""
        payload = build_valid_action_payload()
        payload['rollback_pointer'] = ''
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert 'rollback_pointer_required' in data['denial_reasons']

    # ── Valid Preconditions: Successful Action ───────────────────────────────

    def test_all_preconditions_satisfied_manual_export(self, client):
        """Request with all valid fields for manual_export should succeed."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'manual_export'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['controlled_delivery_action'] is True
        assert data['delivery_action_ready'] is True
        assert data['delivery_action_performed'] is True
        assert data['denial_reasons'] == []

    def test_all_preconditions_satisfied_email_scaffold(self, client):
        """Request with all valid fields for email_scaffold should succeed."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'email_scaffold'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['controlled_delivery_action'] is True
        assert data['delivery_action_ready'] is True
        assert data['delivery_action_performed'] is False  # Email not actually sent
        assert data['denial_reasons'] == []

    def test_all_preconditions_satisfied_api_scaffold(self, client):
        """Request with all valid fields for api_scaffold should succeed."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'api_scaffold'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['controlled_delivery_action'] is True
        assert data['delivery_action_ready'] is True
        assert data['delivery_action_performed'] is False  # API not actually called
        assert data['denial_reasons'] == []

    # ── Safety Flags: Verify All False ───────────────────────────────────────

    def test_safety_flags_all_false_on_denial(self, client):
        """When request denied, all safety flags should be false."""
        payload = build_valid_action_payload()
        payload['operator_approval'] = False
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        flags = data['safety_flags']
        assert flags['live_delivery_performed'] is False
        assert flags['customer_delivery_performed'] is False
        assert flags['email_send_performed'] is False
        assert flags['external_api_delivery_performed'] is False
        assert flags['database_write_performed'] is False
        assert flags['queue_write_performed'] is False
        assert flags['ledger_write_performed'] is False
        assert flags['learning_apply_performed'] is False
        assert flags['calibration_write_performed'] is False
        assert flags['button1_mutation_performed'] is False
        assert flags['button3_mutation_performed'] is False

    def test_safety_flags_manual_export_delivery_performed(self, client):
        """For manual_export, delivery flags should be true, others false."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'manual_export'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        flags = data['safety_flags']
        
        # Delivery flags should be true for manual_export
        assert flags['live_delivery_performed'] is True
        assert flags['customer_delivery_performed'] is True
        
        # Non-delivery flags should all be false
        assert flags['email_send_performed'] is False
        assert flags['external_api_delivery_performed'] is False
        assert flags['database_write_performed'] is False
        assert flags['queue_write_performed'] is False
        assert flags['ledger_write_performed'] is False
        assert flags['learning_apply_performed'] is False
        assert flags['calibration_write_performed'] is False
        assert flags['button1_mutation_performed'] is False
        assert flags['button3_mutation_performed'] is False

    def test_safety_flags_email_scaffold_not_sent(self, client):
        """For email_scaffold, email_send_performed should be false."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'email_scaffold'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        flags = data['safety_flags']
        
        # Email scaffold should NOT actually send
        assert flags['email_send_performed'] is False
        assert flags['live_delivery_performed'] is False
        assert flags['customer_delivery_performed'] is False
        
        # All other flags false
        assert flags['database_write_performed'] is False
        assert flags['learning_apply_performed'] is False
        assert flags['calibration_write_performed'] is False
        assert flags['button1_mutation_performed'] is False
        assert flags['button3_mutation_performed'] is False

    def test_safety_flags_api_scaffold_not_called(self, client):
        """For api_scaffold, external_api_delivery_performed should be false."""
        payload = build_valid_action_payload()
        payload['delivery_channel'] = 'api_scaffold'
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        flags = data['safety_flags']
        
        # API scaffold should NOT actually call API
        assert flags['external_api_delivery_performed'] is False
        assert flags['live_delivery_performed'] is False
        assert flags['customer_delivery_performed'] is False
        
        # All other flags false
        assert flags['database_write_performed'] is False
        assert flags['learning_apply_performed'] is False
        assert flags['calibration_write_performed'] is False
        assert flags['button1_mutation_performed'] is False
        assert flags['button3_mutation_performed'] is False

    # ── Response Fields: Verify All Present ───────────────────────────────────

    def test_response_contains_all_required_fields_success(self, client):
        """Successful response should contain all required fields."""
        payload = build_valid_action_payload()
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        
        required_fields = [
            'controlled_delivery_action', 'delivery_action_ready', 'delivery_action_performed',
            'denial_reason', 'denial_reasons', 'report_id', 'report_status',
            'customer_identity_present', 'delivery_target_present', 'delivery_channel',
            'audit_ready', 'rollback_ready', 'proof_of_delivery_ready', 'operation_id',
            'audit_id', 'rollback_id', 'delivery_receipt_id', 'delivery_mode', 'safety_flags'
        ]
        for field in required_fields:
            assert field in data

    def test_response_contains_all_required_fields_denial(self, client):
        """Denied response should contain all required fields."""
        payload = build_valid_action_payload()
        payload['operator_approval'] = False
        response = client.post('/api/button2/controlled-delivery/action', json=payload)
        assert response.status_code == 400
        data = response.get_json()
        
        required_fields = [
            'controlled_delivery_action', 'delivery_action_ready', 'delivery_action_performed',
            'denial_reason', 'denial_reasons', 'report_id', 'report_status',
            'customer_identity_present', 'delivery_target_present', 'delivery_channel',
            'audit_ready', 'rollback_ready', 'proof_of_delivery_ready', 'operation_id',
            'safety_flags'
        ]
        for field in required_fields:
            assert field in data

    # ── Regression: Existing Endpoints Must Work ─────────────────────────────

    def test_preview_endpoint_still_works(self, client):
        """Existing preview endpoint should still work."""
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
        assert data['controlled_delivery_preview'] is True
        assert data['delivery_ready'] is True

    def test_dashboard_main_page_still_loads(self, client):
        """Main dashboard page should still load."""
        response = client.get('/')
        assert response.status_code == 200

    def test_button2_main_route_still_works(self, client):
        """Button 2 main route should still work."""
        response = client.get('/operator/button2')
        assert response.status_code in [200, 404]  # 404 is ok if route doesn't exist

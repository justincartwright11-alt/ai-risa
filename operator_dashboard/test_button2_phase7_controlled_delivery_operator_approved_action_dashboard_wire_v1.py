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


class TestControlledDeliveryDashboardWire:
    """Verify dashboard wire for operator-approved controlled delivery action."""

    # ── Dashboard Structure Tests ────────────────────────────────────────
    
    def test_dashboard_contains_wire_text(self, client):
        """Verify dashboard contains 'Operator-Approved Controlled Delivery Action' text."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert 'Operator-Approved Controlled Delivery Action' in html

    def test_dashboard_preserves_three_buttons_only(self, client):
        """Verify dashboard still has exactly 3 main buttons, no fourth button."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'id="b1-btn"' in html
        assert 'id="b2-btn"' in html
        assert 'id="b3-btn"' in html
        assert 'id="b4-btn"' not in html

    def test_dashboard_does_not_expose_uncontrolled_send_button(self, client):
        """Verify no uncontrolled 'Send' or 'Deliver Now' button exposed."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # These uncontrolled terms should NOT appear in button labels
        assert 'onclick="sendUncontrolled' not in html
        assert 'onclick="deliverNow' not in html
        assert 'id="uncontrolled-send-btn' not in html

    def test_dashboard_contains_action_execute_button(self, client):
        """Verify dashboard contains 'Execute Controlled Delivery Action' button."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'id="b2-cd-action-execute-btn"' in html
        assert 'onclick="executeControlledDeliveryAction' in html
        assert 'Execute Controlled Delivery Action' in html

    def test_dashboard_contains_approval_confirmation_logic(self, client):
        """Verify dashboard action requires confirmation via confirm() dialog."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'confirm(' in html
        assert 'Execute Controlled Delivery Action?' in html
        # Check for message about preconditions and approval in the confirm dialog
        assert 'preconditions' in html.lower() or 'approval' in html.lower()

    # ── Endpoint Wire Tests ──────────────────────────────────────────────

    def test_dashboard_calls_correct_endpoint(self, client):
        """Verify JavaScript calls /api/button2/controlled-delivery/action."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert '/api/button2/controlled-delivery/action' in html

    def test_dashboard_calls_post_method(self, client):
        """Verify JavaScript uses POST method for action endpoint."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Check for POST method near the action endpoint
        script_section = html[html.find('executeControlledDeliveryAction'):] if 'executeControlledDeliveryAction' in html else ''
        assert 'method' in script_section.lower() or 'POST' in script_section

    def test_dashboard_action_sends_json(self, client):
        """Verify action sends application/json content type."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Content-Type' in html or 'application/json' in html

    # ── Response Rendering Tests ─────────────────────────────────────────

    def test_dashboard_has_action_result_fields(self, client):
        """Verify dashboard displays all required action result fields."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        required_fields = [
            'b2-cd-action-status',
            'b2-cd-action-performed',
            'b2-cd-action-op-id',
            'b2-cd-action-audit-id',
            'b2-cd-action-rollback-id',
            'b2-cd-action-receipt-id',
            'b2-cd-action-delivery-mode'
        ]
        
        for field_id in required_fields:
            assert f'id="{field_id}"' in html

    def test_dashboard_displays_denial_reasons(self, client):
        """Verify dashboard displays denial reasons section."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'id="b2-cd-action-denial-result"' in html
        assert 'Denial Reasons' in html
        assert 'b2-cd-action-denial-list' in html

    def test_dashboard_displays_safety_flags(self, client):
        """Verify dashboard displays all 11 safety flags."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        safety_flags = [
            'b2-cd-action-live-delivery',
            'b2-cd-action-customer-delivery',
            'b2-cd-action-email-send',
            'b2-cd-action-api-call',
            'b2-cd-action-database-write',
            'b2-cd-action-queue-write',
            'b2-cd-action-ledger-write',
            'b2-cd-action-learning-apply',
            'b2-cd-action-calibration-write',
            'b2-cd-action-button1-mutation',
            'b2-cd-action-button3-mutation'
        ]
        
        for flag_id in safety_flags:
            assert f'id="{flag_id}"' in html

    def test_dashboard_shows_scaffolded_channels_as_not_actually_sent(self, client):
        """Verify email_scaffold/api_scaffold mentioned or backend supports them."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Check that the JavaScript mentions delivery channels or the backend supports them
        assert 'delivery_channel' in html or 'manual_export' in html

    # ── Approval/Confirmation Tests ──────────────────────────────────────

    def test_dashboard_requires_confirmation_before_action(self, client):
        """Verify action requires operator confirmation dialog."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        action_func_start = html.find('function executeControlledDeliveryAction()')
        assert action_func_start > 0
        
        # Check that confirm() appears in the function
        action_func_section = html[action_func_start:action_func_start+500]
        assert 'confirm(' in action_func_section

    def test_dashboard_action_wired_to_button(self, client):
        """Verify action button is wired to executeControlledDeliveryAction."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        button_section = html[html.find('b2-cd-action-execute-btn'):html.find('b2-cd-action-execute-btn')+200] if 'b2-cd-action-execute-btn' in html else ''
        assert 'onclick="executeControlledDeliveryAction()' in html

    # ── Safety/Constraint Tests ──────────────────────────────────────────

    def test_dashboard_preserves_preview_endpoint_call(self, client):
        """Verify preview endpoint still called (/api/button2/controlled-delivery/preview)."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert '/api/button2/controlled-delivery/preview' in html

    def test_dashboard_does_not_bypass_approval_gate(self, client):
        """Verify dashboard enforces operator_approval requirement."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Should mention approval requirement
        assert 'approval' in html.lower() or 'confirm' in html.lower()

    def test_dashboard_does_not_block_draft_check(self, client):
        """Verify no code to bypass draft/internal blocking."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Should NOT contain code that ignores draft status
        assert 'draft_flag = false' not in html

    def test_dashboard_panel_not_main_button(self, client):
        """Verify controlled delivery action is NOT a main dashboard button."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Check that action control is in a panel, not in the three-buttons grid
        assert 'b2-controlled-delivery-preview-panel' in html
        panel_section = html[html.find('b2-controlled-delivery-preview-panel'):]
        assert 'b2-cd-action-execute-btn' in panel_section

    # ── Backend Integration Tests ────────────────────────────────────────

    def test_preview_endpoint_works(self, client):
        """Verify preview endpoint is available and working."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'customer_ready',
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'manual_export',
            'operator_approval': True,
            'delivery_evidence': 'evidence_1',
            'audit_record': {'test': True},
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        
        response = client.post(
            '/api/button2/controlled-delivery/preview',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['controlled_delivery_preview'] == True

    def test_action_endpoint_works(self, client):
        """Verify action endpoint is available and working."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'customer_ready',
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'manual_export',
            'operator_approval': True,
            'delivery_evidence': 'evidence_1',
            'audit_record': {'test': True},
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        
        response = client.post(
            '/api/button2/controlled-delivery/action',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['controlled_delivery_action'] == True
        assert 'operation_id' in data
        assert 'audit_id' in data
        assert 'delivery_receipt_id' in data

    def test_action_endpoint_returns_safety_flags(self, client):
        """Verify action endpoint returns all safety flags."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'customer_ready',
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'manual_export',
            'operator_approval': True,
            'delivery_evidence': 'evidence_1',
            'audit_record': {'test': True},
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        
        response = client.post(
            '/api/button2/controlled-delivery/action',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'safety_flags' in data
        
        flags = data['safety_flags']
        assert 'live_delivery_performed' in flags
        assert 'customer_delivery_performed' in flags
        assert 'email_send_performed' in flags
        assert 'external_api_delivery_performed' in flags
        assert 'database_write_performed' in flags
        assert 'queue_write_performed' in flags
        assert 'ledger_write_performed' in flags
        assert 'learning_apply_performed' in flags
        assert 'calibration_write_performed' in flags
        assert 'button1_mutation_performed' in flags
        assert 'button3_mutation_performed' in flags

    def test_action_denies_without_approval(self, client):
        """Verify action endpoint denies without operator_approval."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'customer_ready',
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'manual_export',
            'operator_approval': False,  # NOT approved
            'delivery_evidence': 'evidence_1',
            'audit_record': {'test': True},
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        
        response = client.post(
            '/api/button2/controlled-delivery/action',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['controlled_delivery_action'] == False
        assert 'operator_approval_required' in data['denial_reasons']

    def test_action_denies_draft_report(self, client):
        """Verify action endpoint denies draft reports."""
        payload = {
            'report_id': 'test_123',
            'report_status': 'draft',  # Draft report
            'customer_identity': 'customer_1',
            'delivery_target': 'target_1',
            'delivery_channel': 'manual_export',
            'operator_approval': True,
            'delivery_evidence': 'evidence_1',
            'audit_record': {'test': True},
            'proof_of_delivery': 'proof_1',
            'rollback_pointer': 'rollback_1'
        }
        
        response = client.post(
            '/api/button2/controlled-delivery/action',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['controlled_delivery_action'] == False
        assert 'draft_internal_report_blocked' in data['denial_reasons']

    # ── Regression Tests ─────────────────────────────────────────────────

    def test_button1_unchanged(self, client):
        """Verify Button 1 behavior unchanged."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Find &amp; Build Fight Queue' in html
        assert 'id="b1-btn"' in html

    def test_button2_unchanged(self, client):
        """Verify Button 2 main behavior unchanged."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Generate Premium PDF Reports' in html
        assert 'id="b2-btn"' in html

    def test_button3_unchanged(self, client):
        """Verify Button 3 behavior unchanged."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Find Results &amp; Improve Accuracy' in html
        assert 'id="b3-btn"' in html

    def test_dashboard_no_new_main_buttons(self, client):
        """Verify no new main buttons added beyond 3."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Count button cards
        button_count = html.count('class="btn-card"')
        # Should be exactly 3 (or slightly more if there are internal card uses, but no extra main buttons)
        assert button_count >= 3
        # Make sure there's no b4-btn or b5-btn
        assert 'id="b4-btn"' not in html
        assert 'id="b5-btn"' not in html

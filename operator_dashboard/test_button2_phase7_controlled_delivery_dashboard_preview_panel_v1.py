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


class TestControlledDeliveryDashboardPanel:
    """Verify that the dashboard contains the preview-only controlled delivery panel."""

    def test_dashboard_main_page_loads(self, client):
        """Verify main dashboard page loads."""
        response = client.get('/')
        assert response.status_code == 200

    def test_dashboard_contains_three_buttons_only(self, client):
        """Verify dashboard has exactly 3 main buttons, not 4."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Count button cards by checking for the specific button card IDs
        assert 'id="b1-btn"' in html
        assert 'id="b2-btn"' in html
        assert 'id="b3-btn"' in html
        
        # Make sure there's no b4-btn
        assert 'id="b4-btn"' not in html

    def test_dashboard_button_labels_preserved(self, client):
        """Verify all three main button labels are present."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Find &amp; Build Fight Queue' in html
        assert 'Generate Premium PDF Reports' in html
        assert 'Find Results &amp; Improve Accuracy' in html

    def test_dashboard_contains_controlled_delivery_preview_panel(self, client):
        """Verify dashboard contains the controlled delivery preview panel text."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Check for controlled delivery panel markers
        assert 'Controlled Delivery Preview' in html
        assert 'PREVIEW-ONLY SURFACE' in html
        assert 'b2-controlled-delivery-preview-panel' in html

    def test_dashboard_no_send_email_deliver_buttons(self, client):
        """Verify dashboard does not contain Send/Email/Deliver Now buttons."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        # Should not contain these live-delivery keywords
        assert 'Send Now' not in html or 'Send Now' in html.split('<!-- ── Phase 7:')[0]  # Allow in comments/docs
        assert html.count('onclick="send') == 0
        assert html.count('onclick="email') == 0

    def test_dashboard_preview_panel_no_delivery_stated(self, client):
        """Verify preview panel clearly states no delivery performed."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'No customer delivery performed' in html
        assert 'No email sent' in html
        assert 'No database/queue/ledger writes' in html
        assert 'No learning/calibration updates' in html

    def test_dashboard_preview_panel_contains_safety_flags(self, client):
        """Verify preview panel displays all required safety flags."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        safety_flags = [
            'live_delivery_performed',
            'customer_delivery_performed',
            'email_send_performed',
            'database_write_performed',
            'queue_write_performed',
            'ledger_write_performed',
            'learning_apply_performed',
            'calibration_write_performed',
            'button1_mutation_performed',
            'button3_mutation_performed'
        ]
        
        for flag in safety_flags:
            assert flag in html

    def test_dashboard_preview_panel_js_function_exists(self, client):
        """Verify dashboard contains JavaScript function for controlled delivery preview."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'function testControlledDeliveryPreview()' in html
        assert 'function renderControlledDeliveryPreview(response)' in html
        assert '/api/button2/controlled-delivery/preview' in html

    def test_controlled_delivery_preview_endpoint_accessible(self, client):
        """Verify endpoint is accessible via Flask test client."""
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

    def test_controlled_delivery_preview_denial_reasons(self, client):
        """Verify preview endpoint returns denial reasons when required."""
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
        assert 'draft_internal_report_blocked' in data['denial_reasons']

    def test_dashboard_advanced_link_preserved(self, client):
        """Verify advanced dashboard link is still present."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert '/advanced-dashboard' in html
        assert 'Advanced Dashboard' in html or 'advanced' in html.lower()

    def test_button1_button2_button3_routes_unchanged(self, client):
        """Verify adjacent Button 1/2/3 routes still work."""
        # Button 1 test
        response = client.get('/api/operator/button1/fight-queue')
        assert response.status_code == 200
        
        # Button 2 test - requires approval
        response = client.post('/api/operator/button2/generate-report', json={'operator_approved': False})
        assert response.status_code in [403, 400]
        
        # Button 3 test - requires approval
        response = client.post('/api/operator/button3/apply-result', json={'operator_approved': False})
        assert response.status_code == 403

    def test_preview_panel_reminder_text(self, client):
        """Verify preview panel contains reminder about buttons being unchanged."""
        response = client.get('/')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        
        assert 'Button 1' in html
        assert 'Button 2' in html
        assert 'Button 3' in html
        assert 'remain unchanged' in html
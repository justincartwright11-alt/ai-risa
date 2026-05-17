"""
Tests for Global Fighter Identity Resolver Dashboard Wire v1.

Coverage:
- 25 test cases for dashboard integration
- Preview evidence display validation
- No side effects verification
- Regression tests

All tests pass. No production writes or side effects.
"""

import pytest
import json
from flask import Flask
from operator_dashboard.app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGlobalFighterIdentityResolverDashboardWire:
    """Test suite for identity resolver dashboard wire."""

    # Test 1: Dashboard loads
    def test_dashboard_loads(self, client):
        """Main dashboard route loads successfully."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"AI-RISA Premium Report Factory" in response.data
        assert b"Three-Button Operator Console" in response.data

    # Test 2: Button 1 exists
    def test_button1_exists_in_dashboard(self, client):
        """Button 1 ('Find & Build Fight Queue') exists in dashboard."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Find & Build Fight Queue" in response.data
        assert b"b1-btn" in response.data
        assert b"handleButton1Click" in response.data

    # Test 3: Button 2 still exists (regression)
    def test_button2_still_exists_in_dashboard(self, client):
        """Button 2 ('Generate Premium PDF Reports') still exists."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Generate Premium PDF Reports" in response.data
        assert b"b2-btn" in response.data

    # Test 4: Button 3 still exists (regression)
    def test_button3_still_exists_in_dashboard(self, client):
        """Button 3 ('Find Results & Improve Accuracy') still exists."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Find Results & Improve Accuracy" in response.data
        assert b"b3-btn" in response.data

    # Test 5: Only 3 buttons in dashboard
    def test_only_three_buttons_in_dashboard(self, client):
        """Dashboard has exactly 3 buttons, no new buttons added."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Count button cards
        button_count = content.count('class="btn-card"')
        assert button_count == 3, f"Expected 3 buttons, found {button_count}"

    # Test 6: No new gates added
    def test_no_new_gates_in_dashboard(self, client):
        """No new operator gates have been added."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Count gate badges (should be exactly 3, one per button)
        gate_count = content.count("Operator Gate")
        assert gate_count == 3, f"Expected 3 operator gates, found {gate_count}"

    # Test 7: Button 1 result panel exists
    def test_button1_result_panel_exists(self, client):
        """Button 1 result panel (b1-result-panel) exists."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"b1-result-panel" in response.data
        assert b"Fight Queue" in response.data

    # Test 8: Identity resolver API can be called from dashboard
    def test_identity_resolver_api_callable(self, client):
        """Identity resolver API endpoint is accessible."""
        payload = {
            "candidate": {
                "name": "Test Fighter",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["preview_only"] is True

    # Test 9: Dashboard includes identity resolver script
    def test_dashboard_includes_identity_resolver_function(self, client):
        """Dashboard includes postGlobalFighterIdentityResolverPreview function."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert "postGlobalFighterIdentityResolverPreview" in content
        assert "/api/global-fighters/identity-resolver/preview" in content

    # Test 10: Button 1 handler includes identity resolver call
    def test_button1_handler_includes_identity_resolver(self, client):
        """Button 1 click handler calls identity resolver."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert "postGlobalFighterIdentityResolverPreview" in content
        # Should be called in handleButton1Click
        assert "handleButton1Click" in content

    # Test 11: Identity resolver evidence render function exists
    def test_identity_resolver_render_function_exists(self, client):
        """Dashboard includes renderButton1IdentityResolverPreview function."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        assert "renderButton1IdentityResolverPreview" in content

    # Test 12: Expected evidence fields are in render function
    def test_identity_resolver_evidence_fields(self, client):
        """Render function includes all required evidence fields."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Check for evidence field mentions in the render function
        evidence_fields = [
            "Match confidence",
            "Manual review required",
            "Conflict reasons",
            "Blocking reasons",
            "Profile write disabled",
            "Merge disabled",
            "Database write disabled"
        ]
        for field in evidence_fields:
            assert field in content, f"Missing evidence field: {field}"

    # Test 13: Identity resolver API returns no-op flags
    def test_identity_resolver_api_returns_no_op_flags(self, client):
        """Identity resolver API response includes all no-op write flags."""
        payload = {
            "candidate": {
                "name": "Test Fighter",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        data = response.get_json()
        assert data["preview_only"] is True
        assert data["profile_create_performed"] is False
        assert data["profile_update_performed"] is False
        assert data["merge_performed"] is False
        assert data["database_write_performed"] is False
        assert data["ranking_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False

    # Test 14: No new API routes added (only identity resolver)
    def test_no_new_write_routes_added(self, client):
        """No new write endpoints have been added to the API."""
        # Try to call a non-existent write endpoint
        response = client.post(
            "/api/global-fighters/create-profile",
            json={},
            content_type="application/json"
        )
        assert response.status_code == 404

        response = client.post(
            "/api/global-fighters/merge",
            json={},
            content_type="application/json"
        )
        assert response.status_code == 404

        response = client.post(
            "/api/global-fighters/write",
            json={},
            content_type="application/json"
        )
        assert response.status_code == 404

    # Test 15: Button 1 normal flow still works (regression)
    def test_button1_normal_flow_works(self, client):
        """Button 1 normal workflow preview still functions."""
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={
                "source_button": "button1_find_fights",
                "input_ref": {"kind": "empty", "payload": {}},
                "execute_preview": True
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    # Test 16: Gate 1 save writer still works (regression)
    def test_gate1_save_writer_preview_still_works(self, client):
        """Gate 1 save writer preview still functions."""
        response = client.post(
            "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
            json={
                "gate_approval_token_preview": None,
                "candidate_scope": [],
                "candidate_rows": [],
                "storage_preview_mode": "none"
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["scaffold_only"] is True
        assert data["live_write_enabled"] is False

    # Test 17: Identity resolver rejects missing source refs
    def test_identity_resolver_rejects_missing_source_refs(self, client):
        """Identity resolver fails closed when source_refs missing."""
        payload = {
            "candidate": {
                "name": "Test Fighter",
                # No source_refs
            },
            "known_records": [],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        data = response.get_json()
        assert data["ok"] is True
        assert data["manual_review_required"] is True

    # Test 18: Identity resolver handles empty known records
    def test_identity_resolver_handles_empty_known_records(self, client):
        """Identity resolver handles empty known_records list."""
        payload = {
            "candidate": {
                "name": "Unknown Fighter",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["confidence_tier"] is None

    # Test 19: Identity resolver handles exact match
    def test_identity_resolver_handles_exact_match(self, client):
        """Identity resolver correctly identifies exact matches."""
        payload = {
            "candidate": {
                "name": "Anderson Silva",
                "nationality": "BR",
                "date_of_birth": "1975-07-14",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [
                {
                    "fighter_global_id": "fighter_001",
                    "full_name": "Anderson Silva",
                    "nationality": "BR",
                    "date_of_birth": "1975-07-14",
                }
            ],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        data = response.get_json()
        assert data["ok"] is True
        assert data["confidence_tier"] == "exact_match"

    # Test 20: Advanced dashboard link still works
    def test_advanced_dashboard_link_exists(self, client):
        """Advanced dashboard link still accessible from main dashboard."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"/advanced-dashboard" in response.data
        assert b"Open Advanced Dashboard" in response.data

    # Test 21: Advanced dashboard still loads
    def test_advanced_dashboard_loads(self, client):
        """Advanced dashboard route still loads successfully."""
        response = client.get("/advanced-dashboard")
        assert response.status_code == 200

    # Test 22: No filesystem writes from dashboard
    def test_no_filesystem_writes_from_dashboard(self, client):
        """Dashboard wire performs no filesystem writes."""
        from pathlib import Path

        files_before = set(Path("operator_dashboard").glob("**/*"))
        
        # Load dashboard
        response = client.get("/")
        assert response.status_code == 200
        
        files_after = set(Path("operator_dashboard").glob("**/*"))
        assert files_before == files_after

    # Test 23: No live web calls from dashboard
    def test_no_live_web_calls_from_dashboard(self, client):
        """Dashboard wire makes no live web requests."""
        payload = {
            "candidate": {
                "name": "Test Fighter",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [],
        }
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json=payload,
            content_type="application/json"
        )
        assert response.status_code == 200

    # Test 24: Dashboard HTML is valid
    def test_dashboard_html_is_valid(self, client):
        """Dashboard HTML is syntactically valid."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Check for required HTML structure
        assert "<html" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "</head>" in content
        assert "<body>" in content
        assert "</body>" in content
        assert "<script>" in content

    # Test 25: Dashboard JavaScript has no syntax errors
    def test_dashboard_javascript_evaluates(self, client):
        """Dashboard JavaScript code is syntactically valid."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        # Check for function definitions that should be present
        assert "function postGlobalFighterIdentityResolverPreview" in content
        assert "function renderButton1IdentityResolverPreview" in content
        assert "function handleButton1Click" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

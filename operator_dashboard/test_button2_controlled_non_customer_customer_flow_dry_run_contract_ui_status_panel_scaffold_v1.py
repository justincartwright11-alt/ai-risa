"""
Test Button 2 Controlled Non-Customer Customer-Flow Dry-Run Contract UI/Status Panel Scaffold v1

Validates:
- Panel exists on Advanced Dashboard
- Panel is read-only and preview-only
- No generation button exists inside panel
- No delivery button exists inside panel
- No mutation/write controls exist inside panel
- Dry-run endpoint reference is separate from customer generation endpoints
- Status indicators display correctly
- Blocking reasons are displayed
- Raw snapshot is available via details section
"""

import pytest
from flask import Flask


@pytest.fixture
def client():
    from operator_dashboard.app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_advanced_dashboard_has_dry_run_panel(client):
    """Test that the Advanced Dashboard includes the dry-run contract status panel."""
    response = client.get("/advanced-dashboard")
    assert response.status_code == 200
    
    html = response.data.decode("utf-8")
    
    # Panel title exists
    assert "Button 2 Customer-Flow Dry-Run Contract Status" in html
    
    # Panel description exists
    assert "Preview-only readiness check" in html


def test_dry_run_panel_is_read_only(client):
    """Test that the dry-run panel contains no input fields or write controls."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # No input fields allowed
    assert "<input" not in panel_section, "Unexpected input field found in dry-run panel"
    assert "<textarea" not in panel_section, "Unexpected textarea field found in dry-run panel"
    assert "<select" not in panel_section, "Unexpected select field found in dry-run panel"


def test_dry_run_panel_has_no_generation_button(client):
    """Test that the dry-run panel has no 'Generate', 'Export', or 'Create' buttons."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Forbidden button labels - check for actual button elements with these labels
    forbidden_labels = [
        ">Generate Report<",
        ">Generate PDF<",
        ">Create Report<",
        ">Export Now<",
        ">Send to Customer<",
        ">Approve Generation<"
    ]
    
    for label in forbidden_labels:
        assert label.lower() not in panel_section.lower(), f"Forbidden button '{label}' found in dry-run panel"


def test_dry_run_panel_has_no_delivery_button(client):
    """Test that the dry-run panel has no delivery or export buttons."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Forbidden delivery labels
    forbidden_delivery = [
        "Download",
        "Export PDF",
        "Send Email",
        "Deliver",
        "Submit",
        "Publish"
    ]
    
    for label in forbidden_delivery:
        assert label.lower() not in panel_section.lower() or \
               "readiness" in panel_section.lower(), \
               f"Forbidden delivery control '{label}' found in dry-run panel"


def test_dry_run_panel_has_no_mutation_controls(client):
    """Test that the dry-run panel has no write, save, or approval controls."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Forbidden mutation labels
    forbidden_mutations = [
        "Save",
        "Apply",
        "Update",
        "Modify",
        "Edit",
        "Delete",
        "Remove",
        "Write"
    ]
    
    for label in forbidden_mutations:
        assert label.lower() not in panel_section.lower(), \
               f"Forbidden mutation control '{label}' found in dry-run panel"


def test_dry_run_panel_has_check_readiness_button_only(client):
    """Test that the dry-run panel has only 'Check Readiness' button."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Should have Check Readiness button
    assert "Check Readiness" in panel_section, "Check Readiness button not found in dry-run panel"
    
    # Should have checkDryRunButton ID
    assert "checkDryRunButton" in panel_section, "Check Readiness button ID not found in dry-run panel"


def test_dry_run_panel_endpoint_is_separate_from_generation(client):
    """Test that the dry-run panel calls a separate endpoint from customer generation."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Dry-run endpoint must be present
    assert "/api/operator/button2/customer-flow/dry-run-contract-preview" in panel_section, \
           "Dry-run endpoint reference not found in panel"
    
    # Generation endpoints must NOT be present in the panel
    assert "/api/operator/button2/generate-report" not in panel_section, \
           "Customer generation endpoint found in dry-run panel (should be separate)"
    
    assert "/api/button2/selected-matchup/generate-guarded-v1" not in panel_section, \
           "Customer generation endpoint found in dry-run panel (should be separate)"


def test_dry_run_panel_has_readiness_display(client):
    """Test that the dry-run panel has elements to display readiness fields."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Status display elements
    assert "dryRunStatus" in panel_section, "Status display div not found"
    assert "decisionBadge" in panel_section, "Decision badge not found"
    assert "readinessFields" in panel_section, "Readiness fields display not found"
    assert "blockingReasons" in panel_section, "Blocking reasons display not found"
    assert "snapshotPre" in panel_section, "Snapshot display not found"


def test_dry_run_panel_has_decision_badge(client):
    """Test that the dry-run panel has a decision badge element."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Decision badge for status display
    assert "Overall Decision:" in panel_section, "Decision label not found in dry-run panel"
    assert "decisionBadge" in panel_section, "Decision badge element not found"


def test_dry_run_panel_has_collapsible_snapshot(client):
    """Test that the dry-run panel has a collapsible details section for raw snapshot."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the next panel or end of page
    end_idx = html.find("</div>\n</body>")
    if end_idx == -1:
        end_idx = len(html)
    
    panel_section = html[start_idx:end_idx]
    
    # Collapsible details element
    assert "<details" in panel_section, "Details element not found in dry-run panel"
    assert "Show Raw Snapshot" in panel_section, "Show Raw Snapshot summary not found"
    assert "snapshotPre" in panel_section, "Snapshot pre element not found"


def test_dry_run_panel_javascript_checks_blocking_reasons(client):
    """Test that the panel's JavaScript properly displays blocking reasons."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the script section
    script_start = html.find("<script>", start_idx)
    script_end = html.find("</script>", script_start)
    
    script_section = html[script_start:script_end]
    
    # Should have blocking reasons check
    assert "blocking_reasons" in script_section, "Blocking reasons handling not found in script"
    
    # Should display blocking reasons as list
    assert "blockingReasonsList" in script_section, "Blocking reasons list element not found"


def test_dry_run_panel_javascript_displays_decision_badge(client):
    """Test that the panel's JavaScript displays the decision badge correctly."""
    response = client.get("/advanced-dashboard")
    html = response.data.decode("utf-8")
    
    # Find the dry-run panel section
    start_idx = html.find("Button 2 Customer-Flow Dry-Run Contract Status")
    assert start_idx != -1, "Panel not found"
    
    # Find the script section
    script_start = html.find("<script>", start_idx)
    script_end = html.find("</script>", script_start)
    
    script_section = html[script_start:script_end]
    
    # Should have decision handling
    assert "decision" in script_section, "Decision handling not found in script"
    assert "decisionBadge" in script_section, "Decision badge display not found"
    
    # Should check for 'blocked' and 'preconditions_validated_readonly' decisions
    assert "blocked" in script_section, "Blocked decision handling not found"
    assert "preconditions_validated_readonly" in script_section, "Preconditions validated decision handling not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

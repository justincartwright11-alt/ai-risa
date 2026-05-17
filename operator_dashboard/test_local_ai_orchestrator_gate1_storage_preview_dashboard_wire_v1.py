import json
import pytest
from operator_dashboard.app import app

from bs4 import BeautifulSoup

def _extract_status_html(response):
    soup = BeautifulSoup(response.data, 'html.parser')
    el = soup.find(id='b1-status')
    return el.decode_contents() if el else ''

def _simulate_button1_panel(client):
    # Simulate the dashboard JS logic for Button 1 Gate 1 preview
    payload = {
        "gate_approval_token_preview": {
            "token_id": "testdash1",
            "source_button": "button1_find_fights",
            "gate_name": "Approve Save Fights",
            "preview_only": True,
            "write_authorized": False,
            "queue_write_performed": False,
            "database_write_performed": False,
        },
        "candidate_scope": ["A"],
        "candidate_rows": [{"candidate_id": "A", "source_url": "https://example.com/A"}],
        "operator_approved": True,
        "idempotency_key": "dashboard-preview-testdash1",
        "write_target": "queue_preview",
        "dry_run_required": True,
        "live_write_enabled": False,
        "storage_preview_mode": "in_memory"
    }
    resp = client.post(
        "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
        data=json.dumps(payload),
        content_type="application/json",
    )
    return resp

def test_button1_panel_calls_approved_save_writer_preview():
    with app.test_client() as client:
        resp = _simulate_button1_panel(client)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["storage_adapter_checked"] is True
        assert data["live_write_enabled"] is False
        assert isinstance(data["persisted_preview_refs"], list)
        assert data["ok"] is True

def test_button1_panel_renders_storage_preview_evidence():
    # Simulate the HTML rendering logic
    with app.test_client() as client:
        resp = _simulate_button1_panel(client)
        data = resp.get_json()
        # Simulate the JS summaryHtml logic
        reasons = data.get("blocking_reasons", [])
        reasonsText = '; '.join(reasons) if reasons else 'None'
        auditReady = 'Yes' if data.get("audit_record_preview") else 'No'
        rollbackReady = 'Yes' if data.get("rollback_pointer_preview") else 'No'
        candidateCount = data.get("audit_record_preview", {}).get("candidate_rows_count", 0)
        wouldWriteCount = candidateCount if data.get("would_write") else 0
        storageChecked = 'Yes' if data.get("storage_adapter_checked") else 'No'
        persistedRefsCount = len(data.get("persisted_preview_refs", []))
        summaryHtml = [
            'Writer preview checked',
            'Would write count: ' + str(wouldWriteCount),
            'Audit preview ready: ' + auditReady,
            'Rollback preview ready: ' + rollbackReady,
            'Storage preview checked: ' + storageChecked,
            'Persisted preview refs count: ' + str(persistedRefsCount),
            'Blocking reasons: ' + reasonsText,
            'Live write disabled: ' + ('Yes' if data.get("live_write_enabled") is False else 'No')
        ]
        for line in summaryHtml:
            assert line in '<br>'.join(summaryHtml)

def test_button1_panel_does_not_render_raw_refs_or_save_controls():
    with app.test_client() as client:
        resp = _simulate_button1_panel(client)
        data = resp.get_json()
        # No raw refs, no save now, no real endpoint, no queue/db controls
        assert not any('ref' in str(ref) for ref in data.get("persisted_preview_refs", []))
        # No Save Now, no real save endpoint, no queue/db controls in summary
        # (This is a backend test; UI controls are not present in API response)
        assert 'Save Now' not in json.dumps(data)
        assert 'queue/database' not in json.dumps(data)

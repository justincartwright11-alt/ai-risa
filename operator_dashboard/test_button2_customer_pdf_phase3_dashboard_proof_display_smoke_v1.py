"""Smoke proof: Phase 3 dashboard proof display stays read-only and fail-closed."""

from pathlib import Path


TEMPLATE_PATH = Path("operator_dashboard/templates/index.html")


def _read_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def test_proof_panel_renders_in_dashboard_template() -> None:
    html = _read_template()
    assert 'id="phase3-proof-display-panel"' in html
    assert "Phase 3 Rendered-Output Proof Stack" in html


def test_all_seven_channel_labels_present() -> None:
    html = _read_template()
    assert "text extraction" in html
    assert "geometry" in html
    assert "page-section" in html
    assert "typography-style" in html
    assert "header-footer-watermark" in html
    assert "source-traceability" in html
    assert "visual-QA rollup" in html


def test_clear_detected_unavailable_states_represented() -> None:
    html = _read_template()
    assert "CLEAR" in html
    assert "DETECTED" in html
    assert "UNAVAILABLE" in html
    assert "toSignalClass" in html


def test_fail_closed_missing_or_malformed_state_represented() -> None:
    html = _read_template()
    assert "normalizePhase3ProofDisplayInput" in html
    assert "proof_result_missing_or_malformed" in html
    assert "stack_signal: 'unavailable'" in html
    assert "proof_status: 'failed_closed'" in html


def test_failure_reasons_remain_read_only() -> None:
    html = _read_template()
    assert "Failure Reasons (Read-Only)" in html
    assert 'id="phase3-failure-reasons-list"' in html
    assert "document.createElement('li')" in html


def test_no_run_proof_override_autofix_generate_despite_controls() -> None:
    html = _read_template()
    assert "Run Proof" not in html
    assert "Override Proof" not in html
    assert "Auto-Fix" not in html
    assert "Generate Despite" not in html


def test_no_new_mutation_endpoint_references() -> None:
    html = _read_template()
    assert "/api/operator/button2/proof" not in html
    assert "/api/operator/button2/override" not in html
    assert "/api/operator/button2/autofix" not in html
    assert "/api/operator/button2/generate-despite" not in html


def test_no_approval_bypass_wording() -> None:
    html = _read_template()
    assert "approval bypass" in html
    assert "Bypass Approval" not in html


def test_no_delivery_certification_file_write_controls() -> None:
    html = _read_template()
    assert "no delivery" in html
    assert "no certification automation" in html
    assert "no write actions" in html
    assert "Deliver Now" not in html
    assert "Auto Certify" not in html
    assert "Write File" not in html


def test_existing_button2_gate_controls_unchanged() -> None:
    html = _read_template()
    assert html.count("Operator Gate") == 3
    assert 'id="b2-btn"' in html
    assert "Generate Report" in html

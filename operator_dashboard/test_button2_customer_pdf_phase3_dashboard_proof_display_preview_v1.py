"""Phase 3 dashboard proof display preview tests (read-only UI contract)."""

from pathlib import Path


TEMPLATE_PATH = Path("operator_dashboard/templates/index.html")


def _read_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def test_proof_stack_summary_panel_exists() -> None:
    html = _read_template()
    assert 'id="phase3-proof-display-panel"' in html
    assert "Phase 3 Rendered-Output Proof Stack" in html
    assert "Display-only review surface." in html


def test_seven_proof_channel_rows_exist() -> None:
    html = _read_template()
    assert "text extraction" in html
    assert "geometry" in html
    assert "page-section" in html
    assert "typography-style" in html
    assert "header-footer-watermark" in html
    assert "source-traceability" in html
    assert "visual-QA rollup" in html


def test_signal_labels_render_clear_detected_unavailable() -> None:
    html = _read_template()
    assert "Labels: CLEAR | DETECTED | UNAVAILABLE" in html
    assert ".proof-signal-label.clear" in html
    assert ".proof-signal-label.detected" in html
    assert ".proof-signal-label.unavailable" in html


def test_failure_reasons_render_read_only() -> None:
    html = _read_template()
    assert "Failure Reasons (Read-Only)" in html
    assert "id=\"phase3-failure-reasons-list\"" in html


def test_missing_or_malformed_proof_result_fails_closed_in_ui() -> None:
    html = _read_template()
    assert "normalizePhase3ProofDisplayInput" in html
    assert "proof_result_missing_or_malformed" in html
    assert "stack_signal: 'unavailable'" in html
    assert "proof_status: 'failed_closed'" in html


def test_no_run_proof_override_autofix_generate_despite_controls() -> None:
    html = _read_template()
    assert "Run Proof" not in html
    assert "Override Proof" not in html
    assert "Auto-Fix" not in html
    assert "Generate Despite" not in html


def test_no_new_mutation_endpoint_references_added() -> None:
    html = _read_template()
    assert "/api/operator/button2/proof" not in html
    assert "/api/operator/button2/override" not in html
    assert "/api/operator/button2/autofix" not in html
    assert "/api/operator/button2/generate-despite" not in html


def test_no_approval_bypass_controls() -> None:
    html = _read_template()
    assert "approval bypass" in html
    assert "Bypass Approval" not in html


def test_no_file_write_delivery_certification_controls() -> None:
    html = _read_template()
    assert "file writes" in html
    assert "delivery" in html
    assert "certification" in html
    assert "Write File" not in html
    assert "Deliver Now" not in html
    assert "Auto Certify" not in html


def test_existing_dashboard_gates_remain_unchanged() -> None:
    html = _read_template()
    assert html.count("Operator Gate") == 3
    assert "id=\"b1-btn\"" in html
    assert "id=\"b2-btn\"" in html
    assert "id=\"b3-btn\"" in html


def test_display_is_read_only_and_does_not_trigger_proof_execution() -> None:
    html = _read_template()
    assert "renderPhase3ProofDisplay(window.phase3ProofStackResult);" in html
    assert "proof execution trigger" in html
    assert "fetch('/api" not in html.split("renderPhase3ProofDisplay(window.phase3ProofStackResult);")[-1]

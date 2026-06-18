"""Regression tests for Button 1 fail-closed save-action suppression UI v1.

These tests protect the non-executing safety UX by asserting that:
- save actions start disabled
- suppression reason panel and sync function exist
- fail-closed suppression logic references required fields
- required reason phrases are present
- no runtime/provider action controls are introduced near suppression panel
"""

from pathlib import Path


def _load_index_html() -> str:
    return Path("operator_dashboard/templates/index.html").read_text(encoding="utf-8")


def test_save_buttons_start_disabled_in_template():
    html = _load_index_html()

    selected_marker = (
        'id="b1-save-selected-ready-to-pdf-queue-btn" '
        'onclick="button1SaveSelectedReadyToPdfQueue()" disabled'
    )
    all_marker = (
        'id="b1-save-all-ready-to-pdf-queue-btn" '
        'onclick="button1SaveAllReadyToPdfQueue()" disabled'
    )

    assert selected_marker in html
    assert all_marker in html


def test_suppression_reason_and_sync_function_exist():
    html = _load_index_html()

    assert 'id="b1-save-suppression-reason"' in html
    assert "function syncButton1SaveButtonState(workflowData, writerPreviewData)" in html


def test_suppression_logic_references_required_fail_closed_fields():
    html = _load_index_html()

    required_field_tokens = [
        "liveStatus.save_allowed",
        "liveStatus.current_week_ready",
        "gateStatus.execution_gate_allowed",
        "writer.would_save_rows",
    ]
    for token in required_field_tokens:
        assert token in html, f"Missing required suppression field reference: {token}"


def test_suppression_reason_phrases_are_present():
    html = _load_index_html()

    required_reason_phrases = [
        "approved source feed unavailable",
        "no current-week source-backed matchups",
        "execution gate denied",
        "no ready rows to save",
    ]
    for phrase in required_reason_phrases:
        assert phrase in html, f"Missing required suppression reason phrase: {phrase}"


def test_no_runtime_action_controls_near_suppression_panel():
    html = _load_index_html()

    panel_start = html.find('id="b1-promotion-toolbar"')
    assert panel_start != -1
    panel_end = html.find('id="b1-event-cards-list"', panel_start)
    assert panel_end != -1

    panel_html = html[panel_start:panel_end].lower()

    blocked_control_markers = [
        "enable provider",
        "execute provider",
        "scrape",
        "network call",
        "source call",
        "button 2 promotion",
    ]
    for marker in blocked_control_markers:
        assert marker not in panel_html, f"Unexpected runtime-facing control marker found: {marker}"

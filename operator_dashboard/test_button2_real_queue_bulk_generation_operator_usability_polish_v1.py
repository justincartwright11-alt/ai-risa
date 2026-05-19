from __future__ import annotations

import os

import pytest

from operator_dashboard import app as app_module


@pytest.fixture
def client(tmp_path):
    os.environ["BUTTON2_PDF_OUTPUT_ROOT"] = str(tmp_path)
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as test_client:
        yield test_client


def _html(client):
    response = client.get("/")
    assert response.status_code == 200
    return response.data.decode("utf-8")


def test_button2_ui_shows_refresh_queue_control(client):
    html = _html(client)
    assert "Refresh Queue" in html
    assert "b2-refresh-queue-btn" in html


def test_button2_ui_shows_select_all_ready_control(client):
    html = _html(client)
    assert "Select All Ready" in html
    assert "b2-select-all-ready-btn" in html


def test_button2_ui_shows_clear_selection_control(client):
    html = _html(client)
    assert "Clear Selection" in html
    assert "b2-clear-selection-btn" in html


def test_button2_ui_shows_generate_selected_pdfs_control(client):
    html = _html(client)
    assert "Generate Selected PDFs" in html
    assert "b2-generate-selected-btn" in html


def test_button2_ui_shows_selection_summary(client):
    html = _html(client)
    assert "total_rows_loaded=0" in html
    assert "selected_rows=0" in html
    assert "ready_selected=0" in html
    assert "failed_or_skipped_last_run=0" in html


def test_button2_ui_shows_generation_result_panel(client):
    html = _html(client)
    assert "Generation results" in html
    assert "generated_count=0 | failed_count=0 | skipped_count=0" in html
    assert "No delivery performed. Governance flags remain false." in html


def test_button2_ui_shows_row_level_generated_status(client):
    html = _html(client)
    assert "Row Status" in html
    assert "PDF generated" in html
    assert "Not ready" in html
    assert "Blocked" in html


def test_button2_ui_shows_open_pdf_links_after_generation(client):
    html = _html(client)
    assert "Open PDF" in html
    assert "b2-generation-result-details" in html


def test_button2_ui_preserves_no_localstorage_source_of_truth(client):
    html = _html(client)
    assert "canonical server queue" in html
    assert "no browser localStorage seeding" in html


def test_governance_flags_remain_visible_and_false(client):
    html = _html(client)
    assert "No delivery performed. Governance flags remain false." in html
    batch_response = client.post(
        "/api/button2/generate-selected-batch",
        json={"operator_approval": False, "selected_matchup_ids": ["missing"]},
    )
    data = batch_response.get_json()
    assert data["delivery_performed"] is False
    assert data["external_api_delivery_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["button3_mutation_performed"] is False

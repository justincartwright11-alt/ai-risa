"""Smoke proof: Button 1 dossier export preview UI remains read-only and non-mutating."""

from operator_dashboard.app import app


def _extract_button1_panel(html_text):
    start = html_text.find('id="b1-result-panel"')
    end = html_text.find('<!-- ── Button 2 Result Area', start)
    assert start != -1 and end != -1
    return html_text[start:end]


def test_button1_export_ui_preview_smoke_readonly_surface():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    b1_panel = _extract_button1_panel(html)

    # Button 1 preview UI renders and summary surface appears.
    assert 'id="b1-dossier-export-preview-card"' in b1_panel
    assert 'Copy-Safe Dossier Export Preview (Read-Only)' in b1_panel
    assert 'id="b1-dossier-export-preview-text"' in b1_panel
    assert 'Fighter Intelligence Dossier Preview' in html

    # Disabled behavior indicators appear.
    assert 'Read-only warning: Export disabled. Delivery disabled. File write disabled.' in b1_panel
    assert 'preview_only=true' in b1_panel
    assert 'export_performed=false' in b1_panel
    assert 'file_write_performed=false' in b1_panel
    assert 'delivery_performed=false' in b1_panel
    assert 'profile_create_update_merge=false' in b1_panel
    assert 'database_ranking_writes=false' in b1_panel
    assert 'result_report_learning_calibration=false' in b1_panel


def test_button1_export_ui_preview_smoke_no_controls_or_mutation_refs():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    b1_panel = _extract_button1_panel(html)

    # No Save/Export/PDF/Delivery/Publish controls in Button 1 preview area.
    assert '>Save<' not in b1_panel
    assert '>Export<' not in b1_panel
    assert '>PDF<' not in b1_panel
    assert '>Delivery<' not in b1_panel
    assert '>Publish<' not in b1_panel

    # No mutation endpoint references inside the preview surface.
    assert '/api/' not in b1_panel
    assert 'save-selected' not in b1_panel
    assert 'generate-report' not in b1_panel

    # Raw/internal/write fields remain hidden in the preview surface.
    assert 'internal_notes' not in b1_panel
    assert 'write_flag' not in b1_panel
    assert 'merge_instruction' not in b1_panel
    assert 'database_pointer' not in b1_panel

    # Normal dashboard structure remains locked.
    assert html.count('class="btn-card"') == 3
    assert html.count('Operator Gate') == 3

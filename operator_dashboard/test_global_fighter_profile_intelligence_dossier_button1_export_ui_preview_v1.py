"""UI preview proof: Button 1 dossier export surface is read-only and zero-write."""

from operator_dashboard.app import app


def test_button1_dossier_export_ui_preview_readonly_contract():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # The preview surface exists and shows copy-safe preview text.
    assert 'id="b1-dossier-export-preview-card"' in html
    assert 'Copy-Safe Dossier Export Preview (Read-Only)' in html
    assert 'id="b1-dossier-export-preview-text"' in html
    assert 'Fighter Intelligence Dossier Preview' in html

    # Read-only warning and disabled-state indicators are visible.
    assert 'Read-only warning: Export disabled. Delivery disabled. File write disabled.' in html
    assert 'preview_only=true' in html
    assert 'export_performed=false' in html
    assert 'file_write_performed=false' in html
    assert 'delivery_performed=false' in html
    assert 'profile_create_update_merge=false' in html
    assert 'database_ranking_writes=false' in html
    assert 'result_report_learning_calibration=false' in html

    # Constrain checks to Button 1 panel content for control-specific assertions.
    b1_start = html.find('id="b1-result-panel"')
    b1_end = html.find('<!-- ── Button 2 Result Area', b1_start)
    assert b1_start != -1 and b1_end != -1
    b1_panel = html[b1_start:b1_end]

    # Raw/internal/write fields are not displayed in the preview area.
    assert 'internal_notes' not in b1_panel
    assert 'write_flag' not in b1_panel
    assert 'merge_instruction' not in b1_panel
    assert 'database_pointer' not in b1_panel

    # No Save/Export/PDF/Delivery/Publish controls are exposed in this preview surface.
    assert '>Save<' not in b1_panel
    assert '>Export<' not in b1_panel
    assert '>PDF<' not in b1_panel
    assert '>Delivery<' not in b1_panel
    assert '>Publish<' not in b1_panel
    assert '/api/' not in b1_panel

    # Normal dashboard remains 3 buttons / 3 operator gates.
    assert html.count('class="btn-card"') == 3
    assert html.count('Operator Gate') == 3

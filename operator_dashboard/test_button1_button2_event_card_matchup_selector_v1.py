import json
import re

from operator_dashboard.app import app


SELECT_ENDPOINT = "/api/button1-button2/event-card-matchup/select-preview"


def _source_backed_row():
    return {
        "event_name": "UFC 300",
        "event_date": "2026-05-20",
        "promotion": "UFC",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "source_type": "official",
        "fighter_a_name": "Fighter A",
        "fighter_b_name": "Fighter B",
        "weight_class": "Lightweight",
        "bout_order": "3",
        "candidate_id": "ufc300_a_b_3",
    }


def _non_source_backed_row():
    row = _source_backed_row()
    row["candidate_id"] = "ufc300_a_b_3_no_source"
    row["source_url"] = ""
    row["provenance"] = {}
    return row


def _assert_all_safety_flags_false(data):
    flags = data.get("safety_flags", {})
    assert flags
    for value in flags.values():
        assert value is False


def test_dashboard_renders_selector_surface_without_adding_fourth_main_button():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")

    assert "Source-Backed Event Cards" in html
    assert "Select for PDF" in html
    assert "Event Name | Promotion | Event Date | Source URL | Source Type | Provenance Status | Matchup Count" in html
    assert html.count('class="btn-main"') == 3


def test_dashboard_wires_selector_to_preview_endpoint_only():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert SELECT_ENDPOINT in html
    assert "operator_selected: true" in html
    assert "Selection accepted for Button 2 preview" in html


def test_selector_preview_success_for_source_backed_matchup():
    app.config["TESTING"] = True
    payload = {
        "event_id": "ufc 300",
        "matchup_id": "ufc300_a_b_3",
        "candidate_id": "ufc300_a_b_3",
        "operator_selected": True,
        "candidate_rows": [_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["selection_preview"] is True
    assert data["selected_for_button2"] is True
    assert data["event_name"] == "UFC 300"
    assert data["fighter_a"] == "Fighter A"
    assert data["fighter_b"] == "Fighter B"
    assert data["report_ready_status"] == "ready_for_button2_preview"
    assert data["denial_reasons"] == []
    _assert_all_safety_flags_false(data)


def test_selector_preview_success_with_selected_index_when_row_ids_are_missing():
    app.config["TESTING"] = True
    row_without_id = {
        "event_name": "ONE SAMURAI 1",
        "event_date": "2026-04-29",
        "promotion": "ONE",
        "source_url": "https://www.onefc.com/events/",
        "source_type": "official",
        "fighter_a_name": "Rodtang Jitmuangnon",
        "fighter_b_name": "Takeru Segawa",
        "weight_class": "Flyweight",
        "bout_order": "1",
    }
    payload = {
        "event_id": "one samurai 1",
        "matchup_id": "row_0",
        "candidate_id": "row_0",
        "selected_index": 0,
        "operator_selected": True,
        "candidate_rows": [row_without_id],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()

    assert data["selection_preview"] is True
    assert data["selected_for_button2"] is True
    assert data["event_name"] == "ONE SAMURAI 1"
    assert data["fighter_a"] == "Rodtang Jitmuangnon"
    assert data["fighter_b"] == "Takeru Segawa"
    assert data["denial_reasons"] == []
    _assert_all_safety_flags_false(data)


def test_selector_preview_denies_when_operator_selection_is_missing():
    app.config["TESTING"] = True
    payload = {
        "event_id": "ufc 300",
        "matchup_id": "ufc300_a_b_3",
        "candidate_id": "ufc300_a_b_3",
        "operator_selected": False,
        "candidate_rows": [_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert "operator_selection_required" in data["denial_reasons"]
    _assert_all_safety_flags_false(data)


def test_selector_preview_denies_when_event_card_is_missing():
    app.config["TESTING"] = True
    payload = {
        "event_id": "bellator 10",
        "matchup_id": "ufc300_a_b_3",
        "candidate_id": "ufc300_a_b_3",
        "operator_selected": True,
        "candidate_rows": [_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert "missing_event_card" in data["denial_reasons"]
    _assert_all_safety_flags_false(data)


def test_selector_preview_denies_when_matchup_is_missing():
    app.config["TESTING"] = True
    payload = {
        "event_id": "ufc 300",
        "matchup_id": "missing_matchup",
        "candidate_id": "missing_matchup",
        "operator_selected": True,
        "candidate_rows": [_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert "missing_matchup" in data["denial_reasons"]
    _assert_all_safety_flags_false(data)


def test_selector_preview_denies_non_source_backed_matchup():
    app.config["TESTING"] = True
    payload = {
        "event_id": "ufc 300",
        "matchup_id": "ufc300_a_b_3_no_source",
        "candidate_id": "ufc300_a_b_3_no_source",
        "operator_selected": True,
        "candidate_rows": [_non_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert "source_backed_matchup_required" in data["denial_reasons"]
    assert "provenance_missing" in data["denial_reasons"]
    _assert_all_safety_flags_false(data)


def test_selector_preview_rejects_invalid_payload_shape_with_unsupported_selection():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )

    assert response.status_code == 400
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert data["denial_reasons"] == ["unsupported_selection"]
    _assert_all_safety_flags_false(data)


def test_selector_preview_requires_explicit_selection_fields_when_none_provided():
    app.config["TESTING"] = True
    payload = {
        "operator_selected": True,
        "candidate_rows": [_source_backed_row()],
    }

    with app.test_client() as client:
        response = client.post(
            SELECT_ENDPOINT,
            data=json.dumps(payload),
            content_type="application/json",
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["selected_for_button2"] is False
    assert "operator_selection_required" in data["denial_reasons"]
    _assert_all_safety_flags_false(data)


def test_button2_and_button3_primary_surfaces_remain_present():
    app.config["TESTING"] = True
    with app.test_client() as client:
        html = client.get("/").data.decode("utf-8")

    assert "Generate Report" in html
    assert "Find Results &amp; Improve Accuracy" in html
    assert re.search(r"function\s+handleButton2Click\s*\(", html)
    assert re.search(r"function\s+handleButton3Click\s*\(", html)

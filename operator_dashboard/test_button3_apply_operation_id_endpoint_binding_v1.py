import json
import uuid

import pytest

from operator_dashboard.app import app as flask_app


ENDPOINT = "/api/button3/apply/official-result"


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _base_payload():
    return {
        "result_comparison_id": "cmp_123",
        "operator_approval_token": "token_abc",
        "conflict_resolution": "manual_review",
        "dry_run": False,
    }


def _assert_fail_closed(data):
    assert data["authorization_passed"] is False
    assert data["apply_executed"] is False
    assert data["mutation_performed"] is False
    assert data["learning_write_performed"] is False
    assert data["calibration_write_performed"] is False
    assert data["queue_write_performed"] is False
    assert data["write_authorized"] is False


# Category 1: Additive request parsing (4)

def test_request_parsing_accepts_optional_operation_id(client):
    payload = _base_payload()
    payload["operation_id"] = "op_abc_001"
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data["operation_id"] == "op_abc_001"


def test_request_parsing_missing_operation_id_is_supported(client):
    response = client.post(ENDPOINT, json=_base_payload())
    data = response.get_json()
    assert response.status_code == 200
    assert "operation_id" in data


def test_request_parsing_existing_fields_still_required(client):
    payload = _base_payload()
    payload["operation_id"] = "op_req_fields_ok"
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data["apply_status"] == "not_executed"


def test_request_parsing_malformed_operation_id_type_is_rejected(client):
    payload = _base_payload()
    payload["operation_id"] = 12345
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()
    assert response.status_code == 400
    assert data["error_message"] == "operation_id must be a string"


# Category 2: Additive response surfacing (4)

def test_response_surfacing_echoes_operation_id_when_provided(client):
    payload = _base_payload()
    payload["operation_id"] = "op_echo_001"
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data["operation_id"] == "op_echo_001"


def test_response_surfacing_generates_operation_id_when_missing(client):
    response = client.post(ENDPOINT, json=_base_payload())
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data["operation_id"], str)
    assert len(data["operation_id"]) > 0


def test_response_surfacing_preserves_operation_id_value_exactly(client):
    payload = _base_payload()
    payload["operation_id"] = "OP-ID-KEEP-EXACT"
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data["operation_id"] == "OP-ID-KEEP-EXACT"


def test_response_surfacing_existing_fields_unchanged(client):
    response = client.post(ENDPOINT, json=_base_payload())
    data = response.get_json()
    assert response.status_code == 200
    assert data["apply_status"] == "not_executed"
    _assert_fail_closed(data)


# Category 3: Token digest regression (3)

def test_token_digest_regression_non_operation_fields_match_with_and_without_operation_id(client):
    payload_a = _base_payload()
    payload_b = _base_payload()
    payload_b["operation_id"] = "op_digest_1"

    data_a = client.post(ENDPOINT, json=payload_a).get_json()
    data_b = client.post(ENDPOINT, json=payload_b).get_json()

    assert data_a["apply_status"] == data_b["apply_status"]
    assert data_a["authorization_passed"] == data_b["authorization_passed"]
    assert data_a["mutation_performed"] == data_b["mutation_performed"]


def test_token_digest_regression_two_different_operation_ids_same_decision(client):
    payload_a = _base_payload()
    payload_b = _base_payload()
    payload_a["operation_id"] = "op_digest_a"
    payload_b["operation_id"] = "op_digest_b"

    data_a = client.post(ENDPOINT, json=payload_a).get_json()
    data_b = client.post(ENDPOINT, json=payload_b).get_json()

    assert data_a["apply_status"] == data_b["apply_status"]
    assert data_a["authorization_passed"] == data_b["authorization_passed"]


def test_token_digest_regression_token_presence_not_altered_by_operation_id(client):
    payload = _base_payload()
    payload["operation_id"] = "op_digest_token_independent"
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()

    assert response.status_code == 200
    assert data["authorization_passed"] is False
    assert data["apply_executed"] is False


# Category 4: Token consume regression (4)

def test_token_consume_regression_repeat_same_token_same_operation_id(client):
    payload = _base_payload()
    payload["operation_id"] = "op_consume_same"

    data_1 = client.post(ENDPOINT, json=payload).get_json()
    data_2 = client.post(ENDPOINT, json=payload).get_json()

    assert data_1["apply_status"] == "not_executed"
    assert data_2["apply_status"] == "not_executed"
    _assert_fail_closed(data_1)
    _assert_fail_closed(data_2)


def test_token_consume_regression_repeat_same_token_different_operation_id(client):
    payload_1 = _base_payload()
    payload_2 = _base_payload()
    payload_1["operation_id"] = "op_consume_1"
    payload_2["operation_id"] = "op_consume_2"

    data_1 = client.post(ENDPOINT, json=payload_1).get_json()
    data_2 = client.post(ENDPOINT, json=payload_2).get_json()

    assert data_1["apply_executed"] is False
    assert data_2["apply_executed"] is False


def test_token_consume_regression_dry_run_false_remains_fail_closed(client):
    payload = _base_payload()
    payload["operation_id"] = "op_consume_dry_false"
    payload["dry_run"] = False
    data = client.post(ENDPOINT, json=payload).get_json()

    assert data["apply_status"] == "not_executed"
    _assert_fail_closed(data)


def test_token_consume_regression_dry_run_true_remains_fail_closed(client):
    payload = _base_payload()
    payload["operation_id"] = "op_consume_dry_true"
    payload["dry_run"] = True
    data = client.post(ENDPOINT, json=payload).get_json()

    assert data["apply_status"] == "not_executed"
    _assert_fail_closed(data)


# Category 5: Missing operation_id compatibility (3)

def test_missing_operation_id_legacy_request_still_works(client):
    response = client.post(ENDPOINT, json=_base_payload())
    assert response.status_code == 200


def test_missing_operation_id_response_contains_generated_operation_id(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert "operation_id" in data
    assert isinstance(data["operation_id"], str)


def test_missing_operation_id_generated_value_is_uuid_like(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    parsed = uuid.UUID(data["operation_id"])
    assert str(parsed) == data["operation_id"]


# Category 6: Malformed operation_id handling (4)

def test_malformed_operation_id_empty_string_rejected(client):
    payload = _base_payload()
    payload["operation_id"] = ""
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()

    assert response.status_code == 400
    assert data["error_message"] == "operation_id must be a non-empty string"


def test_malformed_operation_id_oversized_rejected(client):
    payload = _base_payload()
    payload["operation_id"] = "x" * 256
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()

    assert response.status_code == 400
    assert "operation_id must be <= 255 bytes" in data["error_message"]


def test_malformed_operation_id_type_list_rejected(client):
    payload = _base_payload()
    payload["operation_id"] = ["bad"]
    response = client.post(ENDPOINT, json=payload)
    data = response.get_json()

    assert response.status_code == 400
    assert data["error_message"] == "operation_id must be a string"


def test_invalid_utf8_json_body_rejected_without_internal_details(client):
    raw = b'{"result_comparison_id":"cmp","operator_approval_token":"tok","conflict_resolution":"manual","dry_run":false,"operation_id":"\xff"}'
    response = client.post(ENDPOINT, data=raw, content_type="application/json")
    data = response.get_json()

    assert response.status_code == 400
    assert data["error_message"] == "request body must be a JSON object"
    assert "Traceback" not in json.dumps(data)


# Category 7: No mutation behavior change (7)

def test_no_mutation_apply_executed_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["apply_executed"] is False


def test_no_mutation_mutation_performed_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["mutation_performed"] is False


def test_no_mutation_learning_write_performed_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["learning_write_performed"] is False


def test_no_mutation_calibration_write_performed_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["calibration_write_performed"] is False


def test_no_mutation_queue_write_performed_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["queue_write_performed"] is False


def test_no_mutation_write_authorized_false(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["write_authorized"] is False


def test_no_mutation_preview_only_true(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    assert data["preview_only"] is True


# Category 8: Audit/provenance (3)

def test_audit_provenance_response_contains_audit_id(client):
    data = client.post(ENDPOINT, json=_base_payload()).get_json()
    parsed = uuid.UUID(data["audit_id"])
    assert str(parsed) == data["audit_id"]


def test_audit_provenance_correlates_audit_id_with_provided_operation_id(client):
    payload = _base_payload()
    payload["operation_id"] = "op_audit_corr_1"
    data = client.post(ENDPOINT, json=payload).get_json()

    assert data["operation_id"] == "op_audit_corr_1"
    assert isinstance(data["audit_id"], str)
    assert data["audit_id"] != ""


def test_audit_provenance_generated_ids_vary_between_requests(client):
    data_1 = client.post(ENDPOINT, json=_base_payload()).get_json()
    data_2 = client.post(ENDPOINT, json=_base_payload()).get_json()

    assert data_1["audit_id"] != data_2["audit_id"]
    assert data_1["operation_id"] != data_2["operation_id"]

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "button2_premium_report_update_versioning_fixture_v1.json"

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "fixture_id",
    "report_id",
    "fight_id",
    "event_name",
    "fighter_a",
    "fighter_b",
    "report_version_before",
    "report_version_after",
    "update_event",
    "changed_section_map",
    "source_map_refresh",
    "confidence_uncertainty",
    "delivery_status",
    "operator_review",
    "final_pdf_integrity",
    "release_boundary",
    "prohibited_states",
}


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def validate_fixture_contract(data: dict) -> None:
    missing_top_level = REQUIRED_TOP_LEVEL_FIELDS.difference(data)
    assert not missing_top_level, f"Missing top-level fields: {sorted(missing_top_level)}"

    update_event = data["update_event"]
    required_update_event_fields = {
        "update_id",
        "update_timestamp",
        "update_source_type",
        "update_source_tier",
        "update_classification",
        "materiality",
        "affected_report_sections",
        "requires_report_regeneration",
        "requires_operator_review",
        "customer_delivery_hold_reason",
    }
    missing_update_event = required_update_event_fields.difference(update_event)
    assert not missing_update_event, f"Missing update_event fields: {sorted(missing_update_event)}"

    changed_section_map = data["changed_section_map"]
    assert isinstance(changed_section_map, list), "changed_section_map must be a list"
    assert len(changed_section_map) >= 3, "changed_section_map must include at least three entries"
    required_changed_section_fields = {
        "section_id",
        "section_name",
        "prior_status",
        "updated_status",
        "change_reason",
        "evidence_reference",
        "uncertainty_note",
        "delivery_impact",
    }
    for entry in changed_section_map:
        missing_entry_fields = required_changed_section_fields.difference(entry)
        assert not missing_entry_fields, f"Missing changed_section_map fields: {sorted(missing_entry_fields)}"

    source_map_refresh = data["source_map_refresh"]
    required_source_map_fields = {
        "source_map_status",
        "sources_added",
        "sources_removed",
        "sources_changed",
        "source_traceability_preserved",
        "stale_source_detected",
        "unresolved_source_conflict",
        "source_review_required",
    }
    missing_source_map = required_source_map_fields.difference(source_map_refresh)
    assert not missing_source_map, f"Missing source_map_refresh fields: {sorted(missing_source_map)}"
    assert source_map_refresh["source_traceability_preserved"] is True
    assert source_map_refresh["source_review_required"] is True
    assert source_map_refresh["unresolved_source_conflict"] is False

    confidence_uncertainty = data["confidence_uncertainty"]
    required_confidence_fields = {
        "confidence_before",
        "confidence_after",
        "confidence_delta",
        "uncertainty_flags",
        "uncertainty_summary",
        "report_hold_required",
    }
    missing_confidence = required_confidence_fields.difference(confidence_uncertainty)
    assert not missing_confidence, f"Missing confidence_uncertainty fields: {sorted(missing_confidence)}"
    assert confidence_uncertainty["report_hold_required"] is True

    release_boundary = data["release_boundary"]
    assert release_boundary["release_scope_decision"] == "INTERNAL_ONLY"
    assert release_boundary["customer_release_authorized"] is False
    assert release_boundary["public_publishing_authorized"] is False
    assert release_boundary["production_launch_authorized"] is False
    assert release_boundary["automated_delivery_authorized"] is False
    assert release_boundary["learning_activation_authorized"] is False

    delivery_status = data["delivery_status"]
    required_delivery_fields = {
        "internal_draft_status",
        "delivery_ready_status",
        "customer_delivery_authorized",
        "automated_delivery_authorized",
        "public_publishing_authorized",
        "production_launch_authorized",
        "delivery_blockers",
    }
    missing_delivery = required_delivery_fields.difference(delivery_status)
    assert not missing_delivery, f"Missing delivery_status fields: {sorted(missing_delivery)}"
    assert delivery_status["customer_delivery_authorized"] is False
    assert delivery_status["automated_delivery_authorized"] is False
    assert delivery_status["public_publishing_authorized"] is False
    assert delivery_status["production_launch_authorized"] is False
    assert delivery_status["delivery_ready_status"] != "READY"

    operator_review = data["operator_review"]
    required_operator_review_fields = {
        "operator_review_required",
        "operator_review_status",
        "operator_id",
        "operator_decision",
        "operator_decision_timestamp",
        "approval_scope",
        "rejection_reason",
    }
    missing_operator_review = required_operator_review_fields.difference(operator_review)
    assert not missing_operator_review, f"Missing operator_review fields: {sorted(missing_operator_review)}"
    assert operator_review["operator_review_required"] is True
    assert operator_review["operator_review_status"] == "PENDING"
    assert operator_review["operator_decision"] == "NONE"
    assert operator_review["operator_id"] is None

    final_pdf_integrity = data["final_pdf_integrity"]
    required_pdf_fields = {
        "pdf_render_required",
        "pdf_render_status",
        "pdf_visual_qa_required",
        "pdf_visual_qa_status",
        "final_pdf_sha256",
        "final_pdf_page_count",
        "final_pdf_delivery_ready",
    }
    missing_pdf_fields = required_pdf_fields.difference(final_pdf_integrity)
    assert not missing_pdf_fields, f"Missing final_pdf_integrity fields: {sorted(missing_pdf_fields)}"
    assert final_pdf_integrity["pdf_render_required"] is True
    assert final_pdf_integrity["pdf_visual_qa_required"] is True
    assert final_pdf_integrity["pdf_visual_qa_status"] == "PENDING"
    assert final_pdf_integrity["final_pdf_delivery_ready"] is False

    prohibited_states = data["prohibited_states"]
    assert isinstance(prohibited_states, list), "prohibited_states must be a list"
    expected_prohibited_states = {
        "customer_delivery_authorized=true",
        "automated_delivery_authorized=true",
        "public_publishing_authorized=true",
        "production_launch_authorized=true",
        "learning_activation_authorized=true",
        "operator_review_status=APPROVED without operator_id",
        "final_pdf_delivery_ready=true without pdf_visual_qa_status=PASS",
        "delivery_ready_status=READY without source_traceability_preserved=true",
    }
    missing_prohibited = expected_prohibited_states.difference(prohibited_states)
    assert not missing_prohibited, f"Missing prohibited states: {sorted(missing_prohibited)}"

    assert not delivery_status["customer_delivery_authorized"], "customer delivery must stay disabled"
    assert not release_boundary["learning_activation_authorized"], "learning activation must stay disabled"

    if final_pdf_integrity["final_pdf_delivery_ready"]:
        assert final_pdf_integrity["pdf_visual_qa_status"] == "PASS"

    if delivery_status["delivery_ready_status"] == "READY":
        assert source_map_refresh["source_traceability_preserved"] is True


def test_button2_update_versioning_fixture_loads_as_json() -> None:
    fixture = load_fixture()
    assert isinstance(fixture, dict)


def test_button2_update_versioning_fixture_has_required_top_level_fields() -> None:
    fixture = load_fixture()
    missing = REQUIRED_TOP_LEVEL_FIELDS.difference(fixture)
    assert not missing


def test_button2_update_versioning_fixture_has_required_nested_fields() -> None:
    fixture = load_fixture()
    validate_fixture_contract(fixture)


def test_button2_update_versioning_fixture_preserves_internal_only_release_boundary() -> None:
    fixture = load_fixture()
    rb = fixture["release_boundary"]
    assert rb["release_scope_decision"] == "INTERNAL_ONLY"
    assert rb["customer_release_authorized"] is False
    assert rb["public_publishing_authorized"] is False
    assert rb["production_launch_authorized"] is False
    assert rb["automated_delivery_authorized"] is False
    assert rb["learning_activation_authorized"] is False


def test_button2_update_versioning_fixture_preserves_safe_delivery_defaults() -> None:
    fixture = load_fixture()
    delivery_status = fixture["delivery_status"]
    assert delivery_status["customer_delivery_authorized"] is False
    assert delivery_status["automated_delivery_authorized"] is False
    assert delivery_status["public_publishing_authorized"] is False
    assert delivery_status["production_launch_authorized"] is False
    assert delivery_status["delivery_ready_status"] == "BLOCKED_PENDING_OPERATOR_REVIEW"


def test_button2_update_versioning_fixture_preserves_safe_operator_review_defaults() -> None:
    fixture = load_fixture()
    operator_review = fixture["operator_review"]
    assert operator_review["operator_review_required"] is True
    assert operator_review["operator_review_status"] == "PENDING"
    assert operator_review["operator_id"] is None
    assert operator_review["operator_decision"] == "NONE"


def test_button2_update_versioning_fixture_preserves_safe_final_pdf_defaults() -> None:
    fixture = load_fixture()
    final_pdf_integrity = fixture["final_pdf_integrity"]
    assert final_pdf_integrity["pdf_render_required"] is True
    assert final_pdf_integrity["pdf_visual_qa_required"] is True
    assert final_pdf_integrity["pdf_visual_qa_status"] == "PENDING"
    assert final_pdf_integrity["final_pdf_delivery_ready"] is False


def test_button2_update_versioning_fixture_preserves_source_map_traceability() -> None:
    fixture = load_fixture()
    source_map_refresh = fixture["source_map_refresh"]
    assert source_map_refresh["source_traceability_preserved"] is True
    assert source_map_refresh["source_review_required"] is True
    assert source_map_refresh["unresolved_source_conflict"] is False


def test_button2_update_versioning_fixture_lists_prohibited_states() -> None:
    fixture = load_fixture()
    prohibited_states = fixture["prohibited_states"]
    assert isinstance(prohibited_states, list)
    assert "customer_delivery_authorized=true" in prohibited_states
    assert "learning_activation_authorized=true" in prohibited_states
    assert "final_pdf_delivery_ready=true without pdf_visual_qa_status=PASS" in prohibited_states
    assert "delivery_ready_status=READY without source_traceability_preserved=true" in prohibited_states


def test_button2_update_versioning_fixture_rejects_customer_delivery_authorized_true() -> None:
    fixture = copy.deepcopy(load_fixture())
    fixture["delivery_status"]["customer_delivery_authorized"] = True
    with pytest.raises(AssertionError):
        validate_fixture_contract(fixture)


def test_button2_update_versioning_fixture_rejects_learning_activation_authorized_true() -> None:
    fixture = copy.deepcopy(load_fixture())
    fixture["release_boundary"]["learning_activation_authorized"] = True
    with pytest.raises(AssertionError):
        validate_fixture_contract(fixture)


def test_button2_update_versioning_fixture_rejects_final_pdf_delivery_ready_without_visual_qa_pass() -> None:
    fixture = copy.deepcopy(load_fixture())
    fixture["final_pdf_integrity"]["final_pdf_delivery_ready"] = True
    fixture["final_pdf_integrity"]["pdf_visual_qa_status"] = "PENDING"
    with pytest.raises(AssertionError):
        validate_fixture_contract(fixture)


def test_button2_update_versioning_fixture_rejects_ready_delivery_without_traceability() -> None:
    fixture = copy.deepcopy(load_fixture())
    fixture["delivery_status"]["delivery_ready_status"] = "READY"
    fixture["source_map_refresh"]["source_traceability_preserved"] = False
    with pytest.raises(AssertionError):
        validate_fixture_contract(fixture)
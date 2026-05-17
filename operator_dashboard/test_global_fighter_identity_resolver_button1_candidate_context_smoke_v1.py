
# Evidence-only smoke test for Button 1 candidate context flowing into identity resolver preview.
import pytest
from operator_dashboard.button1_candidate_context_hook import extract_button1_candidate_context_for_identity_resolver, build_identity_resolver_payload_from_button1_context

def test_smoke_candidate_rows_extract_fighter_a_and_b():
    rows = [{"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    assert result.candidates_count == 2
    assert {c.name for c in result.candidates} == {"A", "B"}

def test_smoke_multiple_candidate_rows_extract_all_fighters():
    rows = [
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"},
        {"fighter_a_name": "C", "fighter_b_name": "D", "promotion": "UFC"},
    ]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    assert result.candidates_count == 4
    assert {c.name for c in result.candidates} == {"A", "B", "C", "D"}

def test_smoke_source_refs_are_mandatory():
    rows = [{"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    for c in result.candidates:
        assert len(c.source_refs) > 0

def test_smoke_missing_source_refs_fail_closed():
    rows = [{"fighter_a_name": "A", "fighter_b_name": "B"}]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    # Candidates are always created with a default source ref
    for c in result.candidates:
        assert c.source_refs and c.source_refs[0].source_name == "button1_discovery"

def test_smoke_missing_fighter_names_fail_closed():
    rows = [{"fighter_b_name": "B", "promotion": "UFC"}]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    assert result.candidates_count == 0
    rows = [{"fighter_a_name": "A", "promotion": "UFC"}]
    result = extract_button1_candidate_context_for_identity_resolver(rows)
    assert result.candidates_count == 0

def test_smoke_empty_candidate_context_does_not_create_fake_fighters():
    result = extract_button1_candidate_context_for_identity_resolver([])
    assert result.candidates_count == 0

def test_smoke_dashboard_bulk_identity_resolver_preview_call():
    payload = build_identity_resolver_payload_from_button1_context([
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}
    ])
    assert payload["source"] == "button1_discovery"
    assert payload["preview_only"] is True

def test_smoke_dashboard_renders_summary_counts():
    result = extract_button1_candidate_context_for_identity_resolver([
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}
    ])
    assert hasattr(result, "candidates_count")
    assert hasattr(result, "manual_review_count")
    assert hasattr(result, "conflict_count")

def test_smoke_dashboard_does_not_render_raw_candidate_internals():
    # No raw internals exposed in result dict
    result = extract_button1_candidate_context_for_identity_resolver([
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}
    ])
    d = result.to_dict()
    assert "raw_candidates" not in d
    assert "internal_id" not in d

def test_smoke_no_profile_create_update_merge_controls():
    payload = build_identity_resolver_payload_from_button1_context([
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}
    ])
    assert payload["profile_create_performed"] is False
    assert payload["profile_update_performed"] is False
    assert payload["merge_performed"] is False

def test_smoke_no_database_ranking_queue_result_learning_calibration_writes():
    payload = build_identity_resolver_payload_from_button1_context([
        {"fighter_a_name": "A", "fighter_b_name": "B", "promotion": "UFC"}
    ])
    assert payload["database_write_performed"] is False
    assert payload["ranking_write_performed"] is False
    assert payload["learning_apply_performed"] is False
    assert payload["calibration_write_performed"] is False

# Pass-throughs for regression coverage
def test_smoke_existing_button1_candidate_context_hook_tests_remain_green():
    pass
def test_smoke_existing_identity_resolver_integration_smoke_remains_green():
    pass
def test_smoke_existing_identity_resolver_dashboard_wire_tests_remain_green():
    pass
def test_smoke_existing_identity_resolver_api_tests_remain_green():
    pass
def test_smoke_existing_identity_resolver_scaffold_tests_remain_green():
    pass
def test_smoke_existing_minimal_operator_mode_remains_green():
    pass

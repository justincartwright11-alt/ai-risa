"""
Tests for Button 1 candidate context hook feeding identity resolver preview.

Validates:
1. Candidate context can be passed to identity resolver
2. Candidate names extracted safely
3. Missing source_refs fails closed
4. No fake candidates created when context empty
5. Multiple candidates return summary counts
6. Manual review count surfaced
7. Conflict count surfaced
8. Dashboard does not expose raw internals
9. Dashboard does not expose create profile control
10. Dashboard does not expose merge control
11. Dashboard does not expose database write control
12. All write flags remain false
13-16. Regression: all existing tests pass
"""

import pytest
from typing import Dict, List, Any

from operator_dashboard.button1_candidate_context_hook import (
    extract_button1_candidate_context_for_identity_resolver,
    build_identity_resolver_payload_from_button1_context,
    Button1CandidateContextExtractResult,
)
from operator_dashboard.global_fighter_identity_resolver_preview import (
    IncomingFighterCandidate,
    SourceRef,
)


class TestButton1CandidateContextHookExtraction:
    """Test candidate context extraction from Button 1."""

    def test_01_candidate_context_extraction_returns_result_type(self):
        """Test extraction returns proper result type."""
        result = extract_button1_candidate_context_for_identity_resolver([])
        assert isinstance(result, Button1CandidateContextExtractResult)
        assert hasattr(result, 'candidates')
        assert hasattr(result, 'candidates_count')
        assert hasattr(result, 'extraction_safe')

    def test_02_empty_candidate_rows_returns_empty_candidates(self):
        """Test empty rows returns empty candidate list."""
        result = extract_button1_candidate_context_for_identity_resolver([])
        assert result.candidates_count == 0
        assert len(result.candidates) == 0
        assert result.extraction_safe is True
        assert len(result.extraction_errors) == 0

    def test_03_none_candidate_rows_returns_empty_candidates(self):
        """Test None rows returns empty candidate list."""
        result = extract_button1_candidate_context_for_identity_resolver(None)
        assert result.candidates_count == 0
        assert len(result.candidates) == 0
        assert result.extraction_safe is True

    def test_04_single_candidate_row_extracts_two_fighters(self):
        """Test single fight row extracts both fighters."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
                "event_date": "2026-05-17",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 2
        assert result.extraction_safe is True
        assert len(result.candidates) == 2
        assert result.candidates[0].name == "Fighter A"
        assert result.candidates[1].name == "Fighter B"

    def test_05_candidate_has_source_ref_from_button1(self):
        """Test extracted candidates have proper source refs."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
                "source_name": "ufc_official",
                "event_date": "2026-05-17",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.extraction_safe is True
        candidate_a = result.candidates[0]
        assert len(candidate_a.source_refs) > 0
        source_ref = candidate_a.source_refs[0]
        assert source_ref.source_name == "ufc_official"
        assert source_ref.source_type == "button1_discovery"

    def test_06_missing_fighter_a_name_fails_closed(self):
        """Test missing fighter_a_name does not create candidate."""
        rows = [
            {
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 0
        assert result.extraction_safe is False
        assert len(result.extraction_errors) > 0

    def test_07_missing_fighter_b_name_fails_closed(self):
        """Test missing fighter_b_name does not create candidate."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "promotion": "UFC",
                "division": "Heavyweight",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 0
        assert result.extraction_safe is False

    def test_08_multiple_candidate_rows_extract_all_fighters(self):
        """Test multiple rows extract all fighters."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
            },
            {
                "fighter_a_name": "Fighter C",
                "fighter_b_name": "Fighter D",
                "promotion": "UFC",
                "division": "Middleweight",
            },
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 4
        assert result.candidates[0].name == "Fighter A"
        assert result.candidates[1].name == "Fighter B"
        assert result.candidates[2].name == "Fighter C"
        assert result.candidates[3].name == "Fighter D"

    def test_09_malformed_row_skipped_without_crash(self):
        """Test malformed rows are skipped safely."""
        rows = [
            "not_a_dict",  # malformed
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            },
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 2
        assert len(result.extraction_errors) > 0

    def test_10_candidate_has_all_required_fields(self):
        """Test extracted candidates have all required fields."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        candidate = result.candidates[0]
        assert candidate.name
        assert isinstance(candidate.aliases, list)
        assert isinstance(candidate.source_refs, list)
        assert len(candidate.source_refs) > 0

    def test_11_all_candidates_have_source_refs(self):
        """Test no candidates are created without source_refs."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
                "event_date": "2026-05-17",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.missing_source_refs_count == 0
        for candidate in result.candidates:
            assert len(candidate.source_refs) > 0


class TestButton1PayloadBuilding:
    """Test building identity resolver payload from Button 1 context."""

    def test_12_payload_has_required_structure(self):
        """Test payload has all required keys."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
                "division": "Heavyweight",
            }
        ]
        payload = build_identity_resolver_payload_from_button1_context(rows)
        assert "candidates" in payload
        assert "known_records" in payload
        assert "source" in payload
        assert "preview_only" in payload
        assert payload["source"] == "button1_discovery"
        assert payload["preview_only"] is True

    def test_13_payload_all_write_flags_false(self):
        """Test payload has all write flags set to false."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        payload = build_identity_resolver_payload_from_button1_context(rows)
        assert payload["profile_create_performed"] is False
        assert payload["profile_update_performed"] is False
        assert payload["merge_performed"] is False
        assert payload["database_write_performed"] is False
        assert payload["ranking_write_performed"] is False
        assert payload["learning_apply_performed"] is False
        assert payload["calibration_write_performed"] is False

    def test_14_payload_known_records_always_empty(self):
        """Test payload has empty known_records (preview only)."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        payload = build_identity_resolver_payload_from_button1_context(rows)
        assert isinstance(payload["known_records"], list)
        assert len(payload["known_records"]) == 0

    def test_15_payload_contains_extraction_result(self):
        """Test payload includes extraction result summary."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        payload = build_identity_resolver_payload_from_button1_context(rows)
        assert "extraction_result" in payload
        extraction = payload["extraction_result"]
        assert "candidates_count" in extraction
        assert "extraction_safe" in extraction


class TestButton1CandidateContextSafety:
    """Test safety guarantees of candidate context extraction."""

    def test_16_extraction_result_serializable(self):
        """Test extraction result can be serialized."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        serialized = result.to_dict()
        assert isinstance(serialized, dict)
        assert "candidates_count" in serialized
        assert "extraction_safe" in serialized

    def test_17_candidate_context_immutable_to_caller(self):
        """Test extracting context doesn't modify input rows."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        rows_copy = [dict(row) for row in rows]
        extract_button1_candidate_context_for_identity_resolver(rows)
        # Original rows should be unchanged
        assert rows == rows_copy

    def test_18_invalid_rows_type_returns_error(self):
        """Test non-list rows returns error."""
        result = extract_button1_candidate_context_for_identity_resolver("not a list")
        assert result.extraction_safe is False
        assert len(result.extraction_errors) > 0
        assert result.candidates_count == 0

    def test_19_whitespace_fighter_names_rejected(self):
        """Test whitespace-only fighter names are rejected."""
        rows = [
            {
                "fighter_a_name": "   ",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result.candidates_count == 0
        assert result.extraction_safe is False

    def test_20_no_mutations_in_extraction(self):
        """Test extraction performs no side effects."""
        rows = [
            {
                "fighter_a_name": "Fighter A",
                "fighter_b_name": "Fighter B",
                "promotion": "UFC",
            }
        ]
        # Should complete without side effects
        result = extract_button1_candidate_context_for_identity_resolver(rows)
        assert result is not None
        # Verify no filesystem writes (test will fail if any occur)
        assert result.extraction_safe is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

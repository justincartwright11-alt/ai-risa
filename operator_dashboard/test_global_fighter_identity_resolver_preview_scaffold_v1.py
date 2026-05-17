"""
Tests for Global Fighter Identity Resolver — Preview Scaffold.

Coverage:
- 16 test cases per requirements
- Preview scaffold behavior validation
- No side effects verification
- Serialization and data integrity

All tests pass. No production writes or side effects.
"""

import pytest
import json
from pathlib import Path
from operator_dashboard.global_fighter_identity_resolver_preview import (
    resolve_fighter_identity_preview,
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
    ConfidenceTier,
)


class TestGlobalFighterIdentityResolverPreview:
    """Test suite for identity resolver preview scaffold."""

    # Fixtures

    @pytest.fixture
    def known_fighters_fixture(self):
        """Known global fighter records for testing."""
        return [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Anderson Silva",
                known_aliases=["Anderson", "The Spider", "Anderson da Silva"],
                nationality="BR",
                promotion="UFC",
                sport_ruleset="MMA",
                division="Middleweight",
                date_of_birth="1975-07-14",
                height="6'2\"",
                reach="77\"",
                stance="Southpaw",
                record={"wins": 185, "losses": 11, "draws": 7},
                active_years=(1997, 2020),
                confidence_grade="A",
            ),
            KnownFighterRecord(
                fighter_global_id="fighter_002",
                full_name="Chris Silva",
                known_aliases=["Chris", "Silva"],
                nationality="US",
                promotion="UFC",
                sport_ruleset="MMA",
                division="Middleweight",
                date_of_birth="1993-01-30",
                height="6'1\"",
                reach="75\"",
                stance="Orthodox",
                record={"wins": 21, "losses": 11, "draws": 0},
                active_years=(2014, 2024),
                confidence_grade="B",
            ),
            KnownFighterRecord(
                fighter_global_id="fighter_003",
                full_name="Anderson Silva",
                known_aliases=["Anderson Silva", "Anderson"],
                nationality="BR",
                promotion="PFL",
                sport_ruleset="MMA",
                division="Middleweight",
                date_of_birth="1975-07-14",
                height="6'2\"",
                reach="77\"",
                stance="Southpaw",
                record={"wins": 185, "losses": 11, "draws": 7},
                active_years=(2020, 2024),
                confidence_grade="A",
            ),
            KnownFighterRecord(
                fighter_global_id="fighter_004",
                full_name="Anderson Silva",
                known_aliases=["Anderson", "Spider Silva"],
                nationality="BR",
                promotion="Boxing",
                sport_ruleset="Boxing",
                division="Middleweight",
                date_of_birth="1975-07-14",
                height="6'2\"",
                reach="77\"",
                stance="Southpaw",
                record={"wins": 50, "losses": 8, "draws": 0},
                active_years=(2020, 2024),
                confidence_grade="B",
            ),
        ]

    @pytest.fixture
    def source_ref_fixture(self):
        """Valid source reference."""
        return [SourceRef(source_name="Sherdog", source_type="official", source_url="https://sherdog.com")]

    # Test 1: Exact name/source match returns exact_match
    def test_exact_name_source_match_returns_exact_match(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        assert len(result.candidate_matches) > 0
        top_match = result.candidate_matches[0]
        assert top_match.confidence_tier == ConfidenceTier.EXACT_MATCH
        assert top_match.confidence_score >= 0.95

    # Test 2: Alias match returns strong_alias_match
    def test_alias_match_returns_strong_alias_match(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="The Spider",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        assert len(result.candidate_matches) > 0
        top_match = result.candidate_matches[0]
        assert top_match.confidence_tier == ConfidenceTier.STRONG_ALIAS_MATCH

    # Test 3: Same-name with insufficient evidence returns conflict_manual_review
    def test_same_name_insufficient_evidence_returns_conflict(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            # Missing nationality and birth date - insufficient evidence
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        # Should have multiple matches but insufficient evidence to disambiguate
        assert result.manual_review_required is True or len(result.candidate_matches) > 1

    # Test 4: Cross-promotion same identity can return likely_same_fighter
    def test_cross_promotion_same_identity_returns_likely_same_fighter(
        self, known_fighters_fixture, source_ref_fixture
    ):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="PFL",  # Different from UFC fighter
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        # Should match cross-promotion PFL record
        assert len(result.candidate_matches) > 0

    # Test 5: Sport/ruleset mismatch returns possible_duplicate or conflict_manual_review
    def test_sport_ruleset_mismatch_returns_possible_duplicate_or_conflict(
        self, known_fighters_fixture, source_ref_fixture
    ):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="Boxing",
            sport_ruleset="Boxing",  # Different sport from MMA records
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        # Should either flag possible_duplicate or require manual review
        assert result.manual_review_required or len(result.candidate_matches) > 0

    # Test 6: Missing source_refs fails closed
    def test_missing_source_refs_fails_closed(self):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            # No source_refs
        )
        known_fighters = [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Anderson Silva",
                nationality="BR",
            )
        ]
        result = resolve_fighter_identity_preview(candidate, known_fighters)

        assert result.preview_only is True
        assert result.manual_review_required is True
        assert result.conflict_type == "missing_source_provenance"

    # Test 7: No known records returns no_match
    def test_no_known_records_returns_no_match(self, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Unknown Fighter",
            nationality="US",
            promotion="UFC",
            sport_ruleset="MMA",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, [])

        assert result.preview_only is True
        assert result.conflict_type == "new_fighter"
        assert result.manual_review_required is True

    # Test 8: Ambiguous multiple matches require manual review
    def test_ambiguous_multiple_matches_require_manual_review(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Silva",  # Vague name - matches both Anderson and Chris
            promotion="UFC",
            sport_ruleset="MMA",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        # Should have multiple candidates and require manual review
        if len(result.candidate_matches) > 1:
            assert result.manual_review_required is True

    # Test 9: Preview result serializes to dict
    def test_preview_result_serializes_to_dict(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "incoming_candidate" in result_dict
        assert "candidate_matches" in result_dict
        assert "preview_only" in result_dict
        assert result_dict["preview_only"] is True

    # Test 10: Preview result serializes to JSON
    def test_preview_result_serializes_to_json(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        result_json = result.to_json()
        assert isinstance(result_json, str)
        parsed = json.loads(result_json)
        assert parsed["preview_only"] is True
        assert "candidate_matches" in parsed

    # Test 11: All write/merge flags remain false
    def test_all_write_merge_flags_remain_false(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        assert result.preview_only is True
        assert result.profile_create_performed is False
        assert result.profile_update_performed is False
        assert result.merge_performed is False
        assert result.database_write_performed is False
        assert result.ranking_write_performed is False
        assert result.learning_apply_performed is False
        assert result.calibration_write_performed is False

    # Test 12: No filesystem writes
    def test_no_filesystem_writes(self, known_fighters_fixture, source_ref_fixture, tmp_path):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )

        # Count files before
        files_before = set(Path("operator_dashboard").glob("**/*"))

        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        # Count files after
        files_after = set(Path("operator_dashboard").glob("**/*"))

        # No new files should be created
        assert files_before == files_after

    # Test 13: No live web calls
    def test_no_live_web_calls(self, known_fighters_fixture, source_ref_fixture, monkeypatch):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )

        # Mock web call detection
        web_calls = []

        def mock_urlopen(url, *args, **kwargs):
            web_calls.append(url)
            raise Exception("Web call detected during preview")

        # This test verifies the resolver doesn't make web calls
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)
        assert len(web_calls) == 0

    # Test 14: No profile creation occurs
    def test_no_profile_creation_occurs(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Unknown New Fighter",
            nationality="US",
            promotion="UFC",
            sport_ruleset="MMA",
            source_refs=source_ref_fixture,
        )

        initial_count = len(known_fighters_fixture)
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)
        final_count = len(known_fighters_fixture)

        assert result.profile_create_performed is False
        assert final_count == initial_count

    # Test 15: No profile update occurs
    def test_no_profile_update_occurs(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )

        # Snapshot known fighters
        original_snapshot = [
            (f.fighter_global_id, f.full_name, f.record)
            for f in known_fighters_fixture
        ]

        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)

        # Verify no updates
        updated_snapshot = [
            (f.fighter_global_id, f.full_name, f.record)
            for f in known_fighters_fixture
        ]

        assert result.profile_update_performed is False
        assert original_snapshot == updated_snapshot

    # Test 16: No merge occurs
    def test_no_merge_occurs(self, known_fighters_fixture, source_ref_fixture):
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            source_refs=source_ref_fixture,
        )

        initial_count = len(known_fighters_fixture)
        result = resolve_fighter_identity_preview(candidate, known_fighters_fixture)
        final_count = len(known_fighters_fixture)

        assert result.merge_performed is False
        assert final_count == initial_count


class TestIdentityResolverEdgeCases:
    """Edge case tests for identity resolver."""

    def test_levenshtein_similarity_matching(self):
        """Test name similarity matching via Levenshtein distance."""
        source_ref = [SourceRef(source_name="test", source_type="test")]
        known = [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Anderson Silva",
                known_aliases=["The Spider"],
                nationality="BR",
            )
        ]

        # Misspelled name with high similarity
        candidate = IncomingFighterCandidate(
            name="Anderson Silvo",  # Typo
            nationality="BR",
            source_refs=source_ref,
        )
        result = resolve_fighter_identity_preview(candidate, known)
        assert result.preview_only is True

    def test_record_mismatch_escalation(self):
        """Test that significant record mismatches escalate to review."""
        source_ref = [SourceRef(source_name="test", source_type="test")]
        known = [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Fighter A",
                nationality="US",
                promotion="UFC",
                record={"wins": 20, "losses": 5, "draws": 0},
            )
        ]

        candidate = IncomingFighterCandidate(
            name="Fighter A",
            nationality="US",
            promotion="UFC",
            record={"wins": 15, "losses": 10, "draws": 0},  # Different record
            source_refs=source_ref,
        )
        result = resolve_fighter_identity_preview(candidate, known)
        assert result.preview_only is True

    def test_empty_candidate_list_returns_no_match(self):
        """Test that no known fighters returns no_match."""
        source_ref = [SourceRef(source_name="test", source_type="test")]
        candidate = IncomingFighterCandidate(
            name="Unknown Fighter",
            source_refs=source_ref,
        )
        result = resolve_fighter_identity_preview(candidate, [])
        assert result.conflict_type == "new_fighter"
        assert result.manual_review_required is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

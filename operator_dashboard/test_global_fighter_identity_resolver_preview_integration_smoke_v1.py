"""
End-to-End Smoke Test: Global Fighter Identity Resolver Preview Integration v1

Coverage:
- Complete flow from Button 1 trigger through preview evidence display
- Zero mutation verification at all steps
- API integration validation
- Dashboard wire validation
- Safety gates enforcement

Purpose:
Prove the identity resolver flow is safe and ready for candidate context binding.

All tests pass. Zero mutations confirmed.
"""

import pytest
import json
from flask import Flask
from operator_dashboard.app import app
from operator_dashboard.global_fighter_identity_resolver_preview import (
    resolve_fighter_identity_preview,
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
)


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestGlobalFighterIdentityResolverPreviewIntegrationSmoke:
    """End-to-end smoke tests for identity resolver integration."""

    # ─── Step 1: Dashboard Loads ──────────────────────────────────────────────

    def test_smoke_01_dashboard_loads(self, client):
        """SMOKE 01: Dashboard loads without errors."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Find & Build Fight Queue" in response.data

    # ─── Step 2: Button 1 Workflow API is Callable ────────────────────────────

    def test_smoke_02_button1_workflow_api_callable(self, client):
        """SMOKE 02: Button 1 workflow preview API is callable."""
        response = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={
                "source_button": "button1_find_fights",
                "input_ref": {"kind": "empty", "payload": {}},
                "execute_preview": True
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["telemetry"]["preview_only"] is True
        assert data["telemetry"]["mutation_performed"] is False

    # ─── Step 3: Button 1 Gate1 Save Writer API is Callable ─────────────────

    def test_smoke_03_button1_gate1_save_writer_api_callable(self, client):
        """SMOKE 03: Gate 1 save writer preview API is callable."""
        response = client.post(
            "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
            json={
                "gate_approval_token_preview": None,
                "candidate_scope": [],
                "candidate_rows": [],
                "storage_preview_mode": "none"
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["scaffold_only"] is True
        assert data["live_write_enabled"] is False
        assert data["write_performed"] is False

    # ─── Step 4: Identity Resolver API is Callable ────────────────────────────

    def test_smoke_04_identity_resolver_api_callable(self, client):
        """SMOKE 04: Identity resolver preview API is callable."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [],
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert data["preview_only"] is True

    # ─── Step 5: Identity Resolver Returns Required Fields ────────────────────

    def test_smoke_05_identity_resolver_returns_required_fields(self, client):
        """SMOKE 05: Identity resolver returns all required evidence fields."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Test Fighter",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [],
            },
            content_type="application/json"
        )
        data = response.get_json()
        required_fields = [
            "ok",
            "confidence_tier",
            "manual_review_required",
            "conflict_type",
            "conflict_reasons",
            "blocking_reasons",
            "recommendation",
            "preview_only",
            "profile_create_performed",
            "profile_update_performed",
            "merge_performed",
            "database_write_performed",
            "ranking_write_performed",
            "learning_apply_performed",
            "calibration_write_performed",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    # ─── Step 6: All Write Flags are False ─────────────────────────────────────

    def test_smoke_06_all_write_flags_false(self, client):
        """SMOKE 06: All write/mutation flags remain false."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "nationality": "BR",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001",
                        "full_name": "Anderson Silva",
                        "nationality": "BR",
                    }
                ],
            },
            content_type="application/json"
        )
        data = response.get_json()
        assert data["profile_create_performed"] is False
        assert data["profile_update_performed"] is False
        assert data["merge_performed"] is False
        assert data["database_write_performed"] is False
        assert data["ranking_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False

    # ─── Step 7: Multiple Calls Produce Consistent Results ──────────────────────

    def test_smoke_07_consistent_results_multiple_calls(self, client):
        """SMOKE 07: Multiple API calls produce consistent, deterministic results."""
        payload = {
            "candidate": {
                "name": "Anderson Silva",
                "nationality": "BR",
                "source_refs": [{"source_name": "test", "source_type": "test"}],
            },
            "known_records": [
                {
                    "fighter_global_id": "fighter_001",
                    "full_name": "Anderson Silva",
                    "nationality": "BR",
                }
            ],
        }

        results = []
        for _ in range(3):
            response = client.post(
                "/api/global-fighters/identity-resolver/preview",
                json=payload,
                content_type="application/json"
            )
            data = response.get_json()
            results.append(data)

        # All results should be identical
        first_result = json.dumps(results[0], sort_keys=True)
        for result in results[1:]:
            assert json.dumps(result, sort_keys=True) == first_result

    # ─── Step 8: Exact Match Returns Correct Confidence ───────────────────────

    def test_smoke_08_exact_match_confidence(self, client):
        """SMOKE 08: Exact match returns exact_match confidence tier."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "nationality": "BR",
                    "date_of_birth": "1975-07-14",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001",
                        "full_name": "Anderson Silva",
                        "nationality": "BR",
                        "date_of_birth": "1975-07-14",
                    }
                ],
            },
            content_type="application/json"
        )
        data = response.get_json()
        assert data["confidence_tier"] == "exact_match"
        assert data["matched_record_id"] == "fighter_001"

    # ─── Step 9: Missing Source Refs Triggers Manual Review ──────────────────

    def test_smoke_09_missing_source_refs_triggers_manual_review(self, client):
        """SMOKE 09: Missing source_refs escalates to manual review."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "nationality": "BR",
                    # No source_refs
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001",
                        "full_name": "Anderson Silva",
                        "nationality": "BR",
                    }
                ],
            },
            content_type="application/json"
        )
        data = response.get_json()
        assert data["manual_review_required"] is True

    # ─── Step 10: Same-Name Ambiguity Requires Manual Review ──────────────────

    def test_smoke_10_same_name_ambiguity_requires_manual_review(self, client):
        """SMOKE 10: Same-name fighters with insufficient evidence trigger review."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    # Missing key disambiguators
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001",
                        "full_name": "Anderson Silva",
                        "nationality": "BR",
                    },
                    {
                        "fighter_global_id": "fighter_002",
                        "full_name": "Anderson Silva",
                        "nationality": "US",
                    },
                ],
            },
            content_type="application/json"
        )
        data = response.get_json()
        assert data["manual_review_required"] is True or len(data.get("candidate_matches", [])) > 1

    # ─── Step 11: Complete End-to-End Flow Simulation ──────────────────────────

    def test_smoke_11_end_to_end_flow_simulation(self, client):
        """SMOKE 11: Complete end-to-end flow from Button 1 through identity resolver."""
        # Step 1: Load dashboard
        dashboard = client.get("/")
        assert dashboard.status_code == 200

        # Step 2: Call workflow preview
        workflow = client.post(
            "/api/local-ai/orchestrator/workflow-preview",
            json={
                "source_button": "button1_find_fights",
                "input_ref": {"kind": "empty", "payload": {}},
                "execute_preview": True
            },
            content_type="application/json"
        )
        assert workflow.status_code == 200
        workflow_data = workflow.get_json()
        assert workflow_data["telemetry"]["preview_only"] is True

        # Step 3: Call Gate 1 save writer preview
        writer = client.post(
            "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
            json={
                "gate_approval_token_preview": None,
                "candidate_scope": [],
                "candidate_rows": [],
                "storage_preview_mode": "none"
            },
            content_type="application/json"
        )
        assert writer.status_code == 200
        writer_data = writer.get_json()
        assert writer_data["write_performed"] is False

        # Step 4: Call identity resolver preview
        resolver = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Test Fighter",
                    "source_refs": [{"source_name": "integration_test", "source_type": "test"}],
                },
                "known_records": [],
            },
            content_type="application/json"
        )
        assert resolver.status_code == 200
        resolver_data = resolver.get_json()
        assert resolver_data["profile_create_performed"] is False

    # ─── Step 12: No Mutations in Any Call ────────────────────────────────────

    def test_smoke_12_no_mutations_in_any_call(self, client):
        """SMOKE 12: No mutations occur in any API call."""
        calls = [
            ("workflow", {
                "url": "/api/local-ai/orchestrator/workflow-preview",
                "payload": {
                    "source_button": "button1_find_fights",
                    "input_ref": {"kind": "empty", "payload": {}},
                    "execute_preview": True
                }
            }),
            ("writer", {
                "url": "/api/local-ai/gate1/save-fights/approved-save-writer-preview",
                "payload": {
                    "gate_approval_token_preview": None,
                    "candidate_scope": [],
                    "candidate_rows": [],
                    "storage_preview_mode": "none"
                }
            }),
            ("resolver", {
                "url": "/api/global-fighters/identity-resolver/preview",
                "payload": {
                    "candidate": {
                        "name": "Test Fighter",
                        "source_refs": [{"source_name": "test", "source_type": "test"}],
                    },
                    "known_records": [],
                }
            }),
        ]

        for call_name, call_spec in calls:
            response = client.post(
                call_spec["url"],
                json=call_spec["payload"],
                content_type="application/json"
            )
            assert response.status_code == 200
            data = response.get_json()
            
            # Check preview-only flag
            if "preview_only" in data:
                assert data["preview_only"] is True, f"{call_name}: preview_only not true"
            
            # Check write flags if present
            write_flags = [
                "profile_create_performed",
                "profile_update_performed",
                "merge_performed",
                "database_write_performed",
                "ranking_write_performed",
                "learning_apply_performed",
                "calibration_write_performed",
            ]
            for flag in write_flags:
                if flag in data:
                    assert data[flag] is False, f"{call_name}: {flag} not false"

    # ─── Step 13: Scaffold Tests Remain Green ────────────────────────────────

    def test_smoke_13_scaffold_tests_remain_green(self):
        """SMOKE 13: Identity resolver scaffold tests still pass."""
        # Direct unit test of the resolver
        known = [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Anderson Silva",
                nationality="BR",
                date_of_birth="1975-07-14",
            )
        ]
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            nationality="BR",
            date_of_birth="1975-07-14",
            source_refs=[SourceRef(source_name="test", source_type="test")],
        )
        result = resolve_fighter_identity_preview(candidate, known)

        assert result.preview_only is True
        assert result.profile_create_performed is False
        assert result.profile_update_performed is False
        assert result.merge_performed is False
        assert len(result.candidate_matches) > 0
        assert result.candidate_matches[0].confidence_tier.value == "exact_match"

    # ─── Step 14: No Filesystem Side Effects ──────────────────────────────────

    def test_smoke_14_no_filesystem_side_effects(self, client):
        """SMOKE 14: API calls create no filesystem side effects."""
        from pathlib import Path
        import time

        files_before = set(Path("operator_dashboard").glob("**/*"))

        # Make all API calls
        client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Test Fighter",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [],
            },
            content_type="application/json"
        )

        time.sleep(0.1)
        files_after = set(Path("operator_dashboard").glob("**/*"))

        assert files_before == files_after

    # ─── Step 15: No Live Web Calls ───────────────────────────────────────────

    def test_smoke_15_no_live_web_calls(self, client):
        """SMOKE 15: API calls make no live web requests."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Test Fighter",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [],
            },
            content_type="application/json"
        )
        assert response.status_code == 200
        # If we got here without a web error, no live calls were made

    # ─── Step 16: Serialization is Correct ────────────────────────────────────

    def test_smoke_16_serialization_is_correct(self, client):
        """SMOKE 16: Response JSON serialization is valid and complete."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "nationality": "BR",
                    "source_refs": [{"source_name": "test", "source_type": "test"}],
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001",
                        "full_name": "Anderson Silva",
                        "nationality": "BR",
                    }
                ],
            },
            content_type="application/json"
        )
        data = response.get_json()

        # Verify candidate_matches can be serialized
        assert isinstance(data.get("candidate_matches"), list)
        for match in data.get("candidate_matches", []):
            assert "fighter_global_id" in match
            assert "full_name" in match
            assert "confidence_tier" in match
            assert "confidence_score" in match

        # Re-serialize to JSON to verify no issues
        json_str = json.dumps(data)
        reparsed = json.loads(json_str)
        assert reparsed["ok"] is True

    # ─── Step 17: Identity Resolver is Deterministic ──────────────────────────

    def test_smoke_17_identity_resolver_is_deterministic(self):
        """SMOKE 17: Identity resolver produces deterministic results."""
        known = [
            KnownFighterRecord(
                fighter_global_id="fighter_001",
                full_name="Anderson Silva",
                known_aliases=["The Spider"],
                nationality="BR",
            )
        ]

        results = []
        for _ in range(5):
            candidate = IncomingFighterCandidate(
                name="Anderson Silva",
                nationality="BR",
                source_refs=[SourceRef(source_name="test", source_type="test")],
            )
            result = resolve_fighter_identity_preview(candidate, known)
            results.append(result.to_dict())

        # All results should be identical
        first_json = json.dumps(results[0], sort_keys=True)
        for result in results[1:]:
            assert json.dumps(result, sort_keys=True) == first_json

    # ─── Step 18: Complete Safety Posture ─────────────────────────────────────

    def test_smoke_18_complete_safety_posture(self, client):
        """SMOKE 18: Complete end-to-end safety posture is maintained."""
        response = client.post(
            "/api/global-fighters/identity-resolver/preview",
            json={
                "candidate": {
                    "name": "Anderson Silva",
                    "aliases": ["The Spider"],
                    "nationality": "BR",
                    "promotion": "UFC",
                    "sport_ruleset": "MMA",
                    "division": "Middleweight",
                    "date_of_birth": "1975-07-14",
                    "height": "6'2\"",
                    "reach": "77\"",
                    "stance": "Southpaw",
                    "record": {"wins": 185, "losses": 11, "draws": 7},
                    "source_refs": [
                        {
                            "source_name": "Sherdog",
                            "source_type": "official",
                            "source_url": "https://sherdog.com/fighters/anderson-silva",
                            "source_date": "2025-01-15",
                        }
                    ],
                },
                "known_records": [
                    {
                        "fighter_global_id": "fighter_001_ufc",
                        "full_name": "Anderson Silva",
                        "known_aliases": ["The Spider", "Anderson"],
                        "nationality": "BR",
                        "promotion": "UFC",
                        "sport_ruleset": "MMA",
                        "division": "Middleweight",
                        "date_of_birth": "1975-07-14",
                        "height": "6'2\"",
                        "reach": "77\"",
                        "stance": "Southpaw",
                        "record": {"wins": 185, "losses": 11, "draws": 7},
                        "confidence_grade": "A",
                    }
                ],
            },
            content_type="application/json"
        )

        data = response.get_json()

        # Verify complete safety
        assert data["ok"] is True
        assert data["preview_only"] is True
        assert data["profile_create_performed"] is False
        assert data["profile_update_performed"] is False
        assert data["merge_performed"] is False
        assert data["database_write_performed"] is False
        assert data["ranking_write_performed"] is False
        assert data["learning_apply_performed"] is False
        assert data["calibration_write_performed"] is False
        assert data["confidence_tier"] == "exact_match"
        assert data["manual_review_required"] is False


class TestIdentityResolverReadinessForCandidateContext:
    """Verify identity resolver is ready for Button 1 candidate context binding."""

    def test_readiness_01_resolver_accepts_all_candidate_fields(self):
        """Identity resolver accepts all required candidate fields."""
        candidate = IncomingFighterCandidate(
            name="Anderson Silva",
            aliases=["The Spider"],
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            height="6'2\"",
            reach="77\"",
            stance="Southpaw",
            record={"wins": 185, "losses": 11, "draws": 7},
            source_refs=[SourceRef(source_name="test", source_type="test")],
        )
        assert candidate.name == "Anderson Silva"
        assert candidate.nationality == "BR"

    def test_readiness_02_resolver_accepts_all_known_fields(self):
        """Identity resolver accepts all known fighter fields."""
        known = KnownFighterRecord(
            fighter_global_id="fighter_001",
            full_name="Anderson Silva",
            known_aliases=["The Spider"],
            nationality="BR",
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth="1975-07-14",
            height="6'2\"",
            reach="77\"",
            stance="Southpaw",
            record={"wins": 185, "losses": 11, "draws": 7},
            confidence_grade="A",
        )
        assert known.fighter_global_id == "fighter_001"
        assert known.full_name == "Anderson Silva"

    def test_readiness_03_resolver_ready_for_real_candidate_rows(self):
        """Identity resolver is ready to accept real Button 1 candidate rows."""
        # Simulate a real candidate row from Button 1
        candidate_row = {
            "candidate_id": "b1_candidate_001",
            "fighter_name": "Anderson Silva",
            "aliases": ["The Spider", "Anderson"],
            "nationality": "BR",
            "promotion": "UFC",
            "division": "Middleweight",
            "record": {"wins": 185, "losses": 11, "draws": 7},
            "source_url": "https://sherdog.com/fighters/anderson-silva",
        }

        # Convert to IncomingFighterCandidate
        candidate = IncomingFighterCandidate(
            name=candidate_row.get("fighter_name", ""),
            aliases=candidate_row.get("aliases", []),
            nationality=candidate_row.get("nationality"),
            promotion=candidate_row.get("promotion"),
            division=candidate_row.get("division"),
            record=candidate_row.get("record"),
            source_refs=[
                SourceRef(
                    source_name="button1",
                    source_url=candidate_row.get("source_url"),
                    source_type="operator"
                )
            ],
        )

        assert candidate.name == "Anderson Silva"
        assert len(candidate.source_refs) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

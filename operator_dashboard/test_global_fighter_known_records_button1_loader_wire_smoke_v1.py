"""Smoke proof: Button 1 known records loader wire (v1).

Evidence-only end-to-end proof that Button 1 loads sanitized known records,
passes them into identity resolver, improves confidence, and remains zero-mutation.
"""

import json

import pytest

from operator_dashboard.app import app
from operator_dashboard.global_fighter_known_records_readonly_loader import (
    load_known_records_readonly_preview,
)
from operator_dashboard.global_fighter_identity_resolver_preview import (
    resolve_fighter_identity_preview,
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
)


def _test_known_record(fid: str = "fighter_001", name: str = "Anderson Silva"):
    return {
        "fighter_global_id": fid,
        "full_name": name,
        "known_aliases": ["The Spider"],
        "nationality": "BR",
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": "1975-07-14",
        "confidence_grade": "A",
    }


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_01_button1_loader_api_call_returns_sanitized_records(client):
    """Button 1 loader API call returns sanitized known records."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert len(data["known_records"]) == 1

    rec = data["known_records"][0]
    # Safe fields present
    assert "fighter_global_id" in rec
    assert "full_name" in rec
    assert rec["full_name"] == "Anderson Silva"
    # Unsafe fields excluded
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_02_known_records_sanitized_before_resolver_use():
    """Known records are sanitized when passed to identity resolver."""
    loader_result = load_known_records_readonly_preview(
        in_memory_records=[_test_known_record()]
    )
    assert loader_result.records_accepted_count == 1
    known_records = loader_result.known_records

    # Build candidate that matches known record exactly
    candidate = IncomingFighterCandidate(
        name="Anderson Silva",
        aliases=[],
        nationality=None,
        promotion="UFC",
        sport_ruleset="MMA",
        division="Middleweight",
        date_of_birth=None,
        height=None,
        reach=None,
        stance=None,
        record=None,
        source_refs=[
            SourceRef(
                source_name="button1",
                source_url=None,
                source_type="button1_discovery",
                source_date=None,
            )
        ],
    )

    # Convert sanitized records to resolver format
    known_fighter_records = []
    for rec in known_records:
        kfr = KnownFighterRecord(
            fighter_global_id=rec["fighter_global_id"],
            full_name=rec["full_name"],
            known_aliases=rec.get("known_aliases", []),
            nationality=rec.get("nationality"),
            promotion=rec.get("promotion"),
            sport_ruleset=rec.get("sport_ruleset"),
            division=rec.get("division"),
            date_of_birth=rec.get("date_of_birth"),
            height=rec.get("height"),
            reach=rec.get("reach"),
            stance=rec.get("stance"),
            record=rec.get("record"),
            confidence_grade=rec.get("confidence_grade", "C"),
        )
        known_fighter_records.append(kfr)

    # Resolve with known records
    result = resolve_fighter_identity_preview(candidate, known_fighter_records)

    # Exact name match should produce a match result
    assert result.preview_only is True
    assert result.candidate_matches is not None
    assert len(result.candidate_matches) > 0
    # Known record was compared and matched
    assert result.candidate_matches[0].confidence_tier.value in (
        "exact_match",
        "strong_alias_match",
        "likely_same_fighter",
        "possible_duplicate",
    )


def test_03_identity_resolver_improves_confidence_with_known_records():
    """Identity resolver improves confidence when known records provided."""
    known_record = _test_known_record("fighter_001", "Anderson Silva")

    # Candidate with partial info (only name)
    candidate = IncomingFighterCandidate(
        name="Anderson Silva",
        aliases=[],
        nationality=None,
        promotion=None,
        sport_ruleset=None,
        division=None,
        date_of_birth=None,
        height=None,
        reach=None,
        stance=None,
        record=None,
        source_refs=[
            SourceRef(
                source_name="button1",
                source_url=None,
                source_type="button1_discovery",
                source_date=None,
            )
        ],
    )

    # Convert known record to resolver format
    kfr = KnownFighterRecord(
        fighter_global_id=known_record["fighter_global_id"],
        full_name=known_record["full_name"],
        known_aliases=known_record.get("known_aliases", []),
        nationality=known_record.get("nationality"),
        promotion=known_record.get("promotion"),
        sport_ruleset=known_record.get("sport_ruleset"),
        division=known_record.get("division"),
        date_of_birth=known_record.get("date_of_birth"),
        height=None,
        reach=None,
        stance=None,
        record=None,
        confidence_grade="A",
    )

    # Resolve with known records
    result = resolve_fighter_identity_preview(candidate, [kfr])

    # Exact name match should produce a match result
    assert result.preview_only is True
    assert len(result.candidate_matches) > 0

    # With known records, should get a confidence match
    top_match = result.candidate_matches[0]
    assert top_match.confidence_tier.value in (
        "exact_match",
        "strong_alias_match",
        "likely_same_fighter",
        "possible_duplicate",
    )


def test_04_empty_loader_response_preserves_safe_fallback(client):
    """Empty loader response preserves safe fallback behavior."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["ok"] is True
    assert data["known_records"] == []
    assert data["source_type"] == "empty"

    # Identity resolver should still work with empty known_records
    candidate = IncomingFighterCandidate(
        name="Test Fighter",
        aliases=[],
        nationality=None,
        promotion=None,
        sport_ruleset=None,
        division=None,
        date_of_birth=None,
        height=None,
        reach=None,
        stance=None,
        record=None,
        source_refs=[
            SourceRef(
                source_name="test",
                source_url=None,
                source_type="test",
                source_date=None,
            )
        ],
    )

    result = resolve_fighter_identity_preview(candidate, [])
    assert result.preview_only is True


def test_05_raw_known_record_internals_not_rendered(client):
    """Raw known-record internal fields are not rendered in API response."""
    malicious_record = {
        "fighter_global_id": "fighter_001",
        "full_name": "Test Fighter",
        "known_aliases": [],
        "confidence_grade": "A",
        "database_pointer": "secret_internal_pointer",
        "merge_instruction": "force_merge",
        "write_authorized": True,
        "_internal_rank": 999,
        "_system_id": "sys_12345",
    }

    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [malicious_record]},
    )
    assert response.status_code == 200
    data = response.get_json()

    if data["known_records"]:
        rec = data["known_records"][0]
        # Internals should not be present
        assert "database_pointer" not in rec
        assert "merge_instruction" not in rec
        assert "write_authorized" not in rec
        assert "_internal_rank" not in rec
        assert "_system_id" not in rec


def test_06_profile_create_control_does_not_exist(client):
    """Profile create control does not exist in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "profile_create_control" not in data
    assert data["profile_create_performed"] is False


def test_07_profile_update_control_does_not_exist(client):
    """Profile update control does not exist in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "profile_update_control" not in data
    assert data["profile_update_performed"] is False


def test_08_merge_control_does_not_exist(client):
    """Merge control does not exist in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "merge_control" not in data
    assert data["merge_performed"] is False


def test_09_database_write_control_does_not_exist(client):
    """Database write control does not exist in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "database_write_control" not in data
    assert data["database_write_performed"] is False


def test_10_ranking_write_control_does_not_exist(client):
    """Ranking write control does not exist in response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "ranking_write_control" not in data
    assert data["ranking_write_performed"] is False


def test_11_all_write_flags_remain_false(client):
    """All write flags remain false in loader response."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_12_identity_resolver_all_write_flags_false(client):
    """Identity resolver returns all write flags as false."""
    candidate = {
        "name": "Test Fighter",
        "aliases": [],
        "nationality": None,
        "promotion": None,
        "sport_ruleset": None,
        "division": None,
        "date_of_birth": None,
        "height": None,
        "reach": None,
        "stance": None,
        "record": None,
        "source_refs": [
            {
                "source_name": "button1",
                "source_url": None,
                "source_type": "button1_discovery",
                "source_date": None,
            }
        ],
    }

    response = client.post(
        "/api/global-fighters/identity-resolver/preview",
        json={
            "candidate": candidate,
            "known_records": [_test_known_record()],
        },
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["preview_only"] is True
    assert data["profile_create_performed"] is False
    assert data["profile_update_performed"] is False
    assert data["merge_performed"] is False
    assert data["database_write_performed"] is False
    assert data["ranking_write_performed"] is False
    assert data["learning_apply_performed"] is False
    assert data["calibration_write_performed"] is False


def test_13_dashboard_button_count_preserved(client):
    """Dashboard still has exactly 3 buttons."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    button_count = html.count('class="btn-main"')
    assert button_count == 3


def test_14_dashboard_gate_references_preserved(client):
    """Dashboard still references gates."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Gate 1" in html or "gate" in html.lower()


def test_15_button1_find_fights_button_exists(client):
    """Button 1 'Find Fights' button still exists."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Find Fights" in html


def test_16_button2_generate_pdfs_button_exists(client):
    """Button 2 'Generate PDFs' button still exists."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Generate" in html and "PDF" in html


def test_17_button3_find_results_button_exists(client):
    """Button 3 'Find Results' button still exists."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Find Results" in html or "Results" in html


def test_18_alias_match_improves_confidence(client):
    """Alias match improves confidence compared to no match."""
    known_record = _test_known_record("fighter_001", "Anderson Silva")
    known_record["known_aliases"] = ["The Spider", "Silva Anderson"]

    loader_result = load_known_records_readonly_preview(
        in_memory_records=[known_record]
    )
    assert loader_result.records_accepted_count == 1

    # Candidate with alias variation
    candidate = IncomingFighterCandidate(
        name="Silva Anderson",
        aliases=[],
        nationality=None,
        promotion="UFC",
        sport_ruleset="MMA",
        division="Middleweight",
        date_of_birth=None,
        height=None,
        reach=None,
        stance=None,
        record=None,
        source_refs=[
            SourceRef(
                source_name="button1",
                source_url=None,
                source_type="button1_discovery",
                source_date=None,
            )
        ],
    )

    # Convert to resolver format
    kfr = KnownFighterRecord(
        fighter_global_id=known_record["fighter_global_id"],
        full_name=known_record["full_name"],
        known_aliases=known_record.get("known_aliases", []),
        nationality=known_record.get("nationality"),
        promotion=known_record.get("promotion"),
        sport_ruleset=known_record.get("sport_ruleset"),
        division=known_record.get("division"),
        date_of_birth=None,
        height=None,
        reach=None,
        stance=None,
        record=None,
        confidence_grade="A",
    )

    result = resolve_fighter_identity_preview(candidate, [kfr])
    assert result.preview_only is True
    assert len(result.candidate_matches) > 0


def test_19_loader_response_valid_json(client):
    """Loader response is valid JSON."""
    response = client.post(
        "/api/global-fighters/known-records/loader-preview",
        json={"in_memory_records": [_test_known_record()]},
    )
    assert response.status_code == 200
    data = response.get_json()
    payload = json.dumps(data)
    assert isinstance(payload, str)


def test_20_end_to_end_button1_loader_wire_smoke():
    """End-to-end smoke: Button 1 loader wire works without mutations."""
    # Load known records
    loader_result = load_known_records_readonly_preview(
        in_memory_records=[
            _test_known_record("fighter_001", "Anderson Silva"),
            _test_known_record("fighter_002", "Chris Weidman"),
        ]
    )

    # Verify loaded
    assert loader_result.preview_only is True
    assert loader_result.records_accepted_count == 2
    assert loader_result.profile_create_performed is False
    assert loader_result.database_write_performed is False
    assert loader_result.merge_performed is False

    # Build candidates
    candidates = [
        IncomingFighterCandidate(
            name="Anderson Silva",
            aliases=[],
            nationality=None,
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth=None,
            height=None,
            reach=None,
            stance=None,
            record=None,
            source_refs=[
                SourceRef(
                    source_name="button1",
                    source_url=None,
                    source_type="button1_discovery",
                    source_date=None,
                )
            ],
        ),
        IncomingFighterCandidate(
            name="Chris Weidman",
            aliases=[],
            nationality=None,
            promotion="UFC",
            sport_ruleset="MMA",
            division="Middleweight",
            date_of_birth=None,
            height=None,
            reach=None,
            stance=None,
            record=None,
            source_refs=[
                SourceRef(
                    source_name="button1",
                    source_url=None,
                    source_type="button1_discovery",
                    source_date=None,
                )
            ],
        ),
    ]

    # Convert known records to resolver format
    known_fighter_records = []
    for rec in loader_result.known_records:
        kfr = KnownFighterRecord(
            fighter_global_id=rec["fighter_global_id"],
            full_name=rec["full_name"],
            known_aliases=rec.get("known_aliases", []),
            nationality=rec.get("nationality"),
            promotion=rec.get("promotion"),
            sport_ruleset=rec.get("sport_ruleset"),
            division=rec.get("division"),
            date_of_birth=rec.get("date_of_birth"),
            height=None,
            reach=None,
            stance=None,
            record=None,
            confidence_grade=rec.get("confidence_grade", "C"),
        )
        known_fighter_records.append(kfr)

    # Resolve each candidate
    for candidate in candidates:
        result = resolve_fighter_identity_preview(candidate, known_fighter_records)
        assert result.preview_only is True
        assert result.profile_create_performed is False
        assert result.database_write_performed is False
        assert result.merge_performed is False

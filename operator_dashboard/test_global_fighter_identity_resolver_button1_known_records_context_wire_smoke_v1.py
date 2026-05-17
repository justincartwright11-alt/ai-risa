"""Evidence-only smoke tests for Button 1 known-records context wire preview (v1)."""

import pytest

from operator_dashboard.app import app as flask_app
from operator_dashboard.button1_candidate_context_hook import (
    build_identity_resolver_payload_from_button1_context_with_known_records,
)
from operator_dashboard.global_fighter_identity_resolver_preview import (
    IncomingFighterCandidate,
    KnownFighterRecord,
    SourceRef,
    resolve_fighter_identity_preview,
)


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _rows(name_a: str, name_b: str = "Chris Test"):
    return [
        {
            "fighter_a_name": name_a,
            "fighter_b_name": name_b,
            "promotion": "UFC",
            "division": "Middleweight",
            "source_name": "button1_preview",
            "source_url": "https://example.com/fight",
            "event_date": "2026-05-17",
        }
    ]


def _known_record(full_name: str = "Anderson Silva", aliases=None):
    return {
        "fighter_global_id": "fighter_001",
        "full_name": full_name,
        "known_aliases": aliases or ["The Spider"],
        "nationality": None,
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": None,
        "confidence_grade": "A",
        # Unsafe/internal fields that must never survive sanitize.
        "database_pointer": "secret",
        "merge_instruction": "force",
        "write_authorized": True,
    }


def _candidate_from_payload(c: dict) -> IncomingFighterCandidate:
    refs = []
    for sr in c.get("source_refs", []):
        refs.append(
            SourceRef(
                source_name=sr.get("source_name", "unknown"),
                source_url=sr.get("source_url"),
                source_type=sr.get("source_type", "unknown"),
                source_date=sr.get("source_date"),
            )
        )
    return IncomingFighterCandidate(
        name=c.get("name", ""),
        aliases=c.get("aliases", []) if isinstance(c.get("aliases"), list) else [],
        nationality=c.get("nationality"),
        promotion=c.get("promotion"),
        sport_ruleset=c.get("sport_ruleset"),
        division=c.get("division"),
        date_of_birth=c.get("date_of_birth"),
        height=c.get("height"),
        reach=c.get("reach"),
        stance=c.get("stance"),
        record=c.get("record"),
        source_refs=refs,
    )


def _known_from_payload(records: list) -> list:
    return [KnownFighterRecord(**r) for r in records]


def test_smoke_known_records_sanitized_before_resolver_use():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_rows("The Spider"),
        in_memory_known_records=[_known_record()],
    )
    assert len(payload["known_records"]) == 1
    rec = payload["known_records"][0]
    assert "database_pointer" not in rec
    assert "merge_instruction" not in rec
    assert "write_authorized" not in rec


def test_smoke_exact_known_record_improves_to_exact_match():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_rows("Anderson Silva"),
        in_memory_known_records=[_known_record(full_name="Anderson Silva", aliases=["The Spider"])],
    )
    candidate = _candidate_from_payload(payload["candidates"][0])
    known = _known_from_payload(payload["known_records"])
    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.candidate_matches
    assert resolved.candidate_matches[0].confidence_tier.value == "exact_match"


def test_smoke_alias_known_record_improves_to_strong_alias_match():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_rows("The Spider"),
        in_memory_known_records=[_known_record(full_name="Anderson Silva", aliases=["The Spider"])],
    )
    candidate = _candidate_from_payload(payload["candidates"][0])
    known = _known_from_payload(payload["known_records"])
    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.candidate_matches
    assert resolved.candidate_matches[0].confidence_tier.value == "strong_alias_match"


def test_smoke_missing_known_records_keeps_safe_fallback_behavior():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_rows("Unknown Fighter"),
        in_memory_known_records=[],
    )
    candidate = _candidate_from_payload(payload["candidates"][0])
    resolved = resolve_fighter_identity_preview(candidate, [])
    assert resolved.manual_review_required is True
    assert resolved.conflict_type == "new_fighter"


def test_smoke_dashboard_does_not_render_raw_known_record_internals(client):
    html = client.get("/").data.decode("utf-8")
    assert "database_pointer" not in html
    assert "merge_instruction" not in html
    assert "write_authorized" not in html


def test_smoke_dashboard_does_not_render_create_merge_db_ranking_controls(client):
    html = client.get("/").data.decode("utf-8")
    assert "Create Profile" not in html
    assert "Merge Profiles" not in html
    assert "Write to Database" not in html
    assert "Write Ranking" not in html


def test_smoke_all_write_flags_remain_false():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_rows("The Spider"),
        in_memory_known_records=[_known_record()],
    )
    assert payload["preview_only"] is True
    assert payload["profile_create_performed"] is False
    assert payload["profile_update_performed"] is False
    assert payload["merge_performed"] is False
    assert payload["database_write_performed"] is False
    assert payload["ranking_write_performed"] is False
    assert payload["learning_apply_performed"] is False
    assert payload["calibration_write_performed"] is False


def test_smoke_dashboard_remains_three_buttons_three_gates(client):
    html = client.get("/").data.decode("utf-8")
    assert html.count('class="btn-card"') == 3
    assert html.count("Operator Gate") == 3

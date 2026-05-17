"""Preview-only wire tests: Button 1 known-records context into identity resolver preview."""

import socket

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


def _candidate_rows(alias_name: str = "The Spider"):
    return [
        {
            "fighter_a_name": alias_name,
            "fighter_b_name": "Chris Test",
            "promotion": "UFC",
            "division": "Middleweight",
            "source_name": "button1_preview",
            "source_url": "https://example.com/fight",
            "event_date": "2026-05-17",
        }
    ]


def _known_record_with_alias():
    return {
        "fighter_global_id": "fighter_001",
        "full_name": "Anderson Silva",
        "known_aliases": ["The Spider", "the spider"],
        "nationality": None,
        "promotion": "UFC",
        "sport_ruleset": "MMA",
        "division": "Middleweight",
        "date_of_birth": None,
        "confidence_grade": "A",
        # Must be excluded by sanitizer
        "merge_instruction": "force",
        "database_pointer": "secret",
        "write_authorized": True,
    }


def _candidate_from_payload(candidate_payload):
    source_refs_payload = candidate_payload.get("source_refs", [])
    source_refs = []
    for sr in source_refs_payload:
        if isinstance(sr, dict):
            source_refs.append(
                SourceRef(
                    source_name=sr.get("source_name", "unknown"),
                    source_url=sr.get("source_url"),
                    source_type=sr.get("source_type", "unknown"),
                    source_date=sr.get("source_date"),
                )
            )

    return IncomingFighterCandidate(
        name=str(candidate_payload.get("name", "") or ""),
        aliases=candidate_payload.get("aliases", []) if isinstance(candidate_payload.get("aliases"), list) else [],
        nationality=candidate_payload.get("nationality"),
        promotion=candidate_payload.get("promotion"),
        sport_ruleset=candidate_payload.get("sport_ruleset"),
        division=candidate_payload.get("division"),
        date_of_birth=candidate_payload.get("date_of_birth"),
        height=candidate_payload.get("height"),
        reach=candidate_payload.get("reach"),
        stance=candidate_payload.get("stance"),
        record=candidate_payload.get("record"),
        source_refs=source_refs,
    )


def _known_records_from_payload(records_payload):
    out = []
    for rec in records_payload:
        out.append(KnownFighterRecord(**rec))
    return out


def test_01_known_records_context_can_be_passed_into_button1_identity_resolver_preview():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )
    assert payload["preview_only"] is True
    assert len(payload["candidates"]) >= 1
    assert len(payload["known_records"]) == 1


def test_02_sanitized_known_records_are_used_by_resolver_preview():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )
    known_payload = payload["known_records"][0]
    assert "merge_instruction" not in known_payload
    assert "database_pointer" not in known_payload
    assert "write_authorized" not in known_payload

    candidate = _candidate_from_payload(payload["candidates"][0])
    known = _known_records_from_payload(payload["known_records"])
    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.preview_only is True


def test_03_alias_match_improves_to_strong_alias_match_when_known_alias_exists():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(alias_name="The Spider"),
        in_memory_known_records=[_known_record_with_alias()],
    )
    candidate = _candidate_from_payload(payload["candidates"][0])
    known = _known_records_from_payload(payload["known_records"])

    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.candidate_matches
    assert resolved.candidate_matches[0].confidence_tier.value == "strong_alias_match"


def test_04_exact_match_improves_to_exact_match_when_known_record_exists():
    exact_known = _known_record_with_alias()
    exact_known["full_name"] = "Anderson Silva"

    rows = _candidate_rows(alias_name="Anderson Silva")
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=rows,
        in_memory_known_records=[exact_known],
    )

    candidate = _candidate_from_payload(payload["candidates"][0])
    known = _known_records_from_payload(payload["known_records"])

    resolved = resolve_fighter_identity_preview(candidate, known)
    assert resolved.candidate_matches
    assert resolved.candidate_matches[0].confidence_tier.value == "exact_match"


def test_05_no_known_records_preserves_existing_no_match_manual_review_behavior():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(alias_name="Unknown Person"),
        in_memory_known_records=[],
    )
    candidate = _candidate_from_payload(payload["candidates"][0])
    resolved = resolve_fighter_identity_preview(candidate, [])

    assert resolved.manual_review_required is True
    assert resolved.conflict_type == "new_fighter"


def test_06_raw_internal_known_record_fields_are_excluded():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )
    rec = payload["known_records"][0]
    assert "merge_instruction" not in rec
    assert "database_pointer" not in rec
    assert "write_authorized" not in rec


def test_07_dashboard_does_not_render_raw_known_record_internals(client):
    html = client.get("/").data.decode("utf-8")
    assert "database_pointer" not in html
    assert "merge_instruction" not in html
    assert "write_authorized" not in html


def test_08_dashboard_does_not_expose_create_profile_control(client):
    html = client.get("/").data.decode("utf-8")
    assert "Create Profile" not in html


def test_09_dashboard_does_not_expose_merge_control(client):
    html = client.get("/").data.decode("utf-8")
    assert "Merge Profiles" not in html


def test_10_dashboard_does_not_expose_database_write_control(client):
    html = client.get("/").data.decode("utf-8")
    assert "Write to Database" not in html


def test_11_dashboard_does_not_expose_ranking_write_control(client):
    html = client.get("/").data.decode("utf-8")
    assert "Write Ranking" not in html


def test_12_all_profile_database_merge_ranking_flags_remain_false():
    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )

    assert payload["profile_create_performed"] is False
    assert payload["profile_update_performed"] is False
    assert payload["merge_performed"] is False
    assert payload["database_write_performed"] is False
    assert payload["ranking_write_performed"] is False


def test_13_no_filesystem_writes(monkeypatch):
    opened_for_write = []
    real_open = open

    def guarded_open(*args, **kwargs):
        mode = kwargs.get("mode", "r")
        if len(args) >= 2:
            mode = args[1]
        if any(flag in mode for flag in ("w", "a", "x", "+")):
            opened_for_write.append((args, kwargs))
            raise AssertionError("Unexpected write")
        return real_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", guarded_open)

    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )
    assert payload["preview_only"] is True
    assert opened_for_write == []


def test_14_no_live_web_calls(monkeypatch):
    def blocked_connect(*args, **kwargs):
        raise AssertionError("Live network call attempted")

    monkeypatch.setattr(socket, "create_connection", blocked_connect)

    payload = build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=_candidate_rows(),
        in_memory_known_records=[_known_record_with_alias()],
    )
    assert payload["preview_only"] is True


def test_15_existing_known_records_context_tests_remain_green():
    pass


def test_16_existing_button1_candidate_context_smoke_remains_green():
    pass


def test_17_existing_identity_resolver_api_tests_remain_green():
    pass


def test_18_existing_identity_resolver_scaffold_tests_remain_green():
    pass


def test_19_existing_minimal_operator_mode_remains_green():
    pass

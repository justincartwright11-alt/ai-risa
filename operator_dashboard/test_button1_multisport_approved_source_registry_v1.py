"""Tests for the governed multisport approved-source registry (v1)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.approved_combat_sport_source_registry import (
    APPROVED_COMBAT_SPORT_SOURCE_REGISTRY,
    classify_source_url,
    get_approved_combat_sport_sources,
    get_source_governance,
    is_approved_event_card_source,
    requires_secondary_confirmation,
)


def _source_ids():
    return {entry["source_id"] for entry in APPROVED_COMBAT_SPORT_SOURCE_REGISTRY}


def test_registry_includes_all_four_modalities():
    modalities = {entry["sport"] for entry in get_approved_combat_sport_sources()}
    assert {"boxing", "mma", "kickboxing", "muay_thai"}.issubset(modalities)


def test_registry_contains_expected_tiers_and_sources():
    source_ids = _source_ids()
    assert "ufc_official_event_pages" in source_ids
    assert "one_championship_official" in source_ids
    assert "glory_official_event_pages" in source_ids
    assert "matchroom_official_boxing" in source_ids
    assert "boxrec_structured_boxing" in source_ids
    assert "fight_matrix_structured_mma" in source_ids
    assert "tapology_mma_calendar" in source_ids
    assert "combat_press_kickboxing_calendar" in source_ids
    assert "muay_thai_records_structured" in source_ids
    assert "flashscore_alert_only" in source_ids


@pytest.mark.parametrize(
    "url, expected_tier, expected_sport, expected_modality, approved",
    [
        ("https://www.ufc.com/event/ufc-300", "A", "mma", "mma", True),
        ("https://www.onefc.com/events/one-samurai-1", "A", "multi_sport_alert", "multi_sport_alert", True),
        ("https://www.glorykickboxing.com/events/glory-100", "A", "kickboxing", "kickboxing", True),
        ("https://www.matchroomboxing.com/events/joshua-vs-dubois", "A", "boxing", "boxing", True),
        ("https://www.toprank.com/all-events", "A", "boxing", "boxing", True),
        ("https://www.queensberry.co.uk/events", "A", "boxing", "boxing", True),
        ("https://www.nolimitboxing.com/events", "A", "boxing", "boxing", True),
        ("https://boxrec.com/en/event/912345", "B", "boxing", "boxing", True),
        ("https://www.fightmatrix.com/fighter-profile/1234", "B", "mma", "mma", True),
        ("https://www.tapology.com/fightcenter/events/12345", "C", "mma", "mma", True),
        ("https://www.sherdog.com/events/ufc-300-12345", "C", "mma", "mma", True),
        ("https://www.combatpress.com/event-calendar", "C", "kickboxing", "kickboxing", True),
        ("https://www.muaythairecords.com/events/one-samurai-1", "B", "muay_thai", "muay_thai", True),
        ("https://www.flashscore.com/mma/ufc-300", "D", "multi_sport_alert", "multi_sport_alert", False),
        ("https://www.venum.com/news/combat-sports", "D", "multi_sport_alert", "multi_sport_alert", False),
    ],
)
def test_classify_source_url_returns_expected_registry_record(url, expected_tier, expected_sport, expected_modality, approved):
    classification = classify_source_url(url)
    assert classification is not None
    assert classification["tier"] == expected_tier
    assert classification["sport"] == expected_sport
    assert classification["modality"] == expected_modality
    assert is_approved_event_card_source(url) is approved


def test_ufc_official_event_url_is_tier_a_mma():
    classification = classify_source_url("https://www.ufc.com/event/ufc-300")
    assert classification["tier"] == "A"
    assert classification["sport"] == "mma"
    assert classification["official_source"] is True
    assert classification["allowed_for_event_card_discovery"] is True
    assert is_approved_event_card_source("https://www.ufc.com/event/ufc-300", sport="mma") is True


def test_one_championship_official_url_is_tier_a_multisport_alert_and_sport_compatible():
    classification = classify_source_url("https://www.onefc.com/events/one-samurai-1")
    assert classification["tier"] == "A"
    assert classification["sport"] == "multi_sport_alert"
    assert classification["official_source"] is True
    assert is_approved_event_card_source("https://www.onefc.com/events/one-samurai-1", sport="mma") is True


def test_glory_url_classifies_as_tier_a_kickboxing():
    classification = classify_source_url("https://www.glorykickboxing.com/events/glory-100")
    assert classification["tier"] == "A"
    assert classification["sport"] == "kickboxing"
    assert classification["source_name"] == "GLORY official event pages"


def test_boxing_promoter_urls_classify_as_tier_a_boxing():
    for url in [
        "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "https://www.queensberry.co.uk/events",
        "https://www.toprank.com/all-events",
        "https://www.nolimitboxing.com/events",
    ]:
        classification = classify_source_url(url)
        assert classification["tier"] == "A"
        assert classification["sport"] == "boxing"
        assert classification["official_source"] is True


def test_structured_records_and_ranking_sources_classify_as_tier_b():
    boxrec = classify_source_url("https://boxrec.com/en/event/912345")
    fight_matrix = classify_source_url("https://www.fightmatrix.com/fighter-profile/1234")
    muay_thai_records = classify_source_url("https://www.muaythairecords.com/events/one-samurai-1")

    assert boxrec["tier"] == "B"
    assert boxrec["sport"] == "boxing"
    assert fight_matrix["tier"] == "B"
    assert fight_matrix["sport"] == "mma"
    assert muay_thai_records["tier"] == "B"
    assert muay_thai_records["sport"] == "muay_thai"
    assert requires_secondary_confirmation("https://www.muaythairecords.com/events/one-samurai-1") is True


def test_calendar_sources_require_secondary_confirmation():
    tapology = classify_source_url("https://www.tapology.com/fightcenter/events/12345")
    sherdog = classify_source_url("https://www.sherdog.com/events/ufc-300-12345")
    combat_press = classify_source_url("https://www.combatpress.com/event-calendar")

    assert tapology["tier"] == "C"
    assert sherdog["tier"] == "C"
    assert combat_press["tier"] == "C"
    assert requires_secondary_confirmation("https://www.tapology.com/fightcenter/events/12345") is True
    assert requires_secondary_confirmation("https://www.sherdog.com/events/ufc-300-12345") is True
    assert requires_secondary_confirmation("https://www.combatpress.com/event-calendar") is True


def test_flashscore_is_alert_only_and_not_queue_save_sufficient():
    classification = classify_source_url("https://www.flashscore.com/mma/ufc-300")
    governance = get_source_governance("https://www.flashscore.com/mma/ufc-300")

    assert classification["tier"] == "D"
    assert classification["sport"] == "multi_sport_alert"
    assert classification["allowed_for_event_card_discovery"] is False
    assert is_approved_event_card_source("https://www.flashscore.com/mma/ufc-300") is False
    assert governance["alert_only"] is True
    assert governance["queue_save_eligible"] is False
    assert governance["rejected"] is True


def test_unknown_and_missing_urls_are_rejected():
    assert classify_source_url("https://example.com/unapproved-source") is None
    assert classify_source_url("") is None
    assert classify_source_url(None) is None
    assert is_approved_event_card_source("https://example.com/unapproved-source") is False
    assert requires_secondary_confirmation(None) is True


def test_source_governance_blocks_tier_d_and_missing_urls():
    missing = get_source_governance(None)
    tier_d = get_source_governance("https://www.flashscore.com/mma/ufc-300")

    assert missing["denial_reason"] == "missing_url"
    assert missing["queue_save_eligible"] is False
    assert tier_d["denial_reason"] == "alert_only_source"
    assert tier_d["queue_save_eligible"] is False


def test_registry_has_no_mutation_flags_or_delivery_controls():
    registry = get_approved_combat_sport_sources()
    prohibited_keys = {
        "queue_write",
        "auto_save",
        "delivery_enabled",
        "learning_enabled",
        "calibration_enabled",
        "pdf_generate",
    }
    for entry in registry:
        assert not prohibited_keys.intersection(entry.keys())

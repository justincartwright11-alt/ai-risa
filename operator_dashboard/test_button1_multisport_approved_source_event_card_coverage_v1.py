"""Coverage tests for Button 1 multisport approved-source event-card governance (v1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.approved_combat_sport_source_registry import (
    classify_source_url,
    get_source_governance,
    is_approved_event_card_source,
)


def test_registry_audit_ufc_entries_are_mma_not_boxing():
    for url in [
        "https://www.ufc.com/event/ufc-300",
        "https://www.ufcstats.com/event-details/8de7af5c4f6f9d03",
    ]:
        classification = classify_source_url(url)
        assert classification is not None
        assert classification["sport"] == "mma"
        assert classification["modality"] == "mma"
        assert classification["sport"] != "boxing"


def test_event_card_coverage_has_tier_a_for_boxing_mma_kickboxing():
    tier_a_urls_by_sport = {
        "mma": ["https://www.ufc.com/event/ufc-300"],
        "boxing": ["https://www.matchroomboxing.com/events/joshua-vs-dubois"],
        "kickboxing": ["https://www.glorykickboxing.com/events/glory-100"],
    }

    for sport, urls in tier_a_urls_by_sport.items():
        assert any(is_approved_event_card_source(url, sport=sport) for url in urls)


def test_multi_sport_alert_tier_a_source_is_sport_compatible_for_coverage():
    url = "https://www.onefc.com/events/one-samurai-1"

    assert is_approved_event_card_source(url, sport="mma") is True
    assert is_approved_event_card_source(url, sport="kickboxing") is True
    assert is_approved_event_card_source(url, sport="muay_thai") is True


def test_tier_c_discovery_sources_are_coverage_approved_but_not_queue_save_eligible():
    url = "https://www.tapology.com/fightcenter/events/12345"

    assert is_approved_event_card_source(url, sport="mma") is True

    governance = get_source_governance(url)
    assert governance["tier"] == "C"
    assert governance["approved_for_event_card_discovery"] is True
    assert governance["requires_secondary_confirmation"] is True
    assert governance["queue_save_eligible"] is False


def test_tier_d_alert_only_source_is_not_event_card_coverage_approved():
    url = "https://www.flashscore.com/mma/ufc-300"

    assert is_approved_event_card_source(url, sport="mma") is False

    governance = get_source_governance(url)
    assert governance["tier"] == "D"
    assert governance["alert_only"] is True
    assert governance["queue_save_eligible"] is False

"""Preview-only multisport event-card fixtures for Button 1 (v1).

This module defines one governed URL-backed fixture per sport and provides a
safe preparation helper for Button 1 candidate rows. It performs no writes.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List

from operator_dashboard.approved_combat_sport_source_registry import (
    classify_source_url,
    get_source_governance,
)


BUTTON1_MULTISPORT_EVENT_CARD_FIXTURES_V1: List[Dict[str, Any]] = [
    {
        "fixture_id": "boxing_matchroom_fixture_v1",
        "sport": "boxing",
        "event_name": "Joshua vs Dubois",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "expected_tier": "A",
    },
    {
        "fixture_id": "mma_ufc_fixture_v1",
        "sport": "mma",
        "event_name": "UFC 300",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "expected_tier": "A",
    },
    {
        "fixture_id": "kickboxing_glory_fixture_v1",
        "sport": "kickboxing",
        "event_name": "GLORY 100",
        "source_url": "https://www.glorykickboxing.com/events/glory-100",
        "expected_tier": "A",
    },
    {
        "fixture_id": "muay_thai_records_fixture_v1",
        "sport": "muay_thai",
        "event_name": "ONE Samurai 1",
        "source_url": "https://www.muaythairecords.com/events/one-samurai-1",
        "expected_tier": "B",
    },
]


def get_button1_multisport_event_card_fixtures_v1() -> List[Dict[str, Any]]:
    """Return immutable-copy fixture rows for deterministic tests/previews."""

    return [copy.deepcopy(row) for row in BUTTON1_MULTISPORT_EVENT_CARD_FIXTURES_V1]


def prepare_event_card_fixture_for_button1_v1(fixture_row: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a preview-safe Button 1 candidate row from a governed fixture."""

    fixture = dict(fixture_row) if isinstance(fixture_row, dict) else {}
    source_url = fixture.get("source_url")
    sport = fixture.get("sport")

    classification = classify_source_url(source_url)
    governance = get_source_governance(source_url)

    if not classification or classification.get("sport") != sport:
        return {
            "candidate_id": fixture.get("fixture_id") or "invalid_fixture",
            "fixture_id": fixture.get("fixture_id"),
            "fight_name": fixture.get("event_name") or "Unknown Event",
            "sport": sport,
            "source_url": source_url,
            "source_backed": False,
            "preview_only": True,
            "approval_required": True,
            "ready_state": "not_ready",
            "queue_save_eligible": False,
            "unsafe_queue_save_blocked": True,
            "provenance": {"source_url": source_url},
            "denial_reason": "fixture_not_governed_for_sport",
        }

    queue_save_eligible = bool(governance.get("queue_save_eligible"))
    ready_state = "ready_to_save" if queue_save_eligible else "needs_review"

    return {
        "candidate_id": fixture.get("fixture_id"),
        "fixture_id": fixture.get("fixture_id"),
        "fight_name": fixture.get("event_name"),
        "sport": sport,
        "tier": classification.get("tier"),
        "source_url": source_url,
        "source_backed": True,
        "preview_only": True,
        "approval_required": True,
        "ready_state": ready_state,
        "queue_save_eligible": queue_save_eligible,
        "unsafe_queue_save_blocked": not queue_save_eligible,
        "provenance": {
            "source_url": source_url,
            "source_name": classification.get("source_name"),
            "source_id": classification.get("source_id"),
        },
        "requires_secondary_confirmation": bool(governance.get("requires_secondary_confirmation")),
        "official_source": bool(classification.get("official_source")),
    }


def build_button1_runtime_payload_from_fixtures_v1() -> Dict[str, Any]:
    """Build a deterministic runtime payload from all four governed fixtures."""

    fixtures = get_button1_multisport_event_card_fixtures_v1()
    prepared_rows = [prepare_event_card_fixture_for_button1_v1(row) for row in fixtures]
    sport_order = [row.get("sport") for row in prepared_rows]

    return {
        "candidate_rows": prepared_rows,
        "discovered_count": len(prepared_rows),
        "extracted_count": len(prepared_rows),
        "ready_for_report_count": len(prepared_rows),
        "sports_visible": sport_order,
        "preview_only": True,
        "approval_required": True,
    }


__all__ = [
    "BUTTON1_MULTISPORT_EVENT_CARD_FIXTURES_V1",
    "get_button1_multisport_event_card_fixtures_v1",
    "prepare_event_card_fixture_for_button1_v1",
    "build_button1_runtime_payload_from_fixtures_v1",
]

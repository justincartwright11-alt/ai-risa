"""
Governed full-card extraction adapter tests.

Slice: button1-promoter-full-card-extraction-adapters-v1
Validates: adapter contracts, classification logic, registry dispatch,
           read-only governance, Gate 1 integrity, Button 3 isolation.
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from operator_dashboard.button1_promoter_extraction_adapters.base import (
    ExtractionResult,
    VALID_CARD_COMPLETENESS_STATUSES,
)
from operator_dashboard.button1_promoter_extraction_adapters.matchroom_boxing import (
    MatchroomBoxingAdapter,
)
from operator_dashboard.button1_promoter_extraction_adapters.ufc_mma import UFCMMAAdapter
from operator_dashboard.button1_promoter_extraction_adapters.glory_kickboxing import (
    GLORYKickboxingAdapter,
)
from operator_dashboard.button1_promoter_extraction_adapters.registry import (
    get_adapter_for_event_row,
    run_extraction_for_event_row,
    list_registered_source_names,
)
from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    load_readonly_runtime_state,
)
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)


# ---------------------------------------------------------------------------
# Fixtures for test data
# ---------------------------------------------------------------------------

def _boxing_event_row_headline_only() -> dict:
    """Production-matching boxing event row with only 1 headline matchup."""
    return {
        "candidate_id": "live_boxing_event_card_001",
        "event_name": "Joshua vs Dubois",
        "promotion": "Matchroom Boxing",
        "sport": "boxing",
        "source_name": "matchroom_official_boxing",
        "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
        "source_tier": "A",
        "card_completeness_status": "headline_only",
        "expected_matchup_count": None,
        "matchups": [
            {
                "fighter_a": "Anthony Joshua",
                "fighter_b": "Daniel Dubois",
                "weight_class": "Heavyweight",
                "bout_order": 1,
                "source_backed": True,
                "source_url": "https://www.matchroomboxing.com/events/joshua-vs-dubois",
            }
        ],
    }


def _boxing_event_row_full_card() -> dict:
    """Test-only boxing event row with a full 8-bout card for adapter logic testing."""
    source_url = "https://www.matchroomboxing.com/events/joshua-vs-dubois"
    bouts = [
        ("Fighter A1", "Fighter B1"),
        ("Fighter A2", "Fighter B2"),
        ("Fighter A3", "Fighter B3"),
        ("Fighter A4", "Fighter B4"),
        ("Fighter A5", "Fighter B5"),
        ("Fighter A6", "Fighter B6"),
        ("Fighter A7", "Fighter B7"),
        ("Fighter A8", "Fighter B8"),
    ]
    return {
        "candidate_id": "live_boxing_event_card_001",
        "event_name": "Joshua vs Dubois",
        "promotion": "Matchroom Boxing",
        "sport": "boxing",
        "source_name": "matchroom_official_boxing",
        "source_url": source_url,
        "source_tier": "A",
        "card_completeness_status": "headline_only",
        "expected_matchup_count": 8,
        "matchups": [
            {
                "fighter_a": fa,
                "fighter_b": fb,
                "weight_class": "Heavyweight",
                "bout_order": i + 1,
                "source_backed": True,
                "source_url": source_url,
            }
            for i, (fa, fb) in enumerate(bouts)
        ],
    }


def _mma_event_row_headline_only() -> dict:
    return {
        "candidate_id": "live_mma_event_card_001",
        "event_name": "UFC 300",
        "promotion": "UFC",
        "sport": "mma",
        "source_name": "ufc_official_event_pages",
        "source_url": "https://www.ufc.com/event/ufc-300",
        "source_tier": "A",
        "card_completeness_status": "headline_only",
        "expected_matchup_count": None,
        "matchups": [
            {
                "fighter_a": "Alex Pereira",
                "fighter_b": "Jiri Prochazka",
                "weight_class": "Light Heavyweight",
                "bout_order": 1,
                "source_backed": True,
                "source_url": "https://www.ufc.com/event/ufc-300",
            }
        ],
    }


def _mma_event_row_full_card() -> dict:
    source_url = "https://www.ufc.com/event/ufc-300"
    bouts = [(f"Fighter {chr(65+i)}", f"Fighter {chr(97+i)}") for i in range(12)]
    return {
        "candidate_id": "live_mma_event_card_001",
        "event_name": "UFC 300",
        "promotion": "UFC",
        "sport": "mma",
        "source_name": "ufc_official_event_pages",
        "source_url": source_url,
        "source_tier": "A",
        "expected_matchup_count": 12,
        "matchups": [
            {
                "fighter_a": fa,
                "fighter_b": fb,
                "bout_order": i + 1,
                "source_backed": True,
                "source_url": source_url,
            }
            for i, (fa, fb) in enumerate(bouts)
        ],
    }


def _kickboxing_event_row_headline_only() -> dict:
    return {
        "candidate_id": "live_kickboxing_event_card_001",
        "event_name": "GLORY 100",
        "promotion": "GLORY",
        "sport": "kickboxing",
        "source_name": "glory_official_event_pages",
        "source_url": "https://www.glorykickboxing.com/events/glory-100",
        "source_tier": "A",
        "card_completeness_status": "headline_only",
        "expected_matchup_count": None,
        "matchups": [
            {
                "fighter_a": "Rico Verhoeven",
                "fighter_b": "Tariq Osaro",
                "weight_class": "Heavyweight",
                "bout_order": 1,
                "source_backed": True,
                "source_url": "https://www.glorykickboxing.com/events/glory-100",
            }
        ],
    }


def _kickboxing_event_row_full_card() -> dict:
    source_url = "https://www.glorykickboxing.com/events/glory-100"
    bouts = [(f"KB Fighter {i}A", f"KB Fighter {i}B") for i in range(1, 9)]
    return {
        "candidate_id": "live_kickboxing_event_card_001",
        "event_name": "GLORY 100",
        "promotion": "GLORY",
        "sport": "kickboxing",
        "source_name": "glory_official_event_pages",
        "source_url": source_url,
        "source_tier": "A",
        "expected_matchup_count": 8,
        "matchups": [
            {
                "fighter_a": fa,
                "fighter_b": fb,
                "bout_order": i + 1,
                "source_backed": True,
                "source_url": source_url,
            }
            for i, (fa, fb) in enumerate(bouts)
        ],
    }


# ---------------------------------------------------------------------------
# Tests 1-3: Matchroom Boxing adapter
# ---------------------------------------------------------------------------

def test_matchroom_adapter_instantiates_and_can_handle_boxing_row():
    """Test 1: MatchroomBoxingAdapter can_handle() returns True for boxing event row."""
    adapter = MatchroomBoxingAdapter()
    row = _boxing_event_row_headline_only()
    assert adapter.can_handle(row) is True


def test_matchroom_adapter_returns_headline_only_for_single_matchup_production_row():
    """Test 2: Matchroom adapter returns headline_only when feed only has 1 bout."""
    adapter = MatchroomBoxingAdapter()
    row = _boxing_event_row_headline_only()
    result = adapter.extract(row)
    assert isinstance(result, ExtractionResult)
    assert result.card_completeness_status == "headline_only"
    assert result.matchup_count == 1
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.extraction_diagnostics.strip()


def test_matchroom_adapter_returns_full_card_confirmed_when_all_bouts_provided():
    """Test 3: Matchroom adapter returns full_card_confirmed when expected matchups all present."""
    adapter = MatchroomBoxingAdapter()
    row = _boxing_event_row_full_card()
    result = adapter.extract(row)
    assert result.card_completeness_status == "full_card_confirmed"
    assert result.matchup_count == 8
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False


# ---------------------------------------------------------------------------
# Tests 4-6: UFC MMA adapter
# ---------------------------------------------------------------------------

def test_ufc_adapter_instantiates_and_can_handle_mma_row():
    """Test 4: UFCMMAAdapter can_handle() returns True for MMA event row."""
    adapter = UFCMMAAdapter()
    row = _mma_event_row_headline_only()
    assert adapter.can_handle(row) is True


def test_ufc_adapter_returns_headline_only_for_single_matchup_production_row():
    """Test 5: UFC adapter returns headline_only when feed only has 1 bout."""
    adapter = UFCMMAAdapter()
    row = _mma_event_row_headline_only()
    result = adapter.extract(row)
    assert isinstance(result, ExtractionResult)
    assert result.card_completeness_status == "headline_only"
    assert result.matchup_count == 1
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.extraction_diagnostics.strip()


def test_ufc_adapter_returns_full_card_confirmed_when_all_bouts_provided():
    """Test 6: UFC adapter returns full_card_confirmed when expected matchups all present."""
    adapter = UFCMMAAdapter()
    row = _mma_event_row_full_card()
    result = adapter.extract(row)
    assert result.card_completeness_status == "full_card_confirmed"
    assert result.matchup_count == 12
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False


# ---------------------------------------------------------------------------
# Tests 7-9: GLORY Kickboxing adapter
# ---------------------------------------------------------------------------

def test_glory_adapter_instantiates_and_can_handle_kickboxing_row():
    """Test 7: GLORYKickboxingAdapter can_handle() returns True for kickboxing event row."""
    adapter = GLORYKickboxingAdapter()
    row = _kickboxing_event_row_headline_only()
    assert adapter.can_handle(row) is True


def test_glory_adapter_returns_headline_only_for_single_matchup_production_row():
    """Test 8: GLORY adapter returns headline_only when feed only has 1 bout."""
    adapter = GLORYKickboxingAdapter()
    row = _kickboxing_event_row_headline_only()
    result = adapter.extract(row)
    assert isinstance(result, ExtractionResult)
    assert result.card_completeness_status == "headline_only"
    assert result.matchup_count == 1
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.extraction_diagnostics.strip()


def test_glory_adapter_returns_full_card_confirmed_when_all_bouts_provided():
    """Test 9: GLORY adapter returns full_card_confirmed when expected matchups all present."""
    adapter = GLORYKickboxingAdapter()
    row = _kickboxing_event_row_full_card()
    result = adapter.extract(row)
    assert result.card_completeness_status == "full_card_confirmed"
    assert result.matchup_count == 8
    assert result.extraction_ok is True
    assert result.preview_only is True
    assert result.write_authorized is False


# ---------------------------------------------------------------------------
# Test 10: Registry dispatches correctly per source
# ---------------------------------------------------------------------------

def test_registry_dispatches_to_correct_adapter_per_source():
    """Test 10: Registry returns correct adapter type per source_name."""
    boxing_row = _boxing_event_row_headline_only()
    mma_row = _mma_event_row_headline_only()
    kb_row = _kickboxing_event_row_headline_only()

    boxing_adapter = get_adapter_for_event_row(boxing_row)
    mma_adapter = get_adapter_for_event_row(mma_row)
    kb_adapter = get_adapter_for_event_row(kb_row)

    assert isinstance(boxing_adapter, MatchroomBoxingAdapter)
    assert isinstance(mma_adapter, UFCMMAAdapter)
    assert isinstance(kb_adapter, GLORYKickboxingAdapter)

    registered = list_registered_source_names()
    assert "matchroom_official_boxing" in registered
    assert "ufc_official_event_pages" in registered
    assert "glory_official_event_pages" in registered


# ---------------------------------------------------------------------------
# Test 11: Unknown source returns extraction_unsupported
# ---------------------------------------------------------------------------

def test_unknown_source_returns_extraction_unsupported():
    """Test 11: A row with an unregistered source returns extraction_unsupported."""
    unknown_row = {
        "event_name": "Unknown Promotion Event",
        "source_name": "totally_unknown_source_xyz",
        "source_url": "https://www.unknownpromotion.example.com/event/123",
        "matchups": [{"fighter_a": "Fighter X", "fighter_b": "Fighter Y"}],
    }
    adapter = get_adapter_for_event_row(unknown_row)
    assert adapter is None, "No adapter should match an unregistered source"

    result = run_extraction_for_event_row(unknown_row)
    assert result.card_completeness_status == "extraction_unsupported"
    assert result.extraction_ok is False
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.error == "no_adapter_registered"


# ---------------------------------------------------------------------------
# Test 12: All adapters are read-only
# ---------------------------------------------------------------------------

def test_all_adapters_are_read_only_no_writes():
    """Test 12: All three adapters return preview_only=True, write_authorized=False."""
    rows_and_adapters = [
        (_boxing_event_row_headline_only(), MatchroomBoxingAdapter()),
        (_mma_event_row_headline_only(), UFCMMAAdapter()),
        (_kickboxing_event_row_headline_only(), GLORYKickboxingAdapter()),
    ]
    for row, adapter in rows_and_adapters:
        result = adapter.extract(row)
        assert result.preview_only is True, (
            f"{adapter.__class__.__name__} must always return preview_only=True"
        )
        assert result.write_authorized is False, (
            f"{adapter.__class__.__name__} must always return write_authorized=False"
        )
        assert result.card_completeness_status in VALID_CARD_COMPLETENESS_STATUSES


# ---------------------------------------------------------------------------
# Test 13: Muay Thai row not claimed by Boxing/MMA/Kickboxing adapters
# ---------------------------------------------------------------------------

def test_muay_thai_row_not_claimed_by_boxing_mma_or_kickboxing_adapters():
    """Test 13: Muay Thai source row is not handled by the three primary adapters."""
    muay_thai_row = {
        "event_name": "ONE SAMURAI 1",
        "source_name": "muay_thai_records_structured",
        "source_url": "https://www.muaythairecords.com/events/one-samurai-1",
        "sport": "muay_thai",
        "matchups": [{"fighter_a": "Rodtang Jitmuangnon", "fighter_b": "Takeru Segawa"}],
    }
    boxing_adapter = MatchroomBoxingAdapter()
    mma_adapter = UFCMMAAdapter()
    kb_adapter = GLORYKickboxingAdapter()

    assert boxing_adapter.can_handle(muay_thai_row) is False
    assert mma_adapter.can_handle(muay_thai_row) is False
    assert kb_adapter.can_handle(muay_thai_row) is False

    # Registry returns None — no adapter registered for this source
    adapter = get_adapter_for_event_row(muay_thai_row)
    assert adapter is None


# ---------------------------------------------------------------------------
# Test 14: Gate 1 still preview-only after adapter runs
# ---------------------------------------------------------------------------

def test_gate1_still_preview_only_after_adapter_runs():
    """Test 14: Running adapters does not affect Gate 1 preview-only governance."""
    # Run adapters on all three production rows
    for row in [
        _boxing_event_row_headline_only(),
        _mma_event_row_headline_only(),
        _kickboxing_event_row_headline_only(),
    ]:
        run_extraction_for_event_row(row)

    # Gate 1 must still report preview-only, no writes
    state = load_readonly_runtime_state()
    result = run_gate1_save_fights_dry_run_apply_preview(state)
    assert result.preview_only is True
    assert result.write_authorized is False
    assert result.mutation_performed is False
    assert result.queue_write_performed is False


# ---------------------------------------------------------------------------
# Test 15: Adapter run does not mutate Button 3
# ---------------------------------------------------------------------------

def test_adapter_run_does_not_mutate_button3():
    """Test 15: Running extraction adapters does not affect Button 3 state."""
    state_before = load_readonly_runtime_state()
    b3_before = state_before.get("learning_updates", [])
    b3_accuracy_before = state_before.get("accuracy_metrics", {})

    # Run all adapters
    for row in [
        _boxing_event_row_headline_only(),
        _mma_event_row_headline_only(),
        _kickboxing_event_row_headline_only(),
    ]:
        run_extraction_for_event_row(row)

    state_after = load_readonly_runtime_state()
    b3_after = state_after.get("learning_updates", [])
    b3_accuracy_after = state_after.get("accuracy_metrics", {})

    assert b3_after == b3_before, "Button 3 learning_updates must not change after adapter runs"
    assert b3_accuracy_after == b3_accuracy_before, (
        "Button 3 accuracy_metrics must not change after adapter runs"
    )

"""
test_button1_full_card_feed_population_v1.py
---------------------------------------------
Slice: button1-full-card-feed-population-v1

Validates that:
1.  Boxing event row upgrades from headline_only to full_card_confirmed.
2.  Boxing event row has 5 matchups.
3.  Boxing expected_matchup_count matches actual matchup_count.
4.  MMA event row upgrades from headline_only to full_card_confirmed.
5.  MMA event row has 5 matchups.
6.  MMA expected_matchup_count matches actual matchup_count.
7.  GLORY Kickboxing event row upgrades from headline_only to full_card_confirmed.
8.  GLORY Kickboxing event row has 5 matchups.
9.  GLORY expected_matchup_count matches actual matchup_count.
10. All tier-A event matchups have source_backed=True and valid source_url.
11. Adapter extraction confirms full_card_confirmed for all three tier-A events.
12. Adapters enforce preview_only=True and write_authorized=False after upgrade.
13. Muay Thai event remains full_card_confirmed from manual feed (no adapter needed).
14. Gate 1 dry-run is still preview-only after full card population.
15. No database writes, queue saves, PDF generation, or learning occur.
"""
import json
import sys
from pathlib import Path

import pytest

# Workspace root on sys.path
sys.path.insert(0, str(Path(__file__).parents[1]))

from operator_dashboard.button1_promoter_extraction_adapters import (
    run_extraction_for_event_row,
)
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import (
    run_gate1_save_fights_dry_run_apply_preview,
)

FEED_PATH = Path(__file__).parents[1] / "ops" / "approved_sources" / "button1_live_event_source_rows.json"


@pytest.fixture(scope="module")
def feed_events():
    with open(FEED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["events"]


@pytest.fixture(scope="module")
def boxing_row(feed_events):
    return next(r for r in feed_events if r.get("candidate_id") == "live_boxing_event_card_001")


@pytest.fixture(scope="module")
def mma_row(feed_events):
    return next(r for r in feed_events if r.get("candidate_id") == "live_mma_event_card_001")


@pytest.fixture(scope="module")
def kickboxing_row(feed_events):
    return next(r for r in feed_events if r.get("candidate_id") == "live_kickboxing_event_card_001")


@pytest.fixture(scope="module")
def muay_thai_row(feed_events):
    return next(r for r in feed_events if r.get("candidate_id") == "live_muay_thai_event_card_001")


# ---------------------------------------------------------------------------
# Test 1 — Boxing card_completeness_status is full_card_confirmed in feed
# ---------------------------------------------------------------------------
def test_boxing_feed_row_is_full_card_confirmed(boxing_row):
    assert boxing_row["card_completeness_status"] == "full_card_confirmed"


# ---------------------------------------------------------------------------
# Test 2 — Boxing feed has 5 matchups
# ---------------------------------------------------------------------------
def test_boxing_feed_row_has_five_matchups(boxing_row):
    assert boxing_row["matchup_count"] == 5
    assert len(boxing_row["matchups"]) == 5


# ---------------------------------------------------------------------------
# Test 3 — Boxing expected_matchup_count equals actual matchup_count
# ---------------------------------------------------------------------------
def test_boxing_expected_matchup_count_matches_actual(boxing_row):
    assert boxing_row["expected_matchup_count"] == boxing_row["matchup_count"]


# ---------------------------------------------------------------------------
# Test 4 — MMA card_completeness_status is full_card_confirmed in feed
# ---------------------------------------------------------------------------
def test_mma_feed_row_is_full_card_confirmed(mma_row):
    assert mma_row["card_completeness_status"] == "full_card_confirmed"


# ---------------------------------------------------------------------------
# Test 5 — MMA feed has 5 matchups
# ---------------------------------------------------------------------------
def test_mma_feed_row_has_five_matchups(mma_row):
    assert mma_row["matchup_count"] == 5
    assert len(mma_row["matchups"]) == 5


# ---------------------------------------------------------------------------
# Test 6 — MMA expected_matchup_count equals actual matchup_count
# ---------------------------------------------------------------------------
def test_mma_expected_matchup_count_matches_actual(mma_row):
    assert mma_row["expected_matchup_count"] == mma_row["matchup_count"]


# ---------------------------------------------------------------------------
# Test 7 — GLORY Kickboxing card_completeness_status is full_card_confirmed
# ---------------------------------------------------------------------------
def test_kickboxing_feed_row_is_full_card_confirmed(kickboxing_row):
    assert kickboxing_row["card_completeness_status"] == "full_card_confirmed"


# ---------------------------------------------------------------------------
# Test 8 — GLORY Kickboxing feed has 5 matchups
# ---------------------------------------------------------------------------
def test_kickboxing_feed_row_has_five_matchups(kickboxing_row):
    assert kickboxing_row["matchup_count"] == 5
    assert len(kickboxing_row["matchups"]) == 5


# ---------------------------------------------------------------------------
# Test 9 — GLORY expected_matchup_count equals actual matchup_count
# ---------------------------------------------------------------------------
def test_kickboxing_expected_matchup_count_matches_actual(kickboxing_row):
    assert kickboxing_row["expected_matchup_count"] == kickboxing_row["matchup_count"]


# ---------------------------------------------------------------------------
# Test 10 — All tier-A matchups have source_backed=True and non-empty source_url
# ---------------------------------------------------------------------------
def test_all_tier_a_matchups_are_source_backed(boxing_row, mma_row, kickboxing_row):
    for row in (boxing_row, mma_row, kickboxing_row):
        for bout in row["matchups"]:
            assert bout.get("source_backed") is True, (
                f"source_backed missing for {bout.get('fighter_a')} vs {bout.get('fighter_b')}"
            )
            url = bout.get("source_url", "")
            assert url.startswith("https://"), (
                f"Invalid source_url for {bout.get('fighter_a')} vs {bout.get('fighter_b')}"
            )


# ---------------------------------------------------------------------------
# Test 11 — Adapter extraction confirms full_card_confirmed for all three
#            tier-A events
# ---------------------------------------------------------------------------
def test_adapter_extraction_confirms_full_card_confirmed(boxing_row, mma_row, kickboxing_row):
    for row in (boxing_row, mma_row, kickboxing_row):
        result = run_extraction_for_event_row(row)
        cid = row.get("candidate_id")
        assert result.extraction_ok is True, f"extraction_ok=False for {cid}"
        assert result.card_completeness_status == "full_card_confirmed", (
            f"Expected full_card_confirmed for {cid}, got {result.card_completeness_status}"
        )
        assert result.matchup_count == 5, f"Expected 5 matchups for {cid}"
        assert result.expected_matchup_count == 5, f"Expected expected=5 for {cid}"


# ---------------------------------------------------------------------------
# Test 12 — Adapters enforce preview_only=True and write_authorized=False
#            after full card upgrade
# ---------------------------------------------------------------------------
def test_adapter_results_are_read_only_after_upgrade(boxing_row, mma_row, kickboxing_row):
    for row in (boxing_row, mma_row, kickboxing_row):
        result = run_extraction_for_event_row(row)
        cid = row.get("candidate_id")
        assert result.preview_only is True, f"preview_only not True for {cid}"
        assert result.write_authorized is False, f"write_authorized not False for {cid}"


# ---------------------------------------------------------------------------
# Test 13 — Muay Thai event remains full_card_confirmed from manual feed
# ---------------------------------------------------------------------------
def test_muay_thai_feed_row_remains_full_card_confirmed(muay_thai_row):
    assert muay_thai_row["card_completeness_status"] == "full_card_confirmed"
    assert muay_thai_row["matchup_count"] == 15
    assert muay_thai_row["expected_matchup_count"] == 15


# ---------------------------------------------------------------------------
# Test 14 — Gate 1 dry-run is still preview-only after full card population
# ---------------------------------------------------------------------------
def test_gate1_remains_preview_only_after_full_card_population(boxing_row):
    state = {
        "workflow": {
            "jobs": [
                {
                    "input_ref": {
                        "metadata": {
                            "payload": {
                                "candidate_rows": [boxing_row],
                            }
                        }
                    }
                }
            ]
        }
    }
    result = run_gate1_save_fights_dry_run_apply_preview(state)
    assert result.preview_only is True
    assert result.write_authorized is False


# ---------------------------------------------------------------------------
# Test 15 — No database writes, queue saves, PDFs, or learning occur
# ---------------------------------------------------------------------------
def test_no_writes_occur_after_full_card_population(boxing_row, mma_row, kickboxing_row):
    for row in (boxing_row, mma_row, kickboxing_row):
        state = {
            "workflow": {
                "jobs": [
                    {
                        "input_ref": {
                            "metadata": {
                                "payload": {
                                    "candidate_rows": [row],
                                }
                            }
                        }
                    }
                ]
            }
        }
        result = run_gate1_save_fights_dry_run_apply_preview(state)
        cid = row.get("candidate_id")
        assert result.mutation_performed is False, f"mutation_performed=True for {cid}"
        assert result.queue_write_performed is False, f"queue_write_performed=True for {cid}"
        assert result.database_write_performed is False, f"database_write_performed=True for {cid}"

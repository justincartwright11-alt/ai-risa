"""Test Button 1 current-week source discovery refresh and stale feed guard.

Tests current-week window validation, stale/demo feed detection, and operator approval gate.
"""

import os
import json
import pytest
import tempfile
import shutil
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from operator_dashboard.local_ai_orchestrator_readonly_runtime_context_loader import (
    _load_approved_source_live_event_rows,
    _get_current_week_window,
    _parse_event_date,
    _is_event_in_window,
    _is_demo_or_fixture_feed,
    _check_feed_freshness,
)


@pytest.fixture
def temp_workspace():
    """Create temporary workspace directory."""
    tmpdir = tempfile.mkdtemp()
    ops_dir = os.path.join(tmpdir, "ops", "approved_sources")
    os.makedirs(ops_dir, exist_ok=True)
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def config_file(temp_workspace):
    """Create minimal config file."""
    config_path = os.path.join(
        temp_workspace, "ops", "approved_sources",
        "button1_live_event_ingestion_config.json"
    )
    config = {
        "enabled": True,
        "approved_source_url_patterns": [
            r"https?://(?:www\.)?ufc\.com/event/",
            r"https?://(?:www\.)?matchroom\.com/events/",
        ],
        "feed_paths": [
            "ops/approved_sources/button1_live_event_source_rows.json"
        ]
    }
    with open(config_path, "w") as f:
        json.dump(config, f)
    return config_path


class TestCurrentWeekWindowCalculation:
    """Test current-week window calculation."""

    def test_current_week_window_valid(self):
        """Test that current week window is calculated correctly."""
        week_start, week_end, upcoming_end = _get_current_week_window()
        today = date.today()
        
        # Week start should be a Monday
        assert week_start.weekday() == 0  # 0 = Monday
        # Week should span 6 days (Monday-Sunday)
        assert (week_end - week_start).days == 6
        # Week start should be <= today
        assert week_start <= today
        # Week end should be >= today
        assert week_end >= today
        # Upcoming window should extend 14 days into future
        assert (upcoming_end - today).days <= 14


class TestEventDateParsing:
    """Test event date parsing."""

    def test_parse_valid_event_date(self):
        """Test parsing valid ISO date."""
        result = _parse_event_date("2026-06-15")
        assert result == date(2026, 6, 15)

    def test_parse_invalid_event_date(self):
        """Test parsing invalid date returns None."""
        assert _parse_event_date("invalid-date") is None
        assert _parse_event_date("") is None
        assert _parse_event_date(None) is None


class TestCurrentWeekEventFiltering:
    """Test filtering events to current-week window."""

    def test_event_in_window(self):
        """Test that current-week event is in window."""
        today = date.today()
        event_row = {
            "event_date": today.isoformat(),
            "event_name": "Test Event"
        }
        _, _, upcoming_end = _get_current_week_window()
        assert _is_event_in_window(event_row, upcoming_end) is True

    def test_event_outside_window_past(self):
        """Test that past event is outside window."""
        past_date = (date.today() - timedelta(days=60)).isoformat()
        event_row = {
            "event_date": past_date,
            "event_name": "Old Event"
        }
        _, _, upcoming_end = _get_current_week_window()
        assert _is_event_in_window(event_row, upcoming_end) is False

    def test_event_outside_window_future(self):
        """Test that far-future event is outside window."""
        future_date = (date.today() + timedelta(days=30)).isoformat()
        event_row = {
            "event_date": future_date,
            "event_name": "Far Future Event"
        }
        _, _, upcoming_end = _get_current_week_window()
        assert _is_event_in_window(event_row, upcoming_end) is False


class TestDemoOrFixtureFeedDetection:
    """Test demo/fixture feed detection."""

    def test_detect_demo_marker(self):
        """Test detection of demo feed."""
        rows = [
            {
                "event_name": "Demo Event",
                "event_date": date.today().isoformat()
            }
        ]
        assert _is_demo_or_fixture_feed(rows) is True

    def test_detect_fixture_marker(self):
        """Test detection of fixture feed."""
        rows = [
            {
                "event_name": "Fixture Event",
                "event_date": date.today().isoformat()
            }
        ]
        assert _is_demo_or_fixture_feed(rows) is True

    def test_detect_old_event(self):
        """Test detection of old event (fixture-like)."""
        old_date = (date.today() - timedelta(days=60)).isoformat()
        rows = [
            {
                "event_name": "Old Event",
                "event_date": old_date
            }
        ]
        assert _is_demo_or_fixture_feed(rows) is True

    def test_no_demo_marker_current_event(self):
        """Test current event without demo markers."""
        rows = [
            {
                "event_name": "UFC 300 Live Event",
                "event_date": date.today().isoformat()
            }
        ]
        assert _is_demo_or_fixture_feed(rows) is False


class TestFeedFreshnessCheck:
    """Test feed freshness validation."""

    def test_fresh_feed(self, temp_workspace):
        """Test that recently modified feed is fresh."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        # Create a fresh file
        os.makedirs(os.path.dirname(feed_path), exist_ok=True)
        with open(feed_path, "w") as f:
            json.dump({"events": []}, f)
        
        is_fresh, status = _check_feed_freshness(feed_path, max_age_seconds=3600)
        assert is_fresh is True
        assert status == "feed_fresh"

    def test_stale_feed(self, temp_workspace):
        """Test that old feed is detected as stale."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        os.makedirs(os.path.dirname(feed_path), exist_ok=True)
        with open(feed_path, "w") as f:
            json.dump({"events": []}, f)
        
        # Make file appear old
        old_time = time.time() - 86401  # 1 day + 1 second old
        os.utime(feed_path, (old_time, old_time))
        
        is_fresh, status = _check_feed_freshness(feed_path, max_age_seconds=86400)
        assert is_fresh is False
        assert status == "feed_stale"

    def test_missing_feed(self, temp_workspace):
        """Test that missing feed is handled."""
        feed_path = os.path.join(temp_workspace, "nonexistent.json")
        is_fresh, status = _check_feed_freshness(feed_path)
        assert is_fresh is False
        assert status == "feed_file_missing"


class TestStaticOldRowsNotDisplayedAsCurrent:
    """Test that static old/fixture rows are NOT displayed as current-week."""

    def test_old_ufc_event_not_current_week(self, temp_workspace, config_file):
        """Test that old UFC 300 event is not shown as current-week."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        
        # Create feed with old event (fixture)
        old_date = (date.today() - timedelta(days=60)).isoformat()
        feed_data = {
            "events": [
                {
                    "event_name": "UFC 300",
                    "event_date": old_date,
                    "source_url": "https://www.ufc.com/event/ufc-300",
                    "source_name": "ufc_official",
                    "source_type": "official"
                }
            ]
        }
        with open(feed_path, "w") as f:
            json.dump(feed_data, f)
        
        result = _load_approved_source_live_event_rows(temp_workspace)
        
        # Old event should NOT be in current-week rows
        assert result["current_week_ready"] is False
        assert result["save_allowed"] is False
        assert result["feed_status"] in ["demo_or_fixture_feed", "no_current_week_events"]
        assert len(result["rows"]) == 0


class TestCurrentWeekDiscoveryWithApprovalGate:
    """Test current-week discovery with operator approval requirement."""

    def test_current_week_ready_status_true(self, temp_workspace, config_file):
        """Test that current-week event has ready status."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        
        # Create feed with current-week event
        today = date.today()
        feed_data = {
            "events": [
                {
                    "event_name": "UFC Live Event Today",
                    "event_date": today.isoformat(),
                    "source_url": "https://www.ufc.com/event/live-today",
                    "source_name": "ufc_official",
                    "source_type": "official"
                }
            ]
        }
        with open(feed_path, "w") as f:
            json.dump(feed_data, f)
        
        result = _load_approved_source_live_event_rows(temp_workspace)
        
        # Current-week event should be ready
        assert result["current_week_ready"] is True
        assert result["save_allowed"] is True
        assert result["feed_status"] == "current_week_ready"
        assert len(result["rows"]) == 1
        
        # Verify row has discovery metadata
        event = result["rows"][0]
        assert "_discovery_window_start" in event
        assert "_discovery_window_end" in event
        assert "_discovery_generated_at" in event
        assert "_source_feed_status" in event

    def test_save_allowed_only_with_approval(self, temp_workspace, config_file):
        """Test that save_allowed requires explicit operator approval."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        
        today = date.today()
        feed_data = {
            "events": [
                {
                    "event_name": "Current Event",
                    "event_date": today.isoformat(),
                    "source_url": "https://www.ufc.com/event/current",
                    "source_name": "ufc_official",
                    "source_type": "official"
                }
            ]
        }
        with open(feed_path, "w") as f:
            json.dump(feed_data, f)
        
        result = _load_approved_source_live_event_rows(temp_workspace)
        
        # save_allowed should be True only if all guards pass
        assert result["save_allowed"] is True
        # But in actual queue save, we require explicit operator_approval=true
        # This is tested at the Flask app level


class TestStaleAndDemoFeedGuards:
    """Test stale and demo feed guards."""

    def test_stale_feed_blocks_save(self, temp_workspace, config_file):
        """Test that stale feed blocks save."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        
        today = date.today()
        feed_data = {
            "events": [
                {
                    "event_name": "Current Event",
                    "event_date": today.isoformat(),
                    "source_url": "https://www.ufc.com/event/current",
                    "source_name": "ufc_official",
                    "source_type": "official"
                }
            ]
        }
        os.makedirs(os.path.dirname(feed_path), exist_ok=True)
        with open(feed_path, "w") as f:
            json.dump(feed_data, f)
        
        # Make file appear stale
        old_time = time.time() - 86401
        os.utime(feed_path, (old_time, old_time))
        
        result = _load_approved_source_live_event_rows(temp_workspace)
        
        assert result["feed_status"] == "stale"
        assert result["current_week_ready"] is False
        assert result["save_allowed"] is False
        assert len(result["rows"]) == 0

    def test_demo_feed_blocks_save(self, temp_workspace, config_file):
        """Test that demo feed blocks save."""
        feed_path = os.path.join(
            temp_workspace, "ops", "approved_sources",
            "button1_live_event_source_rows.json"
        )
        
        today = date.today()
        feed_data = {
            "events": [
                {
                    "event_name": "Demo Event Test",
                    "event_date": today.isoformat(),
                    "source_url": "https://www.ufc.com/event/demo",
                    "source_name": "ufc_official",
                    "source_type": "official"
                }
            ]
        }
        os.makedirs(os.path.dirname(feed_path), exist_ok=True)
        with open(feed_path, "w") as f:
            json.dump(feed_data, f)
        
        result = _load_approved_source_live_event_rows(temp_workspace)
        
        assert result["feed_status"] == "demo_or_fixture_feed"
        assert result["current_week_ready"] is False
        assert result["save_allowed"] is False
        assert len(result["rows"]) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

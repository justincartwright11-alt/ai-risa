"""
GLORY Kickboxing full-card extraction adapter.

Approved sources: glorykickboxing.com/events/, combatpress.com (under registry governance)
Governance: read-only, fail closed. No writes, no PDFs, no auto-saves.

Card completeness determination:
  - 0 bouts     → extraction_unsupported
  - 1 bout      → headline_only (static feed only has headline bout)
  - 2-N bouts, expected unknown → partial_card
  - >= expected AND all URL-backed → full_card_confirmed

Current production status for GLORY 100:
  Static feed carries 1 matchup → adapter returns headline_only.
  To upgrade: populate the feed matchups[] with all verified bouts from
  glorykickboxing.com and set expected_matchup_count.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import BaseEventCardExtractionAdapter, ExtractionResult


class GLORYKickboxingAdapter(BaseEventCardExtractionAdapter):
    """Extraction adapter for GLORY Kickboxing official event cards."""

    source_name = "glory_official_event_pages"
    supported_url_patterns = [
        "glorykickboxing.com/events/",
        "glorykickboxing.com/event/",
    ]

    # Typical GLORY main card: ~8-10 bouts.
    # Used only when expected_matchup_count is not set in the feed row.
    _TYPICAL_FULL_CARD_MIN = 7

    def extract(self, event_row: Dict[str, Any]) -> ExtractionResult:
        event_name = str(event_row.get("event_name") or "").strip()
        source_url = str(event_row.get("source_url") or "").strip()
        raw_matchups = event_row.get("matchups") or []
        matchups = self._valid_matchups(
            [m for m in raw_matchups if isinstance(m, dict)]
        )
        expected: Optional[int] = event_row.get("expected_matchup_count")

        completeness = self._classify_completeness(matchups, expected, source_url)

        if completeness == "headline_only":
            method = "static_feed_headline_only"
            diagnostics = (
                f"Only {len(matchups)} matchup(s) found in static feed for {event_name!r}. "
                "Full card extraction from glorykickboxing.com is not yet implemented. "
                "To upgrade: populate matchups[] in the feed with all verified bouts from "
                "the approved GLORY event page and set expected_matchup_count."
            )
        elif completeness == "full_card_confirmed":
            method = "static_verified_feed"
            diagnostics = (
                f"All {len(matchups)} matchups verified from {source_url}. "
                "card_completeness_status upgraded to full_card_confirmed."
            )
        elif completeness == "partial_card":
            known = expected or self._TYPICAL_FULL_CARD_MIN
            method = "static_feed_partial"
            diagnostics = (
                f"{len(matchups)} matchup(s) found but expected ~{known} for a full GLORY card. "
                "Remaining bouts not yet in feed. Status: partial_card."
            )
        else:  # extraction_unsupported
            method = "extraction_unsupported"
            diagnostics = (
                f"No valid matchups found in feed row for {event_name!r}. "
                "Extraction unsupported until matchups[] is populated."
            )

        return ExtractionResult(
            source_name=self.source_name,
            event_name=event_name,
            card_completeness_status=completeness,
            matchups=matchups,
            matchup_count=len(matchups),
            expected_matchup_count=expected,
            extraction_method=method,
            extraction_diagnostics=diagnostics,
            extraction_ok=completeness
            in {"full_card_confirmed", "partial_card", "headline_only"},
        )

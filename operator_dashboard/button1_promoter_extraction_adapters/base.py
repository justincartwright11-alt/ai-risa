"""
Base adapter contract and ExtractionResult for Button 1 governed full-card extraction.

All adapters are read-only and fail closed. No writes, no PDFs, no auto-saves.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


VALID_CARD_COMPLETENESS_STATUSES: frozenset = frozenset(
    {
        "full_card_confirmed",
        "partial_card",
        "headline_only",
        "extraction_unsupported",
        "needs_review",
    }
)


@dataclass
class ExtractionResult:
    """
    Read-only result returned by a promoter extraction adapter.

    preview_only is always True. write_authorized is always False.
    No writes, no PDF generation, no delivery, no learning/calibration.
    """

    source_name: str
    event_name: str
    card_completeness_status: str
    matchups: List[Dict[str, Any]]
    matchup_count: int
    expected_matchup_count: Optional[int]
    extraction_method: str
    extraction_diagnostics: str
    extraction_ok: bool
    error: Optional[str] = None
    preview_only: bool = True
    write_authorized: bool = False

    def __post_init__(self) -> None:
        if self.card_completeness_status not in VALID_CARD_COMPLETENESS_STATUSES:
            raise ValueError(
                f"Invalid card_completeness_status: {self.card_completeness_status!r}. "
                f"Must be one of {sorted(VALID_CARD_COMPLETENESS_STATUSES)}"
            )
        # Governance enforcement: these must never flip
        object.__setattr__(self, "preview_only", True)
        object.__setattr__(self, "write_authorized", False)


class BaseEventCardExtractionAdapter(ABC):
    """
    Abstract base for all governed promoter extraction adapters.

    Subclasses declare their source_name and supported_url_patterns.
    The extract() method must be read-only and fail closed.
    """

    source_name: str = ""
    supported_url_patterns: List[str] = []

    def can_handle(self, event_row: Dict[str, Any]) -> bool:
        """Return True if this adapter can handle the given event row."""
        source = str(event_row.get("source_name") or "").strip()
        if source and source == self.source_name:
            return True
        src_url = str(event_row.get("source_url") or "").strip().lower()
        for pattern in self.supported_url_patterns:
            if pattern.lower() in src_url:
                return True
        return False

    @abstractmethod
    def extract(self, event_row: Dict[str, Any]) -> ExtractionResult:
        """
        Extract full-card matchup information from the event row.

        Must be read-only. Must not write any files, queue rows, PDFs,
        or trigger learning/calibration. Must fail closed on any error.
        """
        ...

    # ------------------------------------------------------------------
    # Protected helpers shared by all subclasses
    # ------------------------------------------------------------------

    def _valid_matchups(self, matchups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return only matchups that have non-empty fighter_a and fighter_b."""
        out = []
        for m in matchups:
            if not isinstance(m, dict):
                continue
            fa = str(m.get("fighter_a") or "").strip()
            fb = str(m.get("fighter_b") or "").strip()
            if fa and fb:
                out.append(m)
        return out

    def _is_url_backed(self, url: str) -> bool:
        return isinstance(url, str) and url.strip().lower().startswith(("http://", "https://"))

    def _matchup_has_provenance(self, matchup: Dict[str, Any], event_source_url: str) -> bool:
        """Return True if the matchup carries URL-backed provenance (matchup-level or inherited)."""
        mu_url = str(matchup.get("source_url") or "").strip()
        return self._is_url_backed(mu_url) or self._is_url_backed(event_source_url)

    def _classify_completeness(
        self,
        valid_matchups: List[Dict[str, Any]],
        expected_count: Optional[int],
        event_source_url: str,
    ) -> str:
        """
        Classify card completeness status based on available matchup data.

        Rules:
          - 0 valid matchups → extraction_unsupported
          - 1 valid matchup → headline_only
          - expected_count known AND actual >= expected AND all URL-backed → full_card_confirmed
          - otherwise → partial_card
        """
        count = len(valid_matchups)
        if count == 0:
            return "extraction_unsupported"
        if count == 1:
            return "headline_only"
        if expected_count is not None and count >= expected_count:
            all_backed = all(
                self._matchup_has_provenance(m, event_source_url) for m in valid_matchups
            )
            if all_backed:
                return "full_card_confirmed"
        return "partial_card"

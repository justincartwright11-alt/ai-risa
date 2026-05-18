"""
Adapter registry and dispatcher for Button 1 governed full-card extraction.

get_adapter_for_event_row() returns the first adapter that can_handle() the row.
run_extraction_for_event_row() dispatches to the correct adapter, or returns
extraction_unsupported if no adapter is registered for the source.

Governance: all dispatched calls are read-only. No writes, no PDFs, no auto-saves.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import BaseEventCardExtractionAdapter, ExtractionResult
from .matchroom_boxing import MatchroomBoxingAdapter
from .ufc_mma import UFCMMAAdapter
from .glory_kickboxing import GLORYKickboxingAdapter


# Ordered list of registered adapters.
# Checked in order — first match wins.
_REGISTERED_ADAPTERS: List[BaseEventCardExtractionAdapter] = [
    MatchroomBoxingAdapter(),
    UFCMMAAdapter(),
    GLORYKickboxingAdapter(),
]


def get_adapter_for_event_row(
    event_row: Dict[str, Any],
) -> Optional[BaseEventCardExtractionAdapter]:
    """Return the first registered adapter that can handle this event row, or None."""
    for adapter in _REGISTERED_ADAPTERS:
        if adapter.can_handle(event_row):
            return adapter
    return None


def run_extraction_for_event_row(event_row: Dict[str, Any]) -> ExtractionResult:
    """
    Dispatch extraction to the appropriate adapter.

    If no adapter matches the source, returns an ExtractionResult with
    card_completeness_status='extraction_unsupported'.

    Always read-only. Always preview_only=True, write_authorized=False.
    """
    adapter = get_adapter_for_event_row(event_row)
    if adapter is None:
        event_name = str(event_row.get("event_name") or "").strip()
        source_name = str(event_row.get("source_name") or "").strip()
        return ExtractionResult(
            source_name=source_name or "unknown",
            event_name=event_name,
            card_completeness_status="extraction_unsupported",
            matchups=[],
            matchup_count=0,
            expected_matchup_count=None,
            extraction_method="no_adapter_registered",
            extraction_diagnostics=(
                f"No extraction adapter registered for source_name={source_name!r}. "
                "Register an adapter in the registry to enable full-card extraction."
            ),
            extraction_ok=False,
            error="no_adapter_registered",
        )
    return adapter.extract(event_row)


def list_registered_source_names() -> List[str]:
    """Return source_name values of all registered adapters (for diagnostics)."""
    return [a.source_name for a in _REGISTERED_ADAPTERS]

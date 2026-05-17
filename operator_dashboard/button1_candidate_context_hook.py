"""Button 1 candidate fighter context extraction hook for identity resolver preview.

This module extracts real fighter context from Button 1 discovery candidate rows
and builds preview-safe IncomingFighterCandidate payloads for the identity resolver.

No writes, no merges, no profile operations. Preview-only context binding only.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any

from operator_dashboard.global_fighter_identity_resolver_preview import (
    IncomingFighterCandidate,
    SourceRef,
)
from operator_dashboard.global_fighter_identity_known_records_context import (
    build_known_records_context_preview,
)


@dataclass
class Button1CandidateContextExtractResult:
    """Result of extracting candidate context from Button 1 workflow."""
    candidates: List[IncomingFighterCandidate]
    candidates_count: int
    manual_review_count: int
    conflict_count: int
    missing_source_refs_count: int
    extraction_safe: bool
    extraction_errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "candidates": [asdict(c) for c in self.candidates],
            "candidates_count": self.candidates_count,
            "manual_review_count": self.manual_review_count,
            "conflict_count": self.conflict_count,
            "missing_source_refs_count": self.missing_source_refs_count,
            "extraction_safe": self.extraction_safe,
            "extraction_errors": self.extraction_errors,
        }


def extract_button1_candidate_context_for_identity_resolver(
    candidate_rows: Optional[List[Dict[str, Any]]] = None,
) -> Button1CandidateContextExtractResult:
    """
    Extract fighter candidate context from Button 1 discovery candidate rows.

    Args:
        candidate_rows: List of candidate row dicts from Button 1 discovery workflow.
                        Each row is expected to have fighter names and metadata.

    Returns:
        Button1CandidateContextExtractResult with:
        - candidates: List of IncomingFighterCandidate objects
        - counts: candidates_count, manual_review_count, conflict_count, etc.
        - safety flags: extraction_safe, extraction_errors
    """
    errors = []
    candidates = []
    manual_review_count = 0
    conflict_count = 0
    missing_source_refs_count = 0

    if not candidate_rows:
        candidate_rows = []

    if not isinstance(candidate_rows, list):
        errors.append("candidate_rows must be a list")
        return Button1CandidateContextExtractResult(
            candidates=[],
            candidates_count=0,
            manual_review_count=0,
            conflict_count=0,
            missing_source_refs_count=0,
            extraction_safe=len(errors) == 0,
            extraction_errors=errors,
        )

    # Extract fighter candidates from each row
    for idx, row in enumerate(candidate_rows):
        if not isinstance(row, dict):
            errors.append(f"row[{idx}] is not a dict")
            continue

        # Extract fighter names
        fighter_a_name = _extract_fighter_name(row, "fighter_a_name", "fighter_a")
        fighter_b_name = _extract_fighter_name(row, "fighter_b_name", "fighter_b")

        # Skip rows with missing fighter names (fail closed)
        if not fighter_a_name:
            errors.append(f"row[{idx}] missing fighter_a_name")
            continue
        if not fighter_b_name:
            errors.append(f"row[{idx}] missing fighter_b_name")
            continue

        # Build source ref from Button 1 discovery context
        source_ref = _build_button1_source_ref(row, idx)

        # Extract metadata for both fighters
        promotion = _extract_field(row, "promotion", "event_name")
        division = _extract_field(row, "division", "weight_class")
        sport_ruleset = _extract_field(row, "sport_ruleset", "sport")
        event_date = _extract_field(row, "event_date", "date")

        # Build IncomingFighterCandidate for Fighter A
        candidate_a = IncomingFighterCandidate(
            name=fighter_a_name,
            aliases=[],
            nationality=None,
            promotion=promotion,
            sport_ruleset=sport_ruleset,
            division=division,
            date_of_birth=None,
            height=None,
            reach=None,
            stance=None,
            record=None,
            source_refs=[source_ref],
        )
        candidates.append(candidate_a)

        # Build IncomingFighterCandidate for Fighter B
        candidate_b = IncomingFighterCandidate(
            name=fighter_b_name,
            aliases=[],
            nationality=None,
            promotion=promotion,
            sport_ruleset=sport_ruleset,
            division=division,
            date_of_birth=None,
            height=None,
            reach=None,
            stance=None,
            record=None,
            source_refs=[source_ref],
        )
        candidates.append(candidate_b)

    # Safety checks after extraction
    for candidate in candidates:
        if not candidate.source_refs or len(candidate.source_refs) == 0:
            missing_source_refs_count += 1
            # This should not happen given our build process, but check anyway
            errors.append(f"candidate {candidate.name} has no source_refs")

    extraction_safe = len(errors) == 0
    candidates_count = len(candidates)

    return Button1CandidateContextExtractResult(
        candidates=candidates,
        candidates_count=candidates_count,
        manual_review_count=manual_review_count,
        conflict_count=conflict_count,
        missing_source_refs_count=missing_source_refs_count,
        extraction_safe=extraction_safe,
        extraction_errors=errors,
    )


def _extract_fighter_name(row: Dict[str, Any], *field_names: str) -> str:
    """Extract fighter name from row, trying multiple field names."""
    for field in field_names:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_field(row: Dict[str, Any], *field_names: str) -> Optional[str]:
    """Extract optional field from row, trying multiple field names."""
    for field in field_names:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_button1_source_ref(row: Dict[str, Any], row_index: int) -> SourceRef:
    """Build source ref from Button 1 discovery row context."""
    # Try to get source information from row
    source_name = _extract_field(row, "source_name", "source", "provider") or "button1_discovery"
    source_url = _extract_field(row, "source_url", "url")
    source_type = "button1_discovery"
    source_date = _extract_field(row, "event_date", "date", "source_date")

    return SourceRef(
        source_name=source_name,
        source_url=source_url,
        source_type=source_type,
        source_date=source_date,
    )


def build_identity_resolver_payload_from_button1_context(
    candidate_rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build identity resolver preview payload from Button 1 candidate context.

    Returns a dict with:
    - candidates: list of IncomingFighterCandidate dicts
    - known_records: empty list (preview only, no known records)
    - source: "button1_discovery"
    - preview_only: true
    - all write flags: false
    """
    return build_identity_resolver_payload_from_button1_context_with_known_records(
        candidate_rows=candidate_rows,
        in_memory_known_records=None,
    )


def build_identity_resolver_payload_from_button1_context_with_known_records(
    candidate_rows: Optional[List[Dict[str, Any]]] = None,
    in_memory_known_records: Any = None,
) -> Dict[str, Any]:
    """Build preview-safe resolver payload from Button 1 context + known records.

    Known records are sanitized using the known-records preview context builder.
    No writes are performed.
    """
    extraction_result = extract_button1_candidate_context_for_identity_resolver(candidate_rows)
    known_context = build_known_records_context_preview(in_memory_known_records)

    return {
        "candidates": [asdict(c) for c in extraction_result.candidates],
        "known_records": list(known_context.known_records),
        "source": "button1_discovery",
        "preview_only": True,
        "profile_create_performed": False,
        "profile_update_performed": False,
        "merge_performed": False,
        "database_write_performed": False,
        "ranking_write_performed": False,
        "learning_apply_performed": False,
        "calibration_write_performed": False,
        "known_records_context": known_context.to_dict(),
        "extraction_result": extraction_result.to_dict(),
    }

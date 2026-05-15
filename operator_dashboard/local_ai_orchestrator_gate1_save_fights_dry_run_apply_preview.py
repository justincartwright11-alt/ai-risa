"""Preview-only Gate 1 dry-run apply checks for save-fights candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

from operator_dashboard.local_ai_orchestrator_gate1_token_check import check_gate1_approval_token_preview


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list_of_dict(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(v) for v in value if isinstance(v, dict)]


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _candidate_identifier(row: Mapping[str, Any]) -> str:
    for key in ("candidate_id", "fight_id", "fight_key", "matchup_key", "id", "fight_name"):
        value = _safe_text(row.get(key))
        if value:
            return value
    return ""


def _is_duplicate_or_conflict(row: Mapping[str, Any]) -> bool:
    bool_keys = [
        "duplicate_or_conflict",
        "is_duplicate",
        "duplicate",
        "has_conflict",
        "is_conflict",
        "conflict",
    ]
    if any(row.get(key) is True for key in bool_keys):
        return True

    state = _safe_text(row.get("state")).lower()
    status = _safe_text(row.get("status")).lower()
    state_tokens = {"duplicate", "conflict", "duplicate_or_conflict", "blocked_duplicate", "blocked_conflict"}
    return state in state_tokens or status in state_tokens


def _has_provenance(row: Mapping[str, Any]) -> bool:
    provenance = row.get("provenance")
    if isinstance(provenance, dict):
        source_url = _safe_text(provenance.get("source_url"))
        if source_url:
            return True
        source_urls = provenance.get("source_urls")
        if isinstance(source_urls, list):
            if any(_safe_text(url) for url in source_urls):
                return True

    direct_source_url = _safe_text(row.get("source_url"))
    canonical_source_url = _safe_text(row.get("canonical_source_url"))
    provenance_url = _safe_text(row.get("provenance_url"))
    if direct_source_url or canonical_source_url or provenance_url:
        return True

    source_urls = row.get("source_urls")
    if isinstance(source_urls, list):
        if any(_safe_text(url) for url in source_urls):
            return True

    return False


def _normalize_scope_values(raw_scope: Any) -> Optional[Set[str]]:
    if raw_scope is None:
        return None

    values: List[str] = []
    if isinstance(raw_scope, dict):
        values = [_safe_text(k) for k in raw_scope.keys()]
    elif isinstance(raw_scope, (list, tuple, set)):
        values = [_safe_text(v) for v in raw_scope]
    elif isinstance(raw_scope, str):
        cleaned = _safe_text(raw_scope)
        if cleaned:
            values = [cleaned]
    else:
        return set()

    return {v for v in values if v}


def _resolve_scope(token_preview: Mapping[str, Any], candidate_scope: Any) -> Optional[Set[str]]:
    raw_scope = candidate_scope
    if raw_scope is None:
        raw_scope = token_preview.get("candidate_scope")
    if raw_scope is None:
        raw_scope = token_preview.get("candidate_ids")
    if raw_scope is None:
        raw_scope = token_preview.get("candidate_keys")
    return _normalize_scope_values(raw_scope)


@dataclass
class Gate1SaveFightsDryRunApplyPreviewResult:
    ok: bool
    eligible_for_future_approval: bool
    future_write_eligibility: bool
    preview_only: bool = True
    write_authorized: bool = False
    mutation_performed: bool = False
    queue_write_performed: bool = False
    database_write_performed: bool = False
    candidate_scope_present: bool = False
    candidate_scope_empty: bool = True
    scoped_candidate_count: int = 0
    would_save_count: int = 0
    duplicate_or_conflict_count: int = 0
    provenance_missing_count: int = 0
    blocking_reasons: List[str] = None
    would_save_candidate_ids: List[str] = None
    blocked_candidate_ids: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["blocking_reasons"] is None:
            data["blocking_reasons"] = []
        if data["would_save_candidate_ids"] is None:
            data["would_save_candidate_ids"] = []
        if data["blocked_candidate_ids"] is None:
            data["blocked_candidate_ids"] = []
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def run_gate1_save_fights_dry_run_apply_preview(
    gate_approval_token_preview: Optional[Mapping[str, Any]],
    candidate_rows: Optional[Iterable[Mapping[str, Any]]] = None,
    candidate_scope: Any = None,
) -> Gate1SaveFightsDryRunApplyPreviewResult:
    """Run preview-only Gate 1 save-fights dry-run checks without any writes."""
    token_result = check_gate1_approval_token_preview(gate_approval_token_preview)
    token_preview = _safe_dict(gate_approval_token_preview)

    blocking_reasons = list(token_result.blocking_reasons or [])
    input_rows = _safe_list_of_dict(list(candidate_rows) if candidate_rows is not None else [])

    scope_values = _resolve_scope(token_preview, candidate_scope)
    candidate_scope_present = scope_values is not None
    candidate_scope_empty = scope_values is None or len(scope_values) == 0

    scoped_rows = input_rows
    if scope_values is not None and len(scope_values) > 0:
        scoped_rows = [row for row in input_rows if _candidate_identifier(row) in scope_values]
        if not scoped_rows:
            blocking_reasons.append("candidate scope does not match any provided candidate rows")

    duplicate_or_conflict_count = 0
    provenance_missing_count = 0
    would_save_candidate_ids: List[str] = []
    blocked_candidate_ids: List[str] = []

    for idx, row in enumerate(scoped_rows):
        candidate_id = _candidate_identifier(row) or f"index:{idx}"
        blocked = False

        if _is_duplicate_or_conflict(row):
            duplicate_or_conflict_count += 1
            blocked = True

        if not _has_provenance(row):
            provenance_missing_count += 1
            blocked = True

        if blocked:
            blocked_candidate_ids.append(candidate_id)
        else:
            would_save_candidate_ids.append(candidate_id)

    hard_blocked = not token_result.ok
    if hard_blocked:
        eligible_for_future_approval = False
    else:
        eligible_for_future_approval = len(would_save_candidate_ids) > 0

    return Gate1SaveFightsDryRunApplyPreviewResult(
        ok=not hard_blocked,
        eligible_for_future_approval=eligible_for_future_approval,
        future_write_eligibility=eligible_for_future_approval,
        preview_only=True,
        write_authorized=False,
        mutation_performed=False,
        queue_write_performed=False,
        database_write_performed=False,
        candidate_scope_present=candidate_scope_present,
        candidate_scope_empty=candidate_scope_empty,
        scoped_candidate_count=len(scoped_rows),
        would_save_count=len(would_save_candidate_ids),
        duplicate_or_conflict_count=duplicate_or_conflict_count,
        provenance_missing_count=provenance_missing_count,
        blocking_reasons=blocking_reasons,
        would_save_candidate_ids=would_save_candidate_ids,
        blocked_candidate_ids=blocked_candidate_ids,
    )


__all__ = [
    "Gate1SaveFightsDryRunApplyPreviewResult",
    "run_gate1_save_fights_dry_run_apply_preview",
]

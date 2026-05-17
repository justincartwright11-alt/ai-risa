"""Preview-only known fighter records context builder for Button 1 identity resolver.

Builds a sanitized in-memory known-records list compatible with the existing
identity resolver preview API. No writes, no merges, no profile actions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple


_SAFE_FIELDS = {
    "fighter_global_id",
    "full_name",
    "known_aliases",
    "nationality",
    "promotion",
    "sport_ruleset",
    "division",
    "date_of_birth",
    "height",
    "reach",
    "stance",
    "record",
    "active_years",
    "confidence_grade",
}


def _safe_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_optional_text(value: Any) -> Optional[str]:
    txt = _safe_text(value)
    return txt or None


def _safe_aliases(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    seen = set()
    for item in value:
        txt = _safe_text(item)
        if not txt:
            continue
        key = txt.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(txt)
    return out


def _safe_record(value: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(value, Mapping):
        return None
    out: Dict[str, Any] = {}
    for k in ("wins", "losses", "draws"):
        if k in value:
            out[k] = value[k]
    return out or None


def _safe_active_years(value: Any) -> Optional[Tuple[int, int]]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        try:
            start = int(value[0])
            end = int(value[1])
            return (start, end)
        except Exception:
            return None
    return None


def _safe_confidence_grade(value: Any) -> str:
    txt = _safe_text(value).upper()
    if txt in {"A", "B", "C", "D", "F"}:
        return txt
    return "C"


@dataclass
class KnownRecordsContextPreviewResult:
    known_records: List[Dict[str, Any]]
    records_received_count: int
    records_accepted_count: int
    malformed_records_count: int
    preview_only: bool = True
    profile_create_performed: bool = False
    profile_update_performed: bool = False
    merge_performed: bool = False
    database_write_performed: bool = False
    ranking_write_performed: bool = False
    learning_apply_performed: bool = False
    calibration_write_performed: bool = False
    errors: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["errors"] is None:
            data["errors"] = []
        return data


def sanitize_known_fighter_record_preview(raw_record: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """Sanitize a single in-memory known fighter record to safe preview fields.

    Returns None when required fields are missing or malformed.
    """
    if not isinstance(raw_record, Mapping):
        return None

    fighter_global_id = _safe_text(raw_record.get("fighter_global_id"))
    full_name = _safe_text(raw_record.get("full_name"))
    if not fighter_global_id or not full_name:
        return None

    sanitized: Dict[str, Any] = {
        "fighter_global_id": fighter_global_id,
        "full_name": full_name,
        "known_aliases": _safe_aliases(raw_record.get("known_aliases")),
        "nationality": _safe_optional_text(raw_record.get("nationality")),
        "promotion": _safe_optional_text(raw_record.get("promotion")),
        "sport_ruleset": _safe_optional_text(raw_record.get("sport_ruleset")),
        "division": _safe_optional_text(raw_record.get("division")),
        "date_of_birth": _safe_optional_text(raw_record.get("date_of_birth")),
        "height": _safe_optional_text(raw_record.get("height")),
        "reach": _safe_optional_text(raw_record.get("reach")),
        "stance": _safe_optional_text(raw_record.get("stance")),
        "record": _safe_record(raw_record.get("record")),
        "active_years": _safe_active_years(raw_record.get("active_years")),
        "confidence_grade": _safe_confidence_grade(raw_record.get("confidence_grade")),
    }

    # Ensure we only return the explicit safe fields.
    return {k: sanitized.get(k) for k in _SAFE_FIELDS}


def build_known_records_context_preview(in_memory_known_records: Any) -> KnownRecordsContextPreviewResult:
    """Build preview-only known-records context from in-memory records.

    - Accepts only in-memory list of dict records.
    - Sanitizes fields to safe comparison fields only.
    - Fails closed on malformed records.
    - Returns empty safe context when no records exist.
    """
    errors: List[str] = []

    if in_memory_known_records is None:
        records: List[Mapping[str, Any]] = []
    elif isinstance(in_memory_known_records, list):
        records = in_memory_known_records
    else:
        errors.append("known_records must be provided as a list")
        return KnownRecordsContextPreviewResult(
            known_records=[],
            records_received_count=0,
            records_accepted_count=0,
            malformed_records_count=0,
            errors=errors,
        )

    known_records: List[Dict[str, Any]] = []
    malformed_records_count = 0

    for idx, raw in enumerate(records):
        if not isinstance(raw, Mapping):
            malformed_records_count += 1
            errors.append(f"record[{idx}] is not an object")
            continue

        sanitized = sanitize_known_fighter_record_preview(raw)
        if not sanitized:
            malformed_records_count += 1
            errors.append(f"record[{idx}] missing required fighter_global_id/full_name")
            continue

        known_records.append(sanitized)

    return KnownRecordsContextPreviewResult(
        known_records=known_records,
        records_received_count=len(records),
        records_accepted_count=len(known_records),
        malformed_records_count=malformed_records_count,
        errors=errors,
    )


__all__ = [
    "KnownRecordsContextPreviewResult",
    "sanitize_known_fighter_record_preview",
    "build_known_records_context_preview",
]

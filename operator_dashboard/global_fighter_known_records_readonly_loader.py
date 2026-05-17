"""Preview-only readonly known fighter records loader.

Loads sanitized known fighter records from safe sources (in-memory or local seeds)
for identity resolver preview matching. No writes, no mutations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional


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


def _safe_active_years(value: Any) -> Optional[tuple]:
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


def _safe_dict_copy(d: Any) -> Dict[str, Any]:
    if isinstance(d, dict):
        return dict(d)
    return {}


@dataclass
class KnownRecordsReadonlyLoaderResult:
    """Result of loading known fighter records safely."""

    known_records: List[Dict[str, Any]]
    records_received_count: int
    records_accepted_count: int
    malformed_records_count: int
    source_type: str  # "in_memory" | "local_seed" | "empty"
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


def _sanitize_single_known_record(raw: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """Sanitize a single known fighter record to safe preview fields.

    Returns None if required fields are missing or malformed.
    """
    if not isinstance(raw, Mapping):
        return None

    fighter_global_id = _safe_text(raw.get("fighter_global_id"))
    full_name = _safe_text(raw.get("full_name"))
    if not fighter_global_id or not full_name:
        return None

    # Safe comparison fields only
    sanitized: Dict[str, Any] = {
        "fighter_global_id": fighter_global_id,
        "full_name": full_name,
        "known_aliases": _safe_aliases(raw.get("known_aliases")),
        "nationality": _safe_optional_text(raw.get("nationality")),
        "promotion": _safe_optional_text(raw.get("promotion")),
        "sport_ruleset": _safe_optional_text(raw.get("sport_ruleset")),
        "division": _safe_optional_text(raw.get("division")),
        "date_of_birth": _safe_optional_text(raw.get("date_of_birth")),
        "height": _safe_optional_text(raw.get("height")),
        "reach": _safe_optional_text(raw.get("reach")),
        "stance": _safe_optional_text(raw.get("stance")),
        "record": _safe_record(raw.get("record")),
        "active_years": _safe_active_years(raw.get("active_years")),
        "confidence_grade": _safe_confidence_grade(raw.get("confidence_grade")),
    }

    # Preserve provenance and completeness hints if present
    provenance_src = raw.get("loader_source_type")
    if isinstance(provenance_src, str):
        sanitized["loader_source_type"] = _safe_text(provenance_src)
    provenance_name = raw.get("loader_source_name")
    if isinstance(provenance_name, str):
        sanitized["loader_source_name"] = _safe_text(provenance_name)
    provenance_ts = raw.get("loader_snapshot_ts")
    if isinstance(provenance_ts, str):
        sanitized["loader_snapshot_ts"] = _safe_text(provenance_ts)

    completeness = raw.get("completeness_flags")
    if isinstance(completeness, dict):
        sanitized["completeness_flags"] = _safe_dict_copy(completeness)

    return sanitized


def load_known_records_readonly_preview(
    in_memory_records: Any = None,
    local_seed_records: Any = None,
) -> KnownRecordsReadonlyLoaderResult:
    """Load known fighter records from safe sources for identity resolver preview.

    Priority: in_memory_records > local_seed_records > empty

    No writes are performed. All output is preview-only.
    """
    errors: List[str] = []
    source_type = "empty"
    records_to_process: List[Mapping[str, Any]] = []

    # Priority 1: in_memory_records
    if in_memory_records is not None:
        if isinstance(in_memory_records, list):
            records_to_process = in_memory_records
            source_type = "in_memory"
        else:
            errors.append("in_memory_records must be a list")
            return KnownRecordsReadonlyLoaderResult(
                known_records=[],
                records_received_count=0,
                records_accepted_count=0,
                malformed_records_count=0,
                source_type="empty",
                errors=errors,
            )

    # Priority 2: local_seed_records (only if in_memory not provided)
    if not records_to_process and local_seed_records is not None:
        if isinstance(local_seed_records, list):
            records_to_process = local_seed_records
            source_type = "local_seed"
        else:
            errors.append("local_seed_records must be a list")

    # Process records
    known_records: List[Dict[str, Any]] = []
    malformed_records_count = 0

    for idx, raw in enumerate(records_to_process):
        if not isinstance(raw, Mapping):
            malformed_records_count += 1
            errors.append(f"record[{idx}] is not an object")
            continue

        sanitized = _sanitize_single_known_record(raw)
        if not sanitized:
            malformed_records_count += 1
            errors.append(f"record[{idx}] missing required fighter_global_id/full_name")
            continue

        known_records.append(sanitized)

    return KnownRecordsReadonlyLoaderResult(
        known_records=known_records,
        records_received_count=len(records_to_process),
        records_accepted_count=len(known_records),
        malformed_records_count=malformed_records_count,
        source_type=source_type,
        errors=errors,
    )


__all__ = [
    "KnownRecordsReadonlyLoaderResult",
    "load_known_records_readonly_preview",
]

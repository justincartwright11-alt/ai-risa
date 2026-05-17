"""Preview-only known fighter records source-pack builder.

Combines multiple read-only known-record sources into a sanitized resolver-compatible
known_records payload. No writes, no mutations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple


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
    for key in ("wins", "losses", "draws"):
        if key in value:
            out[key] = value[key]
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


def _safe_dict_copy(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _norm_name(name: str) -> str:
    return " ".join(_safe_text(name).lower().split())


@dataclass
class SourcePackPreviewResult:
    """Result envelope for preview-only source-pack builder."""

    known_records: List[Dict[str, Any]]
    records_received_count: int
    records_accepted_count: int
    malformed_records_count: int
    source_type: str = "source_pack"
    preview_only: bool = True
    profile_create_performed: bool = False
    profile_update_performed: bool = False
    merge_performed: bool = False
    database_write_performed: bool = False
    ranking_write_performed: bool = False
    learning_apply_performed: bool = False
    calibration_write_performed: bool = False
    errors: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["errors"] is None:
            data["errors"] = []
        return data


def _sanitize_single_known_record(raw: Mapping[str, Any], src_type: str) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, Mapping):
        return None

    fighter_global_id = _safe_text(raw.get("fighter_global_id"))
    full_name = _safe_text(raw.get("full_name"))
    if not fighter_global_id or not full_name:
        return None

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
        "loader_source_type": _safe_text(raw.get("loader_source_type")) or src_type,
        "loader_source_name": _safe_text(raw.get("loader_source_name")) or src_type,
    }

    snapshot_ts = _safe_text(raw.get("loader_snapshot_ts"))
    if snapshot_ts:
        sanitized["loader_snapshot_ts"] = snapshot_ts

    origin_id = _safe_text(raw.get("loader_record_origin_id"))
    if origin_id:
        sanitized["loader_record_origin_id"] = origin_id

    completeness = _safe_dict_copy(raw.get("completeness_flags"))
    if completeness is not None:
        sanitized["completeness_flags"] = completeness

    return sanitized


def _collect_source_records(value: Any, label: str, errors: List[str]) -> List[Mapping[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def _is_empty_value(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {} or value == ()


def _merge_two_records(higher: Dict[str, Any], lower: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(higher)

    # Keep higher precedence identity fields, but fill missing optionals from lower.
    for key in (
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
        "loader_snapshot_ts",
        "loader_record_origin_id",
    ):
        if _is_empty_value(out.get(key)) and not _is_empty_value(lower.get(key)):
            out[key] = lower.get(key)

    if _is_empty_value(out.get("confidence_grade")) and not _is_empty_value(lower.get("confidence_grade")):
        out["confidence_grade"] = lower.get("confidence_grade")

    # Alias union preserving original casing from higher first, then lower.
    combined_aliases = []
    seen = set()
    for alias in list(out.get("known_aliases", [])) + list(lower.get("known_aliases", [])):
        txt = _safe_text(alias)
        if not txt:
            continue
        key = txt.lower()
        if key in seen:
            continue
        seen.add(key)
        combined_aliases.append(txt)
    out["known_aliases"] = combined_aliases

    # Merge completeness flags conservatively.
    c_high = out.get("completeness_flags") if isinstance(out.get("completeness_flags"), dict) else {}
    c_low = lower.get("completeness_flags") if isinstance(lower.get("completeness_flags"), dict) else {}
    if c_high or c_low:
        merged_flags: Dict[str, Any] = {}
        for key in set(c_high.keys()).union(c_low.keys()):
            if isinstance(c_high.get(key), bool) or isinstance(c_low.get(key), bool):
                merged_flags[key] = bool(c_high.get(key)) or bool(c_low.get(key))
            else:
                merged_flags[key] = c_high.get(key) if key in c_high else c_low.get(key)
        out["completeness_flags"] = merged_flags

    lineage = []
    for val in [higher.get("loader_source_type"), lower.get("loader_source_type")]:
        txt = _safe_text(val)
        if txt and txt not in lineage:
            lineage.append(txt)
    if len(lineage) > 1:
        out["loader_source_lineage"] = lineage

    return out


def build_known_records_source_pack_preview(
    manual_operator_records: Any = None,
    local_seed_records: Any = None,
    approved_historical_records: Any = None,
    report_history_records: Any = None,
    result_ledger_records: Any = None,
    global_read_projection_records: Any = None,
) -> SourcePackPreviewResult:
    """Build preview-only known_records from multiple safe source classes.

    Source precedence (highest to lowest):
    manual_operator > local_seed > approved_historical > report_history >
    result_ledger > global_read_projection

    No writes are performed. All outputs are sanitized and preview-only.
    """
    errors: List[str] = []

    source_rows = {
        "manual_operator": _collect_source_records(manual_operator_records, "manual_operator_records", errors),
        "local_seed": _collect_source_records(local_seed_records, "local_seed_records", errors),
        "approved_historical": _collect_source_records(
            approved_historical_records,
            "approved_historical_records",
            errors,
        ),
        "report_history": _collect_source_records(report_history_records, "report_history_records", errors),
        "result_ledger": _collect_source_records(result_ledger_records, "result_ledger_records", errors),
        "global_read_projection": _collect_source_records(
            global_read_projection_records,
            "global_read_projection_records",
            errors,
        ),
    }

    precedence = {
        "manual_operator": 0,
        "local_seed": 1,
        "approved_historical": 2,
        "report_history": 3,
        "result_ledger": 4,
        "global_read_projection": 5,
    }

    source_order = [
        "manual_operator",
        "local_seed",
        "approved_historical",
        "report_history",
        "result_ledger",
        "global_read_projection",
    ]

    received_count = sum(len(rows) for rows in source_rows.values())
    malformed_count = 0

    sanitized_with_meta: List[Tuple[Dict[str, Any], int]] = []
    for src in source_order:
        for idx, raw in enumerate(source_rows[src]):
            if not isinstance(raw, Mapping):
                malformed_count += 1
                errors.append(f"{src}[{idx}] is not an object")
                continue
            sanitized = _sanitize_single_known_record(raw, src)
            if sanitized is None:
                malformed_count += 1
                errors.append(f"{src}[{idx}] missing required fighter_global_id/full_name")
                continue
            sanitized_with_meta.append((sanitized, precedence[src]))

    # Phase 1 dedupe by fighter_global_id.
    by_id: Dict[str, Tuple[Dict[str, Any], int]] = {}
    for rec, prio in sanitized_with_meta:
        rid = _safe_text(rec.get("fighter_global_id")).lower()
        if not rid:
            continue
        existing = by_id.get(rid)
        if existing is None:
            by_id[rid] = (rec, prio)
            continue
        old_rec, old_prio = existing
        if prio < old_prio:
            winner, loser = rec, old_rec
            winner_prio = prio
        else:
            winner, loser = old_rec, rec
            winner_prio = old_prio
        by_id[rid] = (_merge_two_records(winner, loser), winner_prio)

    # Phase 2 dedupe by normalized full_name.
    by_name: Dict[str, Tuple[Dict[str, Any], int]] = {}
    for rec, prio in by_id.values():
        name_key = _norm_name(rec.get("full_name", ""))
        if not name_key:
            continue
        existing = by_name.get(name_key)
        if existing is None:
            by_name[name_key] = (rec, prio)
            continue
        old_rec, old_prio = existing
        if prio < old_prio:
            winner, loser = rec, old_rec
            winner_prio = prio
        else:
            winner, loser = old_rec, rec
            winner_prio = old_prio
        by_name[name_key] = (_merge_two_records(winner, loser), winner_prio)

    final_known_records = [item[0] for item in by_name.values()]

    return SourcePackPreviewResult(
        known_records=final_known_records,
        records_received_count=received_count,
        records_accepted_count=len(final_known_records),
        malformed_records_count=malformed_count,
        errors=errors,
    )


__all__ = [
    "SourcePackPreviewResult",
    "build_known_records_source_pack_preview",
]

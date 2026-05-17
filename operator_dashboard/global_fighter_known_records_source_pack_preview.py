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


def _safe_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return value
    return None


def _pick_text(source: Mapping[str, Any], keys: Tuple[str, ...]) -> str:
    for key in keys:
        txt = _safe_text(source.get(key))
        if txt:
            return txt
    return ""


def _pick_optional_text(source: Mapping[str, Any], keys: Tuple[str, ...]) -> Optional[str]:
    txt = _pick_text(source, keys)
    return txt or None


def _pick_aliases(source: Mapping[str, Any], keys: Tuple[str, ...]) -> List[str]:
    for key in keys:
        aliases = _safe_aliases(source.get(key))
        if aliases:
            return aliases
    return []


def _pick_record(source: Mapping[str, Any], keys: Tuple[str, ...]) -> Optional[Dict[str, Any]]:
    for key in keys:
        rec = _safe_record(source.get(key))
        if rec is not None:
            return rec
    return None


def _pick_active_years(source: Mapping[str, Any], keys: Tuple[str, ...]) -> Optional[Tuple[int, int]]:
    for key in keys:
        years = _safe_active_years(source.get(key))
        if years is not None:
            return years
    return None


def _pick_nested_mapping(source: Mapping[str, Any], keys: Tuple[str, ...]) -> Optional[Mapping[str, Any]]:
    for key in keys:
        nested = _safe_mapping(source.get(key))
        if nested is not None:
            return nested
    return None


def _normalize_advanced_projection_record(raw: Mapping[str, Any], src_type: str) -> Mapping[str, Any]:
    nested_primary = _pick_nested_mapping(
        raw,
        (
            "known_record",
            "projection_known_record",
            "fighter_projection",
            "projection",
            "payload",
        ),
    )

    nested_secondary = None
    if nested_primary is not None:
        nested_secondary = _pick_nested_mapping(
            nested_primary,
            (
                "known_record",
                "fighter",
                "record",
                "projection",
                "payload",
            ),
        )

    lookup_chain: List[Mapping[str, Any]] = []
    if nested_secondary is not None:
        lookup_chain.append(nested_secondary)
    if nested_primary is not None:
        lookup_chain.append(nested_primary)
    lookup_chain.append(raw)

    def pick_text(keys: Tuple[str, ...]) -> str:
        for src in lookup_chain:
            txt = _pick_text(src, keys)
            if txt:
                return txt
        return ""

    def pick_optional_text(keys: Tuple[str, ...]) -> Optional[str]:
        for src in lookup_chain:
            txt = _pick_optional_text(src, keys)
            if txt:
                return txt
        return None

    def pick_aliases(keys: Tuple[str, ...]) -> List[str]:
        for src in lookup_chain:
            aliases = _pick_aliases(src, keys)
            if aliases:
                return aliases
        return []

    def pick_record(keys: Tuple[str, ...]) -> Optional[Dict[str, Any]]:
        for src in lookup_chain:
            rec = _pick_record(src, keys)
            if rec is not None:
                return rec
        return None

    def pick_active_years(keys: Tuple[str, ...]) -> Optional[Tuple[int, int]]:
        for src in lookup_chain:
            years = _pick_active_years(src, keys)
            if years is not None:
                return years
        return None

    def pick_dict(keys: Tuple[str, ...]) -> Optional[Dict[str, Any]]:
        for src in lookup_chain:
            for key in keys:
                copied = _safe_dict_copy(src.get(key))
                if copied is not None:
                    return copied
        return None

    normalized: Dict[str, Any] = {
        "fighter_global_id": pick_text(("fighter_global_id", "global_fighter_id", "fighter_id", "fighter_uuid")),
        "full_name": pick_text(("full_name", "fighter_name", "display_name", "name")),
        "known_aliases": pick_aliases(("known_aliases", "aliases", "nicknames")),
        "nationality": pick_optional_text(("nationality", "country", "nation")),
        "promotion": pick_optional_text(("promotion", "promotion_name", "organization", "org")),
        "sport_ruleset": pick_optional_text(("sport_ruleset", "ruleset", "sport")),
        "division": pick_optional_text(("division", "weight_class")),
        "date_of_birth": pick_optional_text(("date_of_birth", "dob", "birth_date")),
        "height": pick_optional_text(("height",)),
        "reach": pick_optional_text(("reach",)),
        "stance": pick_optional_text(("stance",)),
        "record": pick_record(("record", "win_loss_record")),
        "active_years": pick_active_years(("active_years", "career_years")),
        "confidence_grade": pick_text(("confidence_grade", "identity_confidence_grade", "confidence")),
        "loader_source_type": src_type,
        "loader_source_name": pick_text(("loader_source_name", "source_name", "projection_name")) or src_type,
    }

    snapshot_ts = pick_text(("loader_snapshot_ts", "snapshot_ts", "projection_snapshot_ts"))
    if snapshot_ts:
        normalized["loader_snapshot_ts"] = snapshot_ts

    origin_id = pick_text(("loader_record_origin_id", "record_origin_id", "projection_origin_id"))
    if origin_id:
        normalized["loader_record_origin_id"] = origin_id

    completeness = pick_dict(("completeness_flags",))
    if completeness is not None:
        normalized["completeness_flags"] = completeness

    return normalized


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
    if isinstance(value, Mapping):
        container_list = value.get("records")
        if isinstance(container_list, list):
            return container_list
        errors.append(f"{label} must be a list")
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

    advanced_projection_sources = {
        "approved_historical",
        "report_history",
        "result_ledger",
        "global_read_projection",
    }

    received_count = sum(len(rows) for rows in source_rows.values())
    malformed_count = 0

    sanitized_with_meta: List[Tuple[Dict[str, Any], int]] = []
    for src in source_order:
        for idx, raw in enumerate(source_rows[src]):
            if not isinstance(raw, Mapping):
                malformed_count += 1
                errors.append(f"{src}[{idx}] is not an object")
                continue

            candidate = raw
            if src in advanced_projection_sources:
                candidate = _normalize_advanced_projection_record(raw, src)

            sanitized = _sanitize_single_known_record(candidate, src)
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

"""Preview-only Global Fighter Record Read-Only Projection Ledger normalizer.

Normalizes multiple read-only fighter reference projection sources into
resolver-compatible known_records for identity preview.

No writes, no mutations.
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


def _safe_dict_copy(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, Mapping):
        return dict(value)
    return None


def _safe_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return value
    return None


def _norm_name(name: str) -> str:
    return " ".join(_safe_text(name).lower().split())


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


def _normalize_confidence_grade(value: str) -> Optional[str]:
    txt = _safe_text(value)
    if not txt:
        return None
    txt = txt.upper()
    if txt in {"A", "B", "C", "D", "F"}:
        return txt
    return "C"


def _sanitize_source_refs(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: List[Dict[str, Any]] = []
    seen = set()
    for item in value:
        if not isinstance(item, Mapping):
            continue
        source_name = _safe_text(item.get("source_name"))
        source_type = _safe_text(item.get("source_type"))
        if not source_name or not source_type:
            continue

        source_url = _safe_optional_text(item.get("source_url"))
        source_date = _safe_optional_text(item.get("source_date"))
        source_confidence = _safe_optional_text(item.get("source_confidence"))

        key = (source_name.lower(), source_type.lower(), (source_url or "").lower(), source_date or "")
        if key in seen:
            continue
        seen.add(key)

        ref = {
            "source_name": source_name,
            "source_type": source_type,
            "source_url": source_url,
            "source_date": source_date,
        }
        if source_confidence is not None:
            ref["source_confidence"] = source_confidence
        out.append(ref)
    return out


def _normalize_projection_row(raw: Mapping[str, Any], src_type: str) -> Dict[str, Any]:
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

    def pick_source_refs() -> List[Dict[str, Any]]:
        for src in lookup_chain:
            refs = _sanitize_source_refs(src.get("source_refs"))
            if refs:
                return refs
        return []

    confidence_raw = ""
    for src in lookup_chain:
        confidence_raw = _pick_text(src, ("confidence_grade", "identity_confidence_grade", "confidence", "projection_confidence"))
        if confidence_raw:
            break

    out: Dict[str, Any] = {
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
        "confidence_grade": _normalize_confidence_grade(confidence_raw),
        "completeness_flags": pick_dict(("completeness_flags",)) or {},
        "source_refs": pick_source_refs(),
        "projection_source_type": src_type,
        "projection_source_name": pick_text(("projection_source_name", "loader_source_name", "source_name", "projection_name"))
        or src_type,
        "projection_generated_at_preview": pick_text(
            ("projection_generated_at_preview", "projection_snapshot_ts", "loader_snapshot_ts", "snapshot_ts")
        )
        or "generated_in_preview",
        "projection_record_origin_id": pick_text(
            ("projection_record_origin_id", "projection_origin_id", "loader_record_origin_id", "record_origin_id")
        )
        or None,
    }

    return out


def _collect_source_records(value: Any, label: str, errors: List[str]) -> List[Mapping[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        rows = value.get("records")
        if isinstance(rows, list):
            return rows
        errors.append(f"{label} must be a list")
        return []
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def _is_empty(value: Any) -> bool:
    return value in (None, "", [], {}, ())


def _merge_refs(primary: List[Dict[str, Any]], secondary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for ref in primary + secondary:
        source_name = _safe_text(ref.get("source_name"))
        source_type = _safe_text(ref.get("source_type"))
        source_url = _safe_text(ref.get("source_url"))
        source_date = _safe_text(ref.get("source_date"))
        key = (source_name.lower(), source_type.lower(), source_url.lower(), source_date)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def _merge_two_records(higher: Dict[str, Any], lower: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(higher)

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
    ):
        if _is_empty(out.get(key)) and not _is_empty(lower.get(key)):
            out[key] = lower.get(key)

    if _is_empty(out.get("confidence_grade")) and not _is_empty(lower.get("confidence_grade")):
        out["confidence_grade"] = lower.get("confidence_grade")

    aliases = []
    seen_alias = set()
    for alias in list(out.get("known_aliases", [])) + list(lower.get("known_aliases", [])):
        txt = _safe_text(alias)
        if not txt:
            continue
        k = txt.lower()
        if k in seen_alias:
            continue
        seen_alias.add(k)
        aliases.append(txt)
    out["known_aliases"] = aliases

    c_high = out.get("completeness_flags") if isinstance(out.get("completeness_flags"), dict) else {}
    c_low = lower.get("completeness_flags") if isinstance(lower.get("completeness_flags"), dict) else {}
    merged_flags: Dict[str, Any] = {}
    for key in set(c_high.keys()).union(c_low.keys()):
        if isinstance(c_high.get(key), bool) or isinstance(c_low.get(key), bool):
            merged_flags[key] = bool(c_high.get(key)) or bool(c_low.get(key))
        else:
            merged_flags[key] = c_high.get(key) if key in c_high else c_low.get(key)
    if merged_flags:
        out["completeness_flags"] = merged_flags

    out["source_refs"] = _merge_refs(
        out.get("source_refs") if isinstance(out.get("source_refs"), list) else [],
        lower.get("source_refs") if isinstance(lower.get("source_refs"), list) else [],
    )

    lineage: List[str] = []
    for value in [higher.get("projection_source_type"), lower.get("projection_source_type")]:
        txt = _safe_text(value)
        if txt and txt not in lineage:
            lineage.append(txt)
    if len(lineage) > 1:
        out["projection_source_lineage"] = lineage

    return out


@dataclass
class ProjectionLedgerPreviewResult:
    known_records: List[Dict[str, Any]]
    records_received_count: int
    records_accepted_count: int
    malformed_records_count: int
    blocked_records_count: int
    source_type: str = "projection_ledger"
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


def build_projection_ledger_known_records_preview(
    manual_operator_records: Any = None,
    approved_historical_records: Any = None,
    result_ledger_records: Any = None,
    report_history_records: Any = None,
    local_seed_records: Any = None,
    global_read_projection_records: Any = None,
) -> ProjectionLedgerPreviewResult:
    """Normalize read-only projection sources into resolver-compatible known_records.

    Precedence (high to low):
    manual_operator > approved_historical > result_ledger > report_history >
    local_seed > global_read_projection

    No writes are performed. Output is preview-only.
    """
    errors: List[str] = []

    source_rows = {
        "manual_operator": _collect_source_records(manual_operator_records, "manual_operator_records", errors),
        "approved_historical": _collect_source_records(
            approved_historical_records,
            "approved_historical_records",
            errors,
        ),
        "result_ledger": _collect_source_records(result_ledger_records, "result_ledger_records", errors),
        "report_history": _collect_source_records(report_history_records, "report_history_records", errors),
        "local_seed": _collect_source_records(local_seed_records, "local_seed_records", errors),
        "global_read_projection": _collect_source_records(
            global_read_projection_records,
            "global_read_projection_records",
            errors,
        ),
    }

    source_order = [
        "manual_operator",
        "approved_historical",
        "result_ledger",
        "report_history",
        "local_seed",
        "global_read_projection",
    ]
    precedence = {name: idx for idx, name in enumerate(source_order)}

    received_count = sum(len(rows) for rows in source_rows.values())
    malformed_count = 0
    blocked_count = 0

    normalized_rows: List[Tuple[Dict[str, Any], int]] = []

    for src in source_order:
        for idx, raw in enumerate(source_rows[src]):
            if not isinstance(raw, Mapping):
                malformed_count += 1
                errors.append(f"{src}[{idx}] is not an object")
                continue

            rec = _normalize_projection_row(raw, src)

            fighter_global_id = _safe_text(rec.get("fighter_global_id"))
            full_name = _safe_text(rec.get("full_name"))
            if not fighter_global_id or not full_name:
                malformed_count += 1
                errors.append(f"{src}[{idx}] missing required fighter_global_id/full_name")
                continue

            if not rec.get("source_refs"):
                blocked_count += 1
                errors.append(f"{src}[{idx}] missing required source_refs provenance")
                continue

            if not rec.get("confidence_grade"):
                blocked_count += 1
                errors.append(f"{src}[{idx}] missing required projection confidence")
                continue

            completeness_flags = rec.get("completeness_flags") if isinstance(rec.get("completeness_flags"), dict) else {}
            completeness_flags["has_identity_core"] = True
            completeness_flags["has_provenance"] = True
            completeness_flags["projection_confidence_present"] = True
            rec["completeness_flags"] = completeness_flags

            normalized_rows.append((rec, precedence[src]))

    by_id: Dict[str, Tuple[Dict[str, Any], int]] = {}
    for rec, prio in normalized_rows:
        rid = _safe_text(rec.get("fighter_global_id")).lower()
        existing = by_id.get(rid)
        if existing is None:
            by_id[rid] = (rec, prio)
            continue
        old_rec, old_prio = existing
        if prio < old_prio:
            winner, loser, winner_prio = rec, old_rec, prio
        else:
            winner, loser, winner_prio = old_rec, rec, old_prio
        by_id[rid] = (_merge_two_records(winner, loser), winner_prio)

    by_name: Dict[str, Tuple[Dict[str, Any], int]] = {}
    for rec, prio in by_id.values():
        key = _norm_name(_safe_text(rec.get("full_name")))
        if not key:
            continue
        existing = by_name.get(key)
        if existing is None:
            by_name[key] = (rec, prio)
            continue
        old_rec, old_prio = existing
        if prio < old_prio:
            winner, loser, winner_prio = rec, old_rec, prio
        else:
            winner, loser, winner_prio = old_rec, rec, old_prio
        by_name[key] = (_merge_two_records(winner, loser), winner_prio)

    return ProjectionLedgerPreviewResult(
        known_records=[item[0] for item in by_name.values()],
        records_received_count=received_count,
        records_accepted_count=len(by_name),
        malformed_records_count=malformed_count,
        blocked_records_count=blocked_count,
        errors=errors,
    )


__all__ = [
    "ProjectionLedgerPreviewResult",
    "build_projection_ledger_known_records_preview",
]

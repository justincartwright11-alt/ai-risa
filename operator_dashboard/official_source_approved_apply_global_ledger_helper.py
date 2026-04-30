from __future__ import annotations

import hashlib
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SUCCESS_STATUSES = {
    "write_applied_pending_token_consume",
    "consume_failed_after_write",
    "write_applied",
}


def _normalize_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _sanitize_fingerprint_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key in sorted(value.keys()):
            if key in {
                "global_ledger_record_id",
                "internal_mutation_uuid",
                "local_audit_reference",
                "operation_id",
                "timestamp_utc",
                "token_consume_outcome",
            }:
                continue
            sanitized[str(key)] = _sanitize_fingerprint_payload(value[key])
        return sanitized
    if isinstance(value, list):
        return [_sanitize_fingerprint_payload(item) for item in value]
    return value


class OfficialSourceApprovedApplyGlobalLedgerHelper:
    def __init__(self, ledger_path: str | None = None):
        self._ledger_path = ledger_path or str(
            Path(tempfile.gettempdir()) / f"official_source_approved_apply_global_ledger_{uuid.uuid4().hex}.jsonl"
        )

    @property
    def ledger_path(self) -> str:
        return self._ledger_path

    def build_request_fingerprint(self, payload: object) -> str:
        canonical_payload = _sanitize_fingerprint_payload(payload)
        canonical_json = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def read_records(self, ledger_path: str | None = None) -> list[dict]:
        path = Path(ledger_path or self._ledger_path)
        if not path.exists():
            return []

        records: list[dict] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if isinstance(entry, dict):
                    records.append(entry)
        return records

    def lookup(self, local_result_key: object, request_fingerprint: str, ledger_path: str | None = None) -> dict:
        local_result_key_value = _normalize_string(local_result_key)
        if not local_result_key_value:
            return {
                "ok": False,
                "state": "missing_local_result_key",
                "local_result_key": None,
                "record": None,
                "records": [],
            }

        records = [
            record
            for record in self.read_records(ledger_path=ledger_path)
            if _normalize_string(record.get("local_result_key")) == local_result_key_value
        ]
        if not records:
            return {
                "ok": True,
                "state": "new",
                "local_result_key": local_result_key_value,
                "record": None,
                "records": [],
            }

        if any(_normalize_string(record.get("request_fingerprint")) != request_fingerprint for record in records):
            return {
                "ok": True,
                "state": "conflict",
                "local_result_key": local_result_key_value,
                "record": records[-1],
                "records": records,
            }

        replay_record = None
        for record in reversed(records):
            if _normalize_string(record.get("deterministic_status")) in _SUCCESS_STATUSES:
                replay_record = record
                break
        if replay_record is not None:
            return {
                "ok": True,
                "state": "already_recorded",
                "local_result_key": local_result_key_value,
                "record": replay_record,
                "records": records,
            }

        return {
            "ok": True,
            "state": "seen",
            "local_result_key": local_result_key_value,
            "record": records[-1],
            "records": records,
        }

    def append_record(self, *, record: dict, request_fingerprint: str, ledger_path: str | None = None) -> dict:
        path = Path(ledger_path or self._ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "global_ledger_record_id": _normalize_string(record.get("global_ledger_record_id")) or uuid.uuid4().hex,
            "local_result_key": _normalize_string(record.get("local_result_key")) or None,
            "event_id": record.get("event_id"),
            "bout_id": record.get("bout_id"),
            "fighter_ids": record.get("fighter_ids"),
            "fighter_names": record.get("fighter_names"),
            "official_source_reference": record.get("official_source_reference"),
            "approved_actual_result": record.get("approved_actual_result"),
            "operation_id": _normalize_string(record.get("operation_id")) or None,
            "internal_mutation_uuid": _normalize_string(record.get("internal_mutation_uuid")) or None,
            "approval_token_status": _normalize_string(record.get("approval_token_status")) or None,
            "guard_outcome": _normalize_string(record.get("guard_outcome")) or None,
            "apply_or_write_outcome": _normalize_string(record.get("apply_or_write_outcome")) or None,
            "token_consume_outcome": _normalize_string(record.get("token_consume_outcome")) or None,
            "local_audit_reference": record.get("local_audit_reference"),
            "timestamp_utc": _normalize_string(record.get("timestamp_utc")) or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "deterministic_status": _normalize_string(record.get("deterministic_status")) or "unknown",
            "request_fingerprint": _normalize_string(request_fingerprint),
        }

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=False) + "\n")
        return entry


__all__ = ["OfficialSourceApprovedApplyGlobalLedgerHelper"]
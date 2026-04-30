from __future__ import annotations

import hashlib
import json
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SUCCESS_STATUSES = {
    "write_applied",
    "consume_failed_after_write",
    "already_applied_replay",
}


def _normalize_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _sanitize_request_payload(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key in sorted(value.keys()):
            if key in {"approval_token", "operation_id"}:
                continue
            sanitized[str(key)] = _sanitize_request_payload(value[key])
        return sanitized
    if isinstance(value, list):
        return [_sanitize_request_payload(item) for item in value]
    return value


class OfficialSourceApprovedApplyOperationIdPersistenceHelper:
    def __init__(self, audit_path: str | None = None):
        self._audit_path = audit_path or str(
            Path(tempfile.gettempdir()) / f"official_source_approved_apply_operation_id_audit_{uuid.uuid4().hex}.jsonl"
        )

    @property
    def audit_path(self) -> str:
        return self._audit_path

    def build_request_fingerprint(self, payload: object) -> str:
        canonical_payload = _sanitize_request_payload(payload)
        canonical_json = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def read_records(self, audit_path: str | None = None) -> list[dict]:
        path = Path(audit_path or self._audit_path)
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

    def lookup(self, operation_id: object, request_fingerprint: str, audit_path: str | None = None) -> dict:
        operation_id_value = _normalize_string(operation_id)
        if not operation_id_value:
            return {
                "ok": False,
                "state": "missing_operation_id",
                "operation_id": None,
                "record": None,
                "records": [],
            }

        records = [
            record
            for record in self.read_records(audit_path=audit_path)
            if _normalize_string(record.get("operation_id")) == operation_id_value
        ]
        if not records:
            return {
                "ok": True,
                "state": "new",
                "operation_id": operation_id_value,
                "record": None,
                "records": [],
            }

        if any(_normalize_string(record.get("request_fingerprint")) != request_fingerprint for record in records):
            return {
                "ok": True,
                "state": "conflict",
                "operation_id": operation_id_value,
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
                "state": "already_applied",
                "operation_id": operation_id_value,
                "record": replay_record,
                "records": records,
            }

        return {
            "ok": True,
            "state": "seen",
            "operation_id": operation_id_value,
            "record": records[-1],
            "records": records,
        }

    def append_record(
        self,
        *,
        operation_id: str,
        internal_mutation_operation_id: str | None,
        write_attempt_id: str | None,
        request_parse_status: str,
        guard_or_authorization_outcome: str,
        apply_or_write_outcome: str,
        token_consume_outcome: str,
        deterministic_status: str,
        timestamp_utc: str | None,
        selected_key: str | None,
        token_id: str | None,
        terminal_reason_code: str | None,
        contract_version: str | None,
        endpoint_version: str | None,
        request_fingerprint: str,
        audit_path: str | None = None,
    ) -> dict:
        path = Path(audit_path or self._audit_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "timestamp_utc": _normalize_string(timestamp_utc) or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "operation_id": _normalize_string(operation_id) or None,
            "internal_mutation_operation_id": _normalize_string(internal_mutation_operation_id) or None,
            "write_attempt_id": _normalize_string(write_attempt_id) or None,
            "request_parse_status": _normalize_string(request_parse_status) or "not_evaluated",
            "guard_or_authorization_outcome": _normalize_string(guard_or_authorization_outcome) or "not_evaluated",
            "apply_or_write_outcome": _normalize_string(apply_or_write_outcome) or "not_attempted",
            "token_consume_outcome": _normalize_string(token_consume_outcome) or "not_attempted",
            "deterministic_status": _normalize_string(deterministic_status) or "unknown",
            "selected_key": _normalize_string(selected_key) or None,
            "token_id": _normalize_string(token_id) or None,
            "terminal_reason_code": _normalize_string(terminal_reason_code) or None,
            "contract_version": _normalize_string(contract_version) or None,
            "endpoint_version": _normalize_string(endpoint_version) or None,
            "request_fingerprint": _normalize_string(request_fingerprint),
        }

        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=False) + "\n")
        return entry


__all__ = ["OfficialSourceApprovedApplyOperationIdPersistenceHelper"]
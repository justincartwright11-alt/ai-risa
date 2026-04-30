from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


STATE_NOT_CONSUMED = "not_consumed"
STATE_CONSUMED = "consumed"
STATE_CONSUME_REGISTER_FAILED = "consume_register_failed"

REASON_CONSUMED = "consumed"
REASON_CONFLICT = "token_consume_conflict"
REASON_STORE_UNAVAILABLE = "token_consume_store_unavailable"
REASON_MALFORMED = "malformed_field_type"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalized_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


@dataclass(frozen=True)
class ConsumedTokenRecord:
    token_id: str
    consumed_at_utc: str
    operation_id: str
    write_attempt_id: str
    selected_key: str
    reason_code_at_consume: str
    binding_digest_expected: str
    contract_version: str
    endpoint_version: str


class OfficialSourceApprovedApplyTokenConsumeHelper:
    def __init__(self) -> None:
        self._token_records: dict[str, ConsumedTokenRecord] = {}
        self._operation_to_token: dict[str, str] = {}
        self._store_available = True

    def set_store_available(self, is_available: bool) -> None:
        self._store_available = bool(is_available)

    def lookup(self, token_id: object) -> dict:
        token_id_value = _normalized_string(token_id)
        if not token_id_value:
            return {
                "ok": False,
                "state": STATE_NOT_CONSUMED,
                "reason_code": REASON_MALFORMED,
                "errors": ["token_id is required"],
                "token_id": None,
                "record": None,
            }

        if not self._store_available:
            return {
                "ok": False,
                "state": STATE_CONSUME_REGISTER_FAILED,
                "reason_code": REASON_STORE_UNAVAILABLE,
                "errors": ["token consume store unavailable"],
                "token_id": token_id_value,
                "record": None,
            }

        record = self._token_records.get(token_id_value)
        if record is None:
            return {
                "ok": True,
                "state": STATE_NOT_CONSUMED,
                "reason_code": STATE_NOT_CONSUMED,
                "errors": [],
                "token_id": token_id_value,
                "record": None,
            }

        return {
            "ok": True,
            "state": STATE_CONSUMED,
            "reason_code": REASON_CONSUMED,
            "errors": [],
            "token_id": token_id_value,
            "record": {
                "token_id": record.token_id,
                "consumed_at_utc": record.consumed_at_utc,
                "operation_id": record.operation_id,
                "write_attempt_id": record.write_attempt_id,
                "selected_key": record.selected_key,
                "reason_code_at_consume": record.reason_code_at_consume,
                "binding_digest_expected": record.binding_digest_expected,
                "contract_version": record.contract_version,
                "endpoint_version": record.endpoint_version,
            },
        }

    def register_consume(
        self,
        token_id: object,
        *,
        operation_id: object,
        write_attempt_id: object,
        selected_key: object,
        reason_code_at_consume: object,
        binding_digest_expected: object,
        contract_version: object,
        endpoint_version: object,
        consumed_at_utc: object | None = None,
    ) -> dict:
        token_id_value = _normalized_string(token_id)
        operation_id_value = _normalized_string(operation_id)
        write_attempt_id_value = _normalized_string(write_attempt_id)
        selected_key_value = _normalized_string(selected_key)
        reason_code_value = _normalized_string(reason_code_at_consume)
        binding_digest_value = _normalized_string(binding_digest_expected)
        contract_version_value = _normalized_string(contract_version)
        endpoint_version_value = _normalized_string(endpoint_version)
        consumed_at_utc_value = _normalized_string(consumed_at_utc) if consumed_at_utc is not None else _now_utc_iso()

        errors: list[str] = []
        if not token_id_value:
            errors.append("token_id is required")
        if not operation_id_value:
            errors.append("operation_id is required")
        if not write_attempt_id_value:
            errors.append("write_attempt_id is required")
        if not selected_key_value:
            errors.append("selected_key is required")
        if not reason_code_value:
            errors.append("reason_code_at_consume is required")
        if not binding_digest_value:
            errors.append("binding_digest_expected is required")
        if not contract_version_value:
            errors.append("contract_version is required")
        if not endpoint_version_value:
            errors.append("endpoint_version is required")
        if errors:
            return {
                "ok": False,
                "state": STATE_NOT_CONSUMED,
                "token_consume_performed": False,
                "reason_code": REASON_MALFORMED,
                "errors": errors,
                "token_id": token_id_value or None,
                "record": None,
                "idempotent": False,
            }

        if not self._store_available:
            return {
                "ok": False,
                "state": STATE_CONSUME_REGISTER_FAILED,
                "token_consume_performed": False,
                "reason_code": REASON_STORE_UNAVAILABLE,
                "errors": ["token consume store unavailable"],
                "token_id": token_id_value,
                "record": None,
                "idempotent": False,
            }

        existing_for_token = self._token_records.get(token_id_value)
        if existing_for_token is not None:
            if existing_for_token.operation_id == operation_id_value:
                return {
                    "ok": True,
                    "state": STATE_CONSUMED,
                    "token_consume_performed": True,
                    "reason_code": REASON_CONSUMED,
                    "errors": [],
                    "token_id": token_id_value,
                    "record": {
                        "token_id": existing_for_token.token_id,
                        "consumed_at_utc": existing_for_token.consumed_at_utc,
                        "operation_id": existing_for_token.operation_id,
                        "write_attempt_id": existing_for_token.write_attempt_id,
                        "selected_key": existing_for_token.selected_key,
                        "reason_code_at_consume": existing_for_token.reason_code_at_consume,
                        "binding_digest_expected": existing_for_token.binding_digest_expected,
                        "contract_version": existing_for_token.contract_version,
                        "endpoint_version": existing_for_token.endpoint_version,
                    },
                    "idempotent": True,
                }
            return {
                "ok": False,
                "state": STATE_CONSUMED,
                "token_consume_performed": False,
                "reason_code": REASON_CONFLICT,
                "errors": ["token already consumed by a different operation_id"],
                "token_id": token_id_value,
                "record": {
                    "token_id": existing_for_token.token_id,
                    "consumed_at_utc": existing_for_token.consumed_at_utc,
                    "operation_id": existing_for_token.operation_id,
                    "write_attempt_id": existing_for_token.write_attempt_id,
                    "selected_key": existing_for_token.selected_key,
                    "reason_code_at_consume": existing_for_token.reason_code_at_consume,
                    "binding_digest_expected": existing_for_token.binding_digest_expected,
                    "contract_version": existing_for_token.contract_version,
                    "endpoint_version": existing_for_token.endpoint_version,
                },
                "idempotent": False,
            }

        existing_token_for_operation = self._operation_to_token.get(operation_id_value)
        if existing_token_for_operation and existing_token_for_operation != token_id_value:
            return {
                "ok": False,
                "state": STATE_CONSUME_REGISTER_FAILED,
                "token_consume_performed": False,
                "reason_code": REASON_CONFLICT,
                "errors": ["operation_id already linked to a different token_id"],
                "token_id": token_id_value,
                "record": None,
                "idempotent": False,
            }

        record = ConsumedTokenRecord(
            token_id=token_id_value,
            consumed_at_utc=consumed_at_utc_value,
            operation_id=operation_id_value,
            write_attempt_id=write_attempt_id_value,
            selected_key=selected_key_value,
            reason_code_at_consume=reason_code_value,
            binding_digest_expected=binding_digest_value,
            contract_version=contract_version_value,
            endpoint_version=endpoint_version_value,
        )
        self._token_records[token_id_value] = record
        self._operation_to_token[operation_id_value] = token_id_value

        return {
            "ok": True,
            "state": STATE_CONSUMED,
            "token_consume_performed": True,
            "reason_code": REASON_CONSUMED,
            "errors": [],
            "token_id": token_id_value,
            "record": {
                "token_id": record.token_id,
                "consumed_at_utc": record.consumed_at_utc,
                "operation_id": record.operation_id,
                "write_attempt_id": record.write_attempt_id,
                "selected_key": record.selected_key,
                "reason_code_at_consume": record.reason_code_at_consume,
                "binding_digest_expected": record.binding_digest_expected,
                "contract_version": record.contract_version,
                "endpoint_version": record.endpoint_version,
            },
            "idempotent": False,
        }

    def lookup_by_operation(self, operation_id: object) -> dict:
        operation_id_value = _normalized_string(operation_id)
        if not operation_id_value:
            return {
                "ok": False,
                "state": STATE_NOT_CONSUMED,
                "reason_code": REASON_MALFORMED,
                "errors": ["operation_id is required"],
                "operation_id": None,
                "token_id": None,
                "record": None,
            }

        if not self._store_available:
            return {
                "ok": False,
                "state": STATE_CONSUME_REGISTER_FAILED,
                "reason_code": REASON_STORE_UNAVAILABLE,
                "errors": ["token consume store unavailable"],
                "operation_id": operation_id_value,
                "token_id": None,
                "record": None,
            }

        token_id = self._operation_to_token.get(operation_id_value)
        if not token_id:
            return {
                "ok": True,
                "state": STATE_NOT_CONSUMED,
                "reason_code": STATE_NOT_CONSUMED,
                "errors": [],
                "operation_id": operation_id_value,
                "token_id": None,
                "record": None,
            }

        return {
            "ok": True,
            "state": STATE_CONSUMED,
            "reason_code": REASON_CONSUMED,
            "errors": [],
            "operation_id": operation_id_value,
            "token_id": token_id,
            "record": self.lookup(token_id).get("record"),
        }


__all__ = [
    "OfficialSourceApprovedApplyTokenConsumeHelper",
    "STATE_NOT_CONSUMED",
    "STATE_CONSUMED",
    "STATE_CONSUME_REGISTER_FAILED",
    "REASON_CONSUMED",
    "REASON_CONFLICT",
    "REASON_STORE_UNAVAILABLE",
    "REASON_MALFORMED",
]
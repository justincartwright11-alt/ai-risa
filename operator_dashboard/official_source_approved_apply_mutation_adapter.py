from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_VALUE = "official_source_manual_approved"
WRITE_MODE_VALUE = "official_source_approved_apply"
APPROVAL_TYPE_VALUE = "explicit_operator_approval"
WRITE_TARGET_NAME = "actual_results_manual.json"


class _MutationLock:
    def __init__(self, path: Path, fd: int) -> None:
        self._path = path
        self._fd = fd
        self._released = False

    def release(self) -> None:
        if self._released:
            return
        self._released = True
        try:
            os.close(self._fd)
        except OSError:
            pass
        try:
            self._path.unlink()
        except OSError:
            pass


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _build_response(
    *,
    ok: bool,
    write_performed: bool,
    reason_code: str,
    errors: list[str],
    selected_key: str | None,
    fight_id: str | None,
    proposed_write: dict | None,
    write_target: str | None,
    before_row_count: int | None,
    after_row_count: int | None,
    pre_write_file_sha256: str | None,
    post_write_file_sha256: str | None,
    rollback_attempted: bool,
    rollback_succeeded: bool | None,
    post_rollback_file_sha256: str | None,
    rollback_reason_code: str | None,
    rollback_error_detail: str | None,
    rollback_started_at_utc: str | None,
    rollback_finished_at_utc: str | None,
    rollback_terminal_state: str | None,
    approval_token_id: str | None,
    operation_id: str,
    write_attempt_id: str,
    contract_version: str,
    endpoint_version: str,
    escalation_required: bool = False,
    operator_escalation_action: str | None = None,
) -> dict:
    return {
        "ok": bool(ok),
        "mutation_performed": bool(write_performed),
        "write_performed": bool(write_performed),
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "reason_code": reason_code,
        "errors": list(errors or []),
        "selected_key": selected_key,
        "fight_id": fight_id,
        "proposed_write": proposed_write,
        "write_target": write_target,
        "before_row_count": before_row_count,
        "after_row_count": after_row_count,
        "pre_write_file_sha256": pre_write_file_sha256,
        "post_write_file_sha256": post_write_file_sha256,
        "rollback_attempted": bool(rollback_attempted),
        "rollback_succeeded": rollback_succeeded,
        "post_rollback_file_sha256": post_rollback_file_sha256,
        "rollback_reason_code": rollback_reason_code,
        "rollback_error_detail": rollback_error_detail,
        "rollback_started_at_utc": rollback_started_at_utc,
        "rollback_finished_at_utc": rollback_finished_at_utc,
        "rollback_terminal_state": rollback_terminal_state,
        "escalation_required": bool(escalation_required),
        "operator_escalation_action": operator_escalation_action,
        "approval_token_id": approval_token_id,
        "token_consume_performed": False,
        "operation_id": operation_id,
        "write_attempt_id": write_attempt_id,
        "contract_version": contract_version,
        "endpoint_version": endpoint_version,
    }


def _acquire_mutation_lock(target_path: Path, timeout_seconds: int) -> dict:
    lock_path = target_path.with_name(f"{target_path.name}.lock")
    deadline = time.monotonic() + max(timeout_seconds, 0)

    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
            return {"ok": True, "lock": _MutationLock(lock_path, fd), "reason_code": None, "errors": []}
        except FileExistsError:
            if time.monotonic() >= deadline:
                return {
                    "ok": False,
                    "lock": None,
                    "reason_code": "contention_timeout",
                    "errors": ["mutation lock timed out"],
                }
            time.sleep(0.05)
        except OSError as exc:
            return {
                "ok": False,
                "lock": None,
                "reason_code": "mutation_lock_acquire_failed",
                "errors": [str(exc)],
            }


def _cleanup_path(path: Path | None) -> None:
    if path is None:
        return
    try:
        if path.exists():
            path.unlink()
    except OSError:
        pass


def _read_file_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _write_temp_file(target_path: Path, payload: bytes) -> Path:
    temp_handle = tempfile.NamedTemporaryFile(dir=target_path.parent, suffix=".tmp", delete=False)
    temp_path = Path(temp_handle.name)
    try:
        if os.stat(temp_path).st_dev != os.stat(target_path.parent).st_dev:
            raise OSError("cross_filesystem_write_error")
        temp_handle.write(payload)
        temp_handle.flush()
        os.fsync(temp_handle.fileno())
    finally:
        temp_handle.close()
    return temp_path


def _restore_previous_bytes(target_path: Path, original_bytes: bytes, expected_sha256: str) -> dict:
    rollback_started_at_utc = _now_utc_iso()
    rollback_temp_path: Path | None = None
    rollback_error_detail = None
    post_rollback_file_sha256 = None

    try:
        rollback_temp_path = _write_temp_file(target_path, original_bytes)
        os.replace(str(rollback_temp_path), str(target_path))
        rollback_temp_path = None
        restored_bytes = _read_file_bytes(target_path)
        post_rollback_file_sha256 = _sha256_bytes(restored_bytes)
        if post_rollback_file_sha256 != expected_sha256:
            return {
                "rollback_succeeded": False,
                "post_rollback_file_sha256": post_rollback_file_sha256,
                "rollback_reason_code": "rollback_failed_terminal",
                "rollback_error_detail": "restored file hash mismatch",
                "rollback_started_at_utc": rollback_started_at_utc,
                "rollback_finished_at_utc": _now_utc_iso(),
                "rollback_terminal_state": "rollback_failed_terminal",
            }
        return {
            "rollback_succeeded": True,
            "post_rollback_file_sha256": post_rollback_file_sha256,
            "rollback_reason_code": None,
            "rollback_error_detail": None,
            "rollback_started_at_utc": rollback_started_at_utc,
            "rollback_finished_at_utc": _now_utc_iso(),
            "rollback_terminal_state": None,
        }
    except Exception as exc:
        rollback_error_detail = str(exc)
        return {
            "rollback_succeeded": False,
            "post_rollback_file_sha256": post_rollback_file_sha256,
            "rollback_reason_code": "rollback_failed_terminal",
            "rollback_error_detail": rollback_error_detail,
            "rollback_started_at_utc": rollback_started_at_utc,
            "rollback_finished_at_utc": _now_utc_iso(),
            "rollback_terminal_state": "rollback_failed_terminal",
        }
    finally:
        _cleanup_path(rollback_temp_path)


def _normalize_match_key(value: Any) -> str:
    return _normalize_string(value).lower()


def _serialize_rows(rows: list[dict]) -> bytes:
    return (json.dumps(rows, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _atomic_write_single_record(target_path: Path, write_row: dict, lock_timeout_seconds: int) -> dict:
    lock_result = _acquire_mutation_lock(target_path, lock_timeout_seconds)
    if not lock_result.get("ok"):
        return {
            "ok": False,
            "reason_code": str(lock_result.get("reason_code") or "mutation_lock_acquire_failed"),
            "errors": list(lock_result.get("errors") or []),
            "write_target": str(target_path),
            "before_row_count": None,
            "after_row_count": None,
            "pre_write_file_sha256": None,
            "post_write_file_sha256": None,
            "rollback_attempted": False,
            "rollback_succeeded": None,
            "post_rollback_file_sha256": None,
            "rollback_reason_code": None,
            "rollback_error_detail": None,
            "rollback_started_at_utc": None,
            "rollback_finished_at_utc": None,
            "rollback_terminal_state": None,
        }

    lock = lock_result.get("lock")
    temp_path: Path | None = None
    original_bytes = b""
    pre_write_file_sha256 = None
    before_row_count = None

    try:
        try:
            original_bytes = _read_file_bytes(target_path)
        except Exception as exc:
            return {
                "ok": False,
                "reason_code": "pre_write_read_error",
                "errors": [str(exc)],
                "write_target": str(target_path),
                "before_row_count": None,
                "after_row_count": None,
                "pre_write_file_sha256": None,
                "post_write_file_sha256": None,
                "rollback_attempted": False,
                "rollback_succeeded": None,
                "post_rollback_file_sha256": None,
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": None,
                "rollback_finished_at_utc": None,
                "rollback_terminal_state": None,
            }

        pre_write_file_sha256 = _sha256_bytes(original_bytes)

        try:
            existing_rows = json.loads(original_bytes.decode("utf-8"))
            if not isinstance(existing_rows, list):
                raise ValueError("manual actual results must contain a JSON list")
        except Exception as exc:
            return {
                "ok": False,
                "reason_code": "pre_write_parse_error",
                "errors": [str(exc)],
                "write_target": str(target_path),
                "before_row_count": None,
                "after_row_count": None,
                "pre_write_file_sha256": pre_write_file_sha256,
                "post_write_file_sha256": None,
                "rollback_attempted": False,
                "rollback_succeeded": None,
                "post_rollback_file_sha256": None,
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": None,
                "rollback_finished_at_utc": None,
                "rollback_terminal_state": None,
            }

        before_row_count = len(existing_rows)
        candidate_rows = [dict(row) for row in existing_rows]
        match_key = _normalize_match_key(write_row.get("fight_id"))
        updated = False
        for index, row in enumerate(candidate_rows):
            if _normalize_match_key(row.get("fight_id")) == match_key:
                candidate_rows[index] = dict(write_row)
                updated = True
                break
        if not updated:
            candidate_rows.append(dict(write_row))

        try:
            candidate_bytes = _serialize_rows(candidate_rows)
        except Exception as exc:
            return {
                "ok": False,
                "reason_code": "candidate_serialization_error",
                "errors": [str(exc)],
                "write_target": str(target_path),
                "before_row_count": before_row_count,
                "after_row_count": None,
                "pre_write_file_sha256": pre_write_file_sha256,
                "post_write_file_sha256": None,
                "rollback_attempted": False,
                "rollback_succeeded": None,
                "post_rollback_file_sha256": None,
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": None,
                "rollback_finished_at_utc": None,
                "rollback_terminal_state": None,
            }

        try:
            temp_path = _write_temp_file(target_path, candidate_bytes)
        except Exception as exc:
            reason_code = "cross_filesystem_write_error" if str(exc) == "cross_filesystem_write_error" else "temp_write_error"
            return {
                "ok": False,
                "reason_code": reason_code,
                "errors": [str(exc)],
                "write_target": str(target_path),
                "before_row_count": before_row_count,
                "after_row_count": None,
                "pre_write_file_sha256": pre_write_file_sha256,
                "post_write_file_sha256": None,
                "rollback_attempted": False,
                "rollback_succeeded": None,
                "post_rollback_file_sha256": None,
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": None,
                "rollback_finished_at_utc": None,
                "rollback_terminal_state": None,
            }

        rollback_attempted = False
        try:
            os.replace(str(temp_path), str(target_path))
            temp_path = None
            written_bytes = _read_file_bytes(target_path)
            post_write_file_sha256 = _sha256_bytes(written_bytes)
            if post_write_file_sha256 != _sha256_bytes(candidate_bytes):
                rollback_attempted = True
                rollback_result = _restore_previous_bytes(target_path, original_bytes, pre_write_file_sha256)
                if not rollback_result.get("rollback_succeeded"):
                    return {
                        "ok": False,
                        "reason_code": "rollback_failed_terminal",
                        "errors": ["post-write verification failed and rollback did not restore original bytes"],
                        "write_target": str(target_path),
                        "before_row_count": before_row_count,
                        "after_row_count": None,
                        "pre_write_file_sha256": pre_write_file_sha256,
                        "post_write_file_sha256": post_write_file_sha256,
                        "rollback_attempted": True,
                        "rollback_succeeded": False,
                        "post_rollback_file_sha256": rollback_result.get("post_rollback_file_sha256"),
                        "rollback_reason_code": rollback_result.get("rollback_reason_code"),
                        "rollback_error_detail": rollback_result.get("rollback_error_detail"),
                        "rollback_started_at_utc": rollback_result.get("rollback_started_at_utc"),
                        "rollback_finished_at_utc": rollback_result.get("rollback_finished_at_utc"),
                        "rollback_terminal_state": rollback_result.get("rollback_terminal_state"),
                    }
                return {
                    "ok": False,
                    "reason_code": "post_write_hash_mismatch",
                    "errors": ["post-write file hash mismatch"],
                    "write_target": str(target_path),
                    "before_row_count": before_row_count,
                    "after_row_count": None,
                    "pre_write_file_sha256": pre_write_file_sha256,
                    "post_write_file_sha256": post_write_file_sha256,
                    "rollback_attempted": True,
                    "rollback_succeeded": True,
                    "post_rollback_file_sha256": rollback_result.get("post_rollback_file_sha256"),
                    "rollback_reason_code": None,
                    "rollback_error_detail": None,
                    "rollback_started_at_utc": rollback_result.get("rollback_started_at_utc"),
                    "rollback_finished_at_utc": rollback_result.get("rollback_finished_at_utc"),
                    "rollback_terminal_state": None,
                }

            return {
                "ok": True,
                "reason_code": "official_source_write_applied",
                "errors": [],
                "write_target": str(target_path),
                "before_row_count": before_row_count,
                "after_row_count": len(candidate_rows),
                "pre_write_file_sha256": pre_write_file_sha256,
                "post_write_file_sha256": post_write_file_sha256,
                "rollback_attempted": False,
                "rollback_succeeded": None,
                "post_rollback_file_sha256": None,
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": None,
                "rollback_finished_at_utc": None,
                "rollback_terminal_state": None,
            }
        except Exception as exc:
            rollback_attempted = True
            rollback_result = _restore_previous_bytes(target_path, original_bytes, pre_write_file_sha256)
            if not rollback_result.get("rollback_succeeded"):
                return {
                    "ok": False,
                    "reason_code": "rollback_failed_terminal",
                    "errors": [str(exc)],
                    "write_target": str(target_path),
                    "before_row_count": before_row_count,
                    "after_row_count": None,
                    "pre_write_file_sha256": pre_write_file_sha256,
                    "post_write_file_sha256": None,
                    "rollback_attempted": rollback_attempted,
                    "rollback_succeeded": False,
                    "post_rollback_file_sha256": rollback_result.get("post_rollback_file_sha256"),
                    "rollback_reason_code": rollback_result.get("rollback_reason_code"),
                    "rollback_error_detail": rollback_result.get("rollback_error_detail"),
                    "rollback_started_at_utc": rollback_result.get("rollback_started_at_utc"),
                    "rollback_finished_at_utc": rollback_result.get("rollback_finished_at_utc"),
                    "rollback_terminal_state": rollback_result.get("rollback_terminal_state"),
                }
            return {
                "ok": False,
                "reason_code": "atomic_replace_error",
                "errors": [str(exc)],
                "write_target": str(target_path),
                "before_row_count": before_row_count,
                "after_row_count": None,
                "pre_write_file_sha256": pre_write_file_sha256,
                "post_write_file_sha256": None,
                "rollback_attempted": rollback_attempted,
                "rollback_succeeded": True,
                "post_rollback_file_sha256": rollback_result.get("post_rollback_file_sha256"),
                "rollback_reason_code": None,
                "rollback_error_detail": None,
                "rollback_started_at_utc": rollback_result.get("rollback_started_at_utc"),
                "rollback_finished_at_utc": rollback_result.get("rollback_finished_at_utc"),
                "rollback_terminal_state": None,
            }
    finally:
        _cleanup_path(temp_path)
        if lock is not None:
            lock.release()


def _build_proposed_write(
    *,
    guard_result: dict,
    preview_snapshot: dict,
    operation_id: str,
    write_attempt_id: str,
    contract_version: str,
    endpoint_version: str,
) -> tuple[dict | None, list[str]]:
    source_citation = preview_snapshot.get("source_citation") or {}
    audit = preview_snapshot.get("audit") or {}

    proposed_write = {
        "fight_id": _normalize_string(audit.get("record_fight_id")),
        "fight_name": _normalize_string(audit.get("fight_name")),
        "actual_winner": _normalize_string(source_citation.get("extracted_winner")),
        "actual_method": _normalize_string(source_citation.get("extracted_method")) or "UNKNOWN",
        "actual_round": _normalize_string(source_citation.get("extracted_round")) or "UNKNOWN",
        "event_date": _normalize_string(source_citation.get("source_date")),
        "event_name": _normalize_string(source_citation.get("source_title")) or _normalize_string(audit.get("event_name")) or "UNKNOWN",
        "source": SOURCE_VALUE,
        "source_url": _normalize_string(source_citation.get("source_url")),
        "source_title": _normalize_string(source_citation.get("source_title")),
        "source_date": _normalize_string(source_citation.get("source_date")),
        "publisher_host": _normalize_string(source_citation.get("publisher_host")),
        "source_confidence": _normalize_string(source_citation.get("source_confidence")),
        "confidence_score": source_citation.get("confidence_score"),
        "citation_fingerprint": _normalize_string(source_citation.get("citation_fingerprint")),
        "selected_key": _normalize_string(guard_result.get("selected_key")),
        "write_mode": WRITE_MODE_VALUE,
        "approval_type": APPROVAL_TYPE_VALUE,
        "approval_token_id": _normalize_string(guard_result.get("token_id")),
        "operation_id": _normalize_string(operation_id),
        "write_attempt_id": _normalize_string(write_attempt_id),
        "contract_version": _normalize_string(contract_version),
        "endpoint_version": _normalize_string(endpoint_version),
        "approved_at_utc": _now_utc_iso(),
        "binding_digest": _normalize_string(guard_result.get("binding_digest_expected")),
    }

    missing_fields: list[str] = []
    required_fields = [
        "fight_id",
        "fight_name",
        "actual_winner",
        "event_date",
        "source_url",
        "source_title",
        "source_date",
        "publisher_host",
        "source_confidence",
        "citation_fingerprint",
        "selected_key",
        "approval_token_id",
        "operation_id",
        "write_attempt_id",
        "contract_version",
        "endpoint_version",
        "binding_digest",
    ]
    strict_non_unknown_fields = {
        "fight_id",
        "actual_winner",
        "citation_fingerprint",
        "source_url",
        "source_date",
        "selected_key",
        "approval_token_id",
    }

    for field_name in required_fields:
        raw_value = proposed_write.get(field_name)
        normalized = _normalize_string(raw_value)
        if not normalized:
            missing_fields.append(field_name)
            continue
        if field_name in strict_non_unknown_fields and normalized.upper() == "UNKNOWN":
            missing_fields.append(field_name)

    confidence_value = proposed_write.get("confidence_score")
    if confidence_value is None or _normalize_string(confidence_value) == "" or _normalize_string(confidence_value).upper() == "UNKNOWN":
        missing_fields.append("confidence_score")

    if missing_fields:
        return None, missing_fields
    return proposed_write, []


def apply_official_source_approved_apply_mutation(
    *,
    guard_result: dict,
    preview_snapshot: dict,
    accuracy_dir: Path,
    consumed_token_ids: set,
    lock_timeout_seconds: int = 10,
    operation_id: str,
    write_attempt_id: str,
    contract_version: str,
    endpoint_version: str,
) -> dict:
    del consumed_token_ids

    selected_key = _normalize_string(guard_result.get("selected_key")) or None
    approval_token_id = _normalize_string(guard_result.get("token_id")) or None
    write_target = str(accuracy_dir / WRITE_TARGET_NAME)

    precondition_checks = [
        (bool(guard_result.get("guard_allowed")), "precondition_guard_not_allowed", ["guard_result.guard_allowed must be true"]),
        (str(guard_result.get("reason_code") or "") == "accepted_preview_write_eligible", "precondition_wrong_reason_code", ["guard_result.reason_code must be accepted_preview_write_eligible"]),
        (bool(guard_result.get("token_valid")), "precondition_token_not_valid", ["guard_result.token_valid must be true"]),
        (bool(guard_result.get("approval_binding_valid")), "precondition_binding_not_valid", ["guard_result.approval_binding_valid must be true"]),
        (not bool(guard_result.get("manual_review_required")), "precondition_manual_review_required", ["guard_result.manual_review_required must be false"]),
        (bool(approval_token_id), "precondition_token_id_missing", ["guard_result.token_id is required"]),
        (isinstance(preview_snapshot, dict), "precondition_preview_snapshot_invalid", ["preview_snapshot must be an object"]),
        (
            isinstance(guard_result.get("acceptance_gate"), dict)
            and str((guard_result.get("acceptance_gate") or {}).get("state") or "") == "write_eligible"
            and bool((guard_result.get("acceptance_gate") or {}).get("write_eligible")) is True,
            "precondition_gate_not_write_eligible",
            ["acceptance gate must remain write_eligible"],
        ),
        (accuracy_dir.is_dir(), "precondition_accuracy_dir_missing", ["accuracy_dir must exist"]),
    ]

    for passed, reason_code, errors in precondition_checks:
        if not passed:
            return _build_response(
                ok=False,
                write_performed=False,
                reason_code=reason_code,
                errors=errors,
                selected_key=selected_key,
                fight_id=None,
                proposed_write=None,
                write_target=write_target,
                before_row_count=None,
                after_row_count=None,
                pre_write_file_sha256=None,
                post_write_file_sha256=None,
                rollback_attempted=False,
                rollback_succeeded=None,
                post_rollback_file_sha256=None,
                rollback_reason_code=None,
                rollback_error_detail=None,
                rollback_started_at_utc=None,
                rollback_finished_at_utc=None,
                rollback_terminal_state=None,
                approval_token_id=approval_token_id,
                operation_id=operation_id,
                write_attempt_id=write_attempt_id,
                contract_version=contract_version,
                endpoint_version=endpoint_version,
            )

    target_path = accuracy_dir / WRITE_TARGET_NAME
    proposed_write, missing_fields = _build_proposed_write(
        guard_result=guard_result,
        preview_snapshot=preview_snapshot,
        operation_id=operation_id,
        write_attempt_id=write_attempt_id,
        contract_version=contract_version,
        endpoint_version=endpoint_version,
    )
    if proposed_write is None:
        return _build_response(
            ok=False,
            write_performed=False,
            reason_code="critical_field_missing",
            errors=[f"missing required field: {field_name}" for field_name in missing_fields],
            selected_key=selected_key,
            fight_id=None,
            proposed_write=None,
            write_target=str(target_path),
            before_row_count=None,
            after_row_count=None,
            pre_write_file_sha256=None,
            post_write_file_sha256=None,
            rollback_attempted=False,
            rollback_succeeded=None,
            post_rollback_file_sha256=None,
            rollback_reason_code=None,
            rollback_error_detail=None,
            rollback_started_at_utc=None,
            rollback_finished_at_utc=None,
            rollback_terminal_state=None,
            approval_token_id=approval_token_id,
            operation_id=operation_id,
            write_attempt_id=write_attempt_id,
            contract_version=contract_version,
            endpoint_version=endpoint_version,
        )

    write_result = _atomic_write_single_record(target_path, proposed_write, lock_timeout_seconds)
    rollback_terminal_state = write_result.get("rollback_terminal_state")
    return _build_response(
        ok=bool(write_result.get("ok")),
        write_performed=bool(write_result.get("ok")),
        reason_code=str(write_result.get("reason_code") or "internal_apply_error"),
        errors=list(write_result.get("errors") or []),
        selected_key=selected_key,
        fight_id=_normalize_string(proposed_write.get("fight_id")) or None,
        proposed_write=proposed_write,
        write_target=write_result.get("write_target"),
        before_row_count=write_result.get("before_row_count"),
        after_row_count=write_result.get("after_row_count"),
        pre_write_file_sha256=write_result.get("pre_write_file_sha256"),
        post_write_file_sha256=write_result.get("post_write_file_sha256"),
        rollback_attempted=bool(write_result.get("rollback_attempted")),
        rollback_succeeded=write_result.get("rollback_succeeded"),
        post_rollback_file_sha256=write_result.get("post_rollback_file_sha256"),
        rollback_reason_code=write_result.get("rollback_reason_code"),
        rollback_error_detail=write_result.get("rollback_error_detail"),
        rollback_started_at_utc=write_result.get("rollback_started_at_utc"),
        rollback_finished_at_utc=write_result.get("rollback_finished_at_utc"),
        rollback_terminal_state=rollback_terminal_state,
        approval_token_id=approval_token_id,
        operation_id=operation_id,
        write_attempt_id=write_attempt_id,
        contract_version=contract_version,
        endpoint_version=endpoint_version,
        escalation_required=rollback_terminal_state == "rollback_failed_terminal",
        operator_escalation_action="manual_file_recovery_required" if rollback_terminal_state == "rollback_failed_terminal" else None,
    )


__all__ = ["apply_official_source_approved_apply_mutation"]
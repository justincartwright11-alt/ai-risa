from __future__ import annotations

import re
from typing import Any


MODE_VALUE = "official_source_approved_apply"
PHASE_VALUE = "approved_apply"
LOOKUP_INTENT_VALUE = "apply_write"

_BATCH_FORBIDDEN_FIELDS = {
    "selected_keys",
    "targets",
    "batch_size",
    "execution_token",
    "apply_all",
    "queue_wide",
    "queue_scope",
}

_MUTATION_OVERRIDE_FORBIDDEN_FIELDS = {
    "force_write",
    "skip_validation",
    "bypass_gate",
    "bypass_approval",
    "write_target_override",
    "scoring_override",
}

_APPROVAL_BINDING_REQUIRED_STR_FIELDS = (
    "selected_key",
    "citation_fingerprint",
    "source_url",
    "source_date",
    "extracted_winner",
)

_PREVIEW_SOURCE_CITATION_REQUIRED_FIELDS = (
    "source_url",
    "source_title",
    "source_date",
    "publisher_host",
    "source_confidence",
    "confidence_score",
    "citation_fingerprint",
    "extracted_winner",
)

_PREVIEW_ACCEPTANCE_GATE_REQUIRED_FIELDS = (
    "state",
    "write_eligible",
    "reason_code",
    "selected_key",
    "citation_fingerprint",
)

_PREVIEW_AUDIT_REQUIRED_FIELDS = (
    "record_fight_id",
    "provider_attempted",
    "attempted_sources",
)

_OPERATION_ID_ALLOWED_RE = re.compile(r"^[A-Za-z0-9_.-]{16,128}$")
_OPERATION_ID_HAS_ALNUM_RE = re.compile(r"[A-Za-z0-9]")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def build_official_source_approved_apply_schema_response(
    *,
    request_valid: bool,
    reason_code: str,
    errors: list,
    selected_key: str | None = None,
    approval_granted: bool = False,
    operation_id: str | None = None,
) -> dict:
    return {
        "ok": bool(request_valid),
        "mode": MODE_VALUE,
        "phase": PHASE_VALUE,
        "mutation_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "write_performed": False,
        "request_valid": bool(request_valid),
        "reason_code": str(reason_code or "invalid_request_body"),
        "errors": list(errors or []),
        "selected_key": selected_key,
        "operation_id": operation_id,
        "approval_required": True,
        "approval_granted": bool(approval_granted),
        "manual_review_required": not bool(request_valid),
    }


def _invalid(
    reason_code: str,
    error: str,
    *,
    selected_key: str | None = None,
    approval_granted: bool = False,
    operation_id: str | None = None,
) -> dict:
    return build_official_source_approved_apply_schema_response(
        request_valid=False,
        reason_code=reason_code,
        errors=[error],
        selected_key=selected_key,
        approval_granted=approval_granted,
        operation_id=operation_id,
    )


def _require_object(container: dict, field_name: str, missing_reason: str, type_reason: str) -> tuple[dict | None, dict | None]:
    if field_name not in container:
        return None, _invalid(missing_reason, f"{field_name} is required")

    value = container.get(field_name)
    if not isinstance(value, dict):
        return None, _invalid(type_reason, f"{field_name} must be an object")

    return value, None


def validate_official_source_approved_apply_request(payload: object) -> dict:
    if not isinstance(payload, dict):
        return _invalid("invalid_request_body", "request payload must be an object")

    approval_granted = payload.get("approval_granted") is True
    selected_key_raw = payload.get("selected_key")
    selected_key = selected_key_raw.strip() if isinstance(selected_key_raw, str) else None
    operation_id_raw = payload.get("operation_id")
    operation_id = operation_id_raw.strip() if isinstance(operation_id_raw, str) else None

    if "operation_id" in payload:
        if not isinstance(operation_id_raw, str):
            return _invalid(
                "malformed_field_type",
                "operation_id must be a string",
                selected_key=selected_key,
                approval_granted=approval_granted,
            )

        if (
            not operation_id
            or not _OPERATION_ID_ALLOWED_RE.fullmatch(operation_id)
            or " " in operation_id
            or "/" in operation_id
            or "\\" in operation_id
            or not _OPERATION_ID_HAS_ALNUM_RE.search(operation_id)
        ):
            return _invalid(
                "operation_id_format_invalid",
                "operation_id must be 16..128 chars using only letters, digits, underscore, hyphen, or period",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    for field in _BATCH_FORBIDDEN_FIELDS:
        if field in payload:
            return _invalid(
                "batch_field_not_allowed",
                f"{field} is not allowed for one-record apply schema",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    for field in _MUTATION_OVERRIDE_FORBIDDEN_FIELDS:
        if field in payload:
            return _invalid(
                "mutation_override_not_allowed",
                f"{field} is not allowed for schema-only apply validation",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    mode = payload.get("mode")
    if mode != MODE_VALUE:
        return _invalid(
            "invalid_apply_mode",
            f"mode must be {MODE_VALUE}",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    lookup_intent = payload.get("lookup_intent")
    if lookup_intent != LOOKUP_INTENT_VALUE:
        return _invalid(
            "invalid_lookup_intent",
            f"lookup_intent must be {LOOKUP_INTENT_VALUE}",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if isinstance(selected_key_raw, (list, tuple, set)):
        return _invalid(
            "single_record_required",
            "selected_key must contain exactly one record key",
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not isinstance(selected_key_raw, str):
        return _invalid(
            "selected_key_type_invalid",
            "selected_key must be a string",
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not selected_key:
        return _invalid(
            "selected_key_required",
            "selected_key is required",
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if payload.get("approval_granted") is not True:
        return _invalid(
            "approval_granted_required_true",
            "approval_granted must be true",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    approval_token = payload.get("approval_token")
    if not _is_non_empty_string(approval_token):
        return _invalid(
            "approval_token_missing",
            "approval_token is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    approval_binding, err = _require_object(
        payload,
        "approval_binding",
        "approval_binding_missing",
        "approval_binding_type_invalid",
    )
    if err:
        err["selected_key"] = selected_key
        err["approval_granted"] = approval_granted
        err["operation_id"] = operation_id
        return err

    for field in _APPROVAL_BINDING_REQUIRED_STR_FIELDS:
        if not _is_non_empty_string(approval_binding.get(field)):
            return _invalid(
                "approval_binding_field_missing",
                f"approval_binding.{field} is required",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    selected_row_identity = approval_binding.get("selected_row_identity")
    if not isinstance(selected_row_identity, dict):
        return _invalid(
            "malformed_field_type",
            "approval_binding.selected_row_identity must be an object",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not _is_non_empty_string(selected_row_identity.get("fight_name")):
        return _invalid(
            "approval_binding_field_missing",
            "approval_binding.selected_row_identity.fight_name is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if "fight_id" in selected_row_identity and selected_row_identity.get("fight_id") is not None and not isinstance(selected_row_identity.get("fight_id"), str):
        return _invalid(
            "malformed_field_type",
            "approval_binding.selected_row_identity.fight_id must be a string or null",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if "record_fight_id" in approval_binding and approval_binding.get("record_fight_id") is not None and not isinstance(approval_binding.get("record_fight_id"), str):
        return _invalid(
            "malformed_field_type",
            "approval_binding.record_fight_id must be a string or null",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    preview_snapshot, err = _require_object(
        payload,
        "preview_snapshot",
        "preview_snapshot_missing",
        "preview_snapshot_type_invalid",
    )
    if err:
        err["selected_key"] = selected_key
        err["approval_granted"] = approval_granted
        err["operation_id"] = operation_id
        return err

    if not _is_non_empty_string(preview_snapshot.get("selected_key")):
        return _invalid(
            "preview_snapshot_field_missing",
            "preview_snapshot.selected_key is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not isinstance(preview_snapshot.get("manual_review_required"), bool):
        return _invalid(
            "malformed_field_type",
            "preview_snapshot.manual_review_required must be a boolean",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    source_citation = preview_snapshot.get("source_citation")
    if not isinstance(source_citation, dict):
        return _invalid(
            "preview_snapshot_field_missing",
            "preview_snapshot.source_citation is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    for field in _PREVIEW_SOURCE_CITATION_REQUIRED_FIELDS:
        value = source_citation.get(field)
        if field == "confidence_score":
            if not isinstance(value, (int, float)):
                return _invalid(
                    "malformed_field_type",
                    "preview_snapshot.source_citation.confidence_score must be numeric",
                    selected_key=selected_key,
                    approval_granted=approval_granted,
                    operation_id=operation_id,
                )
        elif not _is_non_empty_string(value):
            return _invalid(
                "preview_snapshot_field_missing",
                f"preview_snapshot.source_citation.{field} is required",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    acceptance_gate = preview_snapshot.get("acceptance_gate")
    if not isinstance(acceptance_gate, dict):
        return _invalid(
            "preview_snapshot_field_missing",
            "preview_snapshot.acceptance_gate is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    for field in _PREVIEW_ACCEPTANCE_GATE_REQUIRED_FIELDS:
        value = acceptance_gate.get(field)
        if field == "write_eligible":
            if not isinstance(value, bool):
                return _invalid(
                    "malformed_field_type",
                    "preview_snapshot.acceptance_gate.write_eligible must be a boolean",
                    selected_key=selected_key,
                    approval_granted=approval_granted,
                    operation_id=operation_id,
                )
        elif not _is_non_empty_string(value):
            return _invalid(
                "preview_snapshot_field_missing",
                f"preview_snapshot.acceptance_gate.{field} is required",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    audit = preview_snapshot.get("audit")
    if not isinstance(audit, dict):
        return _invalid(
            "preview_snapshot_field_missing",
            "preview_snapshot.audit is required",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    for field in _PREVIEW_AUDIT_REQUIRED_FIELDS:
        if field not in audit:
            return _invalid(
                "preview_snapshot_field_missing",
                f"preview_snapshot.audit.{field} is required",
                selected_key=selected_key,
                approval_granted=approval_granted,
                operation_id=operation_id,
            )

    if audit.get("record_fight_id") is not None and not isinstance(audit.get("record_fight_id"), str):
        return _invalid(
            "malformed_field_type",
            "preview_snapshot.audit.record_fight_id must be a string or null",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not isinstance(audit.get("provider_attempted"), bool):
        return _invalid(
            "malformed_field_type",
            "preview_snapshot.audit.provider_attempted must be a boolean",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    if not isinstance(audit.get("attempted_sources"), list):
        return _invalid(
            "malformed_field_type",
            "preview_snapshot.audit.attempted_sources must be a list",
            selected_key=selected_key,
            approval_granted=approval_granted,
            operation_id=operation_id,
        )

    return build_official_source_approved_apply_schema_response(
        request_valid=True,
        reason_code="valid_schema",
        errors=[],
        selected_key=selected_key,
        approval_granted=True,
        operation_id=operation_id,
    )


__all__ = [
    "build_official_source_approved_apply_schema_response",
    "validate_official_source_approved_apply_request",
]

from __future__ import annotations

from typing import Any

from operator_dashboard.official_source_acceptance_gate import evaluate_official_source_acceptance_gate
from operator_dashboard.official_source_approved_apply_schema import validate_official_source_approved_apply_request
from operator_dashboard.official_source_approved_apply_token import validate_official_source_approved_apply_token


MODE_VALUE = "official_source_approved_apply"
PHASE_VALUE = "approved_apply"


def _build_guard_response(
    *,
    guard_allowed: bool,
    reason_code: str,
    errors: list[str],
    approval_granted: bool,
    request_valid: bool,
    token_valid: bool,
    token_status: str,
    approval_binding_valid: bool,
    selected_key: str | None,
    acceptance_gate: dict | None,
    binding_digest_expected: str | None,
    binding_digest_actual: str | None,
    manual_review_required: bool,
) -> dict:
    return {
        "ok": bool(guard_allowed),
        "mode": MODE_VALUE,
        "phase": PHASE_VALUE,
        "mutation_performed": False,
        "write_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "approval_required": True,
        "approval_granted": bool(approval_granted),
        "request_valid": bool(request_valid),
        "token_valid": bool(token_valid),
        "token_status": token_status,
        "approval_binding_valid": bool(approval_binding_valid),
        "guard_allowed": bool(guard_allowed),
        "manual_review_required": bool(manual_review_required),
        "reason_code": reason_code,
        "errors": list(errors or []),
        "selected_key": selected_key,
        "acceptance_gate": acceptance_gate,
        "binding_digest_expected": binding_digest_expected,
        "binding_digest_actual": binding_digest_actual,
    }


def _as_stripped_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _as_nullable_stripped_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return ""


def _extract_binding_mismatch(payload: dict) -> tuple[str | None, str | None]:
    selected_key = _as_stripped_string(payload.get("selected_key"))
    approval_binding = payload.get("approval_binding") or {}
    preview_snapshot = payload.get("preview_snapshot") or {}
    source_citation = preview_snapshot.get("source_citation") or {}
    acceptance_gate = preview_snapshot.get("acceptance_gate") or {}
    audit = preview_snapshot.get("audit") or {}

    binding_selected_key = _as_stripped_string(approval_binding.get("selected_key"))
    snapshot_selected_key = _as_stripped_string(preview_snapshot.get("selected_key"))
    gate_selected_key = _as_stripped_string(acceptance_gate.get("selected_key"))

    if selected_key != binding_selected_key or selected_key != snapshot_selected_key or (gate_selected_key and selected_key != gate_selected_key):
        return "selected_key_binding_mismatch", "selected_key binding mismatch"

    binding_citation_fp = _as_stripped_string(approval_binding.get("citation_fingerprint"))
    snapshot_citation_fp = _as_stripped_string(source_citation.get("citation_fingerprint"))
    gate_citation_fp = _as_stripped_string(acceptance_gate.get("citation_fingerprint"))
    if binding_citation_fp != snapshot_citation_fp or (gate_citation_fp and binding_citation_fp != gate_citation_fp):
        return "citation_binding_mismatch", "citation_fingerprint binding mismatch"

    binding_source_url = _as_stripped_string(approval_binding.get("source_url"))
    snapshot_source_url = _as_stripped_string(source_citation.get("source_url"))
    if binding_source_url != snapshot_source_url:
        return "source_url_binding_mismatch", "source_url binding mismatch"

    binding_source_date = _as_stripped_string(approval_binding.get("source_date"))
    snapshot_source_date = _as_stripped_string(source_citation.get("source_date"))
    if binding_source_date != snapshot_source_date:
        return "source_date_binding_mismatch", "source_date binding mismatch"

    binding_winner = _as_stripped_string(approval_binding.get("extracted_winner"))
    snapshot_winner = _as_stripped_string(source_citation.get("extracted_winner"))
    if binding_winner != snapshot_winner:
        return "extracted_winner_binding_mismatch", "extracted_winner binding mismatch"

    binding_record_fight_id = _as_nullable_stripped_string(approval_binding.get("record_fight_id"))
    snapshot_record_fight_id = _as_nullable_stripped_string(audit.get("record_fight_id"))
    if binding_record_fight_id and snapshot_record_fight_id and binding_record_fight_id != snapshot_record_fight_id:
        return "record_identity_binding_mismatch", "record_fight_id binding mismatch"

    return None, None


def _preview_matches_authoritative(payload_preview: dict, authoritative_preview_result: dict) -> bool:
    if not isinstance(authoritative_preview_result, dict):
        return False

    payload_source_citation = payload_preview.get("source_citation") or {}
    auth_source_citation = authoritative_preview_result.get("source_citation") or {}

    payload_audit = payload_preview.get("audit") or {}
    auth_audit = authoritative_preview_result.get("audit") or {}

    payload_acceptance_gate = payload_preview.get("acceptance_gate") or {}
    auth_acceptance_gate = authoritative_preview_result.get("acceptance_gate") or {}

    checks = [
        (_as_stripped_string(payload_preview.get("selected_key")), _as_stripped_string(authoritative_preview_result.get("selected_key"))),
        (_as_stripped_string(payload_source_citation.get("citation_fingerprint")), _as_stripped_string(auth_source_citation.get("citation_fingerprint"))),
        (_as_stripped_string(payload_source_citation.get("source_url")), _as_stripped_string(auth_source_citation.get("source_url"))),
        (_as_stripped_string(payload_source_citation.get("source_date")), _as_stripped_string(auth_source_citation.get("source_date"))),
        (_as_stripped_string(payload_source_citation.get("extracted_winner")), _as_stripped_string(auth_source_citation.get("extracted_winner"))),
        (_as_nullable_stripped_string(payload_audit.get("record_fight_id")), _as_nullable_stripped_string(auth_audit.get("record_fight_id"))),
        (_as_stripped_string(payload_acceptance_gate.get("selected_key")), _as_stripped_string(auth_acceptance_gate.get("selected_key"))),
        (_as_stripped_string(payload_acceptance_gate.get("citation_fingerprint")), _as_stripped_string(auth_acceptance_gate.get("citation_fingerprint"))),
    ]

    return all(left == right for left, right in checks)


def evaluate_official_source_approved_apply_guard(
    request_payload: object,
    *,
    authoritative_preview_result: dict | None,
    now_epoch: int,
    consumed_token_ids: set | None = None,
    replayed_token_ids: set | None = None,
    allowed_clock_skew_seconds: int = 5,
) -> dict:
    try:
        schema_result = validate_official_source_approved_apply_request(request_payload)

        request_valid = bool(schema_result.get("request_valid"))
        approval_granted = bool(schema_result.get("approval_granted"))
        selected_key = schema_result.get("selected_key")

        if not request_valid:
            return _build_guard_response(
                guard_allowed=False,
                reason_code=str(schema_result.get("reason_code") or "invalid_request_body"),
                errors=list(schema_result.get("errors") or []),
                approval_granted=approval_granted,
                request_valid=False,
                token_valid=False,
                token_status="not_evaluated",
                approval_binding_valid=False,
                selected_key=selected_key,
                acceptance_gate=None,
                binding_digest_expected=None,
                binding_digest_actual=None,
                manual_review_required=True,
            )

        payload = request_payload if isinstance(request_payload, dict) else {}

        token_result = validate_official_source_approved_apply_token(
            payload.get("approval_token"),
            payload.get("approval_binding") or {},
            now_epoch=now_epoch,
            consumed_token_ids=consumed_token_ids,
            replayed_token_ids=replayed_token_ids,
            allowed_clock_skew_seconds=allowed_clock_skew_seconds,
            approval_granted=bool(payload.get("approval_granted")),
        )

        if not bool(token_result.get("token_valid")):
            return _build_guard_response(
                guard_allowed=False,
                reason_code=str(token_result.get("reason_code") or "approval_missing"),
                errors=list(token_result.get("errors") or []),
                approval_granted=bool(token_result.get("approval_granted")),
                request_valid=True,
                token_valid=False,
                token_status=str(token_result.get("token_status") or "missing"),
                approval_binding_valid=False,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=None,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        binding_mismatch_code, binding_mismatch_error = _extract_binding_mismatch(payload)
        if binding_mismatch_code:
            return _build_guard_response(
                guard_allowed=False,
                reason_code=binding_mismatch_code,
                errors=[binding_mismatch_error or "binding mismatch"],
                approval_granted=True,
                request_valid=True,
                token_valid=True,
                token_status=str(token_result.get("token_status") or "valid"),
                approval_binding_valid=False,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=None,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        payload_preview = payload.get("preview_snapshot") if isinstance(payload, dict) else None
        if not isinstance(payload_preview, dict) or not isinstance(authoritative_preview_result, dict):
            return _build_guard_response(
                guard_allowed=False,
                reason_code="preview_snapshot_mismatch",
                errors=["preview snapshot does not match authoritative preview result"],
                approval_granted=True,
                request_valid=True,
                token_valid=True,
                token_status=str(token_result.get("token_status") or "valid"),
                approval_binding_valid=True,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=None,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        if not _preview_matches_authoritative(payload_preview, authoritative_preview_result):
            return _build_guard_response(
                guard_allowed=False,
                reason_code="preview_snapshot_mismatch",
                errors=["request preview_snapshot mismatches authoritative preview result"],
                approval_granted=True,
                request_valid=True,
                token_valid=True,
                token_status=str(token_result.get("token_status") or "valid"),
                approval_binding_valid=True,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=None,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        acceptance_gate = evaluate_official_source_acceptance_gate(authoritative_preview_result)
        gate_state = str(acceptance_gate.get("state") or "")
        gate_write_eligible = bool(acceptance_gate.get("write_eligible"))

        if gate_state not in {"manual_review", "rejected"} and gate_write_eligible is not True:
            return _build_guard_response(
                guard_allowed=False,
                reason_code="acceptance_gate_not_write_eligible",
                errors=["acceptance gate is not write_eligible"],
                approval_granted=True,
                request_valid=True,
                token_valid=True,
                token_status=str(token_result.get("token_status") or "valid"),
                approval_binding_valid=True,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=acceptance_gate,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        if gate_state in {"manual_review", "rejected"}:
            return _build_guard_response(
                guard_allowed=False,
                reason_code=str(acceptance_gate.get("reason_code") or "acceptance_gate_not_write_eligible"),
                errors=[f"acceptance gate state is {gate_state}"],
                approval_granted=True,
                request_valid=True,
                token_valid=True,
                token_status=str(token_result.get("token_status") or "valid"),
                approval_binding_valid=True,
                selected_key=schema_result.get("selected_key"),
                acceptance_gate=acceptance_gate,
                binding_digest_expected=token_result.get("binding_digest_expected"),
                binding_digest_actual=token_result.get("binding_digest_actual"),
                manual_review_required=True,
            )

        return _build_guard_response(
            guard_allowed=True,
            reason_code="accepted_preview_write_eligible",
            errors=[],
            approval_granted=True,
            request_valid=True,
            token_valid=True,
            token_status=str(token_result.get("token_status") or "valid"),
            approval_binding_valid=True,
            selected_key=schema_result.get("selected_key"),
            acceptance_gate=acceptance_gate,
            binding_digest_expected=token_result.get("binding_digest_expected"),
            binding_digest_actual=token_result.get("binding_digest_actual"),
            manual_review_required=False,
        )
    except Exception as exc:
        return _build_guard_response(
            guard_allowed=False,
            reason_code="internal_apply_error",
            errors=[str(exc)],
            approval_granted=False,
            request_valid=False,
            token_valid=False,
            token_status="not_evaluated",
            approval_binding_valid=False,
            selected_key=None,
            acceptance_gate=None,
            binding_digest_expected=None,
            binding_digest_actual=None,
            manual_review_required=True,
        )


__all__ = ["evaluate_official_source_approved_apply_guard"]

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any


MODE_VALUE = "official_source_approved_apply"
PHASE_VALUE = "approved_apply"
TOKEN_PREFIX = "osat1"
MAX_TTL_SECONDS = 300

_REASON_VALID_TOKEN = "valid_token"
_REASON_APPROVAL_REQUIRED = "approval_required"
_REASON_APPROVAL_MISSING = "approval_missing"
_REASON_MALFORMED = "malformed_field_type"
_REASON_EXPIRED = "approval_expired"
_REASON_FUTURE_ISSUED = "approval_future_issued"
_REASON_REPLAYED = "approval_replayed"
_REASON_CONSUMED = "approval_token_consumed"
_REASON_BINDING_MISMATCH = "approval_binding_mismatch"

_REQUIRED_BINDING_FIELDS = (
    "selected_key",
    "citation_fingerprint",
    "source_url",
    "source_date",
    "extracted_winner",
)

_TOKEN_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_required_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _normalize_nullable_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return ""


def _build_validation_response(
    *,
    token_valid: bool,
    token_status: str,
    reason_code: str,
    errors: list[str],
    approval_granted: bool,
    selected_key: str | None,
    binding_digest_expected: str | None,
    binding_digest_actual: str | None,
    issued_at_epoch: int | None,
    expires_at_epoch: int | None,
    now_epoch: int,
) -> dict:
    return {
        "ok": bool(token_valid),
        "mode": MODE_VALUE,
        "phase": PHASE_VALUE,
        "mutation_performed": False,
        "bulk_lookup_performed": False,
        "scoring_semantics_changed": False,
        "write_performed": False,
        "approval_required": True,
        "approval_granted": bool(approval_granted),
        "token_valid": bool(token_valid),
        "token_status": token_status,
        "reason_code": reason_code,
        "errors": list(errors or []),
        "selected_key": selected_key,
        "binding_digest_expected": binding_digest_expected,
        "binding_digest_actual": binding_digest_actual,
        "issued_at_epoch": issued_at_epoch,
        "expires_at_epoch": expires_at_epoch,
        "now_epoch": now_epoch,
    }


def _coerce_epoch(value: Any) -> tuple[int | None, str | None]:
    if isinstance(value, bool):
        return None, "epoch value must be an integer"
    if isinstance(value, int):
        return value, None
    return None, "epoch value must be an integer"


def build_official_source_approved_apply_binding_digest(binding: dict) -> dict:
    if not isinstance(binding, dict):
        return {
            "ok": False,
            "binding_digest": None,
            "binding_fields": None,
            "errors": ["binding must be an object"],
        }

    errors: list[str] = []

    binding_fields = {
        "selected_key": _normalize_required_string(binding.get("selected_key")),
        "citation_fingerprint": _normalize_required_string(binding.get("citation_fingerprint")),
        "source_url": _normalize_required_string(binding.get("source_url")),
        "source_date": _normalize_required_string(binding.get("source_date")),
        "extracted_winner": _normalize_required_string(binding.get("extracted_winner")),
        "record_fight_id": _normalize_nullable_string(binding.get("record_fight_id")),
        "selected_row_identity": {
            "fight_name": "",
            "fight_id": "",
        },
    }

    for field in _REQUIRED_BINDING_FIELDS:
        if not binding_fields[field]:
            errors.append(f"binding.{field} is required")

    selected_row_identity = binding.get("selected_row_identity")
    if not isinstance(selected_row_identity, dict):
        errors.append("binding.selected_row_identity must be an object")
    else:
        binding_fields["selected_row_identity"]["fight_name"] = _normalize_required_string(selected_row_identity.get("fight_name"))
        binding_fields["selected_row_identity"]["fight_id"] = _normalize_nullable_string(selected_row_identity.get("fight_id"))
        if not binding_fields["selected_row_identity"]["fight_name"]:
            errors.append("binding.selected_row_identity.fight_name is required")
        if "fight_id" in selected_row_identity and selected_row_identity.get("fight_id") is not None and not isinstance(selected_row_identity.get("fight_id"), str):
            errors.append("binding.selected_row_identity.fight_id must be a string or null")

    if "record_fight_id" in binding and binding.get("record_fight_id") is not None and not isinstance(binding.get("record_fight_id"), str):
        errors.append("binding.record_fight_id must be a string or null")

    if errors:
        return {
            "ok": False,
            "binding_digest": None,
            "binding_fields": binding_fields,
            "errors": errors,
        }

    digest_parts = [
        binding_fields["selected_key"],
        binding_fields["citation_fingerprint"],
        binding_fields["source_url"],
        binding_fields["source_date"],
        binding_fields["extracted_winner"],
        binding_fields["selected_row_identity"]["fight_name"],
        binding_fields["selected_row_identity"]["fight_id"],
        binding_fields["record_fight_id"],
    ]
    canonical = "|".join(digest_parts)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return {
        "ok": True,
        "binding_digest": digest,
        "binding_fields": binding_fields,
        "errors": [],
    }


def issue_official_source_approved_apply_token(binding: dict, *, now_epoch: int, ttl_seconds: int = 300) -> dict:
    now_epoch_int, now_err = _coerce_epoch(now_epoch)
    if now_err:
        return {
            "ok": False,
            "token": None,
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "binding_fields": None,
            "consumed": False,
            "errors": [now_err],
        }

    if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int):
        return {
            "ok": False,
            "token": None,
            "token_id": None,
            "issued_at_epoch": now_epoch_int,
            "expires_at_epoch": None,
            "binding_digest": None,
            "binding_fields": None,
            "consumed": False,
            "errors": ["ttl_seconds must be an integer"],
        }

    if ttl_seconds <= 0:
        return {
            "ok": False,
            "token": None,
            "token_id": None,
            "issued_at_epoch": now_epoch_int,
            "expires_at_epoch": None,
            "binding_digest": None,
            "binding_fields": None,
            "consumed": False,
            "errors": ["ttl_seconds must be positive"],
        }

    ttl_effective = min(ttl_seconds, MAX_TTL_SECONDS)
    digest_result = build_official_source_approved_apply_binding_digest(binding)
    if not digest_result.get("ok"):
        return {
            "ok": False,
            "token": None,
            "token_id": None,
            "issued_at_epoch": now_epoch_int,
            "expires_at_epoch": None,
            "binding_digest": None,
            "binding_fields": digest_result.get("binding_fields"),
            "consumed": False,
            "errors": list(digest_result.get("errors") or []),
        }

    issued_at_epoch = now_epoch_int
    expires_at_epoch = issued_at_epoch + ttl_effective
    token_id = uuid.uuid4().hex
    binding_digest = str(digest_result.get("binding_digest"))
    token = f"{TOKEN_PREFIX}.{issued_at_epoch}.{expires_at_epoch}.{token_id}.{binding_digest}"

    return {
        "ok": True,
        "token": token,
        "token_id": token_id,
        "issued_at_epoch": issued_at_epoch,
        "expires_at_epoch": expires_at_epoch,
        "binding_digest": binding_digest,
        "binding_fields": digest_result.get("binding_fields"),
        "consumed": False,
        "errors": [],
    }


def parse_official_source_approved_apply_token(token: str) -> dict:
    if not _is_non_empty_string(token):
        return {
            "ok": False,
            "token_status": "missing",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token is required"],
        }

    token_value = token.strip()
    parts = token_value.split(".")
    if len(parts) != 5:
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token format is invalid"],
        }

    prefix, issued_raw, expires_raw, token_id, binding_digest = parts

    if prefix != TOKEN_PREFIX:
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token prefix is invalid"],
        }

    try:
        issued_at_epoch = int(issued_raw)
        expires_at_epoch = int(expires_raw)
    except Exception:
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token timestamps are invalid"],
        }

    if issued_at_epoch < 0 or expires_at_epoch < 0 or expires_at_epoch < issued_at_epoch:
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token time range is invalid"],
        }

    if not _TOKEN_ID_RE.match(token_id):
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token id is invalid"],
        }

    if not _SHA256_RE.match(binding_digest):
        return {
            "ok": False,
            "token_status": "malformed",
            "token_id": None,
            "issued_at_epoch": None,
            "expires_at_epoch": None,
            "binding_digest": None,
            "errors": ["approval token digest is invalid"],
        }

    return {
        "ok": True,
        "token_status": "valid",
        "token_id": token_id,
        "issued_at_epoch": issued_at_epoch,
        "expires_at_epoch": expires_at_epoch,
        "binding_digest": binding_digest,
        "errors": [],
    }


def validate_official_source_approved_apply_token(
    token: object,
    binding: dict,
    *,
    now_epoch: int,
    consumed_token_ids: set | None = None,
    replayed_token_ids: set | None = None,
    allowed_clock_skew_seconds: int = 5,
    approval_granted: bool = True,
) -> dict:
    now_epoch_int, now_err = _coerce_epoch(now_epoch)
    if now_err:
        return _build_validation_response(
            token_valid=False,
            token_status="malformed",
            reason_code=_REASON_MALFORMED,
            errors=[now_err],
            approval_granted=approval_granted,
            selected_key=None,
            binding_digest_expected=None,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=0,
        )

    if isinstance(allowed_clock_skew_seconds, bool) or not isinstance(allowed_clock_skew_seconds, int) or allowed_clock_skew_seconds < 0:
        return _build_validation_response(
            token_valid=False,
            token_status="malformed",
            reason_code=_REASON_MALFORMED,
            errors=["allowed_clock_skew_seconds must be a non-negative integer"],
            approval_granted=approval_granted,
            selected_key=None,
            binding_digest_expected=None,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=now_epoch_int,
        )

    digest_result = build_official_source_approved_apply_binding_digest(binding)
    selected_key = None
    binding_digest_expected = None
    if digest_result.get("binding_fields") and isinstance(digest_result["binding_fields"], dict):
        selected_key = digest_result["binding_fields"].get("selected_key") or None
    if digest_result.get("ok"):
        binding_digest_expected = str(digest_result.get("binding_digest"))

    if not approval_granted:
        return _build_validation_response(
            token_valid=False,
            token_status="missing",
            reason_code=_REASON_APPROVAL_REQUIRED,
            errors=["approval_granted must be true"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=now_epoch_int,
        )

    if not digest_result.get("ok"):
        return _build_validation_response(
            token_valid=False,
            token_status="malformed",
            reason_code=_REASON_MALFORMED,
            errors=list(digest_result.get("errors") or []),
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=None,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=now_epoch_int,
        )

    parsed = parse_official_source_approved_apply_token(token if isinstance(token, str) else "")
    token_status = parsed.get("token_status") or "malformed"

    if token_status == "missing":
        return _build_validation_response(
            token_valid=False,
            token_status="missing",
            reason_code=_REASON_APPROVAL_MISSING,
            errors=list(parsed.get("errors") or []),
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=now_epoch_int,
        )

    if not parsed.get("ok"):
        return _build_validation_response(
            token_valid=False,
            token_status="malformed",
            reason_code=_REASON_MALFORMED,
            errors=list(parsed.get("errors") or []),
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=None,
            issued_at_epoch=None,
            expires_at_epoch=None,
            now_epoch=now_epoch_int,
        )

    token_id = str(parsed.get("token_id") or "")
    issued_at_epoch = int(parsed.get("issued_at_epoch"))
    expires_at_epoch = int(parsed.get("expires_at_epoch"))
    binding_digest_actual = str(parsed.get("binding_digest") or "")

    if issued_at_epoch > now_epoch_int + allowed_clock_skew_seconds:
        return _build_validation_response(
            token_valid=False,
            token_status="future_issued",
            reason_code=_REASON_FUTURE_ISSUED,
            errors=["approval token issued_at_epoch is in the future"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=binding_digest_actual,
            issued_at_epoch=issued_at_epoch,
            expires_at_epoch=expires_at_epoch,
            now_epoch=now_epoch_int,
        )

    if now_epoch_int > expires_at_epoch:
        return _build_validation_response(
            token_valid=False,
            token_status="expired",
            reason_code=_REASON_EXPIRED,
            errors=["approval token is expired"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=binding_digest_actual,
            issued_at_epoch=issued_at_epoch,
            expires_at_epoch=expires_at_epoch,
            now_epoch=now_epoch_int,
        )

    replayed_ids = replayed_token_ids or set()
    consumed_ids = consumed_token_ids or set()

    if token_id in replayed_ids:
        return _build_validation_response(
            token_valid=False,
            token_status="replayed",
            reason_code=_REASON_REPLAYED,
            errors=["approval token was replayed"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=binding_digest_actual,
            issued_at_epoch=issued_at_epoch,
            expires_at_epoch=expires_at_epoch,
            now_epoch=now_epoch_int,
        )

    if token_id in consumed_ids:
        return _build_validation_response(
            token_valid=False,
            token_status="consumed",
            reason_code=_REASON_CONSUMED,
            errors=["approval token is already consumed"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=binding_digest_actual,
            issued_at_epoch=issued_at_epoch,
            expires_at_epoch=expires_at_epoch,
            now_epoch=now_epoch_int,
        )

    if binding_digest_actual != binding_digest_expected:
        return _build_validation_response(
            token_valid=False,
            token_status="binding_mismatch",
            reason_code=_REASON_BINDING_MISMATCH,
            errors=["approval token binding digest mismatch"],
            approval_granted=approval_granted,
            selected_key=selected_key,
            binding_digest_expected=binding_digest_expected,
            binding_digest_actual=binding_digest_actual,
            issued_at_epoch=issued_at_epoch,
            expires_at_epoch=expires_at_epoch,
            now_epoch=now_epoch_int,
        )

    return _build_validation_response(
        token_valid=True,
        token_status="valid",
        reason_code=_REASON_VALID_TOKEN,
        errors=[],
        approval_granted=approval_granted,
        selected_key=selected_key,
        binding_digest_expected=binding_digest_expected,
        binding_digest_actual=binding_digest_actual,
        issued_at_epoch=issued_at_epoch,
        expires_at_epoch=expires_at_epoch,
        now_epoch=now_epoch_int,
    )


__all__ = [
    "build_official_source_approved_apply_binding_digest",
    "issue_official_source_approved_apply_token",
    "parse_official_source_approved_apply_token",
    "validate_official_source_approved_apply_token",
]

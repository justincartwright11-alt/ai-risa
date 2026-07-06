"""Controlled storage adapter scaffold for future Gate 1 approved saves.

This module is scaffold-only:
- never performs production queue/database writes
- never performs live web calls
- supports test-only in-memory and explicit temp-path persistence
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from operator_dashboard.local_ai_orchestrator_gate1_approved_save_writer import (
    Gate1ApprovedSaveWriterScaffoldResult,
)


_PRODUCTION_WRITE_TARGETS = {
    "queue",
    "database",
    "queue_prod",
    "database_prod",
    "production_queue",
    "production_database",
}


@dataclass
class Gate1SaveStorageAdapterScaffoldResult:
    ok: bool
    adapter_scaffold_only: bool = True
    production_write_performed: bool = False
    queue_write_performed: bool = False
    database_write_performed: bool = False
    test_write_performed: bool = False
    audit_record_preview: Optional[Dict[str, Any]] = None
    rollback_pointer_preview: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    persisted_preview_refs: Optional[List[str]] = None
    blocking_reasons: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if data["persisted_preview_refs"] is None:
            data["persisted_preview_refs"] = []
        if data["blocking_reasons"] is None:
            data["blocking_reasons"] = []
        return data

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


class Gate1SaveStorageAdapter(ABC):
    """Adapter interface for scaffold preview persistence only."""

    @abstractmethod
    def persist_preview(
        self,
        *,
        idempotency_key: str,
        write_target: str,
        audit_record_preview: Dict[str, Any],
        rollback_pointer_preview: Dict[str, Any],
        would_write_candidates: Sequence[Any],
    ) -> List[str]:
        """Persist preview-only references and return stable persisted ref ids."""


class InMemoryGate1SaveStorageAdapter(Gate1SaveStorageAdapter):
    """Test-only in-memory adapter."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []

    def persist_preview(
        self,
        *,
        idempotency_key: str,
        write_target: str,
        audit_record_preview: Dict[str, Any],
        rollback_pointer_preview: Dict[str, Any],
        would_write_candidates: Sequence[Any],
    ) -> List[str]:
        ref = f"inmem:{idempotency_key}:{len(self.records) + 1}"
        self.records.append(
            {
                "ref": ref,
                "idempotency_key": idempotency_key,
                "write_target": write_target,
                "audit_record_preview": dict(audit_record_preview),
                "rollback_pointer_preview": dict(rollback_pointer_preview),
                "would_write_candidates": list(would_write_candidates),
            }
        )
        return [ref]


class TempPathGate1SaveStorageAdapter(Gate1SaveStorageAdapter):
    """Test-only adapter that writes preview refs under an explicit temp root."""

    def __init__(self, temp_root: Path) -> None:
        self.temp_root = Path(temp_root).resolve()

    def _safe_ref_path(self, idempotency_key: str) -> Path:
        safe_key = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in idempotency_key)
        out = (self.temp_root / f"gate1_preview_{safe_key}.json").resolve()
        if str(out).lower().startswith(str(self.temp_root).lower()) is False:
            raise ValueError("temp path escape blocked")
        return out

    def persist_preview(
        self,
        *,
        idempotency_key: str,
        write_target: str,
        audit_record_preview: Dict[str, Any],
        rollback_pointer_preview: Dict[str, Any],
        would_write_candidates: Sequence[Any],
    ) -> List[str]:
        self.temp_root.mkdir(parents=True, exist_ok=True)
        out = self._safe_ref_path(idempotency_key)
        payload = {
            "idempotency_key": idempotency_key,
            "write_target": write_target,
            "audit_record_preview": dict(audit_record_preview),
            "rollback_pointer_preview": dict(rollback_pointer_preview),
            "would_write_candidates": list(would_write_candidates),
        }
        out.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return [str(out)]


def _request_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, Gate1ApprovedSaveWriterScaffoldResult):
        return value.to_dict()
    if isinstance(value, dict):
        return dict(value)
    return {}


def run_gate1_save_storage_adapter_scaffold(
    *,
    request: Any,
    adapter: Optional[Gate1SaveStorageAdapter] = None,
    allow_future_production_write: bool = False,
) -> Gate1SaveStorageAdapterScaffoldResult:
    """Run scaffold-only persistence for approved save preview output.

    Never performs production queue/database writes.
    """

    data = _request_dict(request)

    operator_approved = bool(data.get("operator_approved", False))
    live_write_enabled = bool(data.get("live_write_enabled", False))
    write_target = data.get("write_target")
    idempotency_key = data.get("idempotency_key")
    audit_record_preview = data.get("audit_record_preview")
    rollback_pointer_preview = data.get("rollback_pointer_preview")
    would_write_candidates = data.get("would_write_candidates")

    blocking_reasons: List[str] = []

    if not operator_approved:
        blocking_reasons.append("operator_approval_missing")
    if not isinstance(write_target, str) or not write_target.strip():
        blocking_reasons.append("write_target_missing")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        blocking_reasons.append("idempotency_key_missing")
    if not isinstance(audit_record_preview, dict):
        blocking_reasons.append("audit_record_preview_missing")
    if not isinstance(rollback_pointer_preview, dict):
        blocking_reasons.append("rollback_pointer_preview_missing")
    if not isinstance(would_write_candidates, list):
        blocking_reasons.append("would_write_candidates_missing")

    target = str(write_target or "").strip()
    is_production_target = target in _PRODUCTION_WRITE_TARGETS

    if is_production_target and not live_write_enabled:
        blocking_reasons.append("live_write_disabled")

    if is_production_target and not allow_future_production_write:
        blocking_reasons.append("production_write_target_blocked")

    if blocking_reasons:
        return Gate1SaveStorageAdapterScaffoldResult(
            ok=False,
            adapter_scaffold_only=True,
            production_write_performed=False,
            queue_write_performed=False,
            database_write_performed=False,
            test_write_performed=False,
            audit_record_preview=audit_record_preview if isinstance(audit_record_preview, dict) else None,
            rollback_pointer_preview=rollback_pointer_preview if isinstance(rollback_pointer_preview, dict) else None,
            idempotency_key=idempotency_key if isinstance(idempotency_key, str) else None,
            persisted_preview_refs=[],
            blocking_reasons=blocking_reasons,
        )

    active_adapter = adapter or InMemoryGate1SaveStorageAdapter()
    refs = active_adapter.persist_preview(
        idempotency_key=idempotency_key,
        write_target=target,
        audit_record_preview=audit_record_preview,
        rollback_pointer_preview=rollback_pointer_preview,
        would_write_candidates=would_write_candidates,
    )

    return Gate1SaveStorageAdapterScaffoldResult(
        ok=True,
        adapter_scaffold_only=True,
        production_write_performed=False,
        queue_write_performed=False,
        database_write_performed=False,
        test_write_performed=True,
        audit_record_preview=audit_record_preview,
        rollback_pointer_preview=rollback_pointer_preview,
        idempotency_key=idempotency_key,
        persisted_preview_refs=list(refs or []),
        blocking_reasons=[],
    )


__all__ = [
    "Gate1SaveStorageAdapter",
    "Gate1SaveStorageAdapterScaffoldResult",
    "InMemoryGate1SaveStorageAdapter",
    "TempPathGate1SaveStorageAdapter",
    "run_gate1_save_storage_adapter_scaffold",
]

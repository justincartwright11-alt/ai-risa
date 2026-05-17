"""
local_ai_orchestrator_gate1_approved_save_writer.py
Controlled scaffold for the Gate 1 approved save writer.
NEVER performs live queue/database/filesystem/web writes. Scaffold only.
"""
from operator_dashboard.local_ai_orchestrator_gate1_token_check import check_gate1_approval_token_preview
from operator_dashboard.local_ai_orchestrator_gate1_save_fights_dry_run_apply_preview import run_gate1_save_fights_dry_run_apply_preview

class Gate1ApprovedSaveWriterScaffoldResult:
    def __init__(self, *, ok, scaffold_only, live_write_enabled, write_performed, queue_write_performed, database_write_performed,
                 audit_record_preview, rollback_pointer_preview, idempotency_key, would_write, blocking_reasons,
                 storage_adapter_checked=False, test_write_performed=False, persisted_preview_refs=None):
        self.ok = ok
        self.scaffold_only = scaffold_only
        self.live_write_enabled = live_write_enabled
        self.write_performed = write_performed
        self.queue_write_performed = queue_write_performed
        self.database_write_performed = database_write_performed
        self.audit_record_preview = audit_record_preview
        self.rollback_pointer_preview = rollback_pointer_preview
        self.idempotency_key = idempotency_key
        self.would_write = would_write
        self.blocking_reasons = blocking_reasons
        self.storage_adapter_checked = storage_adapter_checked
        self.test_write_performed = test_write_performed
        self.persisted_preview_refs = persisted_preview_refs if isinstance(persisted_preview_refs, list) else []

    def to_dict(self):
        return {
            "ok": self.ok,
            "scaffold_only": self.scaffold_only,
            "live_write_enabled": self.live_write_enabled,
            "write_performed": self.write_performed,
            "queue_write_performed": self.queue_write_performed,
            "database_write_performed": self.database_write_performed,
            "audit_record_preview": self.audit_record_preview,
            "rollback_pointer_preview": self.rollback_pointer_preview,
            "idempotency_key": self.idempotency_key,
            "would_write": self.would_write,
            "blocking_reasons": self.blocking_reasons,
            "storage_adapter_checked": self.storage_adapter_checked,
            "test_write_performed": self.test_write_performed,
            "persisted_preview_refs": self.persisted_preview_refs,
        }

    def to_json(self):
        import json
        return json.dumps(self.to_dict(), sort_keys=True)


def _candidate_id_list(candidate_rows):
    rows = candidate_rows if isinstance(candidate_rows, list) else []
    ids = []
    for idx, row in enumerate(rows):
        if not isinstance(row, dict):
            ids.append(f"index:{idx}")
            continue
        val = (
            row.get("candidate_id")
            or row.get("fight_id")
            or row.get("fight_key")
            or row.get("matchup_key")
            or row.get("id")
            or row.get("fight_name")
        )
        if isinstance(val, str) and val.strip():
            ids.append(val.strip())
        else:
            ids.append(f"index:{idx}")
    return ids


def run_gate1_approved_save_writer_scaffold(request, storage_adapter=None):
    # Required fields
    operator_approved = request.get("operator_approved")
    gate_approval_token_preview = request.get("gate_approval_token_preview")
    candidate_scope = request.get("candidate_scope")
    candidate_rows = request.get("candidate_rows")
    idempotency_key = request.get("idempotency_key")
    write_target = request.get("write_target")
    dry_run_required = request.get("dry_run_required", True)
    live_write_enabled = request.get("live_write_enabled", False)

    # Fail closed if live write is requested
    if live_write_enabled is True:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=["live_write_enabled_not_allowed"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Fail closed on missing approval
    if not operator_approved:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=["operator_approval_missing"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Token check
    token_check = check_gate1_approval_token_preview(gate_approval_token_preview)
    if not getattr(token_check, "ok", False):
        blocking_reasons = ["token_check_failed"]
        if hasattr(token_check, "blocking_reasons") and token_check.blocking_reasons:
            blocking_reasons += token_check.blocking_reasons
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=blocking_reasons,
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Dry-run apply preview
    dry_run_result = run_gate1_save_fights_dry_run_apply_preview(
        gate_approval_token_preview=gate_approval_token_preview,
        candidate_rows=candidate_rows,
        candidate_scope=candidate_scope
    )
    # If not eligible for future approval, fail closed with specific reason if provenance/duplicate/conflict, else dry_run_not_eligible
    if not getattr(dry_run_result, "eligible_for_future_approval", False):
        provenance_missing = getattr(dry_run_result, "provenance_missing_count", 0) > 0
        duplicate_conflict = getattr(dry_run_result, "duplicate_or_conflict_count", 0) > 0
        if provenance_missing:
            blocking_reasons = ["provenance_missing"]
        elif duplicate_conflict:
            blocking_reasons = ["duplicate_or_conflict"]
        else:
            blocking_reasons = ["dry_run_not_eligible"]
            if hasattr(dry_run_result, "blocking_reasons") and dry_run_result.blocking_reasons:
                blocking_reasons += list(dry_run_result.blocking_reasons)
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=blocking_reasons,
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # If eligible, check provenance and duplicate/conflict
    if getattr(dry_run_result, "provenance_missing_count", 0) > 0:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=["provenance_missing"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )
    if getattr(dry_run_result, "duplicate_or_conflict_count", 0) > 0:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=["duplicate_or_conflict"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Idempotency key
    if not idempotency_key:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=None,
            would_write=False, blocking_reasons=["idempotency_key_missing"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Write target
    if not write_target:
        return Gate1ApprovedSaveWriterScaffoldResult(
            ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
            queue_write_performed=False, database_write_performed=False,
            audit_record_preview=None, rollback_pointer_preview=None, idempotency_key=idempotency_key,
            would_write=False, blocking_reasons=["write_target_missing"],
            storage_adapter_checked=bool(storage_adapter), test_write_performed=False, persisted_preview_refs=[]
        )

    # Scaffold result: never perform live write
    audit_record_preview = {
        "operator_approved": operator_approved,
        "token": gate_approval_token_preview,
        "candidate_scope": candidate_scope,
        "candidate_rows_count": len(candidate_rows or []),
        "idempotency_key": idempotency_key,
        "write_target": write_target,
        "action": "scaffold_save_preview",
    }
    rollback_pointer_preview = {
        "pre_write_state": "scaffold_only",
        "idempotency_key": idempotency_key,
    }

    storage_adapter_checked = False
    test_write_performed = False
    persisted_preview_refs = []

    if storage_adapter is not None:
        storage_adapter_checked = True
        from operator_dashboard.local_ai_orchestrator_gate1_save_storage_adapter import (
            run_gate1_save_storage_adapter_scaffold,
        )

        storage_result = run_gate1_save_storage_adapter_scaffold(
            request={
                "operator_approved": operator_approved,
                "live_write_enabled": False,
                "write_target": write_target,
                "idempotency_key": idempotency_key,
                "audit_record_preview": audit_record_preview,
                "rollback_pointer_preview": rollback_pointer_preview,
                "would_write_candidates": _candidate_id_list(candidate_rows),
            },
            adapter=storage_adapter,
            allow_future_production_write=False,
        )

        if (not storage_result.ok) or storage_result.queue_write_performed or storage_result.database_write_performed:
            blocking_reasons = list(storage_result.blocking_reasons or [])
            if storage_result.queue_write_performed:
                blocking_reasons.append("adapter_queue_write_not_allowed")
            if storage_result.database_write_performed:
                blocking_reasons.append("adapter_database_write_not_allowed")
            return Gate1ApprovedSaveWriterScaffoldResult(
                ok=False, scaffold_only=True, live_write_enabled=False, write_performed=False,
                queue_write_performed=False, database_write_performed=False,
                audit_record_preview=audit_record_preview,
                rollback_pointer_preview=rollback_pointer_preview,
                idempotency_key=idempotency_key,
                would_write=False,
                blocking_reasons=blocking_reasons,
                storage_adapter_checked=True,
                test_write_performed=False,
                persisted_preview_refs=[]
            )

        test_write_performed = bool(storage_result.test_write_performed)
        persisted_preview_refs = list(storage_result.persisted_preview_refs or [])

    return Gate1ApprovedSaveWriterScaffoldResult(
        ok=True, scaffold_only=True, live_write_enabled=False, write_performed=False,
        queue_write_performed=False, database_write_performed=False,
        audit_record_preview=audit_record_preview,
        rollback_pointer_preview=rollback_pointer_preview,
        idempotency_key=idempotency_key,
        would_write=True,
        blocking_reasons=[],
        storage_adapter_checked=storage_adapter_checked,
        test_write_performed=test_write_performed,
        persisted_preview_refs=persisted_preview_refs
    )

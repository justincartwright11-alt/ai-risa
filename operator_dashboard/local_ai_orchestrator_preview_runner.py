"""Preview-only local AI orchestrator job runner.

This runner executes typed local AI jobs in preview mode only. It never performs
filesystem writes, network calls, route changes, or dashboard mutations.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Dict

from operator_dashboard.local_ai_orchestrator_engine_adapter_registry import (
    LocalAIOrchestratorEngineAdapterRegistry,
    get_default_adapter_registry,
)
from operator_dashboard.local_ai_orchestrator_job_schema import (
    LocalAIJob,
    LocalAIJobBlockingReason,
    LocalAIJobOutputPreview,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _blocked(job: LocalAIJob, code: str, message: str, details: Dict[str, Any] | None = None) -> LocalAIJob:
    reason = LocalAIJobBlockingReason(
        code=code,
        message=message,
        severity="warning",
        details=details or {},
    )
    return replace(
        job,
        status="blocked",
        blocking_reasons=list(job.blocking_reasons) + [reason],
        updated_at_utc=_utc_now_iso(),
    )


def _preview_ready(job: LocalAIJob, summary: Dict[str, Any], metrics: Dict[str, Any] | None = None) -> LocalAIJob:
    preview = LocalAIJobOutputPreview(
        summary=summary,
        artifact_refs=list(job.output_preview.artifact_refs),
        metrics=metrics or {},
    )
    return replace(
        job,
        status="preview_ready",
        output_preview=preview,
        blocking_reasons=[],
        updated_at_utc=_utc_now_iso(),
    )


def _is_missing_input(job: LocalAIJob) -> bool:
    if not job.input_ref.ref_type or not job.input_ref.ref_type.strip():
        return True
    if not job.input_ref.ref_key or not job.input_ref.ref_key.strip():
        return True
    return False


def run_preview_job(
    job: LocalAIJob,
    adapter_registry: LocalAIOrchestratorEngineAdapterRegistry | None = None,
) -> LocalAIJob:
    """Run a local AI job through preview-only orchestration.

    Rules:
    - Accept a LocalAIJob and validate it.
    - Dispatch to typed preview handler.
    - Return preview_ready on success.
    - Return blocked when required input is missing.
    - Return failed only for unexpected safe exceptions.
    - Never perform permanent actions.
    """
    # Fail closed via schema validation.
    job.validate()

    if _is_missing_input(job):
        return _blocked(
            job,
            code="missing_required_input",
            message="required input_ref fields are missing",
            details={"ref_type": job.input_ref.ref_type, "ref_key": job.input_ref.ref_key},
        )

    registry = adapter_registry or get_default_adapter_registry()

    try:
        adapter_result = registry.run_preview(job)
        out = _preview_ready(
            job,
            summary=adapter_result.summary,
            metrics=adapter_result.metrics,
        )
        # Guardrail: telemetry must remain preview-only with no mutation flags.
        out.validate()
        return out
    except ValueError:
        # Preserve fail-closed semantics for validation/type errors.
        raise
    except Exception as exc:
        return replace(
            job,
            status="failed",
            blocking_reasons=list(job.blocking_reasons)
            + [
                LocalAIJobBlockingReason(
                    code="runner_unexpected_error",
                    message="unexpected safe exception in preview runner",
                    severity="high",
                    details={"error": str(exc)},
                )
            ],
            updated_at_utc=_utc_now_iso(),
        )


__all__ = ["run_preview_job"]

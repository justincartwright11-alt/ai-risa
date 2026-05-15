"""Preview-only local AI orchestrator job runner.

This runner executes typed local AI jobs in preview mode only. It never performs
filesystem writes, network calls, route changes, or dashboard mutations.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Any, Callable, Dict

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


def _handler_discovery(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "discovery_preview",
        "source_button": job.source_button,
        "ref_key": job.input_ref.ref_key,
        "candidate_events_estimate": 3,
        "preview_only": True,
        "live_search_executed": False,
    }
    return _preview_ready(job, summary=summary, metrics={"confidence": 0.8})


def _handler_extraction(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "extraction_preview",
        "source_button": job.source_button,
        "ref_key": job.input_ref.ref_key,
        "candidate_fights_estimate": 8,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary, metrics={"parse_coverage": 0.9})


def _handler_normalization(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "normalization_preview",
        "ref_key": job.input_ref.ref_key,
        "normalized_name_pairs_estimate": 8,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_dedupe(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "dedupe_preview",
        "ref_key": job.input_ref.ref_key,
        "duplicates_detected_estimate": 1,
        "unique_fights_estimate": 7,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_ranking(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "ranking_preview",
        "ref_key": job.input_ref.ref_key,
        "ranked_fights_estimate": 7,
        "ready_for_queue_candidates_estimate": 4,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary, metrics={"avg_readiness": 0.74})


def _handler_queue_candidate(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "queue_candidate_preview",
        "ref_key": job.input_ref.ref_key,
        "candidate_queue_rows": 4,
        "approval_required": True,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_report_generation(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "report_generation_preview",
        "ref_key": job.input_ref.ref_key,
        "sections_estimate": 26,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary, metrics={"content_depth_score": 0.78})


def _handler_report_quality(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "report_quality_preview",
        "ref_key": job.input_ref.ref_key,
        "qa_status": "pass_with_warnings",
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary, metrics={"qa_score": 0.88})


def _handler_pdf_preview(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "pdf_preview",
        "ref_key": job.input_ref.ref_key,
        "pdf_preview_available": True,
        "export_approved": False,
        "approval_required": True,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_delivery_candidate(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "delivery_candidate_preview",
        "ref_key": job.input_ref.ref_key,
        "delivery_candidate_ready": True,
        "approval_required": True,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_result_search(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "result_search_preview",
        "ref_key": job.input_ref.ref_key,
        "source_checks_estimate": 5,
        "live_search_executed": False,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_result_match(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "result_match_preview",
        "ref_key": job.input_ref.ref_key,
        "state_counts": {
            "Results Found": 1,
            "Needs Source": 1,
            "Conflict": 0,
            "No Result Yet": 1,
            "Ready to Compare": 1,
        },
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_accuracy_comparison(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "accuracy_comparison_preview",
        "ref_key": job.input_ref.ref_key,
        "rows_compared_estimate": 4,
        "accuracy_pct_estimate": 75.0,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


def _handler_calibration_recommendation(job: LocalAIJob) -> LocalAIJob:
    summary = {
        "stage": "calibration_recommendation_preview",
        "ref_key": job.input_ref.ref_key,
        "recommendation_count": 2,
        "approval_required": True,
        "preview_only": True,
    }
    return _preview_ready(job, summary=summary)


_JOB_HANDLERS: Dict[str, Callable[[LocalAIJob], LocalAIJob]] = {
    "discovery_job": _handler_discovery,
    "extraction_job": _handler_extraction,
    "normalization_job": _handler_normalization,
    "dedupe_job": _handler_dedupe,
    "ranking_job": _handler_ranking,
    "queue_candidate_job": _handler_queue_candidate,
    "report_generation_job": _handler_report_generation,
    "report_quality_job": _handler_report_quality,
    "pdf_preview_job": _handler_pdf_preview,
    "delivery_candidate_job": _handler_delivery_candidate,
    "result_search_job": _handler_result_search,
    "result_match_job": _handler_result_match,
    "accuracy_comparison_job": _handler_accuracy_comparison,
    "calibration_recommendation_job": _handler_calibration_recommendation,
}


def run_preview_job(job: LocalAIJob) -> LocalAIJob:
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

    handler = _JOB_HANDLERS.get(job.job_type)
    if handler is None:
        raise ValueError(f"invalid job_type: {job.job_type}")

    try:
        out = handler(job)
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

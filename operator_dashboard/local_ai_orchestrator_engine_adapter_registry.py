"""Preview-only engine adapter registry for local AI orchestrator jobs.

This module provides a safe adapter layer between local AI jobs and internal
preview engines. Adapters are deterministic, in-memory, and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJob

try:
    from operator_dashboard.button3_auto_result_source_yield_live_executor_preview import (
        build_readonly_executor_preview_response as _button3_build_readonly_executor_preview_response,
    )
except Exception:
    try:
        from button3_auto_result_source_yield_live_executor_preview import (
            build_readonly_executor_preview_response as _button3_build_readonly_executor_preview_response,
        )
    except Exception:
        _button3_build_readonly_executor_preview_response = None


@dataclass(frozen=True)
class AdapterPreviewResult:
    """Adapter preview payload returned to the runner."""

    summary: Dict[str, Any]
    metrics: Dict[str, Any]


_BUTTON1_SUMMARY_FIELDS = [
    "discovered_count",
    "extracted_count",
    "ready_for_report_count",
    "needs_fixture_data_count",
    "draft_only_count",
    "blocked_on_missing_fighter_count",
    "duplicate_or_conflict_count",
]


def _coerce_count(value: Any) -> int:
    try:
        out = int(value)
        return out if out >= 0 else 0
    except Exception:
        return 0


def _button1_payload(job: LocalAIJob) -> Dict[str, Any]:
    metadata = job.input_ref.metadata if isinstance(job.input_ref.metadata, dict) else {}
    payload = metadata.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def _button1_safe_summary(job: LocalAIJob) -> Dict[str, Any]:
    payload = _button1_payload(job)

    discovered_rows = payload.get("discovered_rows", [])
    extracted_rows = payload.get("extracted_rows", [])
    duplicate_rows = payload.get("duplicate_rows", [])

    if not isinstance(discovered_rows, list):
        discovered_rows = []
    if not isinstance(extracted_rows, list):
        extracted_rows = []
    if not isinstance(duplicate_rows, list):
        duplicate_rows = []

    summary = {
        "discovered_count": _coerce_count(payload.get("discovered_count", len(discovered_rows))),
        "extracted_count": _coerce_count(payload.get("extracted_count", len(extracted_rows))),
        "ready_for_report_count": _coerce_count(payload.get("ready_for_report_count", 0)),
        "needs_fixture_data_count": _coerce_count(payload.get("needs_fixture_data_count", 0)),
        "draft_only_count": _coerce_count(payload.get("draft_only_count", 0)),
        "blocked_on_missing_fighter_count": _coerce_count(payload.get("blocked_on_missing_fighter_count", 0)),
        "duplicate_or_conflict_count": _coerce_count(payload.get("duplicate_or_conflict_count", len(duplicate_rows))),
        "approval_required": True,
        "gate_name": "Approve Save Fights",
    }
    return summary


def _base_summary(job: LocalAIJob, stage: str) -> Dict[str, Any]:
    return {
        "stage": stage,
        "source_button": job.source_button,
        "ref_key": job.input_ref.ref_key,
        "preview_only": True,
    }


def _discovery_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(
        summary=summary,
        metrics={
            "readonly_preview": True,
            "live_search_executed": False,
        },
    )


def _extraction_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(summary=summary, metrics={"readonly_preview": True})


def _normalization_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(summary=summary, metrics={"readonly_preview": True})


def _dedupe_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(summary=summary, metrics={"readonly_preview": True})


def _ranking_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(summary=summary, metrics={"readonly_preview": True})


def _queue_candidate_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _button1_safe_summary(job)
    return AdapterPreviewResult(summary=summary, metrics={"readonly_preview": True})


def _report_generation_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "report_generation_preview")
    summary.update({"sections_estimate": 26})
    return AdapterPreviewResult(summary=summary, metrics={"content_depth_score": 0.78})


def _report_quality_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "report_quality_preview")
    summary.update({"qa_status": "pass_with_warnings"})
    return AdapterPreviewResult(summary=summary, metrics={"qa_score": 0.88})


def _pdf_preview_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "pdf_preview")
    summary.update({
        "pdf_preview_available": True,
        "export_approved": False,
        "approval_required": True,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


def _delivery_candidate_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "delivery_candidate_preview")
    summary.update({
        "delivery_candidate_ready": True,
        "approval_required": True,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


def _result_search_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    payload = job.input_ref.metadata.get("payload", {}) if isinstance(job.input_ref.metadata, dict) else {}
    waiting_rows = payload.get("waiting_rows", []) if isinstance(payload, dict) else []
    if not isinstance(waiting_rows, list):
        waiting_rows = []

    state_keys = [
        "Results Found",
        "Needs Source",
        "Conflict",
        "No Result Yet",
        "Ready to Compare",
    ]

    # Safe no-input preview path. No fake rows or candidates are synthesized.
    if not waiting_rows:
        summary = {k: 0 for k in state_keys}
        summary["total_rows"] = 0
        return AdapterPreviewResult(
            summary=summary,
            metrics={
                "source_yield_preview_hooked": bool(_button3_build_readonly_executor_preview_response),
                "used_executor_preview": False,
            },
        )

    if _button3_build_readonly_executor_preview_response is None:
        summary = {k: 0 for k in state_keys}
        summary["total_rows"] = len(waiting_rows)
        return AdapterPreviewResult(
            summary=summary,
            metrics={
                "source_yield_preview_hooked": False,
                "used_executor_preview": False,
            },
        )

    response = _button3_build_readonly_executor_preview_response(
        waiting_rows=waiting_rows,
        provider=None,
        include_diagnostics=False,
    )
    source_summary = response.get("summary", {}) if isinstance(response, dict) else {}

    # Summary-only surface for normal-mode adapter output.
    summary = {
        "Results Found": int(source_summary.get("Results Found", 0) or 0),
        "Needs Source": int(source_summary.get("Needs Source", 0) or 0),
        "Conflict": int(source_summary.get("Conflict", 0) or 0),
        "No Result Yet": int(source_summary.get("No Result Yet", 0) or 0),
        "Ready to Compare": int(source_summary.get("Ready to Compare", 0) or 0),
        "total_rows": int(source_summary.get("total_rows", len(waiting_rows)) or 0),
    }

    return AdapterPreviewResult(
        summary=summary,
        metrics={
            "source_yield_preview_hooked": True,
            "used_executor_preview": True,
        },
    )


def _result_match_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "result_match_preview")
    summary.update({
        "state_counts": {
            "Results Found": 1,
            "Needs Source": 1,
            "Conflict": 0,
            "No Result Yet": 1,
            "Ready to Compare": 1,
        }
    })
    return AdapterPreviewResult(summary=summary, metrics={})


def _accuracy_comparison_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "accuracy_comparison_preview")
    summary.update({
        "rows_compared_estimate": 4,
        "accuracy_pct_estimate": 75.0,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


def _calibration_recommendation_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "calibration_recommendation_preview")
    summary.update({
        "recommendation_count": 2,
        "approval_required": True,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


DEFAULT_ADAPTERS: Dict[str, Callable[[LocalAIJob], AdapterPreviewResult]] = {
    "discovery_job": _discovery_adapter,
    "extraction_job": _extraction_adapter,
    "normalization_job": _normalization_adapter,
    "dedupe_job": _dedupe_adapter,
    "ranking_job": _ranking_adapter,
    "queue_candidate_job": _queue_candidate_adapter,
    "report_generation_job": _report_generation_adapter,
    "report_quality_job": _report_quality_adapter,
    "pdf_preview_job": _pdf_preview_adapter,
    "delivery_candidate_job": _delivery_candidate_adapter,
    "result_search_job": _result_search_adapter,
    "result_match_job": _result_match_adapter,
    "accuracy_comparison_job": _accuracy_comparison_adapter,
    "calibration_recommendation_job": _calibration_recommendation_adapter,
}


class LocalAIOrchestratorEngineAdapterRegistry:
    """Registry for preview-only local AI engine adapters."""

    def __init__(self, adapters: Dict[str, Callable[[LocalAIJob], AdapterPreviewResult]] | None = None):
        self._adapters = dict(adapters or DEFAULT_ADAPTERS)

    def has_adapter(self, job_type: str) -> bool:
        return job_type in self._adapters

    def get_adapter(self, job_type: str) -> Callable[[LocalAIJob], AdapterPreviewResult]:
        adapter = self._adapters.get(job_type)
        if adapter is None:
            raise ValueError(f"no preview adapter registered for job_type: {job_type}")
        return adapter

    def run_preview(self, job: LocalAIJob) -> AdapterPreviewResult:
        adapter = self.get_adapter(job.job_type)
        return adapter(job)


def get_default_adapter_registry() -> LocalAIOrchestratorEngineAdapterRegistry:
    return LocalAIOrchestratorEngineAdapterRegistry()


__all__ = [
    "AdapterPreviewResult",
    "DEFAULT_ADAPTERS",
    "LocalAIOrchestratorEngineAdapterRegistry",
    "get_default_adapter_registry",
]

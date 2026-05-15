"""Preview-only engine adapter registry for local AI orchestrator jobs.

This module provides a safe adapter layer between local AI jobs and internal
preview engines. Adapters are deterministic, in-memory, and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJob


@dataclass(frozen=True)
class AdapterPreviewResult:
    """Adapter preview payload returned to the runner."""

    summary: Dict[str, Any]
    metrics: Dict[str, Any]


def _base_summary(job: LocalAIJob, stage: str) -> Dict[str, Any]:
    return {
        "stage": stage,
        "source_button": job.source_button,
        "ref_key": job.input_ref.ref_key,
        "preview_only": True,
    }


def _discovery_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "discovery_preview")
    summary.update({
        "candidate_events_estimate": 3,
        "live_search_executed": False,
    })
    return AdapterPreviewResult(summary=summary, metrics={"confidence": 0.8})


def _extraction_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "extraction_preview")
    summary.update({"candidate_fights_estimate": 8})
    return AdapterPreviewResult(summary=summary, metrics={"parse_coverage": 0.9})


def _normalization_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "normalization_preview")
    summary.update({"normalized_name_pairs_estimate": 8})
    return AdapterPreviewResult(summary=summary, metrics={})


def _dedupe_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "dedupe_preview")
    summary.update({
        "duplicates_detected_estimate": 1,
        "unique_fights_estimate": 7,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


def _ranking_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "ranking_preview")
    summary.update({
        "ranked_fights_estimate": 7,
        "ready_for_queue_candidates_estimate": 4,
    })
    return AdapterPreviewResult(summary=summary, metrics={"avg_readiness": 0.74})


def _queue_candidate_adapter(job: LocalAIJob) -> AdapterPreviewResult:
    summary = _base_summary(job, "queue_candidate_preview")
    summary.update({
        "candidate_queue_rows": 4,
        "approval_required": True,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


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
    summary = _base_summary(job, "result_search_preview")
    summary.update({
        "source_checks_estimate": 5,
        "live_search_executed": False,
    })
    return AdapterPreviewResult(summary=summary, metrics={})


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

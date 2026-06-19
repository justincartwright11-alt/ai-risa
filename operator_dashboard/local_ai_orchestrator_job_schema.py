"""Typed preview-only job schema for local AI orchestration.

This module defines serializable dataclasses and strict validation for local
AI orchestrator jobs. It is intentionally side-effect free and performs no
filesystem writes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional

ALLOWED_JOB_TYPES = {
    "discovery_job",
    "extraction_job",
    "normalization_job",
    "dedupe_job",
    "ranking_job",
    "queue_candidate_job",
    "report_generation_job",
    "report_quality_job",
    "pdf_preview_job",
    "delivery_candidate_job",
    "result_search_job",
    "result_match_job",
    "accuracy_comparison_job",
    "calibration_recommendation_job",
}

ALLOWED_SOURCE_BUTTONS = {
    "button1_find_fights",
    "button2_generate_pdfs",
    "button3_find_results",
}

ALLOWED_JOB_STATUS = {
    "pending",
    "running",
    "preview_ready",
    "blocked",
    "failed",
    "approved_ready",
    "completed",
}

# Jobs that can precede permanent actions and therefore must require approval.
PERMANENT_ACTION_JOB_TYPES = {
    "queue_candidate_job",
    "delivery_candidate_job",
    "calibration_recommendation_job",
}


def _utc_now_iso() -> str:
    """Return UTC timestamp in ISO-8601 format with trailing Z."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _generate_job_id() -> str:
    """Generate a safely unique job identifier."""
    return f"job_{uuid.uuid4().hex}"


@dataclass(frozen=True)
class LocalAIJobBlockingReason:
    """Serializable blocking reason structure."""

    code: str
    message: str
    severity: str = "warning"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocalAIJobInputRef:
    """Reference to job input snapshot and identity."""

    ref_type: str
    ref_key: str
    snapshot_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocalAIJobOutputPreview:
    """Read-only preview output from a local AI job."""

    summary: Dict[str, Any] = field(default_factory=dict)
    artifact_refs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocalAIJobProvenance:
    """Serializable provenance for traceability and audit."""

    source_urls: List[str] = field(default_factory=list)
    engine_version: str = "local-ai-orchestrator-v1"
    collected_at_utc: str = field(default_factory=_utc_now_iso)
    trace: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocalAIJobSafetyTelemetry:
    """Locked governance telemetry defaults for preview-only operation."""

    preview_only: bool = True
    mutation_performed: bool = False
    queue_write_performed: bool = False
    report_export_approved: bool = False
    durable_write_performed: bool = False
    learning_apply_performed: bool = False
    calibration_write_performed: bool = False
    auto_apply_performed: bool = False
    operator_approval_required: bool = True


@dataclass(frozen=True)
class LocalAIJobApprovalRequirement:
    """Approval requirement for a job before any permanent action."""

    required: bool = True
    gate_id: Optional[str] = None
    reason: str = "operator_approval_required"


@dataclass
class LocalAIJob:
    """Top-level typed job structure for local AI orchestration."""

    job_type: str
    source_button: str
    input_ref: LocalAIJobInputRef
    output_preview: LocalAIJobOutputPreview = field(default_factory=LocalAIJobOutputPreview)
    status: str = "pending"
    blocking_reasons: List[LocalAIJobBlockingReason] = field(default_factory=list)
    provenance: LocalAIJobProvenance = field(default_factory=LocalAIJobProvenance)
    safety_telemetry: LocalAIJobSafetyTelemetry = field(default_factory=LocalAIJobSafetyTelemetry)
    approval_required: LocalAIJobApprovalRequirement = field(default_factory=LocalAIJobApprovalRequirement)
    job_id: str = field(default_factory=_generate_job_id)
    created_at_utc: str = field(default_factory=_utc_now_iso)
    updated_at_utc: str = field(default_factory=_utc_now_iso)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Fail closed validation for schema correctness and governance defaults."""
        if self.job_type not in ALLOWED_JOB_TYPES:
            raise ValueError(f"invalid job_type: {self.job_type}")

        if self.source_button not in ALLOWED_SOURCE_BUTTONS:
            raise ValueError(f"invalid source_button: {self.source_button}")

        if self.status not in ALLOWED_JOB_STATUS:
            raise ValueError(f"invalid status: {self.status}")

        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise ValueError("job_id must be a non-empty string")

        if not self.safety_telemetry.preview_only:
            raise ValueError("preview_only must default to true for schema jobs")

        mutation_flags = [
            self.safety_telemetry.mutation_performed,
            self.safety_telemetry.queue_write_performed,
            self.safety_telemetry.report_export_approved,
            self.safety_telemetry.durable_write_performed,
            self.safety_telemetry.learning_apply_performed,
            self.safety_telemetry.calibration_write_performed,
            self.safety_telemetry.auto_apply_performed,
        ]
        if any(mutation_flags):
            raise ValueError("mutation flags must default false")

        if not self.approval_required.required:
            raise ValueError("approval_required.required must be true by default")

        if self.job_type in PERMANENT_ACTION_JOB_TYPES and not self.approval_required.required:
            raise ValueError(f"permanent action job must require approval: {self.job_type}")

    def to_dict(self) -> Dict[str, Any]:
        """Export the job as a clean, JSON-serializable dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Export the job as a JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)


__all__ = [
    "ALLOWED_JOB_STATUS",
    "ALLOWED_JOB_TYPES",
    "ALLOWED_SOURCE_BUTTONS",
    "PERMANENT_ACTION_JOB_TYPES",
    "LocalAIJob",
    "LocalAIJobApprovalRequirement",
    "LocalAIJobBlockingReason",
    "LocalAIJobInputRef",
    "LocalAIJobOutputPreview",
    "LocalAIJobProvenance",
    "LocalAIJobSafetyTelemetry",
]

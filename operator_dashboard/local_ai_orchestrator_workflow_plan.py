"""Preview-only workflow planner for three-button local AI orchestration.

Builds deterministic LocalAIJob chains for each visible dashboard button while
keeping all actions read-only and approval-gated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import uuid
from typing import Dict, List

from operator_dashboard.local_ai_orchestrator_job_schema import (
    ALLOWED_SOURCE_BUTTONS,
    LocalAIJob,
    LocalAIJobInputRef,
    PERMANENT_ACTION_JOB_TYPES,
)
from operator_dashboard.local_ai_orchestrator_preview_runner import run_preview_job

WORKFLOW_JOB_TYPES_BY_BUTTON: Dict[str, List[str]] = {
    "button1_find_fights": [
        "discovery_job",
        "extraction_job",
        "normalization_job",
        "dedupe_job",
        "ranking_job",
        "queue_candidate_job",
    ],
    "button2_generate_pdfs": [
        "report_generation_job",
        "report_quality_job",
        "pdf_preview_job",
        "delivery_candidate_job",
    ],
    "button3_find_results": [
        "result_search_job",
        "result_match_job",
        "accuracy_comparison_job",
        "calibration_recommendation_job",
    ],
}

GATE_NAME_BY_BUTTON: Dict[str, str] = {
    "button1_find_fights": "Approve Save Fights",
    "button2_generate_pdfs": "Approve Customer PDF Delivery",
    "button3_find_results": "Approve Result Apply / Learning Review",
}


def _deterministic_workflow_id(source_button: str, input_ref: LocalAIJobInputRef) -> str:
    basis = "|".join(
        [
            source_button,
            input_ref.ref_type,
            input_ref.ref_key,
            input_ref.snapshot_hash or "",
        ]
    )
    return f"workflow_{uuid.uuid5(uuid.NAMESPACE_URL, basis).hex}"


@dataclass
class LocalAIWorkflowPreview:
    workflow_id: str
    source_button: str
    jobs: List[LocalAIJob]
    status: str
    gate_required: bool
    gate_name: str
    preview_only: bool = True
    mutation_performed: bool = False
    queue_write_performed: bool = False
    report_export_approved: bool = False
    durable_write_performed: bool = False
    learning_apply_performed: bool = False
    calibration_write_performed: bool = False
    auto_apply_performed: bool = False

    def validate(self) -> None:
        if self.source_button not in ALLOWED_SOURCE_BUTTONS:
            raise ValueError(f"invalid source_button: {self.source_button}")

        expected_jobs = WORKFLOW_JOB_TYPES_BY_BUTTON[self.source_button]
        actual_jobs = [j.job_type for j in self.jobs]
        if actual_jobs != expected_jobs:
            raise ValueError("workflow job order does not match required chain")

        if self.gate_name != GATE_NAME_BY_BUTTON[self.source_button]:
            raise ValueError("gate_name does not match source_button")

        if not self.preview_only:
            raise ValueError("preview_only must remain true")

        mutation_flags = [
            self.mutation_performed,
            self.queue_write_performed,
            self.report_export_approved,
            self.durable_write_performed,
            self.learning_apply_performed,
            self.calibration_write_performed,
            self.auto_apply_performed,
        ]
        if any(mutation_flags):
            raise ValueError("workflow mutation flags must remain false")

        for job in self.jobs:
            if job.source_button != self.source_button:
                raise ValueError("all jobs must retain the workflow source_button")
            if not job.safety_telemetry.preview_only:
                raise ValueError("all jobs must retain preview-only telemetry")
            if job.job_type in PERMANENT_ACTION_JOB_TYPES and not job.approval_required.required:
                raise ValueError("permanent-action candidate job must require approval")

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def build_three_button_workflow_plan(source_button: str, input_ref: LocalAIJobInputRef) -> LocalAIWorkflowPreview:
    """Build a deterministic preview-only workflow plan for one source button."""
    if source_button not in ALLOWED_SOURCE_BUTTONS:
        raise ValueError(f"invalid source_button: {source_button}")

    job_types = WORKFLOW_JOB_TYPES_BY_BUTTON[source_button]
    jobs = [
        LocalAIJob(
            job_type=job_type,
            source_button=source_button,
            input_ref=input_ref,
            status="pending",
        )
        for job_type in job_types
    ]

    plan = LocalAIWorkflowPreview(
        workflow_id=_deterministic_workflow_id(source_button, input_ref),
        source_button=source_button,
        jobs=jobs,
        status="preview_planned",
        gate_required=True,
        gate_name=GATE_NAME_BY_BUTTON[source_button],
    )
    plan.validate()
    return plan


def run_workflow_preview(plan: LocalAIWorkflowPreview) -> LocalAIWorkflowPreview:
    """Run all planned jobs through preview handlers without any permanent actions."""
    plan.validate()
    updated_jobs: List[LocalAIJob] = []
    overall_status = "preview_ready"

    for job in plan.jobs:
        out = run_preview_job(job)
        updated_jobs.append(out)
        if out.status == "failed":
            overall_status = "failed"
            break
        if out.status == "blocked" and overall_status != "failed":
            overall_status = "blocked"

    out_plan = LocalAIWorkflowPreview(
        workflow_id=plan.workflow_id,
        source_button=plan.source_button,
        jobs=updated_jobs,
        status=overall_status,
        gate_required=plan.gate_required,
        gate_name=plan.gate_name,
        preview_only=True,
        mutation_performed=False,
        queue_write_performed=False,
        report_export_approved=False,
        durable_write_performed=False,
        learning_apply_performed=False,
        calibration_write_performed=False,
        auto_apply_performed=False,
    )
    out_plan.validate()
    return out_plan


__all__ = [
    "GATE_NAME_BY_BUTTON",
    "WORKFLOW_JOB_TYPES_BY_BUTTON",
    "LocalAIWorkflowPreview",
    "build_three_button_workflow_plan",
    "run_workflow_preview",
]

"""Safe real-input context packs for three-button local AI preview workflows.

This module builds sanitized, preview-only input_ref payloads for Button 1/2/3.
It performs no writes and no live execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Dict, List

from operator_dashboard.local_ai_orchestrator_job_schema import LocalAIJobInputRef

ALLOWED_SOURCE_BUTTONS = {
    "button1_find_fights",
    "button2_generate_pdfs",
    "button3_find_results",
}

_KIND_BY_SOURCE_BUTTON = {
    "button1_find_fights": "discovery_preview",
    "button2_generate_pdfs": "report_preview",
    "button3_find_results": "result_review_preview",
}


def _sanitize_text(value: Any) -> str:
    return str(value).strip() if isinstance(value, str) else ""


def _sanitize_list(value: Any) -> List[Any]:
    if not isinstance(value, list):
        return []
    return list(value)


def _sanitize_dict(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _sanitize_list_of_dict(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(v) for v in value if isinstance(v, dict)]


@dataclass
class LocalAIInputContextPack:
    source_button: str
    input_ref: Dict[str, Any]
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

        if not isinstance(self.input_ref, dict):
            raise ValueError("input_ref must be a dict")

        expected_kind = _KIND_BY_SOURCE_BUTTON[self.source_button]
        kind = self.input_ref.get("kind", "")
        if kind != expected_kind:
            raise ValueError(f"invalid input_ref.kind for source_button: {self.source_button}")

        payload = self.input_ref.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("input_ref.payload must be a dict")

        if not self.preview_only:
            raise ValueError("preview_only must be true")

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
            raise ValueError("all mutation flags must remain false")

    def to_dict(self) -> Dict[str, Any]:
        self.validate()
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def to_job_input_ref(self) -> LocalAIJobInputRef:
        """Convert to LocalAIJobInputRef for planner/runner usage."""
        self.validate()
        kind = self.input_ref.get("kind", "empty")
        ref_id = self.input_ref.get("ref_id", kind)
        payload = self.input_ref.get("payload", {})
        return LocalAIJobInputRef(
            ref_type=str(kind),
            ref_key=str(ref_id),
            snapshot_hash=None,
            metadata={"payload": payload},
        )


def build_button1_find_fights_context(raw_input: Dict[str, Any] | None = None) -> LocalAIInputContextPack:
    raw = _sanitize_dict(raw_input)
    payload = {
        "manual_text": _sanitize_text(raw.get("manual_text", "")),
        "approved_source_refs": _sanitize_list(raw.get("approved_source_refs", [])),
        "event_hint": _sanitize_text(raw.get("event_hint", "")),
        "promotion_hint": _sanitize_text(raw.get("promotion_hint", "")),
        "date_window": _sanitize_dict(raw.get("date_window", {})),
        "candidate_rows": _sanitize_list_of_dict(raw.get("candidate_rows", [])),
        # Read-only advanced known-record projection context for Button 1 preview.
        "approved_historical_records": _sanitize_list_of_dict(raw.get("approved_historical_records", [])),
        "report_history_records": _sanitize_list_of_dict(raw.get("report_history_records", [])),
        "result_ledger_records": _sanitize_list_of_dict(raw.get("result_ledger_records", [])),
        "global_read_projection_records": _sanitize_list_of_dict(raw.get("global_read_projection_records", [])),
    }

    pack = LocalAIInputContextPack(
        source_button="button1_find_fights",
        input_ref={
            "kind": "discovery_preview",
            "ref_id": _sanitize_text(raw.get("ref_id", "b1_discovery_preview")) or "b1_discovery_preview",
            "payload": payload,
        },
    )
    pack.validate()
    return pack


def build_button2_generate_pdfs_context(raw_input: Dict[str, Any] | None = None) -> LocalAIInputContextPack:
    raw = _sanitize_dict(raw_input)
    payload = {
        "selected_fights": _sanitize_list_of_dict(raw.get("selected_fights", [])),
        "queued_fight_refs": _sanitize_list(raw.get("queued_fight_refs", [])),
        "report_status_refs": _sanitize_list(raw.get("report_status_refs", [])),
        "analysis_ready_refs": _sanitize_list(raw.get("analysis_ready_refs", [])),
        "customer_ready_refs": _sanitize_list(raw.get("customer_ready_refs", [])),
    }

    pack = LocalAIInputContextPack(
        source_button="button2_generate_pdfs",
        input_ref={
            "kind": "report_preview",
            "ref_id": _sanitize_text(raw.get("ref_id", "b2_report_preview")) or "b2_report_preview",
            "payload": payload,
        },
    )
    pack.validate()
    return pack


def build_button3_find_results_context(raw_input: Dict[str, Any] | None = None) -> LocalAIInputContextPack:
    raw = _sanitize_dict(raw_input)
    payload = {
        "waiting_rows": _sanitize_list_of_dict(raw.get("waiting_rows", [])),
        "selected_keys": _sanitize_list(raw.get("selected_keys", [])),
        "result_source_refs": _sanitize_list(raw.get("result_source_refs", [])),
        "report_refs": _sanitize_list(raw.get("report_refs", [])),
        "comparison_refs": _sanitize_list(raw.get("comparison_refs", [])),
        "source_status": _sanitize_dict(raw.get("source_status", {})),
    }

    pack = LocalAIInputContextPack(
        source_button="button3_find_results",
        input_ref={
            "kind": "result_review_preview",
            "ref_id": _sanitize_text(raw.get("ref_id", "b3_result_review_preview")) or "b3_result_review_preview",
            "payload": payload,
        },
    )
    pack.validate()
    return pack


def build_context_pack(source_button: str, raw_input: Dict[str, Any] | None = None) -> LocalAIInputContextPack:
    if source_button == "button1_find_fights":
        return build_button1_find_fights_context(raw_input)
    if source_button == "button2_generate_pdfs":
        return build_button2_generate_pdfs_context(raw_input)
    if source_button == "button3_find_results":
        return build_button3_find_results_context(raw_input)
    raise ValueError(f"invalid source_button: {source_button}")


__all__ = [
    "ALLOWED_SOURCE_BUTTONS",
    "LocalAIInputContextPack",
    "build_button1_find_fights_context",
    "build_button2_generate_pdfs_context",
    "build_button3_find_results_context",
    "build_context_pack",
]

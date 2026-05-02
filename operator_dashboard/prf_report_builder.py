"""
Premium Report Factory Phase 3 – PDF Report Builder

Accepts operator-approved queue records and report type, generates structured
report objects, and exports them to PDF via prf_report_export.

No result lookup, no accuracy comparison, no learning, no web discovery,
no billing, no distribution, no token mutations, no global ledger write,
no scoring rewrite.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone

from operator_dashboard.prf_betting_market_adapter import build_betting_market_enrichment
from operator_dashboard.prf_report_content import build_report_content_bundle
from operator_dashboard.prf_report_export import write_pdf_report, build_report_filename
from operator_dashboard.prf_report_readiness_scaffold import (
    detect_missing_required_sections,
    evaluate_report_readiness_status,
    evaluate_sparse_case_completion,
)

SUPPORTED_REPORT_TYPES = {"single_matchup", "event_card"}
REJECTED_REPORT_TYPES = {"fighter_profile"}
PLACEHOLDER_TOKENS = [
    "unavailable",
    "not available",
    "pending",
    "tbd",
    "no operator notes recorded",
    "insufficient data",
    "content will be enriched later",
    "prediction unavailable",
    "analysis unavailable",
]
QUALITY_REQUIRED_SECTIONS = [
    "headline_prediction",
    "executive_summary",
    "matchup_snapshot",
    "decision_structure",
    "energy_use",
    "fatigue_failure_points",
    "mental_condition",
    "collapse_triggers",
    "deception_and_unpredictability",
    "round_by_round_control_shifts",
    "scenario_tree",
    "risk_warnings",
    "operator_notes",
]

COMBAT_ENGINE_SECTION_MAP = {
    "tactical_keys_engine": [
        "headline_prediction",
        "executive_summary",
        "matchup_snapshot",
        "operator_notes",
    ],
    "decision_structure_engine": [
        "decision_structure",
        "scenario_tree",
        "risk_warnings",
    ],
    "energy_use_engine": [
        "energy_use",
        "round_by_round_control_shifts",
        "risk_warnings",
    ],
    "fatigue_failure_point_engine": [
        "fatigue_failure_points",
        "round_by_round_control_shifts",
        "risk_warnings",
    ],
    "mental_condition_engine": [
        "mental_condition",
        "collapse_triggers",
        "risk_warnings",
    ],
    "collapse_trigger_engine": [
        "collapse_triggers",
        "scenario_tree",
        "risk_warnings",
    ],
    "deception_and_unpredictability_engine": [
        "deception_and_unpredictability",
        "matchup_snapshot",
        "risk_warnings",
    ],
    "dominance_danger_zone_engine": [
        "matchup_snapshot",
        "round_by_round_control_shifts",
        "executive_summary",
    ],
    "round_band_projection_engine": [
        "round_by_round_control_shifts",
        "headline_prediction",
        "scenario_tree",
    ],
    "scenario_tree_method_pathways_engine": [
        "scenario_tree",
        "headline_prediction",
        "executive_summary",
    ],
}

REQUIRED_COMBAT_SECTIONS = tuple(QUALITY_REQUIRED_SECTIONS)


def _compute_report_id(matchup_id: str, report_type: str, generated_at: str) -> str:
    """Deterministic SHA-256 report ID."""
    seed = "{}|{}|{}".format(matchup_id, report_type, generated_at)
    return "prf_r_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _determine_report_status(section_status: dict) -> str:
    """
    Determine report_status from section_status values.
    - 'partial' if any section is blocked
    - 'generated' otherwise (complete or unavailable)
    """
    if "blocked" in set(section_status.values()):
        return "partial"
    return "generated"


def _validate_generated_pdf(file_path: str) -> tuple[bool, str, int, str]:
    """Validate that the export produced a real, non-empty PDF artifact."""
    normalized_path = os.path.abspath(str(file_path or "").strip()) if str(file_path or "").strip() else ""
    if not normalized_path:
        return False, "", 0, "PDF was not created. Check export error."
    if not normalized_path.lower().endswith(".pdf"):
        return False, normalized_path, 0, "Export artifact is not a PDF file."
    if not os.path.exists(normalized_path):
        return False, normalized_path, 0, "PDF was not created. Check export error."
    try:
        size_bytes = os.path.getsize(normalized_path)
    except Exception as exc:
        return False, normalized_path, 0, "Failed to read generated PDF size: {}".format(exc)
    if size_bytes <= 0:
        return False, normalized_path, size_bytes, "Zero-byte PDF file detected. Export failed."
    return True, normalized_path, size_bytes, ""


def _contains_placeholder_text(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return True
    return any(token in normalized for token in PLACEHOLDER_TOKENS)


def _extract_prediction_fields(
    record: dict,
    sections: dict,
    content_preview: dict,
    analysis_source_status: str,
    analysis_source_type: str,
    linked_analysis_record_id: str,
) -> dict:
    """Extract sparse-completion prediction fields from available Button 2 sources."""
    headline = str(sections.get("headline_prediction") or content_preview.get("headline_prediction_preview") or "")
    round_shift = str(sections.get("round_by_round_control_shifts") or "")

    winner = str(record.get("winner") or record.get("predicted_winner") or "").strip()
    method = str(record.get("method") or "").strip()
    confidence = record.get("confidence")
    round_value = str(record.get("round") or "").strip()

    if not winner:
        winner_match = re.search(r"projected winner:\s*([^\.]+)", headline, re.IGNORECASE)
        if winner_match:
            winner = winner_match.group(1).strip()
    if not winner:
        projection_match = re.search(r"final projection is\s+([^\.]+?)\s+by\s+", headline, re.IGNORECASE)
        if projection_match:
            winner = projection_match.group(1).strip()

    if not method:
        method_match = re.search(r"via\s+([A-Za-z\- ]+)", headline, re.IGNORECASE)
        if method_match:
            method = method_match.group(1).strip()
    if not method:
        by_match = re.search(r"\bby\s+([A-Za-z\- ]+)", headline, re.IGNORECASE)
        if by_match:
            method = by_match.group(1).strip()

    if confidence in (None, ""):
        confidence_match = re.search(r"(\d{1,2}(?:\.\d+)?)%", headline)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1)) / 100.0
            except Exception:
                confidence = None
    if confidence in (None, "") and str(analysis_source_status or "").strip().lower() == "found":
        # Linked analysis exists but not all sources expose numeric confidence.
        confidence = 0.5

    if not round_value:
        round_match = re.search(r"round\s*(one|two|three|four|five|\d)", round_shift, re.IGNORECASE)
        if round_match:
            round_value = str(round_match.group(1)).strip()
    if not round_value and str(analysis_source_status or "").strip().lower() == "found":
        round_value = "n/a"

    if str(analysis_source_type or "").strip() == "generated_internal_draft":
        if not winner:
            winner = str(record.get("fighter_a") or "").strip() or "internal_draft_projection"
        if not method:
            method = "decision"
        if confidence in (None, ""):
            confidence = 0.5
        if not round_value:
            round_value = "n/a"

    return {
        "winner": winner,
        "confidence": confidence,
        "method": method,
        "round": round_value,
        "debug_metrics": {
            "analysis_source_status": str(analysis_source_status or "").strip(),
            "linked_analysis_record_id": str(linked_analysis_record_id or "").strip(),
        },
    }


def _build_combat_content_metadata(sections: dict, analysis_source_type: str) -> dict:
    """Build additive Combat Intelligence metadata from existing section outputs."""
    populated_sections = []
    section_source_map = {}
    all_target_sections = set()

    for mapped_sections in COMBAT_ENGINE_SECTION_MAP.values():
        all_target_sections.update(mapped_sections)

    for section_name in sorted(all_target_sections):
        section_text = str(sections.get(section_name) or "")
        populated = not _contains_placeholder_text(section_text)
        if populated:
            populated_sections.append(section_name)
        section_source_map[section_name] = {
            "source_type": str(analysis_source_type or "none").strip(),
            "contributing_engines": [
                engine_name
                for engine_name, mapped_sections in COMBAT_ENGINE_SECTION_MAP.items()
                if section_name in mapped_sections
            ],
            "populated": populated,
        }

    combat_engine_contributions = {}
    missing_engine_outputs = []
    for engine_name, mapped_sections in COMBAT_ENGINE_SECTION_MAP.items():
        contributed_sections = [
            section_name
            for section_name in mapped_sections
            if section_name in populated_sections
        ]
        if not contributed_sections:
            missing_engine_outputs.append(engine_name)
        combat_engine_contributions[engine_name] = {
            "contributed": bool(contributed_sections),
            "sections": contributed_sections,
        }

    missing_required_combat_sections = [
        section_name
        for section_name in REQUIRED_COMBAT_SECTIONS
        if section_name not in populated_sections
    ]

    if len(populated_sections) == len(all_target_sections):
        combat_content_status = "complete"
    elif populated_sections:
        combat_content_status = "partial"
    else:
        combat_content_status = "missing"

    return {
        "combat_engine_contributions": combat_engine_contributions,
        "populated_sections": sorted(populated_sections),
        "missing_engine_outputs": sorted(missing_engine_outputs),
        "combat_content_status": combat_content_status,
        "section_source_map": section_source_map,
        "missing_required_combat_sections": missing_required_combat_sections,
    }


def _evaluate_report_quality(
    report_obj: dict,
    queue_record: dict,
    sections: dict,
    content_preview: dict,
    allow_draft: bool,
    analysis_source_status: str,
    analysis_source_type: str,
) -> tuple[str, bool, list[str], str, str, str]:
    """Evaluate customer-readiness and sparse-completion using scaffold contracts."""
    missing_sections = detect_missing_required_sections(sections)

    fighter_a = str(report_obj.get("fighter_a") or "").strip()
    fighter_b = str(report_obj.get("fighter_b") or "").strip()
    if not fighter_a or not fighter_b:
        if "matchup_snapshot" not in missing_sections:
            missing_sections.append("matchup_snapshot")

    sparse_payload = _extract_prediction_fields(
        queue_record,
        sections,
        content_preview,
        analysis_source_status,
        analysis_source_type,
        str(report_obj.get("linked_analysis_record_id") or "").strip(),
    )
    sparse_result = evaluate_sparse_case_completion(sparse_payload)
    sparse_completion_ready = bool(sparse_result.get("ready"))
    sparse_missing_fields = sparse_result.get("missing_fields") or []

    readiness = evaluate_report_readiness_status(
        analysis_source_status=analysis_source_status,
        allow_draft=allow_draft,
        missing_sections=missing_sections,
        sparse_completion_ready=sparse_completion_ready,
    )

    quality_status = str(readiness.get("report_quality_status") or "blocked_missing_analysis").strip()
    customer_ready = bool(readiness.get("customer_ready"))
    readiness_gate_reason = str(readiness.get("reason_code") or "unknown").strip()

    if str(analysis_source_type or "").strip() == "generated_internal_draft":
        quality_status = "draft_only"
        customer_ready = False
        readiness_gate_reason = "internal_draft_requires_operator_review"

    sparse_completion_status = "complete" if sparse_completion_ready else "incomplete"
    if sparse_completion_ready:
        sparse_completion_reason = "all_sparse_prediction_fields_present"
    else:
        sparse_completion_reason = "missing_fields: {}".format(
            ",".join(str(name) for name in sparse_missing_fields)
        )

    if quality_status == "customer_ready":
        return quality_status, customer_ready, [], "", sparse_completion_status, sparse_completion_reason, readiness_gate_reason

    if quality_status == "draft_only":
        message = "Internal AI-RISA draft requires operator review before customer release."
        if missing_sections:
            message = "Cannot generate customer PDF yet. Analysis data is missing for this matchup."
        if str(analysis_source_type or "").strip() == "generated_internal_draft":
            message = "Internal AI-RISA draft requires operator review before customer release."
        return quality_status, False, missing_sections, message, sparse_completion_status, sparse_completion_reason, readiness_gate_reason

    message = "Cannot generate customer PDF yet. Analysis data is missing for this matchup."
    return "blocked_missing_analysis", False, missing_sections, message, sparse_completion_status, sparse_completion_reason, readiness_gate_reason


def generate_reports(
    queue_records: list,
    report_type: str,
    operator_approval: bool,
    export_format: str,
    notes: str,
    reports_dir: str,
    allow_draft: bool = False,
    betting_analyst_mode: bool = False,
) -> dict:
    """
    Core Phase 3 generation logic.

    Returns the full generate response contract as defined in the locked builder design.
    """
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if not operator_approval:
        return {
            "ok": False,
            "generated_at": generated_at,
            "accepted_count": 0,
            "rejected_count": len(queue_records),
            "generated_reports": [],
            "rejected_reports": [
                {"matchup_id": r.get("matchup_id"), "reason": "operator_approval_required"}
                for r in queue_records
            ],
            "export_summary": {
                "output_folder": reports_dir,
                "total_files": 0,
                "total_size_bytes": 0,
            },
            "warnings": [],
            "errors": ["operator_approval_required"],
        }

    if report_type in REJECTED_REPORT_TYPES:
        return {
            "ok": False,
            "generated_at": generated_at,
            "accepted_count": 0,
            "rejected_count": len(queue_records),
            "generated_reports": [],
            "rejected_reports": [
                {
                    "matchup_id": r.get("matchup_id"),
                    "reason": "report_type_not_supported_in_phase3: {}".format(report_type),
                }
                for r in queue_records
            ],
            "export_summary": {
                "output_folder": reports_dir,
                "total_files": 0,
                "total_size_bytes": 0,
            },
            "warnings": [],
            "errors": ["report_type_not_supported: {}".format(report_type)],
        }

    if report_type not in SUPPORTED_REPORT_TYPES:
        return {
            "ok": False,
            "generated_at": generated_at,
            "accepted_count": 0,
            "rejected_count": len(queue_records),
            "generated_reports": [],
            "rejected_reports": [
                {
                    "matchup_id": r.get("matchup_id"),
                    "reason": "unsupported_report_type: {}".format(report_type),
                }
                for r in queue_records
            ],
            "export_summary": {
                "output_folder": reports_dir,
                "total_files": 0,
                "total_size_bytes": 0,
            },
            "warnings": [],
            "errors": ["unsupported_report_type: {}".format(report_type)],
        }

    generated_reports = []
    rejected_reports = []
    content_preview_rows = []
    warnings = []
    errors = []
    total_size_bytes = 0

    for record in queue_records:
        matchup_id = str(record.get("matchup_id") or "").strip()
        fighter_a = str(record.get("fighter_a") or "").strip()
        fighter_b = str(record.get("fighter_b") or "").strip()
        queue_status = str(record.get("queue_status") or "").strip()

        # Rejection checks
        if not fighter_a or not fighter_b:
            rejected_reports.append({
                "matchup_id": matchup_id,
                "reason": "missing_fighter_names",
            })
            continue

        if queue_status == "needs_review":
            rejected_reports.append({
                "matchup_id": matchup_id,
                "reason": "queue_status_needs_review",
            })
            continue

        # Warnings for missing optional fields
        if not str(record.get("promotion") or "").strip():
            warnings.append("matchup_id={}: missing promotion field".format(matchup_id))
        if not str(record.get("source_reference") or "").strip():
            warnings.append("matchup_id={}: missing source_reference field".format(matchup_id))
        if not str(record.get("event_date") or "").strip():
            warnings.append("matchup_id={}: missing event_date field".format(matchup_id))

        # Merge operator generation notes into record
        record_with_notes = dict(record)
        if notes:
            existing = str(record_with_notes.get("notes") or "").strip()
            if existing:
                record_with_notes["notes"] = "{}\n[Operator generation note: {}]".format(
                    existing, notes
                )
            else:
                record_with_notes["notes"] = notes

        # Assemble sections and content source linkage metadata
        try:
            content_bundle = build_report_content_bundle(
                record_with_notes,
                allow_internal_draft=allow_draft,
            )
            sections = content_bundle.get("sections") or {}
            section_status = content_bundle.get("section_status") or {}
        except Exception as exc:
            err_msg = "section assembly error: {}".format(exc)
            errors.append("matchup_id={}: {}".format(matchup_id, err_msg))
            rejected_reports.append({"matchup_id": matchup_id, "reason": err_msg})
            continue

        analysis_source_status = str(content_bundle.get("analysis_source_status") or "not_found").strip()
        analysis_source_type = str(content_bundle.get("analysis_source_type") or "none").strip()
        linked_analysis_record_id = str(content_bundle.get("linked_analysis_record_id") or "").strip()
        content_preview = content_bundle.get("content_preview") or {}

        event_id = str(record.get("event_id") or "unknown").strip()
        file_name = build_report_filename(event_id, matchup_id)

        report_obj = {
            "report_id": _compute_report_id(matchup_id, report_type, generated_at),
            "matchup_id": matchup_id,
            "event_id": event_id,
            "fighter_a": fighter_a,
            "fighter_b": fighter_b,
            "event_name": str(record.get("event_name") or "").strip(),
            "event_date": str(record.get("event_date") or "").strip(),
            "promotion": str(record.get("promotion") or "").strip(),
            "report_type": report_type,
            "report_status": "pending",
            "export_format": "pdf",
            "file_name": file_name,
            "file_path": None,
            "generated_pdf_exists": False,
            "generated_pdf_path": "",
            "generated_pdf_size_bytes": 0,
            "generated_pdf_openable": False,
            "report_quality_status": "blocked_missing_analysis",
            "customer_ready": False,
            "missing_sections": [],
            "sparse_completion_status": "incomplete",
            "sparse_completion_reason": "not_evaluated",
            "readiness_gate_reason": "not_evaluated",
            "quality_message": "",
            "export_error": "",
            "generated_at": generated_at,
            "section_status": section_status,
            "source_reference": str(record.get("source_reference") or "").strip(),
            "operator_notes": record_with_notes.get("notes") or "",
            "analysis_source_status": analysis_source_status,
            "analysis_source_type": analysis_source_type,
            "linked_analysis_record_id": linked_analysis_record_id,
            "content_preview": content_preview,
            "combat_engine_contributions": {},
            "populated_sections": [],
            "missing_engine_outputs": [],
            "combat_content_status": "missing",
            "section_source_map": {},
        }

        if betting_analyst_mode:
            betting_enrichment = build_betting_market_enrichment(
                queue_record=record_with_notes,
                report_obj=report_obj,
                sections=sections,
            )
            report_obj.update(betting_enrichment)

        quality_status, customer_ready, missing_sections, quality_message, sparse_completion_status, sparse_completion_reason, readiness_gate_reason = _evaluate_report_quality(
            report_obj,
            record_with_notes,
            sections,
            content_preview,
            allow_draft=allow_draft,
            analysis_source_status=analysis_source_status,
            analysis_source_type=analysis_source_type,
        )

        combat_metadata = _build_combat_content_metadata(sections, analysis_source_type)
        missing_sections = sorted(
            set(missing_sections + list(combat_metadata.get("missing_required_combat_sections") or []))
        )

        # Customer-ready cannot pass when required combat section content is unavailable.
        if quality_status == "customer_ready" and missing_sections:
            quality_status = "blocked_missing_analysis"
            customer_ready = False
            readiness_gate_reason = "missing_required_combat_outputs"
            quality_message = "Cannot generate customer PDF yet. Combat intelligence outputs are missing for this matchup."

        report_obj["report_quality_status"] = quality_status
        report_obj["customer_ready"] = customer_ready
        report_obj["missing_sections"] = missing_sections
        report_obj["sparse_completion_status"] = sparse_completion_status
        report_obj["sparse_completion_reason"] = sparse_completion_reason
        report_obj["readiness_gate_reason"] = readiness_gate_reason
        report_obj["quality_message"] = quality_message
        report_obj["combat_engine_contributions"] = combat_metadata["combat_engine_contributions"]
        report_obj["populated_sections"] = combat_metadata["populated_sections"]
        report_obj["missing_engine_outputs"] = combat_metadata["missing_engine_outputs"]
        report_obj["combat_content_status"] = combat_metadata["combat_content_status"]
        report_obj["section_source_map"] = combat_metadata["section_source_map"]

        content_preview_rows.append({
            "matchup_id": matchup_id,
            "analysis_source_status": analysis_source_status,
            "analysis_source_type": analysis_source_type,
            "linked_analysis_record_id": linked_analysis_record_id,
            "report_quality_status": quality_status,
            "missing_sections": missing_sections,
            "sparse_completion_status": sparse_completion_status,
            "sparse_completion_reason": sparse_completion_reason,
            "readiness_gate_reason": readiness_gate_reason,
            "combat_engine_contributions": combat_metadata["combat_engine_contributions"],
            "populated_sections": combat_metadata["populated_sections"],
            "missing_engine_outputs": combat_metadata["missing_engine_outputs"],
            "combat_content_status": combat_metadata["combat_content_status"],
            "section_source_map": combat_metadata["section_source_map"],
            "headline_prediction_preview": str(content_preview.get("headline_prediction_preview") or ""),
            "executive_summary_preview": str(content_preview.get("executive_summary_preview") or ""),
            "operator_approval_state": bool(operator_approval),
        })

        if betting_analyst_mode:
            content_preview_rows[-1].update(
                {
                    key: report_obj.get(key)
                    for key in (
                        "betting_market_status",
                        "odds_source_status",
                        "implied_probability",
                        "fair_price_estimate",
                        "market_edge_summary",
                        "prop_market_notes",
                        "volatility_grade",
                        "round_band_betting_path",
                        "pass_no_bet_conditions",
                        "betting_risk_disclaimer",
                        "betting_engine_contributions",
                        "betting_missing_inputs",
                    )
                }
            )

        if quality_status == "blocked_missing_analysis":
            errors.append("matchup_id={}: {}".format(matchup_id, quality_message))
            rejected_reports.append({
                "matchup_id": matchup_id,
                "reason": quality_message,
                "report_quality_status": quality_status,
                "customer_ready": customer_ready,
                "missing_sections": missing_sections,
                "sparse_completion_status": sparse_completion_status,
                "sparse_completion_reason": sparse_completion_reason,
                "readiness_gate_reason": readiness_gate_reason,
                "combat_engine_contributions": combat_metadata["combat_engine_contributions"],
                "populated_sections": combat_metadata["populated_sections"],
                "missing_engine_outputs": combat_metadata["missing_engine_outputs"],
                "combat_content_status": combat_metadata["combat_content_status"],
                "section_source_map": combat_metadata["section_source_map"],
                "generated_pdf_path": "",
                "generated_pdf_size_bytes": 0,
                "export_error": quality_message,
                "analysis_source_status": analysis_source_status,
                "analysis_source_type": analysis_source_type,
                "linked_analysis_record_id": linked_analysis_record_id,
            })
            if betting_analyst_mode:
                rejected_reports[-1].update(
                    {
                        key: report_obj.get(key)
                        for key in (
                            "betting_market_status",
                            "odds_source_status",
                            "implied_probability",
                            "fair_price_estimate",
                            "market_edge_summary",
                            "prop_market_notes",
                            "volatility_grade",
                            "round_band_betting_path",
                            "pass_no_bet_conditions",
                            "betting_risk_disclaimer",
                            "betting_engine_contributions",
                            "betting_missing_inputs",
                        )
                    }
                )
            continue

        if quality_status == "draft_only":
            warnings.append("matchup_id={}: {}".format(matchup_id, quality_message))

        # Export PDF
        export_result = write_pdf_report(report_obj, sections, reports_dir)

        if export_result.get("ok"):
            valid_pdf, generated_pdf_path, pdf_size_bytes, pdf_error = _validate_generated_pdf(
                export_result.get("file_path")
            )
            report_obj["file_path"] = generated_pdf_path or export_result.get("file_path")
            report_obj["generated_pdf_exists"] = valid_pdf
            report_obj["generated_pdf_path"] = generated_pdf_path
            report_obj["generated_pdf_size_bytes"] = pdf_size_bytes
            report_obj["generated_pdf_openable"] = valid_pdf
            report_obj["export_error"] = pdf_error

            if valid_pdf:
                total_size_bytes += pdf_size_bytes
                report_obj["report_status"] = _determine_report_status(section_status)
                generated_reports.append(report_obj)
            else:
                report_obj["report_status"] = "failed"
                errors.append("matchup_id={}: export failed: {}".format(matchup_id, pdf_error))
                rejected_reports.append({
                    "matchup_id": matchup_id,
                    "reason": "export_failed: {}".format(pdf_error),
                })
        else:
            error_msg = export_result.get("error") or "unknown export error"
            errors.append("matchup_id={}: export failed: {}".format(matchup_id, error_msg))
            report_obj["report_status"] = "failed"
            report_obj["file_name"] = export_result.get("file_name") or file_name
            report_obj["export_error"] = error_msg
            rejected_reports.append({
                "matchup_id": matchup_id,
                "reason": "export_failed: {}".format(error_msg),
            })

    accepted_count = len(generated_reports)
    rejected_count = len(rejected_reports)

    return {
        "ok": accepted_count > 0,
        "generated_at": generated_at,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "generated_reports": generated_reports,
        "rejected_reports": rejected_reports,
        "content_preview_rows": content_preview_rows,
        "export_summary": {
            "output_folder": reports_dir,
            "total_files": accepted_count,
            "total_size_bytes": total_size_bytes,
        },
        "warnings": warnings,
        "errors": errors,
    }


def list_generated_reports(reports_dir: str) -> dict:
    """
    List all generated PDF reports in the reports directory with metadata.
    Reads companion metadata files written alongside PDFs.
    """
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    warnings = []
    errors = []
    reports = []

    if not os.path.isdir(reports_dir):
        return {
            "ok": True,
            "generated_at": generated_at,
            "reports": [],
            "total_count": 0,
            "warnings": ["reports_dir_not_found: {}".format(reports_dir)],
            "errors": [],
        }

    try:
        entries = os.listdir(reports_dir)
    except Exception as exc:
        return {
            "ok": False,
            "generated_at": generated_at,
            "reports": [],
            "total_count": 0,
            "warnings": [],
            "errors": ["failed_to_list_reports_dir: {}".format(exc)],
        }

    for name in sorted(entries):
        if not name.endswith(".pdf"):
            continue
        file_path = os.path.join(reports_dir, name)
        meta_path = file_path + ".meta.json"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
                if isinstance(meta, dict):
                    reports.append(meta)
                    continue
            except Exception as exc:
                warnings.append("meta_read_error for {}: {}".format(name, exc))
        # No metadata — report file only
        size_bytes = 0
        try:
            size_bytes = os.path.getsize(file_path)
        except Exception as exc:
            warnings.append("stat_error for {}: {}".format(name, exc))
        reports.append({
            "file_name": name,
            "file_path": file_path,
            "report_status": "generated" if size_bytes > 0 else "failed",
            "generated_pdf_exists": size_bytes > 0,
            "generated_pdf_path": file_path,
            "generated_pdf_size_bytes": size_bytes,
            "generated_pdf_openable": size_bytes > 0,
            "report_quality_status": "unknown",
            "customer_ready": False,
            "missing_sections": [],
            "quality_message": "",
            "export_error": "" if size_bytes > 0 else "Zero-byte PDF file detected. Export failed.",
        })

    return {
        "ok": True,
        "generated_at": generated_at,
        "reports": reports,
        "total_count": len(reports),
        "warnings": warnings,
        "errors": errors,
    }

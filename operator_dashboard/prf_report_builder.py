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
from datetime import datetime, timezone

from operator_dashboard.prf_report_content import assemble_report_sections
from operator_dashboard.prf_report_export import write_pdf_report, build_report_filename

SUPPORTED_REPORT_TYPES = {"single_matchup", "event_card"}
REJECTED_REPORT_TYPES = {"fighter_profile"}


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


def generate_reports(
    queue_records: list,
    report_type: str,
    operator_approval: bool,
    export_format: str,
    notes: str,
    reports_dir: str,
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

        # Assemble sections
        try:
            sections, section_status = assemble_report_sections(record_with_notes)
        except Exception as exc:
            err_msg = "section assembly error: {}".format(exc)
            errors.append("matchup_id={}: {}".format(matchup_id, err_msg))
            rejected_reports.append({"matchup_id": matchup_id, "reason": err_msg})
            continue

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
            "generated_at": generated_at,
            "section_status": section_status,
            "source_reference": str(record.get("source_reference") or "").strip(),
            "operator_notes": record_with_notes.get("notes") or "",
        }

        # Export PDF
        export_result = write_pdf_report(report_obj, sections, reports_dir)

        if export_result.get("ok"):
            file_path = export_result["file_path"]
            try:
                total_size_bytes += os.path.getsize(file_path)
            except Exception:
                pass
            report_obj["report_status"] = _determine_report_status(section_status)
            report_obj["file_path"] = file_path
            generated_reports.append(report_obj)
        else:
            error_msg = export_result.get("error") or "unknown export error"
            errors.append("matchup_id={}: export failed: {}".format(matchup_id, error_msg))
            report_obj["report_status"] = "failed"
            report_obj["file_name"] = export_result.get("file_name") or file_name
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
        reports.append({
            "file_name": name,
            "file_path": file_path,
            "report_status": "generated",
        })

    return {
        "ok": True,
        "generated_at": generated_at,
        "reports": reports,
        "total_count": len(reports),
        "warnings": warnings,
        "errors": errors,
    }

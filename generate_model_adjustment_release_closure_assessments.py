"""
generate_model_adjustment_release_closure_assessments.py

v4.5-slice-1 — Read-only controlled release closure-assessment generator.

Builds a canonical per-proposal release closure assessment that determines
whether a release path is still theoretically open, structurally blocked,
or effectively closed under current governance constraints.

Hard rules:
- no execution
- no auto-promotion
- no config writes
- no model mutation
- no upstream governance artifact mutation
"""

import json
import os
import sys
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "ops", "model_adjustments")

SOURCE_PATHS = {
    "model_adjustment_release_dependency_matrix_json":
        "ops/model_adjustments/model_adjustment_release_dependency_matrix.json",
    "model_adjustment_release_resolution_requirements_json":
        "ops/model_adjustments/model_adjustment_release_resolution_requirements.json",
    "model_adjustment_release_ineligibility_register_json":
        "ops/model_adjustments/model_adjustment_release_ineligibility_register.json",
    "model_adjustment_release_blocker_registry_json":
        "ops/model_adjustments/model_adjustment_release_blocker_registry.json",
    "model_adjustment_release_prohibition_matrix_json":
        "ops/model_adjustments/model_adjustment_release_prohibition_matrix.json",
    "model_adjustment_execution_release_conditions_json":
        "ops/model_adjustments/model_adjustment_execution_release_conditions.json",
    "model_adjustment_execution_release_authority_json":
        "ops/model_adjustments/model_adjustment_execution_release_authority.json",
    "model_adjustment_execution_release_gate_assessments_json":
        "ops/model_adjustments/model_adjustment_execution_release_gate_assessments.json",
    "model_adjustment_execution_release_decisions_json":
        "ops/model_adjustments/model_adjustment_execution_release_decisions.json",
}

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_closure_assessments.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_closure_assessments.md")

VERSION = "v4.5-slice-1"
EXPECTED_RECORD_COUNT = 4


def abs_path(rel_path: str) -> str:
    return os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))


def load_json(rel_path: str):
    with open(abs_path(rel_path), "r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def load_source(source_key: str):
    rel_path = SOURCE_PATHS[source_key]
    try:
        return load_json(rel_path), None
    except Exception as exc:
        return None, str(exc)


def first_by_proposal(records: list, proposal_id: str) -> dict:
    for record in records:
        if record.get("proposal_id") == proposal_id:
            return record
    return {}


def dedup_sorted(values) -> list:
    return sorted(set(str(value) for value in (values or []) if value))


def classify_closure(dep_record: dict) -> tuple[str, str, str]:
    unsatisfiable_count = len(dep_record.get("unsatisfiable_without_resolution", []))
    downstream_count = len(dep_record.get("downstream_blockers", []))
    dependency_state = dep_record.get("dependency_state", "")

    if unsatisfiable_count > 0 and dependency_state == "structurally_closed":
        return (
            "effectively_closed",
            "structurally_blocked_by_dependency_chain",
            "structural_dependency_closure_prevents_release_under_current_governance_conditions",
        )

    if downstream_count > 0:
        return (
            "structurally_blocked",
            "blocked_by_active_dependency_chain",
            "active_blockers_and_dependency_edges_keep_release_path_closed",
        )

    return (
        "theoretically_open_but_unresolved",
        "requirements_unresolved_but_not_structurally_closed",
        "release_path_remains_theoretical_pending_resolution_of_open_requirements",
    )


def build_structural_drivers(dep_record: dict, rr_record: dict, inelig_record: dict) -> list:
    drivers = []
    drivers.extend(dep_record.get("unsatisfiable_without_resolution", []))
    drivers.extend(dep_record.get("upstream_blockers", []))
    drivers.extend(inelig_record.get("active_release_ineligibility_conditions", []))
    if rr_record.get("required_resolution_path"):
        drivers.append(f"required_resolution_path:{rr_record['required_resolution_path']}")
    return dedup_sorted(drivers)


def build_theoretical_open_items(dep_record: dict, rr_record: dict) -> list:
    theoretical = []
    theoretical.extend(rr_record.get("required_resolutions", []))
    theoretical.extend(dep_record.get("required_remaining_actions", []))
    return dedup_sorted(theoretical)


def build_blocked_dependencies(dep_record: dict) -> list:
    blocked = []
    blocked.extend(dep_record.get("dependency_edges", []))
    blocked.extend(dep_record.get("dependency_chain", []))
    return dedup_sorted(blocked)


def build_records(
    dep_data: dict,
    rr_data: dict,
    inelig_data: dict,
    blocker_data: dict,
    prohibition_data: dict,
    cond_data: dict,
    auth_data: dict,
    gate_data: dict,
    dec_data: dict,
) -> list:
    dep_records = sorted(
        dep_data.get("release_dependency_matrix", []),
        key=lambda item: item.get("release_dependency_matrix_id", ""),
    )
    rr_records = rr_data.get("release_resolution_requirements", [])
    inelig_records = inelig_data.get("release_ineligibility_register", [])
    blocker_records = blocker_data.get("release_blocker_registry", [])
    prohibition_records = prohibition_data.get("release_prohibition_matrix", [])
    cond_records = cond_data.get("execution_release_conditions", [])
    auth_records = auth_data.get("execution_release_authority", [])
    gate_records = gate_data.get("execution_release_gate_assessments", [])
    dec_records = dec_data.get("execution_release_decisions", [])

    output = []
    for index, dep_record in enumerate(dep_records, start=1):
        proposal_id = dep_record.get("proposal_id", "")
        rr_record = first_by_proposal(rr_records, proposal_id)
        inelig_record = first_by_proposal(inelig_records, proposal_id)
        blocker_record = first_by_proposal(blocker_records, proposal_id)
        prohibition_record = first_by_proposal(prohibition_records, proposal_id)
        cond_record = first_by_proposal(cond_records, proposal_id)
        auth_record = first_by_proposal(auth_records, proposal_id)
        gate_record = first_by_proposal(gate_records, proposal_id)
        dec_record = first_by_proposal(dec_records, proposal_id)

        closure_state, closure_classification, closure_reason = classify_closure(dep_record)

        output.append(
            {
                "release_closure_assessment_id": f"release-closure-assessment-{index:04d}",
                "proposal_id": proposal_id,
                "release_dependency_matrix_id": dep_record.get("release_dependency_matrix_id", ""),
                "release_resolution_requirement_id": dep_record.get("release_resolution_requirement_id", ""),
                "release_condition_id": dep_record.get("release_condition_id", ""),
                "release_authority_id": dep_record.get("release_authority_id", ""),
                "release_gate_id": dep_record.get("release_gate_id", ""),
                "release_decision_id": dep_record.get("release_decision_id", ""),
                "release_ineligibility_id": dep_record.get("release_ineligibility_id", ""),
                "release_blocker_id": dep_record.get("release_blocker_id", ""),
                "release_prohibition_id": dep_record.get("release_prohibition_id", ""),
                "closure_state": closure_state,
                "closure_classification": closure_classification,
                "closure_reason": closure_reason,
                "structural_closure_drivers": build_structural_drivers(dep_record, rr_record, inelig_record),
                "unresolved_but_theoretical_requirements": build_theoretical_open_items(dep_record, rr_record),
                "structurally_blocked_dependencies": build_blocked_dependencies(dep_record),
                "required_release_evidence": dedup_sorted(dep_record.get("required_release_evidence", [])),
                "required_release_authority": dep_record.get("required_release_authority", ""),
                "required_operator_role": dep_record.get("required_operator_role", ""),
                "rollback_reference": dep_record.get("rollback_reference", ""),
                "closure_notes": (
                    "v4_5_governance_only_release_closure_assessment"
                    "_tracks_effective_release_closure_no_execution_or_model_mutation"
                ),
                "source_paths": {key: value for key, value in SOURCE_PATHS.items()},
                "currently_unresolved_items": dedup_sorted(dep_record.get("currently_unresolved_items", [])),
                "release_blocker_refs": dedup_sorted(dep_record.get("release_blocker_refs", [])),
                "release_prohibition_refs": dedup_sorted(dep_record.get("release_prohibition_refs", [])),
                "required_signoff_chain": dedup_sorted(auth_record.get("required_signoff_chain", [])),
                "required_gate_evidence": dedup_sorted(gate_record.get("required_gate_evidence", [])),
                "required_remaining_actions": dedup_sorted(dec_record.get("required_remaining_actions", [])),
                "currently_unmet_release_conditions": dedup_sorted(
                    cond_record.get("currently_unmet_release_conditions", [])
                ),
                "required_resolution_path": inelig_record.get("required_resolution_path", ""),
            }
        )

    return output


def build_summary(records: list, source_total: int) -> dict:
    proposals_covered = len({record.get("proposal_id") for record in records})
    states = sorted({record.get("closure_state", "") for record in records})
    state_counts = {
        state: sum(1 for record in records if record.get("closure_state") == state)
        for state in states
    }
    classifications = sorted({record.get("closure_classification", "") for record in records})
    classification_counts = {
        classification: sum(
            1 for record in records if record.get("closure_classification") == classification
        )
        for classification in classifications
    }

    return {
        "total_proposals_in_source": source_total,
        "total_release_closure_assessment_records": len(records),
        "proposals_covered": proposals_covered,
        "all_proposals_covered": proposals_covered == source_total,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "closure_state_counts": state_counts,
        "closure_classification_counts": classification_counts,
        "deterministic_ordering": True,
    }


def build_source_versions(
    dep_data: dict,
    rr_data: dict,
    inelig_data: dict,
    blocker_data: dict,
    prohibition_data: dict,
    cond_data: dict,
    auth_data: dict,
    gate_data: dict,
    dec_data: dict,
) -> dict:
    return {
        "model_adjustment_release_dependency_matrix_version": dep_data.get(
            "model_adjustment_release_dependency_matrix_version", ""
        ),
        "model_adjustment_release_resolution_requirements_version": rr_data.get(
            "model_adjustment_release_resolution_requirements_version", ""
        ),
        "model_adjustment_release_ineligibility_register_version": inelig_data.get(
            "model_adjustment_release_ineligibility_register_version", ""
        ),
        "model_adjustment_release_blocker_registry_version": blocker_data.get(
            "model_adjustment_release_blocker_registry_version", ""
        ),
        "model_adjustment_release_prohibition_matrix_version": prohibition_data.get(
            "model_adjustment_release_prohibition_matrix_version", ""
        ),
        "model_adjustment_execution_release_conditions_version": cond_data.get(
            "model_adjustment_execution_release_conditions_version", ""
        ),
        "model_adjustment_execution_release_authority_version": auth_data.get(
            "model_adjustment_execution_release_authority_version", ""
        ),
        "model_adjustment_execution_release_gate_assessments_version": gate_data.get(
            "model_adjustment_execution_release_gate_assessments_version", ""
        ),
        "model_adjustment_execution_release_decisions_version": dec_data.get(
            "model_adjustment_execution_release_decisions_version", ""
        ),
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Closure Assessments",
        "",
        f"**Version**: {VERSION}",
        f"**Generated At (UTC)**: {generated_at}",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")

    lines.extend(["", "## Source Versions", "", "| Source | Version |", "|---|---|"])
    for key, value in source_versions.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    for record in records:
        lines.append(f"## {record['release_closure_assessment_id']}")
        lines.append("")
        lines.append(f"- proposal_id: {record['proposal_id']}")
        lines.append(f"- release_dependency_matrix_id: {record['release_dependency_matrix_id']}")
        lines.append(f"- release_resolution_requirement_id: {record['release_resolution_requirement_id']}")
        lines.append(f"- closure_state: {record['closure_state']}")
        lines.append(f"- closure_classification: {record['closure_classification']}")
        lines.append(f"- closure_reason: {record['closure_reason']}")
        lines.append(f"- required_release_authority: {record['required_release_authority']}")
        lines.append(f"- required_operator_role: {record['required_operator_role']}")
        lines.append(f"- rollback_reference: {record['rollback_reference']}")
        lines.append("")

        for section in [
            "structural_closure_drivers",
            "unresolved_but_theoretical_requirements",
            "structurally_blocked_dependencies",
            "required_release_evidence",
            "currently_unresolved_items",
        ]:
            lines.append(f"### {section}")
            lines.append("")
            values = record.get(section, [])
            if values:
                for value in values:
                    lines.append(f"- {value}")
            else:
                lines.append("- none")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as file_handle:
        file_handle.write("\n".join(lines))


def main():
    errors = {}

    dep_data, errors["model_adjustment_release_dependency_matrix_json"] = load_source(
        "model_adjustment_release_dependency_matrix_json"
    )
    rr_data, errors["model_adjustment_release_resolution_requirements_json"] = load_source(
        "model_adjustment_release_resolution_requirements_json"
    )
    inelig_data, errors["model_adjustment_release_ineligibility_register_json"] = load_source(
        "model_adjustment_release_ineligibility_register_json"
    )
    blocker_data, errors["model_adjustment_release_blocker_registry_json"] = load_source(
        "model_adjustment_release_blocker_registry_json"
    )
    prohibition_data, errors["model_adjustment_release_prohibition_matrix_json"] = load_source(
        "model_adjustment_release_prohibition_matrix_json"
    )
    cond_data, errors["model_adjustment_execution_release_conditions_json"] = load_source(
        "model_adjustment_execution_release_conditions_json"
    )
    auth_data, errors["model_adjustment_execution_release_authority_json"] = load_source(
        "model_adjustment_execution_release_authority_json"
    )
    gate_data, errors["model_adjustment_execution_release_gate_assessments_json"] = load_source(
        "model_adjustment_execution_release_gate_assessments_json"
    )
    dec_data, errors["model_adjustment_execution_release_decisions_json"] = load_source(
        "model_adjustment_execution_release_decisions_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    records = build_records(
        dep_data,
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        cond_data,
        auth_data,
        gate_data,
        dec_data,
    )
    source_total = len(dep_data.get("release_dependency_matrix", []))
    summary = build_summary(records, source_total)
    source_versions = build_source_versions(
        dep_data,
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        cond_data,
        auth_data,
        gate_data,
        dec_data,
    )
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_closure_assessments_version": VERSION,
        "release_closure_assessments_summary": summary,
        "release_closure_assessments": records,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(records, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"release_closure_assessments={summary['total_release_closure_assessment_records']} "
        f"proposals_covered={summary['proposals_covered']} "
        f"all_covered={summary['all_proposals_covered']} "
        f"record_count_matches_expected={summary['record_count_matches_expected']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"closure_state={summary['closure_state_counts']}"
    )


if __name__ == "__main__":
    main()
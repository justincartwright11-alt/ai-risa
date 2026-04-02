"""
generate_model_adjustment_release_finality_decisions.py

v4.6-slice-1 — Read-only controlled release finality-decision generator.

Builds a canonical per-proposal finality verdict that consolidates the current
governance posture into a final release finality state/class/reason.

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
    "model_adjustment_release_closure_assessments_json":
        "ops/model_adjustments/model_adjustment_release_closure_assessments.json",
    "model_adjustment_release_resolution_requirements_json":
        "ops/model_adjustments/model_adjustment_release_resolution_requirements.json",
    "model_adjustment_release_ineligibility_register_json":
        "ops/model_adjustments/model_adjustment_release_ineligibility_register.json",
    "model_adjustment_release_blocker_registry_json":
        "ops/model_adjustments/model_adjustment_release_blocker_registry.json",
    "model_adjustment_release_prohibition_matrix_json":
        "ops/model_adjustments/model_adjustment_release_prohibition_matrix.json",
    "model_adjustment_execution_release_decisions_json":
        "ops/model_adjustments/model_adjustment_execution_release_decisions.json",
    "model_adjustment_execution_release_gate_assessments_json":
        "ops/model_adjustments/model_adjustment_execution_release_gate_assessments.json",
    "model_adjustment_execution_release_authority_json":
        "ops/model_adjustments/model_adjustment_execution_release_authority.json",
    "model_adjustment_execution_release_conditions_json":
        "ops/model_adjustments/model_adjustment_execution_release_conditions.json",
}

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_finality_decisions.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_finality_decisions.md")

VERSION = "v4.6-slice-1"
EXPECTED_RECORD_COUNT = 4

KNOWN_CLOSURE_STATES = frozenset({
    "effectively_closed",
    "structurally_closed",
    "theoretically_open",
})

KNOWN_FINALITY_STATES = frozenset({
    "governance_final_no_release",
    "structurally_closed",
    "temporarily_closed",
})

REQUIRED_CLOSURE_RECORD_FIELDS = (
    "proposal_id",
    "release_closure_assessment_id",
    "closure_state",
    "closure_classification",
    "release_blocker_refs",
    "release_prohibition_refs",
    "structural_closure_drivers",
    "structurally_blocked_dependencies",
)


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


def validate_closure_record(record: dict, index: int) -> None:
    """Fail-closed: raises ValueError on missing or empty required fields."""
    for field in REQUIRED_CLOSURE_RECORD_FIELDS:
        if field not in record:
            raise ValueError(
                f"closure record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )
    if not record.get("proposal_id"):
        raise ValueError(
            f"closure record[{index}] has empty proposal_id; "
            "fail-closed — manual review required"
        )
    if not record.get("release_closure_assessment_id"):
        raise ValueError(
            f"closure record[{index}] has empty release_closure_assessment_id; "
            "fail-closed — manual review required"
        )
    if record.get("closure_state", "") not in KNOWN_CLOSURE_STATES:
        raise ValueError(
            f"closure record[{index}] unrecognized closure_state={record.get('closure_state')!r}; "
            "fail-closed — manual review required"
        )


def validate_records(records: list) -> None:
    """Structural assertions on fully built output records before any write."""
    decision_ids = [record["release_finality_decision_id"] for record in records]
    if len(decision_ids) != len(set(decision_ids)):
        raise ValueError("duplicate release_finality_decision_id in output; fail-closed")

    proposal_ids = [record["proposal_id"] for record in records]
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValueError("duplicate proposal_id in output records; fail-closed")

    if len(records) != EXPECTED_RECORD_COUNT:
        raise ValueError(
            f"record count {len(records)} does not match "
            f"EXPECTED_RECORD_COUNT={EXPECTED_RECORD_COUNT}; fail-closed"
        )

    for record in records:
        state = record.get("release_finality_state", "")
        if state not in KNOWN_FINALITY_STATES:
            raise ValueError(
                f"unrecognized release_finality_state={state!r} for proposal "
                f"{record.get('proposal_id')!r}; fail-closed"
            )
        for field in (
            "required_remaining_resolutions",
            "release_blocker_refs",
            "release_prohibition_refs",
        ):
            values = record.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate entries in {field!r} for proposal "
                    f"{record.get('proposal_id')!r}; fail-closed"
                )


def classify_finality(closure_record: dict, blocker_record: dict, prohibition_record: dict):
    closure_state = closure_record.get("closure_state", "")
    if closure_state not in KNOWN_CLOSURE_STATES:
        raise ValueError(
            f"classify_finality: unrecognized closure_state={closure_state!r}; "
            "fail-closed — manual review required"
        )
    blocked_dependencies = len(closure_record.get("structurally_blocked_dependencies", []))
    blocker_refs = len(closure_record.get("release_blocker_refs", []))
    prohibition_refs = len(closure_record.get("release_prohibition_refs", []))

    if closure_state == "effectively_closed" and prohibition_refs > 0:
        return (
            "governance_final_no_release",
            "governance_terminal_closure",
            "governance_closure_and_prohibition_posture_make_release_finally_non_releasable",
        )

    if closure_state == "effectively_closed" and (blocked_dependencies > 0 or blocker_refs > 0):
        return (
            "structurally_closed",
            "structural_dependency_terminal_closure",
            "dependency_chain_and_active_blockers_keep_release_structurally_closed",
        )

    return (
        "temporarily_closed",
        "resolvable_governance_closure",
        "release_is_closed_under_current_conditions_but_remains_theoretically_reopenable_after_resolution",
    )


def build_remaining_resolutions(closure_record: dict, rr_record: dict, dec_record: dict) -> list:
    values = []
    values.extend(rr_record.get("required_resolutions", []))
    values.extend(closure_record.get("unresolved_but_theoretical_requirements", []))
    values.extend(dec_record.get("required_remaining_actions", []))
    return dedup_sorted(values)


def build_records(
    closure_data: dict,
    rr_data: dict,
    inelig_data: dict,
    blocker_data: dict,
    prohibition_data: dict,
    dec_data: dict,
    gate_data: dict,
    auth_data: dict,
    cond_data: dict,
) -> list:
    closure_records = sorted(
        closure_data.get("release_closure_assessments", []),
        key=lambda record: record.get("release_closure_assessment_id", ""),
    )
    rr_records = rr_data.get("release_resolution_requirements", [])
    inelig_records = inelig_data.get("release_ineligibility_register", [])
    blocker_records = blocker_data.get("release_blocker_registry", [])
    prohibition_records = prohibition_data.get("release_prohibition_matrix", [])
    dec_records = dec_data.get("execution_release_decisions", [])
    gate_records = gate_data.get("execution_release_gate_assessments", [])
    auth_records = auth_data.get("execution_release_authority", [])
    cond_records = cond_data.get("execution_release_conditions", [])

    output = []
    for index, closure_record in enumerate(closure_records, start=1):
        validate_closure_record(closure_record, index)
        proposal_id = closure_record.get("proposal_id", "")
        rr_record = first_by_proposal(rr_records, proposal_id)
        inelig_record = first_by_proposal(inelig_records, proposal_id)
        blocker_record = first_by_proposal(blocker_records, proposal_id)
        prohibition_record = first_by_proposal(prohibition_records, proposal_id)
        dec_record = first_by_proposal(dec_records, proposal_id)
        gate_record = first_by_proposal(gate_records, proposal_id)
        auth_record = first_by_proposal(auth_records, proposal_id)
        cond_record = first_by_proposal(cond_records, proposal_id)

        finality_state, finality_class, finality_reason = classify_finality(
            closure_record, blocker_record, prohibition_record
        )

        output.append(
            {
                "release_finality_decision_id": f"release-finality-decision-{index:04d}",
                "proposal_id": proposal_id,
                "release_condition_id": closure_record.get("release_condition_id", ""),
                "release_authority_id": closure_record.get("release_authority_id", ""),
                "release_gate_id": closure_record.get("release_gate_id", ""),
                "release_decision_id": closure_record.get("release_decision_id", ""),
                "release_ineligibility_id": closure_record.get("release_ineligibility_id", ""),
                "release_closure_assessment_id": closure_record.get("release_closure_assessment_id", ""),
                "release_finality_state": finality_state,
                "release_finality_class": finality_class,
                "release_finality_reason": finality_reason,
                "required_remaining_resolutions": build_remaining_resolutions(
                    closure_record, rr_record, dec_record
                ),
                "required_release_authority": closure_record.get("required_release_authority", ""),
                "required_operator_role": closure_record.get("required_operator_role", ""),
                "rollback_reference": closure_record.get("rollback_reference", ""),
                "release_finality_notes": (
                    "v4_6_governance_only_release_finality_decision"
                    "_consolidates_terminal_release_posture_no_execution_or_model_mutation"
                ),
                "source_paths": {key: value for key, value in SOURCE_PATHS.items()},
                "closure_state": closure_record.get("closure_state", ""),
                "closure_classification": closure_record.get("closure_classification", ""),
                "structural_closure_drivers": dedup_sorted(
                    closure_record.get("structural_closure_drivers", [])
                ),
                "release_blocker_refs": dedup_sorted(closure_record.get("release_blocker_refs", [])),
                "release_prohibition_refs": dedup_sorted(
                    closure_record.get("release_prohibition_refs", [])
                ),
                "currently_unresolved_items": dedup_sorted(
                    closure_record.get("currently_unresolved_items", [])
                ),
                "required_release_evidence": dedup_sorted(
                    closure_record.get("required_release_evidence", [])
                ),
                "required_gate_evidence": dedup_sorted(gate_record.get("required_gate_evidence", [])),
                "required_signoff_chain": dedup_sorted(auth_record.get("required_signoff_chain", [])),
                "currently_unmet_release_conditions": dedup_sorted(
                    cond_record.get("currently_unmet_release_conditions", [])
                ),
                "required_resolution_path": inelig_record.get("required_resolution_path", ""),
            }
        )

    return output


def build_summary(records: list, source_total: int) -> dict:
    proposals_covered = len({record.get("proposal_id") for record in records})
    states = sorted({record.get("release_finality_state", "") for record in records})
    state_counts = {
        state: sum(1 for record in records if record.get("release_finality_state") == state)
        for state in states
    }
    classes = sorted({record.get("release_finality_class", "") for record in records})
    class_counts = {
        klass: sum(1 for record in records if record.get("release_finality_class") == klass)
        for klass in classes
    }

    return {
        "total_proposals_in_source": source_total,
        "total_release_finality_decision_records": len(records),
        "proposals_covered": proposals_covered,
        "all_proposals_covered": proposals_covered == source_total,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "release_finality_state_counts": state_counts,
        "release_finality_class_counts": class_counts,
        "deterministic_ordering": True,
    }


def build_source_versions(
    closure_data: dict,
    rr_data: dict,
    inelig_data: dict,
    blocker_data: dict,
    prohibition_data: dict,
    dec_data: dict,
    gate_data: dict,
    auth_data: dict,
    cond_data: dict,
) -> dict:
    return {
        "model_adjustment_release_closure_assessments_version": closure_data.get(
            "model_adjustment_release_closure_assessments_version", ""
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
        "model_adjustment_execution_release_decisions_version": dec_data.get(
            "model_adjustment_execution_release_decisions_version", ""
        ),
        "model_adjustment_execution_release_gate_assessments_version": gate_data.get(
            "model_adjustment_execution_release_gate_assessments_version", ""
        ),
        "model_adjustment_execution_release_authority_version": auth_data.get(
            "model_adjustment_execution_release_authority_version", ""
        ),
        "model_adjustment_execution_release_conditions_version": cond_data.get(
            "model_adjustment_execution_release_conditions_version", ""
        ),
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Finality Decisions",
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
        lines.append(f"## {record['release_finality_decision_id']}")
        lines.append("")
        lines.append(f"- proposal_id: {record['proposal_id']}")
        lines.append(f"- release_closure_assessment_id: {record['release_closure_assessment_id']}")
        lines.append(f"- release_finality_state: {record['release_finality_state']}")
        lines.append(f"- release_finality_class: {record['release_finality_class']}")
        lines.append(f"- release_finality_reason: {record['release_finality_reason']}")
        lines.append(f"- required_release_authority: {record['required_release_authority']}")
        lines.append(f"- required_operator_role: {record['required_operator_role']}")
        lines.append(f"- rollback_reference: {record['rollback_reference']}")
        lines.append("")

        for section in [
            "required_remaining_resolutions",
            "structural_closure_drivers",
            "release_blocker_refs",
            "release_prohibition_refs",
            "required_release_evidence",
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

    closure_data, errors["model_adjustment_release_closure_assessments_json"] = load_source(
        "model_adjustment_release_closure_assessments_json"
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
    dec_data, errors["model_adjustment_execution_release_decisions_json"] = load_source(
        "model_adjustment_execution_release_decisions_json"
    )
    gate_data, errors["model_adjustment_execution_release_gate_assessments_json"] = load_source(
        "model_adjustment_execution_release_gate_assessments_json"
    )
    auth_data, errors["model_adjustment_execution_release_authority_json"] = load_source(
        "model_adjustment_execution_release_authority_json"
    )
    cond_data, errors["model_adjustment_execution_release_conditions_json"] = load_source(
        "model_adjustment_execution_release_conditions_json"
    )

    failures = [key for key, value in errors.items() if value is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    records = build_records(
        closure_data,
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        dec_data,
        gate_data,
        auth_data,
        cond_data,
    )
    validate_records(records)
    source_total = len(closure_data.get("release_closure_assessments", []))
    summary = build_summary(records, source_total)
    source_versions = build_source_versions(
        closure_data,
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        dec_data,
        gate_data,
        auth_data,
        cond_data,
    )
    source_status = {f"{key}_error": errors[key] for key in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_finality_decisions_version": VERSION,
        "release_finality_decisions_summary": summary,
        "release_finality_decisions": records,
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
        f"release_finality_decisions={summary['total_release_finality_decision_records']} "
        f"proposals_covered={summary['proposals_covered']} "
        f"all_covered={summary['all_proposals_covered']} "
        f"record_count_matches_expected={summary['record_count_matches_expected']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"release_finality_state={summary['release_finality_state_counts']}"
    )


if __name__ == "__main__":
    main()
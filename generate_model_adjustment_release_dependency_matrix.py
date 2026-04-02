"""
generate_model_adjustment_release_dependency_matrix.py

v4.4-slice-1 — Read-only controlled release dependency matrix generator.

Builds a canonical per-proposal dependency matrix that captures:
- requirement-to-requirement dependency relationships
- upstream vs downstream blocker influence
- unresolved items that keep requirements unsatisfiable
- structural dependency chains that keep release closed

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

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_dependency_matrix.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustments_release_dependency_matrix.md")
# Keep historical naming alignment for markdown output location.
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_dependency_matrix.md")

VERSION = "v4.4-slice-1"
EXPECTED_RECORD_COUNT = 4


def abs_path(rel_path: str) -> str:
    return os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))


def load_json(rel_path: str):
    with open(abs_path(rel_path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_source(source_key: str):
    rel = SOURCE_PATHS[source_key]
    try:
        return load_json(rel), None
    except Exception as exc:
        return None, str(exc)


def first_by_proposal(records: list, proposal_id: str) -> dict:
    for rec in records:
        if rec.get("proposal_id") == proposal_id:
            return rec
    return {}


def dedup_sorted(items) -> list:
    return sorted(set(str(x) for x in (items or []) if x))


def make_dependency_edges(required_resolutions: list) -> list:
    """Create deterministic linear dependency edges from ordered requirements."""
    edges = []
    for idx in range(len(required_resolutions) - 1):
        left = required_resolutions[idx]
        right = required_resolutions[idx + 1]
        edges.append(f"{left} -> {right}")
    return edges


def classify_upstream_blockers(unresolved_items: list) -> list:
    upstream_prefixes = (
        "authority_",
        "release_authority",
        "release_gate_state",
        "release_decision_state",
        "release_status",
        "release_prohibition_state",
        "release_ineligibility_state",
    )
    return dedup_sorted([i for i in unresolved_items if i.startswith(upstream_prefixes)])


def classify_downstream_blockers(unresolved_items: list) -> list:
    return dedup_sorted([i for i in unresolved_items if i.startswith("blocker-")])


def derive_unsatisfiable_items(unresolved_items: list) -> list:
    unsatisfiable_markers = (
        "structurally_unavailable",
        "structurally_unreleasable",
        "blocked_pending_governance_release",
    )
    out = []
    for item in unresolved_items:
        if any(marker in item for marker in unsatisfiable_markers):
            out.append(item)
    return dedup_sorted(out)


def build_records(
    rr_data,
    inelig_data,
    blocker_data,
    prohibition_data,
    cond_data,
    auth_data,
    gate_data,
    dec_data,
):
    rr_records = rr_data.get("release_resolution_requirements", [])
    inelig_records = inelig_data.get("release_ineligibility_register", [])
    blocker_records = blocker_data.get("release_blocker_registry", [])
    prohibition_records = prohibition_data.get("release_prohibition_matrix", [])
    cond_records = cond_data.get("execution_release_conditions", [])
    auth_records = auth_data.get("execution_release_authority", [])
    gate_records = gate_data.get("execution_release_gate_assessments", [])
    dec_records = dec_data.get("execution_release_decisions", [])

    rr_sorted = sorted(rr_records, key=lambda r: r.get("release_resolution_requirement_id", ""))

    out = []
    for idx, rr in enumerate(rr_sorted, start=1):
        proposal_id = rr.get("proposal_id", "")

        inelig = first_by_proposal(inelig_records, proposal_id)
        blocker = first_by_proposal(blocker_records, proposal_id)
        prohibition = first_by_proposal(prohibition_records, proposal_id)
        cond = first_by_proposal(cond_records, proposal_id)
        auth = first_by_proposal(auth_records, proposal_id)
        gate = first_by_proposal(gate_records, proposal_id)
        dec = first_by_proposal(dec_records, proposal_id)

        required_resolutions = dedup_sorted(rr.get("required_resolutions", []))
        unresolved_items = dedup_sorted(rr.get("currently_unresolved_items", []))
        required_evidence = dedup_sorted(rr.get("required_release_evidence", []))

        upstream_blockers = classify_upstream_blockers(unresolved_items)
        downstream_blockers = classify_downstream_blockers(unresolved_items)
        unsatisfiable_items = derive_unsatisfiable_items(unresolved_items)
        dependency_edges = make_dependency_edges(required_resolutions)

        chain = [
            "release_authority_unavailable",
            "release_gate_structurally_unavailable",
            "release_decision_structurally_unreleasable",
            "release_ineligibility_remains_active",
            "release_resolution_requirements_remain_unresolved",
        ]

        record = {
            "release_dependency_matrix_id": f"release-dependency-matrix-{idx:04d}",
            "proposal_id": proposal_id,
            "release_resolution_requirement_id": rr.get("release_resolution_requirement_id", ""),
            "release_condition_id": rr.get("release_condition_id", ""),
            "release_authority_id": rr.get("release_authority_id", ""),
            "release_gate_id": rr.get("release_gate_id", ""),
            "release_decision_id": rr.get("release_decision_id", ""),
            "release_ineligibility_id": rr.get("release_ineligibility_id", ""),
            "release_blocker_id": blocker.get("release_blocker_id", ""),
            "release_prohibition_id": prohibition.get("release_prohibition_id", ""),
            "dependency_state": "structurally_closed",
            "release_requirement_dependencies": required_resolutions,
            "dependency_edges": dependency_edges,
            "upstream_blockers": upstream_blockers,
            "downstream_blockers": downstream_blockers,
            "unsatisfiable_without_resolution": unsatisfiable_items,
            "required_release_evidence": required_evidence,
            "required_release_authority": rr.get("required_release_authority", ""),
            "required_operator_role": rr.get("required_operator_role", ""),
            "rollback_reference": rr.get("rollback_reference", ""),
            "dependency_chain": chain,
            "dependency_notes": (
                "v4_4_governance_only_release_dependency_matrix"
                "_tracks_structural_closure_no_execution_or_model_mutation"
            ),
            "source_paths": {k: v for k, v in SOURCE_PATHS.items()},
        }

        # Carry forward core unresolved lineages for traceability.
        record["currently_unresolved_items"] = unresolved_items
        record["release_blocker_refs"] = dedup_sorted(rr.get("release_blocker_refs", []))
        record["release_prohibition_refs"] = dedup_sorted(rr.get("release_prohibition_refs", []))

        # Augment with upstream artifacts where useful for dependency interpretation.
        record["required_signoff_chain"] = dedup_sorted(auth.get("required_signoff_chain", []))
        record["required_gate_evidence"] = dedup_sorted(gate.get("required_gate_evidence", []))
        record["required_remaining_actions"] = dedup_sorted(dec.get("required_remaining_actions", []))
        record["currently_unmet_release_conditions"] = dedup_sorted(
            cond.get("currently_unmet_release_conditions", [])
        )
        record["required_resolution_path"] = inelig.get("required_resolution_path", "")

        out.append(record)

    return out


def build_summary(records: list, total_source: int):
    covered = len({r.get("proposal_id") for r in records})
    states = sorted({r.get("dependency_state", "") for r in records})
    state_counts = {s: sum(1 for r in records if r.get("dependency_state") == s) for s in states}

    return {
        "total_proposals_in_source": total_source,
        "total_release_dependency_matrix_records": len(records),
        "proposals_covered": covered,
        "all_proposals_covered": covered == total_source,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "dependency_state_counts": state_counts,
        "deterministic_ordering": True,
    }


def build_source_versions(
    rr_data,
    inelig_data,
    blocker_data,
    prohibition_data,
    cond_data,
    auth_data,
    gate_data,
    dec_data,
):
    return {
        "model_adjustment_release_resolution_requirements_version":
            rr_data.get("model_adjustment_release_resolution_requirements_version", ""),
        "model_adjustment_release_ineligibility_register_version":
            inelig_data.get("model_adjustment_release_ineligibility_register_version", ""),
        "model_adjustment_release_blocker_registry_version":
            blocker_data.get("model_adjustment_release_blocker_registry_version", ""),
        "model_adjustment_release_prohibition_matrix_version":
            prohibition_data.get("model_adjustment_release_prohibition_matrix_version", ""),
        "model_adjustment_execution_release_conditions_version":
            cond_data.get("model_adjustment_execution_release_conditions_version", ""),
        "model_adjustment_execution_release_authority_version":
            auth_data.get("model_adjustment_execution_release_authority_version", ""),
        "model_adjustment_execution_release_gate_assessments_version":
            gate_data.get("model_adjustment_execution_release_gate_assessments_version", ""),
        "model_adjustment_execution_release_decisions_version":
            dec_data.get("model_adjustment_execution_release_decisions_version", ""),
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = []
    lines.append("# Model Adjustment Release Dependency Matrix")
    lines.append("")
    lines.append(f"**Version**: {VERSION}")
    lines.append(f"**Generated At (UTC)**: {generated_at}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for key, value in summary.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    lines.append("## Source Versions")
    lines.append("")
    lines.append("| Source | Version |")
    lines.append("|---|---|")
    for key, value in source_versions.items():
        lines.append(f"| {key} | {value} |")

    lines.append("")
    for rec in records:
        lines.append(f"## {rec['release_dependency_matrix_id']}")
        lines.append("")
        lines.append(f"- proposal_id: {rec['proposal_id']}")
        lines.append(f"- release_resolution_requirement_id: {rec['release_resolution_requirement_id']}")
        lines.append(f"- release_condition_id: {rec['release_condition_id']}")
        lines.append(f"- release_authority_id: {rec['release_authority_id']}")
        lines.append(f"- release_gate_id: {rec['release_gate_id']}")
        lines.append(f"- release_decision_id: {rec['release_decision_id']}")
        lines.append(f"- release_ineligibility_id: {rec['release_ineligibility_id']}")
        lines.append(f"- dependency_state: {rec['dependency_state']}")
        lines.append(f"- required_release_authority: {rec['required_release_authority']}")
        lines.append(f"- required_operator_role: {rec['required_operator_role']}")
        lines.append(f"- rollback_reference: {rec['rollback_reference']}")
        lines.append("")

        sections = [
            "release_requirement_dependencies",
            "dependency_edges",
            "upstream_blockers",
            "downstream_blockers",
            "unsatisfiable_without_resolution",
            "currently_unresolved_items",
            "required_release_evidence",
            "dependency_chain",
        ]
        for section in sections:
            lines.append(f"### {section}")
            lines.append("")
            values = rec.get(section, [])
            if values:
                for value in values:
                    lines.append(f"- {value}")
            else:
                lines.append("- none")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    errors = {}

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

    failures = [k for k, v in errors.items() if v is not None]
    if failures:
        for key in failures:
            print(f"[ERROR] {key}: {errors[key]}", file=sys.stderr)
        sys.exit(1)

    records = build_records(
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        cond_data,
        auth_data,
        gate_data,
        dec_data,
    )

    source_total = len(rr_data.get("release_resolution_requirements", []))
    summary = build_summary(records, source_total)
    source_versions = build_source_versions(
        rr_data,
        inelig_data,
        blocker_data,
        prohibition_data,
        cond_data,
        auth_data,
        gate_data,
        dec_data,
    )

    source_status = {f"{k}_error": errors[k] for k in SOURCE_PATHS}
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_dependency_matrix_version": VERSION,
        "release_dependency_matrix_summary": summary,
        "release_dependency_matrix": records,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_markdown(records, summary, source_versions, generated_at)
    print(f"[WRITE] {OUTPUT_MD}")

    print(
        "[STATUS] "
        f"release_dependency_matrix={summary['total_release_dependency_matrix_records']} "
        f"proposals_covered={summary['proposals_covered']} "
        f"all_covered={summary['all_proposals_covered']} "
        f"record_count_matches_expected={summary['record_count_matches_expected']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"dependency_state={summary['dependency_state_counts']}"
    )


if __name__ == "__main__":
    main()

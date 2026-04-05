"""
generate_model_adjustment_release_finality_registry.py

v4.7-slice-1 — Read-only controlled release finality-registry generator.

Consumes the frozen v4.6 release finality decision output and emits a
deterministic, read-only registry/index of terminal release outcomes.

No re-classification logic. No release-enabling path. No upstream mutation.

Hard rules:
- no execution
- no auto-promotion
- no config writes
- no model mutation
- no upstream governance artifact mutation
- no re-classification of finality states
"""

import json
import os
import sys
from datetime import datetime, timezone


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "ops", "model_adjustments")

SOURCE_PATHS = {
    "model_adjustment_release_finality_decisions_json":
        "ops/model_adjustments/model_adjustment_release_finality_decisions.json",
}

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_finality_registry.json")
OUTPUT_MD = os.path.join(OPS_DIR, "model_adjustment_release_finality_registry.md")

VERSION = "v4.7-slice-1"
EXPECTED_RECORD_COUNT = 4

KNOWN_FINALITY_STATES = frozenset({
    "governance_final_no_release",
    "structurally_closed",
    "temporarily_closed",
})

REQUIRED_DECISION_FIELDS = (
    "release_finality_decision_id",
    "proposal_id",
    "release_finality_state",
    "release_finality_class",
    "release_finality_reason",
    "closure_state",
    "closure_classification",
    "release_blocker_refs",
    "release_prohibition_refs",
    "required_remaining_resolutions",
    "required_release_authority",
    "required_operator_role",
    "rollback_reference",
)


def abs_path(rel_path: str) -> str:
    return os.path.join(SCRIPT_DIR, rel_path.replace("/", os.sep))


def load_json(rel_path: str):
    with open(abs_path(rel_path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_source(source_key: str):
    rel_path = SOURCE_PATHS[source_key]
    try:
        return load_json(rel_path), None
    except Exception as exc:
        return None, str(exc)


def dedup_sorted(values) -> list:
    return sorted(set(str(v) for v in (values or []) if v))


def validate_decision_record(record: dict, index: int) -> None:
    """Fail-closed: raises ValueError on missing or malformed required fields."""
    for field in REQUIRED_DECISION_FIELDS:
        if field not in record:
            raise ValueError(
                f"decision record[{index}] missing required field {field!r}; "
                "fail-closed — manual review required"
            )
    if not record.get("release_finality_decision_id"):
        raise ValueError(
            f"decision record[{index}] has empty release_finality_decision_id; "
            "fail-closed — manual review required"
        )
    if not record.get("proposal_id"):
        raise ValueError(
            f"decision record[{index}] has empty proposal_id; "
            "fail-closed — manual review required"
        )
    state = record.get("release_finality_state", "")
    if state not in KNOWN_FINALITY_STATES:
        raise ValueError(
            f"decision record[{index}] unrecognized release_finality_state={state!r}; "
            "fail-closed — manual review required"
        )


def validate_registry(records: list) -> None:
    """Structural assertions on fully built registry records before any write."""
    registry_ids = [r["release_finality_registry_id"] for r in records]
    if len(registry_ids) != len(set(registry_ids)):
        raise ValueError("duplicate release_finality_registry_id in output; fail-closed")

    decision_ids = [r["release_finality_decision_id"] for r in records]
    if len(decision_ids) != len(set(decision_ids)):
        raise ValueError("duplicate release_finality_decision_id in registry; fail-closed")

    proposal_ids = [r["proposal_id"] for r in records]
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValueError("duplicate proposal_id in registry records; fail-closed")

    if len(records) != EXPECTED_RECORD_COUNT:
        raise ValueError(
            f"registry record count {len(records)} does not match "
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
            "registry_blocker_refs",
            "registry_prohibition_refs",
            "registry_remaining_resolutions",
        ):
            values = record.get(field, [])
            if len(values) != len(set(values)):
                raise ValueError(
                    f"duplicate entries in {field!r} for proposal "
                    f"{record.get('proposal_id')!r}; fail-closed"
                )


def build_registry_records(decisions: list) -> list:
    """
    Pure projection of v4.6 finality decisions into registry records.
    No re-classification. No new logic. Ordered by release_finality_decision_id.
    """
    sorted_decisions = sorted(
        decisions,
        key=lambda r: r.get("release_finality_decision_id", ""),
    )

    output = []
    for index, decision in enumerate(sorted_decisions, start=1):
        validate_decision_record(decision, index)

        output.append(
            {
                "release_finality_registry_id": f"release-finality-registry-{index:04d}",
                "release_finality_decision_id": decision["release_finality_decision_id"],
                "proposal_id": decision["proposal_id"],
                "release_condition_id": decision.get("release_condition_id", ""),
                "release_authority_id": decision.get("release_authority_id", ""),
                "release_gate_id": decision.get("release_gate_id", ""),
                "release_decision_id": decision.get("release_decision_id", ""),
                "release_ineligibility_id": decision.get("release_ineligibility_id", ""),
                "release_closure_assessment_id": decision.get("release_closure_assessment_id", ""),
                # — finality state projected verbatim from v4.6, no re-classification —
                "release_finality_state": decision["release_finality_state"],
                "release_finality_class": decision["release_finality_class"],
                "release_finality_reason": decision["release_finality_reason"],
                # — closure context projected verbatim —
                "closure_state": decision.get("closure_state", ""),
                "closure_classification": decision.get("closure_classification", ""),
                # — dedup-sorted ref lists projected from v4.6 —
                "registry_blocker_refs": dedup_sorted(
                    decision.get("release_blocker_refs", [])
                ),
                "registry_prohibition_refs": dedup_sorted(
                    decision.get("release_prohibition_refs", [])
                ),
                "registry_remaining_resolutions": dedup_sorted(
                    decision.get("required_remaining_resolutions", [])
                ),
                "registry_release_evidence": dedup_sorted(
                    decision.get("required_release_evidence", [])
                ),
                "registry_unresolved_items": dedup_sorted(
                    decision.get("currently_unresolved_items", [])
                ),
                # — authority and resolution path projected verbatim —
                "required_release_authority": decision.get("required_release_authority", ""),
                "required_operator_role": decision.get("required_operator_role", ""),
                "rollback_reference": decision.get("rollback_reference", ""),
                "required_resolution_path": decision.get("required_resolution_path", ""),
                # — counts for index/query use —
                "blocker_ref_count": len(dedup_sorted(decision.get("release_blocker_refs", []))),
                "prohibition_ref_count": len(
                    dedup_sorted(decision.get("release_prohibition_refs", []))
                ),
                "remaining_resolution_count": len(
                    dedup_sorted(decision.get("required_remaining_resolutions", []))
                ),
                # — registry metadata —
                "registry_notes": (
                    "v4_7_read_only_registry_projection_of_v4_6_finality_decisions"
                    "_no_reclassification_no_release_enabling_no_upstream_mutation"
                ),
                "upstream_source": SOURCE_PATHS[
                    "model_adjustment_release_finality_decisions_json"
                ],
            }
        )

    return output


def build_summary(records: list, upstream_decision_count: int) -> dict:
    proposals_covered = len({r.get("proposal_id") for r in records})
    states = sorted({r.get("release_finality_state", "") for r in records})
    state_counts = {
        state: sum(1 for r in records if r.get("release_finality_state") == state)
        for state in states
    }
    classes = sorted({r.get("release_finality_class", "") for r in records})
    class_counts = {
        cls: sum(1 for r in records if r.get("release_finality_class") == cls)
        for cls in classes
    }

    total_blockers = sum(r.get("blocker_ref_count", 0) for r in records)
    total_prohibitions = sum(r.get("prohibition_ref_count", 0) for r in records)
    total_remaining = sum(r.get("remaining_resolution_count", 0) for r in records)

    return {
        "upstream_decision_count": upstream_decision_count,
        "total_registry_records": len(records),
        "proposals_covered": proposals_covered,
        "all_proposals_covered": proposals_covered == upstream_decision_count,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "release_finality_state_counts": state_counts,
        "release_finality_class_counts": class_counts,
        "total_blocker_refs_indexed": total_blockers,
        "total_prohibition_refs_indexed": total_prohibitions,
        "total_remaining_resolutions_indexed": total_remaining,
        "deterministic_ordering": True,
    }


def build_source_versions(decisions_data: dict) -> dict:
    return {
        "model_adjustment_release_finality_decisions_version": decisions_data.get(
            "model_adjustment_release_finality_decisions_version", ""
        ),
    }


def write_markdown(records: list, summary: dict, source_versions: dict, generated_at: str):
    lines = [
        "# Model Adjustment Release Finality Registry",
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
        lines.append(f"## {record['release_finality_registry_id']}")
        lines.append("")
        lines.append(f"- release_finality_decision_id: {record['release_finality_decision_id']}")
        lines.append(f"- proposal_id: {record['proposal_id']}")
        lines.append(f"- release_closure_assessment_id: {record['release_closure_assessment_id']}")
        lines.append(f"- release_finality_state: {record['release_finality_state']}")
        lines.append(f"- release_finality_class: {record['release_finality_class']}")
        lines.append(f"- release_finality_reason: {record['release_finality_reason']}")
        lines.append(f"- closure_state: {record['closure_state']}")
        lines.append(f"- closure_classification: {record['closure_classification']}")
        lines.append(f"- required_release_authority: {record['required_release_authority']}")
        lines.append(f"- required_operator_role: {record['required_operator_role']}")
        lines.append(f"- rollback_reference: {record['rollback_reference']}")
        lines.append(f"- required_resolution_path: {record['required_resolution_path']}")
        lines.append(
            f"- blocker_ref_count: {record['blocker_ref_count']} "
            f"| prohibition_ref_count: {record['prohibition_ref_count']} "
            f"| remaining_resolution_count: {record['remaining_resolution_count']}"
        )
        lines.append("")

        for section in [
            "registry_remaining_resolutions",
            "registry_blocker_refs",
            "registry_prohibition_refs",
            "registry_release_evidence",
        ]:
            lines.append(f"### {section}")
            lines.append("")
            values = record.get(section, [])
            if values:
                for v in values:
                    lines.append(f"- {v}")
            else:
                lines.append("- none")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main():
    errors = {}

    decisions_data, errors["model_adjustment_release_finality_decisions_json"] = load_source(
        "model_adjustment_release_finality_decisions_json"
    )

    failures = [k for k, v in errors.items() if v is not None]
    if failures:
        for k in failures:
            print(f"[ERROR] {k}: {errors[k]}", file=sys.stderr)
        sys.exit(1)

    upstream_decisions = decisions_data.get("release_finality_decisions", [])
    upstream_decision_count = len(upstream_decisions)

    records = build_registry_records(upstream_decisions)
    validate_registry(records)

    summary = build_summary(records, upstream_decision_count)
    source_versions = build_source_versions(decisions_data)
    source_status = {
        f"{k}_error": errors[k] for k in SOURCE_PATHS
    }
    generated_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_finality_registry_version": VERSION,
        "release_finality_registry_summary": summary,
        "release_finality_registry": records,
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
        f"registry_records={summary['total_registry_records']} "
        f"proposals_covered={summary['proposals_covered']} "
        f"all_covered={summary['all_proposals_covered']} "
        f"record_count_matches_expected={summary['record_count_matches_expected']} "
        f"deterministic_ordering={summary['deterministic_ordering']} "
        f"release_finality_state={summary['release_finality_state_counts']} "
        f"total_blockers={summary['total_blocker_refs_indexed']} "
        f"total_prohibitions={summary['total_prohibition_refs_indexed']} "
        f"total_remaining={summary['total_remaining_resolutions_indexed']}"
    )


if __name__ == "__main__":
    main()

"""
generate_model_adjustment_release_resolution_requirements.py

v4.3-slice-1 — Read-only controlled release resolution-requirements generator.

Derives a canonical per-proposal release resolution-requirements register from:
  - release ineligibility register          (v4.2)
  - release blocker registry                (v4.1)
  - release prohibition matrix              (v4.0)
  - execution release conditions            (v3.5)
  - execution release authority             (v3.6)
  - execution release gate assessments      (v3.7)
  - execution release decisions             (v3.8)

Hard rules:
  - no execution
  - no auto-promotion
  - no config writes
  - no model mutation
  - no upstream governance artifact mutation

Output:
  ops/model_adjustments/model_adjustment_release_resolution_requirements.json
  ops/model_adjustments/model_adjustment_release_resolution_requirements.md
"""

import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OPS_DIR = os.path.join(SCRIPT_DIR, "ops", "model_adjustments")

SOURCE_PATHS = {
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

OUTPUT_JSON = os.path.join(OPS_DIR, "model_adjustment_release_resolution_requirements.json")
OUTPUT_MD   = os.path.join(OPS_DIR, "model_adjustment_release_resolution_requirements.md")

VERSION = "v4.3-slice-1"
EXPECTED_RECORD_COUNT = 4

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def abs_path(rel: str) -> str:
    return os.path.join(SCRIPT_DIR, rel.replace("/", os.sep))


def load_json(rel: str):
    path = abs_path(rel)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_source(key: str):
    rel = SOURCE_PATHS[key]
    try:
        data = load_json(rel)
        return data, None
    except Exception as exc:
        return None, str(exc)


def first_record_for_proposal(records: list, proposal_id: str) -> dict:
    """Return the first record matching proposal_id, or empty dict."""
    for r in records:
        if r.get("proposal_id") == proposal_id:
            return r
    return {}


def all_records_for_proposal(records: list, proposal_id: str) -> list:
    return [r for r in records if r.get("proposal_id") == proposal_id]


def deduplicated_sorted(items) -> list:
    if not items:
        return []
    return sorted(set(str(i) for i in items if i))


def build_required_resolutions(
    inelig_rec: dict,
    blocker_rec: dict,
    prohibition_rec: dict,
    cond_rec: dict,
    auth_rec: dict,
    gate_rec: dict,
    dec_rec: dict,
) -> list:
    """
    Consolidate required resolution steps from all governance layers.
    Order: authority → condition → gate → decision → ineligibility → prohibition → blocker
    """
    items = []

    # authority layer
    auth_res = auth_rec.get("required_release_authority", "")
    if auth_res:
        items.append(f"resolve_release_authority:{auth_res}")
    auth_chain = auth_rec.get("required_signoff_chain", []) or []
    for step in auth_chain:
        if step:
            items.append(f"signoff_required:{step}")

    # condition layer
    for c in (cond_rec.get("required_release_conditions") or []):
        if c:
            items.append(f"release_condition_required:{c}")

    # gate layer
    for g in (gate_rec.get("unmet_gate_requirements") or []):
        if g:
            items.append(f"gate_requirement_unmet:{g}")

    # decision layer
    for d in (dec_rec.get("required_remaining_actions") or []):
        if d:
            items.append(f"decision_action_required:{d}")

    # ineligibility layer
    res_path = inelig_rec.get("required_resolution_path", "")
    if res_path:
        items.append(f"resolve_ineligibility:{res_path}")

    # prohibition layer
    proh_cond = prohibition_rec.get("required_release_condition", "")
    proh_auth = prohibition_rec.get("required_release_authority", "")
    if proh_cond:
        items.append(f"release_prohibition_condition_required:{proh_cond}")
    if proh_auth and proh_auth not in str(items):
        items.append(f"release_prohibition_authority_required:{proh_auth}")

    # blocker layer
    blocker_res = blocker_rec.get("required_resolution", "")
    if blocker_res:
        items.append(f"blocker_resolution_required:{blocker_res}")

    return deduplicated_sorted(items)


def build_currently_unresolved(
    inelig_rec: dict,
    blocker_rec: dict,
    cond_rec: dict,
    auth_rec: dict,
    gate_rec: dict,
    dec_rec: dict,
) -> list:
    """
    Consolidate all currently unresolved items across all governance layers.
    """
    items = []

    # authority blockers
    for b in (auth_rec.get("authority_blockers") or []):
        if b:
            items.append(b)

    # condition unmet
    for u in (cond_rec.get("currently_unmet_release_conditions") or []):
        if u:
            items.append(u)
    for b in (cond_rec.get("release_blockers") or []):
        if b:
            items.append(b)

    # gate unmet
    for u in (gate_rec.get("unmet_gate_requirements") or []):
        if u:
            items.append(u)
    for b in (gate_rec.get("gate_blockers") or []):
        if b:
            items.append(b)

    # decision blockers
    for b in (dec_rec.get("release_decision_blockers") or []):
        if b:
            items.append(b)

    # ineligibility active conditions
    for c in (inelig_rec.get("active_release_ineligibility_conditions") or []):
        if c:
            items.append(c)

    # blocker conditions
    blocking_cond = blocker_rec.get("blocking_condition", "")
    if blocking_cond:
        items.append(blocking_cond)

    return deduplicated_sorted(items)


def build_required_evidence(
    cond_rec: dict,
    gate_rec: dict,
    dec_rec: dict,
) -> list:
    items = []
    for e in (cond_rec.get("required_release_evidence") or []):
        if e:
            items.append(e)
    for e in (gate_rec.get("required_gate_evidence") or []):
        if e:
            items.append(e)
    for e in (dec_rec.get("required_release_evidence") or []):
        if e:
            items.append(e)
    return deduplicated_sorted(items)


def build_blocker_refs(blocker_rec: dict, inelig_rec: dict) -> list:
    refs = set()
    bid = blocker_rec.get("release_blocker_id", "")
    if bid:
        refs.add(bid)
    for c in (inelig_rec.get("active_release_ineligibility_conditions") or []):
        if str(c).startswith("blocker-"):
            refs.add(c)
    return sorted(refs)


def build_prohibition_refs(prohibition_rec: dict, inelig_rec: dict) -> list:
    refs = set()
    pid = prohibition_rec.get("release_prohibition_id", "")
    if pid:
        refs.add(pid)
    for c in (inelig_rec.get("active_release_ineligibility_conditions") or []):
        if str(c).startswith("release_prohibition_state"):
            refs.add(c)
    return sorted(refs)


# ---------------------------------------------------------------------------
# Main build logic
# ---------------------------------------------------------------------------

def build_records(
    inelig_data: dict,
    blocker_data: dict,
    prohibition_data: dict,
    cond_data: dict,
    auth_data: dict,
    gate_data: dict,
    dec_data: dict,
) -> list:
    inelig_records = inelig_data.get("release_ineligibility_register", [])
    blocker_records = blocker_data.get("release_blocker_registry", [])
    prohibition_records = prohibition_data.get("release_prohibition_matrix", [])
    cond_records = cond_data.get("execution_release_conditions", [])
    auth_records = auth_data.get("execution_release_authority", [])
    gate_records = gate_data.get("execution_release_gate_assessments", [])
    dec_records = dec_data.get("execution_release_decisions", [])

    # Sort ineligibility register by ID to ensure deterministic ordering
    inelig_records_sorted = sorted(
        inelig_records,
        key=lambda r: r.get("release_ineligibility_register_id", "")
    )

    output = []
    seq = 1

    for inelig_rec in inelig_records_sorted:
        proposal_id = inelig_rec.get("proposal_id", "")

        blocker_rec     = first_record_for_proposal(blocker_records, proposal_id)
        prohibition_rec = first_record_for_proposal(prohibition_records, proposal_id)
        cond_rec        = first_record_for_proposal(cond_records, proposal_id)
        auth_rec        = first_record_for_proposal(auth_records, proposal_id)
        gate_rec        = first_record_for_proposal(gate_records, proposal_id)
        dec_rec         = first_record_for_proposal(dec_records, proposal_id)

        req_id = f"release-resolution-requirement-{seq:04d}"

        required_resolutions = build_required_resolutions(
            inelig_rec, blocker_rec, prohibition_rec,
            cond_rec, auth_rec, gate_rec, dec_rec
        )
        currently_unresolved = build_currently_unresolved(
            inelig_rec, blocker_rec, cond_rec, auth_rec, gate_rec, dec_rec
        )
        required_evidence = build_required_evidence(cond_rec, gate_rec, dec_rec)
        blocker_refs      = build_blocker_refs(blocker_rec, inelig_rec)
        prohibition_refs  = build_prohibition_refs(prohibition_rec, inelig_rec)

        record = {
            "release_resolution_requirement_id": req_id,
            "proposal_id": proposal_id,
            "release_condition_id": inelig_rec.get("release_condition_id", ""),
            "release_authority_id": inelig_rec.get("release_authority_id", ""),
            "release_gate_id": inelig_rec.get("release_gate_id", ""),
            "release_decision_id": inelig_rec.get("release_decision_id", ""),
            "release_ineligibility_id": inelig_rec.get("release_ineligibility_decision_id", ""),
            "release_blocker_refs": blocker_refs,
            "release_prohibition_refs": prohibition_refs,
            "resolution_state": "unresolved",
            "required_resolutions": required_resolutions,
            "currently_unresolved_items": currently_unresolved,
            "required_release_evidence": required_evidence,
            "required_release_authority": inelig_rec.get("required_release_authority", ""),
            "required_operator_role": inelig_rec.get("required_operator_role", ""),
            "rollback_reference": inelig_rec.get("rollback_reference", ""),
            "resolution_notes": (
                "v4_3_governance_only_release_resolution_requirements_remain_active"
                "_no_execution_or_model_mutation"
            ),
            "source_paths": {k: v for k, v in SOURCE_PATHS.items()},
        }

        output.append(record)
        seq += 1

    return output


def build_summary(records: list, source_proposals: int) -> dict:
    proposals_covered = len({r["proposal_id"] for r in records})
    return {
        "total_proposals_in_source": source_proposals,
        "total_release_resolution_requirement_records": len(records),
        "proposals_covered": proposals_covered,
        "all_proposals_covered": proposals_covered == source_proposals,
        "record_count_matches_expected": len(records) == EXPECTED_RECORD_COUNT,
        "resolution_state_counts": {
            s: sum(1 for r in records if r["resolution_state"] == s)
            for s in sorted({r["resolution_state"] for r in records})
        },
        "deterministic_ordering": True,
    }


def build_source_versions(
    inelig_data, blocker_data, prohibition_data,
    cond_data, auth_data, gate_data, dec_data
) -> dict:
    return {
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


def build_source_status(errors: dict) -> dict:
    return {f"{k}_error": errors.get(k) for k in SOURCE_PATHS}


# ---------------------------------------------------------------------------
# Markdown writer
# ---------------------------------------------------------------------------

def write_md(records: list, summary: dict, generated_at: str, source_versions: dict):
    lines = [
        "# Model Adjustment Release Resolution Requirements",
        "",
        f"**Version**: {VERSION}  ",
        f"**Generated at (UTC)**: {generated_at}  ",
        "",
        "## Summary",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| total_proposals_in_source | {summary['total_proposals_in_source']} |",
        f"| total_release_resolution_requirement_records | {summary['total_release_resolution_requirement_records']} |",
        f"| proposals_covered | {summary['proposals_covered']} |",
        f"| all_proposals_covered | {summary['all_proposals_covered']} |",
        f"| record_count_matches_expected | {summary['record_count_matches_expected']} |",
        f"| deterministic_ordering | {summary['deterministic_ordering']} |",
        "",
        "## Source Versions",
        "",
        "| Source | Version |",
        "|---|---|",
    ]
    for k, v in source_versions.items():
        lines.append(f"| {k} | {v} |")
    lines += ["", "---", ""]

    for rec in records:
        lines += [
            f"## {rec['release_resolution_requirement_id']}",
            "",
            f"- **proposal_id**: {rec['proposal_id']}",
            f"- **release_condition_id**: {rec['release_condition_id']}",
            f"- **release_authority_id**: {rec['release_authority_id']}",
            f"- **release_gate_id**: {rec['release_gate_id']}",
            f"- **release_decision_id**: {rec['release_decision_id']}",
            f"- **release_ineligibility_id**: {rec['release_ineligibility_id']}",
            f"- **resolution_state**: {rec['resolution_state']}",
            f"- **required_release_authority**: {rec['required_release_authority']}",
            f"- **required_operator_role**: {rec['required_operator_role']}",
            f"- **rollback_reference**: {rec['rollback_reference']}",
            "",
            "### release_blocker_refs",
            "",
        ]
        for b in rec["release_blocker_refs"]:
            lines.append(f"- {b}")
        lines += [
            "",
            "### release_prohibition_refs",
            "",
        ]
        for p in rec["release_prohibition_refs"]:
            lines.append(f"- {p}")
        lines += [
            "",
            "### required_resolutions",
            "",
        ]
        for r in rec["required_resolutions"]:
            lines.append(f"- {r}")
        lines += [
            "",
            "### currently_unresolved_items",
            "",
        ]
        for u in rec["currently_unresolved_items"]:
            lines.append(f"- {u}")
        lines += [
            "",
            "### required_release_evidence",
            "",
        ]
        for e in rec["required_release_evidence"]:
            lines.append(f"- {e}")
        lines += ["", "---", ""]

    with open(OUTPUT_MD, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    errors = {}

    inelig_data,      errors["model_adjustment_release_ineligibility_register_json"]      = load_source("model_adjustment_release_ineligibility_register_json")
    blocker_data,     errors["model_adjustment_release_blocker_registry_json"]             = load_source("model_adjustment_release_blocker_registry_json")
    prohibition_data, errors["model_adjustment_release_prohibition_matrix_json"]           = load_source("model_adjustment_release_prohibition_matrix_json")
    cond_data,        errors["model_adjustment_execution_release_conditions_json"]         = load_source("model_adjustment_execution_release_conditions_json")
    auth_data,        errors["model_adjustment_execution_release_authority_json"]          = load_source("model_adjustment_execution_release_authority_json")
    gate_data,        errors["model_adjustment_execution_release_gate_assessments_json"]   = load_source("model_adjustment_execution_release_gate_assessments_json")
    dec_data,         errors["model_adjustment_execution_release_decisions_json"]          = load_source("model_adjustment_execution_release_decisions_json")

    fatal = [k for k, v in errors.items() if v is not None]
    if fatal:
        for k in fatal:
            print(f"[ERROR] {k}: {errors[k]}", file=sys.stderr)
        sys.exit(1)

    records = build_records(
        inelig_data, blocker_data, prohibition_data,
        cond_data, auth_data, gate_data, dec_data
    )

    source_proposals = len(inelig_data.get("release_ineligibility_register", []))
    summary          = build_summary(records, source_proposals)
    source_versions  = build_source_versions(
        inelig_data, blocker_data, prohibition_data,
        cond_data, auth_data, gate_data, dec_data
    )
    source_status    = build_source_status(errors)
    generated_at     = datetime.now(timezone.utc).isoformat()

    output = {
        "generated_at_utc": generated_at,
        "model_adjustment_release_resolution_requirements_version": VERSION,
        "release_resolution_requirements_summary": summary,
        "release_resolution_requirements": records,
        "source_paths": SOURCE_PATHS,
        "source_status": source_status,
        "source_versions": source_versions,
    }

    os.makedirs(OPS_DIR, exist_ok=True)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)
    print(f"[WRITE] {OUTPUT_JSON}")

    write_md(records, summary, generated_at, source_versions)
    print(f"[WRITE] {OUTPUT_MD}")

    proposals_covered = summary["proposals_covered"]
    all_covered       = summary["all_proposals_covered"]
    rec_count         = summary["total_release_resolution_requirement_records"]
    matches_expected  = summary["record_count_matches_expected"]
    det_order         = summary["deterministic_ordering"]
    res_states        = summary["resolution_state_counts"]

    print(
        f"[STATUS] release_resolution_requirements={rec_count} "
        f"proposals_covered={proposals_covered} "
        f"all_covered={all_covered} "
        f"record_count_matches_expected={matches_expected} "
        f"deterministic_ordering={det_order} "
        f"resolution_state={res_states}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
build_upcoming_schedule_escalation_email_dead_letter_notification_email_manual_intervention_resolution_ledger.py

v72.7: Canonical, deterministic manual-intervention resolution ledger builder
- Reads v72.6 manual-intervention/dead-letter outputs
- Produces canonical JSON ledger and Markdown projection
- Enforces strict state, fingerprint, and upsert rules
- Fails hard on invariant violations

Ledger contract, state model, and upsert rules are frozen and non-negotiable for this slice.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# 1. Constants and enums (frozen)
CASE_STATES = ["open", "assigned", "acknowledged", "resolved", "closed"]
ASSIGNMENT_STATES = ["unassigned", "assigned"]
ACKNOWLEDGEMENT_STATES = ["pending", "acknowledged"]
RESOLUTION_STATES = ["unresolved", "resolved_no_retry", "resolved_retry_requested", "resolved_suppressed"]
RETRY_STATES = ["not_applicable", "eligible", "requested", "executed", "blocked"]
CLOSURE_STATES = ["open", "closed"]

# 2. Normalization helpers (frozen)
def normalize_text(text: Optional[str]) -> str:
    if text is None:
        return ""
    return str(text).strip().lower()

def normalize_target_identity(target: Optional[str]) -> str:
    if not target:
        return ""
    return normalize_text(target)

def build_case_fingerprint_basis(
    source_event_id, source_schedule_id, source_operation, failure_family, failure_code, normalized_target_identity
) -> str:
    return "|".join([
        normalize_text(source_event_id),
        normalize_text(source_schedule_id),
        normalize_text(source_operation),
        normalize_text(failure_family),
        normalize_text(failure_code),
        normalize_target_identity(normalized_target_identity)
    ])

def build_case_fingerprint(basis: str) -> str:
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()

def build_resolution_case_id(fingerprint: str) -> str:
    return f"RES-{fingerprint[:16]}"

# 3. Canonical record constructor (frozen schema)
def build_new_resolution_case(source_record, now_iso, sla_policy) -> dict:
    # Extract and normalize all required fields
    source_event_id = source_record.get("source_event_id", "")
    source_schedule_id = source_record.get("source_schedule_id", "")
    source_run_id = source_record.get("source_run_id", "")
    source_operation = source_record.get("source_operation", "")
    failure_family = source_record.get("failure_family", "")
    failure_code = source_record.get("failure_code", "")
    failure_summary = source_record.get("failure_summary", "")
    failure_details = source_record.get("failure_details", "")
    normalized_target_identity = source_record.get("normalized_target_identity", "")
    # Build fingerprint and case ID
    basis = build_case_fingerprint_basis(
        source_event_id, source_schedule_id, source_operation, failure_family, failure_code, normalized_target_identity
    )
    fingerprint = build_case_fingerprint(basis)
    case_id = build_resolution_case_id(fingerprint)
    # SLA policy: derive due date from now + policy window (e.g., 24h)
    sla_window_hours = sla_policy.get("window_hours", 24)
    sla_started_at = now_iso
    sla_due_at = (datetime.fromisoformat(now_iso.replace("Z", "")) + timedelta(hours=sla_window_hours)).isoformat() + "Z"
    # Canonical record
    return {
        "resolution_case_id": case_id,
        "case_fingerprint": fingerprint,
        "case_state": "open",
        "source_event_id": source_event_id,
        "source_schedule_id": source_schedule_id,
        "source_run_id": source_run_id,
        "source_operation": source_operation,
        "failure_family": failure_family,
        "failure_code": failure_code,
        "failure_summary": failure_summary,
        "failure_details": failure_details,
        "assignment_state": "unassigned",
        "assigned_to": None,
        "assigned_at": None,
        "acknowledgement_state": "pending",
        "acknowledged_at": None,
        "sla_started_at": sla_started_at,
        "sla_due_at": sla_due_at,
        "resolution_state": "unresolved",
        "resolution_reason": None,
        "resolution_notes": None,
        "resolved_at": None,
        "retry_state": "eligible",
        "retry_decision": None,
        "retry_target": None,
        "retry_executed_at": None,
        "closure_state": "open",
        "closed_at": None,
        "created_at": now_iso,
        "updated_at": now_iso
    }

# 4. Upsert resolver (frozen rules)
def upsert_resolution_case(existing_by_fingerprint, candidate_record):
    fp = candidate_record["case_fingerprint"]
    if fp in existing_by_fingerprint:
        existing = existing_by_fingerprint[fp]
        # Only upsert if unresolved/open
        if existing["closure_state"] == "open" and existing["resolution_state"] == "unresolved":
            # Update in place: update fields, bump updated_at
            for k, v in candidate_record.items():
                if k not in ("created_at",):
                    existing[k] = v
            existing["updated_at"] = candidate_record["updated_at"]
            return existing
        else:
            # Do not reopen or duplicate
            return existing
    else:
        return candidate_record

# 5. Transition guard functions (frozen)
def apply_assignment(case, assigned_to, assigned_at):
    if case["closure_state"] != "open":
        raise Exception("Cannot assign a closed case")
    case["assignment_state"] = "assigned"
    case["assigned_to"] = assigned_to
    case["assigned_at"] = assigned_at
    if case["case_state"] == "open":
        case["case_state"] = "assigned"

def apply_acknowledgement(case, acknowledged_at):
    if case["closure_state"] != "open" or case["resolution_state"] != "unresolved":
        raise Exception("Cannot acknowledge a closed or resolved case")
    case["acknowledgement_state"] = "acknowledged"
    case["acknowledged_at"] = acknowledged_at
    case["case_state"] = "acknowledged"

def apply_resolution(case, resolution_state, resolved_at, reason=None, notes=None, retry_decision=None, retry_target=None):
    if case["closure_state"] != "open" or case["resolution_state"] != "unresolved":
        raise Exception("Cannot resolve a closed or already resolved case")
    if resolution_state not in RESOLUTION_STATES:
        raise Exception(f"Invalid resolution_state: {resolution_state}")
    case["resolution_state"] = resolution_state
    case["resolved_at"] = resolved_at
    case["case_state"] = "resolved"
    if reason:
        case["resolution_reason"] = reason
    if notes:
        case["resolution_notes"] = notes
    if retry_decision:
        case["retry_decision"] = retry_decision
    if retry_target:
        case["retry_target"] = retry_target

def apply_closure(case, closed_at):
    if case["case_state"] != "resolved":
        raise Exception("Can only close a resolved case")
    case["closure_state"] = "closed"
    case["closed_at"] = closed_at
    case["case_state"] = "closed"

# 6. Invariant validator (frozen)
def validate_case_invariants(case):
    if case["closure_state"] == "closed" and not case["closed_at"]:
        raise Exception("closed_at required when closure_state is closed")
    if case["closure_state"] == "open" and case["closed_at"]:
        raise Exception("closed_at must not exist when closure_state is open")
    if case["resolution_state"] != "unresolved" and not case["resolved_at"]:
        raise Exception("resolved_at required when resolution_state is not unresolved")
    if case["resolution_state"] == "unresolved" and case["resolved_at"]:
        raise Exception("resolved_at must not exist when resolution_state is unresolved")
    if case["acknowledgement_state"] == "acknowledged" and not case["acknowledged_at"]:
        raise Exception("acknowledged_at required when acknowledgement_state is acknowledged")
    if case["acknowledgement_state"] == "pending" and case["acknowledged_at"]:
        raise Exception("acknowledged_at must not exist when acknowledgement_state is pending")
    if case["assignment_state"] == "assigned" and not case["assigned_at"]:
        raise Exception("assigned_at required when assignment_state is assigned")
    if case["assignment_state"] == "unassigned" and case["assigned_at"]:
        raise Exception("assigned_at must not exist when assignment_state is unassigned")
    if case["retry_state"] == "executed" and not case["retry_executed_at"]:
        raise Exception("retry_executed_at required when retry_state is executed")
    if case["case_state"] == "closed" and case["closure_state"] != "closed":
        raise Exception("case_state closed requires closure_state closed")
    if case["case_state"] == "resolved" and case["resolution_state"] == "unresolved":
        raise Exception("case_state resolved requires resolution_state not unresolved")

def validate_ledger_invariants(cases):
    seen = set()
    for case in cases:
        validate_case_invariants(case)
        fp = case["case_fingerprint"]
        if fp in seen and case["closure_state"] == "open" and case["resolution_state"] == "unresolved":
            raise Exception(f"Duplicate active unresolved case for fingerprint {fp}")
        if case["closure_state"] == "open" and case["resolution_state"] == "unresolved":
            seen.add(fp)

# 7. Deterministic sorter
def sort_resolution_cases(cases):
    return sorted(
        cases,
        key=lambda c: (
            0 if c["closure_state"] == "open" else 1,
            0 if c["resolution_state"] == "unresolved" else 1,
            c["created_at"],
            c["resolution_case_id"]
        )
    )

# 8. JSON writer
def write_json(path, cases):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)
        f.write("\n")

# 9. Markdown writer
def render_markdown(cases, metadata=None):
    lines = ["# Manual-Intervention Resolution Ledger\n"]
    if metadata:
        lines.append(f"_Generated: {metadata.get('generated_at', '')}_\n")
    for c in cases:
        lines.append(f"- **Case ID:** {c['resolution_case_id']}")
        lines.append(f"  - Fingerprint: `{c['case_fingerprint']}`")
        lines.append(f"  - State: `{c['case_state']}` | Assignment: `{c['assignment_state']}` | Ack: `{c['acknowledgement_state']}` | Resolution: `{c['resolution_state']}` | Closure: `{c['closure_state']}`")
        lines.append(f"  - Source: Event `{c['source_event_id']}` | Schedule `{c['source_schedule_id']}` | Run `{c['source_run_id']}` | Op `{c['source_operation']}`")
        lines.append(f"  - Failure: Family `{c['failure_family']}` | Code `{c['failure_code']}` | Summary: {c['failure_summary']}")
        lines.append(f"  - Assigned To: {c['assigned_to']} | Assigned At: {c['assigned_at']}")
        lines.append(f"  - Ack At: {c['acknowledged_at']} | SLA Start: {c['sla_started_at']} | SLA Due: {c['sla_due_at']}")
        lines.append(f"  - Resolved At: {c['resolved_at']} | Reason: {c['resolution_reason']} | Notes: {c['resolution_notes']}")
        lines.append(f"  - Retry: State `{c['retry_state']}` | Decision: {c['retry_decision']} | Target: {c['retry_target']} | Executed At: {c['retry_executed_at']}")
        lines.append(f"  - Closed At: {c['closed_at']}")
        lines.append(f"  - Created: {c['created_at']} | Updated: {c['updated_at']}\n")
    return "\n".join(lines)

# 10. Main entry (stub, to be completed with input/output wiring)
def main():
    # 1. Wire upstream v72.6 manual-intervention/dead-letter input
    # For this slice, use resolution_state as canonical input (empty for now)
    input_path = Path("ops/events/upcoming_schedule_escalation_email_dead_letter_notification_manual_intervention_resolution_state.json")
    ledger_path = Path("ops/events/upcoming_schedule_manual_intervention_resolution_ledger.json")
    md_path = Path("ops/events/upcoming_schedule_manual_intervention_resolution_ledger.md")
    sla_policy = {"window_hours": 24}
    now_iso = datetime.utcnow().isoformat() + "Z"

    # 2. Load prior ledger if present (incremental upsert mode)
    if ledger_path.exists():
        with open(ledger_path, "r", encoding="utf-8") as f:
            prior_ledger = json.load(f)
    else:
        prior_ledger = []
    existing_by_fingerprint = {c["case_fingerprint"]: c for c in prior_ledger}

    # 3. Load upstream incidents
    if input_path.exists():
        with open(input_path, "r", encoding="utf-8") as f:
            incidents = json.load(f)
    else:
        incidents = []

    inserted = 0
    updated = 0
    suppressed = 0
    candidates = []
    for inc in incidents:
        # Normalize and build canonical candidate
        # Map upstream fields to canonical contract
        source_record = {
            "source_event_id": inc.get("intervention_id", ""),
            "source_schedule_id": inc.get("schedule_id", ""),
            "source_run_id": inc.get("run_id", ""),
            "source_operation": inc.get("operation", ""),
            "failure_family": inc.get("failure_family", ""),
            "failure_code": inc.get("failure_code", ""),
            "failure_summary": inc.get("failure_summary", ""),
            "failure_details": inc.get("failure_details", ""),
            "normalized_target_identity": inc.get("target_identity", "")
        }
        candidate = build_new_resolution_case(source_record, now_iso, sla_policy)
        fp = candidate["case_fingerprint"]
        # 4. Upsert
        if fp in existing_by_fingerprint:
            existing = existing_by_fingerprint[fp]
            if existing["closure_state"] == "open" and existing["resolution_state"] == "unresolved":
                updated += 1
                upserted = upsert_resolution_case(existing_by_fingerprint, candidate)
                existing_by_fingerprint[fp] = upserted
            else:
                suppressed += 1
        else:
            inserted += 1
            existing_by_fingerprint[fp] = candidate
        candidates.append(fp)

    # 5. Validate invariants
    cases = list(existing_by_fingerprint.values())
    validate_ledger_invariants(cases)

    # 6. Sort deterministically
    cases_sorted = sort_resolution_cases(cases)

    # 7. Write JSON
    write_json(ledger_path, cases_sorted)

    # 8. Write Markdown
    md = render_markdown(cases_sorted, metadata={"generated_at": now_iso})
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # 9. Print summary
    total = len(cases_sorted)
    open_count = sum(1 for c in cases_sorted if c["closure_state"] == "open")
    unresolved_count = sum(1 for c in cases_sorted if c["resolution_state"] == "unresolved")
    resolved_count = sum(1 for c in cases_sorted if c["resolution_state"] != "unresolved")
    closed_count = sum(1 for c in cases_sorted if c["closure_state"] == "closed")
    print(f"Total: {total} | Open: {open_count} | Unresolved: {unresolved_count} | Resolved: {resolved_count} | Closed: {closed_count}")
    print(f"Inserted: {inserted} | Updated: {updated} | Suppressed: {suppressed}")
    print(f"Ledger: {ledger_path}")
    print(f"Markdown: {md_path}")

if __name__ == "__main__":
    main()

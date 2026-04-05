# v66.1: queue-write eligibility and local sink helpers
def assess_queue_write_eligibility(records):
    for rec in records:
        if rec.get("execution_go"):
            rec["queue_write_eligible"] = True
            rec["queue_write_status"] = "eligible"
            rec["queue_write_reasons"] = []
            rec["queue_write_id"] = build_queue_write_id(rec)
            rec["queue_sink_target"] = build_queue_sink_target(rec)
        else:
            rec["queue_write_eligible"] = False
            rec["queue_write_status"] = "blocked"
            rec["queue_write_reasons"] = ["not execution-go"]
            rec["queue_write_id"] = None
            rec["queue_sink_target"] = None

def build_queue_write_id(record):
    # Deterministic queue write ID based on run_cycle_id
    if record.get("run_cycle_id"):
        return f"queue_write_{record['run_cycle_id']}"
    return None

def build_queue_sink_target(record):
    # Deterministic sink target (could be extended in future)
    return "local_sink"

# v66.2: queue-consumer simulation helpers
def assess_queue_consume_eligibility(records, sink_entries):
    sink_ids = {entry["queue_write_id"] for entry in sink_entries}
    for rec in records:
        if rec.get("queue_write_id") in sink_ids:
            rec["queue_consume_eligible"] = True
            rec["queue_consume_status"] = "eligible"
            rec["queue_consume_reasons"] = []
            rec["dispatch_simulation_id"] = build_dispatch_simulation_id(rec)
            rec["dispatch_simulation_status"] = "ready"
            rec["dispatch_simulation_target"] = build_dispatch_simulation_target(rec)
            rec["dispatch_simulation_payload"] = build_dispatch_simulation_payload(rec)
        else:
            rec["queue_consume_eligible"] = False
            rec["queue_consume_status"] = "blocked"
            rec["queue_consume_reasons"] = ["not in sink"]
            rec["dispatch_simulation_id"] = None
            rec["dispatch_simulation_status"] = None
            rec["dispatch_simulation_target"] = None
            rec["dispatch_simulation_payload"] = None

def build_dispatch_simulation_id(record):
    # Deterministic simulation ID based on queue_write_id
    if record.get("queue_write_id"):
        return f"dispatch_sim_{record['queue_write_id']}"
    return None

def build_dispatch_simulation_target(record):
    # Deterministic simulation target (could be extended in future)
    return "simulated_dispatch"

def build_dispatch_simulation_payload(record):
    # Deterministic payload based on sink-approved entry
    return {
        "event_id": record["event_id"],
        "handoff_payload_id": record["handoff_payload_id"],
        "queue_write_id": record["queue_write_id"],
        "run_cycle_id": record["run_cycle_id"],
        "queue_target": record["queue_target"],
        "dispatch_simulation_id": build_dispatch_simulation_id(record),
    }

def simulate_queue_consumption(sink_entries):
    # Add consumption-side fields to sink entries, stable order by queue_write_id
    for i, entry in enumerate(sorted(sink_entries, key=lambda e: e["queue_write_id"] or "")):
        entry["consumed_in_simulation"] = True
        entry["consume_position"] = i+1
        entry["dispatch_simulation_id"] = f"dispatch_sim_{entry['queue_write_id']}"
        entry["dispatch_simulation_status"] = "simulated"
    return sink_entries

def write_local_queue_sink(path, records):
    # Only execution-go records, stable order by queue_write_id
    sink_entries = []
    for rec in records:
        if rec.get("queue_write_eligible"):
            entry = {
                "queue_write_id": rec["queue_write_id"],
                "event_id": rec["event_id"],
                "handoff_payload_id": rec["handoff_payload_id"],
                "runner_stage_id": rec["runner_stage_id"],
                "queue_bundle_id": rec["queue_bundle_id"],
                "emission_manifest_id": rec["emission_manifest_id"],
                "run_cycle_id": rec["run_cycle_id"],
                "queue_target": rec["queue_target"],
                "dry_run_only": False,
                "written_at_cycle": rec["run_cycle_id"],
            }
            sink_entries.append(entry)
    sink_entries = sorted(sink_entries, key=lambda e: e["queue_write_id"] or "")
    # v66.2: simulate queue consumption
    sink_entries = simulate_queue_consumption(sink_entries)
    path.write_text(json.dumps(sink_entries, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
# v65.9: execution-decision helpers
def assess_execution_decision(records):
    # Only ledger_included records can be go; others are no-go
    for rec in records:
        if rec.get("ledger_included"):
            blockers = rec.get("dispatch_blockers", []) + rec.get("handoff_blockers", [])
            if not blockers:
                rec["execution_decision"] = "go"
                rec["execution_decision_reasons"] = []
                rec["execution_go"] = True
                rec["execution_blocked"] = False
            else:
                rec["execution_decision"] = "conditional"
                rec["execution_decision_reasons"] = blockers
                rec["execution_go"] = False
                rec["execution_blocked"] = True
        else:
            rec["execution_decision"] = "no_go"
            rec["execution_decision_reasons"] = ["not ledger-included"]
            rec["execution_go"] = False
            rec["execution_blocked"] = True

def assign_execution_gate_level(records):
    # Assign gate level based on blockers: open, conditional, blocked
    for rec in records:
        if rec["execution_decision"] == "go":
            rec["execution_gate_level"] = "open"
        elif rec["execution_decision"] == "conditional":
            rec["execution_gate_level"] = "conditional"
        else:
            rec["execution_gate_level"] = "blocked"

def build_execution_gate_summary(records):
    # Summarize go/no-go/conditional counts and reasons
    total = len(records)
    go = sum(1 for r in records if r["execution_decision"] == "go")
    conditional = sum(1 for r in records if r["execution_decision"] == "conditional")
    no_go = sum(1 for r in records if r["execution_decision"] == "no_go")
    open_levels = sum(1 for r in records if r["execution_gate_level"] == "open")
    conditional_levels = sum(1 for r in records if r["execution_gate_level"] == "conditional")
    blocked_levels = sum(1 for r in records if r["execution_gate_level"] == "blocked")
    reasons = {}
    for r in records:
        for reason in r["execution_decision_reasons"]:
            reasons.setdefault(reason, 0)
            reasons[reason] += 1
    return {
        "total": total,
        "go": go,
        "conditional": conditional,
        "no_go": no_go,
        "open_levels": open_levels,
        "conditional_levels": conditional_levels,
        "blocked_levels": blocked_levels,
        "reasons": reasons,
    }
# v65.8: run-cycle ledger helpers
def build_run_cycle_id(record):
    # Deterministic run cycle ID based on emission_manifest_id
    if record.get("emission_manifest_id"):
        return f"run_cycle_{record['emission_manifest_id']}"
    return None

def assign_run_cycle_positions(records):
    # Only for dispatch_ready records, ordered by dispatch_order
    ready = [r for r in records if r.get("dispatch_ready")]
    ready_sorted = sorted(ready, key=lambda r: r["dispatch_order"] or 0)
    for i, rec in enumerate(ready_sorted):
        rec["run_cycle_position"] = i+1
    return ready_sorted

def assess_execution_gate(records):
    # If any dispatch_ready record exists, gate is open; else blocked
    open_count = sum(1 for r in records if r.get("dispatch_ready"))
    if open_count > 0:
        return "open", []
    else:
        return "blocked", ["no dispatch-ready records"]

def build_ledger_summary(records):
    # Summary: total, staged, bundles, manifest, ledger-included, blocked
    total = len(records)
    staged = sum(1 for r in records if r.get("staged_for_runner"))
    bundles = len(set(r["queue_bundle_id"] for r in records if r["queue_bundle_id"]))
    manifest = sum(1 for r in records if r.get("emission_manifest_id"))
    ledger = sum(1 for r in records if r.get("ledger_included"))
    blocked = total - ledger
    return {
        "total_records": total,
        "staged_records": staged,
        "bundles": bundles,
        "manifest_entries": manifest,
        "ledger_included": ledger,
        "blocked_records": blocked,
    }
# v65.7: emission-manifest helpers
def build_emission_manifest_id(record):
    # Deterministic manifest ID based on queue_bundle_id and handoff_payload_id
    if record.get("queue_bundle_id") and record.get("handoff_payload_id"):
        return f"manifest_{record['queue_bundle_id']}_{record['handoff_payload_id']}"
    return None

def build_emission_manifest_entry(record):
    # Deterministic manifest entry for emission-ready records
    if not record.get("bundle_emission_ready"):
        return None
    return {
        "manifest_id": build_emission_manifest_id(record),
        "queue_bundle_id": record["queue_bundle_id"],
        "handoff_payload_id": record["handoff_payload_id"],
        "queue_target": record["queue_target"],
        "bundle_position": record["queue_bundle_position"],
        "event_id": record["event_id"],
    }

def assign_dispatch_order(records):
    # Only for bundle_emission_ready records, grouped by queue_target, ordered by bundle_position then handoff_payload_id
    emission_ready = [r for r in records if r.get("bundle_emission_ready")]
    # Group by queue_target
    by_target = {}
    for rec in emission_ready:
        qt = rec["queue_target"]
        by_target.setdefault(qt, []).append(rec)
    # For each target, sort by bundle_position then handoff_payload_id
    dispatch_list = []
    for qt in sorted(by_target):
        group = sorted(by_target[qt], key=lambda r: (r["queue_bundle_position"], r["handoff_payload_id"]))
        dispatch_list.extend(group)
    # Assign dispatch_order and manifest_position
    for i, rec in enumerate(dispatch_list):
        rec["dispatch_order"] = i+1
        rec["emission_manifest_position"] = i+1
    return dispatch_list
# v65.6: queue-bundle planning helpers
def build_queue_bundle_id(queue_target, bundle_index):
    # Deterministic bundle ID based on queue_target and index
    return f"bundle_{queue_target}_{bundle_index+1}"

def assign_queue_bundle_positions(staged_records_by_target):
    # Returns a dict: {queue_target: [(record, position, size, members)]}
    bundle_map = {}
    for queue_target, records in staged_records_by_target.items():
        # Deterministic order: sort by handoff_payload_id
        sorted_records = sorted(records, key=lambda r: r["handoff_payload_id"])
        bundle_id = build_queue_bundle_id(queue_target, 0)
        size = len(sorted_records)
        members = [r["handoff_payload_id"] for r in sorted_records]
        for pos, rec in enumerate(sorted_records):
            bundle_map[rec["handoff_payload_id"]] = {
                "queue_bundle_id": bundle_id,
                "queue_bundle_position": pos+1,
                "queue_bundle_size": size,
                "queue_bundle_members": members,
                "bundle_emission_ready": True,
                "bundle_emission_blockers": [],
            }
    return bundle_map
import json
from pathlib import Path

# Embedded raw source fixtures simulating live-source payloads
UFC_SOURCE_FIXTURE = {
    "source_name": "UFC_API",
    "events": [
        {
            "id": "ufc_300",
            "date": "2026-04-13",
            "name": "UFC 300",
            "venue": "T-Mobile Arena",
            "sport": "MMA",
            "divisions": ["Lightweight", "Welterweight"],
        }
    ],
}

PFL_SOURCE_FIXTURE = {
    "source_name": "PFL_FEED",
    "events": [
        {
            "event_key": "pfl_2026_01",
            "date": "2026-05-01",
            "promotion": "PFL",
            "venue": None,
            "sport": "MMA",
            "divisions": ["Featherweight"],
        }
    ],
}

ONE_SOURCE_FIXTURE = {
    "source_name": "ONE_CHAMPIONSHIP",
    "events": [
        {
            "event_id": "one_2026_04",
            "date": None,
            "promotion": "ONE",
            "venue": "Singapore Indoor Stadium",
            "sport": "MMA",
            "divisions": [],
        }
    ],
}

REQUIRED_FIELDS = ["event_id", "date", "promotion", "venue", "sport", "divisions"]

def adapt_ufc_source(source):
    records = []
    for e in source["events"]:
        record = {
            "event_id": e.get("id") or "unknown",
            "date": e.get("date") or "unknown",
            "promotion": "UFC",
            "venue": e.get("venue") or "unknown",
            "sport": e.get("sport") or "unknown",
            "divisions": e.get("divisions") or [],
            "source_name": source["source_name"],
            "source_event_key": e.get("id") or "unknown",
            "adapter_status": "ok" if e.get("id") and e.get("date") else "incomplete",
        }
        records.append(record)
    return records

def adapt_pfl_source(source):
    records = []
    for e in source["events"]:
        record = {
            "event_id": e.get("event_key") or "unknown",
            "date": e.get("date") or "unknown",
            "promotion": e.get("promotion") or "PFL",
            "venue": e.get("venue") or "unknown",
            "sport": e.get("sport") or "unknown",
            "divisions": e.get("divisions") or [],
            "source_name": source["source_name"],
            "source_event_key": e.get("event_key") or "unknown",
            "adapter_status": "ok" if e.get("event_key") and e.get("date") else "incomplete",
        }
        records.append(record)
    return records

def adapt_one_source(source):
    records = []
    for e in source["events"]:
        record = {
            "event_id": e.get("event_id") or "unknown",
            "date": e.get("date") or "unknown",
            "promotion": e.get("promotion") or "ONE",
            "venue": e.get("venue") or "unknown",
            "sport": e.get("sport") or "unknown",
            "divisions": e.get("divisions") or [],
            "source_name": source["source_name"],
            "source_event_key": e.get("event_id") or "unknown",
            "adapter_status": "ok" if e.get("event_id") and e.get("date") else "incomplete",
        }
        records.append(record)
    return records

def detect_missing_dependencies(event):
    # Blocker-level: missing date, venue, divisions, promotion, sport
    blockers = []
    missing = []
    for field in REQUIRED_FIELDS:
        value = event.get(field)
        if field == "divisions":
            if not value:
                missing.append(field)
                blockers.append(field)
        elif value == "unknown":
            missing.append(field)
            blockers.append(field)
    return {
        "dependency_status": "blocked" if blockers else ("incomplete" if missing else "ready"),
        "missing_dependencies": missing,
        "handoff_ready": len(blockers) == 0,
        "handoff_blockers": blockers,
    }

def build_handoff_payload(record):
    # Only for handoff_ready records
    payload_version = "v1"
    runner_mode = "event-batch"
    target_report_types = select_target_report_types(record)
    payload = {
        "event_id": record["event_id"],
        "source_name": record["source_name"],
        "source_event_key": record["source_event_key"],
        "runner_mode": runner_mode,
        "target_report_types": target_report_types,
        "handoff_payload_version": payload_version,
    }
    return payload

def build_handoff_payload_id(payload):
    # Deterministic ID based on event_id, source_name, version
    return f"handoff_{payload['event_id']}_{payload['source_name']}_{payload['handoff_payload_version']}"

def select_target_report_types(record):
    # Deterministic, could be more complex in future
    return ["event_summary", "runner_log"]

# v65.5: runner-staging and queue-emission dry-run helpers
def build_runner_stage_id(record):
    # Deterministic runner stage ID based on handoff_payload_id
    if record.get("handoff_payload_id"):
        return f"runner_stage_{record['handoff_payload_id']}"
    return None

def build_runner_stage_payload(record):
    # Only for staged records
    if not record.get("included_in_handoff"):
        return None
    return {
        "handoff_payload_id": record["handoff_payload_id"],
        "event_id": record["event_id"],
        "runner_mode": record["runner_mode"],
        "target_report_types": record["target_report_types"],
        "queue_target": build_queue_target(record),
        "dry_run_only": True,
    }

def build_queue_target(record):
    # Deterministic queue target (could be more complex in future)
    return f"queue_{record['promotion'].lower()}_event_batch"

def build_queue_emission_preview(record):
    # Only for staged records
    if not record.get("included_in_handoff"):
        return None
    return {
        "queue_target": build_queue_target(record),
        "payload_id": record["handoff_payload_id"],
        "dry_run_only": True,
    }

def normalize_event(event):
    norm = {k: event.get(k) for k in ["event_id", "date", "promotion", "venue", "sport", "divisions", "source_name", "source_event_key", "adapter_status"]}
    missing_fields = []
    for field in REQUIRED_FIELDS:
        value = norm[field]
        if field == "divisions":
            if not value:
                missing_fields.append(field)
        elif value == "unknown":
            missing_fields.append(field)
    norm["complete"] = len(missing_fields) == 0
    norm["missing_fields"] = missing_fields
    dep = detect_missing_dependencies(norm)
    norm.update(dep)
    # v65.4: batch handoff logic
    if norm["handoff_ready"]:
        payload = build_handoff_payload(norm)
        norm["included_in_handoff"] = True
        norm["handoff_payload"] = payload
        norm["handoff_payload_id"] = build_handoff_payload_id(payload)
        norm["handoff_payload_version"] = payload["handoff_payload_version"]
        norm["runner_mode"] = payload["runner_mode"]
        norm["target_report_types"] = payload["target_report_types"]
        # v65.5: runner-staging and queue-emission dry-run fields
        norm["staged_for_runner"] = True
        norm["runner_stage_status"] = "staged"
        norm["runner_stage_payload"] = build_runner_stage_payload(norm)
        norm["runner_stage_id"] = build_runner_stage_id(norm)
        norm["queue_emission_preview"] = build_queue_emission_preview(norm)
        norm["queue_target"] = build_queue_target(norm)
        norm["dry_run_only"] = True
    else:
        norm["included_in_handoff"] = False
        norm["handoff_payload"] = None
        norm["handoff_payload_id"] = None
        norm["handoff_payload_version"] = None
        norm["runner_mode"] = None
        norm["target_report_types"] = None
        # v65.5: runner-staging and queue-emission dry-run fields for non-staged
        norm["staged_for_runner"] = False
        norm["runner_stage_status"] = "not_staged"
        norm["runner_stage_payload"] = None
        norm["runner_stage_id"] = None
        norm["queue_emission_preview"] = None
        norm["queue_target"] = None
        norm["dry_run_only"] = True
    return norm

def normalize_events(events):
    # First, normalize all events
    normalized = [normalize_event(e) for e in events]
    # v65.6: queue-bundle planning for staged records
    staged = [r for r in normalized if r.get("staged_for_runner")]
    # Group by queue_target
    staged_by_target = {}
    for rec in staged:
        qt = rec["queue_target"]
        staged_by_target.setdefault(qt, []).append(rec)
    # Assign bundle fields
    bundle_map = assign_queue_bundle_positions(staged_by_target)
    for rec in normalized:
        if rec.get("staged_for_runner"):
            bundle = bundle_map.get(rec["handoff_payload_id"], {})
            rec["queue_bundle_id"] = bundle.get("queue_bundle_id")
            rec["queue_bundle_position"] = bundle.get("queue_bundle_position")
            rec["queue_bundle_size"] = bundle.get("queue_bundle_size")
            rec["queue_bundle_members"] = bundle.get("queue_bundle_members")
            rec["bundle_emission_ready"] = bundle.get("bundle_emission_ready")
            rec["bundle_emission_blockers"] = bundle.get("bundle_emission_blockers")
        else:
            rec["queue_bundle_id"] = None
            rec["queue_bundle_position"] = None
            rec["queue_bundle_size"] = None
            rec["queue_bundle_members"] = None
            rec["bundle_emission_ready"] = False
            rec["bundle_emission_blockers"] = ["not staged"]
    # v65.7: emission-manifest fields
    # Assign manifest fields only to bundle_emission_ready records
    manifest_ready = [r for r in normalized if r.get("bundle_emission_ready")]
    dispatch_list = assign_dispatch_order(normalized)
    manifest_id_map = {r["handoff_payload_id"]: build_emission_manifest_id(r) for r in manifest_ready}
    for rec in normalized:
        if rec.get("bundle_emission_ready"):
            rec["emission_manifest_id"] = manifest_id_map.get(rec["handoff_payload_id"])
            rec["emission_manifest_entry"] = build_emission_manifest_entry(rec)
            rec["dispatch_ready"] = True
            rec["dispatch_blockers"] = []
        else:
            rec["emission_manifest_id"] = None
            rec["emission_manifest_entry"] = None
            rec["emission_manifest_position"] = None
            rec["dispatch_order"] = None
            rec["dispatch_ready"] = False
            rec["dispatch_blockers"] = ["not bundle emission ready"]
    # v65.8: run-cycle ledger fields
    # Only dispatch_ready records are ledger-included
    ledger_ready = [r for r in normalized if r.get("dispatch_ready")]
    for rec in normalized:
        if rec.get("dispatch_ready"):
            rec["ledger_included"] = True
            rec["run_cycle_id"] = build_run_cycle_id(rec)
        else:
            rec["ledger_included"] = False
            rec["run_cycle_id"] = None
            rec["run_cycle_position"] = None
    assign_run_cycle_positions(normalized)
    gate_status, gate_reasons = assess_execution_gate(normalized)
    ledger_summary = build_ledger_summary(normalized)
    for rec in normalized:
        rec["execution_gate_status"] = gate_status
        rec["execution_gate_reasons"] = gate_reasons
        rec["ledger_summary"] = ledger_summary
    # v65.9: execution-decision logic
    assess_execution_decision(normalized)
    assign_execution_gate_level(normalized)
    gate_summary = build_execution_gate_summary(normalized)
    for rec in normalized:
        rec["execution_gate_summary"] = gate_summary
    # v66.1: queue-write eligibility
    assess_queue_write_eligibility(normalized)
    # v66.2: queue-consumer simulation
    sink_path = Path("ops/events/upcoming_schedule_queue_sink.json")
    if sink_path.exists():
        with sink_path.open("r", encoding="utf-8") as f:
            try:
                sink_entries = json.load(f)
            except Exception:
                sink_entries = []
    else:
        sink_entries = []
    assess_queue_consume_eligibility(normalized, sink_entries)
    return normalized

def write_json(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Bundle Emission Manifest",
        "",
        "This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, and emission manifest sequencing.",
        "",
        "## Adapter Coverage",
        f"- UFC: {len([r for r in records if r['source_name']=='UFC_API'])} event(s)",
        f"- PFL: {len([r for r in records if r['source_name']=='PFL_FEED'])} event(s)",
        f"- ONE: {len([r for r in records if r['source_name']=='ONE_CHAMPIONSHIP'])} event(s)",
        "",
        f"## Queue Bundles: {len(set(r['queue_bundle_id'] for r in records if r['queue_bundle_id']))}",
        f"## Manifest Entries: {sum(1 for r in records if r['emission_manifest_id'])}",
        f"## Dispatch Ready: {sum(1 for r in records if r['dispatch_ready'])}",
        f"## Dispatch Blocked: {sum(1 for r in records if not r['dispatch_ready'])}",
        "",
        "## Dispatch Order by Queue Target",
    ]
    # Dispatch order by queue target
    manifest_ready = [r for r in records if r.get("dispatch_ready")]
    by_target = {}
    for rec in manifest_ready:
        qt = rec["queue_target"]
        by_target.setdefault(qt, []).append(rec)
    for qt in sorted(by_target):
        group = sorted(by_target[qt], key=lambda r: r["dispatch_order"])
        lines.append(f"- {qt}: {len(group)} entries")
        for rec in group:
            lines.append(f"  - {rec['emission_manifest_id']} (dispatch_order={rec['dispatch_order']})")
    lines.extend([
        "",
        "## Normalized Events",
        "",
    ])
    for rec in records:
        divisions = ", ".join(rec["divisions"]) if rec["divisions"] else "None"
        lines.append(
            f"- **ID:** {rec['event_id']} | **Date:** {rec['date']} | **Promotion:** {rec['promotion']} | "
            f"**Venue:** {rec['venue']} | **Sport:** {rec['sport']} | **Divisions:** {divisions} | "
            f"**Source:** {rec['source_name']} | **Adapter Status:** {rec['adapter_status']} | **Complete:** {rec['complete']} | "
            f"**Queue Bundle ID:** {rec['queue_bundle_id']} | **Bundle Position:** {rec['queue_bundle_position']} | "
            f"**Bundle Emission Ready:** {rec['bundle_emission_ready']} | **Manifest ID:** {rec['emission_manifest_id']} | "
            f"**Manifest Position:** {rec['emission_manifest_position']} | **Dispatch Order:** {rec['dispatch_order']} | "
            f"**Dispatch Ready:** {rec['dispatch_ready']} | **Dispatch Blockers:** {rec['dispatch_blockers']}"
        )
        if rec["missing_fields"]:
            lines.append(f"  - Missing: {', '.join(rec['missing_fields'])}")
        if rec["handoff_blockers"]:
            lines.append(f"  - Blockers: {', '.join(rec['handoff_blockers'])}")
        if not rec["included_in_handoff"]:
            lines.append("  - Excluded from handoff: not handoff-ready")
    lines.extend([
        "",
        "This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, and emission manifest sequencing format.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    lines = [
        "# Upcoming Schedule Queue Consumer Simulation",
        "",
        "This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, batch handoff packaging, runner/queue dry-run staging, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, and queue-consumer simulation logic.",
        "",
        f"## Total Sink Entries: {sum(1 for r in records if r['queue_write_eligible'])}",
        f"## Consume-Eligible: {sum(1 for r in records if r.get('queue_consume_eligible'))}",
        f"## Consume-Blocked: {sum(1 for r in records if not r.get('queue_consume_eligible'))}",
        f"## Simulated Dispatch-Ready: {sum(1 for r in records if r.get('dispatch_simulation_status')=='ready')}",
        f"## Withheld: {sum(1 for r in records if r.get('queue_consume_status')=='blocked')}",
        "",
        "## Dispatch Target Summary",
    ]
    target_counts = {}
    for rec in records:
        tgt = rec.get("dispatch_simulation_target")
        if tgt:
            target_counts.setdefault(tgt, 0)
            target_counts[tgt] += 1
    for tgt, count in sorted(target_counts.items()):
        lines.append(f"- {tgt}: {count}")
    lines.extend([
        "",
        "## Consume Blocker Summary",
    ])
    reason_counts = {}
    for rec in records:
        for reason in rec.get("queue_consume_reasons", []):
            reason_counts.setdefault(reason, 0)
            reason_counts[reason] += 1
    for reason, count in sorted(reason_counts.items()):
        lines.append(f"- {reason}: {count}")
    lines.extend([
        "",
        "## Normalized Events",
        "",
    ])
    for rec in records:
        divisions = ", ".join(rec["divisions"]) if rec["divisions"] else "None"
        lines.append(
            f"- **ID:** {rec['event_id']} | **Date:** {rec['date']} | **Promotion:** {rec['promotion']} | "
            f"**Venue:** {rec['venue']} | **Sport:** {rec['sport']} | **Divisions:** {divisions} | "
            f"**Queue Write Eligible:** {rec['queue_write_eligible']} | **Queue Consume Eligible:** {rec.get('queue_consume_eligible')} | "
            f"**Queue Consume Status:** {rec.get('queue_consume_status')} | **Dispatch Simulation ID:** {rec.get('dispatch_simulation_id')} | "
            f"**Dispatch Simulation Status:** {rec.get('dispatch_simulation_status')} | **Dispatch Simulation Target:** {rec.get('dispatch_simulation_target')} | "
            f"**Dispatch Simulation Payload:** {rec.get('dispatch_simulation_payload')}"
        )
        if rec["missing_fields"]:
            lines.append(f"  - Missing: {', '.join(rec['missing_fields'])}")
        if rec["handoff_blockers"]:
            lines.append(f"  - Blockers: {', '.join(rec['handoff_blockers'])}")
        if not rec["included_in_handoff"]:
            lines.append("  - Excluded from handoff: not handoff-ready")
    lines.extend([
        "",
        "This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, runner staging, queue emission dry-run, queue-bundle planning, emission manifest sequencing, run-cycle ledger, execution decision gate, local queue writing, and queue-consumer simulation format.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")

def main():
    out_dir = Path("ops/events")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Simulate live-source adapter handoff
    adapted = []
    adapted.extend(adapt_ufc_source(UFC_SOURCE_FIXTURE))
    adapted.extend(adapt_pfl_source(PFL_SOURCE_FIXTURE))
    adapted.extend(adapt_one_source(ONE_SOURCE_FIXTURE))
    normalized = normalize_events(adapted)
    write_json(out_dir / "upcoming_schedule_auto_discovery.json", normalized)
    write_markdown(out_dir / "upcoming_schedule_auto_discovery.md", normalized)
    write_local_queue_sink(out_dir / "upcoming_schedule_queue_sink.json", normalized)

if __name__ == "__main__":
    main()

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
    else:
        norm["included_in_handoff"] = False
        norm["handoff_payload"] = None
        norm["handoff_payload_id"] = None
        norm["handoff_payload_version"] = None
        norm["runner_mode"] = None
        norm["target_report_types"] = None
    return norm

def normalize_events(events):
    return [normalize_event(e) for e in events]

def write_json(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Batch Handoff Builder",
        "",
        "This deterministic output is based on embedded source fixtures, adapter logic, dependency readiness, and batch handoff packaging.",
        "",
        "## Adapter Coverage",
        f"- UFC: {len([r for r in records if r['source_name']=='UFC_API'])} event(s)",
        f"- PFL: {len([r for r in records if r['source_name']=='PFL_FEED'])} event(s)",
        f"- ONE: {len([r for r in records if r['source_name']=='ONE_CHAMPIONSHIP'])} event(s)",
        "",
        f"## Handoff Ready: {sum(1 for r in records if r['handoff_ready'])} / {len(records)}",
        f"## Included in Handoff: {sum(1 for r in records if r['included_in_handoff'])}",
        f"## Blocked Events: {sum(1 for r in records if not r['handoff_ready'])}",
        "",
        "## Handoff Payload IDs",
    ]
    for rec in records:
        if rec["included_in_handoff"] and rec["handoff_payload_id"]:
            lines.append(f"- {rec['handoff_payload_id']}")
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
            f"**Dependency Status:** {rec['dependency_status']} | **Handoff Ready:** {rec['handoff_ready']} | "
            f"**Included in Handoff:** {rec['included_in_handoff']}"
        )
        if rec["missing_fields"]:
            lines.append(f"  - Missing: {', '.join(rec['missing_fields'])}")
        if rec["handoff_blockers"]:
            lines.append(f"  - Blockers: {', '.join(rec['handoff_blockers'])}")
        if not rec["included_in_handoff"]:
            lines.append("  - Excluded from handoff: not handoff-ready")
    lines.extend([
        "",
        "This file defines the normalization contract, adapter coverage, dependency readiness, batch handoff packaging, and batch handoff format.",
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

if __name__ == "__main__":
    main()

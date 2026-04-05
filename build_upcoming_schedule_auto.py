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
    return norm

def normalize_events(events):
    return [normalize_event(e) for e in events]

def write_json(path, records):
    path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Live-Source Adapter",
        "",
        "This deterministic output is based on embedded source fixtures and adapter logic.",
        "",
        "## Adapter Coverage",
        f"- UFC: {len([r for r in records if r['source_name']=='UFC_API'])} event(s)",
        f"- PFL: {len([r for r in records if r['source_name']=='PFL_FEED'])} event(s)",
        f"- ONE: {len([r for r in records if r['source_name']=='ONE_CHAMPIONSHIP'])} event(s)",
        "",
        "## Normalized Events",
        "",
    ]
    for rec in records:
        divisions = ", ".join(rec["divisions"]) if rec["divisions"] else "None"
        lines.append(
            f"- **ID:** {rec['event_id']} | **Date:** {rec['date']} | **Promotion:** {rec['promotion']} | "
            f"**Venue:** {rec['venue']} | **Sport:** {rec['sport']} | **Divisions:** {divisions} | "
            f"**Source:** {rec['source_name']} | **Adapter Status:** {rec['adapter_status']} | **Complete:** {rec['complete']}"
        )
        if rec["missing_fields"]:
            lines.append(f"  - Missing: {', '.join(rec['missing_fields'])}")
    lines.extend([
        "",
        "This file defines the normalization contract, adapter coverage, and batch handoff format.",
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

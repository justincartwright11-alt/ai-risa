import json
from pathlib import Path

EMBEDDED_EVENTS = [
    {
        "event_id": "ufc_300",
        "date": "2026-04-13",
        "promotion": "UFC",
        "venue": "T-Mobile Arena",
        "sport": "MMA",
        "divisions": ["Lightweight", "Welterweight"],
    },
    {
        "event_id": "pfl_2026_01",
        "date": "2026-05-01",
        "promotion": "PFL",
        "venue": None,
        "sport": "MMA",
        "divisions": ["Featherweight"],
    },
    {
        "event_id": "one_2026_04",
        "date": None,
        "promotion": "ONE",
        "venue": "Singapore Indoor Stadium",
        "sport": "MMA",
        "divisions": [],
    },
]

REQUIRED_FIELDS = ["event_id", "date", "promotion", "venue", "sport", "divisions"]


def normalize_event(event):
    normalized = {
        "event_id": event.get("event_id") or "unknown",
        "date": event.get("date") or "unknown",
        "promotion": event.get("promotion") or "unknown",
        "venue": event.get("venue") or "unknown",
        "sport": event.get("sport") or "unknown",
        "divisions": event.get("divisions") or [],
    }
    missing_fields = []
    for field in REQUIRED_FIELDS:
        value = normalized[field]
        if field == "divisions":
            if not value:
                missing_fields.append(field)
        elif value == "unknown":
            missing_fields.append(field)
    normalized["complete"] = len(missing_fields) == 0
    normalized["missing_fields"] = missing_fields
    return normalized


def normalize_events(events):
    return [normalize_event(event) for event in events]


def write_json(path, records):
    path.write_text(
        json.dumps(records, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_markdown(path, records):
    lines = [
        "# Upcoming Schedule Auto-Discovery Normalization Scaffold",
        "",
        "This deterministic output is based on a fixed embedded event snapshot.",
        "",
        "## Normalized Events",
        "",
    ]
    for record in records:
        divisions = ", ".join(record["divisions"]) if record["divisions"] else "None"
        lines.append(
            f"- **ID:** {record['event_id']} | **Date:** {record['date']} | "
            f"**Promotion:** {record['promotion']} | **Venue:** {record['venue']} | "
            f"**Sport:** {record['sport']} | **Divisions:** {divisions} | "
            f"**Complete:** {record['complete']}"
        )
        if record["missing_fields"]:
            lines.append(f"  - Missing: {', '.join(record['missing_fields'])}")
    lines.extend(
        [
            "",
            "This file defines the normalization contract and batch handoff format.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main():
    output_dir = Path("ops/events")
    output_dir.mkdir(parents=True, exist_ok=True)
    records = normalize_events(EMBEDDED_EVENTS)
    write_json(output_dir / "upcoming_schedule_auto_discovery.json", records)
    write_markdown(output_dir / "upcoming_schedule_auto_discovery.md", records)


if __name__ == "__main__":
    main()

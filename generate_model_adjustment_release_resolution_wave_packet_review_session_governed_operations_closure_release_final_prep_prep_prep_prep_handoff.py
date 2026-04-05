from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PARENT_PATH = ROOT / "ops" / "model_adjustments" / (
    "model_adjustment_release_resolution_wave_packet_review_session_"
    "governed_operations_closure_release_final_prep_prep_prep_prep_register.json"
)
OUTPUT_JSON = ROOT / "ops" / "model_adjustments" / (
    "model_adjustment_release_resolution_wave_packet_review_session_"
    "governed_operations_closure_release_final_prep_prep_prep_prep_handoff.json"
)
OUTPUT_MD = ROOT / "ops" / "model_adjustments" / (
    "model_adjustment_release_resolution_wave_packet_review_session_"
    "governed_operations_closure_release_final_prep_prep_prep_prep_handoff.md"
)

PARENT_ARTIFACT_REL = (
    "ops/model_adjustments/"
    "model_adjustment_release_resolution_wave_packet_review_session_"
    "governed_operations_closure_release_final_prep_prep_prep_prep_register.json"
)

HANDOFF_PREFIX = "closure-release-final-prep-prep-prep-prep-handoff"


def load_parent() -> dict[str, Any]:
    with PARENT_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Parent register must be a top-level list.")
    return data


def pick_locator_key(parent_record: dict[str, Any], position: int) -> str:
    candidates = [
        "locator_key",
        "slug",
        "name",
        "title",
        "register_id",
        "map_id",
        "id",
    ]
    for key in candidates:
        value = parent_record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"record-{position:04d}"


def source_register_id(parent_record: dict[str, Any], position: int) -> str:
    candidates = ["register_id", "id", "map_id"]
    for key in candidates:
        value = parent_record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError(f"Parent record {position} lacks a usable source register id.")


def build_handoff_record(parent_record: dict[str, Any], position: int) -> dict[str, Any]:
    child = {
        "handoff_id": f"{HANDOFF_PREFIX}-{position:04d}",
        "handoff_position": position,
        "source_register_id": source_register_id(parent_record, position),
        "source_register_position": position,
        "source_register_artifact": PARENT_ARTIFACT_REL,
        "handoff_locator_key": pick_locator_key(parent_record, position),
    }
    for key in [
        "register_id",
        "map_id",
        "record_type",
        "status",
        "name",
        "title",
        "slug",
    ]:
        if key in parent_record:
            child[key] = parent_record[key]
    return child


def build_output(parent: list[dict[str, Any]]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    seen_source_ids: set[str] = set()
    for idx, parent_record in enumerate(parent, start=1):
        if not isinstance(parent_record, dict):
            raise ValueError(f"Parent record {idx} is not an object.")
        child = build_handoff_record(parent_record, idx)
        sid = child["source_register_id"]
        if sid in seen_source_ids:
            raise ValueError(f"Duplicate source_register_id detected: {sid}")
        seen_source_ids.add(sid)
        records.append(child)
    output = {
        "parent_artifact": PARENT_ARTIFACT_REL,
        "record_count": len(records),
        "records": records,
    }
    validate_output(parent, output)
    return output


def validate_output(parent: list[dict[str, Any]], output: dict[str, Any]) -> None:
    records = output["records"]
    if output["record_count"] != len(records):
        raise ValueError("record_count does not match len(records).")
    if len(records) != len(parent):
        raise ValueError("Child record count does not equal parent record count.")
    for idx, child in enumerate(records, start=1):
        if child["handoff_position"] != idx:
            raise ValueError(f"handoff_position mismatch at record {idx}")
        if child["source_register_position"] != idx:
            raise ValueError(f"source_register_position mismatch at record {idx}")
        expected_id = f"{HANDOFF_PREFIX}-{idx:04d}"
        if child["handoff_id"] != expected_id:
            raise ValueError(f"handoff_id mismatch at record {idx}")
    source_ids = [r["source_register_id"] for r in records]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_register_id values are not unique.")


def render_markdown(output: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# closure-release-final-prep-prep-prep-prep-handoff")
    lines.append("")
    lines.append(f"- parent_artifact: {output['parent_artifact']}")
    lines.append(f"- record_count: {output['record_count']}")
    lines.append("")
    lines.append("| handoff_id | handoff_position | source_register_id | handoff_locator_key |")
    lines.append("|---|---:|---|---|")
    for record in output["records"]:
        lines.append(
            f"| {record['handoff_id']} | "
            f"{record['handoff_position']} | "
            f"{record['source_register_id']} | "
            f"{record['handoff_locator_key']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_json(output: dict[str, Any]) -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_markdown(md: str) -> None:
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(md, encoding="utf-8", newline="\n")


def main() -> None:
    parent = load_parent()
    output = build_output(parent)
    md = render_markdown(output)
    write_json(output)
    write_markdown(md)


if __name__ == "__main__":
    main()

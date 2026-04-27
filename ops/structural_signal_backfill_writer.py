from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_FIELDS = {
    "fight_id",
    "source_file",
    "signal_gap",
    "stoppage_propensity",
    "round_finish_tendency",
    "evidence_note",
}
STRUCTURAL_FIELDS = ["signal_gap", "stoppage_propensity", "round_finish_tendency"]


class WriterValidationError(Exception):
    pass


@dataclass(frozen=True)
class PatchEntry:
    fight_id: str
    source_file: str
    signal_gap: float
    stoppage_propensity: float
    round_finish_tendency: float
    evidence_note: str

    def updates(self) -> dict[str, float]:
        return {
            "signal_gap": self.signal_gap,
            "stoppage_propensity": self.stoppage_propensity,
            "round_finish_tendency": self.round_finish_tendency,
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "unknown", "n/a", "null"}:
        return True
    return False


def _as_float(value: Any, field: str) -> float:
    if isinstance(value, bool):
        raise WriterValidationError(f"{field} must be numeric, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError as exc:
            raise WriterValidationError(f"{field} must be numeric, got {value!r}") from exc
    raise WriterValidationError(f"{field} must be numeric, got {type(value).__name__}")


def _load_patch_file(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WriterValidationError(f"Failed to parse patch file: {path}") from exc

    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("patches"), list):
        rows = payload["patches"]
    else:
        raise WriterValidationError("Patch JSON must be a list or an object with a 'patches' list")

    if not rows:
        raise WriterValidationError("Patch JSON contains no entries")
    return rows


def _resolve_source(repo_root: Path, source_file: str) -> Path:
    source_rel = source_file.replace("\\", "/")
    path = (repo_root / source_rel).resolve()
    if not str(path).startswith(str(repo_root.resolve())):
        raise WriterValidationError(f"Ambiguous source_file path outside repo: {source_file}")
    if not path.exists() or not path.is_file():
        raise WriterValidationError(f"Missing source file: {source_file}")
    return path


def _parse_entry(raw: dict[str, Any], repo_root: Path) -> tuple[PatchEntry, Path, dict[str, Any]]:
    extra = set(raw.keys()) - ALLOWED_FIELDS
    if extra:
        raise WriterValidationError(f"Unknown fields in patch entry for {raw.get('fight_id', 'unknown')}: {sorted(extra)}")

    required = [
        "fight_id",
        "source_file",
        "signal_gap",
        "stoppage_propensity",
        "round_finish_tendency",
        "evidence_note",
    ]
    missing = [k for k in required if k not in raw]
    if missing:
        raise WriterValidationError(f"Missing required fields for {raw.get('fight_id', 'unknown')}: {missing}")

    fight_id = str(raw["fight_id"]).strip()
    source_file = str(raw["source_file"]).strip()
    evidence_note = str(raw["evidence_note"]).strip()
    if not fight_id or not source_file or not evidence_note:
        raise WriterValidationError("fight_id, source_file, and evidence_note must be non-empty")

    source_path = _resolve_source(repo_root, source_file)
    try:
        data = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WriterValidationError(f"Source file is not valid JSON: {source_file}") from exc
    if not isinstance(data, dict):
        raise WriterValidationError(f"Source JSON must be an object: {source_file}")

    embedded_fight_id = str(data.get("fight_id", "")).strip()
    stem_fight_id = source_path.stem
    if embedded_fight_id:
        if embedded_fight_id != fight_id:
            raise WriterValidationError(
                f"fight_id mismatch for {source_file}: patch={fight_id} source={embedded_fight_id}"
            )
    elif stem_fight_id != fight_id:
        raise WriterValidationError(
            f"fight_id mismatch for {source_file}: patch={fight_id} source_stem={stem_fight_id}"
        )

    entry = PatchEntry(
        fight_id=fight_id,
        source_file=source_file,
        signal_gap=_as_float(raw["signal_gap"], "signal_gap"),
        stoppage_propensity=_as_float(raw["stoppage_propensity"], "stoppage_propensity"),
        round_finish_tendency=_as_float(raw["round_finish_tendency"], "round_finish_tendency"),
        evidence_note=evidence_note,
    )
    return entry, source_path, data


def _build_changes(
    rows: list[dict[str, Any]],
    allow_overwrite: bool,
) -> list[dict[str, Any]]:
    repo_root = _repo_root()
    planned: list[dict[str, Any]] = []
    seen_targets: set[tuple[str, str]] = set()

    for raw in rows:
        if not isinstance(raw, dict):
            raise WriterValidationError("Each patch entry must be a JSON object")

        entry, source_path, data = _parse_entry(raw, repo_root)
        target_key = (entry.fight_id, str(source_path))
        if target_key in seen_targets:
            raise WriterValidationError(f"Ambiguous duplicate patch entry for fight_id={entry.fight_id}")
        seen_targets.add(target_key)

        before: dict[str, Any] = {}
        after: dict[str, Any] = {}
        for field, new_val in entry.updates().items():
            current = data.get(field)
            if not allow_overwrite and not _is_missing(current):
                raise WriterValidationError(
                    f"Existing structural value for {entry.fight_id}:{field}={current!r}; use --allow-overwrite"
                )
            before[field] = current
            after[field] = new_val

        planned.append(
            {
                "entry": entry,
                "source_path": source_path,
                "source_data": data,
                "before": before,
                "after": after,
            }
        )

    return planned


def _audit_path(repo_root: Path) -> Path:
    return repo_root / "ops" / "audit" / "structural_signal_backfill_audit.jsonl"


def run_writer(
    patch_file: Path,
    dry_run: bool = True,
    apply: bool = False,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    if dry_run and apply:
        raise WriterValidationError("Choose either --dry-run or --apply")

    mode = "dry-run" if not apply else "apply"
    rows = _load_patch_file(patch_file)
    planned = _build_changes(rows, allow_overwrite=allow_overwrite)

    summary = {
        "mode": mode,
        "patch_file": str(patch_file),
        "entry_count": len(planned),
        "proposed_changes": [
            {
                "fight_id": p["entry"].fight_id,
                "source_file": p["entry"].source_file,
                "before": p["before"],
                "after": p["after"],
                "evidence_note": p["entry"].evidence_note,
            }
            for p in planned
        ],
    }

    if apply:
        repo_root = _repo_root()
        for p in planned:
            data = dict(p["source_data"])
            data.update(p["after"])
            p["source_path"].write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        audit_file = _audit_path(repo_root)
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        with audit_file.open("a", encoding="utf-8") as f:
            for p in planned:
                line = {
                    "timestamp_utc": timestamp,
                    "action": "structural_signal_backfill_apply",
                    "fight_id": p["entry"].fight_id,
                    "source_file": p["entry"].source_file,
                    "fields_written": STRUCTURAL_FIELDS,
                    "before": p["before"],
                    "after": p["after"],
                    "evidence_note": p["entry"].evidence_note,
                    "patch_file": str(patch_file),
                }
                f.write(json.dumps(line) + "\n")

        summary["audit_file"] = str(audit_file)

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Structural signal backfill writer (dry-run first)")
    parser.add_argument("patch_file", help="Path to patch JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print proposed changes")
    parser.add_argument("--apply", action="store_true", help="Apply validated changes")
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Allow overwrite when structural fields already contain non-missing values",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    # Default to dry-run for safety if neither mode is set.
    dry_run = args.dry_run or not args.apply

    try:
        summary = run_writer(
            patch_file=Path(args.patch_file),
            dry_run=dry_run,
            apply=args.apply,
            allow_overwrite=args.allow_overwrite,
        )
    except WriterValidationError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

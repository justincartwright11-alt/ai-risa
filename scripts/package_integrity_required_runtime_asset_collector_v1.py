from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List, Tuple


# Contract-corrected required runtime assets for script-root startup semantics.
REQUIRED_RUNTIME_ASSETS: Tuple[Tuple[str, str], ...] = (
    ("runtime/app.py", "file"),
    ("manifests", "directory"),
    ("governance_docs", "directory"),
    ("tests", "directory"),
)


def collect_required_runtime_asset_presence(package_root: Path) -> List[Tuple[str, bool, str]]:
    rows: List[Tuple[str, bool, str]] = []
    package_root = package_root.resolve()

    for rel_path, item_type in REQUIRED_RUNTIME_ASSETS:
        target = package_root / rel_path
        exists = target.exists()

        if exists:
            if item_type == "file":
                exists = target.is_file()
            elif item_type == "directory":
                exists = target.is_dir()

        rows.append((f"{package_root.name}/{rel_path}".replace("\\", "/"), exists, item_type))

    return rows


def write_presence_csv(output_csv: Path, rows: Iterable[Tuple[str, bool, str]]) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["asset_path", "exists", "item_type"])
        for asset_path, exists, item_type in rows:
            writer.writerow([asset_path, "True" if exists else "False", item_type])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect required runtime asset presence using corrected collector contract."
    )
    parser.add_argument("--package-root", required=True, help="Path to package root")
    parser.add_argument("--output-csv", required=True, help="Path to output CSV")
    args = parser.parse_args()

    package_root = Path(args.package_root)
    output_csv = Path(args.output_csv)

    rows = collect_required_runtime_asset_presence(package_root)
    write_presence_csv(output_csv, rows)

    # Guardrail: runtime/__init__.py must not be treated as required under this contract.
    forbidden = [asset for asset, _exists, _type in rows if asset.endswith("/runtime/__init__.py")]
    if forbidden:
        raise SystemExit("Contract defect: runtime/__init__.py present in required runtime asset set")

    print(f"required_assets_count={len(rows)}")
    print("runtime_init_required=False")
    print(f"output_csv={output_csv.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

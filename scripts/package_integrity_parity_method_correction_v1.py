from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence


WORKSPACE_PREFIX = "C:/Users/jusin/OneDrive/Documents/Custom Office Templates/"


@dataclass(frozen=True)
class Residual:
    path: str
    category: str
    reason: str


def _norm(path: str) -> str:
    p = path.replace("\\", "/")
    if p.startswith(WORKSPACE_PREFIX):
        return p[len(WORKSPACE_PREFIX) :]
    return p


def _is_pycache_artifact(path: str) -> bool:
    return "/__pycache__/" in path or path.endswith(".pyc")


def _is_console_rollup_artifact(path: str) -> bool:
    if "internal_operator_preview_automatic_background_workflow_preview_post_remediation_endpoint_replay_v1/console/" not in path:
        return False
    return path.endswith("runtime_stdout_combined_v1.txt") or path.endswith("runtime_stderr_combined_v1.txt") or "runtime_stdout_combined_" in path or "runtime_stderr_combined_" in path


def _is_collection_control_artifact(path: str) -> bool:
    return path.endswith(
        "evidence/package_integrity_evidence_collection_control_sequence_correction_v1/package_integrity_baseline_integrity_check_v1.txt"
    )


def classify_unmatched(paths: Sequence[str]) -> List[Residual]:
    residuals: List[Residual] = []
    for path in paths:
        if _is_pycache_artifact(path):
            residuals.append(
                Residual(
                    path=path,
                    category="COLLECTION_METHOD_ARTIFACT",
                    reason="Ephemeral bytecode artifact (__pycache__/.pyc) should be excluded from parity surface.",
                )
            )
            continue

        if _is_console_rollup_artifact(path):
            residuals.append(
                Residual(
                    path=path,
                    category="COLLECTION_METHOD_ARTIFACT",
                    reason="Volatile replay console rollup artifact should be excluded from parity surface.",
                )
            )
            continue

        if _is_collection_control_artifact(path):
            residuals.append(
                Residual(
                    path=path,
                    category="EVIDENCE_SELF_INCLUSION",
                    reason="Collector control-sequence artifact belongs to evidence/control context, not package parity defect class.",
                )
            )
            continue

        residuals.append(
            Residual(
                path=path,
                category="TRUE_PACKAGE_DEFECT",
                reason="Unclassified residual remained after method normalization and artifact exclusions.",
            )
        )
    return residuals


def run(parity_csv: Path, output_csv: Path) -> Dict[str, int]:
    with parity_csv.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    type_key = "type"
    if rows and type_key not in rows[0]:
        for candidate in rows[0].keys():
            if candidate and candidate.lstrip("\ufeff") == "type":
                type_key = candidate
                break

    missing = [_norm(r["path"]) for r in rows if r.get(type_key) == "missing_tracked"]
    unexpected = [_norm(r["path"]) for r in rows if r.get(type_key) == "unexpected_current"]

    missing_set = set(missing)
    unmatched_unexpected = [p for p in unexpected if p not in missing_set]

    residuals = classify_unmatched(unmatched_unexpected)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["path", "category", "reason"])
        for r in residuals:
            writer.writerow([r.path, r.category, r.reason])

    counts: Dict[str, int] = {
        "unmatched_unexpected_total": len(unmatched_unexpected),
        "COLLECTION_METHOD_ARTIFACT": 0,
        "EVIDENCE_SELF_INCLUSION": 0,
        "TRUE_PACKAGE_DEFECT": 0,
    }
    for r in residuals:
        counts[r.category] = counts.get(r.category, 0) + 1

    return counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Focused parity-method residual classifier for unmatched unexpected entries."
    )
    parser.add_argument("--parity-csv", required=True)
    parser.add_argument("--output-csv", required=True)
    args = parser.parse_args()

    counts = run(Path(args.parity_csv), Path(args.output_csv))

    verdict = (
        "PACKAGE_INTEGRITY_RESIDUALS_EXPLAINED"
        if counts.get("TRUE_PACKAGE_DEFECT", 0) == 0
        else "PACKAGE_INTEGRITY_REMEDIATION_REQUIRED"
    )

    print(f"unmatched_unexpected_total={counts['unmatched_unexpected_total']}")
    print(f"collection_method_artifact={counts.get('COLLECTION_METHOD_ARTIFACT', 0)}")
    print(f"evidence_self_inclusion={counts.get('EVIDENCE_SELF_INCLUSION', 0)}")
    print(f"true_package_defect={counts.get('TRUE_PACKAGE_DEFECT', 0)}")
    print(f"decision={verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

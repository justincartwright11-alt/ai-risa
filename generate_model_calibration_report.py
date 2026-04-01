#!/usr/bin/env python3
"""
AI-RISA v1.7 Model Calibration (slice 1): read-only calibration analysis.

Builds a calibration summary from existing prediction outputs and resolved outcome
artifacts. This script does not mutate model behavior, scheduler logic, or
pipeline outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT_DEFAULT = Path("C:/ai_risa_data")
OUTPUT_DIR = Path("ops/calibration")
OUTPUT_JSON = "model_calibration_report.json"
OUTPUT_MD = "model_calibration_report.md"

RECONCILIATION_CSV_DEFAULT = Path("reports/reconciliation_history_match_report.csv")
PREDICTION_QUEUE_JSON_DEFAULT = Path("output/prediction_queue.json")

CONFIDENCE_BUCKETS: list[tuple[float, float, str]] = [
    (0.0, 0.50, "0.00-0.49"),
    (0.50, 0.60, "0.50-0.59"),
    (0.60, 0.70, "0.60-0.69"),
    (0.70, 0.80, "0.70-0.79"),
    (0.80, 0.90, "0.80-0.89"),
    (0.90, 1.01, "0.90-1.00"),
]

HIGH_CONFIDENCE_THRESHOLD = 0.70
LOW_CONFIDENCE_THRESHOLD = 0.55


@dataclass
class EvalRow:
    matchup_id: str
    event: str
    predicted_winner_id: str
    actual_winner_id: str
    winner_correct: bool
    predicted_method: str
    actual_method: str
    method_correct: bool | None
    round_error: float | None
    confidence: float | None


@dataclass
class UnevaluableRow:
    matchup_id: str
    reason: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate read-only model calibration report artifacts"
    )
    parser.add_argument("--repo-root", default=str(REPO_ROOT_DEFAULT))
    parser.add_argument(
        "--reconciliation-csv",
        default=str(RECONCILIATION_CSV_DEFAULT),
        help="Resolved prediction-vs-actual CSV relative to repo root",
    )
    parser.add_argument(
        "--prediction-queue-json",
        default=str(PREDICTION_QUEUE_JSON_DEFAULT),
        help="Prediction queue JSON relative to repo root",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Calibration output directory relative to repo root",
    )
    return parser.parse_args()


def normalize_path(path: Path) -> str:
    return path.as_posix()


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_confidence(value: Any) -> float | None:
    num = parse_float(value)
    if num is None:
        return None
    # Handle percentage-style confidence values such as 72 or 72.5.
    if num > 1.0 and num <= 100.0:
        num = num / 100.0
    if num < 0.0 or num > 1.0:
        return None
    return num


def safe_read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def safe_read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def load_evaluation_rows(rows: list[dict[str, str]]) -> tuple[list[EvalRow], list[UnevaluableRow]]:
    evaluated: list[EvalRow] = []
    unevaluable: list[UnevaluableRow] = []

    for row in rows:
        winner_correct = parse_bool(row.get("winner_correct"))
        method_correct = parse_bool(row.get("method_correct"))
        confidence = normalize_confidence(row.get("confidence"))
        matchup_id = str(row.get("matchup_id") or row.get("matchup_id_recon") or "")

        if winner_correct is None:
            unevaluable.append(
                UnevaluableRow(
                    matchup_id=matchup_id,
                    reason="winner_correct_missing_or_invalid",
                )
            )
            continue

        evaluated.append(
            EvalRow(
                matchup_id=matchup_id,
                event=str(row.get("event") or row.get("event_recon") or row.get("event_hist") or ""),
                predicted_winner_id=str(row.get("predicted_winner_id_recon") or row.get("predicted_winner_id") or ""),
                actual_winner_id=str(row.get("actual_winner_id") or ""),
                winner_correct=winner_correct,
                predicted_method=str(row.get("predicted_method") or row.get("method_recon") or ""),
                actual_method=str(row.get("actual_method") or row.get("method_hist") or ""),
                method_correct=method_correct,
                round_error=parse_float(row.get("round_error")),
                confidence=confidence,
            )
        )

    return evaluated, unevaluable


def confidence_bucket_label(confidence: float) -> str:
    for lo, hi, label in CONFIDENCE_BUCKETS:
        if lo <= confidence < hi:
            return label
    return "unknown"


def summarize_confidence(evaluated: list[EvalRow]) -> dict[str, Any]:
    with_conf = [row for row in evaluated if row.confidence is not None]
    coverage = (len(with_conf) / len(evaluated)) if evaluated else 0.0

    bucket_stats: dict[str, dict[str, Any]] = {}
    for _, _, label in CONFIDENCE_BUCKETS:
        bucket_stats[label] = {
            "count": 0,
            "correct": 0,
            "incorrect": 0,
            "avg_confidence": None,
            "empirical_accuracy": None,
            "calibration_gap": None,
        }

    conf_sums: dict[str, float] = {label: 0.0 for _, _, label in CONFIDENCE_BUCKETS}

    for row in with_conf:
        label = confidence_bucket_label(row.confidence if row.confidence is not None else -1)
        if label not in bucket_stats:
            continue
        bucket_stats[label]["count"] += 1
        if row.winner_correct:
            bucket_stats[label]["correct"] += 1
        else:
            bucket_stats[label]["incorrect"] += 1
        conf_sums[label] += float(row.confidence)

    for label, stats in bucket_stats.items():
        count = int(stats["count"])
        if count <= 0:
            continue
        avg_conf = conf_sums[label] / count
        emp_acc = stats["correct"] / count
        stats["avg_confidence"] = round(avg_conf, 4)
        stats["empirical_accuracy"] = round(emp_acc, 4)
        stats["calibration_gap"] = round(avg_conf - emp_acc, 4)

    avg_confidence = (
        sum(float(row.confidence) for row in with_conf if row.confidence is not None) / len(with_conf)
        if with_conf
        else None
    )
    empirical_accuracy = (
        sum(1 for row in with_conf if row.winner_correct) / len(with_conf)
        if with_conf
        else None
    )

    high_conf = [row for row in with_conf if (row.confidence or 0.0) >= HIGH_CONFIDENCE_THRESHOLD]
    low_conf = [row for row in with_conf if (row.confidence or 0.0) <= LOW_CONFIDENCE_THRESHOLD]

    high_conf_incorrect = sum(1 for row in high_conf if not row.winner_correct)
    low_conf_correct = sum(1 for row in low_conf if row.winner_correct)

    return {
        "confidence_coverage": round(coverage, 4),
        "rows_with_confidence": len(with_conf),
        "rows_without_confidence": max(0, len(evaluated) - len(with_conf)),
        "overall_avg_confidence": round(avg_confidence, 4) if avg_confidence is not None else None,
        "overall_empirical_accuracy": round(empirical_accuracy, 4) if empirical_accuracy is not None else None,
        "overall_calibration_gap": (
            round(avg_confidence - empirical_accuracy, 4)
            if avg_confidence is not None and empirical_accuracy is not None
            else None
        ),
        "overconfidence_indicator": {
            "high_confidence_threshold": HIGH_CONFIDENCE_THRESHOLD,
            "sample_count": len(high_conf),
            "incorrect_count": high_conf_incorrect,
            "incorrect_rate": round(high_conf_incorrect / len(high_conf), 4) if high_conf else None,
        },
        "underconfidence_indicator": {
            "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
            "sample_count": len(low_conf),
            "correct_count": low_conf_correct,
            "correct_rate": round(low_conf_correct / len(low_conf), 4) if low_conf else None,
        },
        "confidence_buckets": bucket_stats,
    }


def summarize_miss_patterns(evaluated: list[EvalRow]) -> dict[str, Any]:
    incorrect = [row for row in evaluated if not row.winner_correct]

    wrong_winner_counter: Counter[str] = Counter()
    method_mismatch_counter: Counter[str] = Counter()
    round_error_counter: Counter[str] = Counter()

    for row in incorrect:
        pred = row.predicted_winner_id.strip()
        if pred:
            wrong_winner_counter[pred] += 1

        if row.predicted_method and row.actual_method and row.predicted_method != row.actual_method:
            key = f"{row.predicted_method} -> {row.actual_method}"
            method_mismatch_counter[key] += 1

        if row.round_error is not None:
            abs_err = abs(row.round_error)
            if abs_err >= 2.0:
                round_error_counter[">=2 rounds"] += 1
            elif abs_err >= 1.0:
                round_error_counter["1 round"] += 1

    recurring_patterns: list[dict[str, Any]] = []

    for name, count in wrong_winner_counter.most_common(5):
        recurring_patterns.append(
            {
                "pattern_type": "repeated_incorrect_predicted_winner",
                "pattern": name,
                "count": count,
            }
        )

    for name, count in method_mismatch_counter.most_common(5):
        recurring_patterns.append(
            {
                "pattern_type": "method_mismatch",
                "pattern": name,
                "count": count,
            }
        )

    for name, count in round_error_counter.most_common(5):
        recurring_patterns.append(
            {
                "pattern_type": "round_projection_error_band",
                "pattern": name,
                "count": count,
            }
        )

    recurring_patterns.sort(key=lambda row: int(row.get("count") or 0), reverse=True)

    return {
        "total_incorrect": len(incorrect),
        "top_recurring_patterns": recurring_patterns[:10],
    }


def summarize_unevaluable(
    unevaluable_reconciliation: list[UnevaluableRow], prediction_queue_payload: Any
) -> dict[str, Any]:
    queue_rows = prediction_queue_payload if isinstance(prediction_queue_payload, list) else []
    queue_reason_counter: Counter[str] = Counter()
    for row in queue_rows:
        if not isinstance(row, dict):
            continue
        queue_reason_counter[str(row.get("reason") or "unknown")] += 1

    unreconciled_reason_counter: Counter[str] = Counter(
        row.reason for row in unevaluable_reconciliation
    )

    return {
        "reconciliation_unevaluable_count": len(unevaluable_reconciliation),
        "reconciliation_unevaluable_reasons": dict(unreconciled_reason_counter),
        "prediction_queue_pending_count": len(queue_rows),
        "prediction_queue_pending_reasons": dict(queue_reason_counter),
        "total_unevaluable_or_pending": len(unevaluable_reconciliation) + len(queue_rows),
    }


def build_recommendations(
    evaluated_count: int,
    confidence_summary: dict[str, Any],
    miss_patterns: dict[str, Any],
    unevaluable_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    if evaluated_count < 20:
        recommendations.append(
            {
                "priority": 1,
                "action": "Increase evaluated sample size before high-confidence recalibration decisions.",
                "reason": "Low evaluated volume can hide real calibration drift.",
            }
        )

    if float(confidence_summary.get("confidence_coverage") or 0.0) < 0.70:
        recommendations.append(
            {
                "priority": 1,
                "action": "Backfill or standardize confidence values in resolved prediction records.",
                "reason": "Confidence diagnostics are weak when confidence coverage is low.",
            }
        )

    gap = confidence_summary.get("overall_calibration_gap")
    if isinstance(gap, (int, float)) and abs(float(gap)) >= 0.08:
        recommendations.append(
            {
                "priority": 1,
                "action": "Prepare a calibration patch candidate to reduce overall confidence-accuracy gap.",
                "reason": f"Observed overall calibration gap = {round(float(gap), 4)}.",
            }
        )

    high_conf_error_rate = (
        (confidence_summary.get("overconfidence_indicator") or {}).get("incorrect_rate")
    )
    high_conf_sample_count = (
        (confidence_summary.get("overconfidence_indicator") or {}).get("sample_count")
    )
    if (
        isinstance(high_conf_error_rate, (int, float))
        and isinstance(high_conf_sample_count, int)
        and high_conf_sample_count >= 5
        and high_conf_error_rate >= 0.20
    ):
        recommendations.append(
            {
                "priority": 1,
                "action": "Audit high-confidence misses by prediction family and fighter-style cluster.",
                "reason": "High-confidence miss rate is elevated.",
            }
        )

    if int(miss_patterns.get("total_incorrect") or 0) > 0 and (
        miss_patterns.get("top_recurring_patterns") or []
    ):
        recommendations.append(
            {
                "priority": 2,
                "action": "Target recurring miss patterns for feature-level error analysis.",
                "reason": "Recurring error signatures are present in incorrect predictions.",
            }
        )

    pending = int(unevaluable_summary.get("prediction_queue_pending_count") or 0)
    if pending > evaluated_count:
        recommendations.append(
            {
                "priority": 2,
                "action": "Prioritize result reconciliation throughput so calibration uses more resolved outcomes.",
                "reason": "Pending/unevaluable volume exceeds evaluated volume.",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "priority": 3,
                "action": "Maintain current calibration monitoring cadence; no acute drift signals found.",
                "reason": "Calibration indicators are currently stable with available data.",
            }
        )

    recommendations.sort(key=lambda row: int(row.get("priority") or 99))
    return recommendations


def build_calibration_report_payload(
    repo_root: Path,
    reconciliation_csv_path: Path,
    prediction_queue_json_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    recon_rows = safe_read_csv(repo_root / reconciliation_csv_path)
    prediction_queue_payload = safe_read_json(repo_root / prediction_queue_json_path)

    evaluated, unevaluable_reconciliation = load_evaluation_rows(recon_rows)

    total_evaluated = len(evaluated)
    correct_count = sum(1 for row in evaluated if row.winner_correct)
    incorrect_count = total_evaluated - correct_count

    confidence_summary = summarize_confidence(evaluated)
    miss_patterns = summarize_miss_patterns(evaluated)
    unevaluable_summary = summarize_unevaluable(
        unevaluable_reconciliation,
        prediction_queue_payload,
    )

    recommendations = build_recommendations(
        total_evaluated,
        confidence_summary,
        miss_patterns,
        unevaluable_summary,
    )

    return {
        "calibration_report_version": "v1.7-slice-1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "reconciliation_csv": {
                "path": normalize_path(reconciliation_csv_path),
                "exists": (repo_root / reconciliation_csv_path).exists(),
                "rows": len(recon_rows),
            },
            "prediction_queue_json": {
                "path": normalize_path(prediction_queue_json_path),
                "exists": (repo_root / prediction_queue_json_path).exists(),
                "rows": len(prediction_queue_payload) if isinstance(prediction_queue_payload, list) else 0,
            },
        },
        "evaluation_summary": {
            "total_evaluated_predictions": total_evaluated,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "winner_accuracy": round(correct_count / total_evaluated, 4) if total_evaluated else None,
            "evaluated_vs_unevaluable": {
                "evaluated": total_evaluated,
                "unevaluable_or_pending": int(unevaluable_summary.get("total_unevaluable_or_pending") or 0),
            },
        },
        "confidence_quality": confidence_summary,
        "unevaluable_summary": unevaluable_summary,
        "miss_pattern_summary": miss_patterns,
        "recommended_follow_up_actions": recommendations,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    eval_summary = payload.get("evaluation_summary") or {}
    confidence = payload.get("confidence_quality") or {}
    unevaluable = payload.get("unevaluable_summary") or {}
    misses = payload.get("miss_pattern_summary") or {}
    recommendations = payload.get("recommended_follow_up_actions") or []
    sources = payload.get("sources") or {}

    lines: list[str] = []
    lines.append("# AI-RISA Model Calibration Report (Slice 1)")
    lines.append("")
    lines.append(f"Generated (UTC): {payload.get('generated_at_utc')}")
    lines.append("")
    lines.append("## Evaluation Coverage")
    lines.append(f"- Total Evaluated Predictions: {eval_summary.get('total_evaluated_predictions')}")
    lines.append(f"- Correct: {eval_summary.get('correct_count')}")
    lines.append(f"- Incorrect: {eval_summary.get('incorrect_count')}")
    lines.append(f"- Winner Accuracy: {eval_summary.get('winner_accuracy')}")
    lines.append(f"- Unevaluable/Pending: {unevaluable.get('total_unevaluable_or_pending')}")
    lines.append("")
    lines.append("## Confidence Quality")
    lines.append(f"- Confidence Coverage: {confidence.get('confidence_coverage')}")
    lines.append(f"- Rows with Confidence: {confidence.get('rows_with_confidence')}")
    lines.append(f"- Rows without Confidence: {confidence.get('rows_without_confidence')}")
    lines.append(f"- Overall Avg Confidence: {confidence.get('overall_avg_confidence')}")
    lines.append(f"- Overall Empirical Accuracy: {confidence.get('overall_empirical_accuracy')}")
    lines.append(f"- Overall Calibration Gap (conf - acc): {confidence.get('overall_calibration_gap')}")
    lines.append(
        "- Overconfidence Indicator: "
        f"{(confidence.get('overconfidence_indicator') or {}).get('incorrect_count')}"
        "/"
        f"{(confidence.get('overconfidence_indicator') or {}).get('sample_count')}"
        " high-confidence predictions were incorrect"
    )
    lines.append(
        "- Underconfidence Indicator: "
        f"{(confidence.get('underconfidence_indicator') or {}).get('correct_count')}"
        "/"
        f"{(confidence.get('underconfidence_indicator') or {}).get('sample_count')}"
        " low-confidence predictions were correct"
    )
    lines.append("")
    lines.append("### Confidence Buckets")
    lines.append("| Bucket | Count | Correct | Incorrect | Avg Confidence | Empirical Accuracy | Gap |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")

    bucket_map = confidence.get("confidence_buckets") if isinstance(confidence.get("confidence_buckets"), dict) else {}
    for _, _, label in CONFIDENCE_BUCKETS:
        stats = bucket_map.get(label) if isinstance(bucket_map.get(label), dict) else {}
        lines.append(
            "| {label} | {count} | {correct} | {incorrect} | {avg_conf} | {emp_acc} | {gap} |".format(
                label=label,
                count=stats.get("count"),
                correct=stats.get("correct"),
                incorrect=stats.get("incorrect"),
                avg_conf=stats.get("avg_confidence"),
                emp_acc=stats.get("empirical_accuracy"),
                gap=stats.get("calibration_gap"),
            )
        )

    lines.append("")
    lines.append("## Unevaluable / Pending")
    lines.append(f"- Reconciliation Unevaluable Count: {unevaluable.get('reconciliation_unevaluable_count')}")
    lines.append(f"- Reconciliation Unevaluable Reasons: {unevaluable.get('reconciliation_unevaluable_reasons')}")
    lines.append(f"- Prediction Queue Pending Count: {unevaluable.get('prediction_queue_pending_count')}")
    lines.append(f"- Prediction Queue Pending Reasons: {unevaluable.get('prediction_queue_pending_reasons')}")
    lines.append("")
    lines.append("## Recurring Miss Patterns")
    lines.append(f"- Total Incorrect: {misses.get('total_incorrect')}")

    top_patterns = misses.get("top_recurring_patterns") if isinstance(misses.get("top_recurring_patterns"), list) else []
    if top_patterns:
        for row in top_patterns:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- [{row.get('pattern_type')}] {row.get('pattern')} (count={row.get('count')})"
            )
    else:
        lines.append("- No recurring miss patterns detected from current evaluated set.")

    lines.append("")
    lines.append("## Recommended Calibration Follow-Up")
    for rec in recommendations:
        if not isinstance(rec, dict):
            continue
        lines.append(f"- [P{rec.get('priority')}] {rec.get('action')} ({rec.get('reason')})")

    lines.append("")
    lines.append("## Sources")
    lines.append(f"- Reconciliation CSV: {sources.get('reconciliation_csv')}")
    lines.append(f"- Prediction Queue JSON: {sources.get('prediction_queue_json')}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)

    if not repo_root.exists():
        print(f"ERROR: repo root not found: {repo_root}", file=sys.stderr)
        return 1

    reconciliation_csv_path = Path(args.reconciliation_csv)
    prediction_queue_json_path = Path(args.prediction_queue_json)
    output_dir = Path(args.output_dir)

    payload = build_calibration_report_payload(
        repo_root,
        reconciliation_csv_path,
        prediction_queue_json_path,
        output_dir,
    )

    out_dir = repo_root / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    out_json = out_dir / OUTPUT_JSON
    out_md = out_dir / OUTPUT_MD

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    out_md.write_text(render_markdown(payload), encoding="utf-8")

    print(f"[WRITE] {out_json}")
    print(f"[WRITE] {out_md}")
    print(
        "[STATUS] evaluated={evaluated} incorrect={incorrect} unevaluable_or_pending={unevaluable}".format(
            evaluated=((payload.get("evaluation_summary") or {}).get("total_evaluated_predictions")),
            incorrect=((payload.get("evaluation_summary") or {}).get("incorrect_count")),
            unevaluable=((payload.get("unevaluable_summary") or {}).get("total_unevaluable_or_pending")),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

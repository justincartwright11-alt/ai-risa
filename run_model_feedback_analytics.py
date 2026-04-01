
from __future__ import annotations

# AI-RISA model feedback analytics runner
# Diagnostic-only analytics export.
# No recommendations, no model mutation, no ledger mutation.

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

REVIEW_LOG_PATH = REPORTS_DIR / "model_feedback_review_log.csv"
PRIORITY_BAND_SUMMARY_PATH = REPORTS_DIR / "model_feedback_priority_band_summary.csv"
ISSUE_TYPE_TRENDS_PATH = REPORTS_DIR / "model_feedback_issue_type_trends.csv"
DRIFT_ALERTS_PATH = REPORTS_DIR / "model_feedback_drift_alerts.csv"
WEEKLY_SUMMARY_PATH = REPORTS_DIR / "model_feedback_weekly_summary.json"

STABLE_PRIORITY_BAND_COLUMNS = [
    "band_value",
    "band_label",
    "review_count",
    "accept_count",
    "accept_rate",
    "confirm_count",
    "confirm_rate",
    "action_taken_count",
    "action_taken_rate",
    "false_positive_count",
    "false_positive_rate",
    "avg_severity_component",
    "avg_recurrence_component",
    "avg_affected_count_component",
    "avg_metric_gap_component",
    "avg_composite_score",
]

STABLE_ISSUE_TYPE_TREND_COLUMNS = [
    "period_start",
    "issue_type",
    "review_count",
    "accept_count",
    "accept_rate",
    "confirm_count",
    "confirm_rate",
    "action_taken_count",
    "action_taken_rate",
    "avg_composite_score",
    "avg_severity_component",
    "avg_recurrence_component",
    "avg_affected_count_component",
    "avg_metric_gap_component",
]

STABLE_DRIFT_ALERT_COLUMNS = [
    "flag_type",
    "severity",
    "scope_type",
    "scope_value",
    "measured_value",
    "threshold_value",
    "sample_count",
    "details",
]

BAND_DEFINITIONS = [
    {"value": "high", "label": "High", "min": 0.80, "max": 1.01},
    {"value": "review_next", "label": "Review Next", "min": 0.60, "max": 0.80},
    {"value": "monitor", "label": "Monitor", "min": 0.40, "max": 0.60},
    {"value": "backlog", "label": "Backlog", "min": -1.0, "max": 0.40},
]

FLAG_THRESHOLDS = {
    "min_reviews_for_signal": 5,
    "high_band_false_positive_rate": 0.60,
    "backlog_confirm_rate": 0.60,
    "issue_type_confirm_rate_drop": 0.50,
    "version_confirm_rate_drop": 0.50,
    "family_repeat_failure_count": 3,
}

CANONICAL_COLUMN_MAP = {
    "reviewed_at": ["reviewed_at", "review_timestamp", "timestamp", "review_time"],
    "composite_score": ["composite_score", "composite_priority_score", "rank_score", "score", "priority_score"],
    "review_decision": ["review_decision", "review_label", "decision", "status"],
    "issue_confirmed": ["issue_confirmed", "actual_issue_confirmed", "confirmed", "is_confirmed"],
    "action_taken": ["action_taken", "suggested_action_taken", "did_act", "acted"],
    "impact_level": ["impact_level", "estimated_impact", "impact"],
    "issue_type": ["issue_type", "issue", "category", "feedback_type"],
    "model_version": ["model_version", "version", "engine_version", "prediction_version"],
    "prediction_family_id": ["prediction_family_id", "family_id", "family", "matchup_id"],
    "severity_component": ["severity_component", "severity", "winner_metric"],
    "recurrence_component": ["recurrence_component", "recurrence"],
    "affected_count_component": ["affected_count_component", "affected_count", "count"],
    "metric_gap_component": ["metric_gap_component", "metric_gap", "gap"],
}


@dataclass
class BuildContext:
    review_log: pd.DataFrame
    raw_review_rows: int
    normalized_review_rows: int
    columns_found: List[str]
    dropped_row_reason_counts: Dict[str, int]
    review_log_path: str
    parsed_date_rows: int
    banded_rows: int


def empty_dataframe(columns: List[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")
        for c in out.columns
    ]
    return out


def first_present_column(df: pd.DataFrame, candidates: List[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def coerce_bool(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    true_values = {"1", "true", "yes", "y", "accepted", "accept", "confirm", "confirmed", "done"}
    false_values = {"0", "false", "no", "n", "rejected", "reject", "defer", "", "nan"}
    result = pd.Series(pd.NA, index=series.index, dtype="boolean")
    result[lowered.isin(true_values)] = True
    result[lowered.isin(false_values)] = False
    return result


def coerce_review_decision(series: pd.Series) -> pd.Series:
    lowered = series.astype(str).str.strip().str.lower()
    mapped = lowered.replace(
        {
            "accepted": "accept",
            "accept": "accept",
            "rejected": "reject",
            "reject": "reject",
            "deferred": "defer",
            "defer": "defer",
        }
    )
    return mapped


def assign_band(score: float) -> Tuple[str, str]:
    if pd.isna(score):
        return "backlog", "Backlog"
    for band in BAND_DEFINITIONS:
        if band["min"] <= float(score) < band["max"]:
            return band["value"], band["label"]
    return "backlog", "Backlog"


def load_inputs() -> BuildContext:
    dropped: Dict[str, int] = {}
    if not REVIEW_LOG_PATH.exists():
        return BuildContext(
            review_log=empty_dataframe(list(CANONICAL_COLUMN_MAP.keys()) + ["band_value", "band_label"]),
            raw_review_rows=0,
            normalized_review_rows=0,
            columns_found=[],
            dropped_row_reason_counts={"missing_review_log": 1},
            review_log_path=str(REVIEW_LOG_PATH),
            parsed_date_rows=0,
            banded_rows=0,
        )

    raw_df = pd.read_csv(REVIEW_LOG_PATH)
    # Drop repeated header rows (where any column matches its own name)
    header_row = list(raw_df.columns)
    mask_header = (raw_df == header_row).all(axis=1)
    raw_df = raw_df[~mask_header].reset_index(drop=True)
    raw_count = len(raw_df)
    columns_found = list(raw_df.columns)
    df = normalize_column_names(raw_df)

    normalized = pd.DataFrame(index=df.index)
    for canonical_name, aliases in CANONICAL_COLUMN_MAP.items():
        source = first_present_column(df, aliases)
        normalized[canonical_name] = df[source] if source is not None else pd.NA

    normalized["reviewed_at"] = pd.to_datetime(normalized["reviewed_at"], errors="coerce")
    dropped["invalid_reviewed_at"] = int(normalized["reviewed_at"].isna().sum())

    normalized["composite_score"] = pd.to_numeric(normalized["composite_score"], errors="coerce")
    dropped["invalid_composite_score"] = int(normalized["composite_score"].isna().sum())

    normalized["review_decision"] = coerce_review_decision(normalized["review_decision"])
    invalid_decision_mask = ~normalized["review_decision"].isin(["accept", "reject", "defer"])
    dropped["invalid_review_decision"] = int(invalid_decision_mask.fillna(True).sum())

    normalized["issue_confirmed"] = coerce_bool(normalized["issue_confirmed"])
    normalized["action_taken"] = coerce_bool(normalized["action_taken"])

    for col in ["severity_component", "recurrence_component", "affected_count_component", "metric_gap_component"]:
        normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    normalized["impact_level"] = normalized["impact_level"].astype(str).str.strip().str.lower().replace({"nan": ""})
    normalized["issue_type"] = normalized["issue_type"].fillna("unspecified").astype(str).str.strip().replace({"": "unspecified"})
    normalized["model_version"] = normalized["model_version"].fillna("unknown_version").astype(str).str.strip().replace({"": "unknown_version"})
    normalized["prediction_family_id"] = normalized["prediction_family_id"].fillna("unknown_family").astype(str).str.strip().replace({"": "unknown_family"})

    keep_mask = (
        normalized["reviewed_at"].notna()
        & normalized["composite_score"].notna()
        & normalized["review_decision"].isin(["accept", "reject", "defer"])
    )
    cleaned = normalized.loc[keep_mask].copy()

    if cleaned.empty:
        cleaned["band_value"] = pd.Series(dtype="object")
        cleaned["band_label"] = pd.Series(dtype="object")
        parsed_date_rows = 0
        banded_rows = 0
    else:
        bands = cleaned["composite_score"].apply(assign_band)
        cleaned["band_value"] = bands.str[0]
        cleaned["band_label"] = bands.str[1]
        parsed_date_rows = int(cleaned["reviewed_at"].notna().sum())
        banded_rows = int(cleaned["band_value"].notna().sum())

    normalized_count = len(cleaned)

    return BuildContext(
        review_log=cleaned,
        raw_review_rows=raw_count,
        normalized_review_rows=normalized_count,
        columns_found=columns_found,
        dropped_row_reason_counts=dropped,
        review_log_path=str(REVIEW_LOG_PATH),
        parsed_date_rows=parsed_date_rows,
        banded_rows=banded_rows,
    )


def build_priority_band_summary(ctx: BuildContext) -> pd.DataFrame:
    df = ctx.review_log
    rows: List[Dict[str, Any]] = []
    for band in BAND_DEFINITIONS:
        band_df = df[df["band_value"] == band["value"]].copy()
        review_count = int(len(band_df))
        accept_count = int((band_df["review_decision"] == "accept").sum())
        confirm_count = int((band_df["issue_confirmed"] == True).sum())
        action_count = int((band_df["action_taken"] == True).sum())
        false_positive_count = int(((band_df["review_decision"] != "accept") & (band_df["issue_confirmed"] != True)).sum())

        row = {
            "band_value": band["value"],
            "band_label": band["label"],
            "review_count": review_count,
            "accept_count": accept_count,
            "accept_rate": round(accept_count / review_count, 4) if review_count else 0.0,
            "confirm_count": confirm_count,
            "confirm_rate": round(confirm_count / review_count, 4) if review_count else 0.0,
            "action_taken_count": action_count,
            "action_taken_rate": round(action_count / review_count, 4) if review_count else 0.0,
            "false_positive_count": false_positive_count,
            "false_positive_rate": round(false_positive_count / review_count, 4) if review_count else 0.0,
            "avg_severity_component": round(float(band_df["severity_component"].mean()), 4) if review_count else 0.0,
            "avg_recurrence_component": round(float(band_df["recurrence_component"].mean()), 4) if review_count else 0.0,
            "avg_affected_count_component": round(float(band_df["affected_count_component"].mean()), 4) if review_count else 0.0,
            "avg_metric_gap_component": round(float(band_df["metric_gap_component"].mean()), 4) if review_count else 0.0,
            "avg_composite_score": round(float(band_df["composite_score"].mean()), 4) if review_count else 0.0,
        }
        rows.append(row)

    out = pd.DataFrame(rows)
    return out.reindex(columns=STABLE_PRIORITY_BAND_COLUMNS)


def build_issue_type_trends(ctx: BuildContext) -> pd.DataFrame:
    df = ctx.review_log
    if df.empty:
        return empty_dataframe(STABLE_ISSUE_TYPE_TREND_COLUMNS)

    working = df.copy()
    working["period_start"] = working["reviewed_at"].dt.to_period("W-MON").apply(lambda p: p.start_time.date().isoformat())

    grouped_rows: List[Dict[str, Any]] = []
    for (period_start, issue_type), g in working.groupby(["period_start", "issue_type"], dropna=False):
        review_count = int(len(g))
        accept_count = int((g["review_decision"] == "accept").sum())
        confirm_count = int((g["issue_confirmed"] == True).sum())
        action_count = int((g["action_taken"] == True).sum())
        grouped_rows.append(
            {
                "period_start": str(period_start),
                "issue_type": str(issue_type),
                "review_count": review_count,
                "accept_count": accept_count,
                "accept_rate": round(accept_count / review_count, 4) if review_count else 0.0,
                "confirm_count": confirm_count,
                "confirm_rate": round(confirm_count / review_count, 4) if review_count else 0.0,
                "action_taken_count": action_count,
                "action_taken_rate": round(action_count / review_count, 4) if review_count else 0.0,
                "avg_composite_score": round(float(g["composite_score"].mean()), 4) if review_count else 0.0,
                "avg_severity_component": round(float(g["severity_component"].mean()), 4) if review_count else 0.0,
                "avg_recurrence_component": round(float(g["recurrence_component"].mean()), 4) if review_count else 0.0,
                "avg_affected_count_component": round(float(g["affected_count_component"].mean()), 4) if review_count else 0.0,
                "avg_metric_gap_component": round(float(g["metric_gap_component"].mean()), 4) if review_count else 0.0,
            }
        )

    out = pd.DataFrame(grouped_rows)
    out = out.sort_values(["period_start", "issue_type"]).reset_index(drop=True)
    return out.reindex(columns=STABLE_ISSUE_TYPE_TREND_COLUMNS)


def build_drift_alerts(ctx: BuildContext, priority_band_df: pd.DataFrame, issue_type_trends_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []
    debug: Dict[str, Any] = {}

    min_reviews = FLAG_THRESHOLDS["min_reviews_for_signal"]

    high_row = priority_band_df[priority_band_df["band_value"] == "high"]
    if not high_row.empty:
        row = high_row.iloc[0]
        measured = float(row["false_positive_rate"])
        sample_count = int(row["review_count"])
        eligible = sample_count >= min_reviews
        would_fire_without_guard = measured >= FLAG_THRESHOLDS["high_band_false_positive_rate"]
        fired = eligible and would_fire_without_guard
        debug["threshold_drift_detected"] = {
            "band": "high",
            "measured_false_positive_rate": measured,
            "threshold": FLAG_THRESHOLDS["high_band_false_positive_rate"],
            "sample_count": sample_count,
            "min_required": min_reviews,
            "eligible": eligible,
            "would_fire_without_guard": would_fire_without_guard,
            "fired": fired,
        }
        if fired:
            alerts.append(
                {
                    "flag_type": "threshold_drift_detected",
                    "severity": "high",
                    "scope_type": "priority_band",
                    "scope_value": "high",
                    "measured_value": round(measured, 4),
                    "threshold_value": FLAG_THRESHOLDS["high_band_false_positive_rate"],
                    "sample_count": sample_count,
                    "details": "High band false-positive rate exceeded threshold.",
                }
            )

    backlog_row = priority_band_df[priority_band_df["band_value"] == "backlog"]
    if not backlog_row.empty:
        row = backlog_row.iloc[0]
        measured = float(row["confirm_rate"])
        sample_count = int(row["review_count"])
        eligible = sample_count >= min_reviews
        would_fire_without_guard = measured >= FLAG_THRESHOLDS["backlog_confirm_rate"]
        fired = eligible and would_fire_without_guard
        debug["recurrence_underweight_risk"] = {
            "band": "backlog",
            "measured_confirm_rate": measured,
            "threshold": FLAG_THRESHOLDS["backlog_confirm_rate"],
            "sample_count": sample_count,
            "min_required": min_reviews,
            "eligible": eligible,
            "would_fire_without_guard": would_fire_without_guard,
            "fired": fired,
        }
        if fired:
            alerts.append(
                {
                    "flag_type": "recurrence_underweight_risk",
                    "severity": "medium",
                    "scope_type": "priority_band",
                    "scope_value": "backlog",
                    "measured_value": round(measured, 4),
                    "threshold_value": FLAG_THRESHOLDS["backlog_confirm_rate"],
                    "sample_count": sample_count,
                    "details": "Backlog band confirm rate exceeded threshold.",
                }
            )

    if not issue_type_trends_df.empty:
        trend_debug_rows: List[Dict[str, Any]] = []
        for issue_type, g in issue_type_trends_df.groupby("issue_type", dropna=False):
            g = g.sort_values("period_start")
            if len(g) < 2:
                continue
            prev_row = g.iloc[-2]
            curr_row = g.iloc[-1]
            prev_count = int(prev_row["review_count"])
            curr_count = int(curr_row["review_count"])
            prev_confirm = float(prev_row["confirm_rate"])
            curr_confirm = float(curr_row["confirm_rate"])
            drop_value = prev_confirm - curr_confirm
            eligible = prev_count >= 2 and curr_count >= 2
            would_fire_without_guard = drop_value >= FLAG_THRESHOLDS["issue_type_confirm_rate_drop"]
            fired = eligible and would_fire_without_guard
            trend_debug_rows.append(
                {
                    "issue_type": issue_type,
                    "prev_period": prev_row["period_start"],
                    "curr_period": curr_row["period_start"],
                    "prev_confirm_rate": prev_confirm,
                    "curr_confirm_rate": curr_confirm,
                    "drop_value": round(drop_value, 4),
                    "prev_count": prev_count,
                    "curr_count": curr_count,
                    "eligible": eligible,
                    "threshold": FLAG_THRESHOLDS["issue_type_confirm_rate_drop"],
                    "would_fire_without_guard": would_fire_without_guard,
                    "fired": fired,
                }
            )
            if fired:
                alerts.append(
                    {
                        "flag_type": "issue_type_quality_drop",
                        "severity": "medium",
                        "scope_type": "issue_type",
                        "scope_value": str(issue_type),
                        "measured_value": round(drop_value, 4),
                        "threshold_value": FLAG_THRESHOLDS["issue_type_confirm_rate_drop"],
                        "sample_count": min(prev_count, curr_count),
                        "details": f"Confirm rate dropped from {prev_confirm:.4f} to {curr_confirm:.4f}.",
                    }
                )
        debug["issue_type_quality_drop"] = trend_debug_rows

    if not ctx.review_log.empty:
        family_working = ctx.review_log.copy()
        mask = (family_working["review_decision"] != "accept") & (family_working["issue_confirmed"] != True)
        family_working["is_repeat_fail"] = mask.fillna(False).astype(int)
        family_failures = (
            family_working.groupby("prediction_family_id", dropna=False)["is_repeat_fail"]
            .sum()
            .reset_index()
        )
        family_failures = family_failures.sort_values("is_repeat_fail", ascending=False)
        if not family_failures.empty:
            top_family = family_failures.iloc[0]
            sample_count = int(top_family["is_repeat_fail"])
            fired = sample_count >= FLAG_THRESHOLDS["family_repeat_failure_count"]
            debug["family_level_repeat_failure"] = {
                "top_family": str(top_family["prediction_family_id"]),
                "repeat_failure_count": sample_count,
                "threshold": FLAG_THRESHOLDS["family_repeat_failure_count"],
                "fired": fired,
            }
            if fired:
                alerts.append(
                    {
                        "flag_type": "family_level_repeat_failure",
                        "severity": "low",
                        "scope_type": "prediction_family_id",
                        "scope_value": str(top_family["prediction_family_id"]),
                        "measured_value": sample_count,
                        "threshold_value": FLAG_THRESHOLDS["family_repeat_failure_count"],
                        "sample_count": sample_count,
                        "details": "Family accumulated repeated rejected/unconfirmed reviews.",
                    }
                )

        version_group = (
            ctx.review_log.groupby("model_version", dropna=False)
            .agg(
                review_count=("model_version", "size"),
                confirm_rate=(
                    "issue_confirmed",
                    lambda s: float((s == True).mean()) if len(s) and s.notna().any() else 0.0
                ),
            )
            .reset_index()
        )
        if not version_group.empty:
            # Fill NA confirm_rate with 0.0 to avoid TypeError
            version_group["confirm_rate"] = version_group["confirm_rate"].fillna(0.0)
            worst_version = version_group.sort_values("confirm_rate", ascending=True).iloc[0]
            measured = 1.0 - float(worst_version["confirm_rate"])
            sample_count = int(worst_version["review_count"])
            eligible = sample_count >= min_reviews
            would_fire_without_guard = measured >= FLAG_THRESHOLDS["version_confirm_rate_drop"]
            fired = eligible and would_fire_without_guard
            debug["version_level_confirm_rate_drop"] = {
                "model_version": str(worst_version["model_version"]),
                "confirm_rate_inverse": round(measured, 4),
                "threshold": FLAG_THRESHOLDS["version_confirm_rate_drop"],
                "sample_count": sample_count,
                "min_required": min_reviews,
                "eligible": eligible,
                "would_fire_without_guard": would_fire_without_guard,
                "fired": fired,
            }
            if fired:
                alerts.append(
                    {
                        "flag_type": "version_level_confirm_rate_drop",
                        "severity": "low",
                        "scope_type": "model_version",
                        "scope_value": str(worst_version["model_version"]),
                        "measured_value": round(measured, 4),
                        "threshold_value": FLAG_THRESHOLDS["version_confirm_rate_drop"],
                        "sample_count": sample_count,
                        "details": "Version-level confirm rate deterioration exceeded threshold.",
                    }
                )

    alerts_df = pd.DataFrame(alerts)
    if alerts_df.empty:
        alerts_df = empty_dataframe(STABLE_DRIFT_ALERT_COLUMNS)
    else:
        alerts_df = alerts_df.reindex(columns=STABLE_DRIFT_ALERT_COLUMNS)
    return alerts_df, debug


def build_weekly_summary(
    ctx: BuildContext,
    priority_band_df: pd.DataFrame,
    issue_type_trends_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
    alert_debug: Dict[str, Any],
) -> Dict[str, Any]:
    df = ctx.review_log
    if df.empty:
        current_week_rows = 0
        current_week_reviews = df.copy()
    else:
        latest_date = df["reviewed_at"].max()
        week_start = latest_date - pd.Timedelta(days=int(latest_date.weekday()))
        current_week_reviews = df[df["reviewed_at"] >= week_start].copy()
        current_week_rows = int(len(current_week_reviews))

    summary = {
        "review_log_path": ctx.review_log_path,
        "raw_review_rows": ctx.raw_review_rows,
        "normalized_review_rows": ctx.normalized_review_rows,
        "columns_found": ctx.columns_found,
        "parsed_date_rows": ctx.parsed_date_rows,
        "banded_rows": ctx.banded_rows,
        "current_week_rows": current_week_rows,
        "dropped_row_reason_counts": ctx.dropped_row_reason_counts,
        "priority_band_summary_rows": int(len(priority_band_df)),
        "issue_type_trend_rows": int(len(issue_type_trends_df)),
        "alert_count": int(len(alerts_df)),
        "flags": alerts_df["flag_type"].tolist() if not alerts_df.empty else [],
        "weekly_accept_rate": round(float((current_week_reviews["review_decision"] == "accept").mean()), 4) if current_week_rows else 0.0,
        "weekly_confirm_rate": round(float((current_week_reviews["issue_confirmed"].fillna(False) == True).mean()), 4) if current_week_rows else 0.0,
        "weekly_action_taken_rate": round(float((current_week_reviews["action_taken"].fillna(False) == True).mean()), 4) if current_week_rows else 0.0,
        "alert_debug": alert_debug,
    }
    return summary


def write_outputs(
    priority_band_df: pd.DataFrame,
    issue_type_trends_df: pd.DataFrame,
    alerts_df: pd.DataFrame,
    weekly_summary: Dict[str, Any],
) -> None:
    priority_band_df.reindex(columns=STABLE_PRIORITY_BAND_COLUMNS).to_csv(PRIORITY_BAND_SUMMARY_PATH, index=False)
    issue_type_trends_df.reindex(columns=STABLE_ISSUE_TYPE_TREND_COLUMNS).to_csv(ISSUE_TYPE_TRENDS_PATH, index=False)
    alerts_df.reindex(columns=STABLE_DRIFT_ALERT_COLUMNS).to_csv(DRIFT_ALERTS_PATH, index=False)
    with open(WEEKLY_SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(weekly_summary, f, indent=2, default=str)


def main() -> None:
    ctx = load_inputs()
    priority_band_df = build_priority_band_summary(ctx)
    issue_type_trends_df = build_issue_type_trends(ctx)
    alerts_df, alert_debug = build_drift_alerts(ctx, priority_band_df, issue_type_trends_df)
    weekly_summary = build_weekly_summary(ctx, priority_band_df, issue_type_trends_df, alerts_df, alert_debug)
    write_outputs(priority_band_df, issue_type_trends_df, alerts_df, weekly_summary)

    print(
        json.dumps(
            {
                "status": "ok",
                "review_log_path": ctx.review_log_path,
                "raw_review_rows": ctx.raw_review_rows,
                "normalized_review_rows": ctx.normalized_review_rows,
                "alert_count": len(alerts_df),
                "outputs": {
                    "priority_band_summary": str(PRIORITY_BAND_SUMMARY_PATH),
                    "issue_type_trends": str(ISSUE_TYPE_TRENDS_PATH),
                    "drift_alerts": str(DRIFT_ALERTS_PATH),
                    "weekly_summary": str(WEEKLY_SUMMARY_PATH),
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

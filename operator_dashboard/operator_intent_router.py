"""
Operator Intent Router
======================
Maps plain-English operator commands to safe, structured action plans.

Safety levels:
  AUTO_READ_ONLY            – safe, executes immediately (read-only endpoints)
  APPROVAL_REQUIRED_WRITE   – shows plan first, requires explicit approval
  LOCKED_HIGH_RISK          – always refused; new checkpoint required
"""

import re

# ---------------------------------------------------------------------------
# Locked pattern list — anything matching here is refused immediately
# ---------------------------------------------------------------------------
_LOCKED_PATTERNS = [
    r"apply\s+backfill",
    r"stage\s+(prediction|stub)",
    r"delete\s+(prediction|stub)",
    r"mutate\s+(ledger|accuracy)",
    r"\bbatch\s*2\b",
    r"batch_2",
    r"accuracy\s+ledger\s+(mutation|write|edit|delete)",
    r"regenerat\w*\s+prediction",
    r"remove\s+untracked",
    r"force.?commit",
    r"git\s+push\s+--force",
    r"drop\s+table",
]

# ---------------------------------------------------------------------------
# Intent map: (intent_name, safety_level, [regex patterns])
# Checked in order; first match wins.
# ---------------------------------------------------------------------------
_INTENT_MAP = [
    (
        "system_health",
        "AUTO_READ_ONLY",
        [
            r"check\s+health",
            r"\bhealth\b",
            r"system\s+status",
            r"dashboard\s+status",
            r"is\s+.*\s+running",
            r"\bping\b",
            r"show\s+(dashboard\s+)?warnings?",
        ],
    ),
    (
        "accuracy_calibration",
        "AUTO_READ_ONLY",
        [
            r"accuracy\s+calibration",
            r"run\s+accuracy",
            r"accuracy.?ledger\s+calibration",
            r"ledger\s+calibration",
            r"accuracy\s+review",
            r"calibration\s+review",
        ],
    ),
    (
        "backfill_status_check",
        "AUTO_READ_ONLY",
        [
            r"backfill\s+status",
            r"show\s+backfill",
            r"\bbackfill\b",
            r"ready.?for.?backfill",
        ],
    ),
    (
        "unresolved_result_review",
        "AUTO_READ_ONLY",
        [
            r"unresolved\s+fights?",
            r"show\s+unresolved",
            r"waiting.?for.?results?",
            r"result\s+queue",
            r"\bunresolved\b",
        ],
    ),
    (
        "event_queue_review",
        "AUTO_READ_ONLY",
        [
            r"event\s+queue",
            r"show\s+events?",
            r"upcoming\s+events?",
            r"event\s+review",
        ],
    ),
    (
        "commit_readiness_check",
        "AUTO_READ_ONLY",
        [
            r"commit\s+readiness",
            r"git\s+status",
            r"ready\s+to\s+commit",
            r"what.*(changed|is\s+different)",
            r"show\s+last\s+action",
        ],
    ),
    (
        "build_premium_report",
        "APPROVAL_REQUIRED_WRITE",
        [
            r"build\s+.*report",
            r"generate\s+.*report",
            r"create\s+.*report",
            r"\bvs\.?\s+\w",
        ],
    ),
    (
        "report_scoring_calibration",
        "APPROVAL_REQUIRED_WRITE",
        [
            r"report.?scoring\s+calibration",
            r"score\s+a\s+(finished\s+)?report",
            r"scoring\s+review",
        ],
    ),
    (
        "report_qa_review",
        "APPROVAL_REQUIRED_WRITE",
        [
            r"qa\s+review",
            r"review\s+.*report",
            r"qa.*report",
        ],
    ),
    (
        "fighter_profile_check",
        "AUTO_READ_ONLY",
        [
            r"fighter\s+profile",
            r"check\s+fighter",
            r"find\s+fighter",
            r"fighter\s+info",
        ],
    ),
]

_EXAMPLES = [
    "check health",
    "run accuracy calibration",
    "show backfill status",
    "show unresolved fights",
    "build Jafel Filho vs Cody Durden report",
    "show dashboard warnings",
    "show last action",
]


def route_intent(command: str) -> dict:
    """
    Route a plain-English command to a structured intent plan.

    Returns a dict with:
        intent          – intent category name
        safety_level    – AUTO_READ_ONLY | APPROVAL_REQUIRED_WRITE | LOCKED_HIGH_RISK
        planned_action  – human-readable description of what will happen
        requires_approval – bool
        blocked         – bool (True only for LOCKED_HIGH_RISK)
        examples        – list[str] (only on unknown_intent or locked)
        matchup         – str (only for build_premium_report when parseable)
    """
    text = command.strip().lower()

    # 1. Refuse locked patterns immediately
    for pattern in _LOCKED_PATTERNS:
        if re.search(pattern, text):
            return {
                "intent": "locked_high_risk",
                "safety_level": "LOCKED_HIGH_RISK",
                "planned_action": (
                    "BLOCKED: This action is locked. A new approved checkpoint is "
                    "required to perform structural writes, backfill, or prediction "
                    "mutations."
                ),
                "requires_approval": False,
                "blocked": True,
                "examples": _EXAMPLES,
            }

    # 2. Match intents
    for intent_name, safety, patterns in _INTENT_MAP:
        for pattern in patterns:
            if re.search(pattern, text):
                result: dict = {
                    "intent": intent_name,
                    "safety_level": safety,
                    "requires_approval": safety == "APPROVAL_REQUIRED_WRITE",
                    "blocked": False,
                }
                _enrich(result, text)
                return result

    # 3. Unknown
    return {
        "intent": "unknown_intent",
        "safety_level": "AUTO_READ_ONLY",
        "planned_action": "Command not recognised. Try one of the examples below.",
        "requires_approval": False,
        "blocked": False,
        "examples": _EXAMPLES,
    }


# ---------------------------------------------------------------------------
# Enrichment — adds planned_action and optional fields per intent
# ---------------------------------------------------------------------------
def _enrich(result: dict, text: str) -> None:
    intent = result["intent"]

    if intent == "system_health":
        result["planned_action"] = (
            "Fetch /api/system/health and display system status summary."
        )
        result["endpoint"] = "/api/system/health"

    elif intent == "accuracy_calibration":
        result["planned_action"] = (
            "Fetch /api/accuracy/comparison-summary and "
            "/api/accuracy/confidence-calibration and display accuracy-ledger "
            "calibration summary."
        )
        result["endpoints"] = [
            "/api/accuracy/comparison-summary",
            "/api/accuracy/confidence-calibration",
        ]

    elif intent == "backfill_status_check":
        result["planned_action"] = (
            "Fetch /api/accuracy/structural-signal-backfill-planner and display "
            "READY_FOR_BACKFILL count and blocked state."
        )
        result["endpoint"] = "/api/accuracy/structural-signal-backfill-planner"

    elif intent == "unresolved_result_review":
        result["planned_action"] = (
            "Fetch /api/operator/rolling-success-rate and display fights waiting "
            "for real-life results."
        )
        result["endpoint"] = "/api/operator/rolling-success-rate"

    elif intent == "event_queue_review":
        result["planned_action"] = (
            "Fetch /api/queue and display events currently in the operator queue."
        )
        result["endpoint"] = "/api/queue"

    elif intent == "commit_readiness_check":
        result["planned_action"] = (
            "Fetch /api/system/health for current status. Use terminal git status "
            "for full commit readiness."
        )
        result["endpoint"] = "/api/system/health"

    elif intent == "build_premium_report":
        m = re.search(
            r"build\s+(.+?)\s+vs\.?\s+(.+?)(?:\s+report)?$", text
        ) or re.search(
            r"(.+?)\s+vs\.?\s+(.+?)(?:\s+report)?$", text
        )
        if m:
            fighter_a = m.group(1).strip().title()
            fighter_b = m.group(2).strip().title()
            matchup = f"{fighter_a} vs {fighter_b}"
            result["planned_action"] = (
                f"Build premium report for: {matchup}. "
                f"Calls POST /api/operator/analyze-build-report with "
                f"matchup='{matchup}'. Requires approval before execution."
            )
            result["matchup"] = matchup
        else:
            result["planned_action"] = (
                "Build premium report — please specify fighters: "
                "'build [Fighter A] vs [Fighter B] report'."
            )

    elif intent == "report_scoring_calibration":
        result["planned_action"] = (
            "Report-scoring calibration requires manually scored report outcomes. "
            "No scored reports are currently available. Review the Advanced / "
            "Report-Scoring Calibration panel."
        )

    elif intent == "report_qa_review":
        result["planned_action"] = (
            "Run QA review on a specific report. Specify the report to review."
        )

    elif intent == "fighter_profile_check":
        result["planned_action"] = (
            "Look up fighter profile in the fighter registry. "
            "Specify a fighter name to search."
        )

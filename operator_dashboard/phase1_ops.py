import json
import os
from json import JSONDecodeError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("AI_RISA_PHASE1_DATA_DIR", str(ROOT / "ops" / "intake_tracking" / "phase1")))
EVENTS_DIR = Path(os.getenv("AI_RISA_EVENTS_DIR", str(ROOT / "events")))
MATCHUPS_DIR = Path(os.getenv("AI_RISA_MATCHUPS_DIR", str(ROOT / "matchups")))
REPORTS_DIR = Path(os.getenv("AI_RISA_REPORTS_DIR", str(ROOT / "reports")))
FIGHTERS_DIR = Path(os.getenv("AI_RISA_FIGHTERS_DIR", str(ROOT / "fighters")))
ENRICHMENT_PATH = Path(os.getenv("AI_RISA_ENRICHMENT_PATH", str(ROOT / "fighters" / "manual_profile_enrichment.json")))

EVENT_REVIEW_QUEUE_PATH = DATA_DIR / "event_review_queue.json"
FROZEN_CARDS_PATH = DATA_DIR / "frozen_cards.json"
FIGHT_RUN_QUEUE_PATH = DATA_DIR / "fight_run_queue.json"
RESULTS_LEDGER_PATH = DATA_DIR / "results_ledger.json"
ACTION_LOG_PATH = DATA_DIR / "phase1_action_log.jsonl"

STATE_CHAIN = ["detected", "queued", "reviewed", "approved", "frozen", "ready", "reported", "completed", "scored"]
SPORT_FILTERS = {"mma", "boxing", "kickboxing", "muay thai", "all"}
REPORT_STATUS_NOT_STARTED = "not_started"
REPORT_STATUS_QUEUED = "queued_for_generation"
REPORT_STATUS_COMPLETE = "reported_complete"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _safe_read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload
    except Exception:
        return default


def _safe_write_json(path: Path, payload: Any) -> None:
    _ensure_data_dir()
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _append_action_log(action: str, status: str, details: Dict[str, Any]) -> None:
    _ensure_data_dir()
    row = {
        "timestamp": _utc_now(),
        "action": action,
        "status": status,
        "details": details,
    }
    with ACTION_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _slugify(value: str) -> str:
    cleaned = (value or "").strip().lower()
    out = []
    for char in cleaned:
        out.append(char if char.isalnum() else "_")
    slug = "".join(out)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug.strip("_")


def _guess_sport(name: str, promotion: str) -> str:
    blob = f"{name} {promotion}".lower()
    if "ufc" in blob or "pfl" in blob or "lfa" in blob or "mma" in blob:
        return "mma"
    if "glory" in blob or "kickboxing" in blob or "k-1" in blob:
        return "kickboxing"
    if "muay" in blob or "one friday fights" in blob or "one fight night" in blob:
        return "muay thai"
    return "boxing"


def _load_event_queue() -> List[Dict[str, Any]]:
    payload = _safe_read_json(EVENT_REVIEW_QUEUE_PATH, [])
    return payload if isinstance(payload, list) else []


def _save_event_queue(rows: List[Dict[str, Any]]) -> None:
    _safe_write_json(EVENT_REVIEW_QUEUE_PATH, rows)


def _load_frozen_cards() -> Dict[str, Dict[str, Any]]:
    payload = _safe_read_json(FROZEN_CARDS_PATH, {})
    return payload if isinstance(payload, dict) else {}


def _save_frozen_cards(cards: Dict[str, Dict[str, Any]]) -> None:
    _safe_write_json(FROZEN_CARDS_PATH, cards)


def _load_fight_run_queue() -> List[Dict[str, Any]]:
    payload = _safe_read_json(FIGHT_RUN_QUEUE_PATH, [])
    return payload if isinstance(payload, list) else []


def _save_fight_run_queue(rows: List[Dict[str, Any]]) -> None:
    _safe_write_json(FIGHT_RUN_QUEUE_PATH, rows)


def _load_results_ledger() -> List[Dict[str, Any]]:
    payload = _safe_read_json(RESULTS_LEDGER_PATH, [])
    return payload if isinstance(payload, list) else []


def _save_results_ledger(rows: List[Dict[str, Any]]) -> None:
    _safe_write_json(RESULTS_LEDGER_PATH, rows)


def _state_index(value: str) -> int:
    return STATE_CHAIN.index(value) if value in STATE_CHAIN else -1


def _transition_allowed(current: str, target: str) -> bool:
    i = _state_index(current)
    j = _state_index(target)
    return i >= 0 and j == i + 1


def _advance_state(record: Dict[str, Any], target_state: str) -> Tuple[bool, str]:
    current = record.get("state", "detected")
    if current == target_state:
        return True, "already_in_state"
    while current != target_state:
        idx = _state_index(current)
        if idx < 0 or idx + 1 >= len(STATE_CHAIN):
            return False, f"invalid_state_transition:{current}->{target_state}"
        next_state = STATE_CHAIN[idx + 1]
        if not _transition_allowed(current, next_state):
            return False, f"invalid_state_transition:{current}->{next_state}"
        current = next_state
        record["state"] = current
    return True, "ok"


def _read_event_card(event_file: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with event_file.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload, None
    except JSONDecodeError as exc:
        return None, f"invalid_json(line={exc.lineno}, col={exc.colno}): {exc.msg}"
    except Exception as exc:
        return None, str(exc)


def _extract_event_fields(event_payload: Dict[str, Any], event_file: Path) -> Dict[str, Any]:
    event_name = event_payload.get("event") or event_payload.get("event_name") or event_file.stem
    promotion = event_payload.get("promotion") or ""
    date = event_payload.get("date") or ""
    location = event_payload.get("location") or ""
    sport = _guess_sport(event_name, promotion)
    event_id = _slugify(event_name) or _slugify(event_file.stem)
    bouts_raw = event_payload.get("bouts") if isinstance(event_payload.get("bouts"), list) else []
    bouts: List[Dict[str, Any]] = []
    for bout in bouts_raw:
        if not isinstance(bout, dict):
            continue
        fighter_a = str(bout.get("fighter_a") or "").strip()
        fighter_b = str(bout.get("fighter_b") or "").strip()
        fighters = bout.get("fighters") if isinstance(bout.get("fighters"), list) else []
        if not fighter_a and len(fighters) > 0:
            fighter_a = str(fighters[0] or "").strip()
        if not fighter_b and len(fighters) > 1:
            fighter_b = str(fighters[1] or "").strip()
        normalized_bout = dict(bout)
        normalized_bout["fighter_a"] = fighter_a
        normalized_bout["fighter_b"] = fighter_b
        bouts.append(normalized_bout)
    has_main_event = any(bool(b.get("main_event")) for b in bouts if isinstance(b, dict))
    return {
        "event_id": event_id,
        "event_name": event_name,
        "source": str(event_file.relative_to(ROOT)).replace("\\", "/") if event_file.is_relative_to(ROOT) else str(event_file),
        "date": date,
        "sport": sport,
        "promotion": promotion,
        "location": location,
        "bouts": bouts,
        "bouts_count": len(bouts),
        "has_main_event": has_main_event,
        "state": "queued",
        "trigger_state": "new_trigger",
        "completeness": "complete" if bouts and has_main_event else "incomplete",
        "blockers": [],
        "approved": False,
        "frozen": False,
        "updated_at": _utc_now(),
    }


def _load_enrichment() -> Dict[str, Any]:
    payload = _safe_read_json(ENRICHMENT_PATH, {})
    return payload if isinstance(payload, dict) else {}


def _profile_exists(name: str) -> bool:
    slug = _slugify(name)
    if not slug:
        return False
    candidates = [
        FIGHTERS_DIR / f"{slug}.json",
        FIGHTERS_DIR / f"fighter_{slug}.json",
    ]
    return any(path.exists() for path in candidates)


def _enrichment_exists(name: str, enrichment: Dict[str, Any]) -> bool:
    slug = _slugify(name)
    if not slug:
        return False
    if slug in enrichment:
        return True
    return f"fighter_{slug}" in enrichment


def _compute_card_blockers(event_payload: Dict[str, Any]) -> Tuple[str, List[Dict[str, str]]]:
    bouts = event_payload.get("bouts") if isinstance(event_payload.get("bouts"), list) else []
    blockers: List[Dict[str, str]] = []
    if not bouts:
        blockers.append({"code": "incomplete_card", "message": "Event has no bout list."})

    enrichment = _load_enrichment()
    for bout in bouts:
        fighters = bout.get("fighters") if isinstance(bout, dict) else []
        if not isinstance(fighters, list) or len(fighters) < 2:
            blockers.append({"code": "incomplete_card", "message": "Bout is missing both fighter names."})
            continue
        for fighter in fighters[:2]:
            if not fighter or str(fighter).strip().upper() == "TBA":
                blockers.append({"code": "incomplete_card", "message": f"Bout has placeholder fighter: {fighter}"})
                continue
            if not _profile_exists(str(fighter)):
                blockers.append({"code": "missing_profiles", "message": f"Missing profile for fighter: {fighter}"})
            if not _enrichment_exists(str(fighter), enrichment):
                blockers.append({"code": "missing_enrichment", "message": f"Missing enrichment for fighter: {fighter}"})

    # Deduplicate blocker messages while preserving order
    seen = set()
    deduped = []
    for b in blockers:
        key = (b.get("code"), b.get("message"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(b)

    completeness = "complete" if not deduped else "incomplete"
    return completeness, deduped


def _upsert_fight_run_row(rows: List[Dict[str, Any]], row: Dict[str, Any]) -> None:
    key = row.get("matchup_slug")
    for idx, existing in enumerate(rows):
        if existing.get("matchup_slug") == key:
            rows[idx] = row
            return
    rows.append(row)


def scan_upcoming_events(sport: str = "all") -> Dict[str, Any]:
    sport_norm = (sport or "all").strip().lower()
    if sport_norm not in SPORT_FILTERS:
        sport_norm = "all"

    queue = _load_event_queue()
    queue_by_id = {row.get("event_id"): row for row in queue}

    new_count = 0
    parse_errors: List[Dict[str, str]] = []
    for event_file in sorted(EVENTS_DIR.glob("*.json")):
        payload, parse_error = _read_event_card(event_file)
        if parse_error:
            parse_errors.append({"file": event_file.name, "error": parse_error})
            continue

        row = _extract_event_fields(payload or {}, event_file)
        existing = queue_by_id.get(row["event_id"])
        if existing:
            existing.update({
                "event_name": row["event_name"],
                "source": row["source"],
                "date": row["date"],
                "sport": row["sport"],
                "promotion": row["promotion"],
                "bouts_count": row["bouts_count"],
                "has_main_event": row["has_main_event"],
                "trigger_state": "existing",
                "updated_at": _utc_now(),
            })
        else:
            queue.append(row)
            queue_by_id[row["event_id"]] = row
            new_count += 1

    _save_event_queue(queue)

    filtered_rows = [
        row for row in queue
        if sport_norm == "all" or row.get("sport") == sport_norm
    ]
    _append_action_log("scan_upcoming_events", "succeeded", {
        "new_triggers": new_count,
        "total_rows": len(queue),
        "sport_filter": sport_norm,
        "parse_errors": len(parse_errors),
    })
    return {
        "ok": True,
        "new_triggers": new_count,
        "rows": filtered_rows,
        "parse_errors": parse_errors,
        "timestamp": _utc_now(),
    }


def get_upcoming_events(sport: str = "all") -> Dict[str, Any]:
    sport_norm = (sport or "all").strip().lower()
    if sport_norm not in SPORT_FILTERS:
        sport_norm = "all"
    rows = _load_event_queue()
    filtered_rows = [
        row for row in rows
        if sport_norm == "all" or row.get("sport") == sport_norm
    ]
    return {
        "ok": True,
        "rows": filtered_rows,
        "timestamp": _utc_now(),
    }


def get_event_review_queue() -> Dict[str, Any]:
    rows = _load_event_queue()
    review_rows = [
        row for row in rows
        if row.get("state") in {"detected", "queued", "reviewed", "approved", "blocked", "frozen"}
    ]
    return {"ok": True, "rows": review_rows, "timestamp": _utc_now()}


def freeze_approved_card(event_id: str) -> Dict[str, Any]:
    queue = _load_event_queue()
    record = next((r for r in queue if r.get("event_id") == event_id), None)
    if not record:
        _append_action_log("freeze_approved_card", "failed", {"event_id": event_id, "error": "event_not_found"})
        return {"ok": False, "error": "event_not_found", "blockers": []}

    source = record.get("source") or ""
    event_file = ROOT / source if source else None
    if not event_file or not event_file.exists():
        _append_action_log("freeze_approved_card", "failed", {"event_id": event_id, "error": "missing_event_source"})
        return {"ok": False, "error": "missing_event_source", "blockers": []}

    payload, parse_error = _read_event_card(event_file)
    if parse_error or not payload:
        _append_action_log("freeze_approved_card", "failed", {"event_id": event_id, "error": "invalid_event_source"})
        return {"ok": False, "error": "invalid_event_source", "blockers": [{"code": "incomplete_card", "message": parse_error or "invalid source"}]}

    completeness, blockers = _compute_card_blockers(payload)
    record["completeness"] = completeness
    record["blockers"] = blockers
    record["updated_at"] = _utc_now()

    if blockers:
        record["state"] = "blocked"
        record["approved"] = False
        record["frozen"] = False
        _save_event_queue(queue)
        _append_action_log("freeze_approved_card", "failed", {"event_id": event_id, "error": "card_blocked", "blockers": blockers})
        return {"ok": False, "error": "card_blocked", "blockers": blockers}

    record["state"] = "queued"
    ok, reason = _advance_state(record, "reviewed")
    if ok:
        ok, reason = _advance_state(record, "approved")
    if ok:
        ok, reason = _advance_state(record, "frozen")

    if not ok:
        _save_event_queue(queue)
        _append_action_log("freeze_approved_card", "failed", {"event_id": event_id, "error": reason})
        return {"ok": False, "error": reason, "blockers": []}

    record["approved"] = True
    record["frozen"] = True

    frozen_cards = _load_frozen_cards()
    frozen_cards[event_id] = {
        "event_id": event_id,
        "event_name": record.get("event_name"),
        "date": record.get("date"),
        "sport": record.get("sport"),
        "promotion": record.get("promotion"),
        "source": record.get("source"),
        "payload": payload,
        "frozen_at": _utc_now(),
    }
    _save_frozen_cards(frozen_cards)
    _save_event_queue(queue)
    _append_action_log("freeze_approved_card", "succeeded", {"event_id": event_id})
    return {"ok": True, "event_id": event_id, "state": record.get("state")}


def _build_matchup_slug(fighter_a: str, fighter_b: str) -> str:
    return f"{_slugify(fighter_a)}_vs_{_slugify(fighter_b)}"


def create_matchups(event_id: str) -> Dict[str, Any]:
    queue = _load_event_queue()
    record = next((r for r in queue if r.get("event_id") == event_id), None)
    if not record:
        _append_action_log("create_matchups", "failed", {"event_id": event_id, "error": "event_not_found"})
        return {"ok": False, "error": "event_not_found"}
    if not (record.get("approved") and record.get("frozen")):
        blocker = {"code": "not_frozen", "message": "Event must be approved and frozen before matchup creation."}
        _append_action_log("create_matchups", "failed", {"event_id": event_id, "error": "not_frozen"})
        return {"ok": False, "error": "not_frozen", "blockers": [blocker]}

    frozen_cards = _load_frozen_cards()
    card = frozen_cards.get(event_id)
    if not card:
        _append_action_log("create_matchups", "failed", {"event_id": event_id, "error": "missing_frozen_card"})
        return {"ok": False, "error": "missing_frozen_card"}

    payload = card.get("payload") or {}
    bouts = payload.get("bouts") if isinstance(payload.get("bouts"), list) else []
    run_rows = _load_fight_run_queue()
    created = 0

    for index, bout in enumerate(bouts):
        fighters = bout.get("fighters") if isinstance(bout, dict) else []
        if not isinstance(fighters, list) or len(fighters) < 2:
            continue
        fighter_a = str(fighters[0]).strip()
        fighter_b = str(fighters[1]).strip()
        if not fighter_a or not fighter_b or fighter_a.upper() == "TBA" or fighter_b.upper() == "TBA":
            continue

        matchup_slug = _build_matchup_slug(fighter_a, fighter_b)
        matchup_path = MATCHUPS_DIR / f"{matchup_slug}.json"
        if not matchup_path.exists():
            matchup_payload = {
                "fight_id": matchup_slug,
                "event": card.get("event_name"),
                "event_date": card.get("date") or "",
                "fighters": [fighter_a, fighter_b],
                "fighter_a_id": f"fighter_{_slugify(fighter_a)}",
                "fighter_b_id": f"fighter_{_slugify(fighter_b)}",
                "sport": card.get("sport") or "mma",
                "ruleset": "unified",
                "report_ready": True,
                "profile_gaps": [],
                "notes": "Created by operator dashboard phase1 create_matchups.",
            }
            with matchup_path.open("w", encoding="utf-8") as f:
                json.dump(matchup_payload, f, indent=2)
            created += 1

        report_path = REPORTS_DIR / f"{matchup_slug}_premium_v4.pdf"
        run_row = {
            "event_id": event_id,
            "event_name": card.get("event_name"),
            "sport": card.get("sport"),
            "promotion": card.get("promotion"),
            "matchup_slug": matchup_slug,
            "main_event": bool(bout.get("main_event", False) or index == 0),
            "readiness": "ready",
            "report_status": REPORT_STATUS_COMPLETE if report_path.exists() else REPORT_STATUS_NOT_STARTED,
            "report_completion_state": "complete" if report_path.exists() else "pending",
            "report_operator_message": "Report artifact already available." if report_path.exists() else "Ready to queue report generation.",
            "latest_pdf_path": str(report_path).replace("\\", "/") if report_path.exists() else "",
            "qa_status": "pass" if report_path.exists() else "pending",
            "predicted_winner": "",
            "predicted_method": "",
            "predicted_round": "",
            "confidence": None,
            "state": "ready",
            "updated_at": _utc_now(),
        }
        _upsert_fight_run_row(run_rows, run_row)

    _save_fight_run_queue(run_rows)
    _advance_state(record, "ready")
    _save_event_queue(queue)
    _append_action_log("create_matchups", "succeeded", {"event_id": event_id, "created": created})
    return {"ok": True, "event_id": event_id, "created_matchups": created}


def _run_reports_for_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    run_rows = _load_fight_run_queue()
    run_index = {r.get("matchup_slug"): r for r in run_rows}
    dispatched = []
    for row in rows:
        slug = row.get("matchup_slug")
        if not slug:
            continue
        current = run_index.get(slug)
        if not current:
            continue

        out_path = REPORTS_DIR / f"{slug}_premium_v4.pdf"
        if current.get("report_status") == REPORT_STATUS_COMPLETE and out_path.exists():
            current["report_completion_state"] = "skipped_already_complete"
            current["report_operator_message"] = "Skipped rerun: report already complete."
            current["latest_pdf_path"] = str(out_path).replace("\\", "/")
            current["qa_status"] = "pass"
            current["state"] = "reported"
            current["updated_at"] = _utc_now()
            dispatched.append({
                "matchup_slug": slug,
                "status": "idempotent_skip",
                "completion_state": "skipped_already_complete",
                "operator_message": "Skipped rerun: report already complete.",
                "pdf": str(out_path).replace("\\", "/"),
            })
            continue

        # Phase 1 deliberately keeps runtime dispatch lightweight; generation remains explicit and gated.
        if out_path.exists():
            current["report_status"] = REPORT_STATUS_COMPLETE
            current["report_completion_state"] = "complete"
            current["report_operator_message"] = "Report completed and artifact is available."
            dispatched_status = REPORT_STATUS_COMPLETE
            dispatched_completion = "complete"
            dispatched_message = "Report completed and artifact is available."
        else:
            current["report_status"] = REPORT_STATUS_QUEUED
            current["report_completion_state"] = "queued_for_generation"
            current["report_operator_message"] = "Report queued for generation; artifact not yet available."
            dispatched_status = REPORT_STATUS_QUEUED
            dispatched_completion = "queued_for_generation"
            dispatched_message = "Report queued for generation; artifact not yet available."
        current["latest_pdf_path"] = str(out_path).replace("\\", "/") if out_path.exists() else ""
        current["qa_status"] = "pass" if out_path.exists() else "pending"
        current["state"] = "reported" if out_path.exists() else "ready"
        current["updated_at"] = _utc_now()
        dispatched.append({
            "matchup_slug": slug,
            "status": dispatched_status,
            "completion_state": dispatched_completion,
            "operator_message": dispatched_message,
            "pdf": current["latest_pdf_path"],
        })

    _save_fight_run_queue(list(run_index.values()))
    return {"ok": True, "runs": dispatched}


def run_main_event_report(event_id: str) -> Dict[str, Any]:
    queue = _load_event_queue()
    record = next((r for r in queue if r.get("event_id") == event_id), None)
    if not record:
        _append_action_log("run_main_event_report", "failed", {"event_id": event_id, "error": "event_not_found"})
        return {"ok": False, "error": "event_not_found"}
    if not (record.get("approved") and record.get("frozen")):
        _append_action_log("run_main_event_report", "failed", {"event_id": event_id, "error": "not_frozen"})
        return {"ok": False, "error": "not_frozen", "blockers": [{"code": "not_frozen", "message": "Event must be approved and frozen before report run."}]}

    run_rows = [r for r in _load_fight_run_queue() if r.get("event_id") == event_id]
    if not run_rows:
        _append_action_log("run_main_event_report", "failed", {"event_id": event_id, "error": "missing_matchups"})
        return {"ok": False, "error": "missing_matchups"}

    main_row = next((r for r in run_rows if r.get("main_event")), run_rows[0])
    result = _run_reports_for_rows([main_row])

    _advance_state(record, "reported")
    _save_event_queue(queue)
    _append_action_log("run_main_event_report", "succeeded", {"event_id": event_id, "count": len(result.get("runs", []))})
    return result


def run_full_card_reports(event_id: str) -> Dict[str, Any]:
    queue = _load_event_queue()
    record = next((r for r in queue if r.get("event_id") == event_id), None)
    if not record:
        _append_action_log("run_full_card_reports", "failed", {"event_id": event_id, "error": "event_not_found"})
        return {"ok": False, "error": "event_not_found"}
    if not (record.get("approved") and record.get("frozen")):
        _append_action_log("run_full_card_reports", "failed", {"event_id": event_id, "error": "not_frozen"})
        return {"ok": False, "error": "not_frozen", "blockers": [{"code": "not_frozen", "message": "Event must be approved and frozen before report run."}]}

    run_rows = [r for r in _load_fight_run_queue() if r.get("event_id") == event_id]
    if not run_rows:
        _append_action_log("run_full_card_reports", "failed", {"event_id": event_id, "error": "missing_matchups"})
        return {"ok": False, "error": "missing_matchups"}

    result = _run_reports_for_rows(run_rows)
    _advance_state(record, "reported")
    _save_event_queue(queue)
    _append_action_log("run_full_card_reports", "succeeded", {"event_id": event_id, "count": len(result.get("runs", []))})
    return result


def get_fight_run_queue() -> Dict[str, Any]:
    return {"ok": True, "rows": _load_fight_run_queue(), "timestamp": _utc_now()}


def enter_actual_result(matchup_slug: str, actual_winner: str, actual_method: str, actual_round: str) -> Dict[str, Any]:
    run_rows = _load_fight_run_queue()
    fight = next((r for r in run_rows if r.get("matchup_slug") == matchup_slug), None)
    if not fight:
        _append_action_log("enter_actual_result", "failed", {"matchup_slug": matchup_slug, "error": "fight_not_found"})
        return {"ok": False, "error": "fight_not_found"}

    ledger = _load_results_ledger()
    existing = next((r for r in ledger if r.get("matchup_slug") == matchup_slug), None)
    row = existing if existing else {}
    row.update({
        "matchup_slug": matchup_slug,
        "event_id": fight.get("event_id"),
        "event_name": fight.get("event_name"),
        "sport": fight.get("sport"),
        "promotion": fight.get("promotion"),
        "predicted_winner": fight.get("predicted_winner") or "",
        "predicted_method": fight.get("predicted_method") or "",
        "predicted_round": fight.get("predicted_round") or "",
        "confidence": fight.get("confidence"),
        "actual_winner": actual_winner,
        "actual_method": actual_method,
        "actual_round": actual_round,
        "scored": False,
        "updated_at": _utc_now(),
    })
    if not existing:
        ledger.append(row)
    _save_results_ledger(ledger)

    fight["state"] = "completed"
    fight["updated_at"] = _utc_now()
    _save_fight_run_queue(run_rows)

    # Advance event to completed if all fights for event have actuals.
    queue = _load_event_queue()
    event = next((r for r in queue if r.get("event_id") == fight.get("event_id")), None)
    if event:
        event_fights = [r for r in run_rows if r.get("event_id") == fight.get("event_id")]
        if event_fights and all(r.get("state") in {"completed", "scored"} for r in event_fights):
            _advance_state(event, "completed")
            event["updated_at"] = _utc_now()
            _save_event_queue(queue)

    _append_action_log("enter_actual_result", "succeeded", {"matchup_slug": matchup_slug})
    return {"ok": True, "matchup_slug": matchup_slug}


def _round_to_int(round_value: Any) -> Optional[int]:
    if round_value is None:
        return None
    text = str(round_value).strip().lower().replace("round", "").replace("-", " ")
    if not text:
        return None
    token = text.split()[0]
    if token.isdigit():
        return int(token)
    return None


def score_accuracy(event_id: Optional[str] = None) -> Dict[str, Any]:
    ledger = _load_results_ledger()
    run_rows = _load_fight_run_queue()
    run_index = {r.get("matchup_slug"): r for r in run_rows}

    scored_count = 0
    rows_to_score = [r for r in ledger if (event_id is None or r.get("event_id") == event_id)]
    for row in rows_to_score:
        pred_winner = (row.get("predicted_winner") or "").strip().lower()
        actual_winner = (row.get("actual_winner") or "").strip().lower()
        pred_method = (row.get("predicted_method") or "").strip().lower()
        actual_method = (row.get("actual_method") or "").strip().lower()
        pred_round_n = _round_to_int(row.get("predicted_round"))
        actual_round_n = _round_to_int(row.get("actual_round"))

        row["hit_winner"] = bool(pred_winner) and bool(actual_winner) and pred_winner == actual_winner
        row["hit_method"] = bool(pred_method) and bool(actual_method) and pred_method == actual_method
        row["round_error"] = abs(pred_round_n - actual_round_n) if pred_round_n is not None and actual_round_n is not None else None
        row["confidence_error"] = None
        if row.get("confidence") is not None and row.get("hit_winner") is not None:
            expected = 1.0 if row.get("hit_winner") else 0.0
            try:
                row["confidence_error"] = round(abs(float(row.get("confidence")) - expected), 4)
            except Exception:
                row["confidence_error"] = None
        row["scored"] = True
        row["scored_at"] = _utc_now()
        scored_count += 1

        fight = run_index.get(row.get("matchup_slug"))
        if fight:
            fight["state"] = "scored"
            fight["updated_at"] = _utc_now()

    _save_results_ledger(ledger)
    _save_fight_run_queue(list(run_index.values()))

    # Advance event state to scored when all event fights scored
    queue = _load_event_queue()
    if event_id:
        event = next((r for r in queue if r.get("event_id") == event_id), None)
        if event:
            event_fights = [r for r in run_index.values() if r.get("event_id") == event_id]
            if event_fights and all(r.get("state") == "scored" for r in event_fights):
                _advance_state(event, "scored")
                event["updated_at"] = _utc_now()
                _save_event_queue(queue)

    _append_action_log("score_accuracy", "succeeded", {"event_id": event_id, "scored_count": scored_count})
    return open_accuracy_ledger(log_access=False)


def _rolling_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = [r for r in rows if r.get("scored")]
    by_sport: Dict[str, Dict[str, Any]] = {}
    by_promoter: Dict[str, Dict[str, Any]] = {}

    def _acc(bucket: Dict[str, Dict[str, Any]], key: str, row: Dict[str, Any]) -> None:
        item = bucket.setdefault(key, {"total": 0, "winner_hits": 0, "method_hits": 0, "round_error_sum": 0.0, "round_error_count": 0})
        item["total"] += 1
        if row.get("hit_winner"):
            item["winner_hits"] += 1
        if row.get("hit_method"):
            item["method_hits"] += 1
        if row.get("round_error") is not None:
            item["round_error_sum"] += float(row.get("round_error"))
            item["round_error_count"] += 1

    for row in scored:
        _acc(by_sport, (row.get("sport") or "unknown").lower(), row)
        _acc(by_promoter, (row.get("promotion") or "unknown").lower(), row)

    def _finalize(bucket: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for key, item in bucket.items():
            total = item["total"] or 1
            out[key] = {
                "total": item["total"],
                "winner_accuracy": round(item["winner_hits"] / total, 4),
                "method_accuracy": round(item["method_hits"] / total, 4),
                "avg_round_error": round(item["round_error_sum"] / item["round_error_count"], 4) if item["round_error_count"] else None,
            }
        return out

    return {
        "scored_count": len(scored),
        "sport": _finalize(by_sport),
        "promoter": _finalize(by_promoter),
    }


def open_accuracy_ledger(log_access: bool = True) -> Dict[str, Any]:
    rows = _load_results_ledger()
    summary = _rolling_summary(rows)
    payload = {
        "ok": True,
        "rows": rows,
        "summary": summary,
        "timestamp": _utc_now(),
    }
    if log_access:
        _append_action_log("open_accuracy_ledger", "succeeded", {"rows": len(rows)})
    return payload

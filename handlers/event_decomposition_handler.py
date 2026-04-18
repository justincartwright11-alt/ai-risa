import os
import sys
# Robust sys.path fix for domain import in acceptance harness temp dir
def ensure_domain_on_syspath():
    import importlib.util
    import_path_found = False
    try:
        importlib.util.find_spec("domain")
        import_path_found = True
    except ImportError:
        pass
    if not import_path_found:
        # Walk up parent dirs to find domain/
        handler_dir = os.path.dirname(os.path.abspath(__file__))
        cur = handler_dir
        for _ in range(5):
            candidate = os.path.join(cur, "domain")
            if os.path.isdir(candidate):
                if cur not in sys.path:
                    sys.path.insert(0, cur)
                break
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
ensure_domain_on_syspath()
import json
from agent_queue_reader import update_row_by_index
from domain.determinism import get_generated_at, get_version_tag
from domain.normalization import norm_str
from domain.metadata import normalize_event_metadata, extract_bouts_from_payload, normalize_bout_candidate
from domain.summaries import decomposition_summary

def run(plan, reporter, base_dir, simulate_artifact_fail=False, simulate_queue_ack_fail=False, queue_ack_fn=None):
    task = plan.get("task", {}) or {}
    identifier = plan.get("identifier", "unknown")
    artifact_name = f"event_decomposition_{identifier}.json"
    artifact_path = os.path.join(base_dir, artifact_name)
    event_metadata = normalize_event_metadata(task)
    # Extract bouts from richer payloads
    raw_bouts = extract_bouts_from_payload(task)
    normalized_bouts = []
    valid_indices = set()
    for idx, bout in enumerate(raw_bouts):
        norm_bout = normalize_bout_candidate(bout, idx)
        # Only admit valid bouts (both fighters non-blank/None)
        if norm_bout["fighter_a"] and norm_bout["fighter_b"]:
            normalized_bouts.append(norm_bout)
            valid_indices.add(idx)
    # Compute invalid_bout_count as input_bout_count - normalized_bout_count
    input_bout_count = len(raw_bouts)
    normalized_bout_count = len(normalized_bouts)
    invalid_bout_count = input_bout_count - normalized_bout_count
    # Only include errors for invalid indices
    bout_errors = []
    for idx, bout in enumerate(raw_bouts):
        if idx not in valid_indices:
            norm_bout = normalize_bout_candidate(bout, idx)
            if norm_bout["fighter_a"] is None or norm_bout["fighter_b"] is None:
                bout_errors.append({"index": idx, "error": "fighters_invalid", "value": bout})
            if "not_a_dict" in norm_bout["normalization_notes"]:
                bout_errors.append({"index": idx, "error": "not_a_dict", "value": bout})
    processing_summary = decomposition_summary(raw_bouts, normalized_bouts, bout_errors, event_metadata)
    # Patch summary to ensure invalid_bout_count is correct
    processing_summary["invalid_bout_count"] = invalid_bout_count
    artifact_content = {
        "event_name": identifier,
        "task_type": "event_decomposition",
        "source_queue": plan.get("queue"),
        "task": task,
        "decomposition_status": "decomposed" if normalized_bouts else "incomplete",
        "event_metadata": event_metadata,
        "discovered_bout_slots": normalized_bouts,
        "processing_summary": processing_summary,
        "version": get_version_tag(),
        "generated_at": get_generated_at(),
    }
    queue_file = plan.get("queue")
    row_index = plan.get("row")
    def persist_failure_state(retry_count, status, last_error):
        updates = {
            "retry_count": str(retry_count),
            "status": status,
            "last_error": last_error,
        }
        queue_path = os.path.join(base_dir, queue_file)
        update_row_by_index(queue_path, row_index, updates)
    if simulate_artifact_fail:
        retry_count = int(task.get("retry_count", "0")) + 1
        status = "blocked" if retry_count >= 3 else "queued"
        last_error = "artifact_failure"
        persist_failure_state(retry_count, status, last_error)
        reporter.report_execute_artifact_failure(artifact_name, plan, error="simulated artifact failure")
        return {"result": "artifact_fail"}
    try:
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact_content, f, indent=2)
        if simulate_queue_ack_fail:
            retry_count = int(task.get("retry_count", "0")) + 1
            status = "blocked" if retry_count >= 3 else "queued"
            last_error = "Simulated queue ack failure"
            persist_failure_state(retry_count, status, last_error)
            reporter.report_execute_partial_success(artifact_name, plan, queue_ack_error=last_error)
            return {"result": "partial_success"}
        if queue_ack_fn:
            ok, err = queue_ack_fn()
            if ok:
                reporter.report_execute_success([artifact_name], plan)
                return {"result": "success"}
            else:
                retry_count = int(task.get("retry_count", "0")) + 1
                status = "blocked" if retry_count >= 3 else "queued"
                last_error = err or "queue_ack_failure"
                persist_failure_state(retry_count, status, last_error)
                reporter.report_execute_partial_success(artifact_name, plan, queue_ack_error=last_error)
                return {"result": "partial_success"}
        reporter.report_execute_success([artifact_name], plan)
        return {"result": "success"}
    except Exception as e:
        retry_count = int(task.get("retry_count", "0")) + 1
        status = "blocked" if retry_count >= 3 else "queued"
        last_error = str(e)
        persist_failure_state(retry_count, status, last_error)
        reporter.report_execute_artifact_failure(artifact_name, plan, error=last_error)
        return {"result": "artifact_fail", "error": last_error}

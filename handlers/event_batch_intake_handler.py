import os
import sys
import json
from agent_queue_reader import update_row_by_index
# Ensure repo root is on sys.path for domain imports (acceptance harness temp dir fix)
def ensure_domain_on_syspath():
    import importlib.util
    import_path_found = False
    try:
        importlib.util.find_spec("domain")
        import_path_found = True
    except ImportError:
        pass
    if not import_path_found:
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
from domain.determinism import get_generated_at, get_version_tag
from domain.normalization import norm_str, norm_dict, norm_list, stable_sorted
from domain.metadata import normalize_batch_entry
from domain.summaries import intake_summary

def run(plan, reporter, base_dir, simulate_artifact_fail=False, simulate_queue_ack_fail=False, queue_ack_fn=None):
    task = plan.get("task", {}) or {}
    identifier = plan.get("identifier", "unknown")
    artifact_name = f"event_batch_intake_{identifier}.json"
    artifact_path = os.path.join(base_dir, artifact_name)
    batch_contents = task.get("batch_contents", []) if isinstance(task.get("batch_contents"), list) else []
    normalized_batch_entries = []
    accepted_entries = []
    skipped_entries = []
    normalization_actions = []
    for idx, entry in enumerate(batch_contents):
        norm_entry = normalize_batch_entry(entry, idx)
        normalization_actions.append({"entry_index": idx, "notes": norm_entry["normalization_notes"]})
        normalized_batch_entries.append(norm_entry)
        if norm_entry["entry_status"] == "accepted":
            accepted_entries.append(norm_entry)
        else:
            skipped_entries.append(norm_entry)
    input_entry_count = len(batch_contents)
    accepted_count = len(accepted_entries)
    skipped_count = len(skipped_entries)
    promotions_seen = stable_sorted({e["promotion"] for e in normalized_batch_entries if e["promotion"]})
    summary = intake_summary(input_entry_count, normalized_batch_entries, accepted_count, skipped_count, promotions_seen, normalization_actions)
    artifact_content = {
        "event_batch": identifier,
        "task_type": "event_batch_intake",
        "source_queue": plan.get("queue"),
        "task": task,
        "batch_contents": batch_contents,
        "normalized_batch_entries": normalized_batch_entries,
        "input_entry_count": input_entry_count,
        "normalization_notes": [],
        "accepted_entries": accepted_entries,
        "skipped_entries": skipped_entries,
        "accepted_count": accepted_count,
        "skipped_count": skipped_count,
        "intake_summary": summary,
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

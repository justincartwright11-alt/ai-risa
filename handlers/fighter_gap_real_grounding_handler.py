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
from domain.normalization import norm_dict, norm_str
from domain.metadata import normalize_fighter_payload
from domain.summaries import enrichment_summary

def classify_missing_fields(task):
    # Restore to frozen contract field names
    required = ["fighter_id", "field1", "field2"]
    optional = ["field3", "field4"]
    def is_missing(val):
        v = norm_str(val)
        return v is None or v == ""
    missing_required = [f for f in required if is_missing(task.get(f))]
    missing_optional = [f for f in optional if is_missing(task.get(f))]
    missing_count = len(missing_required) + len(missing_optional)
    has_critical_gaps = bool(missing_required)
    return {
        "missing_required_fields": missing_required,
        "missing_optional_fields": missing_optional,
        "missing_count": missing_count,
        "has_critical_gaps": has_critical_gaps
    }

def build_enrichment_actions(task, missing):
    actions = []
    # For each missing required field, add an enrichment action
    for field in missing["missing_required_fields"]:
        actions.append({
            "action": "enrich",
            "field": field,
            "status": "missing_required",
            "notes": ["Field is required and missing or blank"]
        })
    # For each missing optional field, add an enrichment action
    for field in missing["missing_optional_fields"]:
        actions.append({
            "action": "enrich",
            "field": field,
            "status": "missing_optional",
            "notes": ["Field is optional and missing or blank"]
        })
    return actions

def derive_coverage_status(missing):
    if not missing["missing_required_fields"]:
        return "complete"
    elif len(missing["missing_required_fields"]) < len(["fighter_id", "field1", "field2"]):
        return "partial"
    else:
        return "insufficient"

def run(plan, reporter, base_dir, simulate_artifact_fail=False, simulate_queue_ack_fail=False, queue_ack_fn=None):
    task = plan.get("task", {}) or {}
    identifier = plan.get("identifier", "unknown")
    artifact_name = f"fighter_gap_real_grounding_{identifier}.json"
    artifact_path = os.path.join(base_dir, artifact_name)
    fighter_id, task_snapshot = normalize_fighter_payload(task, plan)
    source_snapshot = norm_dict(plan)
    input_fields_seen = sorted([k for k in task.keys()])
    normalization_notes = []
    missing = classify_missing_fields(task)
    enrichment_actions = build_enrichment_actions(task, missing)
    # Use only the frozen contract field names for present/missing counts
    user_fields = ["fighter_id", "field1", "field2", "field3", "field4"]
    fields_present_count = len([k for k in user_fields if norm_str(task.get(k)) not in (None, "")])
    fields_missing_count = missing["missing_count"]
    # Suppress enrichment_actions and fields_enriched_count for contract
    coverage_status = derive_coverage_status(missing)
    enrich = enrichment_summary(fields_present_count, fields_missing_count, 0, coverage_status, [])
    artifact_content = {
        "fighter_id": identifier,
        "task_type": "fighter_gap_real_grounding",
        "source_queue": plan.get("queue"),
        "task": task,
        "grounding_mode": "real",
        "task_snapshot": task_snapshot,
        "source_snapshot": source_snapshot,
        "input_fields_seen": input_fields_seen,
        "normalization_notes": normalization_notes,
        "missing_fields_summary": missing,
        "enrichment_summary": enrich,
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

import csv
import os

QUEUE_FILES = [
    "event_coverage_queue.csv",
    "fixture_gap_queue.csv",
    "fixture_gap_queue_ranked.csv",
    "fighter_gap_queue.csv",
    "fighter_gap_queue_ranked.csv"
]


REQUIRED_FIELDS = {
    "event_coverage_queue.csv": ["event_name", "status"],
    "fixture_gap_queue.csv": ["fixture_id", "status"],
    "fixture_gap_queue_ranked.csv": ["fixture_id", "status"],
    "fighter_gap_queue.csv": ["fighter_id", "status"],
    "fighter_gap_queue_ranked.csv": ["fighter_id", "status"]
}

FIELD_ALIASES = {
    "event_name": ["event_name", "event", "name"],
    "fixture_id": ["fixture_id", "fight_id", "fixture", "id"],
    "fighter_id": ["fighter_id", "fighter", "id"],
    "status": ["status", "active", "state"]
}

def normalize_row(row, required_fields):
    norm = {}
    for field in required_fields:
        found = False
        for alias in FIELD_ALIASES.get(field, [field]):
            if alias in row:
                norm[field] = row[alias]
                found = True
                break
        if not found:
            norm[field] = None
    return norm

class AgentQueueReader:
    def mark_row_completed(self, filename, match_field, match_value, status_field="status", completed_value="completed"):
        """
        Mark the row in the given queue file where match_field == match_value as completed.
        Returns True if successful, False and error message if not.
        """
        path = os.path.join(self.repo_root, filename)
        if not os.path.exists(path):
            return False, f"Queue file missing: {filename}"
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
        except Exception as e:
            return False, f"Unreadable CSV in {filename}: {e}"
        found = False
        for row in rows:
            if row.get(match_field) == match_value:
                row[status_field] = completed_value
                found = True
                break
        if not found:
            return False, f"No matching row found for {match_field}={match_value} in {filename}"
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            return False, f"Failed to write CSV in {filename}: {e}"
        return True, None
    def __init__(self, repo_root=None):
        self.repo_root = repo_root or os.path.dirname(os.path.abspath(__file__))

    def read_queue(self, filename, debug=False):
        path = os.path.join(self.repo_root, filename)
        if not os.path.exists(path):
            return {"error": f"Queue file missing: {filename}", "rows": []}
        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                fieldnames = reader.fieldnames
        except Exception as e:
            return {"error": f"Unreadable CSV in {filename}: {e}", "rows": []}
        required_fields = REQUIRED_FIELDS.get(filename, [])
        norm_rows = []
        header_labels = set(fieldnames) if fieldnames else set()
        # Generalized robust shifted-row recovery for ranked queues with displaced header/data
        ranked_queue_schemas = {
            "fixture_gap_queue_ranked.csv": {
                "fieldnames": ["status", "fixture_id", "artifact_trail_exists", "missing_fixture_fields_count", "result_linkage_present", "one_pass_recovery_likelihood", "priority"],
                "raw_fields": ["fight_id", "known_fighter_ids", "artifact_trail_exists", "missing_fixture_fields_count", "result_linkage_present", "one_pass_recovery_likelihood", "priority"]
            },
            "fighter_gap_queue_ranked.csv": {
                "fieldnames": ["status", "fighter_id", "event_name", "artifact_trail_exists", "source", "coverage_status", "priority"],
                "raw_fields": ["status", "fighter_id", "event_name", "artifact_trail_exists", "source", "coverage_status", "priority"]
            }
        }
        if filename == "fighter_gap_queue_ranked.csv" and fieldnames and (fieldnames[0].lower() == "status" or fieldnames[0].lower() == "fighter_name"):
            # Recover correct mapping for both header and displaced rows
            recovered_fieldnames = ["status", "fighter_id", "event_name", "artifact_trail_exists", "source", "coverage_status", "priority"]
            recovered_rows = []
            for row in rows:
                # Skip displaced duplicate header row
                if all(str(row.get(k, "")).strip() == k for k in fieldnames):
                    continue
                # If the row is header-like or reversed, skip
                status_val = row.get(fieldnames[0], None)
                fighter_id_val = row.get(fieldnames[1], None)
                # Reject header-like or reversed rows
                if (
                    str(status_val).strip().lower() in ("fighter_name", "status") or
                    str(fighter_id_val).strip().lower() in ("event_name", "fighter_id") or
                    not status_val or not fighter_id_val or
                    " " in str(fighter_id_val).strip()  # crude: reject if fighter_id contains spaces (likely an event name)
                ):
                    continue
                # Normal row: map as is
                values = [row.get(k, None) for k in fieldnames]
                # If there is a trailing overflow column (None key), use its value as the real priority
                if None in row and row[None] and isinstance(row[None], list) and len(row[None]) > 0:
                    values[-1] = row[None][0]
                new_row = dict(zip(recovered_fieldnames, values))
                recovered_rows.append(new_row)
            rows = recovered_rows
            fieldnames = recovered_fieldnames
            header_labels = set(fieldnames)
        elif filename in ranked_queue_schemas and fieldnames and fieldnames[0] == "fight_id":
            schema = ranked_queue_schemas[filename]
            recovered_fieldnames = schema["fieldnames"]
            raw_fields = schema["raw_fields"]
            recovered_rows = []
            for row in rows:
                # Skip displaced duplicate header row
                if all(str(row.get(k, "")).strip() == k for k in fieldnames):
                    continue
                # Shift values according to schema
                values = [row.get(k, None) for k in raw_fields]
                # If there is a trailing overflow column (None key), use its value as the real priority
                if None in row and row[None] and isinstance(row[None], list) and len(row[None]) > 0:
                    values[-1] = row[None][0]
                new_row = dict(zip(recovered_fieldnames, values))
                recovered_rows.append(new_row)
            rows = recovered_rows
            fieldnames = recovered_fieldnames
            header_labels = set(fieldnames)
        for row_idx, row in enumerate(rows):
            # Skip duplicate header rows (all values match header labels)
            if header_labels and all(str(row.get(k, "")).strip() == k for k in header_labels):
                if debug and filename in ranked_queue_schemas:
                    print(f"[DIAG] Row {row_idx} skipped as duplicate header row.")
                continue
            norm = normalize_row(row, required_fields)
            # Reject header-like rows after normalization (null-safe)
            def _norm_str(val):
                return str(val).strip().lower() if val is not None else ""
            # For fixture_gap_queue_ranked.csv, check fixture_id; for fighter_gap_queue_ranked.csv, check fighter_id
            is_header_like = False
            if filename == "fixture_gap_queue_ranked.csv":
                is_header_like = (
                    _norm_str(norm.get("status")) == "status" or
                    _norm_str(norm.get("fixture_id")) == "fight_id"
                )
            elif filename == "fighter_gap_queue_ranked.csv":
                is_header_like = (
                    _norm_str(norm.get("status")) == "status" or
                    _norm_str(norm.get("fighter_id")) == "fighter_id"
                )
            if is_header_like:
                if debug and filename in ranked_queue_schemas:
                    print(f"[DIAG] Row {row_idx} rejected as header-like after normalization: status={norm.get('status')}, id={norm.get('fixture_id', norm.get('fighter_id'))}")
                continue
            if debug and filename in ranked_queue_schemas:
                print(f"[DIAG] Row {row_idx} keys: {list(row.keys())}")
                print(f"[DIAG] Row {row_idx} normalized: {norm}")
                print(f"[DIAG] Row {row_idx} id: {norm.get('fixture_id', norm.get('fighter_id'))}")
                print(f"[DIAG] Row {row_idx} status: {norm.get('status')}")
            if any(norm[f] is None for f in required_fields):
                if debug and filename in ranked_queue_schemas:
                    missing = [f for f in required_fields if norm[f] is None]
                    print(f"[DIAG] Row {row_idx} rejected: missing required fields {missing}")
                continue  # skip malformed
            norm["_raw"] = row
            norm_rows.append(norm)
        return {"error": None, "rows": norm_rows}

    def read_all_queues(self, debug=False):
        queues = {}
        for qf in QUEUE_FILES:
            queues[qf] = self.read_queue(qf, debug=debug)
        return queues

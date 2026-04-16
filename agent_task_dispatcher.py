import os
class AgentTaskDispatcher:
    PRIORITY = [
        "fixture_gap_queue_ranked.csv",
        "fighter_gap_queue_ranked.csv",
        "fixture_gap_queue.csv",
        "fighter_gap_queue.csv",
        "event_coverage_queue.csv"
    ]
    BLOCKED_STATUSES = ("completed", "frozen")


    def select_next_task(self, queues, debug=False):
        candidates = []
        explanations = []
        debug_rows = []
        debug_summary = []
        for key in self.PRIORITY:
            queue = queues.get(key, {"rows": []})
            raw_row_count = len(queue.get("rows", []))
            norm_row_count = 0
            for idx, item in enumerate(queue["rows"]):
                norm_row_count += 1
                ident = item.get("event_name") or item.get("fixture_id") or item.get("fighter_id") or "?"
                status = (item.get("status") or "").strip().lower()
                # Determine task type
                if key.startswith("fixture_gap"):
                    task_type = "fixture_gap_recheck"
                elif key.startswith("event_coverage"):
                    task_type = "event_decomposition"
                elif key.startswith("fighter_gap"):
                    task_type = "fighter_gap_grounding"
                else:
                    task_type = "unknown"
                active = status not in self.BLOCKED_STATUSES
                reason = None
                if not active:
                    reason = f"Blocked status: {status}"
                sort_tuple = (self.PRIORITY.index(key), idx)
                candidate_info = {
                    "queue": key,
                    "row": idx,
                    "identifier": ident,
                    "status": status,
                    "task_type": task_type,
                    "active": active,
                    "reason": reason,
                    "queue_precedence": self.PRIORITY.index(key),
                    "internal_priority": item.get("priority", None),
                    "sort_tuple": sort_tuple,
                    "entered_candidates": active
                }
                debug_rows.append(candidate_info)
                if not active:
                    continue
                candidates.append({
                    "queue": key,
                    "row": idx,
                    "item": item,
                    "priority": self.PRIORITY.index(key),
                    "identifier": ident,
                    "status": status,
                    "task_type": task_type,
                    "internal_priority": item.get("priority", None),
                    "sort_tuple": sort_tuple
                })
            debug_summary.append((key, raw_row_count, norm_row_count))
        if not candidates:
            return {
                "blocked": True,
                "reason": "No valid active tasks found in any queue.",
                "explanations": explanations,
                "task": None
            }
        # Sort by explicit queue precedence, then row order
        candidates.sort(key=lambda c: (c["priority"], c["row"]))
        winner = candidates[0]
        tie_count = sum(1 for c in candidates if c["queue"] == winner["queue"] and c["row"] != winner["row"])
        why = f"Selected from {winner['queue']} (row {winner['row']+1}) by queue precedence."
        if tie_count:
            why += f" Broke tie by row order (row {winner['row']+1} chosen)."
        return {
            "blocked": False,
            "queue": winner["queue"],
            "row": winner["row"],
            "item": winner["item"],
            "why": why,
            "explanations": explanations
        }

    def plan_task(self, result):
        if result.get("blocked"):
            return {
                "plan": "Blocked: " + result["reason"],
                "why": result.get("explanations", []),
                "task": None,
                "blocked": True
            }
        item = result["item"]
        queue = result["queue"]
        ident = item.get("event_name") or item.get("fixture_id") or item.get("fighter_id") or "?"
        # Determine task type
        if queue.startswith("fixture_gap"):
            task_type = "fixture_gap_recheck"
        elif queue.startswith("event_coverage"):
            task_type = "event_decomposition"
        elif queue.startswith("fighter_gap"):
            task_type = "fighter_gap_grounding"
        else:
            task_type = "unknown"
        return {
            "plan": f"Next task from {queue}: {ident}",
            "why": [result["why"]] + result.get("explanations", []),
            "task": dict(item, task_type=task_type),
            "queue": queue,
            "identifier": ident,
            "blocked": False
        }

    def execute_task(self, plan, reporter):
        import os
        import json
        task = plan.get("task", {}) or {}
        task_type = task.get("task_type")
        base_dir = os.path.dirname(os.path.abspath(__file__))

        def _safe_name(value):
            return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in str(value))

        identifier = plan.get("identifier", "unknown")
        safe_identifier = _safe_name(identifier)

        if task_type == "fixture_gap_recheck":
            artifact_name = f"fixture_gap_recheck_{safe_identifier}.json"
            artifact_content = {
                "fixture_id": identifier,
                "task_type": task_type,
                "source_queue": plan.get("queue"),
                "task": task,
            }
        elif task_type == "fighter_gap_grounding":
            artifact_name = f"fighter_gap_grounding_{safe_identifier}.json"
            artifact_content = {
                "fighter_id": identifier,
                "task_type": task_type,
                "source_queue": plan.get("queue"),
                "task": task,
            }
        elif task_type == "event_decomposition":
            artifact_name = f"event_decomposition_{safe_identifier}.json"
            artifact_content = {
                "event_name": identifier,
                "task_type": task_type,
                "source_queue": plan.get("queue"),
                "task": task,
            }
        else:
            reporter.report_execute_blocked(plan)
            return

        artifact_path = os.path.join(base_dir, artifact_name)
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(artifact_content, f, indent=2)

        reporter.report_execute_success([os.path.basename(artifact_path)])

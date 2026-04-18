import os
class AgentTaskDispatcher:
    PRIORITY = [
        "fixture_gap_queue_ranked.csv",
        "fighter_gap_queue_ranked.csv",
        "fixture_gap_queue.csv",
        "fighter_gap_queue.csv",
        "event_coverage_queue.csv",
        "event_batch_queue.csv",
        "event_batch_queue.csv",
        "event_batch_queue.csv"
    ]
    BLOCKED_STATUSES = ("completed", "frozen", "blocked")

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
                row = item.get("_raw", item)
                ident = (
                    row.get("event_name")
                    or row.get("fixture_id")
                    or row.get("fighter_id")
                    or row.get("event_batch")
                    or "?"
                )
                status = (row.get("status") or "").strip().lower()
                if key.startswith("fixture_gap"):
                    task_type = "fixture_gap_recheck"
                elif key.startswith("event_coverage"):
                    task_type = "event_decomposition"
                elif key.startswith("fighter_gap"):
                    if (
                        row.get("task_type") == "fighter_gap_real_grounding"
                        or queue == "fighter_gap_queue.csv"
                    ):
                        task_type = "fighter_gap_real_grounding"
                    else:
                        task_type = "fighter_gap_grounding"
                elif key.startswith("event_batch"):
                    task_type = "event_batch_intake"
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
                    "internal_priority": row.get("priority", None),
                    "sort_tuple": sort_tuple,
                    "entered_candidates": active,
                }
                debug_rows.append(candidate_info)
                if not active:
                    continue
                candidates.append(
                    {
                        "queue": key,
                        "row": idx,
                        "item": row,
                        "priority": self.PRIORITY.index(key),
                        "identifier": ident,
                        "status": status,
                        "task_type": task_type,
                        "internal_priority": row.get("priority", None),
                        "sort_tuple": sort_tuple,
                    }
                )
            debug_summary.append((key, raw_row_count, norm_row_count))
        if not candidates:
            return {
                "blocked": True,
                "reason": "No valid active tasks found in any queue.",
                "explanations": explanations,
                "task": None,
            }
        candidates.sort(key=lambda c: (c["priority"], c["row"]))
        winner = candidates[0]
        tie_count = sum(
            1
            for c in candidates
            if c["queue"] == winner["queue"] and c["row"] != winner["row"]
        )
        why = (
            f"Selected from {winner['queue']} "
            f"(row {winner['row'] + 1}) by queue precedence."
        )
        if tie_count:
            why += f" Broke tie by row order (row {winner['row'] + 1} chosen)."
        return {
            "blocked": False,
            "queue": winner["queue"],
            "row": winner["row"],
            "item": winner["item"],
            "why": why,
            "explanations": explanations,
        }

    def plan_task(self, result):
        if result.get("blocked"):
            return {
                "plan": "Blocked: " + result["reason"],
                "why": result.get("explanations", []),
                "task": None,
                "blocked": True,
            }
        item = result["item"]
        row = item.get("_raw", item)
        queue = result["queue"]
        ident = (
            row.get("event_name")
            or row.get("fixture_id")
            or row.get("fighter_id")
            or row.get("event_batch")
            or "?"
        )
        if queue.startswith("fixture_gap"):
            task_type = "fixture_gap_recheck"
        elif queue.startswith("event_coverage"):
            task_type = "event_decomposition"
        elif queue.startswith("fighter_gap"):
            if (
                row.get("task_type") == "fighter_gap_real_grounding"
                or queue == "fighter_gap_queue.csv"
            ):
                task_type = "fighter_gap_real_grounding"
            else:
                task_type = "fighter_gap_grounding"
        elif queue.startswith("event_batch"):
            task_type = "event_batch_intake"
        else:
            task_type = "unknown"
        return {
            "plan": f"Next task from {queue}: {ident}",
            "why": [result["why"]] + result.get("explanations", []),
            "task": dict(row, task_type=task_type),
            "queue": queue,
            "identifier": ident,
            "row": result["row"],
            "blocked": False,
        }

    def execute_task(
        self,
        plan,
        reporter,
        queue_ack_fn=None,
        simulate_artifact_fail=False,
        simulate_queue_ack_fail=False,
    ):
        import os
        from handlers import registry
        if os.environ.get("AI_RISA_SIM_ARTIFACT_FAIL", "0") == "1":
            simulate_artifact_fail = True
        if os.environ.get("AI_RISA_SIM_QUEUE_ACK_FAIL", "0") == "1":
            simulate_queue_ack_fail = True
        task = plan.get("task", {}) or {}
        task_type = task.get("task_type")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Delegate to handler registry for supported types
        handler = registry.get_handler(task_type)
        if handler is not None:
            return handler.run(
                plan,
                reporter,
                base_dir,
                simulate_artifact_fail=simulate_artifact_fail,
                simulate_queue_ack_fail=simulate_queue_ack_fail,
                queue_ack_fn=queue_ack_fn,
            )
        # Fallback: legacy logic for other types
        reporter.report_execute_blocked(plan)
        return {"result": "blocked"}

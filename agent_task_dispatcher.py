class AgentTaskDispatcher:
    def select_next_task(self, queues):
        # Priority: ranked fixture > ranked fighter > intake unresolved > event > fixture > fighter
        for key in [
            "fixture_gap_queue_ranked.csv",
            "fighter_gap_queue_ranked.csv",
            "fighter_intake_unresolved_queue.csv",
            "event_coverage_queue.csv",
            "fixture_gap_queue.csv",
            "fighter_gap_queue.csv"
        ]:
            queue = queues.get(key, {})
            for item in queue.get("rows", []):
                if not item.get("active") or item["active"].lower() != "true":
                    return {"queue": key, "item": item}
        return None

    def plan_task(self, task):
        if not task:
            return {"plan": "No active tasks found.", "task": None}
        return {
            "plan": f"Next task from {task['queue']}: {task['item']}",
            "task": task
        }

    def execute_task(self, task):
        # Placeholder for safe execution logic
        if not task:
            return {"result": "No task to execute."}
        # Only dry-run for now
        return {"result": f"Would execute task from {task['queue']} (dry-run)", "task": task}

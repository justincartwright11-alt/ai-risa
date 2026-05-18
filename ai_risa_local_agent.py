import argparse
from agent_queue_reader import AgentQueueReader
from agent_task_dispatcher import AgentTaskDispatcher
from agent_reporter import AgentReporter


def main():
    parser = argparse.ArgumentParser(description="Local AI-RISA Operator Agent")
    parser.add_argument("--plan", action="store_true", help="Plan next action without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the next bounded task")
    args = parser.parse_args()

    queue_reader = AgentQueueReader()
    task_dispatcher = AgentTaskDispatcher()
    reporter = AgentReporter()

    # TRACE: Queue load result for event_coverage_queue.csv
    queues = queue_reader.read_all_queues()
    event_rows = queues.get("event_coverage_queue.csv", {}).get("rows", [])
    print(f"[TRACE] event_coverage_queue.csv loaded: {len(event_rows)} rows")
    if event_rows:
        print(f"[TRACE] First event row: {event_rows[0]}")

    # TRACE: Normalized row count for all queues
    for qf, qdata in queues.items():
        print(f"[TRACE] {qf}: {len(qdata.get('rows', []))} normalized rows")

    next_task = task_dispatcher.select_next_task(queues)
    print(f"[TRACE] Candidate selection result: {next_task}")
    plan = task_dispatcher.plan_task(next_task)
    print(f"[TRACE] Final plan object: {plan}")

    reporter.report_plan(plan)

    if plan.get("blocked") or (isinstance(plan, dict) and plan.get("plan", "").startswith("Blocked")):
        print("[TRACE] [BLOCKED] No valid active tasks found (plan/selection path)")

    if args.execute:
        result = task_dispatcher.execute_task(next_task)
        reporter.report_execution(result)
    else:
        reporter.report_dry_run()

if __name__ == "__main__":
    main()

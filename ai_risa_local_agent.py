import argparse
from agent_queue_reader import AgentQueueReader
from agent_task_dispatcher import AgentTaskDispatcher
from agent_reporter import AgentReporter




import os

def main():
    parser = argparse.ArgumentParser(description="Local AI-RISA Operator Agent")
    parser.add_argument("--plan", action="store_true", help="Plan next action without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the next bounded task (fixture-gap recheck only)")
    args = parser.parse_args()

    queue_reader = AgentQueueReader()
    task_dispatcher = AgentTaskDispatcher()
    reporter = AgentReporter()

    queues = queue_reader.read_all_queues(debug=True if args.plan or args.execute else False)
    next_task = task_dispatcher.select_next_task(queues, debug=True if args.plan or args.execute else False)
    plan = task_dispatcher.plan_task(next_task)

    reporter.report_plan(plan)

    if args.execute:
        if plan.get("blocked"):
            print("[ERROR] No executable task: Blocked state.")
            return
        # Allow all supported bounded tasks (fixture_gap_recheck, fighter_gap_grounding, event_decomposition)
        supported = plan.get("task", {}).get("task_type") in ("fixture_gap_recheck", "fighter_gap_grounding", "event_decomposition")
        if not supported:
            reporter.report_execute_blocked(plan)
            return
            if plan and plan.get("task") and plan["task"].get("queue") in [
                "fixture_gap_queue_ranked.csv",
                "fighter_gap_queue_ranked.csv",
                "event_coverage_queue.csv",
                "fixture_gap_queue.csv",
                "fighter_gap_queue.csv"
            ]:
                result = dispatcher.execute_task(plan["task"])
                print("[EXECUTE RESULT]", result)
                # After successful execution, mark the queue row as completed
                queue_file = plan["task"]["queue"]
                item = plan["task"]["item"]
                # Determine the match field for the queue
                if "fixture_id" in item:
                    match_field = "fixture_id"
                    match_value = item["fixture_id"]
                elif "fighter_id" in item:
                    match_field = "fighter_id"
                    match_value = item["fighter_id"]
                elif "event_name" in item:
                    match_field = "event_name"
                    match_value = item["event_name"]
                else:
                    match_field = None
                    match_value = None
                if match_field and match_value:
                    success, error = queue_reader.mark_row_completed(queue_file, match_field, match_value)
                    if success:
                        print(f"[QUEUE ACK] Marked {queue_file} row {match_field}={match_value} as completed.")
                    else:
                        print(f"[QUEUE ACK ERROR] {error}")
                else:
                    print(f"[QUEUE ACK ERROR] Could not determine match field for queue {queue_file}.")
    else:
        reporter.report_dry_run()

if __name__ == "__main__":
    main()

import argparse
from agent_queue_reader import AgentQueueReader
from agent_task_dispatcher import AgentTaskDispatcher
from agent_reporter import AgentReporter




import os

def main():
    parser = argparse.ArgumentParser(description="Local AI-RISA Operator Agent")
    parser.add_argument("--plan", action="store_true", help="Plan next action without executing")
    parser.add_argument("--execute", action="store_true", help="Execute the next bounded task (fixture-gap recheck, fighter-gap real grounding, or event decomposition)")
    args = parser.parse_args()

    queue_reader = AgentQueueReader()
    task_dispatcher = AgentTaskDispatcher()
    reporter = AgentReporter()

    queues = queue_reader.read_all_queues(debug=True if args.plan or args.execute else False)
    next_task = task_dispatcher.select_next_task(queues, debug=True if args.plan or args.execute else False)
    plan = task_dispatcher.plan_task(next_task)
    reporter.report_plan(plan)

    # (Diagnostics removed)
    if args.execute:
        if plan.get("blocked"):
            print("[ERROR] No executable task: Blocked state.")
            return
        supported = plan.get("task", {}).get("task_type") in (
            "fixture_gap_recheck", "fighter_gap_grounding", "fighter_gap_real_grounding", "event_decomposition", "event_batch_intake"
        )
        if not supported:
            reporter.report_execute_blocked(plan)
            return
        simulate_artifact_fail = os.environ.get("AI_RISA_SIM_ARTIFACT_FAIL", "0") == "1"
        simulate_queue_ack_fail = os.environ.get("AI_RISA_SIM_QUEUE_ACK_FAIL", "0") == "1"
        def queue_ack_fn():
            queue_file = plan["queue"]
            item = plan["task"]
            if queue_file == "event_batch_queue.csv" and "event_batch" in item:
                match_field = "event_batch"
                match_value = item["event_batch"]
            elif "fixture_id" in item:
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
                return queue_reader.mark_row_completed(queue_file, match_field, match_value)
            else:
                return False, f"Could not determine match field for queue {queue_file}."
        dispatcher = task_dispatcher
        dispatcher.execute_task(plan, reporter, queue_ack_fn=queue_ack_fn, simulate_artifact_fail=simulate_artifact_fail, simulate_queue_ack_fail=simulate_queue_ack_fail)
    else:
        reporter.report_dry_run()

if __name__ == "__main__":
    main()

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
        task_dispatcher.execute_task(plan, reporter)
    else:
        reporter.report_dry_run()

if __name__ == "__main__":
    main()


class AgentReporter:
    def report_plan(self, plan):
        print("=== AI-RISA Local Agent Plan ===")
        print(plan["plan"])
        if plan.get("blocked"):
            print("[BLOCKED]")
            for why in plan.get("why", []):
                print("-", why)
            print()
            print("Execution supported: No (blocked)")
            return
        print(f"Task type: {self._task_type(plan)}")
        print(f"Source queue: {plan.get('queue', '?')}")
        print(f"Identifier: {plan.get('identifier', '?')}")
        for why in plan.get("why", []):
            print("Reason:", why)
        print(f"Execution supported: {'No (stub only)' if plan.get('blocked') else 'Yes (stub only)'}")
        print()

    def _task_type(self, plan):
        if plan.get('queue', '').startswith('event_'):
            return 'event'
        if plan.get('queue', '').startswith('fixture_'):
            return 'fixture-gap'
        if plan.get('queue', '').startswith('fighter_'):
            return 'fighter-gap'
        return 'unknown'

    def report_dry_run(self):
        print("(Dry run: no files changed, no actions executed)")

    def report_execute_stub(self):
        print("(Execute mode is a stub. No actions performed.)")

    def report_execute_blocked(self, plan):
        print("[EXECUTE BLOCKED]")
        print("Execution refused: Only fixture-gap recheck is supported in this pass.")
        print(f"Selected task type: {plan.get('task', {}).get('task_type', '?')}")
        print()
        print("Files changed: none")
        print("Commands run: none")
        print("Validation result: execute blocked (unsupported task type)")
        print("Remaining risks: none (guarded)")

    def report_execute_success(self, files_changed, plan=None):
        print("[EXECUTE SUCCESS]")
        print(f"Files changed: {', '.join(files_changed)}")
        print("Commands run: python ai_risa_local_agent.py --execute")
        # Task-specific validation result
        task_type = None
        if plan and isinstance(plan, dict):
            task_type = plan.get("task", {}).get("task_type")
        if task_type == "fighter_gap_grounding":
            print("Validation result: fighter-gap grounding artifact written deterministically")
        elif task_type == "fixture_gap_recheck":
            print("Validation result: fixture-gap recheck artifact written deterministically")
        else:
            print("Validation result: artifact written deterministically")
        print("Remaining risks: none (bounded workflow)")

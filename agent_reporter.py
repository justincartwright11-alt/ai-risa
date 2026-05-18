class AgentReporter:
    def report_plan(self, plan):
        print("=== AI-RISA Local Agent Plan ===")
        print(plan["plan"])
        print()

    def report_execution(self, result):
        print("=== Execution Result ===")
        print(result["result"])
        print()

    def report_dry_run(self):
        print("(Dry run: no files changed, no actions executed)")

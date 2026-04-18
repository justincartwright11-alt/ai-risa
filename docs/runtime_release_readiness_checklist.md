# Runtime Release Readiness Checklist

## 1. Frozen Baseline Inventory
- Three-lane governed pack stack (all core packs)
- Runtime orchestrator (frozen)
- Runtime dispatch adapter (frozen)
- Operator runtime entrypoint (frozen)
- Operator runtime usage contract (docs/operator_runtime_usage_contract.md)
- Operator runtime quickstart (docs/operator_runtime_quickstart.md)
- All tests and acceptance fixtures

## 2. Required Validation Gates Before Release
- All unit tests must pass (no failures or skips)
- All operator acceptance tests must pass
- All regression fixtures must pass
- No uncommitted changes in workflows, tests, or docs

## 3. Required Branch/Tag/Freeze Checks
- Current branch is a frozen baseline (e.g., baseline/operator-runtime-entrypoint-v1)
- All relevant tags applied (e.g., operator-runtime-entrypoint-v1)
- No untagged or unreviewed commits after the last freeze

## 4. Required Regression/Acceptance Checks
- Run:
  - python -m unittest tests/test_operator_runtime_entrypoint.py
  - python -m unittest tests/test_runtime_dispatch_adapter.py
  - python -m unittest tests/test_runtime_orchestrator.py
  - python .\tests\operator_acceptance.py
- Confirm: "SUCCESS: All golden regression fixtures passed."

## 5. Required Documentation Checks
- docs/operator_runtime_usage_contract.md is present and matches implementation
- docs/operator_runtime_quickstart.md is present and matches implementation
- No speculative or undocumented features in docs

## 6. Release Signoff Checklist
- [ ] All validation gates green
- [ ] All documentation present and correct
- [ ] All branches/tags frozen and reviewed
- [ ] No uncommitted changes
- [ ] Operator acceptance confirmed
- [ ] Release package assembled (if required)

## 7. Rollback/Readiness Notes
- If any validation or acceptance test fails, do not release
- Roll back to last known good frozen tag if needed
- Never patch frozen layers without a new branch/tag and full validation

## 8. Known Non-Goals and Boundaries
- No new runtime logic or orchestration in this release
- No changes to frozen pack, orchestrator, adapter, or entrypoint contracts
- No speculative features or out-of-band overrides
- This checklist applies only to the current frozen operator runtime baseline

# Runtime Release Manifest / Handoff Note

## Release Overview
This document serves as the authoritative handoff for the frozen, validated, and documented operator runtime baseline. It inventories all frozen branches, tags, documentation, validation gates, and the approved runtime execution surface.

## 1. Frozen Branches and Tags
- **Three-lane governed pack stack:**
  - Branch: `baseline/three-lane-governed-pack-stack`
- **Runtime orchestrator:**
  - Branch: `baseline/runtime-orchestrator-v1`
  - Tag: `runtime-orchestrator-v1`
- **Runtime dispatch adapter:**
  - Branch: `baseline/runtime-dispatch-adapter-v1`
  - Tag: `runtime-dispatch-adapter-v1`
- **Operator runtime entrypoint:**
  - Branch: `baseline/operator-runtime-entrypoint-v1`
  - Tag: `operator-runtime-entrypoint-v1`

## 2. Operator-Facing Documentation
- `docs/operator_runtime_usage_contract.md`
- `docs/operator_runtime_quickstart.md`
- `docs/operator_runtime_runbook.md`
- `docs/runtime_release_readiness_checklist.md`
- `docs/runtime_release_manifest.md` (this file)

## 3. Validation Gates
- All unit tests, regression, and operator acceptance tests must pass:
  - `python -m unittest tests/test_operator_runtime_entrypoint.py`
  - `python -m unittest tests/test_runtime_dispatch_adapter.py`
  - `python -m unittest tests/test_runtime_orchestrator.py`
  - `python .\tests\operator_acceptance.py`
- Final acceptance: `SUCCESS: All golden regression fixtures passed.`

## 4. Approved Runtime Surface
- `workflows/operator_runtime_entrypoint.py`
- `workflows/runtime_dispatch_adapter.py`
- `workflows/runtime_orchestrator.py`
- All frozen pack implementations

## 5. Release Signoff
- Implementation frozen and validated
- Operator contract and quickstart documented
- Release readiness checklist completed
- Operator runbook completed
- No remaining risks

## 6. Handoff Instructions
- Use only the documented branches, tags, and canonical docs for operator use and release.
- Any future changes must branch from this baseline and repeat full validation and documentation.
- This manifest is the single source of truth for the current operator runtime release.

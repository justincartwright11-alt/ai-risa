# AI-RISA Operator Acceptance Harness Runbook

## Purpose

The operator acceptance harness provides a single-command, automated gate for all operator-layer changes. It ensures that core execution and retry logic are validated before any code is accepted.

## How to Run

```
python tests/operator_acceptance.py
```

## What It Validates

- Success path: operator completes a normal task and marks it completed
- Artifact-failure retry to blocked: operator retries artifact failures, blocks after 3 attempts
- Queue-ack partial-success retry to blocked: operator retries queue-ack failures, blocks after 3 attempts
- Deterministic artifact filename behavior: artifact filenames are consistent and not duplicated across retries

## Pass/Fail Interpretation

- **PASS:** All scenarios complete with expected state transitions and outputs. The operator is safe to change or deploy.
- **FAIL:** Any assertion failure, mismatch, or traceback means the operator logic is invalid. No operator-layer change is valid unless this harness passes.

## Required Rule

No operator-layer change is considered valid unless `python tests/operator_acceptance.py` passes cleanly.

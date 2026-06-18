# Button 1 Approved Provider Registry Example — Doc and Smoke Note v1

Slice: button1-current-week-approved-provider-registry-example-doc-and-smoke-note-v1
Date: 2026-06-18

## Purpose

This note records why the example provider registry file is intentionally non-runtime and why Button 1 runtime remains fail-closed.

## Runtime Target (Unchanged)

The runtime preview loader targets exactly one file path:

- ops/approved_sources/button1_live_provider_registry.json

This runtime path remains absent in the current environment.

## Example File (Non-Runtime by Design)

The example file created in the prior slice is separate from runtime:

- ops/approved_sources/button1_live_provider_registry.example.disabled.v1.json

This file is intentionally documentation/example-only and disabled by default.

Key intent signals in the example file:
- example_only: true
- runtime_load_allowed: false
- disabled_by_default: true
- operator_approval_required: true
- execution_mode: preview_only
- providers[].enabled: false

Because runtime reads only the exact runtime filename above, the example file is not consumed by runtime execution paths.

## Smoke Verification (Accepted)

Runtime preview still returns fail-closed status:
- diagnostics=provider_config_missing
- provider_execution_performed=False
- network_calls_performed=False
- queue_write_performed=False
- database_write_performed=False

This confirms the example file does not trigger provider execution, source calls, queue writes, or database writes.

## Governance Boundary (Unchanged)

Not implemented in this slice:
- Provider execution
- Auto-discovery
- Queue persistence
- Customer report generation

No code-path expansion occurred:
- Runtime code changed: false
- UI code changed: false
- Button 2 unaffected
- Button 3 unaffected

## Conclusion

The example provider registry file is intentionally non-runtime and operator-gated.
The real runtime path remains absent, so the system correctly stays fail-closed.

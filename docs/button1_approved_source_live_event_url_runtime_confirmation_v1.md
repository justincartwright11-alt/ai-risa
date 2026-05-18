# Button1 Approved Source Live Event URL Runtime Confirmation v1

## Slice
button1-approved-source-live-event-url-runtime-confirmation-v1

## Checkpoint Under Confirmation
- Source ingestion slice commit: `773c3df`
- Source ingestion slice tag: `button1-approved-source-live-event-url-ingestion-v1`

## Confirmation Goal
Prove, on the live dashboard/runtime path, that Button 1 now:
- sees approved-source URL-backed candidates from governed feed artifacts,
- shows non-zero source-backed readiness,
- produces non-zero Gate 1 would-save for valid URL-backed rows,
- still blocks non-URL rows (fail-closed),
- preserves strict approval-gated behavior.

## Runtime Input Used (Governed Feed Artifact)
Created governed approved-source feed artifact:
- `ops/approved_sources/button1_live_event_source_rows.json`

Feed row used:
- `event_name`: `ONE SAMURAI 1`
- `event_url`: `https://www.onefc.com/events/`
- `source_name`: `one_championship_official`
- `source_type`: `official`

## Live Runtime Evidence
### 1) Actual dashboard hydration state (shared page runtime)
From live page `http://127.0.0.1:5050/` after reload:
- Button 1 card:
  - Ready to save: `32`
  - Needs review: `0`
  - Blocked: `0`
  - Waiting for refresh: `0`

Interpretation:
- Runtime Button 1 now surfaces non-zero source-backed readiness in the actual dashboard path.

### 2) Runtime route proof (`use_runtime_context=true`)
Executed runtime route probe:
- `POST /api/local-ai/orchestrator/workflow-preview`
- `POST /api/local-ai/gate1/save-fights/dry-run-apply-preview`

Observed baseline with current runtime rows:
- candidate_rows: `32`
- live_source_status.approved_source_event_rows_count: `1`
- live_source_status.diagnostics: `[]`
- dry-run would_save_count: `32`
- dry-run blocked_count: `0`

Interpretation:
- Approved-source event feed is recognized in runtime.
- URL-backed candidates are now save-eligible under unchanged Gate 1 checks.

### 3) Fail-closed non-URL blocking proof
In the same runtime run, added one explicit non-URL control row (`non_url_control_001`) and re-ran dry-run:
- Baseline:
  - would_save_count: `32`
  - blocked_count: `0`
- Mixed (baseline + non-URL control):
  - would_save_count: `32`
  - blocked_count: `1`
  - `non_url_control_001` in blocked: `true`
  - `non_url_control_001` in would_save: `false`

Interpretation:
- Non-URL row remains fail-closed blocked.
- URL-backed rows remain eligible.

## Governance Confirmation
- Gate 1 strictness preserved.
- No fake URLs used.
- No synthetic official provenance generated.
- No automatic queue save/write performed.
- Operator approval requirement remains intact.
- Paid-pilot GO/NO-GO remains paused until this confirmation lock is recorded.

## Verdict
`button1-approved-source-live-event-url-runtime-confirmation-v1` passed.

Button 1 runtime now demonstrates approved-source URL-backed readiness and selective Gate 1 behavior:
- URL-backed candidates: eligible (`would_save > 0`).
- Non-URL candidates: blocked.

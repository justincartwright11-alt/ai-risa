# Button1 Source-Backed Candidate Runtime Confirmation v1

## Slice
button1-source-backed-candidate-runtime-confirmation-v1

## Checkpoint Under Confirmation
- Source commit: `fd4412a`
- Source tag: `button1-source-backed-candidate-ingestion-and-provenance-population-v1`

## Confirmation Goal
Prove runtime behavior for Button 1 candidate save-eligibility after ingestion/provenance population lock:
- URL-backed candidate rows can produce non-zero `would_save`.
- Non-URL rows remain blocked.
- Existing baseline runtime cohort with no URL evidence remains fully blocked.

## Runtime Probe Method
Executed a runtime confirmation probe through preview route stack:
- `POST /api/local-ai/orchestrator/workflow-preview`
- `POST /api/local-ai/gate1/save-fights/dry-run-apply-preview`

Probe command:

```bash
@'
# python snippet executed via configured runtime
'@ | C:/Users/jusin/AppData/Local/Python/pythoncore-3.14-64/python.exe -
```

The probe performed two checks in one run:
1. Baseline runtime input (`use_runtime_context=true`) from current workspace data.
2. Mixed runtime input (`context_pack`) containing:
   - one real event URL evidence row: `https://www.ufc.com/event/ufc-300`
   - one local candidate matching that event name
   - one local candidate with no URL evidence

## Live Confirmation Evidence
### 1) Baseline runtime cohort unchanged and strict
- candidate_rows: `31`
- would_save: `0`
- blocked: `31`

Interpretation:
- Existing non-URL cohort remains fail-closed.

### 2) Mixed runtime input produces selective non-zero would-save
- candidate_rows: `3`
- would_save: `["url_backed_001"]`
- blocked: `["no_url_001"]`

Observed row-level behavior:
- `url_backed_001` inherited event-level URL provenance from matching event name (`UFC 300`) and became save-eligible.
- `no_url_001` remained blocked because no accepted URL provenance fields were present.

Interpretation:
- Non-zero `would_save` appears only for URL-backed candidate evidence.
- Non-URL rows remain blocked as required.

## Governance Statement
This is runtime confirmation only.
- No queue/database writes authorized.
- No customer report export authorized.
- No learning/calibration writes authorized.
- Gate 1 logic remained unchanged and strict.

## Verdict
`button1-source-backed-candidate-runtime-confirmation-v1` passed.

The runtime now demonstrates governed selective eligibility:
- URL-backed candidates can move to `would_save`.
- Non-URL candidates remain blocked.
- Baseline no-URL cohort stays fully blocked.

Paid-pilot GO/NO-GO remains paused pending your explicit management decision to resume.

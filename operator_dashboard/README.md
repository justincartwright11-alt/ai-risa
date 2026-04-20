# AI-RISA v40 Release-Hardening README (Operator Quickstart)

## Operator Dashboard Release-Hardening (Build 23, v40)

### Endpoints
See ENDPOINT_INVENTORY.md for full route list and contract shapes.

### Chat Commands
See CHAT_COMMAND_INVENTORY.md for all supported commands and aliases.

### UTC/Deprecation
All UTC handling is contract-safe and deterministic. No deprecated datetime.utcnow() usage remains.

### How to Validate (Acceptance Sequence)

```bash
cd C:\ai_risa_data
$env:PYTHONPATH = "C:\ai_risa_data;C:\ai_risa_data\operator_dashboard"

python -m unittest operator_dashboard.test_chat_contract
python -m unittest operator_dashboard.test_chat_status
python -m unittest operator_dashboard.test_queue_status
python -m unittest operator_dashboard.test_queue_actions
python -m unittest operator_dashboard.test_queue_readonly
python -m unittest operator_dashboard.test_event_evidence
python -m unittest operator_dashboard.test_event_comparison
python -m unittest operator_dashboard.test_event_timeline
python -m unittest operator_dashboard.test_event_anomalies
python -m unittest operator_dashboard.test_event_watchlist
python -m unittest operator_dashboard.test_event_digest
python -m unittest operator_dashboard.test_event_escalation
python -m unittest operator_dashboard.test_event_review_queue
python -m unittest operator_dashboard.test_event_briefing
python -m unittest operator_dashboard.test_event_casefile
python -m unittest operator_dashboard.test_event_portfolio
python -m unittest operator_dashboard.test_control_summary
python -m unittest operator_dashboard.test_integrity
python -m unittest operator_dashboard.test_drift
python -m unittest operator_dashboard.test_forecast
python -m unittest operator_dashboard.test_response_matrix

cd C:\ai_risa_data\operator_dashboard
python verify_chat.py
```

### Final Smoke Pass
- Run all top-level endpoints and chat commands
- Confirm no mutation, execution, or background behavior
- Confirm all contract shapes and deterministic outputs

### Release Readiness
- All endpoints and chat commands are stable, deterministic, and contract-compliant
- No mutation/execution surfaces
- All changes are regression-safe and evidence-based
- Ready for final runtime smoke sweep
## Operator Response Matrix / Playbook (Build 23)

The dashboard now supports a deterministic, read-only operator response matrix / playbook view:

- Aggregates prioritized operator inspection paths from all backend signals
- Ranks top issue, why it matters, and recommended inspection surfaces
- Summarizes stabilizing and worsening signals
- Zero mutation or execution path

### Endpoints
- `GET /api/response-matrix` — deterministic response matrix index (read-only)

### UI Controls
- Compact response matrix/playbook panel near forecast, drift, and integrity
- Shows matrix status, top issue, why it matters, first/second/third surfaces, top recommended paths, trend summary, and recommendation
- Refresh button to re-fetch backend truth

### Chat Commands
- show response matrix
- operator playbook
- what should i inspect
- where do i look first
- what is the best inspection path
- what should i check next

All outputs are deterministic, local, and safe.
## Event Drilldown and Safe Artifact Opening (Build 7)

The dashboard now supports safe, allowlisted queue-side operator actions:

- Inspect any event in the queue (via UI or chat)
- Open the queue file (UI or chat)
- Open an event artifact (UI or chat, only if safe and present)
- Show next, show blocked, show queued, show in progress, show completed events
- Refresh queue

### Endpoints
- `GET /api/queue/event/<event_id>` — deterministic event drilldown (read-only)
- `POST /api/queue/event/<event_id>/open_artifact` — open artifact if and only if path is safe and exists

### Safety Model
- All event_id lookups resolve only against parsed queue rows
- Artifact opening is allowed only if the path is under an approved project root and allowed directory, and the file exists
- No arbitrary path or subprocess execution is possible from user input
- All actions are strictly allowlisted and read-only

### UI Controls
- Compact controls for refresh, show next, show blocked
- Click any event row to inspect details
- Open artifact button appears only if artifact is present and safe

### Chat Commands
- refresh queue
- open queue file
- inspect event <event_id>
- open event artifact <event_id>

All actions are deterministic, local, and safe.
## Event Coverage Queue (Build 6)

## Operator Anomaly Triage (Build 11)

The dashboard now supports deterministic, read-only anomaly triage:

- Aggregates highest-risk mismatches across queue, evidence, comparison, and timeline layers
- Deterministic severity and ranking
- Zero mutation or execution path

### Endpoints
- `GET /api/anomalies` — deterministic anomaly aggregation (read-only)
- `GET /api/forecast` — deterministic operator forecast / early-warning (read-only)
## Operator Forecast / Early Warning (Build 22)

The dashboard now supports a deterministic, read-only operator forecast / early-warning view:

- Aggregates near-term risk from drift, integrity, control summary, and portfolio signals
- Deterministic risk band and early warning synthesis
- Zero mutation or execution path

### Endpoints
- `GET /api/forecast` — deterministic forecast index (read-only)

### UI Controls
- Compact forecast/early-warning panel near control summary/integrity/drift
- Shows forecast status, projected risk bands, early warning items, urgent event forecast, and recommendation
- Refresh button to re-fetch backend truth

### Chat Commands
- show forecast
- operator forecast
- show early warning
- what is likely next
- what should i watch next
- what could go wrong soon

All actions are deterministic, local, and safe.

### UI Controls
- Anomaly panel: shows highest-risk anomalies, severity, and event context
- Refresh anomalies button

### Chat Commands
- show anomalies
- anomaly triage
- show anomaly triage
- show operator anomalies
- triage anomalies

All actions are deterministic, local, and safe.

The dashboard is now queue-aware. The backend exposes:

- `GET /api/queue` — deterministic, read-only snapshot of the event coverage queue (`event_coverage_queue.csv`).
   - Returns: ok, timestamp, queue_file_present, total_rows, queued_count, in_progress_count, blocked_count, complete_count, rows (safe fields only)
   - Robust to missing/malformed files
- `GET /api/queue/recommendation` — deterministic next-action recommendation based on queue state

The dashboard UI shows a compact queue panel with counts, recent events, and recommended next action. The panel fetches backend truth only and degrades safely if unavailable.

## Queue-Aware Chat (Build 6)

The chat now understands:
- show queue
- show blocked events
- show queued events
- show in progress events
- show completed events
- what is next / next event

These commands return safe summaries from the queue. No raw CSV access or direct execution is allowed.

## Deterministic Recommendation

The dashboard and chat use a deterministic recommendation layer to suggest the next valid action based on queue state. If blocked rows exist, they are listed with reasons. If queued rows exist, the first eligible event is identified. If the queue is empty or missing, this is surfaced safely.

## Operator Guidance: Dynamic Port

The dashboard binds to the first available port from 5000 upward. Always check the console output for the correct URL (e.g., `http://127.0.0.1:5000`, `http://127.0.0.1:5001`, etc.). Do not assume port 5000 is always used.
## Operator Action Ledger

All operator actions are recorded in an append-only ledger at:

   action_ledger.jsonl

Each entry includes: timestamp, action, normalized event, user message, outcome status (started/succeeded/failed/clarification), response, error, details summary, and a correlation ID. Every chat action writes both a 'started' and a final outcome row.

## /api/status Endpoint

The dashboard exposes a local-only status endpoint at:

   GET /api/status

Returns a JSON object with:

- last_action
- last_normalized_event
- last_outcome_status
- total_logged_actions
- total_chat_messages
- last_success_timestamp
- last_failure_timestamp
- queue/log/manifest/go-no-go presence
- errors (if any)

## Status Panel (Build 5)

The dashboard UI includes a compact status panel (top section) that fetches backend truth from /api/status. It displays:

- Last action, event, outcome
- Total actions, total chat
- Last success/failure timestamps
- Presence of queue, log, manifest, go/no-go files
- A refresh button to re-fetch status

The panel loads on page open and degrades safely if the backend is unavailable. No values are inferred locally.

## Build 5 Local-Only Safety Model

- All actions are strictly allowlisted and routed through a central dispatcher
- No raw user input is ever executed
- No remote APIs, schedulers, or model calls
- All persistence is local (JSON/CSV/JSONL)
- The ledger and status panel provide full operator auditability
## Persistent Chat History

The dashboard chat now stores the last 200 messages in `chat_history.json` and restores them on page refresh. Each message includes role, content, timestamp, action, normalized event, and error fields. Malformed or missing history files are handled safely.

## Chat Response Contract

All `/chat/send` responses follow this contract:

| Field            | Type    | Description                                 |
|------------------|---------|---------------------------------------------|
| ok               | bool    | True if action succeeded                    |
| action           | string  | Normalized action name                      |
| response         | string  | Main assistant reply                        |
| normalized_event | string? | Normalized event name (if applicable)       |
| details          | string  | Additional details (if any)                 |
| error            | string? | Error message (if any)                      |
| timestamp        | string  | ISO timestamp (UTC)                         |

## Operator Safety

All backend actions are strictly allowlisted and routed through a central dispatcher. No raw user input is ever executed. Unclear input always returns a safe clarification.
## Natural-Language Chat Examples

The dashboard chat supports plain-English requests. Polite/filler words like "please", "now", "tonight", "can you", etc. are ignored for event normalization.

**Examples:**

| Input                                              | Normalized Event Name         |
|----------------------------------------------------|------------------------------|
| run Song vs Figueiredo tonight                     | song_vs_figueiredo           |
| please run Prochazka vs Ulberg now                 | prochazka_vs_ulberg          |
| can you run Nikita Tszyu vs Oscar Diaz for me      | nikita_tszyu_vs_oscar_diaz   |
| would you run Song vs Figueiredo                   | song_vs_figueiredo           |
| just run Prochazka vs Ulberg quickly               | prochazka_vs_ulberg          |
| I want to run Song vs Figueiredo                   | song_vs_figueiredo           |
| can you please run Song vs Figueiredo right now    | song_vs_figueiredo           |
| validate system                                    | (runs validation)            |
| help                                              | (shows help)                 |

If the input is unclear, the assistant will ask for clarification and show examples.
## Overview
A simple local dashboard for running the AI-RISA local agent and operator workflows without using raw terminal commands.

## Features
- Chat with Local AI: type plain-English requests, get results in a chat window
- Run Local AI with validated request shapes (accepted, blocked, failed_precondition)
- Run Acceptance Test
- Open Queue File, Live Release Log, Runtime Manifest, Go/No-Go Note
- View results and status in a browser UI

## Requirements
- Python 3.8+
- Flask (`pip install flask`)


## Quick Start
1. Double-click `start_operator_dashboard.bat` in the `C:\ai_risa_data` folder.
   - This will start the dashboard and open your browser automatically.
   - The console will print diagnostics: host, port, final URL, and browser open status.
2. If you prefer the command line:
   - Open PowerShell or Command Prompt.
   - Run:
     ```
     cd C:\ai_risa_data
     python operator_dashboard\app.py
     ```
   - The console will print the exact URL to open.
3. The dashboard will open at a link like:
   - [http://127.0.0.1:5000](http://127.0.0.1:5000)
   - If port 5000 is busy, it will use the next available port (e.g., [http://127.0.0.1:5001](http://127.0.0.1:5001)) and print the correct link.

## If you see "Connection Refused"
- Make sure the dashboard window is open and running (do not close it).
- Wait for the diagnostics: host, port, and final URL.
- Open the printed URL in your browser (e.g., `http://127.0.0.1:5000`).
- If you see an error about port 5000 being in use, the dashboard will try the next port and print the correct link (e.g., `http://127.0.0.1:5001`).
- If nothing appears, check for errors in the window and ensure Python and Flask are installed.

## If port 5000 is busy
- The dashboard will try ports 5000-5009 automatically.
- The correct link will be printed in the window (e.g., `http://127.0.0.1:5001`).
- Open that link in your browser.
## How to test if the server is listening

Open a second PowerShell window and run:

```
netstat -ano | findstr :5000
```

- If you see `LISTENING` on `127.0.0.1:5000` or `0.0.0.0:5000`, the server is running.
- If you see nothing, the dashboard is not running or crashed.

You can also test directly with:

```
Invoke-WebRequest http://127.0.0.1:5000
```

- If it returns HTML/status 200, the server is up.
- If it errors with connection refused, the server is not running.


## Chat Usage
- Type a request in the chat box and hit Send. Supported commands (natural language accepted):
   - run <event_name>
   - validate system
   - open queue
   - open live log
   - open manifest
   - open go no go note
   - help

### Natural-language examples
   - run Song vs Figueiredo tonight
   - please run Prochazka vs Ulberg
   - can you validate the system for me
   - open the live log
   - what can I say

## Button Usage
- You can still use the action buttons for direct control.
- Results and status will be shown in the dashboard.

## Notes
- The dashboard does not modify any frozen runtime logic.
- All actions are wrappers around the approved runtime scripts and files.
- For any issues, check the terminal output for errors.

---

This dashboard is for local operator use only. No cloud or external dependencies.

## Operator Review Queue (Build 15)

The dashboard now supports a deterministic, read-only operator review queue:

- Aggregates review pressure from escalation, watchlist, digest, anomaly, timeline, queue, and ledger
- Deterministic review priority and ranking
- Zero mutation or execution path

### Endpoints
- `GET /api/review-queue` — deterministic review queue index (read-only)
- `GET /api/queue/event/<event_id>/review-queue` — deterministic event review queue drilldown (read-only)

### UI Controls
- Review queue panel: shows top review-priority events, reasons, and recommendations
- Refresh review queue button

### Chat Commands
- show review queue
- review queue view
- show top review queue
- what should i review next
- show review queue for <event_id>
- why is <event_id> in the review queue

All actions are deterministic, local, and safe.

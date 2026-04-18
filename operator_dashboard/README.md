# AI-RISA Local Operator Dashboard

## Overview
A simple local dashboard for running the AI-RISA local agent and operator workflows without using raw terminal commands.

## Features
- Run Local AI with validated request shapes (accepted, blocked, failed_precondition)
- Run Acceptance Test
- Open Queue File, Live Release Log, Runtime Manifest, Go/No-Go Note
- View results and status in a browser UI

## Requirements
- Python 3.8+
- Flask (`pip install flask`)

## Quick Start
1. Open a terminal in the `operator_dashboard` directory.
2. Install Flask if needed:
   ```
   pip install flask
   ```
3. Run the dashboard:
   ```
   python app.py
   ```
4. Open your browser to [http://localhost:5000](http://localhost:5000)

## Usage
- Select a request shape and click "Run Local AI" to execute the local agent.
- Use the action buttons to run acceptance tests or open key files.
- Results and status will be shown in the dashboard.

## Notes
- The dashboard does not modify any frozen runtime logic.
- All actions are wrappers around the approved runtime scripts and files.
- For any issues, check the terminal output for errors.

---

This dashboard is for local operator use only. No cloud or external dependencies.

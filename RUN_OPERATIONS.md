# AI-RISA Pipeline: Scheduled Execution Operations Guide

**Last Updated:** 2026-04-01  
**Target System:** Windows 10/11 with PowerShell 5.1+  
**Repository:** `C:\ai_risa_data`

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Initial Setup](#initial-setup)
4. [Task Management](#task-management)
5. [Verifying Execution](#verifying-execution)
6. [Troubleshooting](#troubleshooting)
7. [Retention Policy](#retention-policy)
8. [Rollback Procedures](#rollback-procedures)
9. [Quick Reference](#quick-reference)

---

## Overview

The AI-RISA pipeline scheduler provides:

- **Two automated modes:**
  - **Normal Run:** Full pipeline execution with report generation
  - **Dry-Run:** Safe verification without state changes
  
- **Timestamped run history:** Each execution stored in `C:\ai_risa_data\runs\YYYY-MM-DD_HHMMSS\`

- **Automatic retention:** Configurable pruning by age (days) and count

- **Run index:** JSON-based history for querying, auditing, and automation

- **Operator-minimal design:** All settings configurable, no hardcoded values

---

## Architecture

### Directory Structure

```
C:\ai_risa_data\
├── schedule_full_pipeline_run.ps1          # Normal run launcher
├── schedule_full_pipeline_dry_run.ps1      # Dry-run launcher
├── register_pipeline_tasks.ps1             # Task Scheduler manager
├── prune_run_history.py                    # Retention policy
├── RUN_OPERATIONS.md                       # This file
│
├── output/                                 # Current execution artifacts
│   ├── full_pipeline_run_summary.json
│   ├── upcoming_auto_summary.json
│   ├── dependency_resolution_summary.json
│   ├── prediction_queue_build_summary.json
│   ├── prediction_queue_run_summary.json
│   └── event_batch_run_summary.json
│
└── runs/                                   # Run history (timestamped)
    ├── run_history_index.json              # Master index (append-only)
    ├── 2026-03-31_143000/
    │   ├── launcher.log
    │   ├── full_pipeline_run_summary.json
    │   ├── upcoming_auto_summary.json
    │   ├── dependency_resolution_summary.json
    │   ├── prediction_queue_build_summary.json
    │   ├── prediction_queue_run_summary.json
    │   ├── upcoming_events_ingest_summary.json
    │   └── event_batch_run_summary.json
    │
    └── 2026-03-30_140000/
        └── (same structure)
```

### Scheduled Tasks

Two tasks are created in Windows Task Scheduler under `\AI-RISA\`:

| Task Name | Type | Default Time | Launcher | Dry-Run |
|-----------|------|--------------|----------|---------|
| AI-RISA-Pipeline-Normal-Run | Daily | 2:00 PM (14:00) | `schedule_full_pipeline_run.ps1` | N/A |
| AI-RISA-Pipeline-Dry-Run | Daily | 1:00 PM (13:00) | `schedule_full_pipeline_dry_run.ps1` | --dry-run |

---

## Initial Setup

### Prerequisites

- Windows 10/11 with Administrator access
- PowerShell 5.1 or later
- Python 3.7+ (must be in PATH or `%PYTHONPATH%`)
- Repository initialized at `C:\ai_risa_data`
- All pipeline scripts validated (compile gate passed)

### Step 1: Validate Repository

```powershell
# Verify all required files exist
Test-Path C:\ai_risa_data\run_full_pipeline_auto.py
Test-Path C:\ai_risa_data\schedule_full_pipeline_run.ps1
Test-Path C:\ai_risa_data\schedule_full_pipeline_dry_run.ps1
Test-Path C:\ai_risa_data\register_pipeline_tasks.ps1
Test-Path C:\ai_risa_data\prune_run_history.py

# Run manual compile gate (all should exit 0)
python -m py_compile C:\ai_risa_data\*.py
```

### Step 2: Register Scheduled Tasks

Open PowerShell **as Administrator** and run:

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Enable
```

**Output should show:**
```
=== AI-RISA Pipeline Task Scheduler Manager ===
Repository: C:\ai_risa_data
Task Folder: \AI-RISA\

✓ Registered: AI-RISA Pipeline Normal Run
  Path: \AI-RISA\AI-RISA-Pipeline-Normal-Run
  Launcher: C:\ai_risa_data\schedule_full_pipeline_run.ps1
  Schedule: Daily at 14:00
  Run as: SYSTEM

✓ Registered: AI-RISA Pipeline Dry-Run
  Path: \AI-RISA\AI-RISA-Pipeline-Dry-Run
  Launcher: C:\ai_risa_data\schedule_full_pipeline_dry_run.ps1
  Schedule: Daily at 13:00
  Run as: SYSTEM

All tasks registered successfully.
```

### Step 3: Create Runs Directory

The launchers create this automatically, but you can pre-create it:

```powershell
New-Item -Path C:\ai_risa_data\runs -ItemType Directory -Force | Out-Null
```

### Step 4: Run a Dry-Run Verification

Test the scheduler before relying on automation:

```powershell
# Run dry-run launcher manually
cd C:\ai_risa_data
.\schedule_full_pipeline_dry_run.ps1
```

This will:
1. Create folder: `C:\ai_risa_data\runs\YYYY-MM-DD_HHMMSS\`
2. Execute pipeline with `--dry-run` flag
3. Copy all summaries to run folder
4. Create `launcher.log` in run folder
5. Write entry to `run_history_index.json`

Check for success:
```powershell
# Should exit 0
echo $LASTEXITCODE

# View launcher log
Get-Content C:\ai_risa_data\runs\(latest_folder)\launcher.log

# View run index
Get-Content C:\ai_risa_data\runs\run_history_index.json | ConvertFrom-Json | Format-Table -AutoSize
```

---

## Task Management

### List Current Task Status

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -List
```

Output:
```
Current Task Status:

  [AI-RISA-Pipeline-Normal-Run]
    ✓ Enabled
    State: Ready
    Last run: 2026-03-31 14:00:23
    Next run: 2026-04-01 14:00:00

  [AI-RISA-Pipeline-Dry-Run]
    ✓ Enabled
    State: Ready
    Last run: 2026-03-31 13:00:15
    Next run: 2026-04-01 13:00:00
```

### Disable Scheduled Tasks

Temporarily stop automated execution:

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Disable
```

Tasks remain in Task Scheduler but won't trigger. Re-enable with:

```powershell
.\register_pipeline_tasks.ps1 -Enable
```

### Re-Register Tasks (Update Schedule Times)

Change normal run to 6:00 PM, dry-run to 5:00 PM:

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Enable -NormalRunTime 18:00 -DryRunTime 17:00
```

### Remove Tasks Entirely

⚠️ **Warning:** This removes tasks from Task Scheduler. They can be re-registered later.

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Remove
```

Requires confirmation: type `yes` at prompt.

---

## Verifying Execution

### Check Last Execution

```powershell
# View run history index
$index = Get-Content C:\ai_risa_data\runs\run_history_index.json -Raw | ConvertFrom-Json
$latest = $index | Sort-Object -Property timestamp -Descending | Select-Object -First 1

Write-Output "Latest run: $($latest.timestamp)"
Write-Output "Mode: $($latest.mode)"
Write-Output "Status: $($latest.status)"
Write-Output "Exit code: $($latest.exit_code)"
```

### View Run Logs

Each timestamped run folder contains `launcher.log`:

```powershell
# View latest run log
$latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-Content (Join-Path $latestRun.FullName 'launcher.log')
```

### Verify Run Artifacts

Confirm all expected artifacts were collected:

```powershell
# List artifacts in latest run
$latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
Get-ChildItem $latestRun.FullName -File | Format-Table Name, Length, LastWriteTime
```

### Validate Master Summary

Check the pipeline execution result:

```powershell
$latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
$summary = Get-Content (Join-Path $latestRun.FullName 'full_pipeline_run_summary.json') -Raw | ConvertFrom-Json

Write-Output "Status: $($summary.status)"
Write-Output "Exit code: $($summary.details | Select-Object -ExpandProperty 'exit_code')"
Write-Output "Stages completed: $($summary.counts.completed) / $($summary.counts.stage_total)"
Write-Output "Warnings: $($summary.counts.warnings)"
Write-Output "Errors: $($summary.counts.errors)"
```

### Compare Normal vs Dry-Run Results

```powershell
# Get last normal and dry-run executions
$index = Get-Content C:\ai_risa_data\runs\run_history_index.json -Raw | ConvertFrom-Json

$lastNormal = $index | Where-Object { $_.mode -eq 'normal' } | Sort-Object -Property timestamp -Descending | Select-Object -First 1
$lastDryRun = $index | Where-Object { $_.mode -eq 'dry-run' } | Sort-Object -Property timestamp -Descending | Select-Object -First 1

Write-Output "Last normal run: $($lastNormal.timestamp) - Status: $($lastNormal.status)"
Write-Output "Last dry-run: $($lastDryRun.timestamp) - Status: $($lastDryRun.status)"
```

---

## Troubleshooting

### Task Didn't Execute

1. **Verify task is enabled:**
   ```powershell
   .\register_pipeline_tasks.ps1 -List
   ```
   Look for `✓ Enabled` status.

2. **Check Task Scheduler directly:**
   - Open `taskschd.msc`
   - Navigate to `Task Scheduler Library → AI-RISA`
   - Right-click task → Properties → General (check "Enabled" checkbox)

3. **Trigger task manually:**
   ```powershell
   Get-ScheduledTask -TaskPath '\AI-RISA\' -TaskName 'AI-RISA-Pipeline-Normal-Run' | Start-ScheduledTask
   ```

4. **Check Windows Event Viewer:**
   - Event Viewer → Windows Logs → System
   - Look for Task Scheduler entries with status "Error"

### Pipeline Exits with Non-Zero Code

1. **Review launcher log:**
   ```powershell
   $latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
   Get-Content (Join-Path $latestRun.FullName 'launcher.log')
   ```

2. **Check pipeline-specific errors in master summary:**
   ```powershell
   $latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
   $summary = Get-Content (Join-Path $latestRun.FullName 'full_pipeline_run_summary.json') -Raw | ConvertFrom-Json
   $summary.details.stages | Where-Object { $_.exit_code -ne 0 }
   ```

3. **Re-run manually for diagnosis:**
   ```powershell
   cd C:\ai_risa_data
   python .\run_full_pipeline_auto.py --formats md docx pdf
   ```

### Missing Artifacts in Run Folder

The launcher only copies artifacts that exist after pipeline execution. If an artifact is missing:

1. **Check if pipeline actually created it:**
   ```powershell
   Get-ChildItem C:\ai_risa_data\output -File | Where-Object Name -Match '\.json$'
   ```

2. **Review master summary for stage failures:**
   ```powershell
   $summary = Get-Content C:\ai_risa_data\output\full_pipeline_run_summary.json -Raw | ConvertFrom-Json
   $summary.details.stages | Where-Object { $_.status -ne 'success' }
   ```

3. **Run stage directly to isolate issue:**
   ```powershell
   cd C:\ai_risa_data
   python .\build_upcoming_schedule_auto.py  # Example
   Get-Content output\upcoming_auto_summary.json | ConvertFrom-Json | Format-List
   ```

### Dry-Run Didn't Soft-Skip Expected Stages

Check launcher log for actual behavior:

```powershell
$latestRun = Get-ChildItem C:\ai_risa_data\runs -Directory -Filter '*_*' | Sort-Object Name -Descending | Select-Object -First 1 | Where-Object { $_.FullName -match '_' }
Get-Content (Join-Path $latestRun.FullName 'launcher.log') | Select-String -Pattern 'soft|skip|--dry-run'
```

Expected output for dry-run should show:
- `schedule` and `batch` stages executing with `--dry-run` flag
- `ingest`, `resolver`, `queue_build`, `queue_run` soft-skipped with 0 exit code

---

## Retention Policy

### Automatic Retention Overview

Retention is **not** automatically triggered by launchers. You must call it separately:

- From a scheduled task (optional, can be set to run after normal run)
- Manually on-demand
- Via script for integration with external systems

### Apply Retention Policy

**Dry-run (preview deletions):**
```powershell
cd C:\ai_risa_data
python .\prune_run_history.py --dry-run
```

Example output:
```
=== AI-RISA Run History Retention [DRY RUN] ===
Runs directory: C:\ai_risa_data\runs
Max age: 30 days
Max runs: 100

  Would delete [age]: 2026-03-01_120000 (C:\ai_risa_data\runs\2026-03-01_120000)
  Would delete [age]: 2026-03-02_120000 (C:\ai_risa_data\runs\2026-03-02_120000)

Results:
  Runs before: 45
  Runs after: 43
  Deleted: 2
  By age (2 runs)
```

**Live (actually delete):**
```powershell
python .\prune_run_history.py
```

### Configure Retention Policy

**Keep only 14 days, max 50 runs:**
```powershell
python .\prune_run_history.py --max-age 14 --max-runs 50
```

**Keep 60 days, max 200 runs:**
```powershell
python .\prune_run_history.py --max-age 60 --max-runs 200
```

### Schedule Retention Policy

Create a Task Scheduler task to run retention after normal pipeline:

```powershell
# This is a manual setup example
# Run this in PowerShell as Administrator to create the retention task

$action = New-ScheduledTaskAction `
    -Execute 'python.exe' `
    -Argument 'C:\ai_risa_data\prune_run_history.py --max-age 30 --max-runs 100'

$trigger = New-ScheduledTaskTrigger -Daily -At 15:00  # 1 hour after normal run

$principal = New-ScheduledTaskPrincipal `
    -UserID 'SYSTEM' `
    -LogonType ServiceAccount

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable $true

Register-ScheduledTask `
    -TaskPath '\AI-RISA\' `
    -TaskName 'AI-RISA-Retention-Policy' `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description 'Prune old runs based on age and count limits'
```

### Safety Guarantees

The retention policy **never** deletes:
- The newest successful run (protected by design)
- Runs that match neither age nor count constraints
- The entire run history (only oldest runs are pruned)

---

## Rollback Procedures

### Rollback to Previous Run

All run-history is timestamped. To restore state:

1. **Identify run to rollback from:**
   ```powershell
   $index = Get-Content C:\ai_risa_data\runs\run_history_index.json -Raw | ConvertFrom-Json
   $index | Sort-Object -Property timestamp -Descending | Select-Object -First 10 | Format-Table timestamp, mode, status
   ```

2. **Copy run artifacts back to output directory:**
   ```powershell
   $targetRun = 'C:\ai_risa_data\runs\2026-03-30_140000'  # Replace with target timestamp
   
   Copy-Item (Join-Path $targetRun 'full_pipeline_run_summary.json') `
             C:\ai_risa_data\output\ -Force
   
   Copy-Item (Join-Path $targetRun 'upcoming_auto_summary.json') `
             C:\ai_risa_data\output\ -Force
   
   # ... copy other summaries as needed
   ```

3. **Verify rollback:**
   ```powershell
   Get-Content C:\ai_risa_data\output\full_pipeline_run_summary.json -Raw | ConvertFrom-Json | Select-Object stage, status
   ```

### Disable Scheduler to Prevent Overwrites

Before rollback, disable scheduled tasks to prevent new runs:

```powershell
.\register_pipeline_tasks.ps1 -Disable
```

Re-enable after verification:

```powershell
.\register_pipeline_tasks.ps1 -Enable
```

### Emergency: Restore Specific Run Folder

If you need to preserve a specific run that's scheduled for deletion:

```powershell
# Before running retention, copy run folder to backup
$runToPreserve = 'C:\ai_risa_data\runs\2026-03-15_140000'
$backup = 'C:\ai_risa_data\runs\BACKUP_2026-03-15'

Copy-Item $runToPreserve $backup -Recurse -Force
```

---

## Quick Reference

### Most Common Operations

| Task | Command |
|------|---------|
| List current task status | `.\register_pipeline_tasks.ps1 -List` |
| Enable scheduled tasks | `.\register_pipeline_tasks.ps1 -Enable` |
| Disable scheduled tasks | `.\register_pipeline_tasks.ps1 -Disable` |
| Run normal pipeline now | `.\schedule_full_pipeline_run.ps1` |
| Run dry-run now | `.\schedule_full_pipeline_dry_run.ps1` |
| View last run log | `Get-Content C:\ai_risa_data\runs\(latest_folder)\launcher.log` |
| View run history | `Get-Content C:\ai_risa_data\runs\run_history_index.json -Raw \| ConvertFrom-Json` |
| Preview retention deletions | `python .\prune_run_history.py --dry-run` |
| Apply retention policy | `python .\prune_run_history.py` |
| Confirm last successful execution | `$index[-1] \| Format-Table timestamp, status, exit_code` |

### File Locations

| Item | Path |
|------|------|
| Normal run launcher | `C:\ai_risa_data\schedule_full_pipeline_run.ps1` |
| Dry-run launcher | `C:\ai_risa_data\schedule_full_pipeline_dry_run.ps1` |
| Task manager | `C:\ai_risa_data\register_pipeline_tasks.ps1` |
| Retention script | `C:\ai_risa_data\prune_run_history.py` |
| Run history index | `C:\ai_risa_data\runs\run_history_index.json` |
| Latest run folder | `C:\ai_risa_data\runs\(latest_timestamp)\` |

---

## Support

For issues or questions:

1. Review the **Troubleshooting** section above
2. Check launcher logs in run folder
3. Review pipeline execution details in `full_pipeline_run_summary.json`
4. Run manual smoke tests to isolate issues
5. Check Windows Event Viewer for Task Scheduler errors

---

**Document Version:** 1.0  
**Last Tested:** 2026-04-01  
**Compatibility:** Windows 10/11, PowerShell 5.1+, Python 3.7+

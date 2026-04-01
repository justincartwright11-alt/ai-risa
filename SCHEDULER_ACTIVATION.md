# AI-RISA Scheduler Activation Guide

**Status:** Ready for activation  
**Date:** 2026-04-01  
**Version:** 1.0

---

## Activation Instructions

Activating the scheduler requires **Administrator privilege**. Two methods are provided:

### Method 1: Batch File (Easiest) ✓ Recommended

1. **Open File Explorer** and navigate to `C:\ai_risa_data\`
2. **Right-click** on `activate_scheduler.bat`
3. **Select "Run as administrator"** (Windows will prompt for elevation)
4. **Batch file will:**
   - Self-elevate if needed
   - Execute task registration
   - Display registration output
   - Show next steps when complete

### Method 2: PowerShell (Manual)

1. **Open PowerShell as Administrator:**
   - Press `Win+X` → Select "Windows PowerShell (Admin)"
   - Or: Right-click PowerShell → "Run as administrator"

2. **Navigate and run registration:**
   ```powershell
   cd C:\ai_risa_data
   .\register_pipeline_tasks.ps1 -Enable
   ```

3. **Expected output:**
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

---

## Post-Activation Verification

### Step 1: Verify Tasks in Task Scheduler

**Manual verification:**
1. Press `Win+R`, type `taskschd.msc`, press Enter
2. Navigate to: **Task Scheduler Library → AI-RISA**
3. Verify both tasks appear:
   - ✓ AI-RISA-Pipeline-Normal-Run (should show enabled, Ready state)
   - ✓ AI-RISA-Pipeline-Dry-Run (should show enabled, Ready state)

**Or via PowerShell:**
```powershell
Get-ScheduledTask -TaskPath '\AI-RISA\' | Format-Table -Property TaskName, State, Enabled
```

Expected output:
```
TaskName                             State Enabled
--------                             ----- -------
AI-RISA-Pipeline-Dry-Run             Ready    True
AI-RISA-Pipeline-Normal-Run          Ready    True
```

### Step 2: Run Manual Dry-Run Check

Execute dry-run launcher to test scheduler infrastructure:

```powershell
cd C:\ai_risa_data
.\schedule_full_pipeline_dry_run.ps1
```

**Verify execution:**
- Exit code should be 0:
  ```powershell
  echo $LASTEXITCODE
  ```
- New timestamped folder created: `C:\ai_risa_data\runs\2026-MM-DD_HHMMSS\`
- Launcher log created with execution details
- 7 summary JSON files copied to run folder

### Step 3: Confirm Run History

**View latest runs:**
```powershell
cd C:\ai_risa_data\runs
$index = Get-Content run_history_index.json -Raw | ConvertFrom-Json
$index | Sort-Object timestamp -Descending | Select-Object -First 3 | Format-Table timestamp, mode, status, exit_code
```

**Expected output example:**
```
timestamp         mode    status  exit_code
---------         ----    ------  ---------
2026-04-01_150000 dry-run success         0
2026-04-01_140000 normal  success         0
2026-04-01_130000 dry-run success         0
```

**Verify latest run folder:**
```powershell
$latestFolder = Get-ChildItem runs -Directory | Sort-Object Name -Descending | Select-Object -First 1
Write-Output "Latest run: $($latestFolder.Name)"
Write-Output "Contents:"
Get-ChildItem $latestFolder.FullName -File | Format-Table Name, Length
```

Expected files in run folder:
- `launcher.log` (>500 bytes)
- `full_pipeline_run_summary.json` (~8 KB)
- `upcoming_auto_summary.json` (~14 KB)
- `dependency_resolution_summary.json` (~7 KB)
- `prediction_queue_build_summary.json` (~1.5 KB)
- `prediction_queue_run_summary.json` (~2 KB)
- `event_batch_run_summary.json` (~56 KB)
- `upcoming_events_ingest_summary.json` (~12 KB)

---

## Scheduler Timeline

After activation, the scheduler will run on this timeline:

### Daily Schedule (Default)
- **13:00 (1:00 PM):** Dry-run execution
  - File: `C:\ai_risa_data\runs\YYYY-MM-DD_1300xx\`
  - Log: `launcher.log` in run folder

- **14:00 (2:00 PM):** Normal run execution
  - File: `C:\ai_risa_data\runs\YYYY-MM-DD_1400xx\`
  - Log: `launcher.log` in run folder

Both executions automatically:
1. Create timestamped run folder
2. Execute pipeline (dry-run or normal)
3. Collect all summaries
4. Update `run_history_index.json`
5. Log to `launcher.log`

### Customizing Schedule Times

To change execution times (e.g., 6:00 AM and 5:00 AM):

**PowerShell as Administrator:**
```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Enable -NormalRunTime 06:00 -DryRunTime 05:00
```

---

## Setting Retention Policy Defaults

Configure automatic cleanup of old runs:

### Option 1: Conservative (Keep 60 days, max 200 runs)

```powershell
cd C:\ai_risa_data
python .\prune_run_history.py --max-age 60 --max-runs 200
```

### Option 2: Moderate (Keep 30 days, max 100 runs) ← Recommended

```powershell
python .\prune_run_history.py --max-age 30 --max-runs 100
```

### Option 3: Aggressive (Keep 14 days, max 50 runs)

```powershell
python .\prune_run_history.py --max-age 14 --max-runs 50
```

**Always preview first (dry-run):**
```powershell
python .\prune_run_history.py --dry-run --max-age 30 --max-runs 100
```

### Schedule Retention Policy (Optional)

To run retention automatically after normal runs (e.g., 3:00 PM):

**PowerShell as Administrator:**
```powershell
$action = New-ScheduledTaskAction `
    -Execute 'python.exe' `
    -Argument 'C:\ai_risa_data\prune_run_history.py'

$trigger = New-ScheduledTaskTrigger -Daily -At 15:00

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
    -Description 'Prune old runs based on retention policy'
```

---

## Verifying Scheduled Execution

### 1. Verify Next Scheduled Times

```powershell
Get-ScheduledTask -TaskPath '\AI-RISA\' | ForEach-Object {
    $task = $_
    $nextRun = (Get-ScheduledTaskInfo -TaskPath $task.TaskPath -TaskName $task.TaskName).NextRunTime
    Write-Output "$($task.TaskName): Next run = $nextRun"
}
```

### 2. Check Task Handler

Both launchersRun as SYSTEM account by default. Verify:

```powershell
$task = Get-ScheduledTask -TaskPath '\AI-RISA\' -TaskName 'AI-RISA-Pipeline-Normal-Run'
$task.Principal | Format-List UserId, LogonType
```

### 3. Monitor Execution Logs

Check Event Viewer for Task Scheduler events:
- Event Viewer → Windows Logs → System
- Filter for source "TaskScheduler"
- Look for task executions at 13:00 and 14:00

Or check latest run folder directly:
```powershell
Get-ChildItem C:\ai_risa_data\runs -Directory | Sort-Object Name -Descending | Select-Object -First 1 | ForEach-Object {
    Write-Output "Latest run: $($_.Name)"
    Get-Content (Join-Path $_.FullName 'launcher.log') | Select-Object -Last 20
}
```

---

## Baseline Freeze Checklist

Once tasks are running successfully, freeze this version:

- [ ] Both tasks registered and showing "Ready" in Task Scheduler
- [ ] Manual dry-run executed successfully (exit 0)
- [ ] `run_history_index.json` contains at least 1 entry
- [ ] Latest run folder has all 8 summary files
- [ ] Retention policy defaults configured
- [ ] First scheduled dry-run completed (check at 13:05)
- [ ] First scheduled normal run completed (check at 14:05)
- [ ] Run history entries match scheduled times
- [ ] Operator documentation reviewed and accessible

### Create Release Notes

Document this baseline freeze:

```
AI-RISA Pipeline Baseline v1.0 - Scheduled Execution Ready
==========================================================

Freeze Date: 2026-04-01
Frozen By: [Operator Name]
Commit: [Git SHA if applicable]

Components:
✓ 6-stage pipeline orchestrator (normalized schema)
✓ Windows Task Scheduler integration (2 tasks: normal + dry-run)
✓ Timestamped run-history with append-only index
✓ Retention policy (configurable age + count)
✓ Operator documentation (RUN_OPERATIONS.md)

Deployment Status:
✓ Tasks registered in Task Scheduler
✓ Manual verification passed
✓ First dry-run executed: [timestamp]
✓ First normal run executed: [timestamp]
✓ Retention policy configured for: 30 days / 100 max runs

Next Scheduled Executions:
- Dry-run: Daily 13:00 (1:00 PM)
- Normal: Daily 14:00 (2:00 PM)

Run History Location: C:\ai_risa_data\runs\
Operator Guide: C:\ai_risa_data\RUN_OPERATIONS.md
```

---

## Troubleshooting

### Tasks Not Showing in Task Scheduler

**Verify registration:**
```powershell
Get-ScheduledTask -TaskPath '\AI-RISA\' -ErrorAction SilentlyContinue
```

If empty, re-run registration:
```powershell
.\register_pipeline_tasks.ps1 -Enable
```

### Scheduled Task Didn't Execute

1. Verify task is enabled: `.\register_pipeline_tasks.ps1 -List`
2. Check Task Scheduler → SYSTEM account has required permissions
3. Review Windows Event Viewer for Task Scheduler errors
4. Manually trigger task to verify:
   ```powershell
   Get-ScheduledTask -TaskPath '\AI-RISA\' -TaskName 'AI-RISA-Pipeline-Normal-Run' | Start-ScheduledTask
   ```

### Run History Index Unreadable

Ensure no BOM (Byte Order Mark):
```powershell
$bytes = Get-Content C:\ai_risa_data\runs\run_history_index.json -Encoding Byte -TotalCount 3
if ($bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191) {
    Write-Output "ERROR: File has UTF-8 BOM - launchers should not write this"
} else {
    Write-Output "OK: No BOM detected"
}
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Register tasks | `.\register_pipeline_tasks.ps1 -Enable` (needs admin) |
| List tasks | `.\register_pipeline_tasks.ps1 -List` |
| Disable tasks | `.\register_pipeline_tasks.ps1 -Disable` |
| Remove tasks | `.\register_pipeline_tasks.ps1 -Remove` |
| Run dry-run now | `.\schedule_full_pipeline_dry_run.ps1` |
| Run normal now | `.\schedule_full_pipeline_run.ps1` |
| View run history | `Get-Content runs\run_history_index.json \| ConvertFrom-Json` |
| Preview retention | `python .\prune_run_history.py --dry-run` |
| Apply retention | `python .\prune_run_history.py` |

---

**Document Version:** 1.0  
**Created:** 2026-04-01  
**Status:** Ready for Deployment

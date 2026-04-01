# 🔧 ACTIVATION SEQUENCE - User Action Required

**Status:** Ready for manual activation  
**Date:** 2026-04-01  
**Target:** Administrator PowerShell session

---

## ⚠️ Important: Administrator Privilege Required

The task registration script requires Windows Administrator privilege. You must run the following commands from an **Administrator PowerShell session**.

### How to Open Administrator PowerShell

**Method 1: Win+X Menu (Fastest)**
1. Press `Win+X`
2. Select **"Windows PowerShell (Admin)"**
3. Click **"Yes"** when UAC prompt appears

**Method 2: Search Menu**
1. Press `Win+S` (or click Start)
2. Type `PowerShell`
3. Right-click **"Windows PowerShell"**
4. Select **"Run as administrator"**

**Method 3: Run Both Files Directly**
1. Open File Explorer
2. Navigate to `C:\ai_risa_data\`
3. Right-click **`activate_scheduler.bat`**
4. Select **"Run as Administrator"**
5. Wait for completion

---

## 🎯 Activation Steps (from Administrator PowerShell)

Once you have Administrator PowerShell open, run these commands in order:

### Step 1: Navigate and Register Tasks (< 1 minute)

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Enable
```

**Expected output:**
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

**If you see errors:**
- Verify you have Administrator privilege (check title bar for "Administrator")
- Check that the launchers exist: `Test-Path .\schedule_full_pipeline_run.ps1`
- Review error message and consult RUN_OPERATIONS.md

### Step 2: Verify Task Registration (< 1 minute)

```powershell
.\register_pipeline_tasks.ps1 -List
```

**Expected output:**
```
Current Task Status:

  [AI-RISA-Pipeline-Normal-Run]
    ✓ Enabled
    State: Ready
    ...

  [AI-RISA-Pipeline-Dry-Run]
    ✓ Enabled
    State: Ready
    ...
```

**Both tasks should show:**
- ✓ Status: **Enabled**
- State: **Ready**

---

## ✅ Post-Activation Verification (from regular PowerShell - no admin needed)

Once tasks are registered, you can verify without Administrator terminal.

### Step 3: Test Dry-Run Manually (2-3 minutes)

```powershell
cd C:\ai_risa_data
.\schedule_full_pipeline_dry_run.ps1
```

**Expected output (tail of execution):**
```
[TIMESTAMP] === AI-RISA Pipeline: DRY RUN ===
[TIMESTAMP] Start time: ...
[TIMESTAMP] Run folder: C:\ai_risa_data\runs\2026-04-01_HHMMSS
...
[TIMESTAMP] Copying artifacts...
[TIMESTAMP] Updating run index...
[TIMESTAMP] === Execution complete ===
[TIMESTAMP] Status: success
```

**Verify exit code:**
```powershell
echo $LASTEXITCODE
```

Should be **0**.

### Step 4: Confirm Run History (< 1 minute)

```powershell
cd C:\ai_risa_data\runs
$idx = Get-Content run_history_index.json -Raw | ConvertFrom-Json
$idx | Sort-Object timestamp -Descending | Select-Object -First 3 | Format-Table timestamp, mode, status, exit_code -AutoSize
```

**Expected output:**
```
timestamp         mode    status  exit_code
---------         ----    ------  ---------
2026-04-01_... dry-run success         0
...
```

**At minimum:** One entry with `status: success` and `exit_code: 0`

**Verify run folder:**
```powershell
$latest = Get-ChildItem -Directory | Sort-Object Name -Descending | Select-Object -First 1
Write-Output "Latest run folder: $($latest.Name)"
Get-ChildItem $latest.FullName -File | Format-Table Name, Length -AutoSize
```

**Should have these 8 files:**
- launcher.log (500+ bytes)
- full_pipeline_run_summary.json
- upcoming_auto_summary.json
- dependency_resolution_summary.json
- prediction_queue_build_summary.json
- prediction_queue_run_summary.json
- event_batch_run_summary.json
- upcoming_events_ingest_summary.json

---

## 📋 Summary of Commands to Run

**In Administrator PowerShell:**
```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -Enable
.\register_pipeline_tasks.ps1 -List
```

**In Regular PowerShell (after admin tasks complete):**
```powershell
cd C:\ai_risa_data
.\schedule_full_pipeline_dry_run.ps1
echo $LASTEXITCODE

$idx = Get-Content .\runs\run_history_index.json -Raw | ConvertFrom-Json
$idx | Sort-Object timestamp -Descending | Select-Object -First 1 | Format-Table timestamp, mode, status, exit_code
```

---

## ⏰ Timeline After Activation

Once tasks are registered and verified:

| Time | Event |
|------|-------|
| **Today 13:00** | First dry-run task executes automatically |
| **Today 14:00** | First normal run task executes automatically |
| **Tomorrow 13:00** | Dry-run continues daily |
| **Tomorrow 14:00** | Normal run continues daily |

Each execution creates:
- Timestamped folder: `runs\YYYY-MM-DD_HHMMSS\`
- Index entry in `run_history_index.json`
- Execution log: `launcher.log`

---

## 🆘 Troubleshooting

**"Access Denied" or "Script Requires Administrator"**
→ You must run from Administrator PowerShell. See "How to Open Administrator PowerShell" above.

**"Task already exists" error**
→ Normal if running Enable twice. To re-register, run `-Remove` first, then `-Enable`

**No tasks appear after registration**
→ Verification may need Task Scheduler refresh. Close and reopen `taskschd.msc`

**Dry-run exits with non-zero code**
→ Check `launcher.log` in the run folder for details. Run `python .\run_full_pipeline_auto.py --dry-run` directly to isolate.

For additional help, see:
- **RUN_OPERATIONS.md** (Troubleshooting section)
- **SCHEDULER_ACTIVATION.md** (detailed guide)

---

## ✨ You're Ready!

All components are in place. Just follow the activation steps above and the scheduler will be live.

Expected time to completion: **~10 minutes**

Document the results for your baseline freeze record (see BASELINE_v1.0_FROZEN.md).

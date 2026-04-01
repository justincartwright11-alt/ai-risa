# 🚀 AI-RISA Scheduler: Ready for Activation

**Status:** All scripts prepared and validated ✓  
**Next Step:** Activate on target machine  
**Estimated Time:** 5 minutes

---

## Activation Files Created

| File | Purpose | Location |
|------|---------|----------|
| `activate_scheduler.bat` | Admin elevation + task registration (recommended) | `C:\ai_risa_data\activate_scheduler.bat` |
| `activate_scheduler.ps1` | PowerShell elevation wrapper (alternative) | `C:\ai_risa_data\activate_scheduler.ps1` |
| `SCHEDULER_ACTIVATION.md` | Comprehensive activation guide | `C:\ai_risa_data\SCHEDULER_ACTIVATION.md` |

---

## ⚡ Quick Start: Immediate Next Steps

### Step 1: Activate Tasks (1 minute)

**Option A: Batch File (Easiest)**
1. Open File Explorer → `C:\ai_risa_data\`
2. **Right-click** `activate_scheduler.bat` → **Run as administrator**
3. Watch output, verify "All tasks registered successfully"

**Option B: PowerShell (Manual)**
1. Open PowerShell as Administrator
2. Run:
   ```powershell
   cd C:\ai_risa_data
   .\register_pipeline_tasks.ps1 -Enable
   ```

### Step 2: Verify Tasks (1 minute)

```powershell
cd C:\ai_risa_data
.\register_pipeline_tasks.ps1 -List
```

Should show:
```
✓ Enabled  AI-RISA-Pipeline-Dry-Run (13:00 daily)
✓ Enabled  AI-RISA-Pipeline-Normal-Run (14:00 daily)
```

### Step 3: Manual Dry-Run Test (2 minutes)

```powershell
cd C:\ai_risa_data
.\schedule_full_pipeline_dry_run.ps1
```

Should complete with exit code 0 and show "Status: success"

### Step 4: Verify Run History (1 minute)

```powershell
cd C:\ai_risa_data\runs
$idx = Get-Content run_history_index.json -Raw | ConvertFrom-Json
$idx | Sort-Object timestamp -Descending | Select-Object -First 3 | Format-Table timestamp, mode, status, exit_code
```

Should show at least one dry-run entry with `status: success`

---

## 📋 What Gets Activated

### Scheduled Tasks

| Task | Schedule | Launcher | Mode |
|------|----------|----------|------|
| **AI-RISA-Pipeline-Dry-Run** | Daily 13:00 (1:00 PM) | `schedule_full_pipeline_dry_run.ps1` | Safe verification |
| **AI-RISA-Pipeline-Normal-Run** | Daily 14:00 (2:00 PM) | `schedule_full_pipeline_run.ps1` | Full execution |

### Each Execution Will

✓ Create timestamped folder: `runs\YYYY-MM-DD_HHMMSS\`  
✓ Run pipeline (dry-run or normal)  
✓ Collect 7 stage summaries + ingest summary  
✓ Write launcher.log with full execution trace  
✓ Append entry to run_history_index.json  
✓ Preserve exit codes for monitoring

---

## 📚 Complete Documentation

After activation, refer to:

- **RUN_OPERATIONS.md** — Full operator guide (setup, troubleshooting, rollback)
- **SCHEDULER_ACTIVATION.md** — Activation details and verification procedures
- **register_pipeline_tasks.ps1 -Help** — Task management (enable/disable/remove)

---

## ✅ Success Criteria

You'll know activation is successful when:

- [ ] Both tasks appear in Task Scheduler (taskschd.msc) under `\AI-RISA\`
- [ ] Both tasks show "Enabled" state
- [ ] Manual dry-run exits with code 0
- [ ] New timestamped folder created: `runs\YYYY-MM-DD_HHMMSS\`
- [ ] run_history_index.json contains the new run entry
- [ ] At 13:00, dry-run executes automatically
- [ ] At 14:00, normal run executes automatically
- [ ] New entries appear in run_history_index.json after each scheduled execution

---

## ⚙️ Optional: Configure Retention Policy

After activation, set retention defaults:

```powershell
cd C:\ai_risa_data
# Preview what would be deleted
python .\prune_run_history.py --dry-run --max-age 30 --max-runs 100

# Apply retention (keep 30 days, max 100 runs)
python .\prune_run_history.py --max-age 30 --max-runs 100
```

---

## 🔒 Baseline Freeze

Once Step 1-4 are verified and successful, you have a frozen, operational baseline:

**Baseline: AI-RISA Pipeline v1.0 - Scheduled Execution Ready**

- ✓ Core pipeline: 6 normalized stages
- ✓ Scheduler: Windows Task Scheduler integration
- ✓ History: Timestamped runs with index
- ✓ Operations: Documented procedures
- ✓ Validation: Activation verified

This is a **valid production checkpoint** for the AI-RISA automation stack.

---

## 📞 If You Need Help

**Permission Denied Error:**
- Right-click `activate_scheduler.bat` → "Run as administrator"
- Or right-click PowerShell → "Run as administrator"

**Tasks Not Appearing:**
- Verify registration: `.\register_pipeline_tasks.ps1 -List`
- Re-run activation: `.\register_pipeline_tasks.ps1 -Enable`

**Scheduled Execution Didn't Run:**
- Check Event Viewer (Windows Logs → System)
- Check latest run folder: `runs\(latest)\launcher.log`
- Manual trigger: `Get-ScheduledTask -TaskPath '\AI-RISA\' -TaskName 'AI-RISA-Pipeline-Normal-Run' | Start-ScheduledTask`

For detailed troubleshooting, see **RUN_OPERATIONS.md** → Troubleshooting section.

---

## 📦 Deliverables Summary

| Component | Status | File(s) |
|-----------|--------|---------|
| Pipeline Orchestrator | ✓ Complete | `run_full_pipeline_auto.py` + 6 stages |
| Scheduler Infrastructure | ✓ Complete | `activate_scheduler.bat/ps1`, `register_pipeline_tasks.ps1` |
| Run History | ✓ Complete | `runs/` folder + `run_history_index.json` |
| Retention Policy | ✓ Complete | `prune_run_history.py` |
| Operator Docs | ✓ Complete | `RUN_OPERATIONS.md`, `SCHEDULER_ACTIVATION.md` |
| Validation | ✓ Complete | All scripts tested, schema normalized |

---

**Ready to activate. Once you run `activate_scheduler.bat` as Administrator, the scheduler becomes operational. Expected first dry-run: today at 13:00.**

Need any clarifications before activation? Otherwise, this is your checkpoint to freeze baseline v1.0.

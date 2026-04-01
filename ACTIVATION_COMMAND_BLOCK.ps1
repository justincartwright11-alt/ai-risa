# ════════════════════════════════════════════════════════════════════════════════
# AI-RISA SCHEDULER v1.0 — FINAL ACTIVATION
# ════════════════════════════════════════════════════════════════════════════════
# 
# IMPORTANT: This MUST be run in Administrator PowerShell
# 
# Steps:
# 1. Right-click PowerShell → "Run as Administrator" (or Win+X → "Windows PowerShell (Admin)")
# 2. Click "Yes" to UAC prompt
# 3. Paste entire block below into Administrator PowerShell
# 4. Wait for all commands to complete
# 5. Screenshot or copy the final output for POST_ACTIVATION_VERIFICATION.md
#
# ════════════════════════════════════════════════════════════════════════════════

cd C:\ai_risa_data

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " STEP 1: Registering Pipeline Tasks" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

.\register_pipeline_tasks.ps1 -Enable

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " STEP 2: Verifying Task Registration" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

.\register_pipeline_tasks.ps1 -List

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " STEP 3: Checking Task Scheduler State" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Get-ScheduledTask -TaskPath '\AI-RISA' | Format-Table TaskName, State, Enabled -AutoSize

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " STEP 4: Running Manual Dry-Run Test" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

.\schedule_full_pipeline_dry_run.ps1
Write-Host "DRY_RUN_EXIT_CODE=$LASTEXITCODE" -ForegroundColor Yellow

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host " STEP 5: Verifying Run History" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

Get-Content .\runs\run_history_index.json -Raw | ConvertFrom-Json | Format-Table timestamp, mode, status, exit_code -AutoSize

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host " ✓ ACTIVATION COMPLETE" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Next step: Open POST_ACTIVATION_VERIFICATION.md and fill in:" -ForegroundColor Yellow
Write-Host "  - Activation date/time" -ForegroundColor Yellow
Write-Host "  - Machine name and OS version" -ForegroundColor Yellow
Write-Host "  - Administrator username" -ForegroundColor Yellow
Write-Host "  - Task registration status (copy task table above)" -ForegroundColor Yellow
Write-Host "  - Manual dry-run exit code and results" -ForegroundColor Yellow
Write-Host "  - Run history entry details" -ForegroundColor Yellow
Write-Host ""

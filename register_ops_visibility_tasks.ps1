#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Register AI-RISA v1.1 operations visibility tasks.

.DESCRIPTION
    Creates additive monitoring tasks only:
    - AI-RISA-Latest-Run-Alert-Check (repeating interval)
    - AI-RISA-Daily-Health-Summary (daily)
    - AI-RISA-Weekly-Health-Rollup (weekly)

    Slice 3 behavior:
    - alert-check task can emit optional transition-based notifications
    - daily/weekly tasks can refresh scheduler verification + operator checklists

    These tasks are read-only against pipeline outputs and do not modify
    existing production pipeline tasks.
#>

param(
    [string]$RepoRoot = 'C:\ai_risa_data',
    [string]$TaskFolder = '\AI-RISA\',
    [string]$Username = 'SYSTEM',
    [int]$AlertIntervalMinutes = 30,
    [string]$DailySummaryTime = '06:30',
    [string]$WeeklyRollupDay = 'Sunday',
    [string]$WeeklyRollupTime = '07:00',
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Remove,
    [switch]$List
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$tasks = @(
    @{
        Name = 'AI-RISA-Latest-Run-Alert-Check'
        Description = 'Checks latest run index/summaries for alert state and optional transition notifications.'
        Launcher = Join-Path $RepoRoot 'schedule_latest_run_alert_check.ps1'
        Kind = 'interval'
    },
    @{
        Name = 'AI-RISA-Daily-Health-Summary'
        Description = 'Generates daily health summary and optional verification/checklist artifacts.'
        Launcher = Join-Path $RepoRoot 'schedule_daily_health_summary.ps1'
        Kind = 'daily'
        Time = $DailySummaryTime
    },
    @{
        Name = 'AI-RISA-Weekly-Health-Rollup'
        Description = 'Generates weekly health rollup and optional verification/checklist artifacts.'
        Launcher = Join-Path $RepoRoot 'schedule_weekly_health_rollup.ps1'
        Kind = 'weekly'
        Day = $WeeklyRollupDay
        Time = $WeeklyRollupTime
    }
)

function Test-AdminPrivilege {
    $principal = [Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Ensure-TaskFolder {
    param([string]$Path)

    try {
        $existingFolder = Get-ScheduledTaskFolder -Path $Path -ErrorAction SilentlyContinue
        if ($existingFolder) {
            return
        }

        $rootFolder = Get-ScheduledTaskFolder -Path '\' -ErrorAction SilentlyContinue
        if ($rootFolder) {
            $folderName = $Path.Trim('\').Split('\') | Select-Object -Last 1
            $rootFolder | New-ScheduledTaskFolder -Name $folderName -ErrorAction SilentlyContinue | Out-Null
        }
    }
    catch {
        Write-Warning "Could not create task folder: $Path"
    }
}

function Build-Trigger {
    param([hashtable]$Task)

    if ($Task.Kind -eq 'interval') {
        $start = (Get-Date).Date.AddMinutes(1)
        if ($start -lt (Get-Date)) {
            $start = (Get-Date).AddMinutes(1)
        }
        return New-ScheduledTaskTrigger `
            -Once `
            -At $start `
            -RepetitionInterval (New-TimeSpan -Minutes $AlertIntervalMinutes) `
            -RepetitionDuration (New-TimeSpan -Days 3650)
    }

    $timeParts = $Task.Time -split ':'
    if ($timeParts.Count -ne 2) {
        throw "Invalid time format for task '$($Task.Name)': $($Task.Time)"
    }

    $hour = [int]$timeParts[0]
    $minute = [int]$timeParts[1]

    if ($Task.Kind -eq 'weekly') {
        return New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek $Task.Day -At "$($hour):$($minute.ToString('00'))"
    }

    return New-ScheduledTaskTrigger -Daily -At "$($hour):$($minute.ToString('00'))"
}

function Register-VisibilityTask {
    param(
        [hashtable]$Task,
        [string]$Folder,
        [string]$RunAs
    )

    if (-not (Test-Path $Task.Launcher)) {
        Write-Error "Launcher not found: $($Task.Launcher)"
        return $false
    }

    try {
        Unregister-ScheduledTask -TaskPath $Folder -TaskName $Task.Name -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    }
    catch {}

    try {
        $trigger = Build-Trigger -Task $Task
        $action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$($Task.Launcher)`""
        $principal = New-ScheduledTaskPrincipal -UserID $RunAs -LogonType ServiceAccount
        $settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable:$false

        Register-ScheduledTask `
            -TaskPath $Folder `
            -TaskName $Task.Name `
            -Trigger $trigger `
            -Action $action `
            -Principal $principal `
            -Settings $settings `
            -Description $Task.Description `
            -Force | Out-Null

        Enable-ScheduledTask -TaskPath $Folder -TaskName $Task.Name -ErrorAction SilentlyContinue | Out-Null

        Write-Host "REGISTERED: $($Task.Name)" -ForegroundColor Green
        Write-Host "  Path: $Folder$($Task.Name)"
        Write-Host "  Launcher: $($Task.Launcher)"
        if ($Task.Kind -eq 'interval') {
            Write-Host "  Schedule: Every $AlertIntervalMinutes minutes"
        }
        elseif ($Task.Kind -eq 'weekly') {
            Write-Host "  Schedule: Weekly on $($Task.Day) at $($Task.Time)"
        }
        else {
            Write-Host "  Schedule: Daily at $($Task.Time)"
        }
        return $true
    }
    catch {
        Write-Error "Failed to register task '$($Task.Name)': $_"
        return $false
    }
}

function Set-VisibilityTaskState {
    param(
        [string]$Name,
        [string]$Folder,
        [bool]$Enabled
    )

    try {
        $task = Get-ScheduledTask -TaskPath $Folder -TaskName $Name -ErrorAction Stop
        if ($Enabled) {
            Enable-ScheduledTask -InputObject $task | Out-Null
            Write-Host "ENABLED: $Name" -ForegroundColor Green
        }
        else {
            Disable-ScheduledTask -InputObject $task | Out-Null
            Write-Host "DISABLED: $Name" -ForegroundColor Yellow
        }
        return $true
    }
    catch {
        Write-Error "Failed to set state for '$Name': $_"
        return $false
    }
}

Write-Host "`n=== AI-RISA Ops Visibility Task Manager ===" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
Write-Host "Task Folder: $TaskFolder`n"

if (-not (Test-AdminPrivilege)) {
    Write-Error 'This script requires administrator privileges. Please run as Administrator.'
    exit 1
}

if (-not (Test-Path $RepoRoot)) {
    Write-Error "Repository root does not exist: $RepoRoot"
    exit 1
}

Ensure-TaskFolder -Path $TaskFolder

if ($List -or (-not $Enable -and -not $Disable -and -not $Remove)) {
    Write-Host 'Current Ops Task Status:' -ForegroundColor Cyan
    Write-Host ''

    foreach ($task in $tasks) {
        try {
            $status = Get-ScheduledTask -TaskPath $TaskFolder -TaskName $task.Name -ErrorAction Stop
            $enabled = if ($status.PSObject.Properties.Name -contains 'Enabled') { [bool]$status.Enabled } elseif ($status.Settings) { [bool]$status.Settings.Enabled } else { $true }
            Write-Host "  [$($task.Name)]" -ForegroundColor Cyan
            Write-Host "    State: $($status.State)"
            Write-Host "    Enabled: $enabled"
        }
        catch {
            Write-Host "  [$($task.Name)]" -ForegroundColor Gray
            Write-Host '    Status: Not registered' -ForegroundColor Gray
        }
        Write-Host ''
    }
}

if ($Enable) {
    Write-Host 'Enabling ops visibility tasks...' -ForegroundColor Cyan
    Write-Host ''

    $ok = 0
    foreach ($task in $tasks) {
        if (Register-VisibilityTask -Task $task -Folder $TaskFolder -RunAs $Username) {
            $ok++
        }
        Write-Host ''
    }

    if ($ok -eq $tasks.Count) {
        Write-Host 'All ops visibility tasks registered successfully.' -ForegroundColor Green
        exit 0
    }

    Write-Error 'One or more ops visibility tasks failed to register.'
    exit 1
}

if ($Disable) {
    Write-Host 'Disabling ops visibility tasks...' -ForegroundColor Cyan
    Write-Host ''

    foreach ($task in $tasks) {
        Set-VisibilityTaskState -Name $task.Name -Folder $TaskFolder -Enabled $false | Out-Null
    }

    Write-Host ''
    Write-Host 'Ops visibility tasks disabled.' -ForegroundColor Yellow
    exit 0
}

if ($Remove) {
    Write-Host 'WARNING: This will remove AI-RISA ops visibility tasks.' -ForegroundColor Red
    $confirm = Read-Host "Type 'yes' to confirm removal"
    if ($confirm -ne 'yes') {
        Write-Host 'Cancelled.' -ForegroundColor Yellow
        exit 0
    }

    foreach ($task in $tasks) {
        try {
            Unregister-ScheduledTask -TaskPath $TaskFolder -TaskName $task.Name -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
            Write-Host "REMOVED: $($task.Name)" -ForegroundColor Yellow
        }
        catch {
            Write-Warning "Could not remove task '$($task.Name)': $_"
        }
    }

    exit 0
}

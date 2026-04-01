#Requires -Version 5.1
#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Register AI-RISA pipeline tasks with Windows Task Scheduler.
    
.DESCRIPTION
    Creates or updates two scheduled tasks:
    - AI-RISA Pipeline Normal Run (daily at 6:00 AM)
    - AI-RISA Pipeline Dry-Run (daily at 5:00 AM)
    
    All settings are configurable and non-hardcoded. Tasks reference launcher scripts
    that maintain timestamped run-history and run index.
    
.PARAMETER RepoRoot
    Repository root path (default: C:\ai_risa_data)
    
.PARAMETER NormalRunTime
    Time for normal run task (format: HH:mm, default: 14:00 = 2:00 PM)
    
.PARAMETER DryRunTime
    Time for dry-run task (format: HH:mm, default: 13:00 = 1:00 PM)
    
.PARAMETER TaskFolder
    Task Scheduler folder for tasks (default: \AI-RISA\)
    
.PARAMETER Username
    Username to run tasks as (default: SYSTEM)
    
.PARAMETER Enable
    Create or enable tasks (default: $true)
    
.PARAMETER Disable
    Disable tasks without removing them
    
.PARAMETER Remove
    Remove tasks entirely (dangerous!)
    
.PARAMETER List
    List current task status
    
.EXAMPLE
    .\register_pipeline_tasks.ps1 -List
    
.EXAMPLE
    .\register_pipeline_tasks.ps1 -NormalRunTime 14:00 -DryRunTime 13:00
    
.EXAMPLE
    .\register_pipeline_tasks.ps1 -Enable
    
.EXAMPLE
    .\register_pipeline_tasks.ps1 -Disable
#>

param(
    [string]$RepoRoot = 'C:\ai_risa_data',
    [string]$NormalRunTime = '14:00',      # 2:00 PM
    [string]$DryRunTime = '13:00',         # 1:00 PM
    [string]$TaskFolder = '\AI-RISA\',
    [string]$Username = 'SYSTEM',
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Remove,
    [switch]$List
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# ============================================================================
# Configuration
# ============================================================================

$tasks = @(
    @{
        Name = 'AI-RISA-Pipeline-Normal-Run'
        DisplayName = 'AI-RISA Pipeline Normal Run'
        Description = 'Executes AI-RISA full pipeline with report generation'
        Launcher = Join-Path $RepoRoot 'schedule_full_pipeline_run.ps1'
        Schedule = $NormalRunTime
        Mode = 'normal'
    },
    @{
        Name = 'AI-RISA-Pipeline-Dry-Run'
        DisplayName = 'AI-RISA Pipeline Dry-Run'
        Description = 'Executes AI-RISA pipeline in dry-run mode (safe verification)'
        Launcher = Join-Path $RepoRoot 'schedule_full_pipeline_dry_run.ps1'
        Schedule = $DryRunTime
        Mode = 'dry-run'
    }
)

# ============================================================================
# Helper functions
# ============================================================================

function Test-AdminPrivilege {
    $principal = [Security.Principal.WindowsPrincipal]([Security.Principal.WindowsIdentity]::GetCurrent())
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-TaskStatus {
    param([string]$TaskName)
    
    try {
        $task = Get-ScheduledTask -TaskPath $TaskFolder -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($null -eq $task) {
            return 'Not registered'
        }
        
        $state = $task.State
        $lastRun = $task.LastRunTime
        $nextRun = $task.NextRunTime
        # Some PowerShell versions expose Enabled on task.Settings instead of task.Enabled.
        if ($task.PSObject.Properties.Name -contains 'Enabled') {
            $enabled = [bool]$task.Enabled
        }
        elseif ($task.Settings -and ($task.Settings.PSObject.Properties.Name -contains 'Enabled')) {
            $enabled = [bool]$task.Settings.Enabled
        }
        else {
            $enabled = $true
        }
        
        return @{
            State = $state
            Enabled = $enabled
            LastRun = $lastRun
            NextRun = $nextRun
        }
    }
    catch {
        return 'Error querying'
    }
}

function Register-PipelineTask {
    param(
        [hashtable]$Task,
        [string]$TaskFolder,
        [string]$Username
    )
    
    $taskName = $Task.Name
    $displayName = $Task.DisplayName
    $description = $Task.Description
    $launcher = $Task.Launcher
    $schedule = $Task.Schedule
    
    # Validate launcher exists
    if (-not (Test-Path $launcher)) {
        Write-Error "Launcher not found: $launcher"
        return $false
    }
    
    # Parse schedule time
    $timeParts = $schedule -split ':'
    if ($timeParts.Count -ne 2) {
        Write-Error "Invalid schedule format: $schedule (use HH:mm)"
        return $false
    }
    
    $hour = [int]$timeParts[0]
    $minute = [int]$timeParts[1]
    
    if ($hour -lt 0 -or $hour -gt 23 -or $minute -lt 0 -or $minute -gt 59) {
        Write-Error "Invalid time: $schedule"
        return $false
    }
    
    # Create task folder if not exists
    try {
        $existingFolder = Get-ScheduledTaskFolder -Path $TaskFolder -ErrorAction SilentlyContinue
        if ($null -eq $existingFolder) {
            $rootFolder = Get-ScheduledTaskFolder -Path '\' -ErrorAction SilentlyContinue
            if ($rootFolder) {
                $folderName = $TaskFolder.Trim('\').Split('\') | Select-Object -Last 1
                $rootFolder | New-ScheduledTaskFolder -Name $folderName -ErrorAction SilentlyContinue | Out-Null
            }
        }
    }
    catch {
        Write-Warning "Could not create task folder: $TaskFolder"
    }
    
    # Remove existing task if present
    try {
        Unregister-ScheduledTask -TaskPath $TaskFolder -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    }
    catch {}
    
    # Build trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger -Daily -At "$($hour):$($minute.ToString('00'))"
    
    # Build action (execute PowerShell launcher)
    $action = New-ScheduledTaskAction `
        -Execute 'PowerShell.exe' `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$launcher`""
    
    # Build principal (run as system or specified user)
    $principal = New-ScheduledTaskPrincipal `
        -UserID $Username `
        -LogonType ServiceAccount
    
    # Build settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false
    
    # Register task
    try {
        Register-ScheduledTask `
            -TaskPath $TaskFolder `
            -TaskName $taskName `
            -Trigger $trigger `
            -Action $action `
            -Principal $principal `
            -Settings $settings `
            -Description $description `
            -Force | Out-Null

        # Ensure task is enabled after (re)registration.
        Enable-ScheduledTask -TaskPath $TaskFolder -TaskName $taskName -ErrorAction SilentlyContinue | Out-Null
        
        Write-Host "REGISTERED: $displayName" -ForegroundColor Green
        Write-Host "  Path: $TaskFolder$taskName"
        Write-Host "  Launcher: $launcher"
        Write-Host "  Schedule: Daily at $($hour):$($minute.ToString('00'))"
        Write-Host "  Run as: $Username"
        
        return $true
    }
    catch {
        Write-Error "Failed to register task: $_"
        return $false
    }
}

function Set-TaskState {
    param(
        [string]$TaskName,
        [string]$TaskFolder,
        [bool]$Enabled
    )
    
    try {
        $task = Get-ScheduledTask -TaskPath $TaskFolder -TaskName $TaskName -ErrorAction Stop
        if ($Enabled) {
            Enable-ScheduledTask -InputObject $task | Out-Null
            Write-Host "ENABLED: $TaskName" -ForegroundColor Green
        }
        else {
            Disable-ScheduledTask -InputObject $task | Out-Null
            Write-Host "DISABLED: $TaskName" -ForegroundColor Yellow
        }
        return $true
    }
    catch {
        Write-Error "Failed to set task state: $_"
        return $false
    }
}

function Remove-PipelineTask {
    param(
        [string]$TaskName,
        [string]$TaskFolder
    )
    
    try {
        Unregister-ScheduledTask -TaskPath $TaskFolder -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "REMOVED: $TaskName" -ForegroundColor Yellow
        return $true
    }
    catch {
        Write-Error "Failed to remove task: $_"
        return $false
    }
}

# ============================================================================
# Main
# ============================================================================

Write-Host "`n=== AI-RISA Pipeline Task Scheduler Manager ===" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"
Write-Host "Task Folder: $TaskFolder`n"

if (-not (Test-AdminPrivilege)) {
    Write-Error "This script requires administrator privileges. Please run as Administrator."
    exit 1
}

if (-not (Test-Path $RepoRoot)) {
    Write-Error "Repository root does not exist: $RepoRoot"
    exit 1
}

# ========================================================================
# List current status
# ========================================================================

if ($List -or (-not $Enable -and -not $Disable -and -not $Remove)) {
    Write-Host "Current Task Status:" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($task in $tasks) {
        $name = $task.Name
        $displayName = $task.DisplayName
        $status = Get-TaskStatus -TaskName $name
        
        if ($status -eq 'Not registered') {
            Write-Host "  [$name]" -ForegroundColor Gray
            Write-Host "    Status: Not registered" -ForegroundColor Gray
        }
        elseif ($status -eq 'Error querying') {
            Write-Host "  [$name]" -ForegroundColor Red
            Write-Host "    Status: Error (may not have permissions to query)" -ForegroundColor Red
        }
        else {
            $enabled = if ($status.Enabled) { "ENABLED" } else { "DISABLED" }
            $enableColor = if ($status.Enabled) { "Green" } else { "Yellow" }
            
            Write-Host "  [$name]" -ForegroundColor Cyan
            Write-Host "    $enabled" -ForegroundColor $enableColor
            Write-Host "    State: $($status.State)"
            if ($status.LastRun) { Write-Host "    Last run: $($status.LastRun)" }
            if ($status.NextRun) { Write-Host "    Next run: $($status.NextRun)" }
        }
        Write-Host ""
    }
}

# ========================================================================
# Enable tasks
# ========================================================================

if ($Enable) {
    Write-Host "Enabling tasks..." -ForegroundColor Cyan
    Write-Host ""
    
    $registerSuccess = 0
    
    foreach ($task in $tasks) {
        if (Register-PipelineTask -Task $task -TaskFolder $TaskFolder -Username $Username) {
            $registerSuccess++
        }
        Write-Host ""
    }
    
    if ($registerSuccess -eq $tasks.Count) {
        Write-Host "All tasks registered successfully." -ForegroundColor Green
        exit 0
    }
    else {
        Write-Error "One or more tasks failed to register."
        exit 1
    }
}

# ========================================================================
# Disable tasks
# ========================================================================

if ($Disable) {
    Write-Host "Disabling tasks..." -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($task in $tasks) {
        Set-TaskState -TaskName $task.Name -TaskFolder $TaskFolder -Enabled $false
    }
    
    Write-Host ""
    Write-Host "Tasks disabled. They can be re-enabled with: register_pipeline_tasks.ps1 -Enable" -ForegroundColor Green
    exit 0
}

# ========================================================================
# Remove tasks (with confirmation)
# ========================================================================

if ($Remove) {
    Write-Host "WARNING: This will permanently remove all AI-RISA pipeline tasks." -ForegroundColor Red
    $confirm = Read-Host "Type 'yes' to confirm removal"
    
    if ($confirm -ne 'yes') {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host "Removing tasks..." -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($task in $tasks) {
        Remove-PipelineTask -TaskName $task.Name -TaskFolder $TaskFolder
    }
    
    Write-Host ""
    Write-Host "Tasks removed." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

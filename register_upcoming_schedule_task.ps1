# register_upcoming_schedule_task.ps1
# Deterministic Windows Task Scheduler registration for upcoming schedule cadence launcher

$TaskName = "AI-RISA-Upcoming-Schedule-Cadence"
$FullTaskName = $TaskName

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$Launcher = Join-Path $ScriptRoot "run_upcoming_schedule_cadence.bat"
if (!(Test-Path $Launcher)) {
    Write-Error "Launcher script not found: $Launcher"
    exit 1
}
$Action = New-ScheduledTaskAction -Execute $Launcher
$Trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date).Date
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Remove existing task if present (idempotent)
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}


# Register the task, fail loudly if registration fails
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Description "AI-RISA: Upcoming schedule cadence automation (every 15 min, gated by repo cadence/lock)" -ErrorAction Stop | Out-Null
} catch {
    Write-Error "Task registration failed: $_"
    exit 2
}

# Verify the task exists immediately after registration
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if (-not $task) {
    Write-Error "Task verification failed: Task '$TaskName' not found after registration."
    exit 3
}

# Emit artifacts reflecting real success
$artifactJson = Join-Path $ScriptRoot "ops/events/upcoming_schedule_task_registration.json"
$artifactMd = Join-Path $ScriptRoot "ops/events/upcoming_schedule_task_registration.md"
$now = Get-Date -Format o
$def = $task | Get-ScheduledTaskInfo
$actionPath = $task.Actions[0].Execute
$actionArgs = $task.Actions[0].Arguments

$regObj = [ordered]@{
    timestamp = $now
    task_name = $TaskName
    action = $actionPath
    arguments = $actionArgs
    trigger = "every 15 min"
    principal = $task.Principal.UserId
    state = $def.State
    last_run_time = $def.LastRunTime
    next_run_time = $def.NextRunTime
    exit_code = $def.LastTaskResult
    registration_success = $true
}
$regObj | ConvertTo-Json -Depth 4 | Set-Content -Encoding UTF8 $artifactJson

@(
    "# Upcoming Schedule Task Registration",
    "",
    "Registered at: $now",
    "Task name: $TaskName",
    "Action: $actionPath $actionArgs",
    "Trigger: every 15 min",
    "Principal: $($task.Principal.UserId)",
    "State: $($def.State)",
    "Last run: $($def.LastRunTime)",
    "Next run: $($def.NextRunTime)",
    "Exit code: $($def.LastTaskResult)",
    "Registration success: $true"
) | Set-Content -Encoding UTF8 $artifactMd

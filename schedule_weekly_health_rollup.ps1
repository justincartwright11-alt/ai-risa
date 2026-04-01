#Requires -Version 5.1
<#
.SYNOPSIS
    Run AI-RISA weekly health rollup and refresh operator summary.
#>

param(
    [string]$RepoRoot = 'C:\ai_risa_data',
    [int]$Days = 7,
    [switch]$RefreshOperatorSummary = $true,
    [switch]$RunSchedulerVerification = $true,
    [switch]$GenerateChecklist = $true,
    [string]$LogDir = (Join-Path $RepoRoot 'ops\logs')
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Write-Log {
    param(
        [string]$LogFile,
        [string]$Message
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Resolve-PythonCommand {
    if ($env:AI_RISA_PYTHON -and (Test-Path $env:AI_RISA_PYTHON)) {
        return @{ Exe = $env:AI_RISA_PYTHON; PrefixArgs = @() }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return @{ Exe = $pythonCmd.Source; PrefixArgs = @() }
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return @{ Exe = $pyCmd.Source; PrefixArgs = @('-3') }
    }

    $fallbackPatterns = @(
        'C:\Program Files\Python*\python.exe',
        'C:\Python*\python.exe',
        'C:\Users\*\AppData\Local\Programs\Python\Python*\python.exe',
        'C:\Users\*\AppData\Local\Python\*\python.exe'
    )

    foreach ($pattern in $fallbackPatterns) {
        $candidate = Get-ChildItem -Path $pattern -File -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending |
            Select-Object -First 1
        if ($candidate) {
            return @{ Exe = $candidate.FullName; PrefixArgs = @() }
        }
    }

    throw 'Python runtime not found. Install python/py launcher or set AI_RISA_PYTHON.'
}

if (-not (Test-Path $RepoRoot)) {
    Write-Error "Repository root does not exist: $RepoRoot"
    exit 1
}

if (-not (Test-Path $LogDir)) {
    New-Item -Path $LogDir -ItemType Directory -Force | Out-Null
}

$logFile = Join-Path $LogDir 'weekly_health_rollup.log'

try {
    Push-Location $RepoRoot

    $python = Resolve-PythonCommand

    Write-Log -LogFile $logFile -Message '=== AI-RISA Ops: Weekly Health Rollup ==='
    Write-Log -LogFile $logFile -Message "Executing: $($python.Exe) .\generate_weekly_health_rollup.py --days $Days"

    $outputWeekly = & $python.Exe @($python.PrefixArgs) .\generate_weekly_health_rollup.py --days $Days 2>&1
    $weeklyExit = $LASTEXITCODE

    foreach ($line in $outputWeekly) {
        Write-Log -LogFile $logFile -Message "  $line"
    }

    $operatorExit = 0
    if ($RefreshOperatorSummary) {
        Write-Log -LogFile $logFile -Message "Executing: $($python.Exe) .\generate_operator_summary_artifact.py"
        $outputOperator = & $python.Exe @($python.PrefixArgs) .\generate_operator_summary_artifact.py 2>&1
        $operatorExit = $LASTEXITCODE

        foreach ($line in $outputOperator) {
            Write-Log -LogFile $logFile -Message "  $line"
        }
    }

    $verifyExit = 0
    if ($RunSchedulerVerification) {
        Write-Log -LogFile $logFile -Message "Executing: $($python.Exe) .\verify_scheduler_tasks.py"
        $verifyOutput = & $python.Exe @($python.PrefixArgs) .\verify_scheduler_tasks.py 2>&1
        $verifyExit = $LASTEXITCODE

        foreach ($line in $verifyOutput) {
            Write-Log -LogFile $logFile -Message "  $line"
        }
    }

    $checklistExit = 0
    if ($GenerateChecklist) {
        Write-Log -LogFile $logFile -Message "Executing: $($python.Exe) .\generate_operator_checklist.py --period weekly"
        $checklistOutput = & $python.Exe @($python.PrefixArgs) .\generate_operator_checklist.py --period weekly 2>&1
        $checklistExit = $LASTEXITCODE

        foreach ($line in $checklistOutput) {
            Write-Log -LogFile $logFile -Message "  $line"
        }
    }

    $finalExit = $weeklyExit
    if ($finalExit -eq 0) { $finalExit = $operatorExit }
    if ($finalExit -eq 0) { $finalExit = $verifyExit }
    if ($finalExit -eq 0) { $finalExit = $checklistExit }
    Write-Log -LogFile $logFile -Message "Exit code: $finalExit"
    Write-Log -LogFile $logFile -Message '=== Execution complete ==='

    Pop-Location
    exit $finalExit
}
catch {
    Write-Log -LogFile $logFile -Message "ERROR: $_"
    Write-Log -LogFile $logFile -Message "Stack: $($_.ScriptStackTrace)"
    Pop-Location
    exit 1
}

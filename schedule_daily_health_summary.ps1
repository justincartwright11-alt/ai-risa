#Requires -Version 5.1
<#
.SYNOPSIS
    Run AI-RISA daily health summary aggregation and write ops artifacts.
#>

param(
    [string]$RepoRoot = 'C:\ai_risa_data',
    [int]$Hours = 24,
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

$logFile = Join-Path $LogDir 'daily_health_summary.log'

try {
    Push-Location $RepoRoot

    $python = Resolve-PythonCommand

    Write-Log -LogFile $logFile -Message '=== AI-RISA Ops: Daily Health Summary ==='
    Write-Log -LogFile $logFile -Message "Executing: $($python.Exe) .\generate_daily_health_summary.py --hours $Hours"

    $output = & $python.Exe @($python.PrefixArgs) .\generate_daily_health_summary.py --hours $Hours 2>&1
    $exitCode = $LASTEXITCODE

    foreach ($line in $output) {
        Write-Log -LogFile $logFile -Message "  $line"
    }

    Write-Log -LogFile $logFile -Message "Exit code: $exitCode"
    Write-Log -LogFile $logFile -Message '=== Execution complete ==='

    Pop-Location
    exit $exitCode
}
catch {
    Write-Log -LogFile $logFile -Message "ERROR: $_"
    Write-Log -LogFile $logFile -Message "Stack: $($_.ScriptStackTrace)"
    Pop-Location
    exit 1
}

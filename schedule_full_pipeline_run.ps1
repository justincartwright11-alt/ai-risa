#Requires -Version 5.1
<#
.SYNOPSIS
    Launcher for normal AI-RISA pipeline execution with timestamped run-history.
    
.DESCRIPTION
    - Creates timestamped run folder (YYYY-MM-DD_HHMMSS)
    - Executes full pipeline with report formats
    - Stores summaries + log in run folder
    - Updates run index (append-only)
    - Preserves exit codes for Task Scheduler detection
    
.PARAMETER RepoRoot
    Repository root path (default: C:\ai_risa_data)
    
.PARAMETER Formats
    Report formats to generate (default: md docx pdf)
    
.PARAMETER RunsDir
    Timestamped runs storage directory (default: $RepoRoot\runs)
    
.PARAMETER IndexFile
    Run history index file (default: $RunsDir\run_history_index.json)
    
.EXAMPLE
    .\schedule_full_pipeline_run.ps1
    
.EXAMPLE
    .\schedule_full_pipeline_run.ps1 -RepoRoot 'D:\ai_risa' -Formats 'md pdf'
#>

param(
    [string]$RepoRoot = 'C:\ai_risa_data',
    [string]$Formats = 'md docx pdf',
    [string]$RunsDir = (Join-Path $RepoRoot 'runs'),
    [string]$IndexFile = (Join-Path $RunsDir 'run_history_index.json')
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# ============================================================================
# Setup
# ============================================================================

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$runFolder = Join-Path $RunsDir $timestamp
$logFile = Join-Path $runFolder 'launcher.log'

# Ensure repo and runs structure exist
if (-not (Test-Path $RepoRoot)) {
    Write-Error "Repository root does not exist: $RepoRoot"
    exit 1
}

if (-not (Test-Path $RunsDir)) {
    New-Item -Path $RunsDir -ItemType Directory -Force | Out-Null
}

if (-not (Test-Path $runFolder)) {
    New-Item -Path $runFolder -ItemType Directory -Force | Out-Null
}

# ============================================================================
# Logging function
# ============================================================================

function Write-Log {
    param([string]$Message)
    $timestamp_log = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logLine = "[$timestamp_log] $Message"
    Write-Host $logLine
    Add-Content -Path $logFile -Value $logLine -Encoding UTF8
}

function Resolve-PythonCommand {
    # Prefer explicit override, then python.exe, then py.exe launcher.
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

    throw "Python runtime not found. Install python/py launcher or set AI_RISA_PYTHON."
}

# ============================================================================
# Execute pipeline
# ============================================================================

Write-Log "=== AI-RISA Pipeline: NORMAL RUN ==="
Write-Log "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log "Run folder: $runFolder"
Write-Log "Formats: $Formats"

try {
    Push-Location $RepoRoot

    $python = Resolve-PythonCommand
    
    # Build command
    $cmdParts = @($python.Exe) + @($python.PrefixArgs) + @('.\run_full_pipeline_auto.py')
    foreach ($format in $Formats.Split()) {
        $cmdParts += '--formats', $format
    }
    $cmd = $cmdParts -join ' '
    
    Write-Log "Executing: $cmd"
    
    # Run pipeline and capture exit code
    $processOutput = & $python.Exe @($python.PrefixArgs) .\run_full_pipeline_auto.py --formats $($Formats.Split(' ')) 2>&1
    $exitCode = $LASTEXITCODE
    
    # Log pipeline output
    Write-Log "Pipeline output:"
    foreach ($line in $processOutput) {
        Write-Log "  $line"
    }
    
    Write-Log "Exit code: $exitCode"
    
    if ($exitCode -ne 0) {
        Write-Log "WARNING: Pipeline exited with non-zero code: $exitCode"
    }
    
    # ========================================================================
    # Collect artifacts
    # ========================================================================
    
    Write-Log "Collecting artifacts..."
    
    $outputDir = Join-Path $RepoRoot 'output'
    $incomingDir = Join-Path $RepoRoot 'incoming'
    
    # Copy master summary
    if (Test-Path (Join-Path $outputDir 'full_pipeline_run_summary.json')) {
        Copy-Item (Join-Path $outputDir 'full_pipeline_run_summary.json') `
                  (Join-Path $runFolder 'full_pipeline_run_summary.json') -Force
        Write-Log "Copied: full_pipeline_run_summary.json"
    }
    
    # Copy stage summaries (without assuming all exist)
    $stageSummaries = @(
        'upcoming_auto_summary.json',
        'dependency_resolution_summary.json',
        'prediction_queue_build_summary.json',
        'prediction_queue_run_summary.json',
        'event_batch_run_summary.json'
    )
    
    foreach ($summary in $stageSummaries) {
        $sourcePath = Join-Path $outputDir $summary
        if (Test-Path $sourcePath) {
            Copy-Item $sourcePath (Join-Path $runFolder $summary) -Force
            Write-Log "Copied: $summary"
        }
    }
    
    # Copy ingest summary if exists
    $ingestSummary = Join-Path $incomingDir 'upcoming_events_ingest_summary.json'
    if (Test-Path $ingestSummary) {
        Copy-Item $ingestSummary (Join-Path $runFolder 'upcoming_events_ingest_summary.json') -Force
        Write-Log "Copied: upcoming_events_ingest_summary.json"
    }
    
    # ========================================================================
    # Update run index
    # ========================================================================
    
    Write-Log "Updating run index..."
    
    $runRecord = @{
        timestamp = $timestamp
        run_path = $runFolder
        mode = 'normal'
        exit_code = $exitCode
        status = if ($exitCode -eq 0) { 'success' } else { 'failed' }
        started_at = Get-Date -Format 'o'
        completed_at = Get-Date -Format 'o'
        launcher_log = $logFile
    }
    
    # Load or create index
    $index = @()
    if (Test-Path $IndexFile) {
        $indexContent = Get-Content $IndexFile -Raw -ErrorAction SilentlyContinue
        if ($indexContent) {
                $parsedIndex = $indexContent | ConvertFrom-Json
                if ($parsedIndex -is [System.Array]) {
                    $index = @($parsedIndex)
                }
                elseif ($null -ne $parsedIndex) {
                    $index = @($parsedIndex)
                }
        }
    }
    
    # Append record
    $index += $runRecord
    
    # Write back (UTF-8 without BOM for Python compatibility)
        $json = ConvertTo-Json -InputObject @($index) -Depth 10
    [System.IO.File]::WriteAllText($IndexFile, $json, [System.Text.UTF8Encoding]$false)
    
    Write-Log "Run index updated: $IndexFile ($($index.Count) runs recorded)"
    
    Write-Log "=== Execution complete ==="
    Write-Log "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Log "Status: $($runRecord.status)"
    
    Pop-Location
    exit $exitCode
    
}
catch {
    Write-Log "ERROR: $_"
    Write-Log "Stack: $($_.ScriptStackTrace)"
    Pop-Location
    exit 1
}

#Requires -Version 5.1
<#
.SYNOPSIS
    Elevation wrapper for task registration (requests admin privilege).
#>

$scriptPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'register_pipeline_tasks.ps1'

if (-not (Test-Path $scriptPath)) {
    Write-Error "Registration script not found: $scriptPath"
    exit 1
}

Write-Host "Requesting administrator privilege to register scheduler tasks..." -ForegroundColor Cyan
Write-Host ""

Start-Process `
    -FilePath 'powershell.exe' `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$scriptPath`"", "-Enable") `
    -Verb RunAs `
    -Wait

$exitCode = $LASTEXITCODE
Write-Host ""
Write-Host "Registration completed with exit code: $exitCode" -ForegroundColor $(if($exitCode -eq 0) { 'Green' } else { 'Red' })

exit $exitCode

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\jusin\OneDrive\Documents\Custom Office Templates"
$msysBin = "C:\msys64\ucrt64\bin"
$pythonExe = "C:\Users\jusin\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$pdfOutputRoot = "C:\Users\jusin\OneDrive\Documents\Custom Office Templates\reports"

Set-Location $repoRoot
$env:PATH = "$msysBin;$($env:PATH)"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:BUTTON2_PDF_OUTPUT_ROOT = $pdfOutputRoot

if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw "Python runtime not found at: $pythonExe"
}

Write-Host "Starting AI-RISA dashboard on http://127.0.0.1:5050" -ForegroundColor Cyan
Write-Host "BUTTON2_PDF_OUTPUT_ROOT=$env:BUTTON2_PDF_OUTPUT_ROOT" -ForegroundColor DarkCyan

& $pythonExe -c "import os; os.add_dll_directory(r'C:\msys64\ucrt64\bin'); from operator_dashboard.app import app; app.run(debug=False, port=5050)"

param(
    [Parameter(Mandatory = $true)]
    [string]$DocxPath,

    [Parameter(Mandatory = $false)]
    [string]$PdfPath
)

$ErrorActionPreference = "Stop"

function Test-RealPdf {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (!(Test-Path $Path)) {
        throw "PDF was not created: $Path"
    }

    $item = Get-Item $Path
    if ($item.Length -lt 1024) {
        throw "PDF exists but is too small to be valid: $($item.Length) bytes"
    }

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    if ($bytes.Length -lt 5) {
        throw "PDF exists but is too short to validate"
    }

    $header = [System.Text.Encoding]::ASCII.GetString($bytes[0..4])
    if ($header -ne "%PDF-") {
        throw "Invalid PDF header. Expected %PDF-, got: $header"
    }

    return $true
}

$DocxPath = [System.IO.Path]::GetFullPath($DocxPath)

if (!(Test-Path $DocxPath)) {
    throw "DOCX not found: $DocxPath"
}

if ([System.IO.Path]::GetExtension($DocxPath).ToLower() -ne ".docx") {
    throw "Source file must be a .docx: $DocxPath"
}

if ([string]::IsNullOrWhiteSpace($PdfPath)) {
    $PdfPath = [System.IO.Path]::ChangeExtension($DocxPath, ".pdf")
} else {
    $PdfPath = [System.IO.Path]::GetFullPath($PdfPath)
}

$word = $null
$document = $null

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    $document = $word.Documents.Open($DocxPath, $false, $true)

    if (Test-Path $PdfPath) {
        Remove-Item $PdfPath -Force
    }

    # 17 = wdExportFormatPDF
    $document.ExportAsFixedFormat(
        $PdfPath,
        17,     # ExportFormat PDF
        $false, # OpenAfterExport
        0,      # OptimizeFor Print
        0,      # Range AllDocument
        1,      # From
        1,      # To
        0,      # Item DocumentContent
        $true,  # IncludeDocProps
        $true,  # KeepIRM
        0,      # CreateBookmarks NoBookmarks
        $true,  # DocStructureTags
        $true,  # BitmapMissingFonts
        $false  # UseISO19005_1
    )

    $document.Close($false)
    $document = $null

    $word.Quit()
    $word = $null

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    Test-RealPdf -Path $PdfPath | Out-Null

    Write-Host "DOCX: $DocxPath"
    Write-Host "PDF:  $PdfPath"
    Write-Host "Status: OK"
    exit 0
}
catch {
    if ($document -ne $null) {
        try { $document.Close($false) } catch {}
    }
    if ($word -ne $null) {
        try { $word.Quit() } catch {}
    }

    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()

    Write-Error $_.Exception.Message
    exit 1
}

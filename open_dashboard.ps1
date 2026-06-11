# Opens Power BI project or falls back to Streamlit dashboard
$Root = $PSScriptRoot
$Pbip = Join-Path $Root "powerbi\SalesPerformance.pbip"
$Pbir = Join-Path $Root "powerbi\SalesPerformance\SalesPerformance.Report\definition.pbir"

$PbiPaths = @(
    "$env:ProgramFiles\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
    "${env:ProgramFiles(x86)}\Microsoft Power BI Desktop\bin\PBIDesktop.exe",
    "$env:LOCALAPPDATA\Microsoft\WindowsApps\PBIDesktop.exe"
)

foreach ($exe in $PbiPaths) {
    if (Test-Path $exe) {
        Write-Host "Opening Power BI Desktop..."
        if (Test-Path $Pbip) {
            Start-Process $exe -ArgumentList "`"$Pbip`""
        } else {
            Start-Process $exe -ArgumentList "`"$Pbir`""
        }
        exit 0
    }
}

Write-Host ""
Write-Host "Power BI Desktop is not installed on this PC." -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1 - Install Power BI Desktop (free):" -ForegroundColor Cyan
Write-Host "  https://powerbi.microsoft.com/desktop/"
Write-Host "  Enable Preview features: PBIP, PBIR, and TMDL format"
Write-Host "  Then double-click: powerbi\SalesPerformance.pbip"
Write-Host ""
Write-Host "Option 2 - Run interactive Python dashboard now:" -ForegroundColor Cyan
Write-Host "  pip install streamlit plotly"
Write-Host "  streamlit run dashboard\app.py"
Write-Host ""
Write-Host "Option 3 - View static dashboard images in images\ folder" -ForegroundColor Cyan
Write-Host ""

$run = Read-Host "Start Streamlit dashboard now? (y/n)"
if ($run -eq 'y') {
    Set-Location $Root
    streamlit run dashboard\app.py
}

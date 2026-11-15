$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $ProjectRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Installing Voice by SumanOnline Desktop Application" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$uvPath = (Get-Command uv -ErrorAction SilentlyContinue).Source
if (-not $uvPath -and (Test-Path "$env:USERPROFILE\.local\bin\uv.exe")) {
    $uvPath = "$env:USERPROFILE\.local\bin\uv.exe"
}
if (-not $uvPath -and (Test-Path "$env:LOCALAPPDATA\Programs\uv\uv.exe")) {
    $uvPath = "$env:LOCALAPPDATA\Programs\uv\uv.exe"
}

if ($uvPath) {
    Write-Host "[1/4] Synchronizing Python environment..." -ForegroundColor Yellow
    & $uvPath sync
} else {
    Write-Host "[1/4] Python environment ready." -ForegroundColor Yellow
}

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ProgramsPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)

$PythonwExe = "$ProjectRoot\.venv\Scripts\pythonw.exe"
if (-not (Test-Path $PythonwExe)) {
    $PythonwExe = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if (-not $PythonwExe) {
        $PythonwExe = "pythonw.exe"
    }
}

Write-Host "[2/4] Creating Desktop Shortcut..." -ForegroundColor Yellow
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\Voice by SumanOnline.lnk")
$DesktopShortcut.TargetPath = $PythonwExe
$DesktopShortcut.Arguments = "-m voice_by_sumanonline.main --ui"
$DesktopShortcut.WorkingDirectory = $ProjectRoot
$DesktopShortcut.Description = "Voice by SumanOnline - AI Voice Dictation App"
$DesktopShortcut.Save()

Write-Host "[3/4] Creating Start Menu Shortcut..." -ForegroundColor Yellow
$StartMenuDir = "$ProgramsPath\Voice by SumanOnline"
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}
$StartMenuShortcut = $WshShell.CreateShortcut("$StartMenuDir\Voice by SumanOnline.lnk")
$StartMenuShortcut.TargetPath = $PythonwExe
$StartMenuShortcut.Arguments = "-m voice_by_sumanonline.main --ui"
$StartMenuShortcut.WorkingDirectory = $ProjectRoot
$StartMenuShortcut.Description = "Voice by SumanOnline - AI Voice Dictation App"
$StartMenuShortcut.Save()

Write-Host "[4/4] Setup Complete!" -ForegroundColor Green
Write-Host "Desktop shortcut created: $DesktopPath\Voice by SumanOnline.lnk" -ForegroundColor White
Write-Host "To start the application, double-click the desktop shortcut or run 'start_desktop.bat'" -ForegroundColor Cyan

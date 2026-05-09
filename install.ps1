# Whisper PTT installer
# Run from the project folder in PowerShell.
# Installs deps, sets up CUDA DLLs adjacent to the script, registers Startup shortcut.

$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
Write-Host "`n=== Whisper PTT installer ===" -ForegroundColor Cyan
Write-Host "Project dir: $projectDir`n"

# 1. Verify GPU
Write-Host "[1/5] Checking NVIDIA GPU..." -ForegroundColor Cyan
try {
    nvidia-smi | Select-Object -First 3
} catch {
    Write-Host "  WARNING: nvidia-smi not found. PTT will fall back to CPU." -ForegroundColor Yellow
    Write-Host "  Edit whisper_ptt.py: DEVICE = 'cpu', COMPUTE_TYPE = 'int8'" -ForegroundColor Yellow
}

# 2. Install Python deps
Write-Host "`n[2/5] Installing Python dependencies..." -ForegroundColor Cyan
pip install -r (Join-Path $projectDir "requirements.txt")

# 3. Copy CUDA DLLs adjacent to the script (Windows DLL search-path workaround)
Write-Host "`n[3/5] Staging CUDA DLLs next to script..." -ForegroundColor Cyan
$sitePackages = python -c "import sysconfig; print(sysconfig.get_paths()['purelib'])"
$nvDir = Join-Path $sitePackages "nvidia"
if (-not (Test-Path $nvDir)) {
    Write-Host "  ERROR: nvidia package folder not found at $nvDir" -ForegroundColor Red
    Write-Host "  Did 'pip install nvidia-cublas-cu12' succeed?" -ForegroundColor Red
    exit 1
}
$count = 0
Get-ChildItem -Path $nvDir -Recurse -Filter "*.dll" | ForEach-Object {
    Copy-Item $_.FullName -Destination $projectDir -Force
    $count++
}
Write-Host "  Copied $count DLLs into $projectDir" -ForegroundColor Green

# 4. Generate silent launcher (VBS)
Write-Host "`n[4/5] Generating silent launcher..." -ForegroundColor Cyan
$pyExe = (Get-Command python).Source
$pyDir = Split-Path $pyExe -Parent
$pyw = Join-Path $pyDir "pythonw.exe"
if (-not (Test-Path $pyw)) {
    Write-Host "  pythonw.exe not found, falling back to python.exe (will show window)" -ForegroundColor Yellow
    $pyw = $pyExe
}
$scriptPath = Join-Path $projectDir "whisper_ptt.py"
$logPath    = Join-Path $projectDir "whisper_ptt.log"
$vbsPath    = Join-Path $projectDir "whisper_ptt_launcher.vbs"
$vbsContent = "Set WshShell = CreateObject(`"WScript.Shell`")`r`nWshShell.Run `"`"`"$pyw`"`"`" `"`"`"$scriptPath`"`"`" > `"`"`"$logPath`"`"`" 2>&1`", 0, False"
Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII
Write-Host "  Wrote: $vbsPath" -ForegroundColor Green

# 5. Create Startup folder shortcut
Write-Host "`n[5/5] Registering Startup folder shortcut..." -ForegroundColor Cyan
$startup = [Environment]::GetFolderPath('Startup')
$shortcut = Join-Path $startup "WhisperPTT.lnk"
$wsh = New-Object -ComObject WScript.Shell
$lnk = $wsh.CreateShortcut($shortcut)
$lnk.TargetPath = "wscript.exe"
$lnk.Arguments  = "`"$vbsPath`""
$lnk.WorkingDirectory = $projectDir
$lnk.WindowStyle = 7
$lnk.Save()
Write-Host "  Created: $shortcut" -ForegroundColor Green

Write-Host "`n=== Install complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start now (without rebooting):" -ForegroundColor Yellow
Write-Host "  Double-click $shortcut" -ForegroundColor Yellow
Write-Host ""
Write-Host "Tray icon will appear (may be hidden behind ^ arrow on taskbar)." -ForegroundColor Yellow
Write-Host "Hold Left Shift, talk, release. Right-click tray icon to quit." -ForegroundColor Yellow
Write-Host "Logs: $logPath" -ForegroundColor Yellow

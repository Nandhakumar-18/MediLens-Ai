import os
import sys
import shutil

PROJECT_DIR = r'c:\Users\nandh\OneDrive\Documents\Project\MediLensAI'
DIST_DIR    = os.path.join(PROJECT_DIR, 'dist')
EXE_PATH    = os.path.join(DIST_DIR, 'MediLensAI_Setup.exe')
ICON_PATH   = os.path.join(PROJECT_DIR, 'static', 'img', 'icon-192.png')

# 1. Convert PNG icon to ICO for Windows Desktop Shortcut
ico_dest = os.path.join(DIST_DIR, 'app_icon.ico')
try:
    from PIL import Image
    img = Image.open(ICON_PATH)
    img.save(ico_dest, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"Created Windows ICO Icon at: {ico_dest}")
except Exception as e:
    print(f"ICO conversion warning: {e}")

# 2. Create Setup Installer PowerShell Script
ps1_script = r'''
$ErrorActionPreference = "Stop"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  MediLensAI Desktop App — Windows Setup Wizard         " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

$InstallDir = "$env:LOCALAPPDATA\Programs\MediLensAI"
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$StartMenuPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Programs)

Write-Host "[1/4] Creating installation directory at $InstallDir..." -ForegroundColor Yellow
if (-not (Test-Path $InstallDir)) {
    New-Item -Path $InstallDir -ItemType Directory -Force | Out-Null
}

$CurrentDir = $PSScriptRoot
if (-not $CurrentDir) { $CurrentDir = Get-Location }

$SourceExe = Join-Path $CurrentDir "MediLensAI_Setup.exe"
$DestExe = Join-Path $InstallDir "MediLensAI.exe"
$SourceIcon = Join-Path $CurrentDir "app_icon.ico"
$DestIcon = Join-Path $InstallDir "app_icon.ico"

Write-Host "[2/4] Copying MediLensAI application binaries..." -ForegroundColor Yellow
Copy-Item -Path $SourceExe -Destination $DestExe -Force
if (Test-Path $SourceIcon) {
    Copy-Item -Path $SourceIcon -Destination $DestIcon -Force
}

Write-Host "[3/4] Creating Desktop & Start Menu Shortcuts..." -ForegroundColor Yellow
$WshShell = New-Object -ComObject WScript.Shell

# Desktop Shortcut
$DesktopShortcut = $WshShell.CreateShortcut("$DesktopPath\MediLensAI.lnk")
$DesktopShortcut.TargetPath = $DestExe
$DesktopShortcut.WorkingDirectory = $InstallDir
if (Test-Path $DestIcon) { $DesktopShortcut.IconLocation = $DestIcon }
$DesktopShortcut.Description = "MediLensAI Offline Health Intelligence Desktop App"
$DesktopShortcut.Save()

# Start Menu Shortcut
$StartShortcut = $WshShell.CreateShortcut("$StartMenuPath\MediLensAI.lnk")
$StartShortcut.TargetPath = $DestExe
$StartShortcut.WorkingDirectory = $InstallDir
if (Test-Path $DestIcon) { $StartShortcut.IconLocation = $DestIcon }
$StartShortcut.Description = "MediLensAI Offline Health Intelligence Desktop App"
$StartShortcut.Save()

# Create Uninstaller Script
$UninstallScript = @"
@echo off
echo Uninstalling MediLensAI...
taskkill /F /IM MediLensAI.exe 2>nul
del "%USERPROFILE%\Desktop\MediLensAI.lnk" 2>nul
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\MediLensAI.lnk" 2>nul
rmdir /S /Q "$InstallDir" 2>nul
echo MediLensAI has been successfully removed from your computer.
pause
"@
Set-Content -Path (Join-Path $InstallDir "Uninstall.bat") -Value $UninstallScript

Write-Host "[4/4] Installation Complete! Launching MediLensAI..." -ForegroundColor Green
Start-Process -FilePath $DestExe

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS! MediLensAI is now installed on your PC.     " -ForegroundColor Green
Write-Host "  Desktop Shortcut created: MediLensAI.lnk              " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
'''

ps1_path = os.path.join(DIST_DIR, 'install.ps1')
with open(ps1_path, 'w', encoding='utf-8') as f:
    f.write(ps1_script)

# 3. Create 1-Click Batch Installer: MediLensAI_Windows_Setup.cmd
cmd_installer = r'''@echo off
title MediLensAI Windows Setup Wizard
color 0A
echo =======================================================
echo   MediLensAI Windows Setup Wizard
echo =======================================================
echo.
echo Installing MediLensAI to your computer...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation completed with warnings or status %ERRORLEVEL%.
)
pause
'''

cmd_path = os.path.join(DIST_DIR, 'MediLensAI_Windows_Setup.cmd')
with open(cmd_path, 'w', encoding='utf-8') as f:
    f.write(cmd_installer)

print(f"CREATED WINDOWS SETUP WIZARD SCRIPT AT: {cmd_path}")

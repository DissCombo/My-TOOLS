@echo off
title AnyDesk Installer
color 0A

echo ============================================
echo         AnyDesk - Auto Installer
echo ============================================
echo.

REM Check for Admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Needs Administrator rights. Restarting elevated...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo [OK] Running as Administrator.
echo.

REM Check internet
ping -n 1 8.8.8.8 >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] No internet connection. Please connect and retry.
    pause
    exit
)

echo [OK] Internet connected.
echo.
echo [*] Downloading AnyDesk from official source...

set "INSTALLER=%TEMP%\AnyDesk.exe"

REM Delete old installer if exists
if exist "%INSTALLER%" del "%INSTALLER%" >nul 2>&1

REM Download using PowerShell with TLS 1.2 forced (fixes most download failures)
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://download.anydesk.com/AnyDesk.exe', '%INSTALLER%')"

if not exist "%INSTALLER%" (
    echo [X] Download failed. Trying alternate method...
    bitsadmin /transfer AnyDeskDL /download /priority HIGH "https://download.anydesk.com/AnyDesk.exe" "%INSTALLER%"
)

if not exist "%INSTALLER%" (
    echo [X] Both download methods failed.
    echo     Please download manually from: https://anydesk.com/en/downloads/windows
    pause
    exit
)

echo [OK] Downloaded successfully.
echo.
echo [*] Installing AnyDesk...
echo     (A window may briefly appear - this is normal)
echo.

REM Run installer - tries silent first, then normal if that fails
"%INSTALLER%" --install --start-with-win --create-shortcuts --create-desktop-icon --silent >nul 2>&1

REM Wait for install to finish
timeout /t 8 >nul

REM Check all possible install locations
set "ANYDESK="
if exist "%ProgramFiles%\AnyDesk\AnyDesk.exe"       set "ANYDESK=%ProgramFiles%\AnyDesk\AnyDesk.exe"
if exist "%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe"  set "ANYDESK=%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe"
if exist "%APPDATA%\AnyDesk\AnyDesk.exe"             set "ANYDESK=%APPDATA%\AnyDesk\AnyDesk.exe"
if exist "%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"        set "ANYDESK=%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"

REM If still not found, try running it without --silent (visible install)
if not defined ANYDESK (
    echo [!] Silent install may have failed. Trying normal install...
    "%INSTALLER%" --install --start-with-win --create-shortcuts --create-desktop-icon
    timeout /t 15 >nul
)

REM Re-check after normal install
if exist "%ProgramFiles%\AnyDesk\AnyDesk.exe"       set "ANYDESK=%ProgramFiles%\AnyDesk\AnyDesk.exe"
if exist "%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe"  set "ANYDESK=%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe"
if exist "%APPDATA%\AnyDesk\AnyDesk.exe"             set "ANYDESK=%APPDATA%\AnyDesk\AnyDesk.exe"
if exist "%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"        set "ANYDESK=%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"

if defined ANYDESK (
    echo [OK] AnyDesk installed at: %ANYDESK%
    echo.
    echo [*] Launching AnyDesk...
    start "" "%ANYDESK%"
) else (
    echo [!] Could not find AnyDesk after install.
    echo     It may still have installed - check your Desktop or Start Menu.
    echo     Or try running the downloaded file manually: %INSTALLER%
    start "" "%INSTALLER%"
)

echo.
echo [*] Cleaning up...
timeout /t 3 >nul
del "%INSTALLER%" >nul 2>&1

echo.
echo ============================================
echo   Done! AnyDesk should now be open.
echo   Your AnyDesk ID is shown in the app.
echo ============================================
pause
exit

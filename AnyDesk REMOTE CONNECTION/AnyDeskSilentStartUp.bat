@echo off
title AnyDesk Silent Startup Setup
color 0A

echo ============================================
echo     AnyDesk - Silent Background Startup
echo ============================================
echo.

REM Check for Admin rights
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Needs Administrator rights. Restarting elevated...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

REM Find AnyDesk
set "ANYDESK="
if exist "%ProgramFiles%\AnyDesk\AnyDesk.exe"      set "ANYDESK=%ProgramFiles%\AnyDesk\AnyDesk.exe"
if exist "%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe" set "ANYDESK=%ProgramFiles(x86)%\AnyDesk\AnyDesk.exe"
if exist "%APPDATA%\AnyDesk\AnyDesk.exe"            set "ANYDESK=%APPDATA%\AnyDesk\AnyDesk.exe"
if exist "%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"       set "ANYDESK=%LOCALAPPDATA%\AnyDesk\AnyDesk.exe"

if not defined ANYDESK (
    echo [X] AnyDesk not found. Please install it first.
    pause
    exit
)

echo [OK] Found AnyDesk at: %ANYDESK%
echo.

REM --- METHOD 1: Install AnyDesk as a Windows Service ---
echo [*] Installing AnyDesk as a Windows Service...
"%ANYDESK%" --install-service >nul 2>&1

REM Start the service
net start AnyDesk >nul 2>&1
sc config AnyDesk start= auto >nul 2>&1

REM Verify service is running
sc query AnyDesk | find "RUNNING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] AnyDesk Service is running and set to auto-start.
    goto REMOVE_TRAY
)

REM --- METHOD 2: Fallback - Startup folder with --tray flag (no window) ---
echo [!] Service method failed, using startup tray method instead...
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\anydesk_shortcut.vbs"
echo sLinkFile = "%STARTUP%\AnyDesk.lnk" >> "%TEMP%\anydesk_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\anydesk_shortcut.vbs"
echo oLink.TargetPath = "%ANYDESK%" >> "%TEMP%\anydesk_shortcut.vbs"
echo oLink.Arguments = "--tray" >> "%TEMP%\anydesk_shortcut.vbs"
echo oLink.WindowStyle = 7 >> "%TEMP%\anydesk_shortcut.vbs"
echo oLink.Save >> "%TEMP%\anydesk_shortcut.vbs"
cscript //nologo "%TEMP%\anydesk_shortcut.vbs"
del "%TEMP%\anydesk_shortcut.vbs" >nul 2>&1
echo [OK] AnyDesk will now start hidden (tray only) on login.
goto REMOVE_TRAY

:REMOVE_TRAY
REM Remove AnyDesk from normal registry startup to avoid double-launch
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "AnyDesk" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "AnyDesk" /f >nul 2>&1

echo.
echo ============================================
echo  Setup Complete! Here is what was configured:
echo.
echo  - AnyDesk runs silently in the background
echo  - NO window will open on startup
echo  - People can still connect to you remotely
echo  - AnyDesk icon will appear in system tray
echo    (bottom-right clock area) if needed
echo.
echo  To open AnyDesk manually anytime:
echo  Just double-click the AnyDesk desktop icon
echo ============================================
echo.
pause
exit

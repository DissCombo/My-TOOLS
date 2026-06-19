@echo off
title Disable AnyDesk Startup
color 0C

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo [*] Stopping AnyDesk service...
net stop AnyDesk >nul 2>&1
sc config AnyDesk start= disabled >nul 2>&1

echo [*] Removing from startup registry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "AnyDesk" /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v "AnyDesk" /f >nul 2>&1

echo [*] Removing startup folder shortcut...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AnyDesk.lnk" >nul 2>&1

echo.
echo [OK] Done! AnyDesk will no longer start with Windows.
echo      You can still open it manually anytime.
echo.
pause
exit

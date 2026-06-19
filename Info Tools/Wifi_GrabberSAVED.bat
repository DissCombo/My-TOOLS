@echo off
echo =============================
echo    Saved WiFi Passwords
echo =============================
echo.
netsh wlan show profiles | findstr /r /c:".*Profile.*:.*" > temp_profiles.txt

for /f "tokens=*" %%a in (temp_profiles.txt) do (
    for /f "tokens=2 delims=:" %%b in ("%%a") do (
        set "profile=%%b"
        setlocal enabledelayedexpansion
        set "profile=!profile:~1!"
        if not "!profile!"=="" (
            echo Network: !profile!
            netsh wlan show profile name="!profile!" key=clear 2>nul | findstr /i "Key Content"
            echo -------------------------
        )
        endlocal
    )
)

del temp_profiles.txt 2>nul
echo.
pause
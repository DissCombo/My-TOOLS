@echo off
title OSINT Tool - Builder
color 0A

echo.
echo  =============================================
echo   OSINT Tool - EXE Builder
echo  =============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Download it from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b
)

echo  [OK] Python found.
echo.

:: Install PyInstaller
echo  [1/3] Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install PyInstaller.
    pause
    exit /b
)
echo  [OK] PyInstaller ready.
echo.

:: Optional: install OSINT tools
echo  [2/3] Installing optional OSINT tools (sherlock, holehe)...
pip install sherlock-project holehe --quiet
echo  [OK] Optional tools installed (or already present).
echo.

:: Build the exe
echo  [3/3] Building osint_tool.exe ...
echo        (This may take a minute)
echo.

pyinstaller --onefile --console --name osint_tool osint_tool.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Make sure osint_tool.py is in the same folder as this batch file.
    pause
    exit /b
)

echo.
echo  =============================================
echo   BUILD SUCCESSFUL!
echo   Your exe is in the  dist\  folder.
echo   Just double-click  dist\osint_tool.exe
echo  =============================================
echo.
pause

@echo off
title Sherlock Project Installer
echo =======================================
echo        Sherlock Project Installer
echo =======================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

:: Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not available. Try reinstalling Python.
    pause
    exit /b 1
)

echo [OK] pip found.
echo.

:: Install Sherlock
echo Installing Sherlock Project...
echo.
pip install sherlock-project

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. Try running this batch file as Administrator.
    pause
    exit /b 1
)

echo.
echo =======================================
echo   Sherlock installed successfully!
echo =======================================
echo.
echo To use Sherlock, open a command prompt and run:
echo   sherlock username
echo.
echo Example:
echo   sherlock johndoe
echo.
pause

@echo off
setlocal enabledelayedexpansion
title Startup Manager

:MENU
cls
echo ============================================
echo          STARTUP MANAGER
echo ============================================
echo.
echo  [1]  Add a program to Startup
echo  [2]  Remove a program from Startup
echo  [3]  View current Startup items
echo  [4]  Exit
echo.
echo ============================================
set /p CHOICE= Choose an option (1-4): 

if "%CHOICE%"=="1" goto ADD
if "%CHOICE%"=="2" goto REMOVE
if "%CHOICE%"=="3" goto VIEW
if "%CHOICE%"=="4" goto EXIT
echo Invalid choice. Try again.
timeout /t 2 >nul
goto MENU


:: ============================================
:ADD
cls
echo ============================================
echo          ADD TO STARTUP
echo ============================================
echo.
echo Drag and drop a file into this window,
echo OR type the full path to the file/EXE.
echo.
echo Examples:
echo   C:\Program Files\MyApp\app.exe
echo   C:\Users\You\Documents\script.bat
echo   C:\Users\You\Music\song.mp3
echo.
set /p FILEPATH= Path: 

:: Strip surrounding quotes if dragged in
set FILEPATH=%FILEPATH:"=%

if not exist "%FILEPATH%" (
    echo.
    echo [ERROR] File not found: %FILEPATH%
    echo Make sure the path is correct.
    pause
    goto MENU
)

echo.
set /p SHORTCUT_NAME= Enter a name for this startup entry (no spaces, e.g. MyApp): 

if "%SHORTCUT_NAME%"=="" (
    echo [ERROR] Name cannot be empty.
    pause
    goto MENU
)

:: Determine file extension
set EXT=%FILEPATH:~-4%

:: For non-EXE files, wrap in cmd /c start "" "filepath"
echo %EXT% | findstr /i ".exe" >nul
if %errorlevel%==0 (
    set REG_VALUE="%FILEPATH%"
) else (
    set REG_VALUE=cmd /c start "" "%FILEPATH%"
)

reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "%SHORTCUT_NAME%" /t REG_SZ /d "!REG_VALUE!" /f >nul 2>&1

if %errorlevel%==0 (
    echo.
    echo [SUCCESS] "%SHORTCUT_NAME%" has been added to Startup!
    echo It will launch automatically on next login.
) else (
    echo.
    echo [ERROR] Failed to add to startup. Try running as Administrator.
)
echo.
pause
goto MENU


:: ============================================
:REMOVE
cls
echo ============================================
echo          REMOVE FROM STARTUP
echo ============================================
echo.
echo Current Startup entries:
echo.

:: Write registry names to temp file using REG QUERY with /ve trick
:: Each value line from reg query looks like:
::     ValueName    REG_SZ    Data
:: We use a temp file and read with tokens=1* but skip header lines

set TMPFILE=%TEMP%\su_rem_%RANDOM%.txt
set COUNT=0

:: Dump only lines containing REG_SZ into temp file
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul | findstr "REG_SZ" > "%TMPFILE%"

:: Each line: "    Name    REG_SZ    Value"
:: Use tokens to grab just the name (first token after stripping leading spaces)
for /f "usebackq tokens=1" %%N in ("%TMPFILE%") do (
    set /a COUNT+=1
    set "NAME_!COUNT!=%%N"
    echo   [!COUNT!] %%N
)

del "%TMPFILE%" >nul 2>&1

if %COUNT%==0 (
    echo   (No startup entries found)
    echo.
    pause
    goto MENU
)

echo.
echo ============================================
set /p REMOVE_CHOICE= Enter the NUMBER of the entry to remove (or 0 to cancel): 

if "%REMOVE_CHOICE%"=="0" goto MENU

set /a TEST=%REMOVE_CHOICE% 2>nul
if !TEST! LSS 1 (
    echo Invalid choice.
    pause
    goto MENU
)
if !TEST! GTR %COUNT% (
    echo Invalid choice.
    pause
    goto MENU
)

set "ENTRY_TO_REMOVE=!NAME_%REMOVE_CHOICE%!"
echo.
echo Removing: !ENTRY_TO_REMOVE!

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "!ENTRY_TO_REMOVE!" /f

if %errorlevel%==0 (
    echo.
    echo [SUCCESS] "!ENTRY_TO_REMOVE!" has been removed from Startup.
) else (
    echo.
    echo [ERROR] Could not remove the entry. Try running as Administrator.
)
echo.
pause
goto MENU


:: ============================================
:VIEW
cls
echo ============================================
echo       CURRENT STARTUP ITEMS (This User)
echo ============================================
echo.

set COUNT=0
for /f "tokens=1,2,*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2^>nul ^| findstr "REG_SZ"') do (
    set /a COUNT+=1
    echo  Name : %%A
    echo  Path : %%C
    echo  -----------------------------------------------
)

if %COUNT%==0 (
    echo  No startup entries found for current user.
)

echo.
echo [TIP] To see ALL startup items including system-wide ones,
echo open Task Manager ^> Startup tab.
echo.
pause
goto MENU


:: ============================================
:EXIT
cls
echo Goodbye!
timeout /t 1 >nul
exit

@echo off
title File Finder (Fast)
color 0A

:START
cls
echo ============================================
echo        FILE FINDER - Fast Search
echo ============================================
echo.
set /p "FILENAME=Enter file name (e.g. report.pdf): "

if "%FILENAME%"=="" (
    echo [!] No input. Try again.
    pause
    goto START
)

echo.
echo [*] Searching...

REM Write a VBScript to use Windows Search (instant index-based search)
set "VBS=%TEMP%\ffsearch.vbs"
set "OUT=%TEMP%\ffresult.txt"

> "%VBS%" echo Set oConn = CreateObject("ADODB.Connection")
>> "%VBS%" echo Set oRS = CreateObject("ADODB.Recordset")
>> "%VBS%" echo oConn.Open "Provider=Search.CollatorDSO;Extended Properties='Application=Windows';"
>> "%VBS%" echo oRS.Open "SELECT System.ItemPathDisplay FROM SYSTEMINDEX WHERE System.FileName = '%FILENAME%'", oConn
>> "%VBS%" echo Dim fso : Set fso = CreateObject("Scripting.FileSystemObject")
>> "%VBS%" echo Dim ts : Set ts = fso.CreateTextFile("%OUT%", True)
>> "%VBS%" echo If Not oRS.EOF Then
>> "%VBS%" echo   ts.WriteLine oRS.Fields("System.ItemPathDisplay").Value
>> "%VBS%" echo Else
>> "%VBS%" echo   ts.WriteLine "NOTFOUND"
>> "%VBS%" echo End If
>> "%VBS%" echo ts.Close
>> "%VBS%" echo oRS.Close : oConn.Close

cscript //nologo "%VBS%"

set /p "RESULT=" < "%OUT%"
del "%VBS%" >nul 2>&1
del "%OUT%" >nul 2>&1

if "%RESULT%"=="NOTFOUND" (
    echo.
    echo [X] "%FILENAME%" not found in Windows Search index.
    echo     Note: Recently created files may not be indexed yet.
    echo.
    set /p "FALLBACK=Try slower full-drive scan instead? (Y/N): "
    if /i "!FALLBACK!"=="Y" goto SLOWSCAN
    goto DONE
) else (
    echo [OK] Found: %RESULT%
    echo.
    echo [*] Opening location...
    explorer /select,"%RESULT%"
    goto DONE
)

:SLOWSCAN
setlocal enabledelayedexpansion
echo.
echo [*] Scanning drives (this may take a moment)...
set "FOUND="
for %%D in (C D E F G H) do (
    if not defined FOUND (
        if exist "%%D:\" (
            for /f "delims=" %%F in ('dir /s /b "%%D:\%FILENAME%" 2^>nul') do (
                if not defined FOUND set "FOUND=%%F"
            )
        )
    )
)
if defined FOUND (
    echo [OK] Found: !FOUND!
    echo.
    explorer /select,"!FOUND!"
) else (
    echo [X] File not found anywhere on drive.
)

:DONE
echo.
set /p "AGAIN=Search again? (Y/N): "
if /i "%AGAIN%"=="Y" goto START
exit
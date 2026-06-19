@echo off
title IP Geolocator
cls
:menu
mode con: cols=70 lines=20
color 0B

echo ====================================================================
echo                           IP GEOLOCATOR                             
echo ====================================================================
echo.
echo Leave blank and press Enter to locate your own public IP.
echo.
set /p targetIP="Enter IP Address: "

echo.
echo Fetching geolocation data... Please wait...
echo --------------------------------------------------------------------

:: Use PowerShell to query ip-api.com and format the output
powershell -Command ^
    "$ip = '%targetIP%';" ^
    "$url = if ($ip -eq '') { 'http://ip-api.com/json/' } else { 'http://ip-api.com/json/' + $ip };" ^
    "try {" ^
    "    $response = Invoke-RestMethod -Uri $url -Method Get;" ^
    "    if ($response.status -eq 'fail') {" ^
    "        Write-Host 'Error: ' $response.message -ForegroundColor Red;" ^
    "    } else {" ^
    "        Write-Host 'IP Address:  ' $response.query -ForegroundColor Cyan;" ^
    "        Write-Host 'Country:     ' $response.country ' (' $response.countryCode ')' -ForegroundColor White;" ^
    "        Write-Host 'Region/State:' $response.regionName -ForegroundColor White;" ^
    "        Write-Host 'City:         ' $response.city -ForegroundColor White;" ^
    "        Write-Host 'Zip Code:     ' $response.zip -ForegroundColor White;" ^
    "        Write-Host 'Latitude:     ' $response.lat -ForegroundColor White;" ^
    "        Write-Host 'Longitude:    ' $response.lon -ForegroundColor White;" ^
    "        Write-Host 'ISP:          ' $response.isp -ForegroundColor White;" ^
    "    }" ^
    "} catch {" ^
    "    Write-Host 'Failed to connect to geolocation API. Check network.' -ForegroundColor Red;" ^
    "}"

echo --------------------------------------------------------------------
echo.
echo [1] Locate another IP
echo [2] Exit
echo.
set /p choice="Choose an option (1-2): "

if "%choice%"=="1" goto menu
if "%choice%"=="2" exit
goto menu
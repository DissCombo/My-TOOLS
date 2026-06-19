@echo off
color 0A
title Network Info
mode con: cols=70 lines=50

echo.
echo  === NETWORK INFORMATION TOOL ===
echo.

echo  [1] HOSTNAME
hostname
echo.

echo  [2] CURRENT USER
whoami
echo.

echo  [3] IP ADDRESSES
ipconfig | findstr /i "IPv4 IPv6 Subnet Default Gateway Adapter"
echo.

echo  [4] MAC ADDRESSES
ipconfig /all | findstr /i "Physical"
echo.

echo  [5] PUBLIC IP + LOCATION
curl -s https://ipinfo.io 2>nul || echo  curl not available.
echo.

echo  [6] DEVICES ON NETWORK
ping 192.168.1.255 -n 2 >nul 2>&1
ping 192.168.0.255 -n 2 >nul 2>&1
arp -a
echo.

echo  [7] DNS SERVERS
ipconfig /all | findstr /i "DNS Servers"
echo.

echo  [8] ACTIVE CONNECTIONS
netstat -ano | findstr "ESTABLISHED"
echo.

echo  [9] NEARBY Wi-Fi NETWORKS
netsh wlan show networks mode=bssid 2>nul || echo  No wireless adapter found.
echo.

echo  [10] SAVED Wi-Fi PASSWORDS
echo.
for /f "skip=9 tokens=1,2 delims=:" %%i in ('netsh wlan show profiles') do (
    if "%%j" neq "" (
        echo  Profile:%%j
        netsh wlan show profile name="%%j" key=clear 2>nul | findstr "Key Content"
        echo.
    )
)

echo  [11] PING TEST
ping 8.8.8.8 -n 3
echo.

echo  [12] FIREWALL STATUS
netsh advfirewall show allprofiles state
echo.

echo  === DONE ===
echo.
pause

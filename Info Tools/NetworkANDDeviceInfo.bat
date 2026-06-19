@echo off
color 2

Title : "IP INFO"
ipconfig /all

hostname

whoami

ipconfig | findstr /i "IPv4 IPv6 Subnet Default Gateway Adapter"

ipconfig /all | findstr /i "Physical"

ipconfig /all | findstr /i "DNS Servers"

netstat

pause
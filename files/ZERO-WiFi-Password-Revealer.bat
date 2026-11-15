@echo off
title ZERO WiFi Password Revealer - YOUR OWN saved WiFi only
color 0B
echo ==========================================
echo   ZERO WiFi Password Revealer
echo   Shows passwords for WiFi YOU saved before
echo   Run as Administrator for best result
echo ==========================================
echo.

netsh wlan show profiles | findstr "All User Profile" > "%TEMP%\wifi_list.txt"
if not exist "%TEMP%\wifi_list.txt" (
    echo No saved WiFi found on this PC.
    pause
    exit
)

for /f "tokens=5* delims=: " %%a in ('type "%TEMP%\wifi_list.txt"') do (
    echo ------------------------------------------
    echo WiFi Name: %%a
    netsh wlan show profile name="%%a" key=clear | findstr "Key Content"
)

echo.
echo ------------------------------------------
echo DONE! These are YOUR saved networks only.
echo Don't share this with strangers.
pause

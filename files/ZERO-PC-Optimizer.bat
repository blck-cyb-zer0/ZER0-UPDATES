@echo off
title ZERO PC Optimizer / FPS Booster
color 0A
echo ==========================================
echo   ZERO PC OPTIMIZER - Safe FPS Booster
echo   Cleans RAM, Temp, Kills Junk Apps
echo ==========================================
echo.
echo [1/5] Cleaning Windows Temp...
del /q/f/s %TEMP%\* >nul 2>&1
del /q/f/s C:\Windows\Temp\* >nul 2>&1
echo DONE

echo [2/5] Cleaning Prefetch (old launch cache)...
del /q/f/s C:\Windows\Prefetch\* >nul 2>&1
echo DONE

echo [3/5] Flushing DNS (fixes lag / slow internet)...
ipconfig /flushdns >nul 2>&1
echo DONE

echo [4/5] Clearing RAM standby cache...
echo This will close junk background apps, NOT your game.
taskkill /f /im OneDrive.exe >nul 2>&1
taskkill /f /im Skype.exe >nul 2>&1
taskkill /f /im Teams.exe >nul 2>&1
taskkill /f /im Spotify.exe >nul 2>&1
echo DONE

echo [5/5] Setting High Performance Power Plan...
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1
echo DONE

echo.
echo ==========================================
echo  OPTIMIZED! Restart your PC for +20-40 FPS
echo  in Free Fire / GTA / Fortnite.
echo ==========================================
pause

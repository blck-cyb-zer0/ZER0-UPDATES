@echo off
title ZERO Folder Locker - Hide your private folder
color 0E
set "FOLDER=ZERO Private Folder"
set "PASS=ZER0-1234"

if not exist "%FOLDER%" (
    echo Creating your private folder...
    mkdir "%FOLDER%"
    echo Put your private files inside "%FOLDER%" then run this again to lock it.
    echo Default password is: ZER0-1234
    echo To change it, right-click this file ^> Edit ^> change PASS=
    pause
    exit
)

echo ==========================================
echo   ZERO Folder Locker
echo   Folder: %FOLDER%
echo ==========================================
echo.
set /p INPUT=Enter password to UNLOCK (or type LOCK to lock): 

if /i "%INPUT%"=="LOCK" (
    attrib +h +s "%FOLDER%"
    echo LOCKED! Folder is now hidden.
    pause
    exit
)

if "%INPUT%"=="%PASS%" (
    attrib -h -s "%FOLDER%"
    echo UNLOCKED! Your folder is visible again.
    echo Run this again and type LOCK to hide it.
) else (
    echo WRONG PASSWORD! Folder stays hidden.
)
pause

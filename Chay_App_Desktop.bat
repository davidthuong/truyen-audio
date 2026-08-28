@echo off
title AudioStory Studio - Desktop App
cd /d "%~dp0"
echo =========================================================
echo       AUDIOSTORY STUDIO - AI VIDEO & YOUTUBE AUTO-PILOT
echo =========================================================
echo [*] Dang khoi dong ung dung Desktop...
python desktop_app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Gap loi khi khoi dong Desktop App. Dang cai dat thu vien bo sung...
    python -m pip install -r requirements.txt
    python desktop_app.py
    pause
)

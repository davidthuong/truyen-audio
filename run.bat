@echo off
title AI Audio Story Video Studio
echo ====================================================
echo       AI AUDIO STORY VIDEO STUDIO (YOUTUBE)
echo ====================================================
echo [1/2] Dang kiem tra thu vien...
python -m pip install -r requirements.txt --quiet

echo [2/2] Dang khoi dong Web Server tai http://localhost:8000 ...
start http://localhost:8000
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
pause

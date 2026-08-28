@echo off
title Dong Goi AudioStory Studio Thanh File .EXE
cd /d "%~dp0"
echo =========================================================
echo       DONG GOI AUDIOSTORY STUDIO THANH FILE .EXE
echo =========================================================
echo [*] Dang tao file thuc thi .exe doc lap (Vui long doi 1-2 phut)...

pyinstaller --noconfirm --onedir --windowed ^
    --name "AudioStoryStudio" ^
    --add-data "frontend;frontend" ^
    --add-data "assets;assets" ^
    --hidden-import "uvicorn" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.http.h11_impl" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "fastapi" ^
    --hidden-import "webview" ^
    --hidden-import "clr" ^
    --hidden-import "pythonnet" ^
    --hidden-import "engineio.async_drivers.aiohttp" ^
    --collect-all "edge_tts" ^
    --collect-all "webview" ^
    desktop_app.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =========================================================
    echo [OK] DONG GOI HOAN TAT THANH CONG!
    echo File .exe nam tai: dist\AudioStoryStudio\AudioStoryStudio.exe
    echo =========================================================
    explorer dist\AudioStoryStudio
) else (
    echo.
    echo [!] Gap loi trong qua trinh dong goi file .exe.
)
pause

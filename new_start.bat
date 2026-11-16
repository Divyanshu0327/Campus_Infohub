@echo off
setlocal EnableDelayedExpansion
title Campus InfoHub — Project Launcher

:: ═══════════════════════════════════════════════════════════════
::  CAMPUS INFOHUB  —  Full Project Launcher
::  Starts: Backend (FastAPI/Uvicorn)  +  Frontend (Vite/React)
:: ═══════════════════════════════════════════════════════════════

cls
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          CAMPUS INFOHUB  —  Project Launcher            ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Resolve project root (folder where this .bat lives) ────────
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

echo  [INFO] Project Root : %ROOT%
echo  [INFO] Backend Path : %BACKEND%
echo  [INFO] Frontend Path: %FRONTEND%
echo.

:: ═══════════════════════════════════════════
::  STEP 1 — Check Python is available
:: ═══════════════════════════════════════════
echo  ┌─[ 1/4 ] Checking Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo  │  [ERROR] Python not found! Please install Python 3.10+
    echo  │          and make sure it is in your PATH.
    echo  └─ FAILED
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  │  [OK] %PY_VER%
echo  └─ Done
echo.

:: ═══════════════════════════════════════════
::  STEP 2 — Check Node.js / npm is available
:: ═══════════════════════════════════════════
echo  ┌─[ 2/4 ] Checking Node.js / npm ...
node --version >nul 2>&1
if errorlevel 1 (
    echo  │  [ERROR] Node.js not found! Please install Node.js 18+
    echo  │          and make sure it is in your PATH.
    echo  └─ FAILED
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1')  do set NPM_VER=%%v
echo  │  [OK] Node %NODE_VER%  /  npm v%NPM_VER%
echo  └─ Done
echo.

:: ═══════════════════════════════════════════
::  STEP 3 — Set up Python venv + dependencies
:: ═══════════════════════════════════════════
echo  ┌─[ 3/4 ] Setting up Backend (Python venv) ...

if not exist "%BACKEND%\venv\Scripts\activate.bat" (
    echo  │  [INFO] Virtual environment not found — creating one ...
    python -m venv "%BACKEND%\venv"
    if errorlevel 1 (
        echo  │  [ERROR] Failed to create virtual environment!
        echo  └─ FAILED
        pause
        exit /b 1
    )
    echo  │  [OK] Virtual environment created.

    echo  │  [INFO] Installing Python dependencies ...
    call "%BACKEND%\venv\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt" --quiet
    if errorlevel 1 (
        echo  │  [ERROR] pip install failed! Check requirements.txt
        echo  └─ FAILED
        pause
        exit /b 1
    )
    echo  │  [OK] Dependencies installed.
) else (
    echo  │  [OK] Virtual environment already exists — skipping install.
)
echo  └─ Done
echo.

:: ═══════════════════════════════════════════
::  STEP 4 — Install frontend npm packages
:: ═══════════════════════════════════════════
echo  ┌─[ 4/4 ] Checking Frontend (node_modules) ...

if not exist "%FRONTEND%\node_modules" (
    echo  │  [INFO] node_modules not found — running npm install ...
    pushd "%FRONTEND%"
    npm install --silent
    if errorlevel 1 (
        echo  │  [ERROR] npm install failed!
        echo  └─ FAILED
        popd
        pause
        exit /b 1
    )
    popd
    echo  │  [OK] npm packages installed.
) else (
    echo  │  [OK] node_modules already exists — skipping install.
)
echo  └─ Done
echo.

:: ═══════════════════════════════════════════
::  LAUNCH — Backend and Frontend
:: ═══════════════════════════════════════════
echo  ┌─[ LAUNCHING ] Starting services ...
echo  │
echo  │  Launching Backend  (FastAPI + Uvicorn) ...
start "Campus InfoHub — Backend  [http://localhost:8000]" cmd /k ^
    "title Campus InfoHub Backend && ^
     cd /d "%BACKEND%" && ^
     call venv\Scripts\activate && ^
     echo. && ^
     echo  [Backend]  http://localhost:8000 && ^
     echo  [API Docs]  http://localhost:8000/docs && ^
     echo. && ^
     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Small delay so backend starts first
timeout /t 2 /nobreak >nul

echo  │  Launching Frontend (Vite + React) ...
start "Campus InfoHub — Frontend [http://localhost:5173]" cmd /k ^
    "title Campus InfoHub Frontend && ^
     cd /d "%FRONTEND%" && ^
     echo. && ^
     echo  [Frontend]  http://localhost:5173 && ^
     echo. && ^
     npm run dev"

echo  │
echo  └─ Both services launched!
echo.

:: ═══════════════════════════════════════════
::  SUMMARY PANEL
:: ═══════════════════════════════════════════
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                    SERVICES RUNNING                     ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  🌐  Frontend App   →  http://localhost:5173            ║
echo  ║  ⚙️   Backend API   →  http://localhost:8000            ║
echo  ║  📖  API Docs       →  http://localhost:8000/docs       ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  Press any key here to STOP and close this launcher.    ║
echo  ║  (Backend and Frontend windows stay open independently) ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause >nul
exit /b 0

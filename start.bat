@echo off
setlocal EnableDelayedExpansion
title Campus InfoHub — Project Launcher

cls
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          CAMPUS INFOHUB  —  Project Launcher            ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: ── Resolve project root (folder where this .bat lives) ──────
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "VENV_PYTHON=%BACKEND%\venv\Scripts\python.exe"
set "VENV_ACTIVATE=%BACKEND%\venv\Scripts\activate.bat"

echo  [INFO] Project Root  : %ROOT%
echo  [INFO] Backend Path  : %BACKEND%
echo  [INFO] Frontend Path : %FRONTEND%
echo.

:: ═══════════════════════════════════════════
::  STEP 1 — Check Python
:: ═══════════════════════════════════════════
echo  [1/4] Checking Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo  [OK] %PY_VER%
echo.

:: ═══════════════════════════════════════════
::  STEP 2 — Check Node.js / npm
:: ═══════════════════════════════════════════
echo  [2/4] Checking Node.js / npm ...
node --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found! Please install Node.js 18+ and add it to PATH.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1')  do set NPM_VER=%%v
echo  [OK] Node %NODE_VER%  /  npm v%NPM_VER%
echo.

:: ═══════════════════════════════════════════
::  STEP 3 — Python venv + dependencies
:: ═══════════════════════════════════════════
echo  [3/4] Setting up Python virtual environment ...

if not exist "%VENV_PYTHON%" (
    echo  [INFO] Virtual environment not found — creating one ...
    python -m venv "%BACKEND%\venv"
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo  [INFO] Installing Python dependencies ...
    "%BACKEND%\venv\Scripts\pip.exe" install -r "%BACKEND%\requirements.txt" --quiet
    if errorlevel 1 (
        echo  [ERROR] pip install failed! Check requirements.txt
        pause
        exit /b 1
    )
    echo  [OK] Python dependencies installed.
) else (
    echo  [OK] Virtual environment already exists.
)
echo.

:: ═══════════════════════════════════════════
::  STEP 4 — Frontend npm packages
:: ═══════════════════════════════════════════
echo  [4/4] Checking frontend node_modules ...

if not exist "%FRONTEND%\node_modules" (
    echo  [INFO] node_modules not found — running npm install ...
    pushd "%FRONTEND%"
    npm install --silent
    if errorlevel 1 (
        echo  [ERROR] npm install failed!
        popd
        pause
        exit /b 1
    )
    popd
    echo  [OK] npm packages installed.
) else (
    echo  [OK] node_modules already present.
)
echo.

:: ═══════════════════════════════════════════
::  WRITE helper launch scripts to TEMP
:: ═══════════════════════════════════════════
:: Backend launcher (written to temp so the cmd /k runs cleanly)
set "BACKEND_LAUNCHER=%TEMP%\campus_backend_launch.bat"
(
    echo @echo off
    echo title Campus InfoHub — Backend  [http://localhost:8000]
    echo cd /d "%BACKEND%"
    echo echo.
    echo echo  ╔═══════════════════════════════════════╗
    echo echo  ║   Campus InfoHub — Backend            ║
    echo echo  ║   Uvicorn  http://localhost:8000      ║
    echo echo  ║   API Docs http://localhost:8000/docs ║
    echo echo  ╚═══════════════════════════════════════╝
    echo echo.
    echo call venv\Scripts\activate.bat
    echo "%VENV_PYTHON%" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    echo pause
) > "%BACKEND_LAUNCHER%"

:: Frontend launcher
set "FRONTEND_LAUNCHER=%TEMP%\campus_frontend_launch.bat"
(
    echo @echo off
    echo title Campus InfoHub — Frontend  [http://localhost:5173]
    echo cd /d "%FRONTEND%"
    echo echo.
    echo echo  ╔═══════════════════════════════════════╗
    echo echo  ║   Campus InfoHub — Frontend           ║
    echo echo  ║   Vite Dev Server http://localhost:5173 ║
    echo echo  ╚═══════════════════════════════════════╝
    echo echo.
    echo npm run dev
    echo pause
) > "%FRONTEND_LAUNCHER%"

:: ═══════════════════════════════════════════
::  LAUNCH services in separate windows
:: ═══════════════════════════════════════════
echo  Launching Backend  (FastAPI + Uvicorn on :8000) ...
start "" cmd /k "%BACKEND_LAUNCHER%"

:: Give backend 3 seconds head start
timeout /t 3 /nobreak >nul

echo  Launching Frontend (Vite + React on :5173) ...
start "" cmd /k "%FRONTEND_LAUNCHER%"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║                  SERVICES ARE STARTING                  ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  🌐  Frontend App   →  http://localhost:5173            ║
echo  ║  ⚙️   Backend API   →  http://localhost:8000            ║
echo  ║  📖  API Docs       →  http://localhost:8000/docs       ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  Two new windows opened — keep them running!            ║
echo  ║  Close those windows to stop the services.              ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.
pause >nul
exit /b 0

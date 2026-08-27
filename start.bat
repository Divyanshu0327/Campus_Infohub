@echo off
title College Info Hub Launcher
echo Starting College Info Hub...
echo.

echo [1/2] Starting Backend API...
start "College Hub - Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn app.main:app --reload"

echo [2/2] Starting Frontend App...
start "College Hub - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services have been launched in separate windows!
echo - Frontend Application: http://localhost:5173
echo - Backend API: http://localhost:8000
echo - API Documentation: http://localhost:8000/docs
echo.
pause

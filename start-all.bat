@echo off
title Agentic Commerce POC Launcher

set "PROJECT_ROOT=C:\My\Langchain\agentic-commerce-poc"
set "FRONTEND_ROOT=C:\My\Langchain\agentic-commerce-poc\frontend"

echo ============================================
echo Starting Agentic Commerce POC
echo ============================================
echo.

REM ============================================================
REM 1. CHECK / START OLLAMA
REM ============================================================

echo Checking Ollama...

curl -s http://127.0.0.1:11434/api/tags >nul 2>&1

if errorlevel 1 (
    echo Ollama is not running. Starting Ollama...

    start "Ollama" cmd /k "ollama serve"

    echo Waiting for Ollama to start...
    timeout /t 3 /nobreak >nul
) else (
    echo Ollama is already running.
)

echo.

REM ============================================================
REM 2. START FASTAPI
REM ============================================================

echo Starting FastAPI...

start "FastAPI Backend" /D "%PROJECT_ROOT%" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting for FastAPI...
timeout /t 3 /nobreak >nul

echo.

REM ============================================================
REM 3. START REACT
REM ============================================================

echo Starting React...

start "React Frontend" /D "%FRONTEND_ROOT%" cmd /k "npm run dev"

echo Waiting for React...
timeout /t 4 /nobreak >nul

echo.

REM ============================================================
REM 4. OPEN APPLICATION
REM ============================================================

echo Opening React application...

start "" "http://localhost:5173"

echo.
echo ============================================
echo Agentic Commerce POC Started
echo ============================================
echo.
echo Ollama  : http://127.0.0.1:11434
echo FastAPI : http://127.0.0.1:8000
echo Swagger : http://127.0.0.1:8000/docs
echo React   : http://localhost:5173
echo.
echo ============================================

echo You can close this launcher window.
echo FastAPI and React will continue running.
echo.

pause
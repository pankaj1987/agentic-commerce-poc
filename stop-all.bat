@echo off
title Agentic Commerce POC - Stop Services

echo ============================================
echo Stopping Agentic Commerce POC
echo ============================================
echo.

REM ------------------------------------------------
REM 1. Stop FastAPI running on port 8000
REM ------------------------------------------------
echo Stopping FastAPI on port 8000...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Killing FastAPI process PID %%a...
    taskkill /PID %%a /F >nul 2>&1
)

echo FastAPI stopped.

REM ------------------------------------------------
REM 2. Stop React / Vite running on port 5173
REM ------------------------------------------------
echo.
echo Stopping React/Vite on port 5173...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING"') do (
    echo Killing React process PID %%a...
    taskkill /PID %%a /F >nul 2>&1
)

echo React stopped.

REM ------------------------------------------------
REM 3. Ask whether Ollama should also be stopped
REM ------------------------------------------------
echo.
choice /C YN /N /M "Do you also want to stop Ollama? (Y/N): "

if errorlevel 2 goto skip_ollama
if errorlevel 1 goto stop_ollama


:stop_ollama

echo.
echo Stopping Ollama...

taskkill /IM ollama.exe /F >nul 2>&1

if %errorlevel% equ 0 (
    echo Ollama stopped.
) else (
    echo Ollama was not running or could not be stopped.
)

goto finished


:skip_ollama

echo.
echo Ollama will remain running.


:finished

echo.
echo ============================================
echo Agentic Commerce POC stopped
echo ============================================
echo.
echo FastAPI : STOPPED
echo React   : STOPPED
echo Ollama  : Check message above
echo ============================================
echo.

pause
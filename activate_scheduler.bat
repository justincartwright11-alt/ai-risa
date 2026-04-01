@echo off
REM AI-RISA Scheduler Activation Batch File
REM This script will request administrator privilege and register the scheduled tasks

setlocal enabledelayedexpansion

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo Requesting administrator privilege...
    echo.
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

REM We are now running as administrator
cd /d C:\ai_risa_data

echo.
echo === AI-RISA Pipeline Scheduler Activation ===
echo.
echo Registering scheduled tasks...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File C:\ai_risa_data\register_pipeline_tasks.ps1 -Enable

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Tasks registered successfully!
    echo.
    echo Next steps:
    echo 1. Open Task Scheduler (taskschd.msc)
    echo 2. Navigate to: Task Scheduler Library ^> AI-RISA
    echo 3. Verify both tasks appear and are "Enabled"
    echo.
    pause
) else (
    echo.
    echo [ERROR] Task registration failed!
    echo.
    pause
    exit /b 1
)

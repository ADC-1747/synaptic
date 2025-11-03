@echo off
setlocal enabledelayedexpansion

:: Configuration
set "VENV_DIR=synaptic-venv"
set "REQUIREMENTS=requirements.txt"
set "TEST_SCRIPT=tests/latency_check.py"
set "APP_LAUNCHER=run_app_windows.bat"
set "APP_URL=http://0.0.0.0:8000/signal?symbol=XYZ"

set "DURATION=%1"
if "%DURATION%"=="" set "DURATION=10"

set "CONCURRENCY=%2"
if "%CONCURRENCY%"=="" set "CONCURRENCY=10"

set "APP_STARTED=false"

:: Cleanup function
:cleanup
echo.
echo 🧪 Latency test completed.
if "%APP_STARTED%"=="true" (
    echo 🛑 Stopping FastAPI app...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr :8000') do taskkill /PID %%p /F
)
pause
exit /b

echo 🟢 Starting latency test runner...

:: Ensure virtual environment
if not exist "%VENV_DIR%" (
    echo 🔧 Virtual environment not found. Creating %VENV_DIR%...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
    echo 📦 Installing dependencies from %REQUIREMENTS%...
    pip install --upgrade pip
    pip install -r "%REQUIREMENTS%"
) else (
    echo ✅ Virtual environment found.
    call "%VENV_DIR%\Scripts\activate.bat"
    if exist "%REQUIREMENTS%" (
        echo 📦 Ensuring required packages are installed...
        pip install -r "%REQUIREMENTS%" >nul
    )
)

:: Ensure src/ is in PYTHONPATH
set "PROJECT_ROOT=%cd%"
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%
echo 🔗 PYTHONPATH set: %PROJECT_ROOT%

:: Check if app is running
echo 🔍 Checking if FastAPI app is running...
curl -s %APP_URL% >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ FastAPI app already running.
) else (
    echo 🚀 FastAPI app not running. Starting it via %APP_LAUNCHER%...
    start /B cmd /c "%APP_LAUNCHER%"
    set "APP_STARTED=true"
    timeout /t 3 >nul
    echo ⏳ Waiting for FastAPI app to become ready...
    :wait_for_app
    curl -s %APP_URL% >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        timeout /t 1 >nul
        goto wait_for_app
    )
    echo ✅ FastAPI app is ready.
)

:: Run latency test
if exist "%TEST_SCRIPT%" (
    echo 🧪 Running latency test for %DURATION%s with concurrency=%CONCURRENCY%...
    python "%TEST_SCRIPT%" -d %DURATION% -c %CONCURRENCY%
) else (
    echo ❌ Test script not found: %TEST_SCRIPT%
    exit /b 1
)

goto cleanup

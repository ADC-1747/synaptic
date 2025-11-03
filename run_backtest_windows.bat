@echo off
setlocal enabledelayedexpansion

REM ----- Configuration -----
set VENV_DIR=synaptic-venv
set REQUIREMENTS=requirements.txt
set BACKTEST_SCRIPT=src\backtest.py

echo 🟢 Starting backtest runner...

REM ----- Check if venv exists -----
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo 🔧 Virtual environment not found. Creating %VENV_DIR%...
    python -m venv %VENV_DIR%
    call %VENV_DIR%\Scripts\activate.bat
    echo 📦 Installing dependencies from %REQUIREMENTS%...
    python -m pip install --upgrade pip
    python -m pip install -r %REQUIREMENTS%
) else (
    echo ✅ Virtual environment found.
    call %VENV_DIR%\Scripts\activate.bat
    if exist %REQUIREMENTS% (
        echo 📦 Ensuring required packages are installed...
        python -m pip install -r %REQUIREMENTS% >nul
    )
)

REM ----- Set PYTHONPATH -----
set "PROJECT_ROOT=%cd%"
set PYTHONPATH=%PROJECT_ROOT%
echo 🔗 PYTHONPATH set: %PYTHONPATH%

REM ----- Run backtest script -----
if exist "%BACKTEST_SCRIPT%" (
    echo 🚀 Running backtest script %BACKTEST_SCRIPT%...
    python %BACKTEST_SCRIPT%
) else (
    echo ❌ Backtest script not found: %BACKTEST_SCRIPT%
    exit /b 1
)

echo.
echo 📊 Backtest run completed.
pause

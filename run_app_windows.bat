@echo off
setlocal ENABLEDELAYEDEXPANSION

:: Configuration
set "VENV_DIR=synaptic-venv"
set "REQUIREMENTS=requirements.txt"
set "APP_ENTRY=src.signal_service"
set "HOST=0.0.0.0"
set "PORT=8000"

:cleanup
echo.
echo 🛑 Application stopped.
pause
exit /b

echo 🟢 Starting application launcher...

:: Check if port is already in use
echo 🔍 Checking if port %PORT% is already in use...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
    echo ❌ Port %PORT% is already in use by PID %%a
    echo(
    echo Running process details:
    tasklist /FI "PID eq %%a"
    echo(
    set /p answer=Do you want to kill the existing process and continue? (y/n): 
    if /I "!answer!"=="y" (
        echo ⚠️  Killing process %%a...
        taskkill /PID %%a /F >nul 2>&1
        echo ✅ Killed process %%a
    ) else (
        echo ⚠️ Exiting without starting the app.
        goto cleanup
    )
    goto portfreed
)
echo ✅ Port %PORT% is free.

:portfreed

:: Check if venv exists
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

:: Run the FastAPI app using Uvicorn
echo 🚀 Running FastAPI app (%APP_ENTRY%) at http://%HOST%:%PORT%
uvicorn "%APP_ENTRY%:app" --host "%HOST%" --port "%PORT%" --reload
if %ERRORLEVEL% NEQ 0 (
    echo ❌ An error occurred while running the application.
)

goto cleanup

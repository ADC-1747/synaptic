@echo off
setlocal enabledelayedexpansion

:: Settings
set VENV_DIR=synaptic-venv
set REQUIREMENTS=requirements.txt
set TEST_DIR=tests
set PYTHON_EXE=python

:: Cleanup on exit
:cleanup
echo.
echo 🧪 Test run completed.
pause
exit /b

:: Start
echo 🟢 Starting test runner...

:: Check if venv exists
if not exist %VENV_DIR% (
    echo 🔧 Virtual environment not found. Creating %VENV_DIR%...
    %PYTHON_EXE% -m venv %VENV_DIR%
    call %VENV_DIR%\Scripts\activate.bat
    echo 📦 Installing dependencies from %REQUIREMENTS%...
    pip install --upgrade pip
    if exist %REQUIREMENTS% (
        pip install -r %REQUIREMENTS%
    )
) else (
    echo ✅ Virtual environment found.
    call %VENV_DIR%\Scripts\activate.bat
    if exist %REQUIREMENTS% (
        echo 📦 Ensuring required packages are installed...
        pip install -r %REQUIREMENTS% >nul
    )
)

:: Ensure src/ is in PYTHONPATH
set PROJECT_ROOT=%cd%
set PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%
echo 🔗 PYTHONPATH set to include project root: %PROJECT_ROOT%

:: Run tests
if exist %TEST_DIR% (
    echo 🧪 Running tests in %TEST_DIR%...
    pytest %TEST_DIR% -v
) else (
    echo ❌ No test directory found: %TEST_DIR%
    goto cleanup
)

goto cleanup

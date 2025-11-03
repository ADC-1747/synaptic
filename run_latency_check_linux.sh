#!/usr/bin/env bash

set -e  # Exit on the first error

VENV_DIR="synaptic-venv"
REQUIREMENTS="requirements.txt"
TEST_SCRIPT="tests/latency_check.py"
APP_LAUNCHER="./run_app_linux.sh"
APP_URL="http://0.0.0.0:8000/signal?symbol=XYZ"

DURATION=${1:-10}
CONCURRENCY=${2:-10}

cleanup() {
    echo -e "\n🧪 Latency test completed."
    if [ "$APP_STARTED" == "true" ] && [ -n "$APP_PID" ]; then
        echo "🛑 Stopping FastAPI app (PID: $APP_PID)..."
        kill "$APP_PID" || true
    fi
    read -p "Press Enter to exit..."
}
trap cleanup EXIT

echo "🟢 Starting latency test runner..."

# --- Ensure virtual environment ---
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Virtual environment not found. Creating $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "📦 Installing dependencies from $REQUIREMENTS..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS"
else
    echo "✅ Virtual environment found."
    source "$VENV_DIR/bin/activate"
    if [ -f "$REQUIREMENTS" ]; then
        echo "📦 Ensuring required packages are installed..."
        pip install -r "$REQUIREMENTS" --quiet
    fi
fi

# --- Ensure src/ is in PYTHONPATH ---
PROJECT_ROOT="$(pwd)"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "🔗 PYTHONPATH set: $PROJECT_ROOT"

# --- Check if app is running ---
echo "🔍 Checking if FastAPI app is running..."
if curl -s "$APP_URL" >/dev/null; then
    echo "✅ FastAPI app already running."
    APP_STARTED=false
else
    echo "🚀 FastAPI app not running. Starting it via $APP_LAUNCHER..."
    bash "$APP_LAUNCHER" &
    APP_PID=$!
    APP_STARTED=true

    echo "⏳ Waiting for FastAPI app to become ready..."
    until curl -s "$APP_URL" >/dev/null; do
        sleep 1
    done
    echo "✅ FastAPI app is ready."
fi

# --- Run latency test ---
if [ -f "$TEST_SCRIPT" ]; then
    echo "🧪 Running latency test for ${DURATION}s with concurrency=${CONCURRENCY}..."
    python "$TEST_SCRIPT" -d "$DURATION" -c "$CONCURRENCY"
else
    echo "❌ Test script not found: $TEST_SCRIPT"
    exit 1
fi

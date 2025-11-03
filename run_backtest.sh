#!/usr/bin/env bash

set -e  # Exit on the first error

VENV_DIR="synaptic-venv"
REQUIREMENTS="requirements.txt"
BACKTEST_SCRIPT="src/backtest.py"

cleanup() {
    echo -e "\n📊 Backtest run completed."
    read -p "Press Enter to exit..."
}
trap cleanup EXIT

echo "🟢 Starting backtest runner..."

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

# --- Run backtest script ---
if [ -f "$BACKTEST_SCRIPT" ]; then
    echo "🚀 Running backtest script $BACKTEST_SCRIPT..."
    python "$BACKTEST_SCRIPT"
else
    echo "❌ Backtest script not found: $BACKTEST_SCRIPT"
    exit 1
fi

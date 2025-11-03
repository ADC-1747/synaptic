#!/usr/bin/env bash

set -e  # Exit on the first error

VENV_DIR="synaptic-venv"
REQUIREMENTS="requirements.txt"
TEST_DIR="tests"

cleanup() {
    echo -e "\n🧪 Test run completed."
    read -p "Press Enter to exit..."
}
trap cleanup EXIT

echo "🟢 Starting test runner..."

# Check if venv exists
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

# Ensure src/ is in PYTHONPATH
PROJECT_ROOT="$(pwd)"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo "🔗 PYTHONPATH set to include project root: $PROJECT_ROOT"

# Run the tests
if [ -d "$TEST_DIR" ]; then
    echo "🧪 Running tests in $TEST_DIR..."
    pytest "$TEST_DIR" -v
else
    echo "❌ No test directory found: $TEST_DIR"
    exit 1
fi

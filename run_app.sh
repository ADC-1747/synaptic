#!/usr/bin/env bash

set -e  # Exit on first error

VENV_DIR="synaptic-venv"
REQUIREMENTS="requirements.txt"
APP_ENTRY="src.signal_service"
HOST="0.0.0.0"
PORT="8000"

cleanup() {
    echo -e "\n🛑 Application stopped."
    read -p "Press Enter to exit..."
}
trap cleanup EXIT

echo "🟢 Starting application launcher..."

# Check if the port is already in use (via ss or lsof)
echo "🔍 Checking if port $PORT is already in use..."
if ss -tuln | grep -q ":$PORT " || lsof -i TCP:$PORT &>/dev/null; then
    echo "❌ Port $PORT is already in use."
    
    echo -e "\nRunning processes using port $PORT:"
    ss -tuln | grep ":$PORT " || lsof -i TCP:$PORT

    echo -e "\nDo you want to kill the existing process and continue? (y/n): "
    read -r answer
    if [[ "$answer" == "y" ]]; then
        fuser -k "$PORT"/tcp 2>/dev/null || {
            echo "⚠️ Could not kill using fuser, trying lsof..."
            kill -9 $(lsof -ti tcp:"$PORT") 2>/dev/null
        }
        echo "✅ Killed process on port $PORT."
    else
        echo "⚠️ Exiting without starting the app."
        exit 1
    fi
else
    echo "✅ Port $PORT is free."
fi

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

# Run the FastAPI app using Uvicorn
echo "🚀 Running FastAPI app ($APP_ENTRY) at http://$HOST:$PORT"
uvicorn "$APP_ENTRY:app" --host "$HOST" --port "$PORT" --reload

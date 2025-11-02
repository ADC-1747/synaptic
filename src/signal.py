# src/signal.py

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
from src.stream_stub import price_stream, Tick
from src.data_handler import data_handler
from src.indicators import calculate_sma, calculate_rsi, determine_trend, make_decision

app = FastAPI()

# In-memory state for the latest signals
latest_signals: Dict[str, Dict] = {}

# List of active WebSocket connections
websocket_connections: List[WebSocket] = []

async def consumer():
    """
    Consumes ticks from the price stream, updates data, calculates signals,
    and updates the in-memory state.
    """
    async for tick in price_stream(symbols=("XYZ","ABC"), interval_ms=50):
        try:
            data_handler.add_tick(tick.symbol, tick.price)
            prices = data_handler.get_prices(tick.symbol)

            # Calculate indicators
            sma_20 = calculate_sma(prices, 20)
            sma_50 = calculate_sma(prices, 50)
            rsi_14 = calculate_rsi(prices, 14)

            # Determine trend and decision
            trend = determine_trend(sma_20, sma_50)
            decision = make_decision(sma_20, sma_50, rsi_14)

            # Update the signal state
            signal = {
                "symbol": tick.symbol,
                "price": tick.price,
                "trend": trend,
                "rsi": rsi_14,
                "decision": decision,
                "timestamp": tick.ts
            }
            latest_signals[tick.symbol] = signal
            
            # Broadcast the latest decision to WebSocket clients
            await broadcast_decision(signal)
        except ValueError as e:
            print(f"Error processing tick: {e}")
        except Exception as e:
            print(f"An unexpected error occurred in the consumer: {e}")


async def broadcast_decision(signal: Dict):
    """Broadcasts the latest decision to all connected WebSocket clients."""
    for connection in websocket_connections:
        try:
            await connection.send_json(signal)
        except RuntimeError:
            # Handle cases where the connection is closed
            pass

@app.on_event("startup")
async def startup_event():
    """Starts the background consumer task."""
    asyncio.create_task(consumer())

@app.get("/signal")
async def get_signal(symbol: str):
    """Returns the latest trading signal for a given symbol."""
    if not symbol or not isinstance(symbol, str):
        raise HTTPException(status_code=400, detail="Symbol must be a non-empty string.")
    
    if symbol in latest_signals:
        return latest_signals[symbol]
    
    raise HTTPException(status_code=404, detail="No signal available for this symbol")


@app.websocket("/ws/signal")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to stream the latest trading signals."""
    await websocket.accept()
    websocket_connections.append(websocket)
    try:
        while True:
            # Keep the connection alive by waiting for a message (e.g., a ping from the client)
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)
    except Exception as e:
        print(f"An error occurred in the WebSocket endpoint: {e}")
        websocket_connections.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
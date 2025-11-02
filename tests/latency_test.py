# tests/latency_test.py

import asyncio
import time
import httpx
import websockets
import numpy as np
import argparse
from typing import List

# --- Configuration ---
DEFAULT_DURATION = 10  # seconds
DEFAULT_CONCURRENCY = 10
DEFAULT_QPS = 100
HTTP_URL = "http://localhost:8000/signal?symbol=XYZ"
WS_URL = "ws://localhost:8000/ws/signal"

# --- Global lists to store response times ---
http_response_times: List[float] = []
ws_response_times: List[float] = []

async def http_worker(client: httpx.AsyncClient, start_time: float, duration: int):
    """A worker that sends HTTP requests."""
    while time.time() - start_time < duration:
        request_start_time = time.time()
        try:
            response = await client.get(HTTP_URL)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"HTTP request failed: {e}")
        finally:
            request_end_time = time.time()
            http_response_times.append((request_end_time - request_start_time) * 1000) # in ms
        await asyncio.sleep(1 / DEFAULT_QPS) # Throttle requests to achieve target QPS

async def ws_worker(start_time: float, duration: int):
    """A worker that establishes WebSocket connections."""
    while time.time() - start_time < duration:
        request_start_time = time.time()
        try:
            async with websockets.connect(WS_URL) as websocket:
                await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection failed: {e}")
        finally:
            request_end_time = time.time()
            ws_response_times.append((request_end_time - request_start_time) * 1000) # in ms
        await asyncio.sleep(1) # Connect and receive once per second

async def main(duration: int, concurrency: int):
    """Main function to run the latency test."""
    print(f"Starting latency test for {duration} seconds with {concurrency} concurrent users.")
    print(f"Target QPS for HTTP endpoint: {DEFAULT_QPS}")

    start_time = time.time()

    # --- Create and run HTTP workers ---
    async with httpx.AsyncClient() as client:
        http_tasks = [
            http_worker(client, start_time, duration)
            for _ in range(concurrency)
        ]
        
        # --- Create and run WebSocket workers ---
        ws_tasks = [
            ws_worker(start_time, duration)
            for _ in range(concurrency // 2) # Fewer WS connections as they are longer-lived
        ]

        await asyncio.gather(*http_tasks, *ws_tasks)

    end_time = time.time()
    print(f"\nTest finished in {end_time - start_time:.2f} seconds.")

    # --- Calculate and print results ---
    if http_response_times:
        p95_http = np.percentile(http_response_times, 95)
        avg_http = np.mean(http_response_times)
        print("\n--- HTTP /signal Results ---")
        print(f"Total requests: {len(http_response_times)}")
        print(f"Average response time: {avg_http:.2f} ms")
        print(f"P95 response time: {p95_http:.2f} ms")
        if p95_http < 100:
            print("P95 latency is within the 100ms target.")
        else:
            print("P95 latency is ABOVE the 100ms target.")

    if ws_response_times:
        p95_ws = np.percentile(ws_response_times, 95)
        avg_ws = np.mean(ws_response_times)
        print("\n--- WebSocket /ws/signal Results ---")
        print(f"Total connections: {len(ws_response_times)}")
        print(f"Average connection + first message time: {avg_ws:.2f} ms")
        print(f"P95 connection + first message time: {p95_ws:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Latency test for the signal service.")
    parser.add_argument("-d", "--duration", type=int, default=DEFAULT_DURATION, help="Test duration in seconds.")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Number of concurrent users.")
    args = parser.parse_args()

    # --- Instructions ---
    print("To run this test:")
    print("1. Start the FastAPI server: uvicorn src.signal:app --host 0.0.0.0 --port 8000")
    print(f"2. Run this script: python tests/latency_test.py -d {args.duration} -c {args.concurrency}")
    
    asyncio.run(main(args.duration, args.concurrency))

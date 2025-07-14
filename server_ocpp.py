#!/usr/bin/env python3
import asyncio
import json
import websockets
from datetime import datetime

PORT = 2409

# Keep track of all connected clients
connected = set()

def current_time():
    """Return a formatted timestamp."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def handler(websocket, path=None):
    # Register new client
    addr = websocket.remote_address
    print(f"→ New connection from {addr}")
    connected.add(websocket)

    # Send a one-off welcome
    await websocket.send(json.dumps({
        "type":    "welcome",
        "time":    current_time(),
        "message": "You are now connected to OCPP Server"
    }))

    try:
        async for message in websocket:
           
            print(f"[{current_time()}] ► Received from {addr}: {message}")

            # 1) Echo back to the sender (ESP32 expects this)
            try:
                await websocket.send(f"Echo: {message}")
            except Exception:
                pass

            # 2) Broadcast the *raw* message to all other clients
            dead = set()
            for ws in connected:
                if ws is websocket:
                    continue
                try:
                    await ws.send(message)
                except Exception:
                    dead.add(ws)

            # Clean up any dead connections
            for ws in dead:
                connected.remove(ws)

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[{current_time()}] !!! Error: {e}")
    finally:
        connected.remove(websocket)
        print(f"[{current_time()}] ◀ Client disconnected — {len(connected)} remaining")



async def broadcaster():
    # Optional heartbeat so you know the server is alive
    while True:
        if connected:
            beat = json.dumps({
                "type": "heartbeat",
                "time": current_time()
            })
            await asyncio.gather(*(ws.send(beat) for ws in connected))
            print(f"[{current_time()}] ◉ Heartbeat → {len(connected)} client(s)")
        await asyncio.sleep(5)

async def main():
    # Serve with a handler that accepts (websocket, path) signature
    async with websockets.serve(handler, "0.0.0.0", PORT):
        print(f"[{current_time()}] Listening on ws://0.0.0.0:{PORT}")
        # start background heartbeat
        asyncio.create_task(broadcaster())
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down by user.")

import asyncio
import websockets
from datetime import datetime  # For real-time timestamps

PORT = 7890

# Check websockets version
WEBSOCKETS_VERSION = tuple(map(int, websockets.__version__.split(".")))

# WebSocket handler
if WEBSOCKETS_VERSION < (10, 1):  # For websockets < 10.1
    async def echo(websocket, path):  # path is required
        """
        WebSocket handler for older versions of websockets.
        """
        print(f"New connection established at path: {path}")
        try:
            async for message in websocket:
                # Get the current time and format it
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] Received: {message}")
                await websocket.send(f"Echo: {message}")
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed cleanly.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
else:  # For websockets >= 10.1
    async def echo(websocket):  # path is optional or deprecated
        """
        WebSocket handler for newer versions of websockets.
        """
        print("New connection established.")
        try:
            async for message in websocket:
                # Get the current time and format it
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{current_time}] Received: {message}")
                await websocket.send(f"Echo: {message}")
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed cleanly.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

# Main server function
async def main():
    """
    Starts the WebSocket server.
    """
    if WEBSOCKETS_VERSION < (10, 1):
        server = websockets.serve(echo, "0.0.0.0", PORT)  # path required
    else:
        server = websockets.serve(echo, "0.0.0.0", PORT)  # path optional

    async with server:
        print(f"Server is running on ws://0.0.0.0:{PORT}")
        await asyncio.Future()  # Keeps the server running forever

if __name__ == "__main__":
    asyncio.run(main())

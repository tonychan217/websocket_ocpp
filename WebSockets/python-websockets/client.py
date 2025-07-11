import asyncio
import websockets
from datetime import datetime  # For real-time timestamps

PORT = 7890

async def send_messages(websocket):
    """
    Sends messages to the WebSocket server in a loop.
    """
    counter = 0
    while True:
        message = f"Fuck You!"
        print(f"Sending: {message}")
        await websocket.send(message)
        counter += 1
        await asyncio.sleep(1)  # Wait 1 second before sending the next message

async def receive_messages(websocket):
    """
    Receives messages from the WebSocket server in real time and timestamps them.
    """
    while True:
        try:
            response = await websocket.recv()
            # Get the current time and format it
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{current_time}] Received: {response}")
        except websockets.exceptions.ConnectionClosedOK:
            print("Connection closed cleanly.")
            break
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed with error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

async def test_client():
    """
    Connects to the WebSocket server and handles real-time communication.
    """
    uri = f"ws://localhost:{PORT}"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to the server.")
            
            # Create tasks for sending and receiving messages concurrently
            send_task = asyncio.create_task(send_messages(websocket))
            receive_task = asyncio.create_task(receive_messages(websocket))
            
            # Wait for both tasks to complete
            await asyncio.gather(send_task, receive_task)
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed with error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())

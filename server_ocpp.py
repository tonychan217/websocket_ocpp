#!/usr/bin/env python3
import asyncio
import json
import uuid
import websockets
from datetime import datetime, timezone, timedelta

PORT = 2409
TZ_BEIJING = timezone(timedelta(hours=8))
_transaction_counter = 1

# Keep track of all connected clients
connected = set()

# For each websocket, track which DataTransfer command to send next
next_dt_index = {}

# The five DataTransfer commands to cycle through
dt_commands = [
    {
        "command": "GetConverter",
        "payload": {
            "ChargerID": "CP_01",
            "Status": "On",
            "Voltage": 450,
            "Current": 28.6
        }
    },
    {
        "command": "SetConverter",
        "payload": {
            "ChargerID": "CP_01",
            "Error": "No Error"
        }
    },
    {
        "command": "SetRelay",
        "payload": {
            "ChargerID": "CP_01",
            "Error": "No Error"
        }
    },
    {
        "command": "GetConnectorStatus",
        "payload": {
            "ChargerID": "CP_01",
            "Status": "UnplugUnlock"
        }
    },
    {
        "command": "GetEVInfo",
        "payload": {
            "ChargerID": "CP_01",
            "Capacity": 65000,
            "SoC": 82,
            "SoH": 96
        }
    }
]

def current_time() -> str:
    return datetime.now(TZ_BEIJING).strftime("%Y-%m-%dT%H:%M:%SZ")

async def handler(websocket, path=None):
    global _transaction_counter
    addr = websocket.remote_address
    print(f"[{current_time()}] → Connected: {addr}")
    connected.add(websocket)

    try:
        async for raw in websocket:
            ts = current_time()
            print(f"[{ts}] ► Received from {addr}: {raw!r}")

            # ── Broadcast incoming message to all other clients ──
            dead = set()
            for ws in connected:
                if ws is websocket:
                    continue
                try:
                    await ws.send(raw)
                except:
                    dead.add(ws)
            for ws in dead:
                connected.discard(ws)

            # ── Parse and handle OCPP CALL frames ──
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print("  ⚠️ invalid JSON, skipping OCPP logic")
                continue

            # OCPP CALL: [2, UniqueId, Action, Payload]
            if (
                isinstance(msg, list)
                and len(msg) == 4
                and msg[0] == 2
            ):
                unique_id, action, payload = msg[1], msg[2], msg[3]

                # build result_payload per action
                if action == "BootNotification":
                    result_payload = {
                        "currentTime": current_time(),
                        "interval": 10,
                        "status": "Accepted"
                    }
                elif action == "Heartbeat":
                    # 1) Heartbeat CALLRESULT
                    result_payload = {
                        "currentTime": current_time()
                    }
                elif action == "StatusNotification":
                    result_payload = {}
                elif action == "Authorize":
                    result_payload = {
                        "idTagInfo": {"status": "Accepted"}
                    }
                elif action == "StartTransaction":
                    txid = _transaction_counter
                    _transaction_counter += 1
                    result_payload = {
                        "transactionId": txid,
                        "idTagInfo": {"status": "Accepted"}
                    }
                elif action == "StopTransaction":
                    result_payload = {
                        "idTagInfo": {"status": "Accepted"}
                    }
                else:
                    print(f"  ⚠️ Unhandled OCPP action: {action}")
                    continue

                # send the CALLRESULT back to the originator
                resp = [3, unique_id, result_payload]
                text = json.dumps(resp)
                await websocket.send(text)
                print(f"[{current_time()}] ✿ Sent {action} CALLRESULT → {text!r}")

                # 2) If it was a Heartbeat, send exactly one DataTransfer CALL in round-robin
                if action == "Heartbeat":
                    idx = next_dt_index.get(websocket, 0)
                    dt = dt_commands[idx]
                    dt_call = [
                        2,
                        unique_id,
                        "DataTransfer",
                        dt
                    ]
                    dt_text = json.dumps(dt_call)
                    await websocket.send(dt_text)
                    print(f"[{current_time()}] ♥ Sent DataTransfer → {dt_text!r}")

                    # increment and wrap the index
                    next_dt_index[websocket] = (idx + 1) % len(dt_commands)

                # ── Broadcast that CALLRESULT to all OTHER clients ──
                dead = set()
                for ws in connected:
                    if ws is websocket:
                        continue
                    try:
                        await ws.send(text)
                    except:
                        dead.add(ws)
                for ws in dead:
                    connected.discard(ws)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected.discard(websocket)
        next_dt_index.pop(websocket, None)
        print(f"[{current_time()}] ╭(╯^╰)╮ Disconnected: {addr} -- {len(connected)} remaining")

async def main():
    print(f"[{current_time()}] Starting ws://0.0.0.0:{PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()   # run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down by user.")

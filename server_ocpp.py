#!/usr/bin/env python3
import asyncio
import json
import uuid
import websockets
from datetime import datetime, timezone, timedelta

PORT = 2409
TZ_BEIJING = timezone(timedelta(hours=8))

# Keep track of all connected clients
connected = set()

# For each websocket, track which DataTransfer command to send next
next_dt_index = {}

# Keep track of BootNotification unique IDs per client
boot_unique_ids = {}

def current_time() -> str:
    return datetime.now(TZ_BEIJING).strftime("%Y-%m-%dT%H:%M:%SZ")

async def handler(websocket, path=None):  # Remove default path
    actual_path = websocket.request.path or "/"  # Use actual path, default to "/" if None
    addr = websocket.remote_address
    allowed_paths = ["/CP_01", "/CP_02", "/CP_03", "/CP_04", "/CP_05", "/CP_06"]
    if actual_path not in allowed_paths:
        await websocket.close(code=1008)
        return

    suffix = actual_path
    print(f"[{current_time()}] (づ｡◕‿‿◕｡)づ Connected: {addr}{suffix}")
    connected.add(websocket)

    # Send TriggerMessage for CP_0x when connected
    if actual_path in ["/CP_01", "/CP_02", "/CP_03", "/CP_04", "/CP_05", "/CP_06"]:
        
        ws_unique_id = uuid.uuid4().hex
        trigger_msg = [
            2,
            ws_unique_id,
            "TriggerMessage",
            {
                "requestedMessage": "StatusNotification",
                "connectorId": 1
            }
        ]
        text = json.dumps(trigger_msg)
        try:
            await websocket.send(text)
            print(f"[{current_time()}] ✨ Sent TriggerMessage CALL → {text!r}")
        except:
            connected.discard(websocket)
            return

    try:
        async for raw in websocket:
            ts = current_time()
            print(f"[{ts}] ► Received from {addr}{suffix}: {raw!r}")

            # ── Intercept plain "start"/"stop" commands ──
            cmd = raw.strip()
            if cmd in ("start", "stop", "get"):
                ws_unique_id = uuid.uuid4().hex
                if cmd == "start":
                    action = "RemoteStartTransaction"
                    payload = {
                        "connectorId": 1,
                        "idTag": "ABC123",
                        "chargingProfile": {
                            "chargingProfileId": 1,
                            "chargingSchedule": {
                                "chargingRateUnit": "A",
                                "chargingSchedulePeriod": [
                                    { "limit": 32 }
                                ]
                            }
                        }
                    }
                elif cmd == "stop":
                    action = "RemoteStopTransaction"
                    payload = {
                        "transactionId": 1
                    }
                elif cmd == "get":
                    action = "TriggerMessage"
                    payload = {
                        "requestedMessage": "MeterValues",
                        "connectorId": 1
                    }

                call_msg = [2, ws_unique_id, action, payload]
                text = json.dumps(call_msg)
                # Send only to clients connected to the same path
                dead = set()
                for ws in connected:
                    if ws.request.path in [actual_path]:
                        try:
                            await ws.send(text)
                        except:
                            dead.add(ws)
                for ws in dead:
                    connected.discard(ws)
                print(f"[{current_time()}] ✨ Sent {call_msg[2]} CALL → {text!r}")
                # Skip all other logic for this raw message
                continue

            if cmd in ("getStatus1s", "getStatus5s"):
                ws_unique_id = uuid.uuid4().hex

                if cmd == "getStatus1s":
                    action = "GetStatus1s"
                    payload = {
                        "ChargerID": actual_path.lstrip('/')
                    }
           
                elif cmd == "getStatus5s":
                    action = "GetStatus5s"
                    payload = {
                        "ChargerID": actual_path.lstrip('/')
                    }
                

                call_msg = [
                    2,
                    ws_unique_id,
                    "DataTransfer",
                    {
                        "vendorId": "Totex",
                        "messageId": "1",
                        "data": {"command": action, "payload": payload}
                    }
                ]
                text = json.dumps(call_msg)
                # Send only to clients connected to the same path
                dead = set()
                for ws in connected:
                    if ws.request.path in [actual_path]:
                        try:
                            await ws.send(text)
                        except:
                            dead.add(ws)
                for ws in dead:
                    connected.discard(ws)
                print(f"[{current_time()}] ✨ Sent {action} CALL → {text!r}")
                # Skip all other logic for this raw message
                continue

            # ── Broadcast incoming message to clients on the same path ─
            dead = set()
            for ws in connected:
                if ws is websocket or ws.request.path not in [actual_path]:
                    continue
                try:
                    await ws.send(raw)
                except:
                    dead.add(ws)
            for ws in dead:
                connected.discard(ws)

            # Parse incoming message as JSON
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print(f"[{ts}] ⚠️ Invalid JSON, skipping")
                continue

            # OCPP CALL: [2, UniqueId, Action, Payload]
            if (
                isinstance(msg, list)
                and len(msg) == 4
                and msg[0] == 2
            ):
                unique_id, action, payload = msg[1], msg[2], msg[3]

                try:
                    uid = int(unique_id)
                    prev = int(boot_unique_ids.get(websocket, 1))
                    if uid > prev:
                        boot_unique_ids[websocket] = uid
                except (ValueError, TypeError):
                    pass  

                # If it was a BootNotification, send "Accepted" and store unique_id
                if action == "BootNotification":
                    wss_call = [3, unique_id, {
                        "currentTime": current_time(),
                        "interval": 10,
                        "status": "Accepted"}]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] ☆ Sent BootNotification CALL → {wss_text!r}")

                # If it was a StatusNotification, send "Accepted" and store unique_id
                if action == "StatusNotification":
                    wss_call = [3, unique_id, {}]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] ✿ Sent StatusNotification RES → {wss_text!r}")
                    # Check if status is "Finishing" and send TriggerMessage
                    if isinstance(payload, dict) and payload.get("status") == "Finishing":
                        ws_unique_id = uuid.uuid4().hex
                        trigger_msg = [
                            2,
                            ws_unique_id,
                            "TriggerMessage",
                            {
                                "requestedMessage": "StatusNotification",
                                "connectorId": 1
                            }
                        ]
                        trigger_text = json.dumps(trigger_msg)
                        try:
                            await websocket.send(trigger_text)
                            print(f"[{ts}] ✨ Sent TriggerMessage CALL → {trigger_text!r}")
                        except:
                            connected.discard(websocket)
                            return

                # Send Heartbeat after receiving clients' heartbeat
                if action == "Heartbeat":
                    wss_call = [3, unique_id, {"currentTime": current_time()}]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] ♥ Sent Heartbeat RES → {wss_text!r}")

                # If it was a StartTransaction, send "Accepted" and store unique_id
                if action == "StartTransaction":
                    wss_call = [3, unique_id, {
                        "transactionId": 1,
                        "idTagInfo":{
                            "status":"Accepted"
                        }
                    }]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] ╬ Sent StartTransaction RES → {wss_text!r}")

                # If it was a StopTransaction, send "Accepted" and store unique_id
                if action == "StopTransaction":
                    wss_call = [3, unique_id, {
                        "transactionId": 1,
                        "idTagInfo":{
                            "status":"Accepted"
                        }
                    }]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] 乂 Sent StopTransaction RES → {wss_text!r}")

                # If it was a MeterValues, send "Accepted" and store unique_id
                if action == "MeterValues":
                    wss_call = [3, unique_id, {}]
                    wss_text = json.dumps(wss_call)
                    await websocket.send(wss_text)
                    print(f"[{ts}] Σ Sent MeterValues RES → {wss_text!r}")

                if action == "DataTransfer" and isinstance(payload, dict) and "data" in payload:
                    data = payload["data"]
                    # Check if data is a string (needs parsing) or already a dict
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            print(f"[{ts}] ⚠️ Invalid DataTransfer data JSON, skipping")
                            continue
                    # Now data should be a dict
                    if isinstance(data, dict) and data.get("command") in ["SetConverter", "SetRelay", "SetHMI", "SetLED"]:
                        wss_call = [
                            2,  # Changed to CALL to match client expectation
                            unique_id,
                            "DataTransfer",
                            {
                                "vendorId": "Totex",
                                "messageId": "1",
                                "data": {
                                    "command": data["command"],
                                    "payload": data.get("payload", {})
                                }
                            }
                        ]
                        wss_text = json.dumps(wss_call)
                        await websocket.send(wss_text)
                        print(f"[{ts}] ✨ Sent {data['command']} CALL → {wss_text!r}")

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected.discard(websocket)
        next_dt_index.pop(websocket, None)
        print(f"[{current_time()}] ╭(╯^╰)╮ Disconnected: {addr}{suffix} -- {len(connected)} remaining")

async def main():
    print(f"[{current_time()}] Starting ws://0.0.0.0:{PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer shut down by user.")
        

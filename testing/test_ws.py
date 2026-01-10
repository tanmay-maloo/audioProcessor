"""WebSocket test client to send a message to the server.

Usage:
  python3 testing/test_ws.py [ws_url]

Examples:
  python3 testing/test_ws.py ws://localhost:8000/ws/esp32/
  python3 testing/test_ws.py wss://tanmaymaloo.pythonanywhere.com/ws/esp32/
"""
import asyncio
import sys
import socket
import time

try:
    import websockets
except Exception:
    print("Missing dependency: install with `pip install websockets`")
    raise


async def main():
    if len(sys.argv) > 1 and (sys.argv[1].startswith('ws://') or sys.argv[1].startswith('wss://')):
        uri = sys.argv[1]
    else:
        host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
        port = sys.argv[2] if len(sys.argv) > 2 else '8000'
        uri = f"ws://{host}:{port}/ws/esp32/"

    msg = f"WS test from {socket.gethostname()} at {time.time()}"
    print(f"Connecting to {uri}")
    try:
        async with websockets.connect(uri, ping_interval=10, ping_timeout=5) as ws:
            print(f"Connected. Sending message: {msg}")
            await ws.send(msg)
            try:
                # wait for ACK (short timeout)
                data = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"Received: {data!r}")
            except asyncio.TimeoutError:
                print("No response received (timeout)")
    except Exception as e:
        print("WebSocket error:", e)


if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import json

import websockets


async def test_websocket():
    uri = "ws://127.0.0.1:8000/ws/chat/1/"

    async with websockets.connect(uri) as websocket:
        print("WebSocket connected successfully!")

        await websocket.send(
            json.dumps({
                "message": "Hello from YapZone!"
            })
        )

        response = await websocket.recv()
        print("Server response:", response)


asyncio.run(test_websocket())
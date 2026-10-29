import asyncio
import json
import os

import websockets


async def test_websocket():
    token = os.environ.get("YAPZONE_TOKEN")

    if not token:
        raise ValueError("Set the YAPZONE_TOKEN environment variable.")

    conversation_id = 2

    uri = f"ws://127.0.0.1:8000/ws/chat/{conversation_id}/"

    headers = {
        "Authorization": f"Token {token}"
    }

    async with websockets.connect(
        uri,
        additional_headers=headers,
    ) as websocket:
        print("Connected to YapZone!")

        message = {
            "message": "Hello from YapZone WebSocket!"
        }

        await websocket.send(json.dumps(message))
        print("Message sent!")

        response = await websocket.recv()
        data = json.loads(response)

        print("Received message:", data)


asyncio.run(test_websocket())
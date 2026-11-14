import asyncio
import json
import os
import time

import websockets


USER_A_TOKEN = os.environ["YAPZONE_USER_A_TOKEN"]
USER_B_TOKEN = os.environ["YAPZONE_USER_B_TOKEN"]

URL = "ws://127.0.0.1:8000/ws/chat/2/"


async def receive_typing_event(websocket):

    while True:
        response = json.loads(await websocket.recv())

        if response.get("type") == "typing":
            return response


async def main():

    headers_a = {
        "Authorization": f"Token {USER_A_TOKEN}"
    }

    headers_b = {
        "Authorization": f"Token {USER_B_TOKEN}"
    }

    async with (
        websockets.connect(URL, additional_headers=headers_a) as user_a,
        websockets.connect(URL, additional_headers=headers_b) as user_b,
    ):

        print("Both users connected!")

        # First typing event
        await user_a.send(json.dumps({
            "type": "typing",
            "is_typing": True
        }))

        start_time = time.monotonic()

        response = await receive_typing_event(user_b)
        print("User B received:", response)

        # Wait 2 seconds.
        await asyncio.sleep(2)

        # Second typing event resets the timer.
        second_event_time = time.monotonic()

        await user_a.send(json.dumps({
            "type": "typing",
            "is_typing": True
        }))

        response = await receive_typing_event(user_b)
        print("User B received:", response)

        # Wait for automatic timeout.
        response = await asyncio.wait_for(
            receive_typing_event(user_b),
            timeout=5
        )

        elapsed = time.monotonic() - second_event_time

        print("User B received:", response)
        print(f"Timeout after second event: {elapsed:.2f} seconds.")

        assert response["is_typing"] is False
        assert elapsed >= 2.8, "Timer was not reset correctly!"

        print("SUCCESS: Typing timeout resets correctly!")


asyncio.run(main())
import asyncio
import json
import os
import websockets

CONVERSATION_ID = 2

URI = f"ws://127.0.0.1:8000/ws/chat/{CONVERSATION_ID}/"

USER_A_TOKEN = os.environ.get("YAPZONE_USER_A_TOKEN")
USER_B_TOKEN = os.environ.get("YAPZONE_USER_B_TOKEN")


async def connect_user(token):
    return await websockets.connect(
        URI,
        additional_headers={
            "Authorization": f"Token {token}"
        }
    )


async def test_two_users():
    if not USER_A_TOKEN or not USER_B_TOKEN:
        raise ValueError("Set both user tokens as environment variables.")

    async with (
        await connect_user(USER_A_TOKEN) as user_a,
        await connect_user(USER_B_TOKEN) as user_b
    ):
        print("Both users connected!")

        message = {
            "message": "Hello from User A!"
        }

        await user_a.send(json.dumps(message))
        print("User A sent a message.")

        response_a, response_b = await asyncio.gather(
            user_a.recv(),
            user_b.recv()
        )

        print("User A received:", json.loads(response_a))
        print("User B received:", json.loads(response_b))


asyncio.run(test_two_users())
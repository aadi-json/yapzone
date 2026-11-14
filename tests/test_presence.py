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


async def test_presence():

    if not USER_A_TOKEN or not USER_B_TOKEN:
        raise ValueError("Both user tokens are required.")

    # Connect User B first.
    user_b = await connect_user(USER_B_TOKEN)
    print("User B connected.")

    # Consume User B's own online event.
    own_event = json.loads(await user_b.recv())
    print("User B status:", own_event)

    # Connect User A.
    user_a = await connect_user(USER_A_TOKEN)
    print("User A connected.")

    # User B should receive User A's online event.
    online_event = json.loads(await user_b.recv())
    print("User B received:", online_event)

    # Disconnect User A.
    await user_a.close()
    print("User A disconnected.")

    # User B should receive User A's offline event.
    offline_event = json.loads(await user_b.recv())
    print("User B received:", offline_event)

    await user_b.close()


asyncio.run(test_presence())
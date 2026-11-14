import asyncio
import json
import os
import websockets


# Authentication tokens from environment variables
TOKEN_A = os.environ["YAPZONE_USER_A_TOKEN"]
TOKEN_B = os.environ["YAPZONE_USER_B_TOKEN"]

# WebSocket endpoint
URL = "ws://127.0.0.1:8000/ws/chat/2/"


async def receive_event(socket, expected_type):
    """
    Wait until the expected event is received.
    Ignore unrelated events.
    """
    while True:
        event = json.loads(
            await asyncio.wait_for(
                socket.recv(),
                timeout=10
            )
        )

        print("Received:", event)

        if event.get("type") == expected_type:
            return event


async def main():

    headers_a = {
        "Authorization": f"Token {TOKEN_A}"
    }

    headers_b = {
        "Authorization": f"Token {TOKEN_B}"
    }

    async with (
        websockets.connect(
            URL,
            additional_headers=headers_a
        ) as user_a,

        websockets.connect(
            URL,
            additional_headers=headers_b
        ) as user_b,
    ):

        print("\nBoth users connected!")

        # --------------------------------
        # 1. Send a message
        # --------------------------------

        await user_a.send(json.dumps({
            "type": "message",
            "message": "Original message"
        }))

        message = await receive_event(user_a, "message")
        await receive_event(user_b, "message")

        message_id = message["message_id"]

        print("\nOriginal message sent:", message_id)

        # --------------------------------
        # 2. Edit the message
        # --------------------------------

        await user_a.send(json.dumps({
            "type": "edit_message",
            "message_id": message_id,
            "message": "Edited message"
        }))

        await receive_event(user_a, "message_edited")
        await receive_event(user_b, "message_edited")

        print("\nSUCCESS: Message editing works!")

        # --------------------------------
        # 3. Try editing someone else's message
        # --------------------------------

        await user_b.send(json.dumps({
            "type": "edit_message",
            "message_id": message_id,
            "message": "Unauthorized edit"
        }))

        error = await receive_event(user_b, "error")

        print("\nUnauthorized edit response:", error)

        # --------------------------------
        # 4. Delete the original message
        # --------------------------------

        await user_a.send(json.dumps({
            "type": "delete_message",
            "message_id": message_id
        }))

        await receive_event(user_a, "message_deleted")
        await receive_event(user_b, "message_deleted")

        print("\nSUCCESS: Message deletion works!")


if __name__ == "__main__":
    asyncio.run(main())
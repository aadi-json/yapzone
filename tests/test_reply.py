import asyncio
import json
import os
import websockets


TOKEN_A = os.environ["YAPZONE_USER_A_TOKEN"]
TOKEN_B = os.environ["YAPZONE_USER_B_TOKEN"]

URL = "ws://127.0.0.1:8000/ws/chat/2/"


async def receive_event(socket, expected_type):
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

        # 1. Send original message
        await user_a.send(json.dumps({
            "type": "message",
            "message": "Original message for reply test"
        }))

        original_a = await receive_event(user_a, "message")
        original_b = await receive_event(user_b, "message")

        original_message_id = original_a["message_id"]

        print("\nOriginal message ID:", original_message_id)

        # 2. Send reply
        await user_b.send(json.dumps({
            "type": "message",
            "message": "This is my reply!",
            "reply_to": original_message_id
        }))

        reply_a = await receive_event(user_a, "message")
        reply_b = await receive_event(user_b, "message")

        # 3. Validate reply
        assert reply_a["reply_to"] == original_message_id
        assert reply_b["reply_to"] == original_message_id

        assert reply_a["reply_to_details"]["content"] == (
            "Original message for reply test"
        )

        assert reply_b["reply_to_details"]["content"] == (
            "Original message for reply test"
        )

        print("\nSUCCESS: Reply functionality works!")
        print("Reply ID:", reply_a["message_id"])
        print("Original message ID:", reply_a["reply_to"])

        # 4. Try replying to a nonexistent message

        await user_b.send(json.dumps({
            "type": "message",
            "message": "Invalid reply",
            "reply_to": 999999
        }))

        error = await receive_event(user_b, "error")

        assert "not found" in error["error"].lower()

        print("\nSUCCESS: Invalid reply ID rejected!")


if __name__ == "__main__":
    asyncio.run(main())
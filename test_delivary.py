import asyncio
import json
import os
import websockets


TOKEN_A = os.environ["YAPZONE_USER_A_TOKEN"]
TOKEN_B = os.environ["YAPZONE_USER_B_TOKEN"]

URL = "ws://127.0.0.1:8000/ws/chat/2/"


async def main():

    headers_a = {"Authorization": f"Token {TOKEN_A}"}
    headers_b = {"Authorization": f"Token {TOKEN_B}"}

    async with (
        websockets.connect(URL, additional_headers=headers_a) as user_a,
        websockets.connect(URL, additional_headers=headers_b) as user_b,
    ):
        print("Both users connected!")

        # Ignore initial presence events.
        async def receive_event(socket, expected_type):
            while True:
                event = json.loads(await asyncio.wait_for(
                    socket.recv(), timeout=5
                ))

                print("Received:", event)

                if event.get("type") == expected_type:
                    return event

        # User A sends a message.
        await user_a.send(json.dumps({
            "type": "message",
            "message": "Testing delivery receipts!"
        }))

        print("User A sent a message.")

        # User A receives its own message.
        message_a = await receive_event(user_a, "message")

        # User B receives the message.
        message_b = await receive_event(user_b, "message")

        assert message_a["message_id"] == message_b["message_id"]

        # User A receives delivery confirmation.
        receipt = await receive_event(user_a, "delivery_receipt")

        assert receipt["message_id"] == message_a["message_id"]

        print("\nSUCCESS: Delivery receipt received!")


asyncio.run(main())
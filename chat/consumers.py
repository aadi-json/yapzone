import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Conversation, Message
from .connection_manager import connection_manager
from .presence import set_user_online, set_user_offline


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"][
            "conversation_id"
        ]

        self.room_group_name = f"chat_{self.conversation_id}"

        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close()
            return

        self.user_id = user.id
        self.username = user.username

        is_participant = await self.check_participant(self.user_id)

        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        connection_count = await connection_manager.add_connection(
            self.user_id,
            self.channel_name,
        )

        if connection_count == 1:
            await set_user_online(self.user_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "presence_update",
                    "user_id": self.user_id,
                    "username": self.username,
                    "status": "online",
                },
            )

        # Typing timeout task
        self.typing_task = None

        await self.accept()

    async def disconnect(self, close_code):

        # Cancel typing timeout when disconnected.
        if getattr(self, "typing_task", None):
            self.typing_task.cancel()

        if hasattr(self, "room_group_name"):

            connection_count = await connection_manager.remove_connection(
                self.user_id,
                self.channel_name,
            )

            if connection_count == 0:
                await set_user_offline(self.user_id)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "presence_update",
                        "user_id": self.user_id,
                        "username": self.username,
                        "status": "offline",
                    },
                )

            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):

        try:
            data = json.loads(text_data)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Invalid JSON."
            }))
            return

        event_type = data.get("type", "message")

        # Typing events
        if event_type == "typing":

            is_typing = data.get("is_typing")

            if not isinstance(is_typing, bool):
                await self.send(text_data=json.dumps({
                    "error": "is_typing must be a boolean."
                }))
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "user_id": self.user_id,
                    "username": self.username,
                    "is_typing": is_typing,
                },
            )

            # Reset previous timeout.
            if self.typing_task:
                self.typing_task.cancel()

            if is_typing:
                self.typing_task = asyncio.create_task(
                    self.typing_timeout()
                )
            else:
                self.typing_task = None

            return

        # Normal messages
        if event_type != "message":

            await self.send(text_data=json.dumps({
                "error": "Invalid event type."
            }))

            return

        content = data.get("message")

        if not isinstance(content, str) or not content.strip():

            await self.send(text_data=json.dumps({
                "error": "Message cannot be empty."
            }))

            return

        content = content.strip()

        if len(content) > 5000:

            await self.send(text_data=json.dumps({
                "error": "Message cannot exceed 5000 characters."
            }))

            return

        message = await self.save_message(
            self.user_id,
            content,
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                **message,
            },
        )

    # Automatic typing timeout

    async def typing_timeout(self):

        try:
            await asyncio.sleep(3)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "typing_status",
                    "user_id": self.user_id,
                    "username": self.username,
                    "is_typing": False,
                },
            )

            self.typing_task = None

        except asyncio.CancelledError:
            pass

    # Database operations

    @database_sync_to_async
    def check_participant(self, user_id):

        return Conversation.objects.filter(
            id=self.conversation_id,
            participant_1_id=user_id,
        ).exists() or Conversation.objects.filter(
            id=self.conversation_id,
            participant_2_id=user_id,
        ).exists()

    @database_sync_to_async
    def save_message(self, user_id, content):

        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender_id=user_id,
            content=content,
        )

        return {
            "message_id": message.id,
            "message": message.content,
            "sender": message.sender.username,
            "timestamp": message.timestamp.isoformat(),
        }

    # WebSocket event handlers

    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "message",
            "message_id": event["message_id"],
            "message": event["message"],
            "sender": event["sender"],
            "timestamp": event["timestamp"],
        }))

    async def presence_update(self, event):

        await self.send(text_data=json.dumps({
            "type": "presence",
            "user_id": event["user_id"],
            "username": event["username"],
            "status": event["status"],
        }))

    async def typing_status(self, event):

        if event["user_id"] == self.user_id:
            return

        await self.send(text_data=json.dumps({
            "type": "typing",
            "user_id": event["user_id"],
            "username": event["username"],
            "is_typing": event["is_typing"],
        }))